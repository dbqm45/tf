#!/usr/bin/env python3
"""Testy skryptu dossier_check.py (skill eng-legacy-dossier): kompletność teczki systemu i dowody reguł biznesowych."""
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
          f"DC-1: kompletna teczka → OK w pierwszej linii: {r.stdout}{r.stderr}")

    r = case(INDEX.replace("<!-- legacy-dossier -->\n", ""))
    check(r.returncode == 1 and r.stdout.startswith("legacy-dossier-check: BŁĘDY") and "znacznik" in r.stdout,
          f"DC-2: brak znacznika w README.md → błąd: {r.stdout}")

    r = case(INDEX.replace("## Słownik", "## Inne"))
    check(r.returncode == 1 and "Słownik" in r.stdout, f"DC-3: brak sekcji indeksu → błąd: {r.stdout}")

    r = case(module=None)
    check(r.returncode == 1 and "modules/faktury.md" in r.stdout, f"DC-4: moduł z indeksu bez pliku → błąd: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Invoice.java:99"))
    check(r.returncode == 1 and "R-FAK-01" in r.stdout and "99" in r.stdout,
          f"DC-5: dowód wskazuje linię spoza pliku → błąd: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Brak.java:3"))
    check(r.returncode == 1 and "src/Brak.java" in r.stdout, f"DC-6: dowód wskazuje nieistniejący plik → błąd: {r.stdout}")

    r = case(module=MODULE.replace("| — | do weryfikacji |", "| — | kod |"))
    check(r.returncode == 1 and "R-FAK-02" in r.stdout, f"DC-7: reguła bez dowodu i z pewnością „kod” → błąd: {r.stdout}")

    r = case(module=MODULE.replace("R-FAK-02", "R-FAK-01"))
    check(r.returncode == 1 and "R-FAK-01" in r.stdout and "powt" in r.stdout, f"DC-8: powtórzone ID reguły → błąd: {r.stdout}")

    r = case(module=MODULE.replace("Stan: żółty — zaokrąglenia w dwóch miejscach\n", ""))
    check(r.returncode == 1 and "Stan" in r.stdout, f"DC-9: karta modułu bez pola Stan → błąd: {r.stdout}")

    r = case(module=MODULE.replace("| kod |", "| chyba |"))
    check(r.returncode == 1 and "chyba" in r.stdout, f"DC-10: nieznana pewność → błąd: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "src/Invoice.java:2-3"))
    check(r.returncode == 0, f"DC-11: zakres linii w dowodzie jest poprawny: {r.stdout}")

    r = case(module=MODULE.replace("src/Invoice.java:3", "../../etc/hosts:1"))
    check(r.returncode == 1 and "poza repozytorium" in r.stdout, f"DC-13: dowód spoza repozytorium → błąd: {r.stdout}")

    r = case(INDEX, MODULE, "--json")
    try:
        data = json.loads(r.stdout)
    except ValueError:
        data = {}
    check(data.get("status") == "OK" and data.get("modules") == 1 and data.get("rules") == 2
          and data.get("unverified") == 1, f"DC-12: --json z liczbą modułów, reguł i reguł do weryfikacji: {r.stdout}")

    # Tryb audytu architektury: assessment.md (ustalenia ARCH-NNN) i recommendations.md (REC-NNN).
    r = case(INDEX, MODULE, "--json", assess=ASSESS, recs=RECS)
    try:
        data = json.loads(r.stdout)
    except ValueError:
        data = {}
    check(data.get("status") == "OK" and data.get("findings") == 2 and data.get("recommendations") == 2,
          f"DC-14: pełny audyt (inventory + assessment + recommendations) → OK: {r.stdout}")
    r = case(assess=ASSESS.replace("Kategoria: preferencja", "Kategoria: drobiazg"), recs=RECS)
    check(r.returncode == 1 and "drobiazg" in r.stdout, f"DC-15: nieznana kategoria ustalenia → błąd: {r.stdout}")
    r = case(assess=ASSESS.replace("Dowód: src/Invoice.java:3", "Dowód: —"), recs=RECS)
    check(r.returncode == 1 and "ARCH-001" in r.stdout and "dow" in r.stdout.lower(),
          f"DC-16: potwierdzony problem bez dowodu → błąd: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Dotyczy: ARCH-002", "Dotyczy: ARCH-099"))
    check(r.returncode == 1 and "ARCH-099" in r.stdout, f"DC-17: rekomendacja do nieistniejącego ustalenia → błąd: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Dotyczy: ARCH-001", "Dotyczy: ARCH-002"))
    check(r.returncode == 1 and "ARCH-001" in r.stdout, f"DC-18: potwierdzony problem bez rekomendacji → błąd: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Priorytet: P1", "Priorytet: pilne"))
    check(r.returncode == 1 and "pilne" in r.stdout, f"DC-19: nieznany priorytet → błąd: {r.stdout}")
    r = case(assess=ASSESS.replace("## Mocne strony", "## Inne"), recs=RECS)
    check(r.returncode == 1 and "Mocne strony" in r.stdout, f"DC-20: assessment bez mocnych stron → błąd: {r.stdout}")
    r = case(recs=RECS)
    check(r.returncode == 1 and "assessment.md" in r.stdout, f"DC-21: rekomendacje bez assessment.md → błąd: {r.stdout}")
    r = case(assess=ASSESS.replace("Luka: zmiana w aplikacji psuje bibliotekę\n", ""), recs=RECS)
    check(r.returncode == 1 and "Luka" in r.stdout, f"DC-22: ustalenie bez pola Luka → błąd: {r.stdout}")
    r = case(assess=ASSESS, recs=RECS.replace("Decyzja: dokumentacja", "Decyzja: przeprojektowanie"))
    check(r.returncode == 1 and "preferencj" in r.stdout and "REC-002" in r.stdout,
          f"DC-23: przeprojektowanie uzasadnione samą preferencją → błąd: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów dossier_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
