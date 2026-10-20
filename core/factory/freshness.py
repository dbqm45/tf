#!/usr/bin/env python3
"""
Aktualność skilli: terminy przeglądu (`metadata.przeglad`) i znaczniki [niezweryfikowane] (tylko biblioteka standardowa).

  python3 factory/freshness.py                         # skille po terminie, z terminem ≤30 dni, bez terminu
  python3 factory/freshness.py --json                  # to samo jako JSON (np. dla przeglądu okresowego)
  python3 factory/freshness.py --strict                # kod 1, gdy jakiś skill jest po terminie
  python3 factory/freshness.py --reviewed <skill…>     # po przeglądzie: nowy termin = dziś + interwał skilla
  python3 factory/freshness.py --reviewed <skill> --date 2026-10-03   # przegląd z podanego dnia
  --today RRRR-MM-DD (data odniesienia), --root <katalog projektu>

Termin przeglądu to data, do której treść skilla (wersje, przepisy, standardy, metody) uznajemy za aktualną. Po
terminie skill nadal działa; agent sprawdza wtedy ulotne fakty w chwili użycia (core-source-research), a przegląd
w repozytorium fabryki odświeża treść i ustawia nowy termin. Interwał w miesiącach: wyjątek dla skilla, potem
najdłuższy pasujący prefiks, potem domyślny. Nakładki dokładają swoje interwały (`freshness` w pack.yaml), a projekt
może je nadpisać w `factory/config.yaml` → `freshness` (te same klucze co DEFAULT_POLICY). Linia `przeglad` nie wchodzi
do odcisku bramki jakości.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOON_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REVIEW_RE = re.compile(r"^  przeglad:[ \t]*(.*?)[ \t]*$", re.M)
UNVERIFIED = "[niezweryfikowane"

DEFAULT_POLICY = {
    "default_months": 12,
    # wersje frameworków i narzędzi zmieniają się najszybciej, języki — co pół roku; wymiary nakładek: pack.yaml
    "prefixes": {"fw-": 3, "tool-": 3, "lang-": 6},
    "skills": {},
}


def load_policy(root: Path = ROOT) -> dict:
    pol = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_POLICY.items()}
    cfg = root / "factory" / "config.yaml"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_packs_fresh", root / "factory" / "packs.py")
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        raw = pm.load_yaml(cfg)
        packs = pm.compose(root, raw)["freshness"]          # interwały z nakładek
        own = raw.get("freshness") or {}                    # nadpisania projektu
    except Exception:  # brak fabryki w katalogu albo uszkodzona konfiguracja — wartości domyślne
        return pol
    for k in ("prefixes", "skills"):
        pol[k].update(packs.get(k) or {})
    if isinstance(own.get("default_months"), int):
        pol["default_months"] = own["default_months"]
    for k in ("prefixes", "skills"):
        if isinstance(own.get(k), dict):
            pol[k].update(own[k])
    return pol


def interval(name: str, policy: dict) -> int:
    if name in policy["skills"]:
        return policy["skills"][name]
    hits = [p for p in policy["prefixes"] if name.startswith(p)]
    return policy["prefixes"][max(hits, key=len)] if hits else policy["default_months"]


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    year, month = d.year + y, m + 1
    return dt.date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def frontmatter(text: str) -> tuple[int, int] | None:
    """Zakres (początek, koniec) frontmattera bez znaczników `---`; None, gdy go nie ma."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    return (4, end + 1) if end != -1 else None


def review_date(text: str) -> str | None:
    fm = frontmatter(text)
    m = REVIEW_RE.search(text[fm[0]:fm[1]]) if fm else None
    return m.group(1).strip("\"'") if m else None


def unverified(skill_dir: Path) -> int:
    files = [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]
    return sum(p.read_text(encoding="utf-8", errors="ignore").count(UNVERIFIED) for p in files if p.is_file())


