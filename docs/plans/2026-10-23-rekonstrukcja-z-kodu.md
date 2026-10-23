# Plan: rekonstrukcja projektu z kodu

Data: 2026-10-23 · Status: **F0 i F1a zrobione** (scenariusze; graf Java/C#/Go), dalej F1b · Gałąź robocza: `claude/great-hypatia-angvam`

## TL;DR
Nowy skill w `pack-it` (roboczo `eng-project-reconstruction`), który z samego repozytorium (duże, stare, wiele języków)
robi czytelny raport: opis projektu, stack, moduły, domeny i słownik, wymagania, reguły biznesowe, standardy kodu,
ryzyka, sprzeczności, pytania do ludzi. Każde twierdzenie ma dowód `plik:linia`, a skrypt kontrolny sprawdza,
czy dowód istnieje. Cel: **lepiej i taniej niż maister** (SkillPanel/maister, MIT) — mierzone na tych samych repo.
Talos jest osobnym trybem (zmienia kod), ale czyta wynik rekonstrukcji (standardy i słownik) jako kontekst.
Konektory (GitHub, Confluence, Slack) — na samym końcu, odłożone do osobnej decyzji. PHP — poza zakresem (decyzja
użytkownika).

## Przekazanie (jak wznowić po wyczyszczeniu kontekstu)
1. Przeczytaj ten plik i `git status` w `/home/user/tf`.
2. Następny krok: **F1b** (patrz „Etapy”). F0 i F1a gotowe; F0: scenariusze w `docs/plans/evals/eng-project-reconstruction.json`
   (9: 5 trigger, 4 no-trigger z sąsiadami); w F2 przenieść je do `packs/pack-it/tests/skill_evals/` (walidator wymaga
   istniejącego `SKILL.md`, dlatego teraz leżą w `docs/plans/`).
3. Zasady repo: bez README opisującego fabrykę (repo publiczne); `claude-team-factory` i `ev-team-factory` nietknięte;
   merge do `main` po zielonym CI; odpowiedzi po polsku; płatne ewaluacje tylko za zgodą.
4. Bramki przed PR: `python3 tools/workspace.py assemble --packs all --out .work/X`, w `.work/X`:
   `python3 factory/skill_gate.py <skill>`, `python3 factory/skill_gate.py --hints`,
   `python3 .claude/tests/run_skill_evals.py --validate`; w repo: `python3 tools/workspace.py refs`
   (zakaz nazw skilli z innej nakładki), `python3 -m pytest tests/`, `tools/workspace.py sync-gate --out .work/X`.

## Kontekst i decyzje użytkownika (2026-10-23)
- Na teraz **tylko analiza kodu**. Konektory do Confluence, Slacka i **GitHuba** (issues, PR, dyskusje jako źródło
  wymagań) — ostatni etap, decyzja później.
- **Bez PHP.** Języki do dodania w `code_graph.py`: Java, C#, Go (obecnie tylko Python i TS/JS).
- Ma być lepsze od maistera i tańsze; wykorzystać wiedzę o Claude i nowe funkcje (mody, workflow itp.), o ile zasadne.
- Talos: nie scalać, połączyć przez pliki wynikowe.

## Co jest dziś w fabryce (sprawdzone 2026-10-23)
- `packs/pack-it/skills/eng-codebase-mapping/scripts/code_graph.py` — punkty wejścia, warstwy z importów, huby, cykle,
  `--impact`, `--focus`; tylko Python i TS/JS (`TS_EXT`, `ast` dla Pythona).
- `.../eng-codebase-mapping/scripts/git_territory.py` — hotspoty i właściciele z historii gita.
- `.../eng-legacy-dossier/` — szablon dossier as-is + `scripts/dossier_check.py` (kontrola kompletności).
- `eng-code-audit`, `eng-tech-debt-audit`, `ddd-legacy-modernization`, `ddd-strategic-analysis`,
  `ddd-algorithm-recognition`, `core-project-record` (`docs/project/`), `core-cost-control`.
- `modes/mode-talos/skills/talos-story-run/scripts/run_report.py` — katalog przebiegu, budżet, raport kosztu.
- Brakuje: procesu end-to-end, wykrywania standardów, wymagań odtwarzanych z testów i walidacji, weryfikatora
  dowodów (cytat vs linia), odświeżania przyrostowego, Javy/C#/Go w grafie, schematu bazy jako źródła domeny.

## Dlaczego mamy szansę być lepsi i tańsi niż maister
maister (z README, 2026-10): `/maister:init` i `/maister:standards-discover` skanują konfigurację, wzorce i dokumentację
do `.maister/docs/standards/` + `INDEX.md`; orkiestrator potrafi stanąć po kompaktowaniu. Nasze przewagi, które
trzeba **zmierzyć**, nie zakładać:

| Dźwignia | Jak | Efekt |
|---|---|---|
| Najpierw skrypty, potem model | Spis, graf, git, standardy-sygnały, schemat bazy liczone deterministycznie (0 tokenów) | Model czyta streszczenia, nie repo |
| Podział na kawałki wg budżetu tokenów | `repo_inventory.py` dzieli repo na partie ~N tys. tokenów wg modułów z grafu | Równoległe, przewidywalne koszty |
| Kaskada modeli | Haiku: karty modułów (ekstrakcja z dowodem); Sonnet: synteza domen i standardów; Opus tylko przy sprzecznościach | Najdroższy model na najmniejszym wejściu |
| Wspólny, stabilny prefiks | Identyczny początek promptu dla wszystkich kart (instrukcja + mapa repo), zmienna część na końcu | Trafienia w cache promptu [niezweryfikowane w Claude Code dla subagentów — zmierzyć] |
| Ustrukturyzowane wyjście | Karta modułu jako JSON wg schematu → scalanie i kontrola skryptem | Mniej tokenów syntezy, zero „zgubionych” ustaleń |
| Weryfikator dowodów | `recon_check.py`: plik istnieje, linia istnieje, cytat pasuje do linii (±2); odrzuca halucynacje | Precyzja mierzalna, nie deklarowana |
| Odświeżanie przyrostowe | Hash zawartości modułu w `manifest.json`; ponowna analiza tylko zmienionych (git diff) | Druga i kolejne analizy za ułamek kosztu |
| Punkty kontrolne | Plan przebiegu z polami do odhaczenia (wzór Talosa), wznowienie po kompaktowaniu/przerwie | Brak „stania” orkiestratora |
| Twardy budżet | Szacunek przed startem (tokeny × cennik), STOP po przekroczeniu, raport kosztu | Koszt pod kontrolą człowieka |
| Pewność i luki | Każda sekcja: poziom pewności + „czego nie sprawdzono” + pytania do ludzi | Uczciwy raport zamiast „pewnej” fikcji |

## Nowe funkcje Claude / Claude Code — co bierzemy
Ocena zasadności; fakty o funkcjach do potwierdzenia w dokumentacji przed użyciem (core-grounding).

| Funkcja | Decyzja | Uzasadnienie |
|---|---|---|
| Subagenci z parametrem `model` (tło, równolegle) | **Tak, domyślnie** | Karty modułów równolegle na Haiku; działa bez dodatkowych zgód |
| Narzędzie Workflow (skrypt orkiestracji: `agent()`, `parallel()`, `pipeline()`, schematy, wznowienie) | **Tak, jako tryb opcjonalny** dla dużych repo | Deterministyczna orkiestracja i wznawianie; wymaga wyraźnej zgody użytkownika na przebieg wieloagentowy |
| Skrypty w skillu (progressive disclosure) | **Tak** | Ciężka praca poza kontekstem modelu |
| Message Batches API (zniżka za tryb wsadowy) | **Opcja „tanio i wolno”** dla `claude -p`/SDK z kluczem API [niezweryfikowane: wysokość zniżki i dostępność w planie użytkownika] | Karty modułów nie muszą być interaktywne |
| Prompt caching | **Tak** (projekt promptów pod cache) | Patrz tabela wyżej |
| Artifacts (prywatna strona HTML) | **Tak, na koniec** | „Czytelny raport” do przeglądarki/udostępnienia: spis, diagram modułów, filtr pewności |
| Mod (plugin-authoring: panel obok czatu, status line) | **Później, opcjonalnie** | Panel postępu: moduły zrobione/w toku, koszt vs budżet. Miłe, nie krytyczne |
| Hooki | **Nie dla rekonstrukcji** | Tryb tylko do odczytu; kontrola skryptem na końcu wystarczy |
| `/loop`, zaplanowane zadania, `claude -p` w CI | **Później** | Okresowe odświeżanie przyrostowe raportu |
| Worktree | **Nie** | Nic nie zmieniamy w kodzie |
| Długi kontekst (1M) | **Tylko synteza, jeśli dostępny** [niezweryfikowane] | Karty i tak są małe; nie płacić za czytanie całego repo |

## Playbook „The AI-native SDLC” (Anthropic, 21.08.2026) — co bierzemy
Przejrzany 2026-10-23. Fabryka ma go już opracowanego w `core/skills/core-delivery-lifecycle/references/ai-native-sdlc.md`
(łańcuch artefaktów, plan przed kodem, `CLAUDE.md`, skille i hooki, ciągłe ewaluacje, `REVIEW.md`, bramki,
`control_band.py` z pasmami 1σ/2σ/3σ). Nie dublujemy tego. Luki, które warto domknąć w tym planie:

| Z playbooka | Luka w fabryce | Gdzie w planie |
|---|---|---|
| `/init` → `CLAUDE.md` poniżej strony; `REVIEW.md` z zasadami przeglądu | Brak generatora z faktycznego kodu | **F2:** rekonstrukcja tworzy szkice `CLAUDE.md` (polecenia, konwencje, pułapki — tylko to, czego agent nie wywnioskuje) i `REVIEW.md` (standardy jako reguły przeglądu, waga, limit drobiazgów, wykluczenia) z dowodami; człowiek zatwierdza |
| Miary: odsetek zmian zielonych za pierwszym razem, czas od planu do merge, zgodność diffu z `plan.md` | Opisane, nieliczone | **F3:** `plan_drift.py` (pliki w diffie vs pliki w `plan.md`, testy obiecane vs dodane) + miary w raporcie przebiegu Talosa |
| Jedno źródło prawdy na artefakt, powiązanie z SHA commita | Częściowo | **F2:** `manifest.json` z SHA bazowym; raport podaje, co jest źródłem (repo) i czego nie widziano (zewnętrzne systemy) |
| Każdy incydent → nowy stały scenariusz ewaluacji | Reguła jest, nie ma jej w rekonstrukcji | **F4:** każde błędne twierdzenie znalezione w benchmarku → nowy scenariusz lub test `recon_check` |
| Ciągłe ewaluacje przy każdej zmianie skilli/`CLAUDE.md`, wg harmonogramu | Płatne przebiegi tylko ręcznie, za zgodą | **Decyzja D5** (koszt): np. tygodniowy przebieg Haiku na scenariuszach zmienionych skilli z budżetem |

Pominięte (poza zakresem analizy kodu albo już pokryte): Claude Design, Claude Tag, Claude Security (produkty,
konektory — etap F7), ustawienia zarządzane i hooki-bramki wdrożeń (już w referencji), tryb auto i worktree.

## Wynik (w analizowanym projekcie)
```
docs/project/00-reconstruction/
  report.md            # raport zbiorczy: TL;DR, opis, stack, mapa modułów, domeny, wymagania, reguły,
                       # standardy (skrót), ryzyka, sprzeczności, pytania, czego nie sprawdzono, koszt przebiegu
  stack.md             # wersje z plików budowania (pom/gradle/csproj/go.mod/package.json/pyproject)
  modules/<moduł>.json # karty modułów (schemat), + .md generowane skryptem
  domain.md            # subdomeny, konteksty, słownik (termin → plik:linia), rozjazdy nazw
  requirements.md      # wymagania odtworzone z testów, walidacji, endpointów, schematu bazy
  rules.md             # reguły biznesowe z dowodem
  standards/INDEX.md   # spis standardów (pomysł z maistera) + pliki per obszar:
  standards/<obszar>.md  # nazewnictwo, błędy, testy, API, logowanie, konfiguracja, warstwy…
                         # każdy: reguła, dowód, liczba wystąpień, wyjątki, sprzeczności, pewność
  CLAUDE.draft.md      # szkic instrukcji dla agenta (< 1 strona), do zatwierdzenia
  REVIEW.draft.md      # szkic zasad przeglądu PR ze standardów
  manifest.json        # hashe modułów, data, commit, koszt — podstawa odświeżania przyrostowego
```

## Przebieg skilla (7 kroków)
1. **Start:** katalog przebiegu, commit bazowy, szacunek kosztu z `repo_inventory.py`, zgoda na budżet, plan z polami.
2. **Spis mechaniczny (0 tokenów):** `repo_inventory.py` (języki, rozmiary, pliki budowania, wykluczenia
   vendor/generated, podział na partie), `code_graph.py`, `git_territory.py`, `standards_scan.py`, `schema_scan.py`.
3. **Karty modułów (Haiku, równolegle):** odpowiedzialność, wejścia, zależności, reguły, pojęcia, odstępstwa — JSON
   z dowodami. `recon_check.py` po każdej partii; karta z błędnymi dowodami wraca raz, potem eskalacja na Sonnet.
4. **Domeny i słownik (Sonnet):** z kart + grafu; metoda z `ddd-legacy-modernization` i `ddd-strategic-analysis`.
5. **Wymagania i reguły:** z testów (nazwy, asercje), walidacji, endpointów, ograniczeń w schemacie bazy.
6. **Standardy:** sygnały ze `standards_scan.py` + potwierdzenie na próbkach; liczby wystąpień i wyjątki.
7. **Raport + kontrola:** `recon_check.py --final` (dowody, kompletność sekcji, pewność, pytania), raport kosztu,
   opcjonalnie Artifact HTML.

Odświeżanie: `--refresh` → tylko moduły ze zmienionym hashem + ponowna synteza dotkniętych sekcji.

## Etapy realizacji (każdy = osobny PR, zielone CI, merge)
- **F0. Scenariusze i decyzje (darmowe).** Scenariusze ewaluacji skilla (trafienie, sąsiedzi: `eng-legacy-dossier`,
  `eng-codebase-mapping`, `eng-code-audit`, `ddd-legacy-modernization`; zakazy: zmiana kodu, twierdzenie bez dowodu),
  `checks` rozróżniające; decyzje D1–D4.
- Etapy są cięte tak, żeby każdy zmieścił się w jednym oknie limitu (~5–10% tygodniowego) i kończył się zielonym CI
  i merge — bez przerywania w połowie.
- **F1a. Graf dla Javy, C# i Go (TDD):** ✓ zrobione 2026-10-23 (`code_graph.py`, testy T13–T15).
  - `code_graph.py`: Java (package/import, `@SpringBootApplication`, `main`, kontrolery), C# (namespace/using,
    `Program.cs`, kontrolery ASP.NET), Go (`package`/`import`, `func main`, `go.mod` jako korzeń modułu). Testy na
    małych fixture'ach w `tests/`.
