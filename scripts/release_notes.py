#!/usr/bin/env python3
"""Wypisuje wpis core/factory/CHANGELOG.md jednej wersji (notatki GitHub Release); kod 1, gdy wpisu nie ma.

  python3 scripts/release_notes.py 2.7.0 > notes.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventional as cc  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    notes = cc.release_notes(Path("core/factory/CHANGELOG.md").read_text(encoding="utf-8"), argv[0])
    if notes is None:
        print(f"✗ core/factory/CHANGELOG.md nie ma wpisu „## [{argv[0]}]”", file=sys.stderr)
        return 1
    print(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