def scan(root: Path, today: dt.date) -> list[dict]:
    rows = []
    for md in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        raw = review_date(md.read_text(encoding="utf-8"))
        row = {"skill": md.parent.name, "due": raw, "unverified": unverified(md.parent)}
        if raw is None:
            row["status"] = "missing"
        elif not DATE_RE.match(raw):
            row["status"] = "invalid"
        else:
            try:
                due = dt.date.fromisoformat(raw)
            except ValueError:
                row["status"] = "invalid"
            else:
                row["status"] = "overdue" if due < today else "soon" if (due - today).days <= SOON_DAYS else "ok"
        rows.append(row)
    return rows


def mark_reviewed(md: Path, reviewed: dt.date, months: int) -> str:
    """Ustawia `metadata.przeglad` = dzień przeglądu + interwał; zwraca nowy termin."""
    due = add_months(reviewed, months).isoformat()
    text = md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        raise ValueError(f"{md}: brak frontmattera")
    head, rest = text[:fm[1]], text[fm[1]:]
    line = f"  przeglad: {due}"
    if REVIEW_RE.search(head):
        head = REVIEW_RE.sub(line, head, count=1)
    elif re.search(r"^metadata:[ \t]*$", head, re.M):
        head = re.sub(r"^metadata:[ \t]*$", f"metadata:\n{line}", head, count=1, flags=re.M)
    else:
        head += f"metadata:\n{line}\n"
    md.write_text(head + rest, encoding="utf-8")
    return due


LABEL = {"overdue": "po terminie", "soon": f"termin ≤{SOON_DAYS} dni", "missing": "bez terminu",
         "invalid": "zły format terminu", "ok": "aktualny"}


def summary(rows: list[dict]) -> dict:
    out = {k: sum(r["status"] == k for r in rows) for k in LABEL}
    out["unverified"] = sum(r["unverified"] for r in rows)
    return out


def main(argv: list[str]) -> int:
    args, opts, reviewed, it = [], {}, [], iter(argv[1:])
    for a in it:
        if a in ("--root", "--today", "--date"):
            opts[a] = next(it, "")
        elif a == "--reviewed":
            opts[a] = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            opts[a] = True
        elif opts.get("--reviewed"):
            reviewed.append(a)
        else:
            args.append(a)
    root = Path(opts.get("--root") or ROOT).resolve()
    try:
        today = dt.date.fromisoformat(opts["--today"]) if opts.get("--today") else dt.date.today()
        day = dt.date.fromisoformat(opts["--date"]) if opts.get("--date") else today
    except ValueError as e:
        print(f"✗ Zła data: {e}")
        return 2
    policy = load_policy(root)

    if opts.get("--reviewed"):
        if not reviewed:
            print("✗ Podaj skille po --reviewed.")
            return 2
        missing = [n for n in reviewed if not (root / ".claude" / "skills" / n / "SKILL.md").is_file()]
        if missing:
            print(f"✗ Nieznane skille: {', '.join(missing)}")
            return 2
        for n in reviewed:
            due = mark_reviewed(root / ".claude" / "skills" / n / "SKILL.md", day, interval(n, policy))
            print(f"✓ {n}: przegląd {day.isoformat()}, następny termin {due} ({interval(n, policy)} mies.)")
        return 0

    rows = scan(root, today)
    s = summary(rows)
    if opts.get("--json"):
        print(json.dumps({"today": today.isoformat(), "summary": s, "skills": rows}, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            if r["status"] != "ok":
                extra = f", [niezweryfikowane]: {r['unverified']}" if r["unverified"] else ""
                print(f"  {'✗' if r['status'] in ('overdue', 'invalid') else '⚠'} {r['skill']:<36} "
                      f"{LABEL[r['status']]} ({r['due'] or '—'}{extra})")
        print(f"{'✓' if not s['overdue'] and not s['invalid'] else '⚠'} skilli: {len(rows)}, po terminie: "
              f"{s['overdue']}, termin ≤{SOON_DAYS} dni: {s['soon']}, bez terminu: {s['missing']}, "
              f"znaczników [niezweryfikowane]: {s['unverified']}")
        if s["overdue"]:
            print("  Po przeglądzie (fakty sprawdzone w źródłach z datą): python3 factory/freshness.py --reviewed <skill>")
    return 1 if opts.get("--strict") and (s["overdue"] or s["invalid"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
