#!/usr/bin/env python3
"""
Stop / SubagentStop: quality gate — a turn does not end with a red build and tests ("the prompt asks, the hook enforces").

Works only with the project configuration `.claude/quality-gate.json` (the factory does not know the project's commands):
  {"command": "npm test", "related": "npx jest --findRelatedTests {files}", "watch": ["src/", "test/"],
   "timeout": 600, "max_blocks": 3}
- `command` — build and tests (a string or an argument list, no shell), run under the test_lock.py lock;
- `related` — optional: the tests related to the changed files only (a string or an argument list, no shell). The token
  `{files}` expands into the changed files as separate arguments; `{files,}` inside a token is replaced with the files joined
  with commas; `{dirs}` gives the directories of the changed source files. The factory knows no test tool: the command
  for the project's stack is chosen in the project (the /tf-task loop proposes one). A placeholder that gives nothing → the
  full `command`. With `related` the gate runs
  it instead of `command` — in a big repository (an Nx monorepo) the whole suite on every turn is the bottleneck. The
  changed files are the ones the fingerprint sees (changed relative to HEAD and new, within `watch`) that still exist;
  when only deletions remain or there are more than RELATED_MAX files, the gate runs the full `command`;
- `watch` — paths whose change triggers the gate (default: the whole repository);
- `timeout` — seconds; exceeding it is a red result;
- `max_blocks` — after this many blocks of the same code state the gate lets it through with a message for the human (protection
  against a loop, default 3).
The command runs only when code in `watch` changed relative to HEAD (a fingerprint of the diff and new files); after a green
run the same fingerprint does not run the tests a second time. A deliberately red batch (TDD, test before code): the file
`.claude/quality-gate.expected-red` with a reason — the gate lets it through; delete it after the batch. `QG_GATE_DISABLE=1` disables
the gate (e.g. in `.claude/settings.local.json`). State: `.tf/logs/quality-gate.json`. Standard library only.
The agent gets long command output as its beginning and end; the whole of the last run is in
`.tf/logs/quality-gate-output.txt`.

  python3 .claude/hooks/quality_gate.py --status [--quiet-ok]   # whether the gate works and why not (tf doctor, session start)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
HEAD, TAIL = 1000, 2000   # this many characters of the output start and end go to the agent
OUTPUT = "quality-gate-output.txt"
RELATED_MAX = 200   # more changed files than this: the full command (Windows limits a command line to ~32k characters)


def clip(out: str, saved: str) -> str:
    """Output for the agent: short in full, long as a beginning and end with a note of how much was omitted and where
    the whole is. The first error is often at the start of the log and the summary at the end — the end alone loses the cause."""
    if len(out) <= HEAD + TAIL:
        return out
    return (out[:HEAD] + f"\n… [skipped {len(out) - HEAD - TAIL} characters; full output: {saved}] …\n" + out[-TAIL:])


def save_output(root: Path, name: str, out: str) -> str:
    """Saves the full output of the last run in .tf/logs/ and returns the relative path (a write error does not interrupt)."""
    rel = f".tf/logs/{name}"
    try:
        (root / ".tf" / "logs").mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(out, encoding="utf-8")
    except OSError:
        pass
    return rel


def _lock():
    spec = importlib.util.spec_from_file_location("test_lock", HERE / "test_lock.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> bytes:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=30)
    return r.stdout if r.returncode == 0 else b""


def fingerprint(root: Path, watch: list[str]) -> str | None:
    """Fingerprint of changes in `watch` relative to HEAD; None when nothing changed. Task files (`docs/project/changes/`,
    written by `tf task` after each step) are not a code change and do not trigger the gate."""
    paths = ["--", *(watch or ["."]), ":(exclude)docs/project/changes"]
    diff = git(root, "diff", "HEAD", "--binary", *paths)
    new = git(root, "ls-files", "--others", "--exclude-standard", *paths).decode(errors="replace").split()
    if not diff and not new:
        return None
    h = hashlib.sha256(diff)
    for rel in sorted(new):
        p = root / rel
        h.update(rel.encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def changed_files(root: Path, watch: list[str]) -> list[str]:
    """The files the fingerprint sees (changed relative to HEAD and new, within `watch`) that still exist, sorted."""
    paths = ["--", *(watch or ["."]), ":(exclude)docs/project/changes"]
    names = (git(root, "diff", "HEAD", "--name-only", "-z", *paths)
             + git(root, "ls-files", "--others", "--exclude-standard", "-z", *paths)).decode(errors="replace")
    return sorted({n for n in names.split("\0") if n and (root / n).is_file()})


CODE_EXT = {".py", ".go", ".rs", ".java", ".kt", ".cs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".rb", ".php", ".swift",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".scala", ".ex", ".exs", ".dart", ".vue", ".svelte"}
PLACEHOLDER = re.compile(r"\{(files|dirs)(,?)\}")


def placeholder_values(root: Path | None, files: list[str], kind: str) -> list[str]:
    """`files` — the changed files; `dirs` — the directories of the changed source files (`./pkg/a`; `.` for the root).
    Nothing here knows a test tool: the project's command (chosen for its stack) decides what to do with them."""
    if kind == "files":
        return files
    return sorted({("./" + Path(f).parent.as_posix()) if Path(f).parent.as_posix() != "." else "."
                   for f in files if Path(f).suffix in CODE_EXT})


