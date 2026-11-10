#!/usr/bin/env python3
"""
Mapa pokrycia katalogu skilli (B2) — narzędzie autora fabryki, nie instalowane w projektach.

  python3 tools/coverage_map.py --summary                  # jedna linia + dziury, do CI (informacja)
  python3 tools/coverage_map.py --out docs/coverage-map.md # pełny raport Markdown (nie jest commitowany)
  python3 tools/coverage_map.py --areas plik.json --root katalog

Dla każdego hasła z `tools/coverage_areas.json` (obszar → lista haseł) liczy skille rdzenia, nakładek i trybów,
w których metadanych (`description`, `metadata.katalog`, `metadata.slowa`) hasło występuje — bez względu na
wielkość liter; hasło to zwykle rdzeń wyrazu („faktur” trafia w „faktury”, „fakturach”). Liczą się metadane, bo po
nich podpowiedź i model wybierają skill; wiedza ukryta w treści, do której nic nie prowadzi, jest dla trasowania
niewidoczna. Hasło bez skilla to **dziura**, z jednym skillem — **cienkie** miejsce.

Mapa wskazuje kandydatów, nie decyduje: nowy skill powstaje dopiero, gdy scenariusz ewaluacji potwierdzi, że brak
szkodzi (core-skill-authoring). Kod wyjścia zawsze 0, gdy wejście jest poprawne (informacja, nie bramka); 2 — błąd
wejścia. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)
FIELD = re.compile(r"^\s*(description|katalog|slowa):\s*(.*)$", re.M)


def load_skills(root: Path) -> dict[str, str]:
    """Nazwa skilla → tekst metadanych (opis, katalog, słowa) małymi literami."""
    out: dict[str, str] = {}
    files = list((root / "core" / "skills").glob("*/SKILL.md"))
    for base in ("packs", "modes"):
        files += list((root / base).glob("*/skills/*/SKILL.md"))
    for f in sorted(files):
        m = FRONT.match(f.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        text = " ".join(v.strip().strip('"') for _, v in FIELD.findall(m.group(1)))
        out[f.parent.name] = re.sub(r"\s+", " ", text.lower())
    return out


def coverage(skills: dict[str, str], areas: dict[str, list[str]]) -> list[tuple[str, str, list[str]]]:
    rows = []
    for area, terms in areas.items():
        for term in terms:
            t = term.lower()
            rows.append((area, term, sorted(n for n, txt in skills.items() if t in txt)))
    return rows


def report(rows, n_skills: int) -> str:
    holes = [(a, t) for a, t, s in rows if not s]
    thin = [(a, t, s[0]) for a, t, s in rows if len(s) == 1]
    out = [f"# Mapa pokrycia katalogu", "",
           f"Skilli: {n_skills} · haseł: {len(rows)} · dziury: {len(holes)} · cienkie: {len(thin)}.", "",
           "Liczą się metadane skilli (opis, katalog, słowa) — to, po czym trasowanie wybiera skill. Dziura to "
           "kandydat na skill albo na dopisanie słów do istniejącego; decyzja po scenariuszu ewaluacji.", "",
           "| Obszar | Hasło | Skilli | Skille (do 4) |", "|---|---|---|---|"]
    for area, term, s in rows:
        more = f" … +{len(s) - 4}" if len(s) > 4 else ""
        out.append(f"| {area} | `{term}` | {len(s)} | {', '.join(s[:4])}{more} |")
    out += ["", "## Dziury", ""] + ([f"- {a}: `{t}`" for a, t in holes] or ["- brak"])
    out += ["", "## Cienkie (jeden skill)", ""] + ([f"- {a}: `{t}` — {s}" for a, t, s in thin] or ["- brak"])
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Mapa pokrycia katalogu skilli (informacja, kod 0).")
    ap.add_argument("--root", default=str(ROOT), help="katalog repozytorium fabryki")
    ap.add_argument("--areas", default=str(ROOT / "tools" / "coverage_areas.json"), help="plik obszarów (JSON)")
    ap.add_argument("--out", help="zapisz pełny raport Markdown")
    ap.add_argument("--summary", action="store_true", help="krótkie podsumowanie na stdout (CI)")
    a = ap.parse_args()
    try:
        areas = json.loads(Path(a.areas).read_text(encoding="utf-8"))
        assert isinstance(areas, dict) and all(isinstance(v, list) for v in areas.values())
    except (OSError, ValueError, AssertionError) as e:
        print(f"✗ plik obszarów {a.areas}: {e}", file=sys.stderr)
        return 2
    skills = load_skills(Path(a.root))
    rows = coverage(skills, areas)
    text = report(rows, len(skills))
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    if a.summary or not a.out:
        holes = [f"{ar}: {t}" for ar, t, s in rows if not s]
        thin = sum(1 for *_, s in rows if len(s) == 1)
        print(f"Mapa pokrycia — skilli: {len(skills)}, haseł: {len(rows)}, dziury: {len(holes)}, cienkie: {thin}"
              + (" (pełny raport: python3 tools/coverage_map.py --out docs/coverage-map.md)" if not a.out else ""))
        for h in holes:
            print(f"  ⚠ dziura — {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
