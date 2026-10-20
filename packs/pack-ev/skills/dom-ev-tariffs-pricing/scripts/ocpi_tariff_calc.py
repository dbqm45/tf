#!/usr/bin/env python3
"""
Kalkulator ceny sesji z taryfy OCPI 2.2.1 dla okresów ładowania (`charging_periods` jak w CDR). Tylko biblioteka
standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py <taryfa.json> <okresy.json>
      [--cdr <cdr.json>] [--tz Europe/Warsaw] [--tolerance 0.01] [--json]

<okresy.json>: obiekt z `start_date_time`, `end_date_time` i `charging_periods` — może to być sam CDR. Taryfa i CDR
mogą być opakowane w odpowiedź OCPI (`{"data": …}`). Kod wyjścia: 0 — policzone (i zgodne z CDR), 1 — rozbieżność
z CDR większa niż tolerancja, 2 — błąd wejścia.

Reguły (OCPI 2.2.1-d2, mod_tariffs i mod_cdrs; źródło i sprzeczności przykładów: skill dom-ev-tariffs-pricing):
- dla każdego wymiaru (ENERGY, TIME, PARKING_TIME, FLAT) obowiązuje pierwszy element z pasującymi restrykcjami, który
  ma ten wymiar; restrykcje liczone na początku okresu (CPO dzieli okresy przy zmianie elementu), w czasie lokalnym
  `--tz` (strefa `Location.time_zone`; domyślnie UTC);
- FLAT raz na sesję; ENERGY za kWh; TIME i PARKING_TIME za godzinę;
- step_size raz dla ENERGY (suma energii, krok ostatniego użytego składnika) i raz dla czasu: zaokrągla się sumę wymiaru
  ostatniego płatnego okresu czasowego (TIME albo PARKING_TIME) krokiem jego składnika, nadwyżka idzie do tego okresu;
- VAT per składnik (brak pola `vat` = brak VAT); min_price i max_price osobno dla kwot bez VAT i z VAT;
- elementy rezerwacji (`reservation`) są pomijane z ostrzeżeniem; OCPI nie definiuje zaokrąglania cen — wynik ma
  4 miejsca po przecinku, zaokrąglenie na fakturze należy do CPO i przepisów.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
PRICED = ("FLAT", "ENERGY", "TIME", "PARKING_TIME")
COST_KEY = {"FLAT": "total_fixed_cost", "ENERGY": "total_energy_cost", "TIME": "total_time_cost",
            "PARKING_TIME": "total_parking_cost"}
STEP_UNIT = {"ENERGY": Decimal(1000), "TIME": Decimal(3600), "PARKING_TIME": Decimal(3600)}  # Wh / s na jednostkę ceny
Q = Decimal("0.0001")


class InputError(Exception):
    pass


def _d(x) -> Decimal:
    return Decimal(str(x))


def _ts(value: str) -> dt.datetime:
    try:
        t = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as e:
        raise InputError(f"zła data/czas: {value!r}") from e
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _hhmm(s: str) -> dt.time:
    return dt.time.fromisoformat(s)


def _num(x: Decimal) -> float:
    return float(x.quantize(Q, rounding=ROUND_HALF_UP))


def _time_ok(r: dict, local: dt.datetime) -> bool:
    """[start_time, end_time) w czasie lokalnym; end < start = przez północ; end 00:00 = do końca dnia."""
    t = local.time()
    start = _hhmm(r["start_time"]) if r.get("start_time") else dt.time(0, 0)
    end = _hhmm(r["end_time"]) if r.get("end_time") else None
    if end is None or end == dt.time(0, 0):
        return t >= start
    return start <= t < end if start < end else (t >= start or t < end)


class _Ctx:
    def __init__(self, local: dt.datetime, duration_s: float, energy_kwh: Decimal, dims: dict[str, Decimal]):
        self.local, self.duration_s, self.energy_kwh, self.dims = local, duration_s, energy_kwh, dims

    def value(self, kind: str, side: str) -> Decimal | None:
        """Prąd (CURRENT) lub moc (POWER) okresu: dla max_* bierze MAX_, dla min_* MIN_, potem średnią, potem drugą skrajną."""
        d = self.dims
        order = [f"{side}_{kind}", kind, f"{'MIN' if side == 'MAX' else 'MAX'}_{kind}"]
        for k in order:
            if k in d:
                return d[k]
        if kind == "POWER" and "ENERGY" in d and d.get("TIME"):
            return d["ENERGY"] / d["TIME"]
        return None


def _matches(r: dict | None, c: _Ctx, warn) -> bool:
    if not r:
        return True
    if r.get("start_time") or r.get("end_time"):
        if not _time_ok(r, c.local):
            return False
    date = c.local.date().isoformat()
    if r.get("start_date") and date < r["start_date"]:
        return False
    if r.get("end_date") and date >= r["end_date"]:
        return False
    if r.get("day_of_week") and DAYS[c.local.weekday()] not in r["day_of_week"]:
        return False
    if r.get("min_kwh") is not None and c.energy_kwh < _d(r["min_kwh"]):
        return False
    if r.get("max_kwh") is not None and c.energy_kwh >= _d(r["max_kwh"]):
        return False
    if r.get("min_duration") is not None and c.duration_s < r["min_duration"]:
        return False
    if r.get("max_duration") is not None and c.duration_s >= r["max_duration"]:
        return False
    for kind in ("CURRENT", "POWER"):
        for side in ("MIN", "MAX"):
            limit = r.get(f"{side.lower()}_{kind.lower()}")
            if limit is None:
                continue
            v = c.value(kind, side)
            if v is None:
                warn(f"restrykcja {side.lower()}_{kind.lower()} bez danych w okresie ({side}_{kind}/{kind}) — element pominięty")
                return False
            if (side == "MIN" and v < _d(limit)) or (side == "MAX" and v >= _d(limit)):
                return False
    return True


def _unwrap(obj):
    if isinstance(obj, dict) and "data" in obj and "status_code" in obj:
        return obj["data"]
    return obj


def calculate(tariff: dict, session: dict, tz: str = "UTC") -> dict:
    tariff, session = _unwrap(tariff), _unwrap(session)
    try:
        zone = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise InputError(f"nieznana strefa czasowa: {tz}") from e
    warnings: list[str] = []

    def warn(msg):
        if msg not in warnings:
            warnings.append(msg)

    try:
        elements = tariff["elements"]
        periods = sorted(session["charging_periods"], key=lambda p: _ts(p["start_date_time"]))
        start, end = _ts(session["start_date_time"]), _ts(session["end_date_time"])
    except (KeyError, TypeError) as e:
        raise InputError(f"brak pola {e} w taryfie lub okresach") from e
    if not periods:
        raise InputError("brak charging_periods")
    if any(el.get("restrictions", {}).get("reservation") for el in elements):
        warn("elementy taryfy z restrykcją reservation (rezerwacja) pominięte — kalkulator nie liczy kosztów rezerwacji")
    for key, cmp in (("start_date_time", lambda t: start < t), ("end_date_time", lambda t: start >= t)):
        if tariff.get(key) and cmp(_ts(tariff[key])):
            warn(f"sesja poza okresem ważności taryfy ({key} = {tariff[key]})")

    lines: list[dict] = []
    energy_so_far = Decimal(0)
    flat_done = False
    for i, p in enumerate(periods):
        p_start = _ts(p["start_date_time"])
        dims = {d["type"]: _d(d["volume"]) for d in p.get("dimensions", [])}
        ctx = _Ctx(p_start.astimezone(zone), (p_start - start).total_seconds(), energy_so_far, dims)
        chosen: dict[str, tuple[int, dict]] = {}
        for idx, el in enumerate(elements):
            r = el.get("restrictions")
            if r and r.get("reservation"):
                continue
            types = {c["type"] for c in el.get("price_components", [])} - set(chosen)
            if not types or not _matches(r, ctx, warn):
                continue
            for c in el["price_components"]:
                if c["type"] in types and c["type"] not in chosen:
                    chosen[c["type"]] = (idx, c)
        for typ in PRICED:
            if typ not in chosen:
                continue
            idx, comp = chosen[typ]
            if typ == "FLAT":
                if flat_done:
                    continue
                flat_done, volume = True, Decimal(1)
            elif typ in dims:
                volume = dims[typ]
            else:
                continue
            lines.append({"period": i, "start": p["start_date_time"], "type": typ, "element": idx, "volume": volume,
                          "billed": volume, "price": _d(comp["price"]), "vat": comp.get("vat"),
                          "step_size": int(comp.get("step_size", 1))})
        energy_so_far += dims.get("ENERGY", Decimal(0))

    _apply_step(lines, ("ENERGY",))
    _apply_step(lines, ("TIME", "PARKING_TIME"))

    totals = {k: [Decimal(0), Decimal(0)] for k in COST_KEY.values()}
    for ln in lines:
        excl = ln["billed"] * ln["price"]
        incl = excl * (1 + _d(ln["vat"]) / 100) if ln["vat"] is not None else excl
        ln["cost_excl_vat"], ln["cost_incl_vat"] = excl, incl
        totals[COST_KEY[ln["type"]]][0] += excl
        totals[COST_KEY[ln["type"]]][1] += incl
    excl = sum(v[0] for v in totals.values())
    incl = sum(v[1] for v in totals.values())
    for name, op in (("min_price", max), ("max_price", min)):
        lim = tariff.get(name)
        if lim:
            new = (op(excl, _d(lim["excl_vat"])) if lim.get("excl_vat") is not None else excl,
                   op(incl, _d(lim["incl_vat"])) if lim.get("incl_vat") is not None else incl)
            if new != (excl, incl):
                warn(f"{name} zastosowane: {_num(excl)}/{_num(incl)} → {_num(new[0])}/{_num(new[1])}")
            excl, incl = new

    used = {COST_KEY[ln["type"]] for ln in lines}
    out = {"currency": tariff.get("currency"), "total_cost": {"excl_vat": _num(excl), "incl_vat": _num(incl)}}
    for key, (e, i_) in totals.items():
        out[key] = {"excl_vat": _num(e), "incl_vat": _num(i_)} if key in used else None
    out["total_energy"] = _num(sum((_d(d["volume"]) for p in periods for d in p.get("dimensions", [])
                                    if d["type"] == "ENERGY"), Decimal(0)))
    out["total_time"] = _num(_d((end - start).total_seconds()) / 3600)
    out["total_parking_time"] = _num(sum((_d(d["volume"]) for p in periods for d in p.get("dimensions", [])
                                          if d["type"] == "PARKING_TIME"), Decimal(0)))
    out["lines"] = [{**ln, **{k: _num(ln[k]) for k in ("volume", "billed", "price", "cost_excl_vat", "cost_incl_vat")}}
                    for ln in lines]
    out["warnings"] = warnings
    out["_has_energy"] = any(d["type"] == "ENERGY" for p in periods for d in p.get("dimensions", []))
    return out


def _apply_step(lines: list[dict], types: tuple[str, ...]) -> None:
    """step_size raz na sesję: suma wymiaru ostatniego płatnego okresu, krok jego składnika, nadwyżka do tego okresu."""
    relevant = [ln for ln in lines if ln["type"] in types]
    if not relevant:
        return
    last = relevant[-1]
    unit = STEP_UNIT[last["type"]]
    total = sum(ln["billed"] for ln in relevant if ln["type"] == last["type"]) * unit
    # wolumeny w h i kWh są zaokrąglone w CDR (0,666667 h ≠ 2400 s) — przed krokiem do pełnej sekundy / 0,01 Wh
    total = total.quantize(Decimal("1") if last["type"] != "ENERGY" else Decimal("0.01"), rounding=ROUND_HALF_UP)
    step = Decimal(max(last["step_size"], 1))
    rounded = Decimal(math.ceil(total / step)) * step
    others = sum(ln["billed"] for ln in relevant if ln["type"] == last["type"] and ln is not last)
    last["billed"] = max(rounded / unit - others, last["billed"])


def compare(result: dict, cdr: dict, tolerance: float = 0.01) -> list[dict]:
    """Rozbieżności między wyliczeniem a kosztami i czasami w CDR (tylko pola obecne w CDR)."""
    cdr = _unwrap(cdr)
    tol = _d(tolerance)
    diffs = []
    for key in ("total_cost", *COST_KEY.values()):
        theirs = cdr.get(key)
        if not theirs:
            continue
        ours = result.get(key) or {"excl_vat": 0.0, "incl_vat": 0.0}
        for part in ("excl_vat", "incl_vat"):
            if theirs.get(part) is None:
                continue
            if abs(_d(ours[part]) - _d(theirs[part])) > tol:
                diffs.append({"field": f"{key}.{part}", "calculated": ours[part], "cdr": theirs[part]})
    for key in ("total_energy", "total_time", "total_parking_time"):
        if cdr.get(key) is None or (key == "total_energy" and not result.get("_has_energy")):
            continue
        if abs(_d(result[key]) - _d(cdr[key])) > tol:
            diffs.append({"field": key, "calculated": result[key], "cdr": cdr[key]})
    return diffs


def _load(path: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        raise InputError(f"nie można odczytać {path}: {e.strerror}") from e
    except json.JSONDecodeError as e:
        raise InputError(f"{path}: zły JSON ({e.msg}, linia {e.lineno})") from e


def describe(r: dict, diffs: list[dict] | None) -> str:
    cur = r["currency"] or ""
    out = [f"Koszt sesji: {r['total_cost']['excl_vat']} {cur} bez VAT, {r['total_cost']['incl_vat']} {cur} z VAT"]
    for key in COST_KEY.values():
        if r.get(key):
            out.append(f"  {key}: {r[key]['excl_vat']} / {r[key]['incl_vat']}")
    out.append(f"  energia {r['total_energy']} kWh, czas sesji {r['total_time']} h, postój {r['total_parking_time']} h")
    for ln in r["lines"]:
        out.append(f"  okres {ln['period']} {ln['start']} {ln['type']}: {ln['volume']} → {ln['billed']} × {ln['price']}"
                   f" (element {ln['element']}, step {ln['step_size']}) = {ln['cost_excl_vat']}")
    out += [f"  ⚠ {w}" for w in r["warnings"]]
    if diffs is not None:
        out.append("✓ zgodne z CDR" if not diffs else "✗ rozbieżności z CDR:")
        out += [f"  - {d['field']}: wyliczone {d['calculated']}, w CDR {d['cdr']}" for d in diffs]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Cena sesji z taryfy OCPI 2.2.1 i porównanie z CDR (bez sieci).")
    ap.add_argument("tariff", help="taryfa OCPI (JSON)")
    ap.add_argument("periods", help="obiekt z start_date_time, end_date_time i charging_periods (np. CDR)")
    ap.add_argument("--cdr", help="CDR do porównania kosztów")
    ap.add_argument("--tz", default="UTC", help="strefa czasowa lokacji (IANA), np. Europe/Warsaw")
    ap.add_argument("--tolerance", type=float, default=0.01, help="dopuszczalna różnica kwot i czasów")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = calculate(_load(args.tariff), _load(args.periods), args.tz)
        diffs = compare(result, _load(args.cdr), args.tolerance) if args.cdr else None
    except InputError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    result.pop("_has_energy", None)
    if args.json:
        print(json.dumps({**result, **({"cdr_diffs": diffs} if diffs is not None else {})}, ensure_ascii=False, indent=1))
    else:
        print(describe(result, diffs))
    return 1 if diffs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
