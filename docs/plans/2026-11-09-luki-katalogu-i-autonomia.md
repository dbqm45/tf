# Plan: luki katalogu (sekcja A) i polityka autonomii (sekcja B)

Stan: 2026-11-09, do akceptacji kroków. Źródło: przegląd listy kompetencji „Autonomous Full Stack Agent” (obszary
A–L, cykl życia, artefakty, kategorie dodatkowe) i propozycji „Agent Architecture & Autonomy” wobec katalogu fabryki.
Decyzja człowieka 2026-11-09: najpierw sekcja A, potem B.

Pokrycie sprawdzone 2026-11-09 wyszukaniem słów kluczowych w `SKILL.md` i `references/` (`core/`, `packs/`, `modes/`)
— przegląd zgrubny, nie audyt treści. Liczby w nawiasach to liczba skilli z trafieniem.

Zasady dla każdego kroku:
- Nowy lub zmieniany skill wg `core-skill-authoring`: najpierw scenariusze `tests/skill_evals/<skill>.json`, potem
  treść, `python3 .tf/factory/skill_gate.py <skill>` w `.work/h-all` i `tools/workspace.py sync-gate`.
- Kod (moduły `tf analyze`, hooki, instalator) metodą TDD: test czerwony, potem kod.
- Każdy krok to osobny PR; ewaluacja na modelu (płatna) tylko za zgodą człowieka.
- Skill dostaje miejsce tylko wtedy, gdy wypełnia lukę; nie dopisujemy treści „dla kompletności”.

## Sekcja A — luki w katalogu

### A1. Analityka produktowa — nowy skill `pm-product-analytics` (`pack-it`, obok `pm-*`)
Luka: plan śledzenia zdarzeń (0 trafień). `pm-saas-metrics` liczy MRR i churn, ale nie mówi, jak zbierać dane.
- Zakres: pytanie → metryka → zdarzenie; plan śledzenia (nazewnictwo `obiekt_czynność`, właściwości, wersje
  schematu); instrumentacja klient/serwer; tożsamość (anonimowy → zalogowany); zgody RODO i ePrivacy na śledzenie,
  minimalizacja; lejki, retencja kohort, aktywacja; jakość danych zdarzeń (duplikaty, brakujące zdarzenia, testy
  instrumentacji); narzędzia (PostHog, Amplitude, Mixpanel, własny potok) bez reklamy dostawcy.
- Powiązania: `pm-saas-metrics`, `proc-product-discovery`, `arch-privacy-compliance`, `data-engineering`.
- Scenariusze ewaluacji przed treścią (np. „dodaj śledzenie rejestracji”, „lejek nie zgadza się z bazą”, „śledzenie bez
  zgody”).

### A2. Wzorce aplikacji biznesowej — w `pack-it` (decyzja człowieka 2026-11-09: bez osobnej nakładki)
Luki: soft delete (0), impersonacja (0), tabele danych z filtrowaniem po stronie serwera i eksport (słabo), command
palette (1), audit log jako funkcja produktu (4), ABAC (1). Wzorce występują w każdej aplikacji biznesowej (CPMS,
eMSP, systemy wewnętrzne, panele), więc trafiają do `pack-it`, a nie do nakładki „admin”. Plan szczegółowy:
`docs/plans/2026-11-09-a2-wzorce-aplikacji-biznesowej.md`.
- A2a. Skill `be-business-app-patterns` (nazwa robocza): uprawnienia sprawdzane na serwerze (RBAC, kiedy ABAC),
  audit log, soft delete, impersonacja, operacje masowe, potwierdzenia operacji nieodwracalnych.
- A2b. Tabele danych i eksport: referencje w `fe-architecture` (stan w URL, wirtualizacja, operacje masowe
  z zaznaczania, command palette, dostępność tabel) i `be-api-design` (filtrowanie i sortowanie po stronie serwera,
  paginacja kursorowa, eksport w tle).
- A2c. Moduł `tf analyze` `authz` w `pack-it` (tier 0, TDD): endpointy zmieniające dane bez sprawdzenia uprawnień
  po stronie serwera, uprawnienie sprawdzane tylko w UI, usuwanie bez audytu.

