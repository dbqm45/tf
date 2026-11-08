#!/usr/bin/env python3
"""
Recenzent liczb w dokumentach markdown — bez modelu i bez sieci. Uzupełnia grounding_check.py (odwołania).

  python3 .claude/skills/core-grounding/scripts/claims_check.py docs/project/07-review/raport.md
  python3 .claude/skills/core-grounding/scripts/claims_check.py docs/evals/ [--strict]

Sprawdza:
- błąd: arytmetykę zapisu „X/Y (Z%)” — procent musi zgadzać się z ułamkiem z dokładnością zaokrąglenia,
- błąd: daty RRRR-MM-DD, które nie istnieją (2026-02-30), i daty stanu z przyszłości („stan na”, „dostęp”, „pobrano”,
  „zmierzono”, „uruchomiono”),
- ostrzeżenie: liczbę z jednostką (%, pp, USD, zł, EUR, ms, s, min, h, GB, MB, razy) w linii tekstu bez śladu
  pochodzenia w tej samej linii — `polecenie` albo `ścieżka`, link, adres URL, plik:linia, „źródło”, „wg”/„według”,
  [założenie], [niezweryfikowane], przypis [^n]; dokument z deklaracją źródła danych („Pliki:”, „Dane:”,
  „Źródło danych:” albo „surowe wyniki w” zaraz przed `ścieżką`, także w środku zdania) ma ją dla wszystkich liczb.
Pomija bloki kodu, nagłówki i — dla ostrzeżeń — wiersze tabel (źródło tabeli stoi zwykle nad nią).
Pierwsza linia wyniku: „Werdykt: OK | OSTRZEŻENIA | BŁĘDY”. Kod wyjścia: 1 przy błędach (z --strict także przy
ostrzeżeniach), inaczej 0.
"""
from __future__ import annotations

import datetime as dt
import re
import signal
import sys
from pathlib import Path

FRACTION = re.compile(r"(?<![\d.,])(\d+)\s*/\s*(\d+)\s*\(\s*(\d+(?:[.,]\d+)?)\s*%\s*\)")
DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
STATE_WORDS = re.compile(r"stan na|dostęp|pobran\w*|zmierzon\w*|uruchomion\w*|sprawdzon\w*", re.I)
CLAIM = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?\s*(%|pp\b|p\.p\.|USD\b|zł\b|PLN\b|EUR\b|ms\b|s\b|min\b|h\b|GB\b|MB\b"
                   r"|razy\b|×)", re.I)
DOC_SOURCE = re.compile(r"(?<![\w])(pliki|dane|źródło danych|surowe wyniki(?: w)?)\s*\**\s*:?\s*\**\s*`[^`]+`", re.I)
SOURCE = re.compile(r"`[^`]+`|https?://|\]\([^)]+\)|\b[\w./-]+\.\w+:\d+|źródł\w*|\bwg\b|według|\[założenie\]"
                    r"|\[niezweryfikowane\]|\[\^[^\]]+\]", re.I)


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
                errors.append(f"{where}: {m.group(0)} — dzielenie przez zero")
                continue
            decimals = len(z.split(".")[1]) if "." in z else 0
            want = 100 * a / b
            if abs(float(z) - want) > 0.5 * 10 ** -decimals + 1e-9:
                errors.append(f"{where}: {m.group(0)} — {a}/{b} to {want:.{decimals}f}%, nie {z}%")
        for m in DATE.finditer(line):
            try:
                day = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                errors.append(f"{where}: {m.group(0)} — taka data nie istnieje")
                continue
            if day > today and STATE_WORDS.search(line):
                errors.append(f"{where}: {m.group(0)} — data stanu z przyszłości (dziś {today.isoformat()})")
        if line.lstrip().startswith("|"):
            continue
        claims = [c.group(0) for c in CLAIM.finditer(line)]
        if claims and not declared and not SOURCE.search(line):
            warnings.append(f"{where}: {', '.join(claims)} — liczba bez śladu pochodzenia w tej linii "
                            f"(polecenie, ścieżka, link, źródło albo [założenie])")
    return errors, warnings


def files(arg: str) -> list[Path]:
    p = Path(arg)
    if p.is_dir():
        return sorted(x for x in p.rglob("*.md") if x.is_file())
    return [p]


def main(argv: list[str]) -> int:
    if hasattr(signal, "SIGPIPE"):   # wynik przez `| head` bez wyjątku
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
                errors.append(f"{f}: brak pliku")
                continue
            e, w = check_text(f.read_text(encoding="utf-8", errors="replace"), f.as_posix(), today)
            errors += e
            warnings += w
    verdict = "BŁĘDY" if errors else ("OSTRZEŻENIA" if warnings else "OK")
    print(f"Werdykt: {verdict} (błędy: {len(errors)}, ostrzeżenia: {len(warnings)})")
    for e in errors:
        print(f"✗ {e}")
    for w in warnings:
        print(f"⚠ ostrzeżenie: {w}")
    return 1 if errors or (strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
