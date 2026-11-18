#!/usr/bin/env python3
"""
Reviewer of numbers in markdown documents — no model and no network. Complements grounding_check.py (references).

  python3 .claude/skills/core-grounding/scripts/claims_check.py docs/project/07-review/report.md
  python3 .claude/skills/core-grounding/scripts/claims_check.py docs/evals/ [--strict]

Checks:
- error: the arithmetic of the notation „X/Y (Z%)” — the percentage must match the fraction within rounding accuracy,
- error: YYYY-MM-DD dates that do not exist (2026-02-30), and as-of dates from the future („stan na”, „dostęp”, „pobrano”,
  „zmierzono”, „uruchomiono” — "as of", "accessed", "downloaded", "measured", "run"),
- warning: a number with a unit (%, pp, USD, zł, EUR, ms, s, min, h, GB, MB, razy) in a text line without a trace of
  origin in the same line — a `command` or a `path`, a link, a URL, file:line, „źródło” (source), „wg”/„według” (per),
  [assumption], [unverified] (also the old [założenie], [niezweryfikowane]), a footnote [^n]; a document with a data source declaration („Pliki:”, „Dane:”,
  „Źródło danych:” or „surowe wyniki w” right before a `path`, also mid-sentence) has it for all numbers.
Skips code blocks, headings and — for warnings — table rows (a table's source usually stands above it).
First line of the result: „Werdykt: OK | WARNINGS | ERRORS” (verdict). Exit code: 1 on errors (with --strict also on
warnings), otherwise 0.
"""
from __future__ import annotations

import datetime as dt
import re
import signal
import sys
from pathlib import Path

FRACTION = re.compile(r"(?<![\d.,])(\d+)\s*/\s*(\d+)\s*\(\s*(\d+(?:[.,]\d+)?)\s*%\s*\)")
DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
STATE_WORDS = re.compile(r"stan na|dostęp|pobran\w*|zmierzon\w*|uruchomion\w*|sprawdzon\w*"
                         r"|as of|accessed|fetched|measured|checked", re.I)
CLAIM = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?\s*(%|pp\b|p\.p\.|USD\b|zł\b|PLN\b|EUR\b|ms\b|s\b|min\b|h\b|GB\b|MB\b"
                   r"|razy\b|times\b|×)", re.I)
DOC_SOURCE = re.compile(r"(?<![\w])(pliki|dane|źródło danych|surowe wyniki(?: w)?|files|data|data source|raw results(?: in)?)\s*\**\s*:?\s*\**\s*`[^`]+`", re.I)
SOURCE = re.compile(r"`[^`]+`|https?://|\]\([^)]+\)|\b[\w./-]+\.\w+:\d+|źródł\w*|\bwg\b|według|\bsources?\b|according to"
                    r"|\[(?:założenie|niezweryfikowane|assumption|unverified)\]|\[\^[^\]]+\]", re.I)


def check_text(text: str, label: str, today: dt.date) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    in_code = False
    declared = bool(DOC_SOURCE.search(text))
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.lstrip().startswith("#"):
            continue
        where = f"{label}:{n}"
        for m in FRACTION.finditer(line):
            a, b, z = int(m.group(1)), int(m.group(2)), m.group(3).replace(",", ".")
            if b == 0:
                errors.append(f"{where}: {m.group(0)} — division by zero")
                continue
            decimals = len(z.split(".")[1]) if "." in z else 0
            want = 100 * a / b
            if abs(float(z) - want) > 0.5 * 10 ** -decimals + 1e-9:
                errors.append(f"{where}: {m.group(0)} — {a}/{b} is {want:.{decimals}f}%, not {z}%")
        for m in DATE.finditer(line):
            try:
                day = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                errors.append(f"{where}: {m.group(0)} — this date does not exist")
                continue
            if day > today and STATE_WORDS.search(line):
                errors.append(f"{where}: {m.group(0)} — state date is in the future (today is {today.isoformat()})")
        if line.lstrip().startswith("|"):
            continue
        claims = [c.group(0) for c in CLAIM.finditer(line)]
        if claims and not declared and not SOURCE.search(line):
            warnings.append(f"{where}: {', '.join(claims)} — number with no trace of origin in this line "
                            f"(command, path, link, source or [assumption])")
    return errors, warnings


def files(arg: str) -> list[Path]:
    p = Path(arg)
    if p.is_dir():
        return sorted(x for x in p.rglob("*.md") if x.is_file())
    return [p]


def main(argv: list[str]) -> int:
    if hasattr(signal, "SIGPIPE"):   # output through `| head` without an exception
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    args = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if not args:
        print(__doc__)
        return 2
    today = dt.date.today()
    errors, warnings = [], []
    for arg in args:
        for f in files(arg):
            if not f.is_file():
                errors.append(f"{f}: file not found")
                continue
            e, w = check_text(f.read_text(encoding="utf-8", errors="replace"), f.as_posix(), today)
            errors += e
            warnings += w
    verdict = "ERRORS" if errors else ("WARNINGS" if warnings else "OK")
    print(f"Verdict: {verdict} (errors: {len(errors)}, warnings: {len(warnings)})")
    for e in errors:
        print(f"✗ {e}")
    for w in warnings:
        print(f"⚠ warning: {w}")
    return 1 if errors or (strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
