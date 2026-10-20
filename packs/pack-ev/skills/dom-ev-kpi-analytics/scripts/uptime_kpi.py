#!/usr/bin/env python3
"""
Dostępność portów ładowania (uptime) ze zdarzeń statusu: trzy definicje obok siebie, MTTR, MTBF, skuteczność sesji.
Tylko biblioteka standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-kpi-analytics/scripts/uptime_kpi.py <dane.json> [--threshold 97] [--unknown outage|exclude]
      [--up-status <S> ...] [--down-status <S> ...] [--json]

<dane.json>: {"window": {"start": ISO, "end": ISO},
              "events": [{"ts": ISO, "port": "...", "status": "Available|Faulted|...", "reason": "utility"?}, ...],
              "exclusions": [{"port"?: "...", "start": ISO, "end": ISO, "reason": "maintenance"}]?,
              "sessions": [{"port": "...", "outcome": "ok|failed"}]?}
Zdarzenia to zwykle StatusNotification z OCPP plus pseudo-status `Offline` z CSMS (brak połączenia, heartbeat).
Status obowiązuje do następnego zdarzenia portu; stan na początku okna bierzesz z ostatniego zdarzenia przed oknem.

Definicje (minuty okna W, przestój T_out, przestój z przyczyn wyłączonych T_ex):
- surowa:  (W − T_out) / W                          — co widzi kierowca;
- NEVI:    (W − (T_out − T_ex)) / W                 — 23 CFR 680.116(b), na rok 525 600 min, każdy port osobno, próg 97 %;
- SLA:     (W − T_out) / (W − T_ex)                 — wyłączenia usunięte z mianownika (częste w umowach serwisowych).
Wyłączenia NEVI: utility (przerwa w dostawie energii), vehicle (wina pojazdu), maintenance (planowana konserwacja),
vandalism, disaster, outside_hours (poza godzinami pracy stacji). Wyłącza się PRZESTÓJ z tej przyczyny, nie czas.
Operator musi umieć wykazać, że port bez tej przyczyny by działał — skrypt tego nie sprawdza.

Czas nieznany (brak statusu przed oknem): domyślnie przestój (--unknown outage), albo poza oknem (--unknown exclude).
Kod wyjścia: 0 — każdy port ≥ próg (NEVI), 1 — co najmniej jeden poniżej, 2 — błąd wejścia.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

UP = {"Available", "Occupied", "Charging", "Preparing", "SuspendedEV", "SuspendedEVSE", "Finishing", "Reserved"}
DOWN = {"Faulted", "Unavailable", "Offline"}
EXCLUDED = {"utility", "vehicle", "maintenance", "vandalism", "disaster", "outside_hours"}
NEVI_YEAR_MIN = 525600


class InputError(Exception):
    pass


def _ts(v) -> dt.datetime:
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError as e:
        raise InputError(f"zła data: {v!r}") from e
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _min(seconds: float) -> float:
    return round(seconds / 60, 3)


def _pct(num: float, den: float):
    return round(num / den * 100, 3) if den > 0 else None


def _merge(windows):
    out = []
    for s, e in sorted(windows):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _overlap(s, e, windows) -> float:
    return sum(max(0.0, (min(e, we) - max(s, ws)).total_seconds()) for ws, we in windows)


def compute(d: dict, threshold: float = 97.0, unknown: str = "outage", up_status=(), down_status=()) -> dict:
    if not isinstance(d, dict) or "window" not in d:
        raise InputError("brak pola window {start, end}")
    ws, we = _ts(d["window"].get("start")), _ts(d["window"].get("end"))
    if we <= ws:
        raise InputError("koniec okna musi być po początku")
    if unknown not in ("outage", "exclude"):
        raise InputError("unknown: outage albo exclude")
    up = (UP | set(up_status)) - set(down_status)
    down = (DOWN | set(down_status)) - set(up_status)
    warnings = []

    def warn(code, msg):
        if not any(w["code"] == code and w["msg"] == msg for w in warnings):
            warnings.append({"code": code, "msg": msg})

    span = (we - ws).total_seconds()
    if 360 * 86400 <= span <= 370 * 86400 and span != NEVI_YEAR_MIN * 60:
        warn("nevi-window", f"okno ma {_min(span)} min; NEVI liczy rok jako 525 600 min — porównując z raportem NEVI, przelicz")

    by_port: dict = {}
    for e in d.get("events", []):
        if e.get("status") not in up | down:
            raise InputError(f"nieznany status {e.get('status')!r} portu {e.get('port')!r} — zmapuj go "
                             "(--up-status / --down-status)")
        by_port.setdefault(str(e.get("port")), []).append((_ts(e.get("ts")), e["status"], e.get("reason")))

    excl_windows: dict = {}
    for x in d.get("exclusions", []) or []:
        if x.get("reason") not in EXCLUDED:
            warn("reason-not-excluded", f"okno wyłączenia z przyczyną {x.get('reason')!r} spoza listy NEVI — pominięte")
            continue
        s, e = _ts(x.get("start")), _ts(x.get("end"))
        excl_windows.setdefault(x.get("port"), []).append((s, e))

    sessions: dict = {}
    for s in d.get("sessions", []) or []:
        if s.get("outcome") not in ("ok", "failed"):
            raise InputError(f"outcome sesji musi być ok albo failed: {s.get('outcome')!r}")
        sessions.setdefault(str(s.get("port")), []).append(s["outcome"] == "ok")

    ports = {}
    for pid in sorted(by_port):
        evs = sorted(by_port[pid], key=lambda x: x[0])
        windows = _merge(excl_windows.get(pid, []) + excl_windows.get(None, []))
        before = [x for x in evs if x[0] <= ws]
        segs = []                                     # (start, end, kind, reason)
        cur = ("up" if before[-1][1] in up else "down", before[-1][2]) if before else ("unknown", None)
        if not before:
            warn("unknown-start", f"port {pid}: brak statusu przed początkiem okna — czas do pierwszego zdarzenia nieznany")
        t = ws
        for ts, status, reason in evs:
            if ts <= ws:
                continue
            if ts >= we:
                break
            segs.append((t, ts, *cur))
            t, cur = ts, ("up" if status in up else "down", reason)
        segs.append((t, we, *cur))

        out_s = excl_s = unk_s = 0.0
        episodes, prev_down = 0, False
        for s, e, kind, reason in segs:
            length = (e - s).total_seconds()
            if length <= 0:
                continue
            if kind == "unknown":
                unk_s += length
                prev_down = False
                continue
            if kind == "down":
                out_s += length
                if not prev_down:
                    episodes += 1
                if reason in EXCLUDED:
                    excl_s += length
                else:
                    if reason:
                        warn("reason-not-excluded", f"przyczyna {reason!r} spoza listy NEVI — przestój nie jest wyłączony")
                    excl_s += _overlap(s, e, windows)
            prev_down = kind == "down"

        w = span
        if unknown == "outage":
            known_out = out_s
            out_s += unk_s
        else:
            known_out = out_s
            w -= unk_s
        up_s = w - out_s
        ok = sessions.get(pid, [])
        ports[pid] = {
            "window_min": _min(w), "outage_min": _min(out_s), "excluded_min": _min(excl_s), "unknown_min": _min(unk_s),
            "uptime_raw": _pct(w - out_s, w), "uptime_nevi": _pct(w - (out_s - excl_s), w),
            "uptime_sla": _pct(w - out_s, w - excl_s),
            "outages": episodes, "mttr_min": _min(known_out / episodes) if episodes else None,
            "mtbf_min": _min(up_s / episodes) if episodes else None,
            "sessions": len(ok), "session_success": _pct(sum(ok), len(ok)) if ok else None,
        }

    vals = [p["uptime_nevi"] for p in ports.values() if p["uptime_nevi"] is not None]
    all_ok = [x for v in sessions.values() for x in v]
    summary = {"ports": len(ports), "threshold": float(threshold),
               "mean_uptime_nevi": round(sum(vals) / len(vals), 3) if vals else None,
               "below_threshold": sorted(pid for pid, p in ports.items()
                                         if p["uptime_nevi"] is not None and p["uptime_nevi"] < threshold),
               "session_success": _pct(sum(all_ok), len(all_ok)) if all_ok else None}
    return {"window": {"start": d["window"]["start"], "end": d["window"]["end"]}, "ports": ports,
            "summary": summary, "warnings": warnings}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Uptime portów ładowania: surowy, NEVI i SLA; MTTR, MTBF, sesje.")
    ap.add_argument("data", help="plik JSON z oknem, zdarzeniami statusu, wyłączeniami i sesjami")
    ap.add_argument("--threshold", type=float, default=97.0, help="próg uptime NEVI w %% (domyślnie 97)")
    ap.add_argument("--unknown", choices=["outage", "exclude"], default="outage")
    ap.add_argument("--up-status", nargs="*", default=[], help="dodatkowe statusy liczone jako dostępne")
    ap.add_argument("--down-status", nargs="*", default=[], help="dodatkowe statusy liczone jako przestój (np. PAUSED)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        d = json.loads(Path(args.data).read_text(encoding="utf-8"))
        r = compute(d, args.threshold, args.unknown, args.up_status, args.down_status)
    except (OSError, json.JSONDecodeError, InputError, KeyError, TypeError, AttributeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"Okno {r['window']['start']} → {r['window']['end']}, próg {r['summary']['threshold']} % (NEVI)")
        print(f"  {'port':<14} {'surowy':>8} {'NEVI':>8} {'SLA':>8} {'przestój':>10} {'wył.':>8} {'MTTR':>8} {'sesje':>7}")
        for pid, p in r["ports"].items():
            f = lambda v: "—" if v is None else f"{v:.3f}"
            s = "—" if p["session_success"] is None else f"{p['session_success']:.1f}%"
            mark = " ✗" if pid in r["summary"]["below_threshold"] else ""
            print(f"  {pid:<14} {f(p['uptime_raw']):>8} {f(p['uptime_nevi']):>8} {f(p['uptime_sla']):>8} "
                  f"{p['outage_min']:>10} {p['excluded_min']:>8} {('—' if p['mttr_min'] is None else p['mttr_min']):>8} {s:>7}{mark}")
        sm = r["summary"]
        print(f"  średnia NEVI: {sm['mean_uptime_nevi']} %; poniżej progu: {', '.join(sm['below_threshold']) or 'brak'}")
        for w in r["warnings"]:
            print(f"  ⚠ [{w['code']}] {w['msg']}")
    return 1 if r["summary"]["below_threshold"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
