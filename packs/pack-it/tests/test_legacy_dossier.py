#!/usr/bin/env python3
"""Tests of the dossier_check.py script (skill eng-legacy-dossier): completeness of the system dossier and the business rule evidence."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / ".claude" / "skills" / "eng-legacy-dossier" / "scripts" / "dossier_check.py").is_file())
SCRIPT = ROOT / ".claude" / "skills" / "eng-legacy-dossier" / "scripts" / "dossier_check.py"

INDEX = """<!-- legacy-dossier -->
# Teczka systemu: fakturowanie
System: fakturowanie · Commit: abc1234 · Data: 2026-10-17

## TL;DR
Wystawia faktury i korekty.

## Moduły
| Moduł | Po co | Stan |
|---|---|---|
| [faktury](modules/faktury.md) | wystawianie faktur | żółty |

## Przepływy
Wystawienie faktury: kontroler → serwis → repozytorium.

## Słownik
| W kodzie | W biznesie |
|---|---|
| `Doc` | faktura |

## Stan i kandydaci do refaktoru
- faktury: duplikacja zaokrągleń → eng-tech-debt-audit

## Pytania otwarte
- Kto zatwierdza korekty?

## Ograniczenia
Bez modułu raportów.
"""

MODULE = """<!-- legacy-dossier:module -->
# Moduł: faktury
Stan: żółty — zaokrąglenia w dwóch miejscach

## Po co
Wystawia faktury.

## Odpowiedzialności
- numeracja, sumy

## Wejścia i wyjścia
- POST /invoices

## Reguły biznesowe
| ID | Reguła | Dowód | Pewność |
|---|---|---|---|
| R-FAK-01 | Kwoty zaokrągla się do 2 miejsc w górę | src/Invoice.java:3 | kod |
| R-FAK-02 | Faktura po 30 dniach jest przeterminowana | — | do weryfikacji |

## Dane
- tabela invoices

## Zależności
- klienci

## Pułapki
- zaokrąglenie także w PdfExporter

## Testy
- brak testów numeracji

## Pytania
- Czy 30 dni to dni robocze?
"""


ASSESS = """<!-- legacy-dossier:assessment -->
# Architecture Assessment — fakturowanie

## Podsumowanie
Granice bibliotek są słabe; routing i testy w porządku.

## Zakres i metoda
Aplikacja shop-app i jej biblioteki; nx graph, przegląd kodu.

## Kryteria oceny
Clarity, Coupling, Testability, Enforceability.

## Ustalenia
### ARCH-001 — Biblioteka współdzielona importuje kod aplikacji
Obszar: granice bibliotek
Kategoria: potwierdzony problem
Stan obecny: shared-ui importuje serwis z shop-app
Stan oczekiwany: zależności tylko w dół
Luka: zmiana w aplikacji psuje bibliotekę
Dowód: src/Invoice.java:3
Wpływ: sprzężenie, brak niezależnego użycia

### ARCH-002 — Różny układ plików w bibliotekach
Obszar: spójność
Kategoria: preferencja
Stan obecny: dwa style katalogów
Stan oczekiwany: jeden styl
Luka: kosmetyczna
Dowód: —
Wpływ: brak potwierdzonego

## Mocne strony
- lazy loading tras

## Do dalszego zbadania
- stan w serwisach
"""

RECS = """<!-- legacy-dossier:recommendations -->
# Architecture Recommendations & Roadmap — fakturowanie

## Docelowe zasady
- obowiązkowe: zależności tylko w dół (enforce-module-boundaries)

## Rekomendacje
### REC-001 — Odwrócić zależność shared-ui → shop-app
Dotyczy: ARCH-001
Decyzja: refaktoryzacja przyrostowa
Priorytet: P1
Wysiłek: 1 dzień
Ryzyko: regresja w widoku zamówień
Weryfikacja: lint zgłasza niedozwolony import, testy zielone

### REC-002 — Opisać przyjęty układ plików
Dotyczy: ARCH-002
Decyzja: dokumentacja
Priorytet: P3
Wysiłek: 1 h
Ryzyko: brak
Weryfikacja: opis w README biblioteki

## Roadmapa
Faza A: REC-001. Faza C: REC-002.

