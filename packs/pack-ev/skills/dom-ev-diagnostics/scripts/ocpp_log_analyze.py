#!/usr/bin/env python3
"""
Analizator logów OCPP-J (1.6 i 2.0.1): ustalenia z dowodem w postaci numerów linii. Tylko biblioteka standardowa.
Sieć: brak.

  python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py <log.jsonl | -> [--ocpp auto|1.6|2.0.1]
          [--timeout 30] [--skew 300] [--json]

Wejście: JSON Lines, jedna ramka na linię:
  {"ts": "2026-10-20T08:00:00Z", "cp": "<id stacji>", "dir": "cp>csms" | "csms>cp", "frame": [<ramka OCPP-J>]}
Ramki: CALL [2, id, akcja, ładunek], CALLRESULT [3, id, ładunek], CALLERROR [4, id, kod, opis, szczegóły].

Ustalenia (kod — waga):
  call-no-response (high)      CALL bez odpowiedzi do końca logu albo z odpowiedzią po --timeout s
  callerror (medium)           CALLERROR — kod błędu i akcja, której dotyczy
  duplicate-message-id (medium) to samo id CALL ponownie w tym samym kierunku
  open-transaction (high)      1.6 StartTransaction bez StopTransaction / 2.0.1 Started bez Ended do końca logu
  unknown-transaction (medium) StopTransaction/MeterValues z transactionId nieznanym w logu (albo sprzed jego początku);
                               2.0.1: zdarzenie transakcji bez Started w logu
  seqno-gap (high)             2.0.1 luka w seqNo w obrębie transakcji
  seqno-duplicate (medium)     2.0.1 seqNo powtórzony lub mniejszy niż poprzedni
  meter-decrease (high)        malejący licznik energii w transakcji (Energy.Active.Import.Register; Wh, kWh × 1000)
  clock-skew (medium)          znacznik czasu w ładunku różni się od `ts` logu o więcej niż --skew s
                               (zegar ładowarki albo komunikat z kolejki offline)
  reboot (low)                 BootNotification po wcześniejszej aktywności stacji w logu
  invalid-line (low)           linia, której nie da się odczytać (nie przerywa analizy)
Kod wyjścia: 0 — przeanalizowano (także z ustaleniami), 2 — błąd wywołania albo brak pliku.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

SEVERITY = {"call-no-response": "high", "open-transaction": "high", "seqno-gap": "high", "meter-decrease": "high",
            "callerror": "medium", "duplicate-message-id": "medium", "unknown-transaction": "medium",
            "seqno-duplicate": "medium", "clock-skew": "medium", "reboot": "low", "invalid-line": "low"}
ORDER = {"high": 0, "medium": 1, "low": 2}
ENERGY = "Energy.Active.Import.Register"
TIMESTAMPED = {"StartTransaction", "StopTransaction", "TransactionEvent", "StatusNotification"}
OPPOSITE = {"cp>csms": "csms>cp", "csms>cp": "cp>csms"}


def parse_ts(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def energy_wh(meter_values) -> list[float]:
    """Odczyty rejestru energii (Wh) z listy meterValue: sampledValue bez measurand to rejestr energii."""
    out = []
    for mv in meter_values or []:
        for sv in (mv or {}).get("sampledValue") or []:
            if (sv.get("measurand") or ENERGY) != ENERGY:
                continue
            try:
                v = float(sv.get("value"))
            except (TypeError, ValueError):
                continue
            unit = sv.get("unit") or ((sv.get("unitOfMeasure") or {}).get("unit")) or "Wh"
            out.append(v * 1000 if unit.lower() == "kwh" else v)
    return out


class Analyzer:
    def __init__(self, ocpp: str = "auto", timeout: float = 30, skew: float = 300):
        self.ocpp, self.timeout, self.skew = ocpp, timeout, skew
        self.findings: list[dict] = []
        self.stations: dict[str, dict] = {}
        self.pending: dict[tuple, dict] = {}        # (cp, kierunek CALL, id) → CALL czekający na odpowiedź
        self.seen_calls: set[tuple] = set()
        self.tx16: dict[tuple, dict] = {}           # (cp, transactionId) → transakcja 1.6
        self.start16: dict[tuple, dict] = {}        # (cp, id StartTransaction) → dane startu
        self.tx2: dict[tuple, dict] = {}            # (cp, transactionId) → transakcja 2.0.1

    def add(self, code: str, cp: str, ts, lines: list[int], message: str) -> None:
        self.findings.append({"code": code, "severity": SEVERITY[code], "cp": cp,
                              "ts": ts.isoformat().replace("+00:00", "Z") if isinstance(ts, dt.datetime) else ts,
                              "lines": lines, "message": message})

    def station(self, cp: str) -> dict:
        return self.stations.setdefault(cp, {"ocpp": None if self.ocpp == "auto" else self.ocpp, "frames": 0, "active": False})

    def meter(self, tx: dict, cp: str, ts, line: int, values: list[float]) -> None:
        for v in values:
            if tx.get("last") is not None and v < tx["last"]:
                self.add("meter-decrease", cp, ts, [tx["last_line"], line],
                         f"licznik energii spadł z {tx['last']:g} Wh do {v:g} Wh (transakcja {tx['id']})")
            tx["last"], tx["last_line"] = v, line

    def feed(self, raw: str, line: int) -> None:
        try:
            rec = json.loads(raw)
            ts, cp, d, frame = parse_ts(rec["ts"]), str(rec["cp"]), rec["dir"], rec["frame"]
            if ts is None or d not in OPPOSITE or not isinstance(frame, list) or frame[0] not in (2, 3, 4):
                raise ValueError
            mid = str(frame[1])
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            self.add("invalid-line", "-", None, [line], "linia nie jest rekordem {ts, cp, dir, frame} z ramką OCPP-J")
            return
        st = self.station(cp)
        st["frames"] += 1
        if frame[0] == 2:
            self.call(cp, d, ts, line, mid, frame, st)
        else:
            self.response(cp, d, ts, line, mid, frame)
        st["active"] = True

    def call(self, cp, d, ts, line, mid, frame, st) -> None:
        action, payload = str(frame[2]), frame[3] if len(frame) > 3 and isinstance(frame[3], dict) else {}
        key = (cp, d, mid)
        if key in self.seen_calls:
            self.add("duplicate-message-id", cp, ts, [line], f"id „{mid}” użyte ponownie dla {action} ({d})")
        self.seen_calls.add(key)
        self.pending[key] = {"ts": ts, "line": line, "action": action, "payload": payload}
        if st["ocpp"] is None and action in ("StartTransaction", "StopTransaction"):
            st["ocpp"] = "1.6"
        elif st["ocpp"] is None and action == "TransactionEvent":
            st["ocpp"] = "2.0.1"
        if action == "BootNotification" and d == "cp>csms" and st["active"]:
            self.add("reboot", cp, ts, [line], "BootNotification w trakcie logu — ładowarka uruchomiła się ponownie")
        if action in TIMESTAMPED and (pts := parse_ts(payload.get("timestamp"))) is not None:
            diff = abs((pts - ts).total_seconds())
            if diff > self.skew:
                self.add("clock-skew", cp, ts, [line], f"{action}: znacznik w ładunku różni się od czasu logu o "
                                                     f"{diff:.0f} s (zegar ładowarki albo kolejka offline)")
        if action == "StartTransaction":
            self.start16[(cp, mid)] = {"line": line, "meterStart": payload.get("meterStart"), "ts": ts}
        elif action in ("StopTransaction", "MeterValues") and "transactionId" in payload:
            tx = self.tx16.get((cp, str(payload["transactionId"])))
            if tx is None:
                self.add("unknown-transaction", cp, ts, [line], f"{action} z transactionId {payload['transactionId']} "
                                                              "nieznanym w logu (albo sprzed jego początku)")
                return
            values = energy_wh(payload.get("meterValue") or payload.get("transactionData"))
            if action == "StopTransaction" and isinstance(payload.get("meterStop"), (int, float)):
                values.append(float(payload["meterStop"]))
                tx["stopped"] = True
            self.meter(tx, cp, ts, line, values)
        elif action == "TransactionEvent":
            self.transaction_event(cp, ts, line, payload)

    def transaction_event(self, cp, ts, line, p) -> None:
        txid = str((p.get("transactionInfo") or {}).get("transactionId"))
        ev, seq = p.get("eventType"), p.get("seqNo")
        tx = self.tx2.get((cp, txid))
        if tx is None:
            tx = self.tx2[(cp, txid)] = {"id": txid, "start_line": line, "seq": None, "ended": False, "last": None}
            if ev != "Started":
                self.add("unknown-transaction", cp, ts, [line], f"TransactionEvent {ev} dla transakcji {txid} bez Started w logu")
                tx["no_start"] = True
        if isinstance(seq, int):
            if tx["seq"] is not None and seq <= tx["seq"]:
                self.add("seqno-duplicate", cp, ts, [line], f"seqNo {seq} po {tx['seq']} w transakcji {txid}")
            elif tx["seq"] is not None and seq > tx["seq"] + 1:
                self.add("seqno-gap", cp, ts, [line], f"brak seqNo {tx['seq'] + 1}–{seq - 1} w transakcji {txid} "
                                                     "(zgubione albo jeszcze w kolejce ładowarki)")
            tx["seq"] = max(seq, tx["seq"] if tx["seq"] is not None else seq)
        self.meter(tx, cp, ts, line, energy_wh(p.get("meterValue")))
        if ev == "Ended":
            tx["ended"] = True

    def response(self, cp, d, ts, line, mid, frame) -> None:
        call = self.pending.pop((cp, OPPOSITE[d], mid), None)
        if call is None:
            return
        if (ts - call["ts"]).total_seconds() > self.timeout:
            self.add("call-no-response", cp, call["ts"], [call["line"], line],
                     f"{call['action']}: odpowiedź po {(ts - call['ts']).total_seconds():.0f} s (> {self.timeout:g} s)")
        if frame[0] == 4:
            code = frame[2] if len(frame) > 2 else "?"
            self.add("callerror", cp, ts, [call["line"], line], f"CALLERROR {code} na {call['action']}")
        elif call["action"] == "StartTransaction" and isinstance(frame[2], dict) and "transactionId" in frame[2]:
            start = self.start16.pop((cp, mid), {})
            txid = str(frame[2]["transactionId"])
            tx = self.tx16[(cp, txid)] = {"id": txid, "lines": [start.get("line", call["line"]), line], "ts": call["ts"],
                                           "stopped": False, "last": None}
            if isinstance(start.get("meterStart"), (int, float)):
                self.meter(tx, cp, call["ts"], call["line"], [float(start["meterStart"])])

    def finish(self) -> dict:
        for (cp, _, mid), call in self.pending.items():
            self.add("call-no-response", cp, call["ts"], [call["line"]], f"{call['action']} (id „{mid}”) bez odpowiedzi do końca logu")
        for (cp, txid), tx in self.tx16.items():
            if not tx["stopped"]:
                self.add("open-transaction", cp, tx["ts"], tx["lines"], f"transakcja {txid} bez StopTransaction do końca logu")
        for (cp, txid), tx in self.tx2.items():
            if not tx["ended"] and not tx.get("no_start"):
                self.add("open-transaction", cp, None, [tx["start_line"]], f"transakcja {txid} bez TransactionEvent Ended do końca logu")
        self.findings.sort(key=lambda f: (f["cp"], ORDER[f["severity"]], f["lines"][0]))
        return {"stations": {cp: {"ocpp": st["ocpp"] or "nieznana", "frames": st["frames"]} for cp, st in self.stations.items()},
                "findings": self.findings}


def analyze(lines, ocpp: str = "auto", timeout: float = 30, skew: float = 300) -> dict:
    a = Analyzer(ocpp, timeout, skew)
    for i, raw in enumerate(lines, 1):
        if raw.strip():
            a.feed(raw, i)
    return a.finish()


def text(res: dict) -> str:
    out = []
    for cp, st in sorted(res["stations"].items()):
        fs = [f for f in res["findings"] if f["cp"] == cp]
        out.append(f"{cp} (OCPP {st['ocpp']}, ramek: {st['frames']}, ustaleń: {len(fs)})")
        out += [f"  [{f['severity'].upper()}] {f['ts'] or '—'} {f['code']} — {f['message']} "
                f"(linie {', '.join(map(str, f['lines']))})" for f in fs]
    bad = [f for f in res["findings"] if f["cp"] == "-"]
    if bad:
        out.append(f"Nieczytelne linie: {', '.join(str(f['lines'][0]) for f in bad)}")
    counts = {s: sum(f["severity"] == s for f in res["findings"]) for s in ORDER}
    out.append(f"Razem: high {counts['high']}, medium {counts['medium']}, low {counts['low']}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Analizator logów OCPP-J (1.6, 2.0.1) — ustalenia z numerami linii.")
    ap.add_argument("log", help="plik JSON Lines albo „-” (stdin)")
    ap.add_argument("--ocpp", choices=["auto", "1.6", "2.0.1"], default="auto")
    ap.add_argument("--timeout", type=float, default=30, help="maksymalny czas odpowiedzi na CALL w sekundach")
    ap.add_argument("--skew", type=float, default=300, help="dopuszczalna różnica zegara w sekundach")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        lines = sys.stdin.read().splitlines() if args.log == "-" else open(args.log, encoding="utf-8").read().splitlines()
    except OSError as e:
        print(f"✗ Nie można odczytać {args.log}: {e.strerror}", file=sys.stderr)
        return 2
    res = analyze(lines, args.ocpp, args.timeout, args.skew)
    print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else text(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
