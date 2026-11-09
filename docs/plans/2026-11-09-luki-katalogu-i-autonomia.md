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

### A2. Panel administracyjny — nakładka `pack-admin` (pierwszy profil aplikacji)
Luki: tabele danych z filtrowaniem i sortowaniem po stronie serwera, eksport dużych zbiorów, operacje masowe (słabo);
command palette (1); soft delete (0); impersonacja z audytem (0); audit log jako funkcja produktu (4); ABAC (1).
- A2a. Plan nakładki (`tools/workspace.py new-pack admin`, `docs/new-pack.md`): wymagane nakładki (`pack-it`,
  `pack-ux`), prefiks, persona lub rola, macierz CI.
- A2b. Skill `admin-patterns`: model uprawnień (RBAC → ABAC, kiedy które), autoryzacja na serwerze (frontend nie jest
  granicą bezpieczeństwa), audit log (co, kto, kiedy, przed/po, odporność na manipulację, retencja), soft delete
  (kiedy tak, kiedy nie, RODO a „usunięte”), impersonacja (zgoda, znacznik w sesji, audyt, zakaz operacji
  wrażliwych), operacje masowe (podgląd, potwierdzenie, idempotencja, częściowe błędy, cofnięcie), potwierdzenia
  operacji nieodwracalnych.
- A2c. Skill `admin-data-tables` (jeśli A2b okaże się za duży): paginacja kursorowa, filtrowanie i sortowanie po
  stronie serwera, URL jako stan, wirtualizacja, eksport w tle (zadanie, plik, powiadomienie), dostępność tabel,
  command palette.
- A2d. Moduł `tf analyze` `admin-authz` (tier 0): endpointy i akcje zmieniające dane bez sprawdzenia uprawnień po
  stronie serwera; uprawnienie sprawdzane tylko w UI; usuwanie bez audytu. Fixtures z prawdziwymi i fałszywymi
  trafieniami, bramka `min_recall` / `max_false_positives` jak w `security`.

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

### Kolejność sekcji A
1. A1 i A2 (największa luka przy panelach administracyjnych; A2 zaczyna się od planu A2a do akceptacji).
2. A3 i A4 (rozszerzenia istniejących skilli).
3. A5 i A6.
4. A7, gdy jest potrzeba — moduł po module.

## Sekcja B — architektura agenta i autonomia

Pięć warstw z propozycji odpowiada fabryce: warstwy 1–4 to skille i nakładki, warstwa 5 to persony, hooki, `.tf/wip`
i bramki. Osobny projekt „standardu” nie jest potrzebny; profile aplikacji to nakładki (`pack-admin` jako pierwszy,
A2). Ręcznie spisaną macierz wiedzy (20–30 domen, 150–250 subdomen, L1–L4) zastępuje B2.

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
- Najpierw plan kroku do akceptacji (pliki, kolejność, testy), potem kod.

### B2. Mapa pokrycia generowana z katalogu (zamiast ręcznej macierzy wiedzy)
- Plik obszarów (domena → hasła) i skrypt liczący skille z trafieniem dla każdego hasła; raport w `.tf/reports/`
  albo w `docs/`, uruchamiany w CI jako informacja (bez blokowania).
- Nowe skille powstają tam, gdzie mapa pokazuje dziurę, a scenariusz ewaluacji potwierdza, że brak szkodzi.

### Kolejność sekcji B
1. B1 (po sekcji A albo równolegle, jeśli człowiek zdecyduje).
2. B2.