def expand_related(template, files: list[str], root: Path | None = None) -> list[str] | None:
    """argv of the `related` command. A token that is exactly `{files}` or `{dirs}` becomes separate arguments; with a
    comma (`{files,}`) or inside a longer token — the values joined with commas (spaces without the comma). None when a
    placeholder gives nothing (e.g. only non-code files changed for `{dirs}`) — then the full command runs. No shell."""
    argv, cache = [], {}

    def values(kind: str) -> list[str]:
        if kind not in cache:
            cache[kind] = placeholder_values(root, files, kind)
        return cache[kind]

    for token in (shlex.split(template) if isinstance(template, str) else [str(t) for t in template]):
        m = PLACEHOLDER.fullmatch(token)
        if m and not m.group(2):
            if not values(m.group(1)):
                return None
            argv.extend(values(m.group(1)))
            continue
        for m in PLACEHOLDER.finditer(token):
            if not values(m.group(1)):
                return None
        argv.append(PLACEHOLDER.sub(lambda m: ("," if m.group(2) else " ").join(values(m.group(1))), token))
    return argv


def gate_command(root: Path, cfg: dict) -> list[str] | str:
    """What the gate runs: `related` with the changed files when it is set and there are files to give it, else `command`."""
    related = cfg.get("related")
    if related:
        files = changed_files(root, list(cfg.get("watch") or []))
        argv = expand_related(related, files, root) if files and len(files) <= RELATED_MAX else None
        if argv:
            return argv
    return cfg["command"]


def shown(cmd) -> str:
    """A command for a message: a string as it is, an argument list joined (shortened when very long)."""
    text = cmd if isinstance(cmd, str) else " ".join(map(str, cmd))
    return text if len(text) <= 300 else text[:300] + " …"


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run(root: Path, cmd, timeout: float) -> tuple[bool | None, str]:
    """(green?, output trimmed to the beginning and end); None = the test lock is busy. Full output: .tf/logs/."""
    lock = _lock()
    split = getattr(lock, "split_command", shlex.split)   # Windows: a backslash is a path separator, not an escape
    argv = split(cmd) if isinstance(cmd, str) else list(map(str, cmd))
    argv = lock.resolve(argv) if hasattr(lock, "resolve") else argv   # Windows: `npx` → `npx.cmd`
    with lock.held(root) as ok:
        if not ok:
            return None, ""
        try:
            proc = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    errors="replace", start_new_session=os.name != "nt",
                                    env={**os.environ, "TF_TEST_LOCK_HELD": "1"})
        except OSError as e:   # the program was not found: an error, never a pass
            return False, (f"the command could not start: `{argv[0] if argv else cmd}` ({e.__class__.__name__}: {e}) "
                           "— fix the command in .claude/quality-gate.json")
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                proc.kill()
            out, _ = proc.communicate()
            saved = save_output(root, OUTPUT, out or "")
            return False, f"przekroczony limit czasu {timeout:g} s\n" + clip(out or "", saved)
    saved = save_output(root, OUTPUT, out or "")
    return proc.returncode == 0, clip(out or "", saved)