### A3. Developer Experience — rozszerzenie `eng-repo-readiness` (`pack-it`)
Luka: devcontainer, `docker compose` dla środowiska deweloperskiego, `make`/`just`, czas wejścia do projektu, pętla
feedbacku (0 trafień dla devcontainera). Skill dziś patrzy pod kątem agentów.
- Zakres: jedno polecenie do uruchomienia projektu, zależności usług lokalnie, dane startowe (seed), sekrety
  deweloperskie bez prawdziwych kluczy, czas od klonu do zielonych testów jako miara, szybkie testy powiązane.
- Rozszerzenie zamiast nowego skilla; nowe scenariusze ewaluacji dla części DX.

### A4. Mapa artefaktów — `core-delivery-lifecycle` (`core`)
Luka: jedno miejsce „faza → artefakt → kto pisze → skill źródłowy”; brak ERD (0 trafień).
- Tabela artefaktów: PRD, SPEC, ARCHITECTURE, ADR, ERD, openapi, DESIGN_SYSTEM, ACCESSIBILITY, SECURITY,
  THREAT_MODEL, TEST_PLAN, DEPLOYMENT, RUNBOOK, CHANGELOG, README — w której fazie powstaje, która persona lub rola
  pisze, który skill prowadzi, kiedy artefakt jest zbędny (mały projekt).
- ERD: dopisać do `be-database` (diagram encji jako kod, np. Mermaid, z migracji).

### A5. Ład danych — sekcja w `arch-privacy-compliance` (`pack-it`)
Luka: własność danych, klasyfikacja (public, internal, confidential, PII), katalog i pochodzenie danych są
rozproszone po `data-engineering` i skillach bezpieczeństwa; retencja i RODO są pokryte.
- Sekcja „ład danych”: właściciel zbioru, klasy i wymagania na klasę (szyfrowanie, dostęp, maskowanie, retencja),
  inwentarz danych osobowych, odwołanie do `data-engineering` (pochodzenie, kontrakty danych).

### A6. Biblioteki formularzy — referencja w `fw-react` (`pack-it`)
Luka: React Hook Form (0 trafień), walidacja (Zod) jest. Referencja: formularz z walidacją schematem współdzielonym
z serwerem, błędy pól i formularza, dostępność, formularze wielokrokowe.

### A7. Kolejne moduły `tf analyze` (tier 0)
Obecnie `security` i `architecture` (`pack-it`). Kandydaci, każdy jako osobny krok z fixtures i bramką:
- `accessibility` (odłożony krok 3 planu `2026-11-08-tf-analyze-i-katalog-tf.md`), `pack-ux`;
- `tech-debt` (TODO/FIXME z wiekiem z gita, martwy kod, przestarzałe zależności), `pack-it`;
- `i18n` (zahardkodowane teksty UI, formatowanie dat i kwot bez `Intl`), `pack-it`;
- `observability` (brak health checków, logi nieustrukturyzowane, brak identyfikatora korelacji), `pack-it`.

### A8. Pytanie o brakującą informację — `ai-agents` (`pack-it`, dopisane 2026-11-09, decyzja człowieka)
Luka: `ai-agents` opisuje zatwierdzanie akcji przez człowieka, ale nie pauzę z pytaniem o brakującą informację
(artykuł R. Gite, „Six Agent Harness Techniques That Actually Worked for Me”, 2026-11-02). Zakres: agent najpierw
szuka informacji narzędziami i w kontekście; dopiero brak, którego nie da się uzupełnić, kończy się konkretnym
pytaniem; stan przebiegu zachowany i wznowienie od miejsca przerwania; bez pytań, gdy odpowiedź jest dostępna.
Nowy scenariusz ewaluacji (agent ma zapytać zamiast zgadywać) i sąsiad, w którym pytać nie należy.

