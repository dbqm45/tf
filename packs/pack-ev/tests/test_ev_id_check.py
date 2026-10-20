#!/usr/bin/env python3
"""Testy walidatora identyfikatorów EV (skill dom-ev-identifiers): składnia EVSE ID i EMAID, normalizacja, kody wyjścia."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-identifiers" / "scripts" / "ev_id_check.py"


def load():
    spec = importlib.util.spec_from_file_location("ev_id_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    m = load()

    # EVSE ID: z separatorem i bez, normalizacja do wielkich liter z `*`
    r = m.check("SK*IOY*E222901")
    check(r["type"] == "evse" and r["valid"] and r["normalized"] == "SK*IOY*E222901"
          and r["parts"] == {"country": "SK", "operator": "IOY", "evse": "222901"}, f"EV-1: EVSE z separatorem: {r}")
    r = m.check("pl123e45a")
    check(r["type"] == "evse" and r["valid"] and r["normalized"] == "PL*123*E45A", f"EV-2: EVSE bez separatora, małe litery: {r}")
    r = m.check("PL*ABC*E12*1", "evse")
    check(r["valid"] and r["parts"]["evse"] == "12*1", f"EV-3: `*` dozwolona w ID punktu: {r}")
    r = m.check("P1*ABC*E1", "evse")
    check(not r["valid"] and any("kraj" in e for e in r["errors"]), f"EV-4: kod kraju z cyfrą → błąd: {r}")
    r = m.check("PL*AB*E1", "evse")
    check(not r["valid"], f"EV-5: operator 2 znaki → błąd: {r}")
    r = m.check("PL*ABC*E" + "1" * 32, "evse")
    check(not r["valid"], f"EV-6: ID punktu > 31 znaków → błąd: {r}")
    r = m.check("PL*ABC*X123", "evse")
    check(not r["valid"] and any("E" in e for e in r["errors"]), f"EV-7: brak litery E przed ID punktu → błąd: {r}")

    # EMAID: separatory `-` lub `*`, cyfra kontrolna opcjonalna i niesprawdzana
    r = m.check("NL-TNM-000122045-U")
    check(r["type"] == "emaid" and r["valid"] and r["normalized"] == "NL-TNM-000122045-U"
          and r["parts"] == {"country": "NL", "provider": "TNM", "instance": "000122045", "check_digit": "U"}
          and any("cyfra kontrolna niesprawdzana" in w for w in r["warnings"]), f"EM-1: EMAID z cyfrą kontrolną: {r}")
    r = m.check("nltnm000122045", "emaid")
    check(r["valid"] and r["normalized"] == "NL-TNM-000122045" and r["parts"]["check_digit"] is None
          and any("bez cyfry kontrolnej" in w for w in r["warnings"]), f"EM-2: EMAID bez cyfry kontrolnej i separatorów: {r}")
    r = m.check("NL*TNM*000122045*U", "emaid")
    check(r["valid"] and r["normalized"] == "NL-TNM-000122045-U", f"EM-3: separator `*` w EMAID: {r}")
    r = m.check("NL-TNM*000122045-U", "emaid")
    check(not r["valid"] and any("separator" in e for e in r["errors"]), f"EM-4: mieszane separatory → błąd: {r}")
    r = m.check("NL-TNM-00012204-U", "emaid")
    check(not r["valid"], f"EM-5: instancja 8 znaków → błąd: {r}")

    # Typ automatyczny: `-` → EMAID; niejednoznaczne → ostrzeżenie
    r = m.check("DE-ABC-E12345678")
    check(r["type"] == "emaid" and r["valid"], f"AU-1: `-` rozstrzyga na EMAID: {r}")
    r = m.check("DE*ABC*E12345678")
    check(r["type"] == "evse" and r["valid"] and any("niejednoznaczn" in w for w in r["warnings"]),
          f"AU-2: pasuje do obu formatów → EVSE z ostrzeżeniem: {r}")
    r = m.check("to nie jest id")
    check(r["type"] is None and not r["valid"] and r["errors"], f"AU-3: nieznany format → błąd: {r}")

    # Długość jak OCPI CiString(48)
    r = m.check("PL*ABC*E" + "1" * 31 + "*" * 10, "evse")
    check(not r["valid"] and any("48" in e for e in r["errors"]), f"LEN-1: > 48 znaków → błąd: {r}")

    # Wiersz poleceń: JSON i kody wyjścia
    p = run("SK*IOY*E222901", "NL-TNM-000122045-U", "--json")
    data = json.loads(p.stdout) if p.stdout.strip().startswith("[") else None
    check(p.returncode == 0 and data and len(data) == 2 and all(x["valid"] for x in data), f"CLI-1: JSON, kod 0: {p.returncode} {p.stdout[:300]}")
    p = run("SK*IOY*E222901", "zle")
    check(p.returncode == 1 and "zle" in p.stdout, f"CLI-2: niepoprawne ID → kod 1: {p.returncode} {p.stdout[:300]}")
    p = run("--type", "nieznany", "X")
    check(p.returncode == 2, f"CLI-3: zły argument → kod 2: {p.returncode}")
    p = run()
    check(p.returncode == 2, f"CLI-4: brak ID → kod 2: {p.returncode}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów walidatora identyfikatorów EV nie przeszło:")
        for f in fails:
            print("  -", f)
        return 1
    print(f"✓ {total}/{total} testów walidatora identyfikatorów EV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
