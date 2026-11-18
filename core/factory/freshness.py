#!/usr/bin/env python3
"""
Skill freshness: review deadlines (`metadata.review`) and [unverified] markers (standard library only).

  python3 .tf/factory/freshness.py                         # skills past due, due within ≤30 days, without a deadline
  python3 .tf/factory/freshness.py --json                  # the same as JSON (e.g. for a periodic review)
  python3 .tf/factory/freshness.py --strict                # exit code 1 when any skill is past due
  python3 .tf/factory/freshness.py --reviewed <skill…>     # after a review: new deadline = today + the skill's interval
  python3 .tf/factory/freshness.py --reviewed <skill> --date 2026-10-03   # review from the given day
  --today YYYY-MM-DD (reference date), --root <project directory>

The review deadline is the date until which the skill's content (versions, recipes, standards, methods) is considered current. After
the deadline the skill still works; the agent then checks volatile facts at the time of use (core-source-research), and a review
in the factory repository refreshes the content and sets a new deadline. Interval in months: a skill exception, then
the longest matching prefix, then the default. Packs add their own intervals (`freshness` in pack.yaml), and the project
may override them in `.tf/config/config.yaml` → `freshness` (the same keys as DEFAULT_POLICY). The `review` line does not enter
the quality gate fingerprint.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
import re
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOON_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REVIEW_RE = re.compile(r"^  review:[ \t]*(.*?)[ \t]*$", re.M)
UNVERIFIED = ("[unverified", "[niezweryfikowane")   # pl: sprzed 14.x

DEFAULT_POLICY = {
    "default_months": 12,
    # framework and tool versions change fastest, languages — every half year; pack dimensions: pack.yaml
    "prefixes": {"fw-": 3, "tool-": 3, "lang-": 6},
    "skills": {},
}


def load_policy(root: Path = ROOT) -> dict:
    pol = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_POLICY.items()}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_packs_fresh", root / ".tf" / "factory" / "packs.py")
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        packs = pm.compose(root, pm.load_config(root))["freshness"]   # intervals from packs
        own_p = root / ".tf" / "config" / "config.yaml"
        own = (pm.load_yaml(own_p).get("freshness") or {}) if own_p.is_file() else {}   # project overrides
    except Exception:  # no factory in the directory or a corrupted configuration — default values
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
    """Range (start, end) of the frontmatter without the `---` markers; None when there is none."""
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
    return sum(p.read_text(encoding="utf-8", errors="ignore").count(m) for p in files if p.is_file() for m in UNVERIFIED)


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
    """Sets `metadata.review` = review day + interval; returns the new deadline."""
    due = add_months(reviewed, months).isoformat()
    text = md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        raise ValueError(f"{md}: no frontmatter")
    head, rest = text[:fm[1]], text[fm[1]:]
    line = f'  review: "{due}"'   # text, not a YAML date: the Agent Skills specification — metadata is string → string
    if REVIEW_RE.search(head):
        head = REVIEW_RE.sub(line, head, count=1)
    elif re.search(r"^metadata:[ \t]*$", head, re.M):
        head = re.sub(r"^metadata:[ \t]*$", f"metadata:\n{line}", head, count=1, flags=re.M)
    else:
        head += f"metadata:\n{line}\n"
    md.write_text(head + rest, encoding="utf-8")
    return due


LABEL = {"overdue": "overdue", "soon": f"due in ≤{SOON_DAYS} days", "missing": "no review date",
         "invalid": "invalid review date format", "ok": "current"}


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
        print(f"✗ Invalid date: {e}")
        return 2
    policy = load_policy(root)

    if opts.get("--reviewed"):
        if not reviewed:
            print("✗ Give the skills after --reviewed.")
            return 2
        missing = [n for n in reviewed if not (root / ".claude" / "skills" / n / "SKILL.md").is_file()]
        if missing:
            print(f"✗ Unknown skills: {', '.join(missing)}")
            return 2
        for n in reviewed:
            due = mark_reviewed(root / ".claude" / "skills" / n / "SKILL.md", day, interval(n, policy))
            print(f"✓ {n}: reviewed {day.isoformat()}, next review date {due} ({interval(n, policy)} months)")
        return 0

    rows = scan(root, today)
    s = summary(rows)
    if opts.get("--json"):
        print(json.dumps({"today": today.isoformat(), "summary": s, "skills": rows}, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            if r["status"] != "ok":
                extra = f", [unverified]: {r['unverified']}" if r["unverified"] else ""
                print(f"  {'✗' if r['status'] in ('overdue', 'invalid') else '⚠'} {r['skill']:<36} "
                      f"{LABEL[r['status']]} ({r['due'] or '—'}{extra})")
        print(f"{'✓' if not s['overdue'] and not s['invalid'] else '⚠'} skills: {len(rows)}, overdue: "
              f"{s['overdue']}, due in ≤{SOON_DAYS} days: {s['soon']}, no review date: {s['missing']}, "
              f"[unverified] markers: {s['unverified']}")
        if s["overdue"]:
            print("  After a review (facts checked in dated sources): python3 .tf/factory/freshness.py --reviewed <skill>")
    return 1 if opts.get("--strict") and (s["overdue"] or s["invalid"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
