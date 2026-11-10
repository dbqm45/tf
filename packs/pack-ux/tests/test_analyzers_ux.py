#!/usr/bin/env python3
"""Moduł tf analyze z pack-ux (accessibility): obecny po instalacji i przechodzi bramkę na swoich zestawach
testowych. python3 .claude/tests/test_analyzers_ux.py"""
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
ANALYZE = ROOT / ".tf" / "factory" / "analyze.py"
MODS = ROOT / ".tf" / "factory" / "analyzers"


def main() -> int:
    fails, total = [], 0
    for name in ("accessibility",):
        total += 2
        if not (MODS / name / "analyzer.yaml").is_file():
            fails.append(f"U-1: moduł {name} zainstalowany w .tf/factory/analyzers/")
        r = subprocess.run([sys.executable, str(ANALYZE), "gate", "--module", name], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300)
        if not (r.returncode == 0 and r.stdout.startswith("Werdykt: OK")):
            fails.append(f"U-2: moduł {name} przechodzi bramkę: {r.stdout}{r.stderr}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów modułów analizy pack-ux")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