### A9. Przegląd specyfikacji przez panel recenzentów — `core-delivery-lifecycle` (dopisane 2026-11-09, decyzja człowieka)
Luka: jest „przegląd planu” w fazie 5 i `ddd-model-stress-test` dla modelu domeny, ale brak niezależnego przeglądu
specyfikacji przed kodem (artykuł G. Trisciuoglio, „Spec-Driven Development: How I Stopped Vibe Coding My AI
Agents”, 2026-08-19). Zakres, bez zewnętrznych narzędzi — podagenci Claude w osobnych kontekstach:
- 2–3 recenzentów bez wglądu w siebie nawzajem, każdy z innym zadaniem: przeciwnik (dziury, sprzeczności,
  niesprawdzalne wymagania), operator (awarie, częściowe zapisy, współbieżność, ponowienia, obserwowalność),
  wykonawca (czy da się zbudować i sprawdzić testem w ustalonym stacku);
- raport: ustalenia z wagą (blokujące / poważne / drobne), zbieżne u wszystkich (defekt) osobno od pojedynczych
  (do zważenia) i rozbieżnych (decyzja człowieka); uwaga o ograniczonej niezależności (ten sam dostawca modeli);
- bramka: specyfikacja przechodzi do planu, gdy blokujące i poważne ustalenia są zamknięte śladem (nowe lub
  zmienione wymaganie, zapisana decyzja); recenzent zadania może odrzucić pracę, cytując ustalenie;
- referencja w `core-delivery-lifecycle`, szablon raportu w `core-project-record`, scenariusz ewaluacji.

### Kolejność sekcji A
1. A1 i A2 (największe luki w aplikacjach biznesowych).
2. A3 i A4 (rozszerzenia istniejących skilli).
3. A5 i A6.
4. A7, gdy jest potrzeba — moduł po module.

## Sekcja B — architektura agenta i autonomia

Pięć warstw z propozycji odpowiada fabryce: warstwy 1–4 to skille i nakładki, warstwa 5 to persony, hooki, `.tf/wip`
i bramki. Osobny projekt „standardu” nie jest potrzebny; profile aplikacji, gdy będą potrzebne, to nakładki;
wzorce wspólne dla aplikacji biznesowych zostają w `pack-it` (A2). Ręcznie spisaną macierz wiedzy (20–30 domen, 150–250 subdomen, L1–L4) zastępuje B2.

### B1. Jawna polityka autonomii — `autonomy:` w `.tf/config/config.yaml`
Luka: granice są rozproszone (`ask`/`deny` w `settings.json`, hooki `guard_bash` i `guard_paths`, zasady
w `core-async-delegation` i `core-agent-security`); brak jednego miejsca „typ operacji → poziom”.
- Poziomy: `full` (samodzielnie), `evidence` (samodzielnie z wymaganym dowodem), `confirm` (pytanie do człowieka),
  `deny`.
- Typy operacji (wartości domyślne w `.tf/factory/config.yaml`, nadpisanie w `.tf/config/config.yaml`):
  analiza kodu, komponenty, testy → `full`; refaktoryzacja → `full` w uzgodnionym zakresie; nowa zależność →
  `evidence` (audyt wg `ops-supply-chain-security`); zmiana architektury → `evidence` (ADR); zmiany bezpieczeństwa →
  `evidence` (przegląd `security-reviewer`); migracja bazy → `full` lokalnie i w testach, `confirm` na produkcji;
  deploy staging → `full`; deploy produkcja → `confirm`; usuwanie danych (`DROP`, `TRUNCATE`, `DELETE` bez `WHERE`,
  `rm -rf` poza katalogiem roboczym) → `confirm`.
- Egzekwowanie: hook (`guard_bash` albo nowy `autonomy_guard`) czyta politykę i dla `confirm` zwraca decyzję „ask”,
  dla `deny` blokuje; `evidence` sprawdza obecność dowodu (np. ADR w zmianie, wpis audytu zależności), inaczej
  ostrzega. Skille `core-async-delegation` i `core-agent-security` odsyłają do polityki zamiast powtarzać listę.
- TDD: testy hooka na tabeli przypadków (polecenie → poziom → decyzja), test nadpisania z `.tf/config/`, test, że
  polityka nie rozluźnia `deny` z `settings.json`.
- Ryzyka: fałszywe trafienia blokujące pracę (rozpoznawanie „produkcji” po poleceniu jest zawodne — kontekst
  środowiska z konfiguracji projektu, nie zgadywanie); polityka jako jedyna obrona (zostaje `deny` w `settings.json`
  i piaskownica).
