#!/usr/bin/env python3
"""Testy kontroli wymagań (proc-requirements-shaping/scripts/requirements_lint.py): python3 tests/test_requirements_lint.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "proc-requirements-shaping" / "scripts" / "requirements_lint.py"

GOOD = """---
artifact: requirements
---
# Wymagania: fiszki

## TL;DR
Trzy wymagania konieczne.

## Wymagania funkcjonalne
- FR-001: Uczący się może wkleić tekst i dostać propozycje fiszek. Priorytet: must
- FR-002: Uczący się może zaakceptować albo odrzucić każdą propozycję. Priorytet: must

## Historyjki (MVP)
| ID | Historia | Kryteria | Priorytet |
|---|---|---|---|
| US-01 | Jako uczący się… | Given wklejony tekst When proszę o fiszki Then widzę 5–15 propozycji | must |

## Reguła biznesowa
Propozycja fiszki trafia do talii dopiero po akceptacji uczącego się, a zaakceptowane wchodzą do harmonogramu powtórek.

## Atrybuty jakości
| Atrybut | Scenariusz | Priorytet |
|---|---|---|
| wydajność | uczący się widzi propozycje w ciągu 10 s dla tekstu do 10 tys. znaków | H |

## Obecny system
Dziś działa moduł logowania na Supabase z tabelą users (FK do profiles).

## Poza zakresem MVP
- import PDF
- współdzielenie talii

## Otwarte pytania
- [ ] Czy limit tekstu wystarczy? → właściciel produktu
"""

LEAKY = GOOD.replace(
    "| wydajność | uczący się widzi propozycje w ciągu 10 s dla tekstu do 10 tys. znaków | H |",
    "| wydajność | podczas generowania pokazujemy spinner | H |\n| bezpieczeństwo | limit 100 żądań per IP po stronie serwera w Redisie | H |",
).replace("- FR-002: Uczący się", "- FR-002: Przez WebSocket uczący się")

BRIEF = """# Brief
## Ograniczenia
- Budżet czasu MVP: {budget}
- Szacunek przepływu MVP: {estimate}
{ack}
"""


def run(files: dict, *args: str):
    with tempfile.TemporaryDirectory() as d:
        paths = {}
        for name, text in files.items():
            p = Path(d) / name
            p.write_text(text, encoding="utf-8")
            paths[name] = str(p)
        argv = [paths.get(a, a) for a in args]
        out = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, timeout=30)
        return out


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    out = run({"r.md": GOOD}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and r.get("readiness", {}).get("score") == 4 and not r.get("leaks"),
          f"poprawne wymagania → gotowość 4/4, brak wycieków (sekcja „Obecny system” pominięta), kod 0: {out.returncode} {out.stdout[-300:]}")

    out = run({"r.md": LEAKY}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    cats = {l["category"] for l in r.get("leaks", [])}
    check(out.returncode == 1 and {"interfejs", "mechanizm", "miejsce wykonania", "dostawca", "protokół"} <= cats,
          f"wyciek techniki → kategorie interfejs, mechanizm, miejsce wykonania, dostawca, protokół i kod 1: {out.returncode} {cats}")
    lines = {l["line"] for l in r.get("leaks", [])}
    check(all(isinstance(n, int) and n > 0 for n in lines), f"każdy wyciek ma numer linii: {lines}")

    out = run({"r.md": LEAKY}, "r.md")
    check(out.returncode == 1 and "r.md:" in out.stdout and "dostawca" in out.stdout,
          f"wyjście tekstowe: plik:linia — kategoria: {out.stdout[-300:]}")

    thin = "# Wymagania\n## TL;DR\nNic.\n## Reguła biznesowa\nTODO\n"
    out = run({"r.md": thin}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    rd = r.get("readiness", {})
    check(out.returncode == 0 and rd.get("score") == 0 and rd.get("warning") and len(rd.get("missing", [])) == 4,
          f"puste wymagania → gotowość 0/4 z ostrzeżeniem i listą 4 braków, ale kod 0 (to ostrzeżenie): {out.stdout[-300:]}")

    long_rule = GOOD.replace("Propozycja fiszki trafia", "Propozycja fiszki, " + "bardzo " * 40 + "trafia")
    out = run({"r.md": long_rule}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(r.get("readiness", {}).get("score") == 3, f"reguła dłuższa niż jedno zdanie (>200 znaków) nie liczy się: {out.stdout[-200:]}")

    out = run({"r.md": GOOD, "b.md": BRIEF.format(budget="3 tygodnie", estimate="5 tygodni", ack="")},
              "r.md", "--brief", "b.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 1 and r.get("mvp", {}).get("too_big") is True,
          f"szacunek ponad budżet z briefu bez potwierdzenia kosztu → MVP za duże, kod 1: {out.stdout[-300:]}")

    out = run({"r.md": GOOD, "b.md": BRIEF.format(budget="3 tygodnie", estimate="5 tygodni",
                                                   ack="- Koszt potwierdzony: 2026-10-10, właściciel produktu przyjmuje 5 tygodni")},
              "r.md", "--brief", "b.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and r.get("mvp", {}).get("too_big") is True and r["mvp"].get("acknowledged") is True,
          f"MVP ponad budżet z zapisanym potwierdzeniem kosztu → kod 0: {out.stdout[-300:]}")

    out = run({"r.md": GOOD, "b.md": BRIEF.format(budget="4 tygodnie", estimate="10 dni", ack="")},
              "r.md", "--brief", "b.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and r.get("mvp", {}).get("too_big") is False,
          f"10 dni w budżecie 4 tygodni → mieści się (jednostki przeliczone): {out.stdout[-300:]}")

    out = run({"r.md": GOOD, "b.md": "# Brief\n## Ograniczenia\n- Zespół: 1 osoba\n"}, "r.md", "--brief", "b.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and r.get("mvp", {}).get("budget_days") is None and r["mvp"].get("warning"),
          f"brief bez budżetu czasu → ostrzeżenie „ustal budżet”, nie błąd: {out.stdout[-300:]}")

    out = run({}, "nie-ma.md")
    check(out.returncode == 2, f"brak pliku → kod 2: {out.returncode}")

    out = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=30)
    check(out.returncode == 0 and "--brief" in out.stdout, "--help opisuje opcje")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów kontroli wymagań")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
