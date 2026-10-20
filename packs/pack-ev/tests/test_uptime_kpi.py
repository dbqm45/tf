#!/usr/bin/env python3
"""Testy kalkulatora dostępności portów (skill dom-ev-kpi-analytics): przedziały statusów z StatusNotification,
przestoje, wyłączenia wg NEVI, trzy definicje uptime (surowa, NEVI, SLA), stan nieznany, MTTR i MTBF, skuteczność
sesji, próg i kody wyjścia.

Wzór NEVI: 23 CFR 680.116(b) — µ = ((525 600 − (T_outage − T_excluded)) / 525 600) × 100 dla każdego portu, wyłączenia:
przerwy w dostawie energii, wina pojazdu, planowana konserwacja, wandalizm, klęski żywiołowe, godziny poza czasem
pracy stacji (eCFR, kopia w bazie wiedzy `us-nevi`, pobrane 2026-10-20).
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-kpi-analytics" / "scripts" / "uptime_kpi.py"

START, END = "2026-09-01T00:00:00Z", "2026-10-01T00:00:00Z"   # 30 dni = 43 200 min


def load():
    spec = importlib.util.spec_from_file_location("uptime_kpi", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ev(ts, status, port="P1", **kw):
    return {"ts": ts, "port": port, "status": status, **kw}


def data(events, **extra):
    return {"window": {"start": START, "end": END}, "events": events, **extra}


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

    def port(r, pid="P1"):
        return r["ports"][pid]

    # Podstawy
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available")]))
    p = port(r)
    check(p["window_min"] == 43200 and p["outage_min"] == 0 and p["uptime_raw"] == 100.0 and p["uptime_nevi"] == 100.0,
          f"U-1: port cały czas Available → 100 %: {p}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-10T08:00:00Z", "Faulted"),
                        ev("2026-09-10T12:00:00Z", "Available")]))
    p = port(r)
    check(p["outage_min"] == 240 and abs(p["uptime_raw"] - round((43200 - 240) / 43200 * 100, 3)) < 1e-9,
          f"U-2: 4 h Faulted → przestój 240 min, uptime surowy {p}")
    check(p["outages"] == 1 and p["mttr_min"] == 240.0 and p["mtbf_min"] == 43200 - 240,
          f"U-3: liczba przestojów, MTTR i MTBF: {p}")

    # Wyłączenia NEVI
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"),
                        ev("2026-09-10T08:00:00Z", "Unavailable", reason="utility"),
                        ev("2026-09-10T12:00:00Z", "Available")]))
    p = port(r)
    check(p["excluded_min"] == 240 and p["uptime_nevi"] == 100.0 and p["uptime_sla"] == 100.0 and p["uptime_raw"] < 100,
          f"U-4: przestój z przyczyną 'utility' wyłączony w NEVI i SLA, nie w surowym: {p}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-10T08:00:00Z", "Faulted"),
                        ev("2026-09-10T12:00:00Z", "Available")],
                       exclusions=[{"port": "P1", "start": "2026-09-10T10:00:00Z", "end": "2026-09-10T14:00:00Z",
                                    "reason": "maintenance"}]))
    p = port(r)
    check(p["outage_min"] == 240 and p["excluded_min"] == 120,
          f"U-5: okno konserwacji wyłącza tylko część przestoju, która się z nim pokrywa: {p}")
    w, to, te = 43200, 240, 120
    check(abs(p["uptime_nevi"] - round((w - (to - te)) / w * 100, 3)) < 1e-9
          and abs(p["uptime_sla"] - round((w - to) / (w - te) * 100, 3)) < 1e-9,
          f"U-6: NEVI odejmuje wyłączenia od przestoju, SLA usuwa je z mianownika — to różne liczby: {p}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"),
                        ev("2026-09-10T08:00:00Z", "Faulted", reason="operator"),
                        ev("2026-09-10T12:00:00Z", "Available")]))
    check(port(r)["excluded_min"] == 0 and any(x["code"] == "reason-not-excluded" for x in r["warnings"]),
          f"U-7: przyczyna spoza listy NEVI (operator) nie wyłącza przestoju, ostrzeżenie: {r['warnings']}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available")],
                       exclusions=[{"start": "2026-09-01T00:00:00Z", "end": "2026-09-02T00:00:00Z", "reason": "outside_hours"}]))
    check(port(r)["excluded_min"] == 0 and port(r)["uptime_nevi"] == 100.0,
          "U-8: okno wyłączenia bez przestoju nie zmienia wyniku (wyłącza się przestój, nie czas)")

    # Okno, sortowanie, łączenie
    r = m.compute(data([ev("2026-09-30T22:00:00Z", "Faulted"), ev("2026-08-31T12:00:00Z", "Available"),
                        ev("2026-10-01T03:00:00Z", "Available")]))
    check(port(r)["outage_min"] == 120, f"U-9: zdarzenia nieposortowane, przestój przycięty do końca okna: {port(r)}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-05T00:00:00Z", "Faulted"),
                        ev("2026-09-05T01:00:00Z", "Faulted"), ev("2026-09-05T02:00:00Z", "Available")]))
    check(port(r)["outages"] == 1 and port(r)["outage_min"] == 120, f"U-10: powtórzony status nie tworzy drugiego przestoju: {port(r)}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-05T00:00:00Z", "Occupied"),
                        ev("2026-09-05T01:00:00Z", "Charging"), ev("2026-09-05T02:00:00Z", "Available")]))
    check(port(r)["outage_min"] == 0, "U-11: Occupied i Charging to czas dostępny (port w użyciu)")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-05T00:00:00Z", "Offline"),
                        ev("2026-09-05T03:00:00Z", "Available")]))
    check(port(r)["outage_min"] == 180, "U-12: Offline (brak połączenia z CSMS) to przestój")

    # Stan nieznany
    r = m.compute(data([ev("2026-09-02T00:00:00Z", "Available")]))
    p = port(r)
    check(p["unknown_min"] == 1440 and p["outage_min"] == 1440 and any(x["code"] == "unknown-start" for x in r["warnings"]),
          f"U-13: brak statusu przed oknem → doba nieznana, domyślnie liczona jako przestój: {p} {r['warnings']}")
    r = m.compute(data([ev("2026-09-02T00:00:00Z", "Available")]), unknown="exclude")
    p = port(r)
    check(p["unknown_min"] == 1440 and p["outage_min"] == 0 and p["window_min"] == 43200 - 1440,
          f"U-14: unknown='exclude' usuwa czas nieznany z okna: {p}")

    # Statusy spoza listy
    try:
        m.compute(data([ev("2026-08-31T12:00:00Z", "PAUSED")]))
        check(False, "U-15: nieznany status (PAUSED) bez mapowania → InputError")
    except m.InputError:
        check(True, "")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-05T00:00:00Z", "PAUSED"),
                        ev("2026-09-05T05:00:00Z", "Available")]), down_status=["PAUSED"])
    check(port(r)["outage_min"] == 300, f"U-16: PAUSED zmapowany jako przestój: {port(r)}")
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available"), ev("2026-09-05T00:00:00Z", "PAUSED"),
                        ev("2026-09-05T05:00:00Z", "Available")]), up_status=["PAUSED"])
    check(port(r)["outage_min"] == 0, "U-17: PAUSED zmapowany jako dostępny")

    # Wiele portów, NEVI rok, próg
    yr = {"window": {"start": "2025-10-01T00:00:00Z", "end": "2026-10-01T00:00:00Z"},
          "events": [ev("2025-09-30T00:00:00Z", "Available", "A"), ev("2025-09-30T00:00:00Z", "Available", "B"),
                     ev("2026-01-01T00:00:00Z", "Faulted", "B"), ev("2026-01-12T00:00:00Z", "Available", "B")]}
    r = m.compute(yr)
    b = port(r, "B")
    check(b["window_min"] == 525600 and b["uptime_nevi"] == round((525600 - 11 * 1440) / 525600 * 100, 3),
          f"U-18: okno 365 dni = 525 600 min jak we wzorze NEVI: {b}")
    check(r["summary"]["ports"] == 2 and r["summary"]["below_threshold"] == ["B"] and r["summary"]["threshold"] == 97.0,
          f"U-19: port B (11 dni przestoju ≈ 97,0 %) poniżej progu 97 %: {r['summary']}")
    check(abs(r["summary"]["mean_uptime_nevi"] - round((100 + b["uptime_nevi"]) / 2, 3)) < 1e-9,
          f"U-20: średnia NEVI po portach: {r['summary']}")
    leap = {"window": {"start": "2027-10-01T00:00:00Z", "end": "2028-10-01T00:00:00Z"},
            "events": [ev("2027-09-30T00:00:00Z", "Available")]}
    check(any(x["code"] == "nevi-window" for x in m.compute(leap)["warnings"]),
          "U-21: okno roczne ≠ 525 600 min (rok przestępny) → ostrzeżenie, że NEVI liczy na 525 600")

    # Sesje
    sessions = [{"port": "P1", "outcome": "ok"}] * 8 + [{"port": "P1", "outcome": "failed"}] * 2
    r = m.compute(data([ev("2026-08-31T12:00:00Z", "Available")], sessions=sessions))
    check(port(r)["sessions"] == 10 and port(r)["session_success"] == 80.0 and r["summary"]["session_success"] == 80.0,
          f"U-22: skuteczność sesji 8/10 = 80 %: {port(r)}")
    try:
        m.compute(data([ev("2026-08-31T12:00:00Z", "Available")], sessions=[{"port": "P1", "outcome": "maybe"}]))
        check(False, "U-23: outcome spoza ok/failed → InputError")
    except m.InputError:
        check(True, "")

    # Błędy wejścia
    for bad, why in ((data([{"ts": "wczoraj", "port": "P1", "status": "Available"}]), "zła data"),
                     ({"window": {"start": END, "end": START}, "events": []}, "koniec przed początkiem"),
                     ({"events": []}, "brak window")):
        try:
            m.compute(bad)
            check(False, f"U-24: {why} → InputError")
        except m.InputError:
            check(True, "")

    # CLI
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "in.json"
        f.write_text(json.dumps(yr), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        check(p.returncode == 1 and "B" in p.stdout, f"CLI-1: kod 1, gdy port poniżej progu: {p.returncode} {p.stdout[-300:]} {p.stderr[-200:]}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f), "--threshold", "96"], capture_output=True, text=True)
        check(p.returncode == 0, f"CLI-2: --threshold 96 → kod 0: {p.returncode}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f), "--json"], capture_output=True, text=True)
        try:
            check(json.loads(p.stdout)["ports"]["A"]["uptime_nevi"] == 100.0, "CLI-3: --json")
        except (ValueError, KeyError) as e:
            check(False, f"CLI-3: --json zwraca JSON: {e}")
        f.write_text(json.dumps(data([ev("2026-08-31T12:00:00Z", "PAUSED")])), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True)
        check(p.returncode == 2, f"CLI-4: kod 2 przy błędzie wejścia: {p.returncode}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f), "--down-status", "PAUSED"], capture_output=True, text=True)
        check(p.returncode == 1, f"CLI-5: --down-status PAUSED (cały miesiąc przestoju) → kod 1: {p.returncode} {p.stderr[-200:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów uptime_kpi nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów uptime_kpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