- **F1b. Spis i standardy (TDD):** `repo_inventory.py`, `standards_scan.py`.
- **F1c. Schemat i weryfikator (TDD):** `schema_scan.py` (migracje SQL, Flyway/Liquibase, encje JPA i EF),
    `recon_check.py` (weryfikator dowodów i kompletności).
- **F2. Skill + szablony:** `SKILL.md` (zwięźle, przykłady), `references/` (szablon raportu, schemat karty JSON,
  prompt karty pod cache), bramka, `refs`, `--hints`.
- **F3. Integracja z Talosem:** w kroku przyjęcia historyjki Talos czyta `docs/project/00-reconstruction/standards/INDEX.md`
  i `domain.md`, jeśli istnieją (bez nazw skilli z innej nakładki — opis słowny). Scenariusz ewaluacji Talosa.
- **F4. Pomiar (płatny, za zgodą):** ewaluacja skilla na Haiku (~1–2 USD); benchmark vs maister — patrz niżej.
- **F5. Odświeżanie przyrostowe + raport HTML (Artifact).**
- **F6. Opcjonalnie:** mod z panelem postępu; tryb Workflow dla bardzo dużych repo; tryb wsadowy (Batches).
- **F7. Odłożone do decyzji:** konektory GitHub (issues/PR jako źródło wymagań), Confluence, Slack;
  izolacja przebiegu „bez skilli” (już w `docs/todo.md`).

