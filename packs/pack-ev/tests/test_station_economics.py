#!/usr/bin/env python3
"""Testy kalkulatora ekonomii stacji ładowania (skill dom-ev-business-economics): energia z liczby EVSE, utilization
i średniej mocy, przychód, koszt energii, opłata za moc, prowizje, OPEX, EBITDA, NPV, okres zwrotu, marża na kWh,
pełny koszt kWh, próg rentowności utilization, wrażliwość, walidacja i kody wyjścia.

Wartości oczekiwane policzone ręcznie w komentarzach. Kalkulator nie zawiera cen rynkowych — wszystkie liczby
przychodzą z wejścia.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-business-economics" / "scripts" / "station_economics.py"

# 2 EVSE × 8760 h × 10 % × 50 kW = 87 600 kWh/rok
# przychód 87 600 × 0,50 = 43 800; energia 87 600 × 0,20 = 17 520; prowizje 10 % × 43 800 = 4 380
# opłata za moc 10 /kW/mies. × 100 kW × 12 = 12 000; OPEX stały 5 000 → EBITDA 4 900
# CAPEX 20 000 − dotacja 5 000 = 15 000
BASE = {
    "years": 4, "discount_rate": 0.0, "evse": 2, "avg_power_kw": 50, "utilization": 0.10,
    "price_per_kwh": 0.50, "energy_cost_per_kwh": 0.20, "revenue_fees_pct": 0.10,
    "demand_charge_per_kw_month": 10, "contracted_kw": 100,
    "opex_per_year": {"maintenance": 3000, "software": 1200, "connectivity": 800},
    "capex": {"chargers": 14000, "grid_connection": 4000, "civil": 2000}, "grants": 5000,
}


def load():
    spec = importlib.util.spec_from_file_location("station_economics", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def near(a, b, eps=0.01):
    return a is not None and abs(a - b) <= eps


def main() -> int:
    if not SCRIPT.exists():
        print(f"✗ brak {SCRIPT.relative_to(ROOT)}")
        return 1
    m = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    r = m.compute(BASE)
    y1 = r["years"][0]
    check(near(y1["kwh"], 87600) and near(y1["revenue"], 43800) and near(y1["energy_cost"], 17520),
          f"E-1: energia, przychód i koszt energii w roku 1: {y1}")
    check(near(y1["fees"], 4380) and near(y1["demand_charges"], 12000) and near(y1["opex"], 5000),
          f"E-2: prowizje, opłata za moc i OPEX: {y1}")
    check(near(y1["ebitda"], 4900), f"E-3: EBITDA = 4 900: {y1}")
    check(near(r["net_capex"], 15000), f"E-4: CAPEX netto po dotacji: {r['net_capex']}")
    check(near(r["npv"], -15000 + 4 * 4900), f"E-5: NPV przy stopie 0 = 4 600: {r['npv']}")
    check(near(r["payback_years"], 3 + 300 / 4900, 0.001), f"E-6: okres zwrotu 3,061 roku (interpolacja): {r['payback_years']}")
    check(near(r["unit"]["margin_per_kwh"], 0.25, 1e-6), f"E-7: marża na kWh = 0,50 × (1 − 10 %) − 0,20: {r['unit']}")
    check(near(r["unit"]["full_cost_per_kwh"], 38900 / 87600, 1e-4),
          f"E-8: pełny koszt kWh (energia + prowizje + moc + OPEX) / kWh: {r['unit']}")
    check(near(r["breakeven_utilization"], 17000 / 219000, 1e-5),
          f"E-9: próg rentowności utilization dla EBITDA = 0 ≈ 7,76 %: {r['breakeven_utilization']}")

    d = copy.deepcopy(BASE)
    d["discount_rate"] = 0.10
    r10 = m.compute(d)
    annuity = sum(1 / 1.1 ** k for k in range(1, 5))
    check(near(r10["npv"], -15000 + 4900 * annuity), f"E-10: NPV przy 10 % ≈ 532,34: {r10['npv']}")

    d = copy.deepcopy(BASE)
    d["years"] = 3
    r3 = m.compute(d)
    check(r3["payback_years"] is None and near(r3["npv"], -300), f"E-11: brak zwrotu w horyzoncie 3 lat, NPV −300: {r3['npv']} {r3['payback_years']}")

    d = copy.deepcopy(BASE)
    d.update(years=2, utilization=[0.05, 0.10])
    r2 = m.compute(d)
    check(near(r2["years"][0]["kwh"], 43800) and near(r2["years"][1]["kwh"], 87600),
          f"E-12: utilization jako lista na każdy rok: {[y['kwh'] for y in r2['years']]}")

    d = copy.deepcopy(BASE)
    d["other_revenue_per_year"] = 1000
    check(near(m.compute(d)["years"][0]["ebitda"], 5900), "E-13: przychód dodatkowy (sklep, reklama) bez prowizji ładowania")

    s = r["sensitivity"]
    check(near(s["utilization_x1.2"], -15000 + 4 * (4900 + 0.2 * 21900)),
          f"E-14: wrażliwość: utilization × 1,2 → NPV 22 120: {s}")
    check(near(s["price_x0.9"], -15000 + 4 * (4900 - 0.1 * 43800 * 0.9)),
          f"E-15: wrażliwość: cena × 0,9 (prowizje maleją razem z przychodem): {s}")
    check(near(s["energy_cost_x1.2"], -15000 + 4 * (4900 - 0.2 * 17520)), f"E-16: wrażliwość: koszt energii × 1,2: {s}")

    d = copy.deepcopy(BASE)
    d["demand_charge_per_kw_month"] = 0
    d["contracted_kw"] = 0
    check(near(m.compute(d)["years"][0]["ebitda"], 16900), "E-17: bez opłaty za moc EBITDA rośnie o 12 000")

    for key, val, why in (("utilization", 1.5, "utilization > 1"), ("utilization", [0.1], "lista krótsza niż years"),
                          ("years", 0, "years < 1"), ("evse", -1, "ujemna liczba EVSE"), ("discount_rate", -0.1, "ujemna stopa"),
                          ("revenue_fees_pct", 1.2, "prowizja > 100 %")):
        d = copy.deepcopy(BASE)
        d[key] = val
        try:
            m.compute(d)
            check(False, f"V: {why} → InputError")
        except m.InputError:
            check(True, "")
    d = copy.deepcopy(BASE)
    d.pop("price_per_kwh")
    try:
        m.compute(d)
        check(False, "V: brak price_per_kwh → InputError")
    except m.InputError:
        check(True, "")
    d = copy.deepcopy(BASE)
    d["grants"] = 30000
    check(any(w["code"] == "grants-exceed-capex" for w in m.compute(d)["warnings"]),
          "V: dotacja większa niż CAPEX → ostrzeżenie")

    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "in.json"
        f.write_text(json.dumps(BASE), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        check(p.returncode == 0 and "4600" in p.stdout.replace(" ", "").replace(",", ""),
              f"CLI-1: NPV ≥ 0 → kod 0, NPV w wyniku: {p.returncode} {p.stdout[-400:]} {p.stderr[-200:]}")
        d = copy.deepcopy(BASE)
        d["years"] = 3
        f.write_text(json.dumps(d), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        check(p.returncode == 1, f"CLI-2: NPV < 0 → kod 1: {p.returncode}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f), "--json"], capture_output=True, text=True)
        try:
            check(near(json.loads(p.stdout)["npv"], -300), "CLI-3: --json z NPV")
        except (ValueError, KeyError) as e:
            check(False, f"CLI-3: --json zwraca JSON: {e}")
        f.write_text("{}", encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        check(p.returncode == 2, f"CLI-4: kod 2 przy błędnym wejściu: {p.returncode}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów station_economics nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów station_economics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
