#!/usr/bin/env python3
"""Testy kalkulatora taryf OCPI 2.2.1 (skill dom-ev-tariffs-pricing): przykłady liczbowe ze specyfikacji, restrykcje,
step_size, VAT, min/max_price, porównanie z CDR, kody wyjścia.

Taryfy przepisane z przykładów OCPI 2.2.1-d2 (github.com/ocpi/ocpi, tag v2.2.1-d2, examples/*.json, dostęp 2026-10-20).
Uwaga: część przykładów liczbowych w specyfikacji jest wewnętrznie sprzeczna (tariff_14 „free of charge”: 0,78 € w 2.2.1,
0,80 € w d2, przy cenach z taryfy wychodzi 0,73 €; tariff_4 sobota: 2,28 € zamiast 114 min × 1,25 €/h = 2,375 €).
Testy sprawdzają regułę z tekstu specyfikacji (mod_cdrs „step_size”, mod_tariffs d2), nie błędną arytmetykę.
"""
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-tariffs-pricing" / "scripts" / "ocpi_tariff_calc.py"


def load():
    spec = importlib.util.spec_from_file_location("ocpi_tariff_calc", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pc(type_, price, step=1, vat=None):
    c = {"type": type_, "price": price, "step_size": step}
    if vat is not None:
        c["vat"] = vat
    return c


def tariff(*elements, **extra):
    return {"country_code": "PL", "party_id": "EVT", "id": "T1", "currency": "EUR",
            "elements": [{"price_components": list(comps), **({"restrictions": r} if r else {})} for comps, r in elements],
            "last_updated": "2026-10-20T00:00:00Z", **extra}


def session(start: str, *periods):
    """periods: (minuty, {wymiar: wolumen}) — TIME i PARKING_TIME podawane w minutach, reszta w jednostkach OCPI."""
    t = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    out = []
    for minutes, dims in periods:
        d = []
        for k, v in dims.items():
            d.append({"type": k, "volume": round(v / 60, 6) if k in ("TIME", "PARKING_TIME") else v})
        out.append({"start_date_time": t.isoformat().replace("+00:00", "Z"), "dimensions": d})
        t += dt.timedelta(minutes=minutes)
    return {"start_date_time": out[0]["start_date_time"], "end_date_time": t.isoformat().replace("+00:00", "Z"),
            "charging_periods": out}


T14 = tariff(([pc("TIME", 1.20, 1800), pc("PARKING_TIME", 1.00, 900)], {"start_time": "00:00", "end_time": "17:00"}),
             ([pc("TIME", 2.40, 900), pc("PARKING_TIME", 1.00, 900)], {"start_time": "17:00", "end_time": "20:00"}),
             ([pc("TIME", 2.40, 900)], {"start_time": "20:00", "end_time": "00:00"}))
WD = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
T4 = tariff(([pc("FLAT", 2.50, 1, 15.0)], None),
            ([pc("TIME", 1.00, 900, 20.0)], {"max_current": 32.0}),
            ([pc("TIME", 2.00, 600, 20.0)], {"min_current": 32.0, "day_of_week": WD}),
            ([pc("TIME", 1.25, 600, 20.0)], {"min_current": 32.0, "day_of_week": ["SATURDAY", "SUNDAY"]}),
            ([pc("PARKING_TIME", 5.0, 300, 10.0)], {"start_time": "09:00", "end_time": "18:00", "day_of_week": WD}),
            ([pc("PARKING_TIME", 6.0, 300, 10.0)], {"start_time": "10:00", "end_time": "17:00", "day_of_week": ["SATURDAY"]}))


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    def cost(r, key="total_cost"):
        return (r[key]["excl_vat"], r[key]["incl_vat"]) if r.get(key) else None

    m = load()

    # Przykład CDR ze specyfikacji: 1,973 h × 2 €/h, step_size 300 s → 2 h → 4,00 €, VAT 10 % → 4,40 €
    t_cdr = tariff(([pc("TIME", 2.0, 300, 10.0)], None))
    s_cdr = {"start_date_time": "2015-06-29T21:39:09Z", "end_date_time": "2015-06-29T23:37:32Z",
             "charging_periods": [{"start_date_time": "2015-06-29T21:39:09Z", "dimensions": [{"type": "TIME", "volume": 1.973}]}]}
    r = m.calculate(t_cdr, s_cdr)
    check(cost(r) == (4.0, 4.4) and cost(r, "total_time_cost") == (4.0, 4.4), f"SPEC-1: przykład CDR 4,00/4,40: {cost(r)}")
    check(abs(r["total_time"] - 1.9731) < 0.001, f"SPEC-2: total_time = cała sesja (h): {r['total_time']}")

    # tariff_14: przełączanie elementów i step_size
    r = m.calculate(T14, session("2026-10-20T16:35:00Z", (25, {"TIME": 25}), (10, {"TIME": 10})))
    check(cost(r) == (1.3, 1.3), f"STEP-1: przykład #2 — TIME 35 → 45 min, 25 min po 1,20 + 20 min po 2,40 = 1,30: {cost(r)}")
    r = m.calculate(T14, session("2026-10-20T16:55:00Z", (5, {"TIME": 5}), (5, {"TIME": 5}), (2, {"PARKING_TIME": 2})))
    check(cost(r) == (0.55, 0.55) and cost(r, "total_parking_cost") == (0.25, 0.25),
          f"STEP-2: przykład #1 (d2) — TIME bez zaokrąglenia, postój 2 → 15 min = 0,55: {cost(r)}")
    r = m.calculate(T14, session("2026-10-20T19:40:00Z", (12, {"TIME": 12}), (8, {"PARKING_TIME": 8}),
                                 (12, {"PARKING_TIME": 12})))
    check(cost(r) == (0.73, 0.73) and cost(r, "total_parking_cost") == (0.25, 0.25),
          f"STEP-3: postój darmowy po 20:00 — płatne 8 min → 15 min po 1,00 €/h; TIME 12 min po 2,40: {cost(r)}")
    check(r["total_parking_time"] == 0.3333, f"STEP-4: total_parking_time to czas faktyczny, nie zaokrąglony: {r['total_parking_time']}")
    r = m.calculate(tariff(([pc("PARKING_TIME", 1.00, 300)], None)), session("2026-10-20T19:00:00Z", (20, {"TIME": 20}),
                                                                       (40, {"PARKING_TIME": 40})))
    check(cost(r, "total_parking_cost") == (0.6667, 0.6667), f"STEP-6: 40 min jako 0,666667 h nie daje dodatkowego kroku: {cost(r, 'total_parking_cost')}")
    r = m.calculate(tariff(([pc("ENERGY", 0.25, 500)], None)), session("2026-10-20T10:00:00Z", (10, {"ENERGY": 0.1})))
    check(cost(r) == (0.125, 0.125), f"STEP-5: ENERGY step_size 500 Wh: 0,1 kWh → 0,5 kWh × 0,25 = 0,125: {cost(r)}")

    # tariff_4_complex: FLAT, restrykcje prądu, dni tygodnia i godzin, VAT per składnik
    r = m.calculate(T4, session("2026-10-19T09:30:00Z", (165, {"TIME": 165, "MAX_CURRENT": 16}), (42, {"PARKING_TIME": 42})))
    check(cost(r) == (9.0, 10.3) and cost(r, "total_fixed_cost") == (2.5, 2.875),
          f"CPLX-1: poniedziałek 09:30, 16 A, postój 42 → 45 min: 9,00 / 10,30: {cost(r)}")
    r = m.calculate(T4, session("2026-10-24T13:30:00Z", (114, {"TIME": 114, "MIN_CURRENT": 43, "MAX_CURRENT": 43}),
                                (71, {"PARKING_TIME": 71})))
    check(cost(r) == (12.375, 13.975), f"CPLX-2: sobota 13:30, 43 A, postój 71 → 75 min: 12,375 / 13,975: {cost(r)}")
    r = m.calculate(T4, session("2026-10-21T10:00:00Z", (60, {"TIME": 60, "MIN_CURRENT": 40, "MAX_CURRENT": 40})))
    check(cost(r) == (4.5, 5.275), f"CPLX-3: środa, 40 A → TIME 2,00 €/h + FLAT: {cost(r)}")

    # Restrykcje mocy i czasu trwania (przykłady z mod_tariffs)
    t_pow = tariff(([pc("ENERGY", 0.20, 1, 20.0)], {"max_power": 16.0}), ([pc("ENERGY", 0.35, 1, 20.0)], {"max_power": 32.0}),
                   ([pc("ENERGY", 0.50, 1, 20.0)], None))
    r = m.calculate(t_pow, session("2026-10-20T10:00:00Z", (10, {"ENERGY": 1, "MAX_POWER": 6}), (50, {"ENERGY": 40, "MAX_POWER": 48}),
                                   (8, {"ENERGY": 0.5, "MAX_POWER": 4})))
    check(cost(r) == (20.3, 24.36), f"RES-1: max_power — 1 kWh po 0,20 + 40 po 0,50 + 0,5 po 0,20 = 20,30: {cost(r)}")
    t_dur = tariff(([pc("ENERGY", 0.0, 1, 20.0)], {"max_duration": 1800}), ([pc("ENERGY", 0.25, 1, 20.0)], {"max_duration": 3600}),
                   ([pc("ENERGY", 0.40, 1, 20.0)], None))
    r = m.calculate(t_dur, session("2026-10-20T10:00:00Z", (30, {"ENERGY": 5}), (10, {"ENERGY": 1.2})))
    check(cost(r) == (0.3, 0.36), f"RES-2: max_duration — 30 min gratis, potem 0,25 €/kWh: {cost(r)}")
    night = tariff(([pc("ENERGY", 0.30)], {"start_time": "22:00", "end_time": "06:00"}), ([pc("ENERGY", 0.50)], None))
    r = m.calculate(night, session("2026-10-20T21:30:00Z", (60, {"ENERGY": 10})), tz="Europe/Warsaw")
    check(cost(r) == (3.0, 3.0), f"RES-3: 21:30 UTC = 23:30 w Warszawie → taryfa nocna przez północ: {cost(r)}")
    r = m.calculate(night, session("2026-10-20T21:30:00Z", (60, {"ENERGY": 10})))
    check(cost(r) == (5.0, 5.0), f"RES-4: domyślnie UTC → 21:30 poza oknem nocnym: {cost(r)}")
    kwh = tariff(([pc("ENERGY", 0.40)], {"max_kwh": 10}), ([pc("ENERGY", 0.30)], None))
    r = m.calculate(kwh, session("2026-10-20T10:00:00Z", (30, {"ENERGY": 10}), (30, {"ENERGY": 5})))
    check(cost(r) == (5.5, 5.5), f"RES-5: max_kwh wyłącznie — od 10 kWh tańsza cena: {cost(r)}")

    # min_price, brak VAT, brak składnika, rezerwacja
    t12 = tariff(([pc("ENERGY", 0.25, 1, 10.0)], None), min_price={"excl_vat": 0.50, "incl_vat": 0.55})
    r = m.calculate(t12, session("2026-10-20T10:00:00Z", (5, {"ENERGY": 1})))
    check(cost(r) == (0.5, 0.55) and any("min_price" in w for w in r["warnings"]), f"MIN-1: min_price podnosi koszt: {cost(r)} {r['warnings']}")
    r = m.calculate(tariff(([pc("ENERGY", 0.25)], None), max_price={"excl_vat": 2.0, "incl_vat": 2.0}),
                    session("2026-10-20T10:00:00Z", (60, {"ENERGY": 20})))
    check(cost(r) == (2.0, 2.0), f"MAX-1: max_price ogranicza koszt: {cost(r)}")
    r = m.calculate(tariff(([pc("ENERGY", 0.25)], None)), session("2026-10-20T10:00:00Z", (60, {"ENERGY": 4, "TIME": 60})))
    check(cost(r) == (1.0, 1.0) and r["warnings"] == [], f"NOVAT-1: brak `vat` = brak VAT; TIME bez składnika nie jest błędem: {r}")
    resv = tariff(([pc("TIME", 5.0)], {"reservation": "RESERVATION"}), ([pc("ENERGY", 0.25)], None))
    r = m.calculate(resv, session("2026-10-20T10:00:00Z", (60, {"ENERGY": 4})))
    check(cost(r) == (1.0, 1.0) and any("rezerwac" in w for w in r["warnings"]), f"RESV-1: elementy rezerwacji pominięte z ostrzeżeniem: {r['warnings']}")
    lines = m.calculate(T4, session("2026-10-19T09:30:00Z", (165, {"TIME": 165, "MAX_CURRENT": 16}), (42, {"PARKING_TIME": 42})))["lines"]
    check(any(x["type"] == "PARKING_TIME" and x["billed"] == 0.75 and x["element"] == 4 for x in lines),
          f"LINES-1: rozbicie z numerem elementu i wolumenem po step_size: {lines}")

    # Porównanie z CDR
    cdr = {**s_cdr, "currency": "EUR", "tariffs": [t_cdr], "total_cost": {"excl_vat": 4.0, "incl_vat": 4.4}, "total_energy": 15.342,
           "total_time": 1.973, "total_time_cost": {"excl_vat": 4.0, "incl_vat": 4.4}}
    check(m.compare(m.calculate(t_cdr, s_cdr), cdr) == [], "CDR-1: zgodny CDR → brak rozbieżności")
    bad = {**cdr, "total_cost": {"excl_vat": 4.2, "incl_vat": 4.62}}
    diff = m.compare(m.calculate(t_cdr, s_cdr), bad)
    check([d["field"] for d in diff] == ["total_cost.excl_vat", "total_cost.incl_vat"], f"CDR-2: rozbieżność kosztu: {diff}")

    # Wiersz poleceń
    with tempfile.TemporaryDirectory() as t:
        tp, sp, cp, bp = (Path(t) / n for n in ("t.json", "s.json", "c.json", "b.json"))
        tp.write_text(json.dumps(t_cdr)), sp.write_text(json.dumps(s_cdr)), cp.write_text(json.dumps(cdr)), bp.write_text(json.dumps(bad))
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a], capture_output=True, text=True)
        p = run(str(tp), str(sp), "--json")
        check(p.returncode == 0 and json.loads(p.stdout)["total_cost"]["excl_vat"] == 4.0, f"CLI-1: --json, kod 0: {p.returncode} {p.stderr[-200:]}")
        p = run(str(tp), str(cp), "--cdr", str(cp))
        check(p.returncode == 0 and "4.4" in p.stdout, f"CLI-2: CDR jako plik okresów i porównanie, kod 0: {p.returncode} {p.stdout[-300:]}")
        p = run(str(tp), str(bp), "--cdr", str(bp))
        check(p.returncode == 1 and "total_cost" in p.stdout, f"CLI-3: rozbieżność z CDR → kod 1: {p.returncode} {p.stdout[-300:]}")
        p = run(str(tp), str(Path(t) / "brak.json"))
        check(p.returncode == 2, f"CLI-4: brak pliku → kod 2: {p.returncode}")
        (Path(t) / "zly.json").write_text("{nie json")
        p = run(str(Path(t) / "zly.json"), str(sp))
        check(p.returncode == 2, f"CLI-5: zły JSON → kod 2: {p.returncode}")
        p = run(str(tp), str(sp), "--tz", "Nie/Ma")
        check(p.returncode == 2, f"CLI-6: nieznana strefa → kod 2: {p.returncode}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów kalkulatora taryf OCPI nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów kalkulatora taryf OCPI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
