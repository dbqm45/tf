#!/usr/bin/env python3
"""
Przykład: taryfa → CDR → CDR kredytowy → nowy CDR → rozliczenie po stronie eMSP (OCPI 2.2.1). Dydaktyczny, nie
produkcja. Tylko biblioteka standardowa (+ ocpi_tariff_calc.py ze skilla dom-ev-tariffs-pricing).

  python3 examples/ocpi-tariff-cdr/cdr_flow.py make <taryfa.json> <sesja.json> --id CDR-1 [--tz Europe/Warsaw]
  python3 examples/ocpi-tariff-cdr/cdr_flow.py credit <cdr.json> [--suffix -C]
  python3 examples/ocpi-tariff-cdr/cdr_flow.py correct <cdr.json> <taryfa.json> [--tz Europe/Warsaw]

Zasady (OCPI 2.2.1-d2, mod_cdrs „Credit CDRs”): CDR się nie zmienia ani nie usuwa; korekta to CDR kredytowy z nowym
`id`, `credit: true`, `credit_reference_id` = id oryginału, wszystkimi danymi oryginału i ujemnym tylko `total_cost`;
potem nowy CDR z nowym `id`, bez pól `credit`.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
_spec = importlib.util.spec_from_file_location(
    "ocpi_tariff_calc", ROOT / ".claude" / "skills" / "dom-ev-tariffs-pricing" / "scripts" / "ocpi_tariff_calc.py")
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)

SESSION_FIELDS = ("country_code", "party_id", "start_date_time", "end_date_time", "cdr_token", "auth_method",
                  "cdr_location")
COST_FIELDS = ("total_cost", "total_fixed_cost", "total_energy", "total_energy_cost", "total_time", "total_time_cost",
               "total_parking_time", "total_parking_cost")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_cdr(tariff: dict, session: dict, cdr_id: str, tz: str = "UTC") -> dict:
    """CDR z sesji i taryfy; koszty z kalkulatora. Taryfa kopiowana do CDR (stan z chwili sesji)."""
    r = calc.calculate(tariff, session, tz)
    cdr = {k: session[k] for k in SESSION_FIELDS if k in session}
    cdr.update(id=cdr_id, session_id=session.get("id"), currency=tariff["currency"], tariffs=[copy.deepcopy(tariff)],
               charging_periods=copy.deepcopy(session["charging_periods"]))
    cdr.update({k: r[k] for k in COST_FIELDS})
    cdr["last_updated"] = session["end_date_time"]
    return cdr


def credit_cdr(cdr: dict, suffix: str = "-C", now: str | None = None) -> dict:
    """CDR kredytowy: dane oryginału, nowe id, credit, credit_reference_id i ujemny tylko total_cost."""
    credit = copy.deepcopy(cdr)
    credit.update(id=cdr["id"] + suffix, credit=True, credit_reference_id=cdr["id"], last_updated=now or _now(),
                  total_cost={k: -v for k, v in cdr["total_cost"].items()})
    return credit


def correct(cdr: dict, tariff: dict, tz: str = "UTC", new_id: str | None = None) -> tuple[dict, dict]:
    """Korekta: (CDR kredytowy dla `cdr`, nowy CDR policzony z poprawionej taryfy)."""
    session = {k: cdr[k] for k in SESSION_FIELDS if k in cdr}
    session.update(id=cdr.get("session_id"), charging_periods=cdr["charging_periods"])
    new = make_cdr(tariff, session, new_id or cdr["id"] + "-R1", tz)
    new["last_updated"] = _now()
    return credit_cdr(cdr), new


class EmspLedger:
    """Strona eMSP: odbiór CDR idempotentny po (country_code, party_id, id); kredyt tylko do znanego, nieskredytowanego CDR."""

    def __init__(self):
        self.cdrs: dict[tuple, dict] = {}
        self.credited: set[str] = set()

    def receive(self, cdr: dict) -> str:
        key = (cdr["country_code"], cdr["party_id"], cdr["id"])
        if key in self.cdrs:
            return "duplicate"
        if cdr.get("credit"):
            ref = cdr.get("credit_reference_id")
            if (cdr["country_code"], cdr["party_id"], ref) not in self.cdrs:
                return f"rejected: credit_reference_id {ref} nieznany"
            if ref in self.credited:
                return f"rejected: {ref} już skredytowany"
            self.credited.add(ref)
        self.cdrs[key] = cdr
        return "accepted"

    def balance(self) -> dict:
        total = {"excl_vat": Decimal(0), "incl_vat": Decimal(0)}
        for c in self.cdrs.values():
            for k in total:
                total[k] += Decimal(str(c["total_cost"][k]))
        return {k: float(v) for k, v in total.items()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Przykład OCPI: taryfa → CDR → CDR kredytowy → nowy CDR.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("tariff"), m.add_argument("session"), m.add_argument("--id", required=True), m.add_argument("--tz", default="UTC")
    c = sub.add_parser("credit")
    c.add_argument("cdr"), c.add_argument("--suffix", default="-C")
    k = sub.add_parser("correct")
    k.add_argument("cdr"), k.add_argument("tariff"), k.add_argument("--tz", default="UTC")
    args = ap.parse_args(argv)
    try:
        read = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
        if args.cmd == "make":
            out = make_cdr(read(args.tariff), read(args.session), args.id, args.tz)
        elif args.cmd == "credit":
            out = credit_cdr(read(args.cdr), args.suffix)
        else:
            out = list(correct(read(args.cdr), read(args.tariff), args.tz))
    except (OSError, json.JSONDecodeError, KeyError, calc.InputError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
