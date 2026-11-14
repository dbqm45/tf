#!/usr/bin/env python3
"""Przestarzała ścieżka (tryb mode-talos, warstwa zgodności): skrypt jest w `.claude/skills/tf/scripts/`.
To przekierowanie uruchamia go z tymi samymi argumentami — dla istniejących instalacji, własnych skryptów i CI."""
import subprocess
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "tf" / "scripts" / Path(__file__).name

if __name__ == "__main__":
    if not TARGET.is_file():
        print(f"✗ brak {TARGET} — zaktualizuj fabrykę (tf update); pętla jest w rdzeniu, polecenie /tf")
        raise SystemExit(2)
    raise SystemExit(subprocess.run([sys.executable, str(TARGET), *sys.argv[1:]]).returncode)
