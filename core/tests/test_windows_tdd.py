#!/usr/bin/env python3
"""TDD and the task loop on Windows, simulated on any system (no fcntl, msvcrt, `os.name == "nt"`, no POSIX signals).

A Windows user saw "the new test PASSED at once" after a red test: `test_lock.py -- npx vitest run` started `npx`
without a shell, which finds only `.exe` files (npx is `npx.cmd`), so the tests never ran; the traceback has no failure
words, and with the exit code hidden (`… | tail`) the TDD hook took the run for green. And `run_state.py` failed to
import `ui_snap.py`: its `kill_tree(…, sig=SIGKILL)` default (from signal) does not exist on Windows.
python3 .claude/tests/test_windows_tdd.py"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"
LOCK = HOOKS / "test_lock.py"
GUARD = HOOKS / "tdd_guard.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"

# A Windows `msvcrt` for test_lock: the real one on Windows, elsewhere one built on flock (the same exclusive lock
# between handles of one file); it counts its calls, so the test knows the msvcrt path ran.
FAKE_MSVCRT = '''
import types
try:
    import msvcrt as _real
except ImportError:
    _real = None
if _real is not None:
    msvcrt = _real
else:
    import fcntl as _fcntl
    msvcrt = types.SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, calls=[])

    def _locking(fd, mode, nbytes):
        msvcrt.calls.append(mode)
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN if mode == 0 else _fcntl.LOCK_EX | _fcntl.LOCK_NB)
        except BlockingIOError:
            raise PermissionError(13, "Permission denied") from None
    msvcrt.locking = _locking
'''

# test_lock.py as on Windows: no fcntl, msvcrt, os.name == "nt" (WINDOWS), `npx` resolved by shutil.which to a program
# (here: this Python, so the "runner" is a script) — or not found at all with `--no-npx`.
DRIVER = FAKE_MSVCRT + '''
import shutil, sys
sys.path.insert(0, sys.argv[1])
import test_lock as t
t.fcntl, t.msvcrt, t.WINDOWS = None, msvcrt, True
args = sys.argv[2:]
missing = args[0] == "--no-npx"
args = args[1:] if missing else args
t.shutil.which = lambda name, *a, **k: None if missing or name != "npx" else sys.executable
sys.exit(t.main(args))
'''

RUNNER = '''import sys
print("RUN  v1.6.0 src/price.test.ts")
print("the runner says: discount() returned 100" if sys.argv[1] == "red" else "all good")
sys.exit(1 if sys.argv[1] == "red" else 0)
'''


def load_lock():
    spec = importlib.util.spec_from_file_location("tf_test_lock_win", LOCK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "proj"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "price.test.ts").write_text("test('discount', () => expect(discount(100)).toBe(90))\n")
        runner = Path(d) / "runner.py"
        runner.write_text(RUNNER, encoding="utf-8")
        driver = Path(d) / "driver.py"
        driver.write_text(DRIVER, encoding="utf-8")
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        for k in ("TF_TEST_LOCK_HELD", "CLAUDE_TDD", "CLAUDE_TDD_BASH"):
            env.pop(k, None)

        # W-1. a real lock without fcntl: msvcrt, exclusive, waits with a timeout, re-entrant
        ns: dict = {}
        exec(FAKE_MSVCRT, ns)
        lock = load_lock()
        lock.fcntl, lock.msvcrt = None, ns["msvcrt"]
        saved = os.environ.pop("TF_TEST_LOCK_HELD", None)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                with lock.held(proj, wait=5) as first:
                    with lock.held(proj, wait=0.5) as second:
                        pass
                    os.environ["TF_TEST_LOCK_HELD"] = "1"
                    with lock.held(proj, wait=0.5) as reentry:
                        pass
                    os.environ.pop("TF_TEST_LOCK_HELD")
                with lock.held(proj, wait=0.5) as after:
                    pass
        finally:
            if saved is not None:
                os.environ["TF_TEST_LOCK_HELD"] = saved
        check(first and second is False, f"W-1: msvcrt lock is exclusive and times out: {first} {second}")
        check(reentry is True and after is True, f"W-1: re-entry with TF_TEST_LOCK_HELD and a free lock after: {reentry} {after}")
        check("without a lock" not in err.getvalue(), f"W-1: no 'without a lock' warning with msvcrt: {err.getvalue()}")
        calls = getattr(ns["msvcrt"], "calls", None)
        check(calls is None or (2 in calls and 0 in calls), f"W-1: the msvcrt path locked and unlocked: {calls}")

        # W-2. resolving the program and splitting a Windows command line
        lock.WINDOWS = True
        real_which = lock.shutil.which
        lock.shutil.which = lambda name, *a, **k: r"C:\Program Files\nodejs\npx.cmd" if name == "npx" else None
        try:
            check(lock.resolve(["npx", "vitest", "run"]) == [r"C:\Program Files\nodejs\npx.cmd", "vitest", "run"],
                  f"W-2: npx → npx.cmd: {lock.resolve(['npx', 'vitest', 'run'])}")
            check(lock.split_command(r'npx vitest run tests\unit\a.test.ts "a b"')
                  == ["npx", "vitest", "run", r"tests\unit\a.test.ts", "a b"],
                  f"W-2: a backslash is a path separator: {lock.split_command(r'npx vitest run tests' + chr(92) + 'a.ts')}")
        finally:
            lock.shutil.which, lock.WINDOWS = real_which, False

        def lock_run(*args):
            return subprocess.run([sys.executable, str(driver), str(HOOKS), *args], cwd=proj, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", env=env, timeout=60)

        def hook(data):
            out = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(data), capture_output=True, text=True,
                                 encoding="utf-8", env=env, timeout=30).stdout
            return json.loads(out)["hookSpecificOutput"] if out.strip() else None

        command = "python .claude/hooks/test_lock.py -- npx vitest run 2>&1 | tail -20"

        def flow(session, run, failure_event=False):
            """test edit → the run through test_lock as Claude Code reports it → a production edit; (PreToolUse, run)."""
            hook({"hook_event_name": "PostToolUse", "tool_name": "Edit", "session_id": session, "cwd": str(proj),
                  "tool_input": {"file_path": str(proj / "src" / "price.test.ts")}})
            data = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": session, "cwd": str(proj),
                    "tool_input": {"command": command}}
            if failure_event:   # the exit code reached Claude Code: PostToolUseFailure with the output in `error`
                data.update(hook_event_name="PostToolUseFailure", error=f"Exit code {run.returncode}\n{run.stdout}{run.stderr}")
            else:               # a pipe hid the exit code: PostToolUse, the output only
                data["tool_response"] = {"stdout": run.stdout + run.stderr, "stderr": "", "interrupted": False}
            note = hook(data)
            pre = hook({"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": session, "cwd": str(proj),
                        "tool_input": {"file_path": str(proj / "src" / "price.ts")}})
            return pre, note

        red_log = proj / ".tf" / "logs" / "tdd-red.jsonl"

        def red_rows():
            return red_log.read_text(encoding="utf-8").splitlines() if red_log.is_file() else []

        # W-3. a failing command → red recorded, the code edit allowed (also when a pipe hides the exit code)
        r = lock_run("--", "npx", str(runner), "red")
        check(r.returncode == 1 and "exited with code 1" in r.stderr and "without a lock" not in r.stderr,
              f"W-3: test_lock on Windows: the exit code and its line: {r.returncode} {r.stdout} {r.stderr}")
        pre, _ = flow("red-pipe", r)
        check(pre is None, f"W-3: a red run through test_lock (exit code hidden) → the code edit is allowed: {pre}")
        check(len(red_rows()) == 1 and "price.test.ts" in red_rows()[0], f"W-3: tdd-red.jsonl entry: {red_rows()}")
        pre, _ = flow("red-fail", r, failure_event=True)
        check(pre is None and len(red_rows()) == 2, f"W-3: PostToolUseFailure → red: {pre} {red_rows()}")

        # W-4. a passing command → "PASSED at once" as before
        r = lock_run("--", "npx", str(runner), "green")
        check(r.returncode == 0 and "exited with code" not in r.stderr, f"W-4: green run: {r.returncode} {r.stderr}")
        pre, _ = flow("green", r)
        check(pre and pre["permissionDecision"] == "deny" and "PASSED at once" in pre["permissionDecisionReason"],
              f"W-4: a green new test → PASSED at once: {pre}")

        # W-5. a program that is not found is an error: neither green (no "PASSED at once") nor red
        r = lock_run("--no-npx", "--", "tf-npx-not-installed", "vitest", "run")   # not on PATH under any name
        check(r.returncode == 127 and "did not run" in r.stderr, f"W-5: not found → 127: {r.returncode} {r.stderr}")
        for session, failure_event in (("nf-pipe", False), ("nf-fail", True)):
            pre, note = flow(session, r, failure_event)
            check(pre and pre["permissionDecision"] == "deny" and "PASSED" not in pre["permissionDecisionReason"]
                  and "write a test" in pre["permissionDecisionReason"],
                  f"W-5: not found ({session}) is not a pass and not a red: {pre}")
            check(note and "did not run" in note.get("additionalContext", ""), f"W-5: a note for the agent: {note}")
        check(len(red_rows()) == 2, f"W-5: no red entry for a command that did not run: {red_rows()}")
        sh = {"stdout": "", "stderr": "bash: npx: command not found"}
        hook({"hook_event_name": "PostToolUse", "tool_name": "Edit", "session_id": "sh", "cwd": str(proj),
              "tool_input": {"file_path": str(proj / "src" / "price.test.ts")}})
        hook({"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "sh", "cwd": str(proj),
              "tool_input": {"command": "npx vitest run | tail -5"}, "tool_response": sh})
        pre = hook({"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": "sh", "cwd": str(proj),
                    "tool_input": {"file_path": str(proj / "src" / "price.ts")}})
        check(pre and "PASSED" not in pre["permissionDecisionReason"], f"W-5: a shell's 'command not found' is not green: {pre}")

        # W-6. the quality gate: a command that cannot start is red, never a silent pass
        spec = importlib.util.spec_from_file_location("tf_quality_gate_win", HOOKS / "quality_gate.py")
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        ok, out = gate.run(proj, "tf-no-such-program-xyz --run", 30)
        check(ok is False and "could not start" in out, f"W-6: the gate with a missing program: {ok} {out}")

    # W-7. the tf skill scripts import without POSIX signals and fcntl (run_state.py imports ui_snap.py)
    sim = ("import signal, sys\n"
           "for n in ('SIGKILL', 'SIGHUP', 'SIGPIPE', 'SIGALRM', 'SIGUSR1', 'SIGUSR2', 'SIGCHLD', 'SIGQUIT'):\n"
           "    hasattr(signal, n) and delattr(signal, n)\n"
           "sys.modules['fcntl'] = None\n"
           f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
           "import ui_snap, run_state, run_report, intake, plan_drift, security_scan, dashboard_live\n"
           f"sys.path.insert(0, {str(HOOKS)!r})\n"
           "import test_lock, quality_gate\n"
           "print('imported')\n")
    r = subprocess.run([sys.executable, "-c", sim], capture_output=True, text=True, timeout=60)
    check(r.returncode == 0 and "imported" in r.stdout, f"W-7: imports without POSIX signals: {r.stderr[-600:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} Windows TDD and the task loop: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
