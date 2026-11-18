#!/usr/bin/env python3
"""Hooks do not interrupt the session on their own error, but the error is recorded (.tf/logs/hook-errors.jsonl).

python3 tests/test_hook_errors.py

A hook that fails silently (`except Exception: pass`) disables its protection without a trace — e.g. the TDD guard
stops blocking, and `onFailure: "block"` will not work because the process exits with code 0. The rule (the human's decision
2026-11-10): the behaviour stays (a hook does not interrupt the session), but every such exception goes to the log, and
`tf doctor` shows a summary. Recording an error itself never raises an exception.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
LOG = Path(".tf") / "logs" / "hook-errors.jsonl"


def load():
    spec = importlib.util.spec_from_file_location("hook_errors", HOOKS / "hook_errors.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_hook(name: str, project: Path, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOKS / f"{name}.py")], input=stdin, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def entries(project: Path) -> list[dict]:
    p = project / LOG
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        proj = t / "proj"
        proj.mkdir()
        os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
        try:
            he = load()
        except Exception as e:  # the module does not exist yet — the rest of the test should run anyway
            he = None
            check(False, f"H-0: .claude/hooks/hook_errors.py can be loaded: {e}")
        if he:
            # H-1: an entry with the hook name, exception type, location (file:line); the message truncated
            try:
                raise ValueError("x" * 1000)
            except ValueError as e:
                he.record("demo_hook", e)
            got = entries(proj)
            check(len(got) == 1 and got[0].get("hook") == "demo_hook" and got[0].get("type") == "ValueError"
                  and re.search(r"test_hook_errors\.py:\d+", got[0].get("where", "")) and len(got[0].get("msg", "")) <= 200
                  and isinstance(got[0].get("ts"), (int, float)), f"H-1: error entry: {got}")
            # H-2: recording does not raise when the log directory cannot be created
            blocker = t / "plik"
            blocker.write_text("x")
            os.environ["CLAUDE_PROJECT_DIR"] = str(blocker)
            try:
                he.record("demo_hook", RuntimeError("y"))
                ok = True
            except Exception:
                ok = False
            check(ok, "H-2: record does not raise an exception for an unwritable directory")
            os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
            # H-3: the log size is limited
            for i in range(3000):
                he.record("spam", RuntimeError(f"error {i} " + "z" * 150))
            size = (proj / LOG).stat().st_size
            check(size <= he.MAX_BYTES, f"H-3: the log limited to {he.MAX_BYTES} B: {size}")
            # H-4: the summary for tf doctor — the number of errors from recent days and the hooks
            (proj / LOG).write_text("\n".join(json.dumps(x) for x in [
                {"ts": time.time() - 3600, "hook": "tdd_guard", "type": "KeyError", "where": "tdd_guard.py:1", "msg": "a"},
                {"ts": time.time() - 7200, "hook": "tdd_guard", "type": "KeyError", "where": "tdd_guard.py:1", "msg": "a"},
                {"ts": time.time() - 30 * 86400, "hook": "skill_hint", "type": "OSError", "where": "x:1", "msg": "b"},
            ]) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(HOOKS / "hook_errors.py"), "--summary", "--days", "7"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(proj)})
            check(r.returncode == 0 and "2" in r.stdout and "tdd_guard" in r.stdout and "skill_hint" not in r.stdout,
                  f"H-4: --summary: {r.stdout}{r.stderr}")
            (proj / LOG).unlink()
            r = subprocess.run([sys.executable, str(HOOKS / "hook_errors.py"), "--summary"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30,
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(proj)})
            check(r.returncode == 0 and r.stdout.strip() == "", f"H-4: with no errors --summary prints nothing: {r.stdout}")
        # H-5: real hooks with a corrupted input: code 0, nothing on stdout, an error in the log (jev_guard without
        # an API key finishes before reading the input — its place is covered by the static check H-6)
        for name in ("skill_hint", "skill_change_guard", "context_guard", "tdd_guard"):
            p = t / f"p-{name}"
            p.mkdir()
            r = run_hook(name, p, "{this is not json")
            hooks = {e.get("hook") for e in entries(p)}
            check(r.returncode == 0 and not r.stdout.strip() and name in hooks,
                  f"H-5: {name} with a corrupted input: code {r.returncode}, stdout {r.stdout[:120]!r}, "
                  f"dziennik {sorted(hooks)}")
    # H-6: the core hooks do not silently swallow a broad exception (pass / return 0 without recording)
    silent = []
    for f in sorted(HOOKS.glob("*.py")):
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines[:-1]):
            if re.match(r"^\s*except\s*(?:\(?\s*(?:Exception|BaseException)\b[^:]*)?:\s*(#.*)?$", line) \
                    and re.match(r"^\s*(pass|return 0|return)\s*(#.*)?$", lines[i + 1]) and "record(" not in lines[i + 1]:
                silent.append(f"{f.name}:{i + 1}")
    check(not silent, f"H-6: silent swallowing of an exception in hooks: {silent}")
    # H-7: tf doctor shows a summary of hook errors
    tf = (ROOT / ".tf" / "factory" / "tf.py").read_text(encoding="utf-8")
    check("hook_errors.py" in tf and "--summary" in tf, "H-7: tf doctor calls hook_errors.py --summary")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} hook errors recorded: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
