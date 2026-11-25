#!/usr/bin/env python3
"""
Machine-level test lock: one build-and-test run at a time for a given repository.

  python3 .claude/hooks/test_lock.py -- ./gradlew test
  python3 .claude/hooks/test_lock.py -- npm test

Why: the quality gate (quality_gate.py) and an agent may run tests at the same moment; a shared build directory
(e.g. Gradle build/, Maven target/) gets corrupted then, and the failure looks like a real regression.
- Waits for the lock up to $QG_LOCK_WAIT seconds (default 900); longer → runs nothing, exit code 75 ("LOCK BUSY").
- Re-entrant: the command gets TF_TEST_LOCK_HELD=1, and a call with this variable runs immediately
  (e.g. a test script that itself calls test_lock).
- The exit code is the command's exit code; a non-zero one also ends the output with the line
  "✗ test_lock: the command exited with code N" (stderr), so the TDD hook sees a red run even when a pipe (`| tail`)
  hides the exit code. A command that cannot be started (not found) is code 127 and the line
  "✗ test_lock: the command did not run" — an error, never a pass and never a red test.
- Windows: the executable is resolved like a shell does (`npx` → `npx.cmd`, `shutil.which`), because a process started
  without a shell finds only `.exe` files.
- The lock is a file in the temp directory, keyed by the repository path ($CLAUDE_PROJECT_DIR or the current
  directory): `fcntl.flock` on POSIX, `msvcrt.locking` on Windows; without either the command runs without a lock,
  with a warning.
Standard library only.
"""
from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: the code page (cp1250) cannot hold "→", "⚠" — UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
try:
    import msvcrt
except ImportError:  # POSIX
    msvcrt = None

BUSY = 75
NOT_RUN = 127                 # the command could not be started (as a shell says for "command not found")
WINDOWS = os.name == "nt"
EXITED = "✗ test_lock: the command exited with code"    # tdd_guard.py reads these two lines (a red run / not a run)
DID_NOT_RUN = "✗ test_lock: the command did not run"


def lock_path(root: Path) -> Path:
    key = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"tf-test-lock-{key}"


def _try_lock(f) -> bool:
    """One non-blocking attempt at the exclusive lock: True = ours, False = someone else holds it."""
    if fcntl is not None:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)   # the first byte; locking past the end of the file is allowed
        return True
    except OSError:
        return False


def _unlock(f) -> None:
    if fcntl is not None:
        fcntl.flock(f, fcntl.LOCK_UN)
        return
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


@contextlib.contextmanager
def held(root: Path, wait: float | None = None):
    """Context with the lock; returns True when the lock is ours (or unnecessary), False — busy after the `wait` time."""
    if os.environ.get("TF_TEST_LOCK_HELD") == "1":
        yield True
        return
    if fcntl is None and msvcrt is None:
        print("⚠ test_lock: no fcntl or msvcrt — tests without a lock", file=sys.stderr)
        yield True
        return
    if wait is None:
        try:
            wait = float(os.environ.get("QG_LOCK_WAIT", "900"))
        except ValueError:   # a malformed value: the default wait, not a crash
            wait = 900.0
    f = open(lock_path(root), "a+")
    deadline = time.monotonic() + wait
    try:
        while not _try_lock(f):
            if time.monotonic() >= deadline:
                yield False
                return
            time.sleep(0.2)
        try:
            yield True
        finally:
            _unlock(f)
    finally:
        f.close()


def resolve(argv: list[str]) -> list[str]:
    """Windows: the program as a shell would find it — `npx` → `C:\\…\\npx.cmd` (PATHEXT); elsewhere unchanged.
    A process started without a shell finds only `.exe` files, so `npx`, `npm`, `yarn`, `pnpm` would not start."""
    if not WINDOWS or not argv:
        return list(argv)
    found = shutil.which(argv[0])
    return [found, *argv[1:]] if found else list(argv)


def split_command(command: str) -> list[str]:
    """A command line → arguments. On Windows a backslash is a path separator, not an escape (`tests\\a.test.ts`
    must not become `testsa.test.ts`); quotes around an argument are removed."""
    import shlex
    if not WINDOWS:
        return shlex.split(command)
    return [a[1:-1] if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'" else a for a in shlex.split(command, posix=False)]


def call(cmd: list[str], **kw) -> int:
    """Runs the command and returns its exit code; a non-zero one ends the output with the EXITED line. A program that
    cannot be started is code NOT_RUN with the DID_NOT_RUN line — an error, never a pass."""
    try:
        code = subprocess.call(resolve(cmd), **kw)
    except OSError as e:
        print(f"{DID_NOT_RUN}: cannot start `{cmd[0]}` ({e.__class__.__name__}: {e}) — check the program name and "
              f"PATH (code {NOT_RUN}); this is not a test result", file=sys.stderr)
        return NOT_RUN
    if code != 0:
        sys.stdout.flush()
        print(f"{EXITED} {code}", file=sys.stderr)
    return code


def main(argv: list[str]) -> int:
    if "--" not in argv or argv.index("--") == len(argv) - 1:
        print(__doc__)
        return 2
    cmd = argv[argv.index("--") + 1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    with held(root) as ok:
        if not ok:
            print(f"LOCK BUSY: other tests of this repository have been running longer than {os.environ.get('QG_LOCK_WAIT', '900')} s "
                  f"— nothing was run (code {BUSY}); try again after they finish", file=sys.stderr)
            return BUSY
        return call(cmd, env={**os.environ, "TF_TEST_LOCK_HELD": "1"})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
