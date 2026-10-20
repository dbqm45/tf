#!/usr/bin/env python3
"""Test end-to-end przykładu examples/depot-smart-charging: plan mocy zajezdni pod limit przyłącza → TxProfile na EVSE
→ composite schedule (dom-ev-smart-charging) zgodny z planem. Pomija się w projekcie bez examples/."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
EXAMPLE = ROOT / "examples" / "depot-smart-charging"
CALC = ROOT / ".claude" / "skills" / "dom-ev-smart-charging" / "scripts" / "composite_schedule.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not EXAMPLE.is_dir():
        print("✓ 0/0 testów depot-smart-charging (pominięte: brak examples/ — przykład nie jest instalowany w projekcie)")
        return 0
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    depot, calc = load("depot", EXAMPLE / "depot.py"), load("composite_schedule", CALC)
    scenario = json.loads((EXAMPLE / "data" / "depot.json").read_text(encoding="utf-8"))
    plan = depot.plan(scenario)
    grid, slot = scenario["grid_limit_a"], scenario["slot_s"]
    nslots = len(plan["slots"])

    check(all(sum(s["allocation"].values()) <= grid + 1e-9 for s in plan["slots"]),
          f"P-1: suma prądów w każdym slocie ≤ limit przyłącza {grid} A")
    caps = {v["evse"]: v["max_a"] for v in scenario["vehicles"]}
    check(all(a == 0 or 6 <= a <= caps[e] for s in plan["slots"] for e, a in s["allocation"].items()),
          "P-2: każdy przydział to 0 albo 6 A … max pojazdu (poniżej 6 A pojazd nie ładuje)")
    v = {x["evse"]: x for x in plan["vehicles"]}
    check(v["EVSE-1"]["delivered_kwh"] >= v["EVSE-1"]["needed_kwh"] - 1e-6 and v["EVSE-1"]["met"],
          f"P-3: pojazd z najwcześniejszym odjazdem dostaje całą energię: {v['EVSE-1']}")
    check(not v["EVSE-4"]["met"] and v["EVSE-4"]["delivered_kwh"] < v["EVSE-4"]["needed_kwh"],
          f"P-4: zapotrzebowanie niemożliwe do spełnienia jest zgłoszone: {v['EVSE-4']}")
    check(all(s["allocation"].get("EVSE-3", 0) == 0 for s in plan["slots"] if s["start"] < scenario["vehicles"][2]["arrival_s"]),
          "P-5: przed przyjazdem pojazd nie dostaje mocy")

    profiles = depot.tx_profiles(plan, scenario)
    check(len(profiles) == 4 and all(calc.validate(p["csChargingProfiles"]) == [] for p in profiles)
          and all(p["csChargingProfiles"]["chargingProfilePurpose"] == "TxProfile" for p in profiles),
          f"OCPP-1: poprawne SetChargingProfile (TxProfile) dla każdego EVSE: {[calc.validate(p['csChargingProfiles']) for p in profiles]}")
    ok = True
    for p in profiles:
        evse = p["evse"]
        r = calc.compute([p], scenario["start"], nslots * slot)
        for s in plan["slots"]:
            want = s["allocation"].get(evse, 0)
            got = [x["limit"] for x in r["chargingSchedulePeriod"] if x["startPeriod"] <= s["start"]][-1]
            ok = ok and abs(got - want) < 1e-6
    check(ok, "OCPP-2: composite schedule każdego EVSE odtwarza plan slot po slocie")
    station = depot.station_max_profile(scenario)
    r = calc.compute([station] + [p for p in profiles if p["evse"] == "EVSE-1"], scenario["start"], nslots * slot)
    check(max(x["limit"] for x in r["chargingSchedulePeriod"]) <= grid, "OCPP-3: profil Max zajezdni ogranicza composite schedule")

    p = subprocess.run([sys.executable, str(EXAMPLE / "depot.py"), str(EXAMPLE / "data" / "depot.json")], capture_output=True, text=True)
    check(p.returncode == 1 and "EVSE-4" in p.stdout and "niespełnione" in p.stdout,
          f"CLI-1: kod 1, gdy któryś pojazd nie dostanie energii: {p.returncode} {p.stdout[-300:]} {p.stderr[-200:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów depot-smart-charging nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów depot-smart-charging (end-to-end)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
