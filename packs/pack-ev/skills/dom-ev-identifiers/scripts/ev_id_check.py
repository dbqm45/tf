#!/usr/bin/env python3
"""
Walidator składni identyfikatorów EV: EVSE ID i EMAID (Contract ID). Tylko biblioteka standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-identifiers/scripts/ev_id_check.py <ID> [<ID> ...] [--type auto|evse|emaid] [--json]

Kod wyjścia: 0 — wszystkie ID poprawne, 1 — co najmniej jedno niepoprawne, 2 — błąd wywołania.

Sprawdza wyłącznie SKŁADNIĘ. Nie sprawdza, czy operator lub dostawca istnieje w rejestrze, ani cyfry kontrolnej
EMAID — algorytm z ISO 15118-2 nie jest opisany w publicznie dostępnych źródłach (stan 2026-10-20; walidator
referencyjny: ochp.eu/id-validator).

Reguły (źródła i poziom pewności: references/formaty.md skilla dom-ev-identifiers):
  EVSE ID  kraj (2 litery, ISO 3166-1 alpha-2) + operator (3 znaki alfanumeryczne) + „E” + ID punktu
           (1–31 znaków alfanumerycznych lub `*`); separator `*` opcjonalny; postać znormalizowana z `*`.
  EMAID    kraj (2 litery) + dostawca (3 alfanumeryczne) + instancja (9 alfanumerycznych) + opcjonalna cyfra
           kontrolna (1 znak); separator `-` albo `*` (jeden rodzaj), opcjonalny; postać znormalizowana z `-`.
  Oba      najwyżej 48 znaków (OCPI 2.2.1: `evse_id` CiString(48)); wielkość liter bez znaczenia.
Długości ID punktu i instancji pochodzą ze źródeł wtórnych — [do weryfikacji] w ISO 15118-2 Annex H.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

MAX_LEN = 48
COUNTRY = re.compile(r"[A-Z]{2}")
PARTY = re.compile(r"[A-Z0-9]{3}")
POINT = re.compile(r"[A-Z0-9][A-Z0-9*]{0,30}")
INSTANCE = re.compile(r"[A-Z0-9]{9}")
CHECK_DIGIT = re.compile(r"[A-Z0-9]")
NO_CHECK = "cyfra kontrolna niesprawdzana — algorytm z ISO 15118-2 nie jest publicznie opisany"


def _result(raw: str, kind: str | None, errors: list[str], parts: dict | None = None,
            normalized: str | None = None, warnings: list[str] | None = None) -> dict:
    return {"id": raw, "type": kind, "valid": not errors, "normalized": normalized if not errors else None,
            "parts": parts if not errors else None, "errors": errors, "warnings": warnings or []}


def _length_errors(s: str) -> list[str]:
    return [f"dłuższy niż {MAX_LEN} znaków ({len(s)}) — OCPI 2.2.1 `evse_id` to CiString({MAX_LEN})"] if len(s) > MAX_LEN else []


def check_evse(raw: str) -> dict:
    s = raw.strip().upper()
    errors = _length_errors(s)
    if "*" in s:
        country, _, rest = s.partition("*")
        operator, _, tail = rest.partition("*")
    else:
        country, operator, tail = s[:2], s[2:5], s[5:]
    if not COUNTRY.fullmatch(country):
        errors.append(f"kod kraju „{country}”: oczekiwane 2 litery (ISO 3166-1 alpha-2)")
    if not PARTY.fullmatch(operator):
        errors.append(f"ID operatora „{operator}”: oczekiwane 3 znaki alfanumeryczne")
    point = tail[1:]
    if not tail.startswith("E"):
        errors.append("brak litery „E” przed ID punktu ładowania")
    elif not POINT.fullmatch(point):
        errors.append(f"ID punktu „{point}”: oczekiwane 1–31 znaków alfanumerycznych lub `*`, zaczynające się od znaku alfanumerycznego")
    return _result(raw, "evse", errors, {"country": country, "operator": operator, "evse": point},
                   f"{country}*{operator}*E{point}")


def check_emaid(raw: str) -> dict:
    s = raw.strip().upper()
    errors = _length_errors(s)
    seps = {c for c in s if c in "-*"}
    if len(seps) > 1:
        return _result(raw, "emaid", errors + ["mieszane separatory `-` i `*` — w jednym EMAID używa się jednego rodzaju"])
    if seps:
        fields = s.split(seps.pop())
        if len(fields) not in (3, 4):
            return _result(raw, "emaid", errors + [f"oczekiwane 3 lub 4 części rozdzielone separatorem, jest {len(fields)}"])
        country, provider, instance = fields[:3]
        check = fields[3] if len(fields) == 4 else None
    else:
        if len(s) not in (14, 15):
            return _result(raw, "emaid", errors + [f"bez separatorów oczekiwane 14 lub 15 znaków, jest {len(s)}"])
        country, provider, instance = s[:2], s[2:5], s[5:14]
        check = s[14:] or None
    if not COUNTRY.fullmatch(country):
        errors.append(f"kod kraju „{country}”: oczekiwane 2 litery (ISO 3166-1 alpha-2)")
    if not PARTY.fullmatch(provider):
        errors.append(f"ID dostawcy „{provider}”: oczekiwane 3 znaki alfanumeryczne")
    if not INSTANCE.fullmatch(instance):
        errors.append(f"instancja „{instance}”: oczekiwane 9 znaków alfanumerycznych")
    if check is not None and not CHECK_DIGIT.fullmatch(check):
        errors.append(f"cyfra kontrolna „{check}”: oczekiwany 1 znak alfanumeryczny")
    warnings = [NO_CHECK] if check else ["bez cyfry kontrolnej (dozwolone; wymóg zależy od eMSP i partnera)"]
    normalized = "-".join([country, provider, instance] + ([check] if check else []))
    return _result(raw, "emaid", errors, {"country": country, "provider": provider, "instance": instance,
                                          "check_digit": check}, normalized, warnings)


def check(raw: str, kind: str = "auto") -> dict:
    if kind == "evse":
        return check_evse(raw)
    if kind == "emaid":
        return check_emaid(raw)
    if "-" in raw:
        return check_emaid(raw)
    evse, emaid = check_evse(raw), check_emaid(raw)
    if evse["valid"] and emaid["valid"]:
        evse["warnings"].append("niejednoznaczny: pasuje też do EMAID — podaj --type emaid, jeśli to kontrakt")
        return evse
    if evse["valid"] or emaid["valid"]:
        return evse if evse["valid"] else emaid
    return _result(raw, None, ["nie pasuje do formatu EVSE ID ani EMAID"]
                   + [f"EVSE: {e}" for e in evse["errors"]] + [f"EMAID: {e}" for e in emaid["errors"]])


def describe(r: dict) -> str:
    if r["valid"]:
        line = f"✓ {r['id']} → {r['type'].upper()} {r['normalized']} ({', '.join(f'{k}={v}' for k, v in r['parts'].items() if v)})"
    else:
        line = f"✗ {r['id']}: " + "; ".join(r["errors"])
    return line + "".join(f"\n    ⚠ {w}" for w in r["warnings"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Walidator składni EVSE ID i EMAID (bez sieci, bez cyfry kontrolnej).")
    ap.add_argument("ids", nargs="+", metavar="ID")
    ap.add_argument("--type", choices=["auto", "evse", "emaid"], default="auto")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON (lista)")
    args = ap.parse_args(argv)
    results = [check(i, args.type) for i in args.ids]
    print(json.dumps(results, ensure_ascii=False, indent=1) if args.json else "\n".join(describe(r) for r in results))
    return 0 if all(r["valid"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
