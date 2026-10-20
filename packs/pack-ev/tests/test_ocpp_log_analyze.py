#!/usr/bin/env python3
"""Testy analizatora logów OCPP (skill dom-ev-diagnostics): ustalenia dla OCPP 1.6 i 2.0.1, wejście JSON Lines, kody wyjścia."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-diagnostics" / "scripts" / "ocpp_log_analyze.py"


def load():
    spec = importlib.util.spec_from_file_location("ocpp_log_analyze", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ln(ts: str, cp: str, d: str, frame: list) -> str:
    return json.dumps({"ts": f"2026-10-20T{ts}Z", "cp": cp, "dir": d, "frame": frame})


UP, DOWN = "cp>csms", "csms>cp"


def log16_ok() -> list[str]:
    """Poprawna sesja OCPP 1.6: Boot, Start, MeterValues, Stop — bez ustaleń."""
    return [
        ln("08:00:00", "CP1", UP, [2, "b1", "BootNotification", {"chargePointVendor": "V", "chargePointModel": "M"}]),
        ln("08:00:01", "CP1", DOWN, [3, "b1", {"status": "Accepted", "currentTime": "2026-10-20T08:00:01Z", "interval": 300}]),
        ln("08:01:00", "CP1", UP, [2, "s1", "StartTransaction", {"connectorId": 1, "idTag": "T1", "meterStart": 1000,
                                                                  "timestamp": "2026-10-20T08:01:00Z"}]),
        ln("08:01:01", "CP1", DOWN, [3, "s1", {"transactionId": 42, "idTagInfo": {"status": "Accepted"}}]),
        ln("08:10:00", "CP1", UP, [2, "m1", "MeterValues", {"connectorId": 1, "transactionId": 42, "meterValue": [
            {"timestamp": "2026-10-20T08:10:00Z", "sampledValue": [{"value": "2.5", "unit": "kWh",
                                                                    "measurand": "Energy.Active.Import.Register"}]}]}]),
        ln("08:10:01", "CP1", DOWN, [3, "m1", {}]),
        ln("08:20:00", "CP1", UP, [2, "e1", "StopTransaction", {"transactionId": 42, "meterStop": 4000,
                                                                 "timestamp": "2026-10-20T08:20:00Z"}]),
        ln("08:20:01", "CP1", DOWN, [3, "e1", {}]),
    ]


def codes(res: dict, cp: str | None = None) -> list[str]:
    return sorted(f["code"] for f in res["findings"] if cp is None or f["cp"] == cp)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    m = load()

    r = m.analyze(log16_ok())
    check(r["findings"] == [] and r["stations"]["CP1"]["ocpp"] == "1.6" and r["stations"]["CP1"]["frames"] == 8,
          f"OK-1: poprawna sesja 1.6 bez ustaleń, wersja wykryta: {r}")

    # 1.6: otwarta transakcja, nieznana transakcja, malejący licznik
    r = m.analyze(log16_ok()[:6])
    check(codes(r) == ["open-transaction"] and r["findings"][0]["severity"] == "high"
          and r["findings"][0]["lines"] == [3, 4], f"TX-1: Start bez Stop → open-transaction z liniami dowodu: {r['findings']}")
    lines = log16_ok() + [ln("08:30:00", "CP1", UP, [2, "e2", "StopTransaction", {"transactionId": 99, "meterStop": 1,
                                                                                    "timestamp": "2026-10-20T08:30:00Z"}]),
                          ln("08:30:01", "CP1", DOWN, [3, "e2", {}])]
    r = m.analyze(lines)
    check(codes(r) == ["unknown-transaction"] and r["findings"][0]["lines"] == [9], f"TX-2: Stop z nieznanym id: {r['findings']}")
    lines = log16_ok()
    lines[6] = ln("08:20:00", "CP1", UP, [2, "e1", "StopTransaction", {"transactionId": 42, "meterStop": 2000,
                                                                        "timestamp": "2026-10-20T08:20:00Z"}])
    r = m.analyze(lines)
    check(codes(r) == ["meter-decrease"], f"TX-3: meterStop 2000 Wh < MeterValues 2,5 kWh → meter-decrease: {r['findings']}")

    # Ramki: brak odpowiedzi, CALLERROR, zdublowane id
    r = m.analyze(log16_ok()[:2] + [ln("09:00:00", "CP1", DOWN, [2, "r1", "RemoteStartTransaction", {"idTag": "T1"}])])
    check(codes(r) == ["call-no-response"] and r["findings"][0]["severity"] == "high",
          f"RPC-1: CALL bez odpowiedzi → call-no-response: {r['findings']}")
    late = [ln("09:00:00", "CP1", DOWN, [2, "r1", "RemoteStartTransaction", {"idTag": "T1"}]),
            ln("09:01:00", "CP1", UP, [3, "r1", {"status": "Accepted"}])]
    check(codes(m.analyze(late, timeout=30)) == ["call-no-response"] and codes(m.analyze(late, timeout=120)) == [],
          "RPC-2: odpowiedź po 60 s → ustalenie przy timeout 30, brak przy 120")
    r = m.analyze([ln("09:00:00", "CP1", DOWN, [2, "c1", "ChangeConfiguration", {"key": "X", "value": "1"}]),
                   ln("09:00:01", "CP1", UP, [4, "c1", "NotSupported", "brak", {}])])
    check(codes(r) == ["callerror"] and "NotSupported" in r["findings"][0]["message"]
          and "ChangeConfiguration" in r["findings"][0]["message"], f"RPC-3: CALLERROR z kodem i akcją: {r['findings']}")
    r = m.analyze([ln("09:00:00", "CP1", UP, [2, "h1", "Heartbeat", {}]), ln("09:00:01", "CP1", DOWN, [3, "h1", {"currentTime": "x"}]),
                   ln("09:05:00", "CP1", UP, [2, "h1", "Heartbeat", {}]), ln("09:05:01", "CP1", DOWN, [3, "h1", {"currentTime": "x"}])])
    check(codes(r) == ["duplicate-message-id"], f"RPC-4: to samo id CALL w tym samym kierunku: {r['findings']}")

    # Zegar i restart
    lines = log16_ok()
    lines[2] = ln("08:01:00", "CP1", UP, [2, "s1", "StartTransaction", {"connectorId": 1, "idTag": "T1", "meterStart": 1000,
                                                                         "timestamp": "2026-10-20T07:30:00Z"}])
    r = m.analyze(lines)
    check(codes(r) == ["clock-skew"] and "1860" in r["findings"][0]["message"], f"CLK-1: różnica 31 min → clock-skew: {r['findings']}")
    check(codes(m.analyze(lines, skew=3600)) == [], "CLK-2: próg --skew 3600 → brak ustalenia")
    r = m.analyze(log16_ok() + log16_ok()[:2])
    check("reboot" in codes(r), f"BOOT-1: BootNotification po wcześniejszej aktywności → reboot: {r['findings']}")

    # OCPP 2.0.1: seqNo, otwarta transakcja, wykrycie wersji
    def te(ts, mid, ev, seq, tx="T-1", wh=None):
        p = {"eventType": ev, "timestamp": f"2026-10-20T{ts}Z", "triggerReason": "Authorized", "seqNo": seq,
             "transactionInfo": {"transactionId": tx}}
        if wh is not None:
            p["meterValue"] = [{"timestamp": f"2026-10-20T{ts}Z", "sampledValue": [{"value": wh}]}]
        return [ln(ts, "CP2", UP, [2, mid, "TransactionEvent", p]), ln(ts, "CP2", DOWN, [3, mid, {}])]

    ok2 = te("10:00:00", "t1", "Started", 0, wh=100) + te("10:05:00", "t2", "Updated", 1, wh=500) + te("10:10:00", "t3", "Ended", 2, wh=900)
    r = m.analyze(ok2)
    check(r["findings"] == [] and r["stations"]["CP2"]["ocpp"] == "2.0.1", f"V2-1: poprawna transakcja 2.0.1: {r}")
    r = m.analyze(te("10:00:00", "t1", "Started", 0) + te("10:05:00", "t2", "Updated", 3))
    check(codes(r) == ["open-transaction", "seqno-gap"], f"V2-2: luka seqNo 0→3 i brak Ended: {r['findings']}")
    r = m.analyze(te("10:00:00", "t1", "Started", 0) + te("10:05:00", "t2", "Updated", 1) + te("10:06:00", "t3", "Updated", 1)
                  + te("10:10:00", "t4", "Ended", 2))
    check(codes(r) == ["seqno-duplicate"], f"V2-3: powtórzony seqNo: {r['findings']}")
    r = m.analyze(te("10:00:00", "t1", "Started", 0, wh=500) + te("10:05:00", "t2", "Ended", 1, wh=300))
    check(codes(r) == ["meter-decrease"], f"V2-4: malejący licznik w 2.0.1: {r['findings']}")
    r = m.analyze(ok2, ocpp="1.6")
    check(r["stations"]["CP2"]["ocpp"] == "1.6", "V2-5: --ocpp wymusza wersję")

    # Wejście: złe linie nie przerywają analizy
    r = m.analyze(["nie json", json.dumps({"ts": "x"})] + log16_ok())
    check(codes(r) == ["invalid-line", "invalid-line"] and r["stations"]["CP1"]["frames"] == 8,
          f"IN-1: złe linie → invalid-line, reszta przeanalizowana: {r['findings']}")

    # Wiersz poleceń
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "log.jsonl"
        f.write_text("\n".join(log16_ok()[:6]) + "\n", encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), str(f), "--json"], capture_output=True, text=True)
        data = json.loads(p.stdout) if p.returncode == 0 else {}
        check(p.returncode == 0 and [x["code"] for x in data.get("findings", [])] == ["open-transaction"],
              f"CLI-1: JSON z pliku: {p.returncode} {p.stdout[:200]} {p.stderr[:200]}")
        p = subprocess.run([sys.executable, str(SCRIPT), "-"], input=f.read_text(encoding="utf-8"), capture_output=True, text=True)
        check(p.returncode == 0 and "CP1" in p.stdout and "open-transaction" in p.stdout, f"CLI-2: tekst ze stdin: {p.stdout[:300]}")
        p = subprocess.run([sys.executable, str(SCRIPT), str(Path(t) / "brak.jsonl")], capture_output=True, text=True)
        check(p.returncode == 2, f"CLI-3: brak pliku → kod 2: {p.returncode}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów analizatora logów OCPP nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów analizatora logów OCPP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
