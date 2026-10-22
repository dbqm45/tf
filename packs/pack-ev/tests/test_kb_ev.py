#!/usr/bin/env python3
"""Testy rejestru źródeł EV (skill dom-ev-knowledge-base) na mechanizmie bazy wiedzy rdzenia (core-knowledge):
rejestr poprawny i z deklaracją obszarów, zgodność starej ścieżki `kb.py`, wyszukiwanie w skillach EV."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SKILLS = ROOT / ".claude" / "skills"
CORE_KB = SKILLS / "core-knowledge" / "scripts" / "kb.py"
OLD_KB = SKILLS / "dom-ev-knowledge-base" / "scripts" / "kb.py"
REGISTRY = SKILLS / "dom-ev-knowledge-base" / "references" / "zrodla.json"


def load():
    spec = importlib.util.spec_from_file_location("kb", CORE_KB)
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

    kb = load()
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    reg = kb.load_registry(REGISTRY)
    errs = kb.validate_registry(data["sources"], set(data.get("areas") or []))
    check(not errs and len(reg) >= 15, f"R-1: rejestr EV poprawny i ≥ 15 źródeł: {errs} {len(reg)}")
    check({"ocpp", "ocpi", "regulations-eu", "regulations-pl", "regulations-us"} <= set(data.get("areas") or []),
          f"R-2: obszary zadeklarowane w rejestrze: {data.get('areas')}")
    check(kb.validate_registries(ROOT) == [], f"R-3: rejestry całej fabryki razem: {kb.validate_registries(ROOT)}")

    # Stara ścieżka skryptu przekierowuje do rdzenia
    p = subprocess.run([sys.executable, str(OLD_KB), "sources", "--area", "ocpi", "--root", str(ROOT)],
                       capture_output=True, text=True)
    check(p.returncode == 0 and "ocpi" in p.stdout.lower(), f"OLD-1: stara ścieżka kb.py działa: {p.returncode} {p.stderr[-300:]}")

    # Pytanie o korektę CDR trafia w skill rozliczeń
    hits = kb.search("korekta CDR kredytowy credit_reference_id", ROOT, k=3)
    check(any("dom-ev-cdr-settlement" in h["path"] for h in hits), f"REAL-1: baza fabryki → dom-ev-cdr-settlement: {[h['path'] for h in hits]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów rejestru EV nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów rejestru EV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