- **Triaż ryzyka zmian** (dopisane 2026-11-09 po przeglądzie „The Agentic Software Factory”, decyzja człowieka):
  przed PR deterministyczne drzewo decyzji na podstawie diffu, bez modelu:
  - zmiana dotyka uwierzytelniania i autoryzacji, logiki finansowej (płatności, rozliczenia, ceny), schematu bazy
    i migracji, sekretów albo konfiguracji wdrożenia → `confirm`: zatwierdza człowiek;
  - zmiana osłabia testy (usunięte lub zmienione asercje, pominięte testy) albo zmienia specyfikację lub kryteria
    akceptacji → `confirm` — tak agent „wygrywa” zielony build;
  - aktualizacja zależności z lockfile'em albo zmiana tylko dokumentacji, przy zielonych testach → `full`;
  - pozostałe → `evidence` (zielone testy, przegląd niezależnego recenzenta w osobnym kontekście).
  Reguły (wzorce ścieżek i treści) w `autonomy.triage:` z wartościami domyślnymi rdzenia i nadpisaniem w
  `.tf/config/`; wynik: etykieta PR (`risk: high|medium|low`) i lista „co musi zobaczyć człowiek” w opisie PR.
  Wykorzystuje `tdd_guard` (wykrywanie osłabienia testów) zamiast drugiej implementacji. TDD na tabeli diffów.
- Najpierw plan kroku do akceptacji (pliki, kolejność, testy), potem kod.

### B2. Mapa pokrycia generowana z katalogu (zamiast ręcznej macierzy wiedzy)
- Plik obszarów (domena → hasła) i skrypt liczący skille z trafieniem dla każdego hasła; raport w `.tf/reports/`
  albo w `docs/`, uruchamiany w CI jako informacja (bez blokowania).
- Nowe skille powstają tam, gdzie mapa pokazuje dziurę, a scenariusz ewaluacji potwierdza, że brak szkodzi.