## Benchmark vs maister (F4, płatny)
- Repozytoria: 3 publiczne — średnie Java/Spring, stare (np. sprzed 10 lat) Java lub C#, Go. Wybór do zatwierdzenia.
- maister instalujemy w osobnym, jednorazowym workspace, po `skill_audit.py` i zgodzie użytkownika (obcy plugin).
- Złoty standard: ręcznie przygotowana lista ~20 faktów na repo (stack, moduły, 5 reguł, 5 standardów).
- Metryki: koszt USD i czas; pokrycie złotych faktów; precyzja dowodów (losowe 30 twierdzeń → `recon_check` + ręcznie);
  liczba twierdzeń bez dowodu; koszt odświeżenia po zmianie 5% plików.
- Kryterium sukcesu: ≥ pokrycie maistera przy ≤ 50% kosztu, precyzja dowodów ≥ 95% [cel do potwierdzenia pomiarem].

## Decyzje (przyjęte domyślnie 2026-10-23 — użytkownik może zmienić)
- **D1. Nazwa skilla:** `eng-project-reconstruction` (domyślnie).
- **D2. Wspólna mechanika przebiegu:** `run_report.py` jest w `mode-talos`, a nakładki nie mogą się odwoływać do siebie.
  Opcje: (a) przenieść ogólną część do `core/` i używać w obu (domyślnie, w F2), (b) osobna mała kopia w skillu.
- **D3. Wybór repo do benchmarku** i zgoda na koszt (szacunek podam przed startem).
- **D4. Raport HTML jako Artifact** — domyślnie tak (prywatny) w F5; Markdown zawsze.
- **D3** nadal otwarte (przed F4).
- **D5. Ciągłe ewaluacje wg harmonogramu** (płatne) — otwarte; domyślnie nie, tylko ręcznie za zgodą.

## Ryzyka
- Regex dla Javy/C#/Go nie złapie wszystkiego (refleksja, DI z XML, generowany kod) → raport oznacza luki;
  ewentualnie tree-sitter, jeśli zainstalowany (opcjonalnie, bez twardej zależności).
- Haiku może gubić reguły w gęstym kodzie → eskalacja per karta po błędzie `recon_check`.
- Prompt caching w subagentach może nie działać tak, jak zakładamy → zmierzyć w F4, nie obiecywać.
- Benchmark z maistrem zależy od stanu jego wersji w dniu pomiaru — zapisać commit.
