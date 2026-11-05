---
name: talos-story-run
description: Użyj na polecenie człowieka (/talos-story-run, agent talos) — historyjka → plan kawałków → commit na kawałek → PR i raport kosztu.
metadata:
  przeglad: "2027-04-21"
  katalog: "Użyj tylko na polecenie człowieka (`/talos-story-run STORY [--auto] [--budget USD]` albo `claude --agent talos`) — automat „story → PR”: przyjęcie historyjki, plan z pionowych kawałków (każdy scalany i działający), pętla kawałka (test czerwony → kod → weryfikacja → przegląd zakresu → commit), przypadki brzegowe odłożone do decyzji, fazy warunkowe, STOP, jeden PR, raport czasu, tokenów, kosztu i modeli. Nie do zwykłej implementacji w rozmowie (persona pracuje sama), delegowania pracy bez nadzoru w ogóle (core-async-delegation) ani faz całego projektu (core-delivery-lifecycle)."
argument-hint: "[plik story | treść | TSK-n [--change CHG-n]] [--auto] [--budget USD]"
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
   **Karencja wersji (N10):** `python3 .claude/skills/talos-story-run/scripts/security_scan.py cooldown` — FAIL
   (brak `min-release-age=7` npm, `minimumReleaseAge: 10080` pnpm, `npmMinimalAgeGate` Yarn, `exclude-newer` uv albo
   lockfile poza gitem) → STOP z linią do dodania z wyniku; ustawień nie zmieniasz sam.
2. `run_report.py start "<tytuł historyjki>" --story-file <plik>` (albo `--story "<treść>"`) →
   katalog `tmp/talos/runs/<data>-<slug>/` (ignorowany przez git): `story.md`, `plan.md`, `parked.md`.
   Ścieżka celowo poza `.claude/` — Claude Code ma `.claude/` na liście chronionych (code.claude.com
   /docs/en/permission-modes), więc `--permission-mode acceptEdits` i tak odmówiłby pisania do `.claude/runs/`.
   **Wejście to klucz cięcia** (`/talos-story-run TSK-57`, tak woła Talosa faza realizacji zmiany): `run_report.py
   start --task TSK-57 --change CHG-12` składa `story.md` z wiersza cięcia w `docs/project/changes/CHG-12/plan.md`
   (wartość, wydanie, flaga, pliki, weryfikacja) i z `intent.md` zmiany; `run.json` dostaje `change`, `task` i `flag`.
   TSK spoza planów zmian → kod 2 i STOP („nie ma cięcia TSK-57 w planach zmian”); TSK w planach wielu zmian bez
   `--change` → kod 2 i lista zmian (PRB-33).
3. Gałąź `story/<slug>` od bazy cięcia (core-git-workflow). Zapamiętaj bazę przed `git switch -c` i wracaj do niej
   między cięciami (`git switch <baza>`), żeby kolejne cięcia nie dziedziczyły commitów poprzedniego — chyba że plan
   mówi inaczej.
   - **Przebieg cięcia ze zmianą pdi** (`--change CHG-n`, tak woła Talosa faza delivery): baza to aktualna gałąź fazy
     (`pdi/CHG-n-delivery`), bo pdi commituje na niej `decisions.md` zmiany przed uruchomieniem persony — bez tego
     cięcia nie miałyby decyzji wiążących Talosa. Nie robisz `git switch main` przed `git switch -c`.
   - **Zwykła historyjka** (bez `--change`): baza to gałąź domyślna (zwykle `main`); `git switch main`, potem
     `git switch -c story/<slug>`.
   Przy cięciu z kluczem slug zaczyna się od klucza (`story/tsk-57-…`), więc hook `commit-msg` pilnuje stopki
   `Change: TSK-57`.

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
- Przypadki brzegowe znalezione przy planowaniu → `parked.md` w formacie z nagłówka pliku. Plik jest w `tmp/talos/runs/<data>-<slug>/`
  (poza gitem) — w commitach i kodzie nie odsyłasz do niego; pozycje trafiają do opisu PR i raportu przebiegu
  (sekcja „Odłożone do decyzji”, przy cięciu z kluczem w `docs/project/changes/CHG-n/runs/TSK-n.md`).
- **Bez `--auto`:** pokaż plan (kawałki, fazy warunkowe, założenia, odłożone) i czekaj na akceptację człowieka.
  **Z `--auto`:** idziesz dalej; plan i założenia trafią do opisu PR.

## 3. Pętla kawałka
1. **Test czerwony** z kryteriów kawałka (TDD; hook `tdd_guard` pilnuje kolejności). Tylko przypadki z kryteriów.
2. **Najmniejszy kod**, który go zazieleni. Pracujesz we własnym kontekście (cache); mechaniczną zmianę w 1–2
   plikach z gotową specyfikacją zlecasz `quick-fixer`.
