#!/usr/bin/env python3
"""
Zgodność starej ścieżki: mechanizm bazy wiedzy jest w rdzeniu (skill core-knowledge). Ten plik przekazuje wywołanie
do `.claude/skills/core-knowledge/scripts/kb.py` z tymi samymi argumentami. Nowe odwołania kieruj do rdzenia.
"""
import runpy
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "core-knowledge" / "scripts" / "kb.py"

if not CORE.exists():
    print("✗ brak .claude/skills/core-knowledge/scripts/kb.py — ta wersja nakładki EV wymaga rdzenia ≥ 5.6.0 "
          "(tf update)", file=sys.stderr)
    raise SystemExit(2)
sys.argv[0] = str(CORE)
runpy.run_path(str(CORE), run_name="__main__")
