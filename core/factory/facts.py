#!/usr/bin/env python3
"""
Szukanie już zweryfikowanych faktów, zanim zacznie się nowy research (tańsze niż ponowne sprawdzanie źródeł).

  python3 factory/facts.py ISO 19112          # wszystkie hasła naraz, bez wielkości liter, po rdzeniu słowa
  python3 factory/facts.py eidas podpis --json
  --root <katalog projektu> · --today RRRR-MM-DD (data odniesienia) · --max-age 180 (dni, po których ustalenie jest „stare”)

Przeszukuje:
- tabele weryfikacji w docs/project/archive/research/*.md (werdykty P / C / N / S → potwierdzone / częściowo /
  niepotwierdzone / sprzeczne; data z nazwy pliku RRRRMMDD-…),
- sekcje „## Źródła” w skillach (.claude/skills/*/SKILL.md i references/*.md; data z „odczyt RRRR-MM-DD” w linii).
Ustalenie stare albo niepotwierdzone sprawdź ponownie w źródłach (agent researcher); nowe tabele weryfikacji zapisuj
w docs/project/archive/research/, żeby kolejne wyszukanie je znalazło. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERDICT = {"P": "potwierdzone", "C": "częściowo", "N": "niepotwierdzone", "S": "sprzeczne"}
LINE_VERDICT = re.compile(r"^\s*[-*]\s*(P|C|N|S)\b")
DATE_IN_LINE = re.compile(r"odczyt[^0-9]{0,12}(\d{4}-\d{2}-\d{2})")


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
                inside = line.strip().startswith("## Źródła")
                continue
            if inside and line.strip() and matches(line, ks):
                d = DATE_IN_LINE.search(line)
                out.append({"file": f.relative_to(root).as_posix(), "line": i, "text": line.strip().lstrip("-* ").strip(),
                            "verdict": "źródło skilla", "date": d.group(1) if d else None})
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
    hits.sort(key=lambda h: (h["verdict"] == "źródło skilla", h["stale"], -(h["age_days"] is None), h["age_days"] or 0))
    if opts.get("--json"):
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return 0
    if not hits:
        print(f"Brak zweryfikowanych ustaleń dla: {' '.join(terms)} — sprawdź w źródłach (agent researcher, skill "
              "core-source-research) i zapisz tabelę w docs/project/archive/research/.")
        return 0
    for h in hits:
        when = f"{h['date']} · {h['age_days']} dni" if h["date"] else "bez daty"
        note = " — nie podawaj jako faktu" if h["verdict"] in ("niepotwierdzone", "sprzeczne") else ""
        note += " — stare: sprawdź ponownie" if h["stale"] and h["date"] else ""
        print(f"- [{h['verdict']} · {when}] {h['text'][:220]}{note}  ({h['file']}:{h['line']})")
    print(f"\n{len(hits)} ustaleń. Świeże i potwierdzone możesz użyć z datą; resztę sprawdź w źródłach.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
