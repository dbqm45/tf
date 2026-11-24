#!/usr/bin/env python3
"""Hooks work on Windows: UTF-8 encoding independent of the code page, and a time limit.

python3 tests/test_hook_portability.py

On Windows Python by default encodes stdin/stdout with the system code page (e.g. cp1250), while Claude Code sends and reads
JSON in UTF-8. We simulate this with PYTHONIOENCODING=cp1250. The second problem: `git` hung by a child process
(e.g. fsmonitor on Windows holds a pipe) exceeded the hook limit — Claude Code killed the process and reported
"Stop hook error ... No stderr output". The hook must finish by itself, with code 0, before the limit.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
POLISH = "Zażółć gęślą jaźń — „cudzysłów” i zależności"


def hook_commands() -> list[tuple[str, list[str], int]]:
    # team mode: settings.json; private (the default): settings.local.json
    path = next(p for p in (ROOT / ".claude" / "settings.json", ROOT / ".claude" / "settings.local.json") if p.exists())
    settings = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for event, groups in settings["hooks"].items():
        for g in groups:
            for h in g["hooks"]:
                args = [a.replace("${CLAUDE_PROJECT_DIR}", "") .lstrip("/") for a in h.get("args", [])]
                out.append((event, args, h.get("timeout") or 60))
    return out


def run(args: list[str], root: Path, stdin: bytes, extra_env: dict | None = None, timeout: float = 30):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root), "PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0",
           **(extra_env or {})}
    script = ROOT / args[0]
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, str(script), *args[1:]], input=stdin, capture_output=True, env=env,
                       cwd=root, timeout=timeout)
    return r, time.monotonic() - t0


def payload(event: str) -> bytes:
    data = {"hook_event_name": event, "session_id": "s", "cwd": "", "prompt": POLISH,
            "tool_name": "Write", "tool_input": {"file_path": "notatki.md", "content": POLISH, "command": f"echo '{POLISH}'"},
            "last_assistant_message": POLISH, "stop_hook_active": False}
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def project(d: str) -> Path:
    """A copy of the factory's `.claude/` in an empty repo — the hooks have skills and templates, and the writes do not reach the factory."""
    root = Path(d)
    shutil.copytree(ROOT / ".claude", root / ".claude", ignore=shutil.ignore_patterns("__pycache__", "*.jsonl"))
    subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
    return root


def encoding_tests() -> list[str]:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = project(d)
        run([".claude/hooks/project_record.py", "wip", "start", "Zażółć gęślą jaźń"], root, b"",
            {"PYTHONIOENCODING": "utf-8"})
        for event, args, _ in hook_commands():
            r, _ = run(args, root, payload(event))
            name = " ".join(args)
            if r.returncode not in (0, 2):
                fails.append(f"{event} {name}: exit code {r.returncode}, stderr: {r.stderr[-200:]!r}")
            try:
                r.stdout.decode("utf-8")
            except UnicodeDecodeError:
                fails.append(f"{event} {name}: stdout is not UTF-8 with the cp1250 code page")
    return fails


def plugin_rules_test() -> list[str]:
    """factory_rules.py is registered only in the plugin's hooks.json (not in settings), so the loop above misses it:
    the factory rules hold characters outside cp1250 (→) and the hook crashed on Windows with UnicodeEncodeError."""
    with tempfile.TemporaryDirectory() as d:
        root = project(d)
        rules = f"## Factory rules\n- tests first → code; {POLISH}\n"
        (root / ".tf" / "plugin").mkdir(parents=True)
        (root / ".tf" / "plugin" / "RULES.md").write_text(rules, encoding="utf-8")
        r, _ = run([".claude/hooks/factory_rules.py"], root, payload("SessionStart"))
        if r.returncode != 0:
            return [f"factory_rules.py: exit code {r.returncode} with the cp1250 code page, stderr: {r.stderr[-300:]!r}"]
        try:
            context = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        except (UnicodeDecodeError, ValueError, KeyError) as e:
            return [f"factory_rules.py: stdout is not UTF-8 JSON with the cp1250 code page ({type(e).__name__})"]
        return [] if context == rules.strip() else ["factory_rules.py: the rules came out changed"]


def hint_test() -> list[str]:
    """A Polish prompt read under cp1250 must not get garbled (skill_hint matches word stems)."""
    with tempfile.TemporaryDirectory() as d:
        root = project(d)
        # a core skill — the test works without packs; the Polish characters in the prompt check the decoding
        prompt = "Jaki numer wersji nadać po usunięciu flagi z publicznego API — SemVer, podbicie major czy minor?"
        data = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt}, ensure_ascii=False).encode("utf-8")
        r, _ = run([".claude/hooks/skill_hint.py"], root, data)
        r_utf, _ = run([".claude/hooks/skill_hint.py"], root, data, {"PYTHONIOENCODING": "utf-8"})
        if "core-semver" not in r_utf.stdout.decode("utf-8", "replace"):
            return ["skill_hint: the expected hint is missing (test invalid)"]
        if r.stdout != r_utf.stdout:
            return ["skill_hint gives a different result under cp1250 than under UTF-8 (the prompt was decoded wrongly)"]
    return []


def hanging_git_test() -> list[str]:
    """A hung `git` must not hold the Stop hook until the Claude Code limit."""
    if os.name == "nt":
        return []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        r, _ = run([".claude/hooks/project_record.py", "wip", "start", "Długie zadanie"], root, b"")
        wip = root / ".tf/wip/dlugie-zadanie.md"
        if not wip.exists():
            return [f"wip start: {r.stdout[-200:]!r}"]
        (root / "app.ts").write_text("x", encoding="utf-8")
        old = time.time() - 3600
        os.utime(wip, (old, old))
        fake = root / "fakebin"
        fake.mkdir()
        g = fake / "git"
        g.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
        g.chmod(g.stat().st_mode | stat.S_IEXEC)
        env = {"PATH": f"{fake}{os.pathsep}{os.environ.get('PATH', '')}", "CLAUDE_HOOK_DEADLINE": "1.5"}
        r, took = run([".claude/hooks/project_record.py", "--hook-stop"], root, b"{}", env, timeout=40)
        fails = []
        if r.returncode != 0:
            fails.append(f"Stop with a hung git: code {r.returncode}")
        if took > 4:
            fails.append(f"Stop with a hung git took {took:.1f} s (own limit 1.5 s)")
    return fails


def main() -> int:
    tests = [("encoding", encoding_tests), ("plugin rules", plugin_rules_test), ("skill_hint", hint_test),
             ("hung git", hanging_git_test)]
    fails = []
    for name, fn in tests:
        f = fn()
        print(f"{'OK ' if not f else 'FAIL'} {name}" + ("" if not f else "\n  " + "\n  ".join(f)))
        fails += f
    print(f"\n{len(tests)} test groups, errors: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