## Kryteria sukcesu
- brak importów pod prąd w nx graph
"""


def run(d: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(d / "dossier"), "--root", str(d), *args],
                          capture_output=True, text=True)


def make(d: Path, index: str = INDEX, module: str | None = MODULE, assess: str | None = None,
         recs: str | None = None) -> None:
    (d / "dossier" / "modules").mkdir(parents=True)
    if assess is not None:
        (d / "dossier" / "assessment.md").write_text(assess, encoding="utf-8")
    if recs is not None:
        (d / "dossier" / "recommendations.md").write_text(recs, encoding="utf-8")
    (d / "dossier" / "README.md").write_text(index, encoding="utf-8")
    if module is not None:
        (d / "dossier" / "modules" / "faktury.md").write_text(module, encoding="utf-8")
    (d / "src").mkdir()
    (d / "src" / "Invoice.java").write_text("class Invoice {\n  // ...\n  BigDecimal round() {}\n}\n")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    def case(index=INDEX, module=MODULE, *args, assess=None, recs=None):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            make(d, index, module, assess, recs)
            return run(d, *args)

    r = case()
    check(r.returncode == 0 and r.stdout.splitlines()[0] == "legacy-dossier-check: OK",
          f"DC-1: a complete dossier → OK on the first line: {r.stdout}{r.stderr}")

    r = case(INDEX.replace("<!-- legacy-dossier -->\n", ""))
    check(r.returncode == 1 and r.stdout.startswith("legacy-dossier-check: ERRORS") and "marker" in r.stdout,
          f"DC-2: no marker in README.md → error: {r.stdout}")

    r = case(INDEX.replace("## Słownik", "## Inne"))
    check(r.returncode == 1 and "Glossary" in r.stdout, f"DC-3: a missing index section → error: {r.stdout}")

    r = case(module=None)
    check(r.returncode == 1 and "modules/faktury.md" in r.stdout, f"DC-4: a module from the index without a file → error: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Invoice.java:99"))
    check(r.returncode == 1 and "R-FAK-01" in r.stdout and "99" in r.stdout,
          f"DC-5: evidence points to a line beyond the file → error: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Brak.java:3"))
    check(r.returncode == 1 and "src/Brak.java" in r.stdout, f"DC-6: evidence points to a nonexistent file → error: {r.stdout}")

    r = case(module=MODULE.replace("| — | do weryfikacji |", "| — | kod |"))
    check(r.returncode == 1 and "R-FAK-02" in r.stdout, f"DC-7: a rule without evidence and with confidence 'kod' → error: {r.stdout}")

    r = case(module=MODULE.replace("R-FAK-02", "R-FAK-01"))
    check(r.returncode == 1 and "R-FAK-01" in r.stdout and "duplicated" in r.stdout, f"DC-8: a repeated rule ID → error: {r.stdout}")

    r = case(module=MODULE.replace("Stan: żółty — zaokrąglenia w dwóch miejscach\n", ""))
    check(r.returncode == 1 and "State" in r.stdout, f"DC-9: a module card without the Stan field → error: {r.stdout}")

    r = case(module=MODULE.replace("| kod |", "| chyba |"))
    check(r.returncode == 1 and "chyba" in r.stdout, f"DC-10: unknown confidence → error: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Invoice.java:2-3"))
    check(r.returncode == 0, f"DC-11: a line range in the evidence is valid: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "../../etc/hosts:1"))
    check(r.returncode == 1 and "outside the repository" in r.stdout, f"DC-13: evidence from outside the repository → error: {r.stdout}")

    r = case(INDEX, MODULE, "--json")
    try:
        data = json.loads(r.stdout)
    except ValueError:
        data = {}
    check(data.get("status") == "OK" and data.get("modules") == 1 and data.get("rules") == 2
          and data.get("unverified") == 1, f"DC-12: --json with the number of modules, rules and rules to verify: {r.stdout}")

    # Architecture audit mode: assessment.md (ARCH-NNN findings) and recommendations.md (REC-NNN).
    r = case(INDEX, MODULE, "--json", assess=ASSESS, recs=RECS)
    try:
        data = json.loads(r.stdout)
    except ValueError:
        data = {}
    check(data.get("status") == "OK" and data.get("findings") == 2 and data.get("recommendations") == 2,
          f"DC-14: a full audit (inventory + assessment + recommendations) → OK: {r.stdout}")
    r = case(assess=ASSESS.replace("Kategoria: preferencja", "Kategoria: drobiazg"), recs=RECS)
    check(r.returncode == 1 and "drobiazg" in r.stdout, f"DC-15: an unknown finding category → error: {r.stdout}")
    r = case(assess=ASSESS.replace("Dowód: src/Invoice.java:3", "Dowód: —"), recs=RECS)
    check(r.returncode == 1 and "ARCH-001" in r.stdout and "evidence" in r.stdout.lower(),
          f"DC-16: a confirmed problem without evidence → error: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Dotyczy: ARCH-002", "Dotyczy: ARCH-099"))
    check(r.returncode == 1 and "ARCH-099" in r.stdout, f"DC-17: a recommendation for a nonexistent finding → error: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Dotyczy: ARCH-001", "Dotyczy: ARCH-002"))
    check(r.returncode == 1 and "ARCH-001" in r.stdout, f"DC-18: a confirmed problem without a recommendation → error: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Priorytet: P1", "Priorytet: pilne"))
    check(r.returncode == 1 and "pilne" in r.stdout, f"DC-19: unknown priority → error: {r.stdout}")
    r = case(assess=ASSESS.replace("## Mocne strony", "## Inne"), recs=RECS)
    check(r.returncode == 1 and "Strengths" in r.stdout, f"DC-20: an assessment without strengths → error: {r.stdout}")
    r = case(recs=RECS)
    check(r.returncode == 1 and "assessment.md" in r.stdout, f"DC-21: recommendations without assessment.md → error: {r.stdout}")
    r = case(assess=ASSESS.replace("Luka: zmiana w aplikacji psuje bibliotekę\n", ""), recs=RECS)
    check(r.returncode == 1 and "Gap" in r.stdout, f"DC-22: a finding without the Luka field → error: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Decyzja: dokumentacja", "Decyzja: przeprojektowanie"))
    check(r.returncode == 1 and "preference" in r.stdout and "REC-002" in r.stdout,
          f"DC-23: a redesign justified by preference alone → error: {r.stdout}")

    # 14.x: the migration rewrites a Polish dossier into English syntax; the content stays, the check passes
    import importlib.util
    spec = importlib.util.spec_from_file_location("ld_migrations", ROOT / ".tf" / "factory" / "migrations.py")
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        make(d, assess=ASSESS, recs=RECS)
        target = d / "docs" / "project" / "04-architecture" / "legacy-dossier"
        target.parent.mkdir(parents=True)
        (d / "dossier").rename(target)
        (d / ".claude").symlink_to(ROOT / ".claude", target_is_directory=True)
        (d / ".tf" / "factory" / "packs").mkdir(parents=True)
        (d / ".tf" / "factory" / "packs" / "pack-it").symlink_to(ROOT / ".tf" / "factory" / "packs" / "pack-it",
                                                              target_is_directory=True)
        changed = mig.migrate_values(d, dry=False)
        idx = (target / "README.md").read_text(encoding="utf-8")
        mod = (target / "modules" / "faktury.md").read_text(encoding="utf-8")
        ass = (target / "assessment.md").read_text(encoding="utf-8")
        rec = (target / "recommendations.md").read_text(encoding="utf-8")
        check("## Glossary" in idx and "## Open questions" in idx and "Wystawia faktury i korekty." in idx
              and "State: yellow — zaokrąglenia w dwóch miejscach" in mod and "## Business rules" in mod
              and "| ID | Rule | Evidence | Confidence |" in mod and "| src/Invoice.java:3 | code |" in mod
              and "| — | to verify |" in mod and "Category: confirmed problem" in ass and "Gap: zmiana w aplikacji" in ass
              and "Decision: incremental refactoring" in rec and "Addresses: ARCH-001" in rec,
              f"DC-24: dossier migration — sections, fields and values in English, content unchanged: {changed} {mod[:400]}")
        r = subprocess.run([sys.executable, str(SCRIPT), str(target), "--root", str(d)], capture_output=True, text=True)
        check(r.returncode == 0, f"DC-25: the dossier after migration passes the check: {r.stdout}")
        check(mig.migrate_values(d, dry=False) == [], "DC-26: a repeated dossier migration changes nothing")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of dossier_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
