#!/usr/bin/env python3
"""The engine scripts (.tf/factory/) work on Windows with a code page other than UTF-8.

python3 tests/test_engine_encoding.py

Report 2026-11-09: `tf install` on Windows — `build.py` run by the installer with captured output
wrote in cp1250 and crashed on “✓” (UnicodeEncodeError). We simulate it with PYTHONIOENCODING=cp1250 and PYTHONUTF8=0.
E-1: every engine and analyser script switches stdout/stderr to UTF-8. E-2: `build.py check` under cp1250 finishes
without UnicodeEncodeError and writes UTF-8. E-3: a script that runs other engine scripts reads their output as UTF-8. E-4: the engine's child
processes (e.g. tests after an update) start in UTF-8 mode (PYTHONUTF8=1).
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
            fails.append(f"E-1: {p.relative_to(ROOT)} does not switch stdout/stderr to UTF-8")
        # E-4: child processes (tests after an update, build.py, hooks run from tests) in UTF-8 mode too —
        # otherwise a test printing “✓” to captured output or reading a file without encoding crashes on cp1250
        if p.parent == ENGINE and 'os.environ.setdefault("PYTHONUTF8", "1")' not in p.read_text(encoding="utf-8"):
            fails.append(f"E-4: {p.relative_to(ROOT)} does not enable UTF-8 mode (PYTHONUTF8) for child processes")
    env = {**os.environ, "PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0"}
    r = subprocess.run([sys.executable, str(ENGINE / "build.py"), "check"], cwd=ROOT, capture_output=True, env=env,
                       timeout=600)
    err = r.stderr.decode("utf-8", "replace")
    if "UnicodeEncodeError" in err:
        fails.append(f"E-2: build.py check under cp1250 → UnicodeEncodeError: {err[-400:]}")
    try:
        r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        fails.append("E-2: build.py check under cp1250 does not write UTF-8")
    # E-3: subprocess with text=True without encoding decodes with the system code page (cp1250) — Polish letters in UTF-8
    # (e.g. “Ł” = C5 81) fall apart or interrupt the read; we read the output of Python scripts as UTF-8
    call = re.compile(r"subprocess\.run\(\[sys\.executable[^\n]*(?:\n[^\n]*){0,2}")
    for p in sorted(ENGINE.glob("*.py")):
        for m in call.finditer(p.read_text(encoding="utf-8")):
            txt = m.group(0)
            if "text=True" in txt and "encoding=" not in txt:
                line = p.read_text(encoding="utf-8")[:m.start()].count("\n") + 1
                fails.append(f"E-3: {p.relative_to(ROOT)}:{line} reads Python output without encoding=\"utf-8\"")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} engine script encoding ({len(scripts())} scripts)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