### B3. Metryki skuteczności fabryki (dopisane 2026-11-09, decyzja człowieka)
Cel: mierzyć, czy fabryka i jej zmiany pomagają, zamiast oceniać „na odczucie” (badanie METR 2025: doświadczeni
programiści z AI byli wolniejsi, choć czuli się szybsi; DORA 2024: spadek stabilności dostaw przy większej
adopcji AI).
- Skrypt `tf metrics` (silnik, tylko biblioteka standardowa, dane z gita i — jeśli dostępne — z historii PR):
  - **odsetek revertów** (commity `revert` i PR cofnięte w ciągu N dni wobec wszystkich zmian) — główny wskaźnik
    jakości;
  - **mediana czasu cyklu** od pierwszego commita gałęzi (albo przydzielenia zadania) do merge'a;
  - **czas przeglądu na PR** (od otwarcia do merge'a, liczba rund poprawek), gdy dostępna jest historia PR;
  - pomocniczo: rozmiar PR, odsetek PR z czerwonym CI przed merge'em.
- Okres bazowy 4 tygodnie przed zmianą sposobu pracy; raport porównuje okno bieżące z bazowym i z pasmami
  kontrolnymi (`control_band.py`). Bez liczenia samej liczby PR — łatwo ją zawyżyć.
- Wynik w `.tf/reports/metrics.md` i JSON do dalszej analizy; TDD na sztucznym repo z historią.
- **Koszt przyjętej zmiany** (dopisane 2026-11-09 po artykule J. Wąsowskiego o koszcie przyjętej zmiany i odsetku
  poprawek specyfikacji, decyzja człowieka): (tokeny i narzędzia + czas człowieka na doprecyzowanie, przegląd
  i poprawki + porzucone próby) / zmiany przyjęte przez człowieka. „Przyjęta” = zmergowana i niecofnięta przez N dni
  (definicja zapisana w nagłówku raportu; zmiana definicji = nowa seria). Koszt tokenów z istniejących logów
  (`log_usage`, `cost_report`), zmiany z gita i historii PR; czas człowieka opcjonalnie, z etykietą „bez pracy
  ludzi”, gdy go brak. Porzucone próby zostają w liczniku.
- **Przyczyna poprawki**: przy każdym powrocie zadania do poprawki jedno pole o czterech wartościach — `luka-specyfikacji`
  (→ poprawić szablon wymagań), `blad-agenta` mimo jasnej specyfikacji (→ model, skill albo bramka),
  `zmiana-wymagan` (liczona, nie strata), `nieznana` (nie domyślna). Miejsce zapisu: opis PR lub komentarz recenzenta
  w ustalonym formacie oraz przebiegi Talosa (story → PR); liczymy defekty, nie czerwone testy. Raport: odsetek
  zadań z co najmniej jednym powrotem, z podziałem na przyczyny.

### B4. Ewaluacje skilli mierzą wkład skilla, nie tylko zaliczenie (dopisane 2026-11-09, decyzja człowieka)
Powód: w ewaluacjach A1 i A2a modele bez skilla przechodziły sprawdzenia treści w większości scenariuszy
(`pm-product-analytics` 3 z 4, `be-business-app-patterns` 5 z 5) — scenariusz zaliczony bez skilla nie dowodzi,
że skill coś wnosi. Do tego „testy przeszły” to nie „zmiana przyjęta” (zaliczenie części sprawdzeń ≠ zaliczenie
scenariusza).
- `skill_gate` przy ewaluacji z `--baseline`: ostrzeżenie dla scenariusza trigger, który bez skilla przechodzi
  sprawdzenia treści na wszystkich modelach — do zaostrzenia albo zastąpienia trudniejszym.
- Raport „wkład skilla na model” z istniejących wyników (`.jsonl` w `docs/evals/` i logach): dla każdego skilla
  i modelu odsetek scenariuszy zaliczonych ze skillem i bez; wejście do `core-cost-control` — czy przy silniejszym
  modelu skill warto ładować (eksperyment N. Jaina, martinfowler.com, 2026-10 [niezweryfikowane]: struktura wokół
  agenta pomogła tańszemu modelowi, a silniejszemu tylko podniosła koszt).
- Zamknięty zbiór (holdout): każde uruchomienie, które czyta lub ocenia scenariusze holdout, zapisuje wpis w dzienniku
  (data, skille, modele, kto uruchomił, wynik) — liczba zajrzeń jest jawna w raporcie, jak w protokole „audytowanego
  dostępu do zbioru testowego” (E. Eshratifar, „You Don't Need Jev”, 2026-10-20 [niezweryfikowane]).
- TDD na sztucznych wynikach ewaluacji; bez nowych płatnych przebiegów.
- **Plan kroku (2026-11-09):**
  1. testy (czerwone) w `core/tests/test_skill_evals.py`: `no_uplift` (scenariusz trigger zaliczony bez skilli na
     każdym modelu z przebiegiem bez skilli), `contribution` (skill × model: treść ze skillem, bez skilli, wkład),
     sekcje raportu, dziennik holdout (wpis przy uruchomieniu ze scenariuszami holdout, licznik wcześniejszych),
     `--contribution <plik.jsonl>` bez uruchamiania modelu; w `core/tests/test_skill_gate.py`: ostrzeżenia kroku 8
     z podsumowania (`paid_warnings`);
  2. kod w `core/tests/run_skill_evals.py` (funkcje, raport, opcja, dziennik
     `docs/evals/holdout-dostep.jsonl` w repo fabryki, `.tf/logs/evals/holdout-dostep.jsonl` w projekcie) i
     `core/factory/skill_gate.py` (`bez_wkladu` w podsumowaniu, ostrzeżenie — nie błąd);
  3. `workspace.py check --packs all`, `refs`, testy repo.

### Kolejność sekcji B
1. B1 z triażem ryzyka zmian (po sekcji A albo równolegle, jeśli człowiek zdecyduje).
2. B3 — wcześnie, żeby okres bazowy zebrać przed dużymi zmianami sposobu pracy.
3. B4 — przed kolejnymi skillami sekcji A, żeby ich ewaluacje mierzyły wkład.
4. B2.
