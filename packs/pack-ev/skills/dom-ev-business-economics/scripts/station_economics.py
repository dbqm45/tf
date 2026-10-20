#!/usr/bin/env python3
"""
Ekonomia stacji ładowania: roczny rachunek wyników, NPV, okres zwrotu, marża na kWh, próg rentowności utilization
i wrażliwość. Tylko biblioteka standardowa. Sieć: brak. Model uproszczony do decyzji „czy liczyć dalej” — nie zastępuje
modelu finansowego (podatki, amortyzacja, finansowanie, inflacja i wzrost cen są poza zakresem).

  python3 .claude/skills/dom-ev-business-economics/scripts/station_economics.py <stacja.json> [--json]

<stacja.json> (kwoty netto w jednej walucie; nie ma tu cen rynkowych — wszystkie liczby podajesz sam, ze źródłem):
  years, discount_rate (np. 0.08), evse, avg_power_kw (średnia moc w czasie ładowania, nie moc nominalna),
  utilization (udział czasu ładowania w roku 0–1 albo lista na każdy rok), price_per_kwh, energy_cost_per_kwh,
  revenue_fees_pct (prowizje roamingu i płatności jako udział przychodu z ładowania), demand_charge_per_kw_month,
  contracted_kw (moc umowna), opex_per_year {pozycja: kwota}, capex {pozycja: kwota}, grants, other_revenue_per_year.

Rok: kWh = EVSE × 8760 × utilization × moc średnia; przychód = kWh × cena (+ przychód dodatkowy);
EBITDA = przychód − energia − prowizje − opłata za moc × moc umowna × 12 − OPEX. Rok 0: −(CAPEX − dotacje).
Kod wyjścia: 0 — NPV ≥ 0, 1 — NPV < 0, 2 — błąd wejścia.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

HOURS = 8760
REQUIRED = ("years", "evse", "avg_power_kw", "utilization", "price_per_kwh", "energy_cost_per_kwh")


class InputError(Exception):
    pass


def _num(d, key, default=None, lo=None, hi=None):
    v = d.get(key, default)
    if v is None:
        raise InputError(f"brak pola {key}")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise InputError(f"{key} musi być liczbą: {v!r}")
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise InputError(f"{key} poza zakresem {lo}…{hi}: {v}")
    return float(v)


def _sum(d, key):
    v = d.get(key) or {}
    if not isinstance(v, dict) or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in v.values()):
        raise InputError(f"{key} musi być obiektem {{pozycja: kwota}}")
    return float(sum(v.values()))


def _npv(d: dict) -> tuple[float, list[dict], float]:
    years = int(_num(d, "years", lo=1, hi=40))
    rate = _num(d, "discount_rate", 0.0, lo=0)
    evse = _num(d, "evse", lo=0)
    power = _num(d, "avg_power_kw", lo=0)
    price = _num(d, "price_per_kwh", lo=0)
    energy = _num(d, "energy_cost_per_kwh", lo=0)
    fees = _num(d, "revenue_fees_pct", 0.0, lo=0, hi=1)
    demand = _num(d, "demand_charge_per_kw_month", 0.0, lo=0) * _num(d, "contracted_kw", 0.0, lo=0) * 12
    other = _num(d, "other_revenue_per_year", 0.0, lo=0)
    opex = _sum(d, "opex_per_year")
    net_capex = _sum(d, "capex") - _num(d, "grants", 0.0, lo=0)
    u = d.get("utilization")
    util = u if isinstance(u, list) else [u] * years
    if len(util) != years:
        raise InputError(f"utilization: lista musi mieć {years} wartości (jest {len(util)})")
    rows, npv = [], -net_capex
    for k, uk in enumerate(util, start=1):
        if isinstance(uk, bool) or not isinstance(uk, (int, float)) or not 0 <= uk <= 1:
            raise InputError(f"utilization w roku {k} musi być liczbą 0–1: {uk!r}")
        kwh = evse * HOURS * uk * power
        charging = kwh * price
        row = {"year": k, "utilization": uk, "kwh": kwh, "revenue": charging + other, "energy_cost": kwh * energy,
               "fees": charging * fees, "demand_charges": demand, "opex": opex}
        row["ebitda"] = row["revenue"] - row["energy_cost"] - row["fees"] - demand - opex
        npv += row["ebitda"] / (1 + rate) ** k
        rows.append(row)
    return npv, rows, net_capex


def compute(d: dict) -> dict:
    if not isinstance(d, dict):
        raise InputError("wejście musi być obiektem JSON")
    for k in REQUIRED:
        if k not in d:
            raise InputError(f"brak pola {k}")
    npv, rows, net_capex = _npv(d)
    warnings = []
    if net_capex < 0:
        warnings.append({"code": "grants-exceed-capex", "msg": "dotacje większe niż CAPEX — sprawdź dane"})

    payback, cum = None, -net_capex
    for row in rows:
        if cum < 0 <= cum + row["ebitda"]:
            payback = row["year"] - 1 + (-cum / row["ebitda"])
            break
        cum += row["ebitda"]
    if payback is None and net_capex <= 0:
        payback = 0.0

    price, energy = float(d["price_per_kwh"]), float(d["energy_cost_per_kwh"])
    fees = float(d.get("revenue_fees_pct", 0))
    margin = price * (1 - fees) - energy
    y1 = rows[0]
    fixed = y1["demand_charges"] + y1["opex"] - float(d.get("other_revenue_per_year", 0))
    per_unit_util = float(d["evse"]) * HOURS * float(d["avg_power_kw"]) * margin
    breakeven = (fixed / per_unit_util if per_unit_util > 0 else None)
    if breakeven is not None and breakeven > 1:
        warnings.append({"code": "breakeven-above-100", "msg": "próg rentowności powyżej 100 % utilization — "
                         "przy tych cenach i kosztach stałych stacja nie zarobi na EBITDA"})
    full_cost = ((y1["energy_cost"] + y1["fees"] + y1["demand_charges"] + y1["opex"]) / y1["kwh"]) if y1["kwh"] else None

    def variant(fn):
        v = copy.deepcopy(d)
        fn(v)
        return round(_npv(v)[0], 2)

    def scale_util(v, f):
        u = v["utilization"]
        v["utilization"] = [min(1.0, x * f) for x in u] if isinstance(u, list) else min(1.0, u * f)

    sensitivity = {
        "utilization_x0.8": variant(lambda v: scale_util(v, 0.8)),
        "utilization_x1.2": variant(lambda v: scale_util(v, 1.2)),
        "price_x0.9": variant(lambda v: v.update(price_per_kwh=price * 0.9)),
        "price_x1.1": variant(lambda v: v.update(price_per_kwh=price * 1.1)),
        "energy_cost_x1.2": variant(lambda v: v.update(energy_cost_per_kwh=energy * 1.2)),
    }
    rnd = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items()} for row in rows]
    return {"net_capex": round(net_capex, 2), "npv": round(npv, 2),
            "payback_years": round(payback, 3) if payback is not None else None,
            "unit": {"margin_per_kwh": round(margin, 6), "full_cost_per_kwh": round(full_cost, 6) if full_cost else None},
            "breakeven_utilization": round(breakeven, 6) if breakeven is not None else None,
            "years": rnd, "sensitivity": sensitivity, "warnings": warnings}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Ekonomia stacji ładowania: EBITDA, NPV, zwrot, marża na kWh, próg utilization.")
    ap.add_argument("data", help="plik JSON z założeniami stacji")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        r = compute(json.loads(Path(args.data).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, InputError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"CAPEX netto {r['net_capex']:.2f} · NPV {r['npv']:.2f} · zwrot "
              f"{'brak w horyzoncie' if r['payback_years'] is None else str(r['payback_years']) + ' lat'}")
        print(f"  marża na kWh {r['unit']['margin_per_kwh']:.4f} · pełny koszt kWh "
              f"{'—' if r['unit']['full_cost_per_kwh'] is None else format(r['unit']['full_cost_per_kwh'], '.4f')} · próg "
              f"utilization {'—' if r['breakeven_utilization'] is None else format(r['breakeven_utilization'] * 100, '.2f') + ' %'}")
        print(f"  {'rok':>3} {'util.':>6} {'kWh':>10} {'przychód':>11} {'energia':>10} {'prowizje':>9} {'moc':>9} {'OPEX':>9} {'EBITDA':>10}")
        for y in r["years"]:
            print(f"  {y['year']:>3} {y['utilization'] * 100:>5.1f}% {y['kwh']:>10.0f} {y['revenue']:>11.2f} {y['energy_cost']:>10.2f} "
                  f"{y['fees']:>9.2f} {y['demand_charges']:>9.2f} {y['opex']:>9.2f} {y['ebitda']:>10.2f}")
        print("  wrażliwość NPV: " + ", ".join(f"{k} {v:.2f}" for k, v in r["sensitivity"].items()))
        for w in r["warnings"]:
            print(f"  ⚠ [{w['code']}] {w['msg']}")
    return 0 if r["npv"] >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
