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
- The exit code is the command's exit code. The lock is a file in the temp directory, keyed by the repository path
  ($CLAUDE_PROJECT_DIR or the current directory). Without fcntl (Windows) the command runs without a lock, with a warning.
Standard library only.
"""
from __future__ import annotations

import contextlib
import hashlib
import os
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

BUSY = 75


def lock_path(root: Path) -> Path:
    key = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"tf-test-lock-{key}"


@contextlib.contextmanager
def held(root: Path, wait: float | None = None):
    """Context with the lock; returns True when the lock is ours (or unnecessary), False — busy after the `wait` time."""
    if os.environ.get("TF_TEST_LOCK_HELD") == "1" or fcntl is None:
        if fcntl is None:
            print("⚠ test_lock: no fcntl — tests without a lock", file=sys.stderr)
        yield True
        return
    wait = float(os.environ.get("QG_LOCK_WAIT", "900")) if wait is None else wait
    f = open(lock_path(root), "a+")
    deadline = time.monotonic() + wait
    try:
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    yield False
                    return
                time.sleep(0.2)
        try:
            yield True
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    finally:
        f.close()


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
        return subprocess.call(cmd, env={**os.environ, "TF_TEST_LOCK_HELD": "1"})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
