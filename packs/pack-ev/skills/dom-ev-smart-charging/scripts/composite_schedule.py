#!/usr/bin/env python3
"""
Composite schedule OCPP z profili ładowania (1.6 i 2.0.1) — to, co ładowarka powinna zwrócić na GetCompositeSchedule.
Tylko biblioteka standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py <profile.json> --start <ISO> --duration <s>
      [--tx-start <ISO>] [--unit A|W] [--default-limit 48] [--voltage 230] [--json]

<profile.json>: lista profili, {"profiles": [...]} albo ładunki SetChargingProfile (1.6 `csChargingProfiles`,
2.0.1 `chargingProfile`). Kod wyjścia: 0 — policzone, 1 — co najmniej jeden profil odrzucony walidacją (pominięty),
2 — błąd wejścia.

Reguły (wg implementacji referencyjnej EVerest libocpp, doc/common/smart_charging_profiles.md i testów; źródło
i niespójności: skill dom-ev-smart-charging):
- grupy: Max (ChargePointMaxProfile / ChargingStationMaxProfile), ExternalConstraints (2.0.1), TxDefault, Tx;
  w grupie w danej chwili obowiązuje aktywny profil o najwyższym stackLevel;
- aktywny: validFrom ≤ t < validTo; początek harmonogramu: Absolute — startSchedule, Relative — start transakcji
  (--tx-start) albo --start, Recurring — startSchedule przesunięty o pełne doby/tygodnie; poza `duration` nieaktywny;
- wynik: Tx, a gdy go brak TxDefault, a gdy go brak limit domyślny (48 A jak w libocpp; --default-limit 0 = „nie
  ładuj”), ograniczony przez Max i ExternalConstraints;
- A↔W: W = A × napięcie × fazy; fazy okresu = najmniejsza podana liczba faz aktywnych profili, domyślnie 3;
- 2.0.1: z listy `chargingSchedule` brany jest pierwszy harmonogram (kolejne dotyczą ISO 15118 — ostrzeżenie).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

GROUP = {"ChargePointMaxProfile": "Max", "ChargingStationMaxProfile": "Max",
         "ChargingStationExternalConstraints": "External", "TxDefaultProfile": "TxDefault", "TxProfile": "Tx"}
RECUR = {"Daily": 86400, "Weekly": 7 * 86400}
DEFAULT_PHASES = 3


class InputError(Exception):
    pass


def _ts(v) -> dt.datetime:
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError as e:
        raise InputError(f"zła data: {v!r}") from e
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _schedule(p: dict) -> dict:
    s = p.get("chargingSchedule")
    return (s[0] if s else {}) if isinstance(s, list) else (s or {})


def _pid(p: dict):
    return p.get("chargingProfileId", p.get("id"))


def validate(p: dict) -> list[str]:
    """Błędy profilu wg reguł K01 (OCPP 2.0.1) zaimplementowanych w libocpp; puste = profil poprawny."""
    errs = []
    purpose, kind = p.get("chargingProfilePurpose"), p.get("chargingProfileKind")
    s = _schedule(p)
    periods = s.get("chargingSchedulePeriod") or []
    if purpose not in GROUP:
        errs.append(f"nieznany chargingProfilePurpose {purpose!r}")
    if kind not in ("Absolute", "Relative", "Recurring"):
        errs.append(f"nieznany chargingProfileKind {kind!r}")
    if s.get("chargingRateUnit") not in ("A", "W"):
        errs.append(f"chargingRateUnit {s.get('chargingRateUnit')!r} — dozwolone A albo W")
    if not periods:
        errs.append("brak chargingSchedulePeriod")
    else:
        if periods[0].get("startPeriod") != 0:
            errs.append(f"pierwszy startPeriod musi być 0 (jest {periods[0].get('startPeriod')})")
        starts = [x.get("startPeriod", -1) for x in periods]
        if starts != sorted(set(starts)):
            errs.append("startPeriod muszą rosnąć")
    if kind in ("Absolute", "Recurring") and not s.get("startSchedule"):
        errs.append(f"{kind} wymaga startSchedule")
    if kind == "Relative" and s.get("startSchedule"):
        errs.append("Relative nie może mieć startSchedule")
    if GROUP.get(purpose) == "Max" and kind == "Relative":
        errs.append("profil Max nie może być Relative")
    if kind == "Recurring" and p.get("recurrencyKind") not in RECUR:
        errs.append(f"Recurring wymaga recurrencyKind Daily albo Weekly (jest {p.get('recurrencyKind')!r})")
    return errs


class _Profile:
    def __init__(self, p: dict, origin: dt.datetime):
        self.raw, self.id, self.group = p, _pid(p), GROUP[p["chargingProfilePurpose"]]
        self.purpose, self.kind, self.level = p["chargingProfilePurpose"], p["chargingProfileKind"], p.get("stackLevel", 0)
        s = _schedule(p)
        self.unit, self.duration = s["chargingRateUnit"], s.get("duration")
        self.periods = sorted(s["chargingSchedulePeriod"], key=lambda x: x["startPeriod"])
        self.valid_from = _ts(p["validFrom"]) if p.get("validFrom") else None
        self.valid_to = _ts(p["validTo"]) if p.get("validTo") else None
        self.base = _ts(s["startSchedule"]) if s.get("startSchedule") else origin
        self.step = RECUR.get(p.get("recurrencyKind")) if self.kind == "Recurring" else None

    def start_for(self, t: dt.datetime) -> dt.datetime:
        if not self.step:
            return self.base
        k = math.floor((t - self.base).total_seconds() / self.step)
        return self.base + dt.timedelta(seconds=k * self.step)

    def at(self, t: dt.datetime):
        if (self.valid_from and t < self.valid_from) or (self.valid_to and t >= self.valid_to):
            return None
        start = self.start_for(t)
        off = (t - start).total_seconds()
        if off < 0 or (self.duration is not None and off >= self.duration):
            return None
        period = [x for x in self.periods if x["startPeriod"] <= off][-1]
        return period

    def breakpoints(self, ws: dt.datetime, we: dt.datetime) -> set[dt.datetime]:
        pts = {x for x in (self.valid_from, self.valid_to) if x}
        starts = [self.base]
        if self.step:
            k0 = math.floor((ws - self.base).total_seconds() / self.step) - 1
            k1 = math.floor((we - self.base).total_seconds() / self.step) + 1
            starts = [self.base + dt.timedelta(seconds=k * self.step) for k in range(k0, k1 + 1)]
        for st in starts:
            pts.update(st + dt.timedelta(seconds=x["startPeriod"]) for x in self.periods)
            if self.duration is not None:
                pts.add(st + dt.timedelta(seconds=self.duration))
        return {x for x in pts if ws < x < we}


def _unwrap(data) -> list[dict]:
    if isinstance(data, dict):
        data = data.get("profiles", [data])
    out = []
    for item in data:
        if isinstance(item, dict) and ("csChargingProfiles" in item or "chargingProfile" in item):
            item = item.get("csChargingProfiles") or item.get("chargingProfile")
        out.append(item)
    return out


def compute(profiles: list[dict], start: str, duration: int, tx_start: str | None = None, unit: str = "A",
            default_limit: float = 48.0, voltage: float = 230.0) -> dict:
    ws = _ts(start)
    we = ws + dt.timedelta(seconds=int(duration))
    origin = _ts(tx_start) if tx_start else ws
    valid, invalid, warnings = [], [], []
    for p in _unwrap(profiles):
        errs = validate(p)
        if errs:
            invalid.append({"id": _pid(p), "errors": errs})
            continue
        if isinstance(p.get("chargingSchedule"), list) and len(p["chargingSchedule"]) > 1:
            warnings.append(f"profil {_pid(p)}: kilka chargingSchedule — liczony pierwszy (pozostałe dla ISO 15118)")
        valid.append(_Profile(p, origin))

    cuts = sorted({ws} | set().union(*(pr.breakpoints(ws, we) for pr in valid)) if valid else {ws})
    out = []
    for t in cuts:
        active = {}
        for pr in valid:
            period = pr.at(t)
            if period is None:
                continue
            best = active.get(pr.group)
            if best is None or pr.level >= best[0].level:
                active[pr.group] = (pr, period)
        given = [per["numberPhases"] for _, per in active.values() if per.get("numberPhases")]
        phases = min(given) if given else DEFAULT_PHASES

        def amps(entry):
            pr, per = entry
            return per["limit"] if pr.unit == "A" else per["limit"] / (voltage * phases)

        base = active.get("Tx") or active.get("TxDefault")
        limit, source = (amps(base), f"{base[0].purpose}#{base[0].id}") if base else (float(default_limit), "default")
        for g in ("Max", "External"):
            if g in active and amps(active[g]) < limit:
                limit, source = amps(active[g]), f"{active[g][0].purpose}#{active[g][0].id}"
        value = limit if unit == "A" else limit * voltage * phases
        value = round(value, 3)
        off = int((t - ws).total_seconds())
        if out and out[-1]["limit"] == value and out[-1]["numberPhases"] == phases:
            continue
        out.append({"startPeriod": off, "limit": value, "numberPhases": phases, "source": source})
    return {"startSchedule": _iso(ws), "duration": int(duration), "chargingRateUnit": unit,
            "chargingSchedulePeriod": out, "invalid": invalid, "warnings": warnings}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Composite schedule OCPP 1.6/2.0.1 z profili ładowania (bez sieci).")
    ap.add_argument("profiles", help="plik JSON z profilami")
    ap.add_argument("--start", required=True, help="początek okna (ISO 8601)")
    ap.add_argument("--duration", type=int, required=True, help="długość okna w sekundach")
    ap.add_argument("--tx-start", help="start transakcji (dla profili Relative)")
    ap.add_argument("--unit", choices=["A", "W"], default="A")
    ap.add_argument("--default-limit", type=float, default=48.0, help="limit w A, gdy żaden profil nie działa (0 = nie ładuj)")
    ap.add_argument("--voltage", type=float, default=230.0, help="napięcie fazowe do przeliczeń A↔W")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        data = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
        r = compute(data, args.start, args.duration, args.tx_start, args.unit, args.default_limit, args.voltage)
    except (OSError, json.JSONDecodeError, InputError, KeyError, TypeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"Composite schedule od {r['startSchedule']} przez {r['duration']} s ({r['chargingRateUnit']}):")
        for p in r["chargingSchedulePeriod"]:
            print(f"  +{p['startPeriod']:>6} s  {p['limit']:>10} {r['chargingRateUnit']}  fazy {p['numberPhases']}  ← {p['source']}")
        for x in r["invalid"]:
            print(f"  ✗ profil {x['id']} pominięty: {'; '.join(x['errors'])}")
        for w in r["warnings"]:
            print(f"  ⚠ {w}")
    return 1 if r["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
