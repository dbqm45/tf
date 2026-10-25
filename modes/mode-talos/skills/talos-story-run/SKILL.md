---
name: talos-story-run
description: Użyj na polecenie człowieka (/talos-story-run, agent talos) — historyjka → plan kawałków → commit na kawałek → PR i raport kosztu.
metadata:
  przeglad: 2027-04-21
  katalog: "Użyj tylko na polecenie człowieka (`/talos-story-run STORY [--auto] [--budget USD]` albo `claude --agent talos`) — automat „story → PR”: przyjęcie historyjki, plan z pionowych kawałków (każdy scalany i działający), pętla kawałka (test czerwony → kod → weryfikacja → przegląd zakresu → commit), przypadki brzegowe odłożone do decyzji, fazy warunkowe, STOP, jeden PR, raport czasu, tokenów, kosztu i modeli. Nie do zwykłej implementacji w rozmowie (persona pracuje sama), delegowania pracy bez nadzoru w ogóle (core-async-delegation) ani faz całego projektu (core-delivery-lifecycle)."
argument-hint: "[plik story | treść] [--auto] [--budget USD]"
disable-model-invocation: true
---

# Talos: historyjka → PR

Automat na żądanie. Zasady, które wygrywają z każdą pokusą „zrobić więcej”:
- **KISS:** robisz kryteria akceptacji, nic ponad nie. Przypadek brzegowy, pomysł, ryzyko → `parked.md`, nie kod.
  Wyjątek: przypadek, który łamie kryterium akceptacji albo bezpieczeństwo — obsługujesz i opisujesz w raporcie.
- **Najtaniej:** najtańszy wystarczający model na krok; czytasz raz (ustalenia trafiają do planu); fazy tylko wtedy,
  gdy są potrzebne. Bez domyślnego budżetu — `--budget` to twardy STOP.
- **Dowody:** każdy krok kończy polecenie weryfikacji z wynikiem; fakt o kodzie z `plik:linia` (core-grounding).
- **STOP zamiast brnięcia:** najwyżej 2 próby naprawy na bramkę; blokada → blok STOP i raport, nie obejście.

## 0. Start
Skrypt przebiegu: `python3 .claude/skills/talos-story-run/scripts/run_report.py` (dalej `run_report.py`).
1. Czyste drzewo robocze, inaczej STOP („niezacommitowane zmiany: <pliki>”).
2. `run_report.py start "<tytuł historyjki>" --story-file <plik>` (albo `--story "<treść>"`) →
   katalog `.claude/runs/<data>-<slug>/` (ignorowany przez git): `story.md`, `plan.md`, `parked.md`.
3. Gałąź `story/<slug>` od aktualnej gałęzi domyślnej (core-git-workflow).

## 1. Przyjęcie historyjki
Sprawdź, czy da się ją zrobić bez zgadywania: **kto, co, po co**; **kryteria akceptacji** sprawdzalne testem;
**zakres** (czego nie robimy). Stan repozytorium zbiera `scout` (lista `plik:linia`, bez całych plików).
- **Wiedza o projekcie, jeśli jest:** gdy istnieje `docs/project/00-reconstruction/standards/INDEX.md` (rekonstrukcja
  z kodu), czytasz ten spis i `docs/project/00-reconstruction/domain.md` (słownik) — standardy obowiązują w planie
  i kodzie, nazwy bierzesz ze słownika. Pełnego raportu nie czytasz; konkretny standard otwierasz, gdy kawałek go dotyczy.
- Brak kryteriów akceptacji → do 3 pytań do człowieka; z `--auto` → STOP z tymi pytaniami.
- **Kształt historyjki**, gdy jest zainstalowany lint (pack-it):
  `python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py --story <katalog-przebiegu>/story.md`.
  Uwagi AC-001…004 (scenariusz bez Wtedy, słaby wynik, szczegół implementacji, druga akcja) trafiają do planu jako
  **[założenie]** albo pytanie. STORY-001 (kilka akcji, kilku aktorów) — historyjki nie zaczynasz: bez `--auto` pytasz
  człowieka o podział; z `--auto` → blok STOP z propozycją podziału (jedna historyjka na akcję z listy akcji
  głównych, którą wypisuje lint).
- Drobna niejasność → wariant zachowawczy (mniej plików, mniejsza zmiana zachowania), zapisany w planie jako
  **[założenie]**.

## 2. Plan z kawałków
`plan.md` — jeden wiersz na kawałek, pola do odhaczenia (stan wznowienia):
`- [ ] K<n> — <wartość> · kryteria: <testy> · pliki: <ścieżki> · weryfikacja: \`<polecenie>\` · kto: <tier>`
- **Kawałek pionowy** (INVEST): niesie wartość widoczną dla użytkownika albo systemu, sam przechodzi testy i build,
  nie zostawia połowy funkcji (gdy trzeba — za flagą). Pierwszy kawałek to najcieńsza działająca ścieżka.
- Więcej niż 5 kawałków → historyjka za duża: zaproponuj podział i STOP.
- Każdy kawałek = jeden commit (Conventional Commits, core-conventional-commits); cała historyjka = jeden PR.
- **Fazy warunkowe** wpisz do planu tylko z powodem: dokumentacja przy zmianie publicznego API lub zachowania
  opisanego w docs; `security-reviewer` przy auth, sekretach, uprawnieniach, IaC, CI; `architect` przy decyzji
  trudnej do odwrócenia.
