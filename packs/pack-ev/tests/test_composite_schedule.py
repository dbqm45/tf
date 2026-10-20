#!/usr/bin/env python3
"""Testy kalkulatora composite schedule OCPP (skill dom-ev-smart-charging): stack level, Absolute/Relative/Recurring,
validFrom/To, łączenie Max/ExternalConstraints/TxDefault/Tx, A↔W i fazy, walidacja profili, kody wyjścia.

Przypadki C-1…C-5 przepisane z testów EVerest libocpp (Apache 2.0, github.com/EVerest/libocpp,
tests/lib/ocpp/v16/test_composite_schedule.cpp i tests/lib/ocpp/v16/json/*.json, dostęp 2026-10-20). C-6 i C-7 —
przykłady z doc/common/smart_charging_profiles.md; dokumentacja mówi tam „brak ładowania” poza ważnością profilu, a kod
libocpp stosuje limit domyślny (48 A) — test sprawdza oba warianty parametrem default_limit.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-smart-charging" / "scripts" / "composite_schedule.py"


def load():
    spec = importlib.util.spec_from_file_location("composite_schedule", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def per(*items):
    return [{"startPeriod": s, "limit": l, **({"numberPhases": n} if n else {})} for s, l, *rest in items for n in [rest[0] if rest else None]]


MAX_401 = {"chargingProfileId": 24, "chargingProfileKind": "Recurring", "chargingProfilePurpose": "ChargePointMaxProfile",
           "recurrencyKind": "Daily", "stackLevel": 0,
           "chargingSchedule": {"chargingRateUnit": "A", "duration": 86400, "startSchedule": "2024-01-17T08:00:00.000Z",
                                "chargingSchedulePeriod": per((0, 24.0, 1), (900, 28.0, 1), (1800, 30.0, 1), (2700, 32.0, 1))}}
REL_303 = {"chargingProfileId": 301, "chargingProfileKind": "Relative", "chargingProfilePurpose": "TxDefaultProfile",
           "stackLevel": 5, "validFrom": "2024-01-01T12:00:00Z", "validTo": "2025-01-01T14:00:00Z",
           "chargingSchedule": {"chargingRateUnit": "A", "duration": 3600,
                                "chargingSchedulePeriod": per((0, 16.0), (1800, 15.0), (2700, 14.0))}}
MAX_24A = {"chargingProfileId": 24, "chargingProfileKind": "Recurring", "chargingProfilePurpose": "ChargePointMaxProfile",
           "recurrencyKind": "Daily", "stackLevel": 0,
           "chargingSchedule": {"chargingRateUnit": "A", "duration": 86400, "startSchedule": "2024-01-17T00:00:00.000Z",
                                "chargingSchedulePeriod": per((0, 16.0, 1), (3600, 16.0, 3), (7200, 10.0, 1), (10800, 10.0, 3))}}
TXD_25W = {"chargingProfileId": 25, "chargingProfileKind": "Relative", "chargingProfilePurpose": "TxDefaultProfile",
           "stackLevel": 0,
           "chargingSchedule": {"chargingRateUnit": "W", "duration": 3600,
                                "chargingSchedulePeriod": per((0, 12420.0), (300, 8280.0), (600, 6210.0), (900, 4140.0), (1200, 2070.0))}}
ABS_301 = {"chargingProfileId": 301, "chargingProfileKind": "Absolute", "chargingProfilePurpose": "TxDefaultProfile",
           "stackLevel": 5, "validFrom": "2024-01-01T12:00:00Z", "validTo": "2024-01-01T14:00:00Z",
           "chargingSchedule": {"chargingRateUnit": "A", "duration": 3600, "startSchedule": "2024-01-01T12:02:00Z",
                                "chargingSchedulePeriod": per((0, 32.0), (1800, 31.0), (2700, 30.0))}}


def simple(pid, purpose, limit, level=0, kind="Relative", start=None, duration=None, unit="A", **extra):
    sched = {"chargingRateUnit": unit, "chargingSchedulePeriod": per((0, limit))}
    if start:
        sched["startSchedule"] = start
    if duration:
        sched["duration"] = duration
    return {"chargingProfileId": pid, "chargingProfileKind": kind, "chargingProfilePurpose": purpose, "stackLevel": level,
            "chargingSchedule": sched, **extra}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    m = load()

    def periods(res, phases=False):
        return [(p["startPeriod"], p["limit"]) + ((p["numberPhases"],) if phases else ()) for p in res["chargingSchedulePeriod"]]

    # Przypadki z testów libocpp
    r = m.compute([MAX_401], "2024-08-21T08:00:00Z", 3600)
    check(periods(r, True) == [(0, 24.0, 1), (900, 28.0, 1), (1800, 30.0, 1), (2700, 32.0, 1)] and r["duration"] == 3600
          and r["startSchedule"] == "2024-08-21T08:00:00Z" and r["chargingRateUnit"] == "A",
          f"C-1: SingleStationMaxForEvse0 — profil Max cykliczny, limit domyślny niższy niż brak ograniczenia: {r}")
    r = m.compute([REL_303], "2024-01-02T08:00:00Z", 3600)
    check(periods(r) == [(0, 16.0), (1800, 15.0), (2700, 14.0)], f"C-2: TxDefault Relative bez transakcji startuje od start: {periods(r)}")
    r = m.compute([MAX_24A, TXD_25W], "2024-01-02T00:00:00Z", 3600)
    check(periods(r, True) == [(0, 16.0, 1), (1200, 9.0, 1)],
          f"C-3: MixingCurrentAndPower_16A_1P — W→A przy 1 fazie (230 V), Max 16 A: {periods(r, True)}")
    r = m.compute([MAX_24A, TXD_25W], "2024-01-02T01:00:00Z", 3600)
    check(periods(r, True) == [(0, 16.0, 3), (300, 12.0, 3), (600, 9.0, 3), (900, 6.0, 3), (1200, 3.0, 3)],
          f"C-4: MixingCurrentAndPower_16A_3P — W→A przy 3 fazach: {periods(r, True)}")
    r = m.compute([ABS_301], "2024-01-01T12:01:59Z", 3602)
    check(periods(r) == [(0, 48.0), (1, 32.0), (1801, 31.0), (2701, 30.0), (3601, 48.0)],
          f"C-5: ExtraSeconds — Absolute z duration, limit domyślny przed i po: {periods(r)}")

    # Przykłady z dokumentacji libocpp
    doc = simple(1, "TxDefaultProfile", 32.0, 1, validFrom="2024-01-01T12:00:00Z", validTo="2024-01-01T20:00:00Z")
    doc["chargingSchedule"]["chargingSchedulePeriod"] = per((0, 32.0), (3600, 6.0))
    r = m.compute([doc], "2024-01-01T10:00:00Z", 10800, tx_start="2024-01-01T10:00:00Z")
    check(periods(r) == [(0, 48.0), (7200, 6.0)], f"C-6a: przed validFrom limit domyślny, potem 6 A (godzina od startu transakcji minęła): {periods(r)}")
    r = m.compute([doc], "2024-01-01T10:00:00Z", 10800, tx_start="2024-01-01T10:00:00Z", default_limit=0.0)
    check(periods(r) == [(0, 0.0), (7200, 6.0)], f"C-6b: default_limit=0 → „brak ładowania” jak w dokumentacji: {periods(r)}")
    r = m.compute([doc], "2024-01-01T19:50:00Z", 1200, tx_start="2024-01-01T19:50:00Z", default_limit=0.0)
    check(periods(r) == [(0, 32.0), (600, 0.0)], f"C-6c: 10 min po 32 A, potem validTo: {periods(r)}")
    rec = simple(1, "TxDefaultProfile", 32.0, 1, kind="Recurring", start="2024-01-01T12:00:00Z", recurrencyKind="Daily")
    rec["chargingSchedule"]["chargingSchedulePeriod"] = per((0, 32.0), (3600, 6.0))
    r = m.compute([rec], "2024-01-10T11:50:00Z", 1200)
    check(periods(r) == [(0, 6.0), (600, 32.0)], f"C-7: Recurring Daily — 6 A z poprzedniego dnia, od 12:00 32 A: {periods(r)}")

    # Reguły łączenia
    txd, tx, mx = simple(1, "TxDefaultProfile", 32.0), simple(2, "TxProfile", 10.0), simple(3, "ChargePointMaxProfile", 20.0, kind="Absolute", start="2026-01-01T00:00:00Z")
    r = m.compute([txd, tx, mx], "2026-10-20T10:00:00Z", 600, tx_start="2026-10-20T10:00:00Z")
    check(periods(r) == [(0, 10.0)] and r["chargingSchedulePeriod"][0]["source"] == "TxProfile#2",
          f"MIX-1: TxProfile zastępuje TxDefault, źródło okresu: {r['chargingSchedulePeriod']}")
    tx25 = simple(2, "TxProfile", 25.0)
    r = m.compute([txd, tx25, mx], "2026-10-20T10:00:00Z", 600, tx_start="2026-10-20T10:00:00Z")
    check(periods(r) == [(0, 20.0)] and r["chargingSchedulePeriod"][0]["source"] == "ChargePointMaxProfile#3",
          f"MIX-2: Max ogranicza Tx: {r['chargingSchedulePeriod']}")
    ext = {"id": 9, "stackLevel": 0, "chargingProfilePurpose": "ChargingStationExternalConstraints", "chargingProfileKind": "Absolute",
           "chargingSchedule": [{"id": 1, "startSchedule": "2026-10-20T10:05:00Z", "duration": 300, "chargingRateUnit": "A",
                                 "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 6.0}]}]}
    r = m.compute([txd, ext], "2026-10-20T10:00:00Z", 900)
    check(periods(r) == [(0, 32.0), (300, 6.0), (600, 32.0)], f"MIX-3: OCPP 2.0.1 ExternalConstraints (lista chargingSchedule) obniża limit na 5 min: {periods(r)}")
    low = simple(1, "TxDefaultProfile", 32.0, 1)
    high = simple(2, "TxDefaultProfile", 16.0, 2, kind="Absolute", start="2026-10-20T10:10:00Z", duration=600)
    r = m.compute([low, high], "2026-10-20T10:00:00Z", 1800)
    check(periods(r) == [(0, 32.0), (600, 16.0), (1200, 32.0)], f"MIX-4: wyższy stackLevel wygrywa w swoim oknie: {periods(r)}")
    r = m.compute([simple(1, "TxDefaultProfile", 16.0)], "2026-10-20T10:00:00Z", 600, unit="W")
    check(periods(r) == [(0, 11040.0)] and r["chargingRateUnit"] == "W", f"UNIT-1: A→W = 16 × 230 × 3: {periods(r)}")
    r = m.compute([], "2026-10-20T10:00:00Z", 600)
    check(periods(r) == [(0, 48.0)] and r["chargingSchedulePeriod"][0]["source"] == "default", f"DEF-1: brak profili → limit domyślny: {r}")

    # Walidacja (reguły K01 z libocpp)
    bad1 = simple(5, "TxDefaultProfile", 16.0, start="2026-10-20T10:00:00Z")
    bad2 = simple(6, "ChargePointMaxProfile", 16.0)
    bad3 = simple(7, "TxDefaultProfile", 16.0)
    bad3["chargingSchedule"]["chargingSchedulePeriod"] = per((60, 16.0))
    errs = {pid: m.validate(p) for pid, p in ((5, bad1), (6, bad2), (7, bad3))}
    check(any("startSchedule" in e for e in errs[5]) and any("Relative" in e for e in errs[6]) and any("0" in e for e in errs[7]),
          f"VAL-1: Relative ze startSchedule, Max Relative, pierwszy startPeriod ≠ 0: {errs}")
    r = m.compute([bad3, simple(1, "TxDefaultProfile", 20.0)], "2026-10-20T10:00:00Z", 600)
    check(periods(r) == [(0, 20.0)] and r["invalid"] and r["invalid"][0]["id"] == 7, f"VAL-2: błędny profil pominięty i zgłoszony: {r}")

    # Wiersz poleceń
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "p.json"
        f.write_text(json.dumps([MAX_24A, TXD_25W]), encoding="utf-8")
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), *a], capture_output=True, text=True)
        p = run(str(f), "--start", "2024-01-02T01:00:00Z", "--duration", "3600", "--json")
        check(p.returncode == 0 and json.loads(p.stdout)["chargingSchedulePeriod"][1]["limit"] == 12.0, f"CLI-1: --json: {p.returncode} {p.stderr[-200:]}")
        p = run(str(f), "--start", "2024-01-02T01:00:00Z", "--duration", "3600")
        check(p.returncode == 0 and "12.0" in p.stdout and "ChargePointMaxProfile#24" in p.stdout, f"CLI-2: tekst z źródłem okresu: {p.stdout[-300:]}")
        f.write_text(json.dumps({"profiles": [bad3]}), encoding="utf-8")
        p = run(str(f), "--start", "2026-10-20T10:00:00Z", "--duration", "600")
        check(p.returncode == 1, f"CLI-3: błędny profil → kod 1: {p.returncode}")
        p = run(str(Path(t) / "brak.json"), "--start", "2026-10-20T10:00:00Z", "--duration", "600")
        check(p.returncode == 2, f"CLI-4: brak pliku → kod 2: {p.returncode}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów composite schedule nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów composite schedule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
