#!/usr/bin/env python3
"""
Rejestr standardów i przepisów EV: wersje, statusy i daty (stosowanie, transpozycja, terminy) z datą ostatniego
sprawdzenia. Tylko biblioteka standardowa. Sieć: brak.

  python3 .claude/skills/dom-ev-knowledge-base/scripts/standards_check.py [--registry <plik>] [--today RRRR-MM-DD]
      [--horizon 180] [--strict] [--json] [--root <projekt>]

Domyślny rejestr: `.claude/skills/dom-ev-knowledge-base/references/rejestr-standardow.json`. Wpis:
  {id, nazwa, rodzaj: standard|specyfikacja|regulacja|norma, rynek: EU|PL|US|global, wersja, status:
   obowiązuje|przyjęty|projekt|uchylony|zastąpiony, zrodlo: "kb:<id>" albo URL https, sprawdzono: RRRR-MM-DD,
   skille: [...], daty: [{co, data|null, do_weryfikacji?}], zastapiony_przez?, uwagi?}
Raport:
- stale — sprawdzono dawniej niż `przeglad_miesiecy` (domyślnie 6) → odśwież wpis (researcher, kb.py ingest);
- recent — data z `daty`, która minęła od ostatniego sprawdzenia → przejrzyj skille z listy `skille`;
- upcoming — data w ciągu `--horizon` dni;
- unverified — daty nieznane albo oznaczone do weryfikacji.
Kod wyjścia: 0 — rejestr poprawny (z --strict: także bez stale i recent), 1 — są stale/recent przy --strict,
2 — błędy rejestru.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = next((p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir()), Path.cwd())
DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "references" / "rejestr-standardow.json"
RODZAJ = {"standard", "specyfikacja", "regulacja", "norma"}
STATUS = {"obowiązuje", "przyjęty", "projekt", "uchylony", "zastąpiony"}
RYNEK = {"EU", "PL", "US", "global"}
REQUIRED = ("id", "nazwa", "rodzaj", "rynek", "status", "zrodlo", "sprawdzono")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InputError(Exception):
    pass


def _date(v):
    if not isinstance(v, str) or not DATE_RE.match(v):
        return None
    try:
        return dt.date.fromisoformat(v)
    except ValueError:
        return None


def _add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _kb_ids(root: Path) -> set[str]:
    p = root / ".claude" / "skills" / "dom-ev-knowledge-base" / "references" / "zrodla.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {s.get("id") for s in (d.get("sources", []) if isinstance(d, dict) else d)}


def check(reg: dict, today: str | None = None, root: Path = ROOT, horizon_days: int = 180) -> dict:
    if not isinstance(reg, dict) or not isinstance(reg.get("wpisy"), list):
        raise InputError("rejestr musi mieć listę `wpisy`")
    t = _date(today) if today else dt.date.today()
    if t is None:
        raise InputError(f"zła data --today: {today!r}")
    months = int(reg.get("przeglad_miesiecy", 6))
    kb, skills_dir = _kb_ids(Path(root)), Path(root) / ".claude" / "skills"
    errors, stale, recent, upcoming, unverified = [], [], [], [], []

    def err(code, eid, msg):
        errors.append({"code": code, "id": eid, "msg": msg})

    ids = [e.get("id") for e in reg["wpisy"] if isinstance(e, dict)]
    seen = set()
    for e in reg["wpisy"]:
        if not isinstance(e, dict):
            err("type", None, "wpis musi być obiektem")
            continue
        eid = e.get("id")
        for k in REQUIRED:
            if k not in e:
                err("missing", eid, f"brak pola {k}")
        if eid in seen:
            err("duplicate", eid, "powtórzone id")
        seen.add(eid)
        for k, allowed in (("rodzaj", RODZAJ), ("status", STATUS), ("rynek", RYNEK)):
            if k in e and e[k] not in allowed:
                err("value", eid, f"{k}={e[k]!r} spoza {sorted(allowed)}")
        checked = _date(e.get("sprawdzono"))
        if "sprawdzono" in e and checked is None:
            err("value", eid, f"sprawdzono musi być RRRR-MM-DD: {e.get('sprawdzono')!r}")
        src = e.get("zrodlo", "")
        if isinstance(src, str) and src.startswith("kb:"):
            if src[3:] not in kb:
                err("source", eid, f"{src} nie ma w zrodla.json")
        elif "zrodlo" in e and not (isinstance(src, str) and src.startswith("https://")):
            err("source", eid, f"zrodlo to kb:<id> albo URL https: {src!r}")
        for s in e.get("skille", []) or []:
            if skills_dir.is_dir() and not (skills_dir / s / "SKILL.md").exists():
                err("skill", eid, f"nie ma skilla {s}")
        if e.get("status") in ("uchylony", "zastąpiony"):
            rep = e.get("zastapiony_przez")
            if not rep or rep not in ids:
                err("replaced-by", eid, f"status {e.get('status')} wymaga zastapiony_przez z istniejącym id (jest {rep!r})")
        if e.get("do_weryfikacji"):
            unverified.append({"id": eid, "co": "wpis"})
        for x in e.get("daty", []) or []:
            if not isinstance(x, dict) or "co" not in x:
                err("value", eid, f"daty[]: wpis {{co, data}}: {x!r}")
                continue
            d = x.get("data")
            if d is None or x.get("do_weryfikacji"):
                unverified.append({"id": eid, "co": x["co"], "data": d})
                if d is None:
                    continue
            dd = _date(d)
            if dd is None:
                err("value", eid, f"daty[{x['co']}]: zła data {d!r}")
                continue
            if checked and checked < dd <= t:
                recent.append({"id": eid, "co": x["co"], "data": d, "skille": e.get("skille", [])})
            if t < dd <= t + dt.timedelta(days=horizon_days):
                upcoming.append({"id": eid, "co": x["co"], "data": d})
        if checked and _add_months(checked, months) < t:
            stale.append({"id": eid, "sprawdzono": e.get("sprawdzono")})
    upcoming.sort(key=lambda u: u["data"])
    return {"entries": len(reg["wpisy"]), "months": months, "today": t.isoformat(), "errors": errors, "stale": stale,
            "recent": recent, "upcoming": upcoming, "unverified": unverified}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Rejestr standardów i przepisów EV: poprawność, terminy, zmiany.")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--today")
    ap.add_argument("--horizon", type=int, default=180, help="ile dni naprzód pokazywać nadchodzące daty")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--strict", action="store_true", help="kod 1, gdy są wpisy po terminie albo daty, które minęły")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        r = check(reg, args.today, Path(args.root), args.horizon)
    except (OSError, json.JSONDecodeError, InputError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"Rejestr: {r['entries']} wpisów, dziś {r['today']}, ponowne sprawdzenie co {r['months']} mies.")
        for x in r["errors"]:
            print(f"  ✗ [{x['code']}] {x['id']}: {x['msg']}")
        for x in r["stale"]:
            print(f"  ⚠ do ponownego sprawdzenia: {x['id']} (sprawdzono {x['sprawdzono']})")
        for x in r["recent"]:
            print(f"  ⚠ minęło od sprawdzenia: {x['id']} — {x['co']} {x['data']} → przejrzyj {', '.join(x['skille']) or 'skille'}")
        for x in r["upcoming"]:
            print(f"  → nadchodzi: {x['data']} {x['id']} — {x['co']}")
        if r["unverified"]:
            print(f"  ? do weryfikacji: {len(r['unverified'])} dat/wpisów (--json pokazuje listę)")
    if r["errors"]:
        return 2
    return 1 if args.strict and (r["stale"] or r["recent"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