- Przypadki brzegowe znalezione przy planowaniu → `parked.md` w formacie z nagłówka pliku.
- **Bez `--auto`:** pokaż plan (kawałki, fazy warunkowe, założenia, odłożone) i czekaj na akceptację człowieka.
  **Z `--auto`:** idziesz dalej; plan i założenia trafią do opisu PR.

## 3. Pętla kawałka
1. **Test czerwony** z kryteriów kawałka (TDD; hook `tdd_guard` pilnuje kolejności). Tylko przypadki z kryteriów.
2. **Najmniejszy kod**, który go zazieleni. Pracujesz we własnym kontekście (cache); mechaniczną zmianę w 1–2
   plikach z gotową specyfikacją zlecasz `quick-fixer`.
3. **Weryfikacja:** polecenie z planu, potem testy, lint i typy projektu (komendy z CLAUDE.md). Linia werdyktu:
   `BRAMKA K<n>: PASS` albo `FAIL (<skrót>, próba k/2)`.
4. **Przegląd zakresu:** `scope-reviewer` dostaje kawałek z planu i `git diff`. Kod spoza kryteriów (obsługa
   nieproszonych przypadków, refaktor obok, nowa zależność bez potrzeby) → wycofujesz, a sprawa trafia do `parked.md`.
5. **Commit** plików kawałka po nazwie: `<typ>(<zakres>): <opis>` + w treści `Kawałek K<n>: <wartość>`.
   Odhacz kawałek w `plan.md`.
6. Z `--budget`: `run_report.py status <katalog>` — koszt powyżej budżetu → STOP po tym kawałku.

## 4. Zakończenie
1. Fazy warunkowe z planu (tylko te).
2. **Zgodność z planem:** `python3 .claude/skills/talos-story-run/scripts/plan_drift.py <katalog> --base <gałąź domyślna>`
   — pliki zmienione vs pliki kawałków, zmiany spoza planu, pokrycie diffu planem, testy w diffie. Zmiana spoza planu
   bez uzasadnienia → wycofujesz albo opisujesz w PR jako odstępstwo.
3. Push gałęzi i jeden PR: historyjka, kawałki = commity, weryfikacja, założenia, **Odłożone do decyzji** (lista
   z `parked.md`), wynik `plan_drift` (pokrycie, odstępstwa), skrót raportu kosztu. Nie scalasz — decyzja człowieka.
4. `run_report.py finish <katalog>` → `report.md` (czas, tokeny, koszt, modele, agenci). Pokaż
   człowiekowi skrót: czas, koszt, modele, kawałki zrobione/plan, liczba odłożonych, link do PR.

## Kto co robi (koszt)
| Krok | Kto | Tier |
|---|---|---|
| fakty o repozytorium | `scout` | fast |
| wersje, dokumentacja zewnętrzna | `researcher` | fast |
| plan, test, kod | Talos we własnym kontekście | std |
| zmiana mechaniczna ze specyfikacją | `quick-fixer` | fast |
| przegląd zakresu kawałka | `scope-reviewer` (świeży kontekst) | std |
| decyzja trudna do odwrócenia | `architect` (tylko analiza) | deep |
| auth, sekrety, IaC, CI | `security-reviewer` | deep |

## Blok STOP
```
STOP — <faza / K<n>>
Powód: <co blokuje, z dowodem: polecenie i wynik albo plik:linia>
Zrobione: <kawałki z SHA commitów>
Potrzebne od człowieka: <decyzja / dostęp / informacja>
Wznowienie: od <K<n> w plan.md>
```
Po STOP i tak uruchamiasz `run_report.py finish` — raport kosztu powstaje zawsze.

## Przykład
**Wejście:** `/talos-story-run "Jako operator chcę zaimportować plik CDR (CSV) i zobaczyć sesje z błędem." --auto`

**Wynik:**
- plan: K1 import poprawnego CSV do tabeli sesji (test na pliku z 3 wierszami) · K2 lista sesji z błędem walidacji
  (test: wiersz bez EVSE ID trafia na listę) · K3 komunikat o odrzuconym pliku (test: zły nagłówek → 422);
- `parked.md`: duplikaty CDR między plikami, strefy czasowe w znacznikach czasu, pliki > 50 MB — do decyzji;
- 3 commity `feat(cdr): …`, jeden PR z sekcją „Odłożone do decyzji”;
- raport: 14 min, 0,41 USD, modele: sonnet (kod), haiku (scout, quick-fixer) [przykładowe liczby].

## Checklista
- [ ] czyste drzewo, katalog przebiegu i gałąź `story/<slug>`
- [ ] historyjka gotowa (kryteria sprawdzalne) albo pytania / STOP; założenia zapisane
- [ ] plan: ≤5 kawałków pionowych, każdy z testem, plikami i weryfikacją; fazy warunkowe z powodem
- [ ] bez `--auto` — akceptacja planu przez człowieka
- [ ] każdy kawałek: test czerwony → kod → weryfikacja → przegląd zakresu → commit; ≤2 próby naprawy
- [ ] przypadki brzegowe w `parked.md`, nie w kodzie; lista w opisie PR
- [ ] jeden PR, bez scalania; `run_report.py finish` uruchomiony, skrót pokazany człowiekowi

## Źródła
- Anthropic, „Prompting Claude Opus 5.5” i „Prompting Claude Sonnet 5.5” (platform.claude.com, odczyt 2026-10-20):
  praca do końca bez niezamówionych dodatków, koniec tury tekstem to raport, lista zadań do wznowienia.
- Bill Wake, „INVEST in Good Stories, and SMART Tasks” (2003): kryteria dobrej historyjki i kawałka.
