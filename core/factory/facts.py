#!/usr/bin/env python3
"""
Searching for already verified facts before starting new research (cheaper than re-checking sources).

  python3 .tf/factory/facts.py ISO 19112          # all terms at once, case-insensitive, by word stem
  python3 .tf/factory/facts.py eidas podpis --json
  --root <project directory> · --today YYYY-MM-DD (reference date) · --max-age 180 (days after which a finding is "old")

Searches:
- verification tables in docs/project/archive/research/*.md (verdicts `confirmed` / `partial` / `unconfirmed` / `contradicted` at the start of
  a row; the former letters P / C / N / S too; the date from the file name YYYYMMDD-…),
- "## Sources" sections in skills (.claude/skills/*/SKILL.md and references/*.md; the date from "accessed YYYY-MM-DD" in the line).
Re-check an old or unconfirmed finding in the sources (the researcher agent); save new verification tables
in docs/project/archive/research/ so the next search finds them. Standard library only.
"""
from __future__ import annotations

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
VERDICT = {"confirmed": "confirmed", "partial": "partial", "unconfirmed": "unconfirmed", "contradicted": "contradicted",
           "P": "confirmed", "C": "partial", "N": "unconfirmed", "S": "contradicted"}   # letters P/C/N/S — tables from before 14.x
LINE_VERDICT = re.compile(r"^\s*[-*]\s*(confirmed|partial|unconfirmed|contradicted|P|C|N|S)\b")
DATE_IN_LINE = re.compile(r"accessed[^0-9]{0,12}(\d{4}-\d{2}-\d{2})")


def keys(terms: list[str]) -> list[str]:
    return [t.lower()[:5] if len(t) > 5 else t.lower() for t in terms if t.strip()]


def matches(line: str, ks: list[str]) -> bool:
    low = line.lower()
    return all(k in low for k in ks)


def research(root: Path, ks: list[str]) -> list[dict]:
    out = []
    for f in sorted((root / "docs" / "project" / "archive" / "research").glob("*.md")):
        m = re.match(r"(\d{4})(\d{2})(\d{2})", f.name)
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.strip().startswith("#") or not matches(line, ks):
                continue
            v = LINE_VERDICT.match(line)
            out.append({"file": f.relative_to(root).as_posix(), "line": i, "text": line.strip().lstrip("-* ").strip(),
                        "verdict": VERDICT[v.group(1)] if v else "—", "date": date})
    return out


def skill_sources(root: Path, ks: list[str]) -> list[dict]:
    out = []
    files = [*(root / ".claude" / "skills").glob("*/SKILL.md"), *(root / ".claude" / "skills").glob("*/references/*.md")]
    for f in sorted(files):
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        inside = False
        for i, line in enumerate(lines, 1):
            if line.startswith("## "):
                inside = line.strip().startswith("## Sources")
                continue
            if inside and line.strip() and matches(line, ks):
                d = DATE_IN_LINE.search(line)
                out.append({"file": f.relative_to(root).as_posix(), "line": i, "text": line.strip().lstrip("-* ").strip(),
                            "verdict": "skill-source", "date": d.group(1) if d else None})
    return out


def main(argv: list[str]) -> int:
    opts, terms, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--root", "--today", "--max-age"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            opts[a] = True
        else:
            terms.append(a)
    if not terms:
        print(__doc__)
        return 2
    root = Path(opts.get("--root") or ROOT).resolve()
    today = dt.date.fromisoformat(opts["--today"]) if opts.get("--today") else dt.date.today()
    max_age = int(opts.get("--max-age") or 180)
    ks = keys(terms)
    hits = research(root, ks) + skill_sources(root, ks)
    for h in hits:
        age = (today - dt.date.fromisoformat(h["date"])).days if h["date"] else None
        h["age_days"], h["stale"] = age, (age is None or age > max_age)
    hits.sort(key=lambda h: (h["verdict"] == "skill-source", h["stale"], -(h["age_days"] is None), h["age_days"] or 0))
    if opts.get("--json"):
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return 0
    if not hits:
        print(f"No verified findings for: {' '.join(terms)} — check the sources (agent researcher, skill "
              "core-source-research) and save the table in docs/project/archive/research/.")
        return 0
    for h in hits:
        when = f"{h['date']} · {h['age_days']} days" if h["date"] else "no date"
        note = " — do not state it as a fact" if h["verdict"] in ("unconfirmed", "contradicted") else ""
        note += " — old: check it again" if h["stale"] and h["date"] else ""
        print(f"- [{h['verdict']} · {when}] {h['text'][:220]}{note}  ({h['file']}:{h['line']})")
    print(f"\n{len(hits)} findings. You can use fresh and confirmed ones with their date; check the rest in the sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
