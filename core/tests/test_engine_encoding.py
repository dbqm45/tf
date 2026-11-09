#!/usr/bin/env python3
"""Skrypty silnika (.tf/factory/) działają na Windows przy stronie kodowej innej niż UTF-8.

python3 tests/test_engine_encoding.py

Zgłoszenie 2026-11-09: `tf install` na Windows — `build.py` uruchomiony przez instalator z przechwyconym wyjściem
pisał w cp1250 i padał na „✓” (UnicodeEncodeError). Symulujemy to przez PYTHONIOENCODING=cp1250 i PYTHONUTF8=0.
E-1: każdy skrypt silnika i analizatora przestawia stdout/stderr na UTF-8. E-2: `build.py check` przy cp1250 kończy się
bez UnicodeEncodeError i pisze UTF-8. E-3: skrypt uruchamiający inne skrypty silnika czyta ich wyjście jako UTF-8. E-4: procesy potomne
silnika (np. testy po aktualizacji) startują w trybie UTF-8 (PYTHONUTF8=1).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory").is_dir())
ENGINE = ROOT / ".tf" / "factory"


def scripts() -> list[Path]:
    out = [p for p in sorted(ENGINE.glob("*.py")) if "__main__" in p.read_text(encoding="utf-8")]
    return out + sorted((ENGINE / "analyzers").glob("*/scripts/*.py"))


def main() -> int:
    fails = []
    for p in scripts():
        if "reconfigure(encoding=\"utf-8\"" not in p.read_text(encoding="utf-8"):
            fails.append(f"E-1: {p.relative_to(ROOT)} nie przestawia stdout/stderr na UTF-8")
        # E-4: procesy potomne (testy po aktualizacji, build.py, hooki uruchamiane z testów) też w trybie UTF-8 —
        # inaczej test drukujący „✓” do przechwyconego wyjścia albo czytający plik bez encoding pada na cp1250
        if p.parent == ENGINE and 'os.environ.setdefault("PYTHONUTF8", "1")' not in p.read_text(encoding="utf-8"):
            fails.append(f"E-4: {p.relative_to(ROOT)} nie włącza trybu UTF-8 (PYTHONUTF8) dla procesów potomnych")
    env = {**os.environ, "PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0"}
    r = subprocess.run([sys.executable, str(ENGINE / "build.py"), "check"], cwd=ROOT, capture_output=True, env=env,
                       timeout=600)
    err = r.stderr.decode("utf-8", "replace")
    if "UnicodeEncodeError" in err:
        fails.append(f"E-2: build.py check przy cp1250 → UnicodeEncodeError: {err[-400:]}")
    try:
        r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        fails.append("E-2: build.py check przy cp1250 nie pisze UTF-8")
    # E-3: subprocess z text=True bez encoding dekoduje stroną kodową systemu (cp1250) — polskie litery w UTF-8
    # (np. „Ł” = C5 81) rozsypują się albo przerywają odczyt; wyjście skryptów Pythona czytamy jako UTF-8
    call = re.compile(r"subprocess\.run\(\[sys\.executable[^\n]*(?:\n[^\n]*){0,2}")
    for p in sorted(ENGINE.glob("*.py")):
        for m in call.finditer(p.read_text(encoding="utf-8")):
            txt = m.group(0)
            if "text=True" in txt and "encoding=" not in txt:
                line = p.read_text(encoding="utf-8")[:m.start()].count("\n") + 1
                fails.append(f"E-3: {p.relative_to(ROOT)}:{line} czyta wyjście Pythona bez encoding=\"utf-8\"")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} kodowanie skryptów silnika ({len(scripts())} skryptów)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