3. **Weryfikacja:** polecenie z planu, potem jedno polecenie weryfikacji produktu z pierwszej linii CLAUDE.md
   (format, lint, typy, testy i skan; wzór `templates/verify.sh`), a bez niego testy, lint i typy z CLAUDE.md. Linia
   werdyktu: `BRAMKA K<n>: PASS` albo `FAIL (<skrót>, próba k/2)`.
   **Skan bezpieczeństwa** po zielonych testach: `python3 .claude/skills/talos-story-run/scripts/security_scan.py scan
   --slice K<n> --attempt <k> --out <katalog-przebiegu>/security/K<n>` — semgrep (OWASP Top 10 i `.semgrep.yml`
   produktu) na plikach kawałka, audyt zależności tylko przy zmianie manifestu lub lockfile'a; SARIF, werdykt
   i `summary.md` każdej próby w `security/K<n>/proba-<k>/` (próby się nie nadpisują, raport pokazuje wszystkie).
   Blokujące (error albo warning z CWE z OWASP Top 10, reguła SEC-001 z ci_for_sdlc) → FAIL próby: ustalenia
   (reguła, plik:linia) z `security/K<n>/feedback.md` (zawsze z ostatniej próby) są wejściem następnej próby; po 2 próbach skrypt drukuje blok STOP — kawałka
   nie commitujesz, tak jak przy czerwonym teście. Brak skanera to FAIL z poleceniem instalacji, nie cichy PASS.
   Ustalenia poniżej progu trafiają do raportu przebiegu (sekcja „Bezpieczeństwo”). Nowa zależność młodsza niż
   7 dni (menedżer pakietów odmawia instalacji) → STOP z wyjaśnieniem, nie obejście.
4. **Przegląd zakresu:** `scope-reviewer` dostaje kawałek z planu i `git diff`. Kod spoza kryteriów (obsługa
   nieproszonych przypadków, refaktor obok, nowa zależność bez potrzeby) → wycofujesz, a sprawa trafia do `parked.md`.
5. **Commit** plików kawałka po nazwie: `<typ>(<zakres>): <opis>` + w treści `Kawałek K<n>: <wartość>`.
   Odhacz kawałek w `plan.md`. Przebieg cięcia z kluczem: każdy commit ma stopkę `Change: TSK-n`
   (core-conventional-commits). Kawałek cięcia z flagą (kolumna „Flaga” w planie cięć albo `flags`
   w `release.yaml`, w `run.json` pole `flag`): nowe zachowanie jest za flagą (domyślnie wyłączoną), a commit ma też
   stopkę `Flag: <klucz>`.
6. Z `--budget`: `run_report.py status <katalog>` — koszt powyżej budżetu → STOP po tym kawałku.

## 4. Zakończenie
1. Fazy warunkowe z planu (tylko te).
2. **Zgodność z planem:** `python3 .claude/skills/talos-story-run/scripts/plan_drift.py <katalog> --base <baza cięcia>`
   (dla `--change`: gałąź fazy `pdi/CHG-n-delivery`; inaczej gałąź domyślna, zwykle `main`)
   — pliki zmienione vs pliki kawałków, zmiany spoza planu, pokrycie diffu planem, testy w diffie. Zmiana spoza planu
   bez uzasadnienia → wycofujesz albo opisujesz w PR jako odstępstwo.
3. Push gałęzi i jeden PR: historyjka, kawałki = commity, weryfikacja, założenia, **Odłożone do decyzji** (lista
   z `parked.md`), wynik `plan_drift` (pokrycie, odstępstwa), skrót raportu kosztu. Nie scalasz — decyzja człowieka.
4. `run_report.py finish <katalog>` → `report.md` (czas, tokeny, koszt, modele, agenci). Pokaż
   człowiekowi skrót: czas, koszt, modele, kawałki zrobione/plan, liczba odłożonych, link do PR.
   Przebieg cięcia z kluczem: `finish` zapisuje też raport w repo, `docs/project/changes/CHG-n/runs/TSK-n.md`
   (ślad audytowy zmiany) — ten plik dołączasz do PR cięcia osobnym commitem z `Change: TSK-n`.

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
- [ ] karencja wersji (`security_scan.py cooldown`) PASS albo STOP
- [ ] każdy kawałek: test czerwony → kod → weryfikacja i skan bezpieczeństwa → przegląd zakresu → commit;
      ≤2 próby naprawy; blokujące ustalenie skanu = czerwona bramka
- [ ] przypadki brzegowe w `parked.md`, nie w kodzie; lista w opisie PR
- [ ] jeden PR, bez scalania; `run_report.py finish` uruchomiony, skrót pokazany człowiekowi

## Źródła
- Anthropic, „Prompting Claude Opus 5.5” i „Prompting Claude Sonnet 5.5” (platform.claude.com, odczyt 2026-10-20):
  praca do końca bez niezamówionych dodatków, koniec tury tekstem to raport, lista zadań do wznowienia.
- OWASP Top 10 2021 i 2025, „List of Mapped CWEs” (github.com/OWASP/Top10, odczyt 2026-11-02): lista CWE progu
  blokującego; reguła jak SEC-001 w ci_for_sdlc (`--sarif`).
- semgrep 1.183.0 (kod pakietu, odczyt 2026-11-02): `--sarif --output`, `--metrics=off`, rejestr reguł z semgrep.dev
  (host na liście dozwolonych kontenera); stan semgrepa (`SEMGREP_SETTINGS_FILE`, `SEMGREP_LOG_FILE`,
  `SEMGREP_VERSION_CACHE_PATH`) `security_scan.py` kieruje do `tmp/talos/runs/.semgrep/`, bo bez zapisywalnego HOME
  semgrep kończy się błędem (PRB-32, odtworzone 2026-11-05) — zmiennych nie dopisujesz przed poleceniem; npm 11.10.0 `min-release-age` (dni), pnpm 10.17.0 `minimumReleaseAge`
  (minuty), uv `exclude-newer` (czas względny) — szczegóły i luki: plan `docs/plans/2026-11-02-z8c-2-…`.
- Bill Wake, „INVEST in Good Stories, and SMART Tasks” (2003): kryteria dobrej historyjki i kawałka.
