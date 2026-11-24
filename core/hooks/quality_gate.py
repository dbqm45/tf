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
- `related_decision` — who worked `related` out, when and why (`run_state.py gate-related`), or `state: not-found` with
  the reason: the loop does not search again and `--status` shows a ⚠;
- `watch` — paths whose change triggers the gate (default: the whole repository);
- `timeout` — seconds; exceeding it is a red result;
- `max_blocks` — after this many blocks of the same code state the gate lets it through with a message for the human (protection
  against a loop, default 3).
The command runs only when code in `watch` changed relative to HEAD (a fingerprint of the diff and new files); after a green
run the same fingerprint does not run the tests a second time. A deliberately red batch (TDD, test before code): the file
`.claude/quality-gate.expected-red` with a reason — the gate lets it through; delete it after the batch. `QG_GATE_DISABLE=1` disables
the gate (e.g. in `.claude/settings.local.json`). State: `.tf/logs/quality-gate.json`; every run (time, duration, result)
is appended to `.tf/logs/quality-gate-runs.jsonl` — the /tf-task run report sums it. Standard library only.
During an active /tf-task run (`.tf/runs/<KEY>/run.json` with a stage other than done/closed, updated within the last
6 hours) the gate does not run the full `command`: the loop's `verify` evidence is required before a slice is done and
before the PR, so tests after every turn and subagent only repeat it: the gate skips with one `ℹ` note per code state,
`related` or not. Outside a run nothing changes. Changes only in `.tf/`, `.claude/` or `docs/project/changes/` (the factory's
and the agent's own files, e.g. `related` written into the gate config) are not code and run nothing.
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
import time
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


# Not project code: task files written by `tf task`, the factory's own files (.tf/: engine, runs, logs, config) and the
# agent's configuration (.claude/: the gate config `related` is written into, settings, hooks). A change there alone runs
# no tests — in a monorepo a root config file would otherwise make "affected" mean every project.
NOT_CODE = ("docs/project/changes", ".tf", ".claude")


def scope(watch: list[str]) -> list[str]:
    return ["--", *(watch or ["."]), *(f":(exclude){p}" for p in NOT_CODE)]


def fingerprint(root: Path, watch: list[str]) -> str | None:
    """Fingerprint of changes in `watch` relative to HEAD; None when nothing changed. Task files (`docs/project/changes/`,
    written by `tf task` after each step) are not a code change and do not trigger the gate."""
    paths = scope(watch)
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
    paths = scope(watch)
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


def related_command(root: Path, cfg: dict) -> list[str] | None:
    """`related` with the changed files; None when it is not set or there is nothing (or too much) to give it."""
    related = cfg.get("related")
    if not related:
        return None
    files = changed_files(root, list(cfg.get("watch") or []))
    return expand_related(related, files, root) if files and len(files) <= RELATED_MAX else None


def gate_command(root: Path, cfg: dict) -> list[str] | str:
    """What the gate runs: `related` with the changed files when it is set and there are files to give it, else `command`."""
    return related_command(root, cfg) or cfg["command"]


ACTIVE_HOURS = 6   # a /tf-task run updated within this many hours counts as active
DONE_STAGES = ("done", "closed")


def active_run(root: Path, now: float | None = None) -> str | None:
    """The key of an active /tf-task run: `.tf/runs/<KEY>/run.json` with a stage other than done/closed, updated within the
    last ACTIVE_HOURS hours (the file's time). None — no run, the gate works as always."""
    now = time.time() if now is None else now
    best = None
    for f in (root / ".tf" / "runs").glob("*/run.json"):
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))
            age = now - f.stat().st_mtime
        except (OSError, ValueError):
            continue
        if isinstance(meta, dict) and meta.get("stage") not in DONE_STAGES and age <= ACTIVE_HOURS * 3600:
            if best is None or age < best[0]:
                best = (age, str(meta.get("key") or f.parent.name))
    return best[1] if best else None


RUNS_LOG = "quality-gate-runs.jsonl"   # one line per gate run: time, duration, result (the run report sums it)


def log_run(root: Path, cmd, ok: bool, seconds: float, related: bool) -> None:
    try:
        (root / ".tf" / "logs").mkdir(parents=True, exist_ok=True)
        row = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "duration_s": round(seconds, 1), "ok": ok,
               "related": related, "command": shown(cmd)}
        with (root / ".tf" / "logs" / RUNS_LOG).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


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
    task = active_run(root)
    if task:
        # A /tf-task run verifies every slice itself (`verify` evidence, reused while the files are unchanged, is required
        # before done and the PR): tests after every turn and every subagent would only repeat that work and make the
        # human wait on "running stop hooks". One short note per code state, not per turn of the same state.
        if state.get("task_skip") != fp:
            print(f"ℹ quality gate: the /tf-task run {task} is active — the tests are left to its `verify`",
                  file=sys.stderr)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({**state, "task_skip": fp}), encoding="utf-8")
        return None
    related = related_command(root, cfg)
    cmd = related or cfg["command"]
    started = time.monotonic()
    ok, tail = run(root, cmd, float(cfg.get("timeout", 600)))
    if ok is None:
        print("quality gate: other tests of this repository are running (the lock is taken) — skipping", file=sys.stderr)
        return None
    log_run(root, cmd, ok, time.monotonic() - started, bool(related))
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
    decision = cfg.get("related_decision") if isinstance(cfg.get("related_decision"), dict) else {}
    if decision.get("state") == "not-found":
        return "on", (f"⚠ Quality gate on: `{command}` — the whole suite on every check; a narrow `related` command was not "
                      f"found ({decision.get('reason') or 'no reason'}, {decision.get('at') or 'no date'}). To retry: remove "
                      "`related_decision` from .claude/quality-gate.json; the next /tf-task run works it out.")
    return "on", (f"✓ Quality gate on: `{command}` — the whole suite on every check; for speed add `related` (only the "
                  "tests of the changed files, a command for this project's stack — the /tf-task loop works one out).")


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
