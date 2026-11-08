#!/usr/bin/env python3
"""
Blokada testów na poziomie maszyny: jedno uruchomienie buildu i testów naraz dla danego repozytorium.

  python3 .claude/hooks/test_lock.py -- ./gradlew test
  python3 .claude/hooks/test_lock.py -- npm test

Po co: bramka jakości (quality_gate.py) i agent mogą uruchomić testy w tej samej chwili; wspólny katalog build
(np. build/ Gradle, target/ Mavena) psuje się wtedy, a porażka wygląda jak prawdziwa regresja.
- Czeka na blokadę do $QG_LOCK_WAIT sekund (domyślnie 900); dłużej → nic nie uruchamia, kod 75 („LOCK BUSY”).
- Re-entrant: polecenie dostaje TF_TEST_LOCK_HELD=1, a wywołanie z tą zmienną uruchamia się od razu
  (np. skrypt testów, który sam woła test_lock).
- Kod wyjścia to kod polecenia. Blokada jest plikiem w katalogu tymczasowym, kluczem jest ścieżka repozytorium
  ($CLAUDE_PROJECT_DIR albo bieżący katalog). Bez fcntl (Windows) polecenie biegnie bez blokady z ostrzeżeniem.
Tylko biblioteka standardowa.
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
    """Kontekst z blokadą; zwraca True, gdy blokada jest nasza (albo niepotrzebna), False — zajęta po czasie `wait`."""
    if os.environ.get("TF_TEST_LOCK_HELD") == "1" or fcntl is None:
        if fcntl is None:
            print("⚠ test_lock: brak fcntl — testy bez blokady", file=sys.stderr)
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
            print(f"LOCK BUSY: inne testy tego repozytorium trwają dłużej niż {os.environ.get('QG_LOCK_WAIT', '900')} s "
                  f"— nic nie uruchomiono (kod {BUSY}); spróbuj ponownie po ich zakończeniu", file=sys.stderr)
            return BUSY
        return subprocess.call(cmd, env={**os.environ, "TF_TEST_LOCK_HELD": "1"})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