def decide(root: Path, data: dict) -> dict | None:
    if os.environ.get("QG_GATE_DISABLE") == "1":
        return None
    cfg_path = root / ".claude" / "quality-gate.json"
    if not cfg_path.is_file():
        return None
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not cfg.get("command"):
        return None
    fp = fingerprint(root, list(cfg.get("watch") or []))
    if fp is None:
        return None
    state_path = root / ".tf" / "logs" / "quality-gate.json"
    state = load_state(state_path)
    if state.get("green") == fp:
        return None
    marker = root / ".claude" / "quality-gate.expected-red"
    if marker.is_file():
        print(f"quality gate: a declared red batch — {marker.read_text(encoding='utf-8').strip()[:200]}",
              file=sys.stderr)
        return None
    max_blocks = int(cfg.get("max_blocks", 3))
    red = state.get("red") or {}
    if red.get("fp") == fp and red.get("count", 0) >= max_blocks:
        return {"systemMessage": f"Quality gate: the tests are still red after {max_blocks} attempts on the same state of "
                                 f"the code — letting it through, the decision is a human's (`{shown(cfg['command'])}`)."}
    cmd = gate_command(root, cfg)
    ok, tail = run(root, cmd, float(cfg.get("timeout", 600)))
    if ok is None:
        print("quality gate: other tests of this repository are running (the lock is taken) — skipping", file=sys.stderr)
        return None
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if ok:
        state_path.write_text(json.dumps({"green": fp}), encoding="utf-8")
        return None
    count = red.get("count", 0) + 1 if red.get("fp") == fp else 1
    state_path.write_text(json.dumps({"green": state.get("green"), "red": {"fp": fp, "count": count}}),
                          encoding="utf-8")
    who = "the subagent" if data.get("hook_event_name") == "SubagentStop" else "the turn"
    return {"decision": "block",
            "reason": f"Quality gate: `{shown(cmd)}` does not pass — fix it before ending {who} "
                      f"(attempt {count}/{max_blocks}). If the red test is intended (TDD), write the reason in "
                      f".claude/quality-gate.expected-red.\n--- output (full: .tf/logs/{OUTPUT}) ---\n{tail}"}


OFF = "The factory will not block red tests."


def _disabled_by(root: Path, env) -> str | None:
    """Where the QG_GATE_DISABLE=1 switch comes from: the session environment or the project settings file."""
    for name in ("settings.local.json", "settings.json"):
        try:
            cfg = json.loads((root / ".claude" / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str((cfg.get("env") or {}).get("QG_GATE_DISABLE", "")) == "1":
            return f"in .claude/{name}"
    return "in the session environment" if env.get("QG_GATE_DISABLE") == "1" else None


def gate_status(root: Path, env=None) -> tuple[str, str]:
    """Gate state in plain language: (state, message). States: on, expected-red, disabled, no-config, invalid,
    no-command. Runs nothing."""
    env = os.environ if env is None else env
    where = _disabled_by(root, env)
    if where:
        return "disabled", (f"⚠ Quality gate disabled by the variable QG_GATE_DISABLE=1 ({where}). {OFF} "
                            "To turn it on: remove this variable.")
    cfg_path = root / ".claude" / "quality-gate.json"
    hint = 'To turn it on: tf onboard --yes (it detects the test command) or write it in this file, e.g. {"command": "npm test"}.'
    if not cfg_path.is_file():
        return "no-config", f"⚠ Quality gate disabled: no .claude/quality-gate.json file. {OFF} {hint}"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = None
    if not isinstance(cfg, dict):
        return "invalid", (f"⚠ Quality gate disabled: the file .claude/quality-gate.json is not valid JSON. "
                           f"{OFF} Fix the file.")
    if not cfg.get("command"):
        return "no-command", (f"⚠ Quality gate disabled: .claude/quality-gate.json lacks the \"command\" field. "
                              f"{OFF} {hint}")
    command = cfg["command"] if isinstance(cfg["command"], str) else " ".join(map(str, cfg["command"]))
    marker = root / ".claude" / "quality-gate.expected-red"
    if marker.is_file():
        try:
            reason = marker.read_text(encoding="utf-8").strip()[:200]
        except OSError:
            reason = ""
        return "expected-red", ("⚠ Quality gate lets red tests through: the file .claude/quality-gate.expected-red"
                                + (f" ({reason})" if reason else "") + ". Remove it when the batch is done.")
    related = cfg.get("related")
    if related:
        related = related if isinstance(related, str) else " ".join(map(str, related))
        return "on", (f"✓ Quality gate on: `{related}` for the changed files (`related`), "
                      f"the full `{command}` when there are none to pass (only deletions) or too many.")
    return "on", (f"✓ Quality gate on: `{command}` — the whole suite on every check; for speed add `related` (only the "
                  "tests of the changed files, a command for this project's stack — the /tf-task loop proposes one).")


def main() -> int:
    if "--status" in sys.argv[1:]:   # tf doctor and session start: one sentence about the gate state, always exit 0
        state, text = gate_status(Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve())
        if state != "on" or "--quiet-ok" not in sys.argv[1:]:
            print(text)
        return 0
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    try:
        out = decide(root, data)
    except Exception as e:  # noqa: BLE001 — the gate must not break the session
        print(f"quality gate: error ({e}) — skipping", file=sys.stderr)
        return 0
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
