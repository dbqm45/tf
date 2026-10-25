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

STORY_BLOCKS = """## Historyjki (format bloku)
### US-02: Uczący się powtarza fiszki
Jako uczący się chcę powtarzać fiszki, aby utrwalić materiał. Priorytet: must
- AC-1: Zakładając, że talia ma 3 fiszki do powtórki
  Gdy uczący się rozpocznie powtórkę
  Wtedy widzi pierwszą fiszkę
- AC-2: Zakładając, że talia nie ma fiszek do powtórki
  Gdy uczący się rozpocznie powtórkę
  Wtedy widzi komunikat „Na dziś koniec”

### US-03: Talie uczącego się
Jako uczący się chcę zarządzać taliami.
- AC-1: Gdy uczący się doda talię
  Oraz gdy zmieni jej nazwę
  Wtedy widzi talię z nową nazwą
- AC-2: Gdy uczący się usunie talię
  Wtedy talia znika z listy

### US-04: Uczący się oznacza fiszkę
Jako uczący się chcę oznaczyć trudną fiszkę.
Zakładając, że uczący się widzi fiszkę
Gdy oznaczy ją jako trudną
Wtedy fiszka wraca w tej samej sesji
"""

TALOS_STORY = """# Eksport i import fiszek

Jako uczący się chcę eksportować i importować talie w CSV.

## Kryteria akceptacji
- AC-1: Gdy uczący się wyeksportuje talię
  Wtedy pobiera plik CSV
- AC-2: Gdy uczący się zaimportuje plik CSV
  Wtedy widzi nową talię
"""

TALOS_STORY_OK = """# Uczący się eksportuje talię

Jako uczący się chcę wyeksportować talię do CSV, aby mieć kopię.

Kryteria akceptacji:
- AC-1: Zakładając, że talia ma 10 fiszek
  Gdy uczący się wyeksportuje talię
  Wtedy pobiera plik CSV z 10 wierszami
- AC-2: Zakładając, że talia jest pusta
  Gdy uczący się wyeksportuje talię
  Wtedy widzi komunikat „Talia jest pusta”
"""

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

    # G2.4: kształt historyjek (reguły kontraktu pdi 0.4.0) — nowe problemy to ostrzeżenia, --strict → kod 1
    out = run({"r.md": GOOD}, "r.md", "--json", "--strict")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and [s.get("id") for s in r.get("stories", [])] == ["US-01"]
          and not r["stories"][0].get("findings") and r["stories"][0].get("scenarios") == 1,
          f"KS-1: historyjka z tabeli (Given/When/Then w jednej linii) bez uwag, --strict → kod 0: {out.returncode} {out.stdout[-400:]}")

    mixed = GOOD.replace("## Reguła biznesowa", STORY_BLOCKS + "\n## Reguła biznesowa")
    out = run({"r.md": mixed}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    by_id = {s["id"]: {f["rule"] for f in s.get("findings", [])} for s in r.get("stories", [])}
    check(out.returncode == 0 and by_id.get("US-02") == set() and "STORY-001" in by_id.get("US-03", set())
          and "AC-004" in by_id.get("US-03", set()),
          f"KS-2: blok US-NN z AC-n — czysty bez uwag; dwie akcje → STORY-001 i AC-004 jako ostrzeżenie, kod 0: {out.returncode} {by_id}")
    s3 = next((s for s in r.get("stories", []) if s["id"] == "US-03"), {})
    check(s3.get("line", 0) > 0 and len(s3.get("actions", [])) == 2,
          f"KS-3: historyjka ma numer linii i listę różnych akcji głównych (podstawa podziału): {s3}")
    check("AC-ID" in by_id.get("US-04", set()) and "AC-ID" not in by_id.get("US-02", set()),
          f"KS-4: blok bez identyfikatorów AC-n → ostrzeżenie AC-ID: {by_id}")
    out = run({"r.md": mixed}, "r.md", "--strict")
    check(out.returncode == 1 and "US-03" in out.stdout and "STORY-001" in out.stdout,
          f"KS-5: --strict zamienia ostrzeżenia w kod 1, wyjście z identyfikatorem historyjki i reguły: {out.returncode} {out.stdout[-400:]}")

    tbl = GOOD.replace("- FR-002: Uczący się może zaakceptować", "- FR-002: Uczący się może zapisać fiszkę w tabeli cards i zaakceptować")
    out = run({"r.md": tbl}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    warn = [w for w in r.get("warnings", []) if w.get("rule") == "AC-003"]
    check(out.returncode == 0 and not r.get("leaks") and warn and warn[0].get("category") == "struktura danych",
          f"KS-6: tabela w wymaganiu (nowe w kontrakcie) → ostrzeżenie AC-003, nie blokuje: {out.returncode} {out.stdout[-400:]}")
    out = run({"r.md": LEAKY}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(all(l.get("rule") == "AC-003" for l in r.get("leaks", [])) and r.get("leaks"),
          "KS-7: dotychczasowe wycieki techniki oznaczone regułą AC-003")

    pl = GOOD.replace("Given wklejony tekst When proszę o fiszki Then widzę 5–15 propozycji",
                      "Mając wklejony tekst Kiedy proszę o fiszki Wtedy widzę 5–15 propozycji")
    out = run({"r.md": pl}, "r.md", "--json")
    r = json.loads(out.stdout or "{}")
    check(r.get("readiness", {}).get("score") == 4, f"KS-8: polskie warianty (Mając/Kiedy/Wtedy) liczą się do gotowości: {out.stdout[-300:]}")

    out = run({"story.md": TALOS_STORY}, "--story", "story.md", "--strict")
    check(out.returncode == 1 and "STORY-001" in out.stdout and "eksport" in out.stdout.lower(),
          f"KS-9: --story (story.md Talosa) z dwiema akcjami → STORY-001 z listą akcji, --strict kod 1: {out.returncode} {out.stdout[-400:]}")
    out = run({"story.md": TALOS_STORY_OK}, "--story", "story.md", "--strict", "--json")
    r = json.loads(out.stdout or "{}")
    check(out.returncode == 0 and r.get("story", {}).get("scenarios") == 2 and not r["story"].get("findings"),
          f"KS-10: --story z jedną akcją i dwoma scenariuszami → kod 0: {out.returncode} {out.stdout[-400:]}")

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
