#!/usr/bin/env python3
"""
Przykład: plan ładowania zajezdni pod limit przyłącza → profile OCPP 1.6 TxProfile na każde EVSE. Dydaktyczny, nie
produkcja. Tylko biblioteka standardowa.

  python3 examples/depot-smart-charging/depot.py <scenariusz.json> [--profiles <katalog>] [--json]

Algorytm: sloty czasu (`slot_s`), w każdym pojazdy obecne i z niedoładowaną energią dostają prąd w kolejności
najwcześniejszego odjazdu (EDF): min(max pojazdu, prąd potrzebny do końca, wolny limit przyłącza). Przydział poniżej
6 A to 0 — poniżej tej wartości pojazd nie ładuje (PWM 10 %, dom-ev-charger-hardware). Prąd jest na fazę; wszystkie
pojazdy i przyłącze trójfazowe w tym przykładzie. Kod wyjścia: 0 — każdy pojazd dostał energię, 1 — co najmniej
jeden nie (zgłoszony), 2 — błąd wejścia.

Czego brakuje do produkcji: pomiar rzeczywistego poboru (pojazd bierze mniej niż limit), nierównowaga faz i pojazdy
1-fazowe, rezerwa na obciążenie budynku, ceny energii i PV, ponowne planowanie po zdarzeniach (przyjazd, odłączenie),
ISO 15118 (harmonogram od pojazdu) — skille dom-ev-smart-charging i dom-ev-energy-management.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

MIN_A = 6.0


def _energy_kwh(amps: float, phases: int, voltage: float, seconds: float) -> float:
    return amps * voltage * phases * seconds / 3600 / 1000


def plan(sc: dict) -> dict:
    slot, grid, volt = sc["slot_s"], float(sc["grid_limit_a"]), float(sc.get("voltage", 230))
    vehicles = [{**v, "delivered_kwh": 0.0} for v in sc["vehicles"]]
    horizon = max(v["departure_s"] for v in vehicles)
    slots = []
    for i in range(math.ceil(horizon / slot)):
        start = i * slot
        free, alloc = grid, {}
        active = [v for v in vehicles if v["arrival_s"] <= start < v["departure_s"] and v["delivered_kwh"] < v["needed_kwh"] - 1e-9]
        for v in sorted(active, key=lambda x: (x["departure_s"], x["evse"])):
            rem = v["needed_kwh"] - v["delivered_kwh"]
            need = rem * 1000 * 3600 / (volt * v["phases"] * slot)
            a = min(float(v["max_a"]), free, max(need, MIN_A))
            a = math.floor(a * 10) / 10
            if a < MIN_A:
                continue
            alloc[v["evse"]] = a
            free -= a
            v["delivered_kwh"] += min(rem, _energy_kwh(a, v["phases"], volt, slot))
        slots.append({"start": start, "allocation": {v["evse"]: alloc.get(v["evse"], 0) for v in vehicles}})
    out_v = [{"evse": v["evse"], "needed_kwh": v["needed_kwh"], "delivered_kwh": round(v["delivered_kwh"], 3),
              "met": v["delivered_kwh"] >= v["needed_kwh"] - 1e-6, "departure_s": v["departure_s"]} for v in vehicles]
    return {"slots": slots, "vehicles": out_v}


def tx_profiles(pl: dict, sc: dict) -> list[dict]:
    """SetChargingProfile (OCPP 1.6) z TxProfile Absolute dla każdego EVSE; okresy łączone, gdy limit się nie zmienia."""
    out = []
    for n, v in enumerate(sc["vehicles"], start=1):
        periods = []
        for s in pl["slots"]:
            a = float(s["allocation"].get(v["evse"], 0))
            if not periods or periods[-1]["limit"] != a:
                periods.append({"startPeriod": s["start"], "limit": a, "numberPhases": v["phases"]})
        out.append({"evse": v["evse"], "connectorId": n, "csChargingProfiles": {
            "chargingProfileId": 1000 + n, "transactionId": n, "stackLevel": 0,
            "chargingProfilePurpose": "TxProfile", "chargingProfileKind": "Absolute",
            "chargingSchedule": {"startSchedule": sc["start"], "duration": len(pl["slots"]) * sc["slot_s"],
                                 "chargingRateUnit": "A", "chargingSchedulePeriod": periods}}})
    return out


def station_max_profile(sc: dict) -> dict:
    """ChargePointMaxProfile zajezdni: bezpiecznik po stronie stacji, niezależny od planu CSMS."""
    return {"chargingProfileId": 1, "stackLevel": 0, "chargingProfilePurpose": "ChargePointMaxProfile",
            "chargingProfileKind": "Absolute",
            "chargingSchedule": {"startSchedule": sc["start"], "chargingRateUnit": "A",
                                 "chargingSchedulePeriod": [{"startPeriod": 0, "limit": float(sc["grid_limit_a"]), "numberPhases": 3}]}}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Plan ładowania zajezdni pod limit przyłącza → OCPP TxProfile.")
    ap.add_argument("scenario")
    ap.add_argument("--profiles", help="katalog na pliki SetChargingProfile (po jednym na EVSE)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        sc = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
        pl = plan(sc)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if args.profiles:
        d = Path(args.profiles)
        d.mkdir(parents=True, exist_ok=True)
        for p in tx_profiles(pl, sc):
            (d / f"{p['evse']}.json").write_text(json.dumps({k: p[k] for k in ("connectorId", "csChargingProfiles")}, indent=1), encoding="utf-8")
        (d / "station-max.json").write_text(json.dumps({"connectorId": 0, "csChargingProfiles": station_max_profile(sc)}, indent=1), encoding="utf-8")
    if args.json:
        print(json.dumps(pl, ensure_ascii=False, indent=1))
    else:
        t0 = dt.datetime.fromisoformat(sc["start"].replace("Z", "+00:00"))
        print(f"{sc.get('name', 'zajezdnia')}: limit {sc['grid_limit_a']} A")
        for s in pl["slots"]:
            used = sum(s["allocation"].values())
            row = "  ".join(f"{e}:{a:>5.1f}" for e, a in s["allocation"].items())
            print(f"  {(t0 + dt.timedelta(seconds=s['start'])).strftime('%H:%M')}  {row}  Σ {used:.1f} A")
        for v in pl["vehicles"]:
            print(f"  {v['evse']}: {v['delivered_kwh']} / {v['needed_kwh']} kWh — {'spełnione' if v['met'] else 'niespełnione'}")
    return 0 if all(v["met"] for v in pl["vehicles"]) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
