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

#### A3 — plan realizacji (2026-11-10, decyzja człowieka: „tak”, po rekomendacji)
Pętla deweloperska jako część ścieżki B skilla (audyt) i nowa referencja `references/petla-deweloperska.md`; fakty
zbiera `scripts/readiness_check.py` (sekcja `dx`), ocena i pomiar czasu zostają przy agencie.
1. Testy skryptu (najpierw, czerwone) w `packs/pack-it/tests/test_readiness_check.py`:
   - repo z `Makefile` (`setup`, `test`), `compose.yaml` z Postgresem i healthcheckiem, skryptem `seed`
     i fikcyjnymi wartościami w `.env.example` → bez ustaleń DX, `dx.setup` i `dx.services` wypełnione, polecenie
     testów powiązanych (`vitest related`);
   - repo z `pg` i `ioredis` bez compose/devcontainera, bez polecenia startowego i z kluczem w `.env.example` →
     ustalenia: brak polecenia startowego (średnia), usługi bez środowiska lokalnego (średnia), sekret w
     `.env.example` (wysoka), brak danych startowych (niska);
   - repo „zdrowe” z istniejącego testu dostaje skrypt `dev` (nowy wymóg: jedno polecenie startowe).
2. Skrypt: polecenie startowe (`make`/`just`/Taskfile, skrypty `dev`/`start`/`setup`, sekcja uruchomienia w README),
   usługi z compose i ich healthchecki, devcontainer (informacja), dane startowe, wartości w `.env.example`
   wyglądające na prawdziwe klucze, polecenie testów powiązanych ze zmianą dla wykrytego runnera.
3. Scenariusze ewaluacji (przed treścią): `dx-wejscie-do-projektu` (nowa osoba potrzebuje dwóch dni) i
   `dx-testy-wymagaja-uslug` (agent nie uruchomi testów, bo potrzebują Postgresa i Redisa).
4. Treść: krok 6 w ścieżce B, referencja z miarą „od klonu do zielonych testów” (procedura pomiaru w czystym
   katalogu, cel i zapis w raporcie), checklista, `slowa`, `katalog`; bramka `skill_gate.py`.

### A4. Mapa artefaktów — `core-delivery-lifecycle` (`core`)
Luka: jedno miejsce „faza → artefakt → kto pisze → skill źródłowy”; brak ERD (0 trafień).
- Tabela artefaktów: PRD, SPEC, ARCHITECTURE, ADR, ERD, openapi, DESIGN_SYSTEM, ACCESSIBILITY, SECURITY,
  THREAT_MODEL, TEST_PLAN, DEPLOYMENT, RUNBOOK, CHANGELOG, README — w której fazie powstaje, która persona lub rola
  pisze, który skill prowadzi, kiedy artefakt jest zbędny (mały projekt).
- ERD: dopisać do `be-database` (diagram encji jako kod, np. Mermaid, z migracji).

#### A4 — plan realizacji (2026-11-10, decyzja człowieka: „tak”, po rekomendacji)
Mapa zamiast tabeli nazw z innych metodyk (PRD, SPEC…): fabryka ma już własne ścieżki w `docs/project/`, rozsiane po
~60 skillach. Sprawdzenie ich wykazało dwie niespójności: `03-architecture/` w arch-eu-product-law i `05-delivery/` w
ops-cloud-migration (pack-it) — katalogów nie ma w strukturze core-project-record.
1. Test (najpierw, czerwony) `tests/test_artifact_map.py` w repo fabryki:
   - numerowane katalogi `docs/project/NN-…/` we wszystkich skillach (core, packs, modes) należą do struktury
     z core-project-record;
   - każdy artefakt (plik) wymieniony w skillach pod numerowanym katalogiem jest w mapie; nazwy z datą, numerem
     kroku i `<…>` porównywane po normalizacji;
   - `be-database` opisuje ERD (`erDiagram`, `docs/project/04-architecture/erd.md`), a mapa go zawiera;
   - SKILL.md core-delivery-lifecycle odsyła do mapy.
2. Poprawki ścieżek: `04-architecture/<data>-mapa-prawna.md`, `05-plan/migration-plan.md`.
3. `core/skills/core-delivery-lifecycle/references/mapa-artefaktow.md`: tabela na fazę (artefakt, kto pisze, skill
   z nakładką, kto czyta, kiedy pominąć w małym projekcie) oraz artefakty spoza `docs/project/` (raporty
   `tf analyze`, `metrics.md`, triaż ryzyka w opisie PR, README, CHANGELOG, kontrakt API przy kodzie).
4. `be-database`: sekcja ERD — Mermaid `erDiagram` w `04-architecture/erd.md`, generowany lub sprawdzany względem
   migracji, aktualizowany w tym samym PR co migracja.
5. Scenariusz ewaluacji core-delivery-lifecycle `mapa-artefaktow` (przed treścią), bramka.

### A5. Ład danych — sekcja w `arch-privacy-compliance` (`pack-it`)
Luka: własność danych, klasyfikacja (public, internal, confidential, PII), katalog i pochodzenie danych są
rozproszone po `data-engineering` i skillach bezpieczeństwa; retencja i RODO są pokryte.
- Sekcja „ład danych”: właściciel zbioru, klasy i wymagania na klasę (szyfrowanie, dostęp, maskowanie, retencja),
  inwentarz danych osobowych, odwołanie do `data-engineering` (pochodzenie, kontrakty danych).

#### A5 razem z modułem `data-classification` (decyzja człowieka 2026-11-10)
Inwentarz danych osobowych z A5 nie powstaje ręcznie od zera: moduł `tf analyze` (tier 0, `pack-it`) daje jego
szkic i pilnuje, żeby nowe pola osobowe nie pojawiały się bez klasy. Potem A7 moduł po module.

Skill (`arch-privacy-compliance`):
1. Scenariusz ewaluacji `klasyfikacja-danych` (najpierw): pytanie o klasy danych, właściciela i inwentarz w
   istniejącym systemie; sprawdza właściciela zbioru, klasy, wymagania na klasę (szyfrowanie, dostęp, maskowanie,
   retencja) i inwentarz pól.
2. Treść: zasada „Ład danych” w SKILL.md (krótko) i `references/lad-danych.md` — właściciel zbioru, cztery klasy
   (publiczne, wewnętrzne, poufne, dane osobowe; szczególne kategorie z art. 9 osobno) z tabelą wymagań na klasę,
   format inwentarza (`docs/project/04-architecture/data-inventory.md`: tabela, pole, klasa, cel, retencja,
   właściciel, gdzie jeszcze leży), oznaczanie klasy w kodzie (komentarz lub adnotacja przy polu), odwołanie do
   `data-engineering` (pochodzenie, kontrakty danych) i do modułu `data-classification`.
3. `katalog`, `slowa`, checklista; bramka `skill_gate.py`. Płatna ewaluacja tylko za zgodą.

Moduł `packs/pack-it/analyzers/data-classification/` (TDD: najpierw zestawy testowe i wpis w
`tests/test_analyzers.py`, uruchomienie na czerwono, potem skrypt):
- `pii-field-unclassified` (średnia): pole o nazwie typowej dla danych osobowych (e-mail, telefon, PESEL, IBAN, data
  urodzenia, imię i nazwisko, adres, IP, dokument tożsamości, zdrowie; nazwy angielskie i polskie, camelCase
  i snake_case) w migracji SQL, `schema.prisma`, modelu Django/SQLAlchemy, encji TypeORM lub JPA — bez znacznika
  klasy przy polu (komentarz `pii`, `confidential`, `klasa:` itp. w tej samej lub dwóch poprzednich liniach) i bez
  wpisu w inwentarzu (`docs/**/data-inventory*.md`, `docs/**/privacy.md`);
- `pii-in-logs` (wysoka): wywołanie loggera, `console.*` lub `print` z identyfikatorem osobowym w argumentach
  (poza samymi napisami; interpolacje `${…}` i f-stringi się liczą);
- `pii-to-analytics` (wysoka): wywołanie narzędzia analityki (`analytics.track`, `posthog.capture`,
  `mixpanel.track`, `gtag`, `segment`…) z identyfikatorem osobowym.
- Poza zakresem tier 0 (za dużo szumu): dane osobowe w odpowiedziach API — do piętra z modelem.
- Fixtures `podlozone` (każda reguła i każdy format) i `czyste` (znacznik klasy, wpis w inwentarzu, pola podobne,
  ale nie osobowe jak `email_verified`, `is_mobile`; sam napis w logu; skrót identyfikatora w analityce; testy
  pomijane). Bramka: recall 1.0, 0 fałszywych trafień.
- Przewodnik (tabela modułów) i CHANGELOG przez commit.

### A6. Biblioteki formularzy — referencja w `fw-react` (`pack-it`)
Luka: React Hook Form (0 trafień), walidacja (Zod) jest. Referencja: formularz z walidacją schematem współdzielonym
z serwerem, błędy pól i formularza, dostępność, formularze wielokrokowe.

### A7. Kolejne moduły `tf analyze` (tier 0)
Obecnie `security` i `architecture` (`pack-it`). Kandydaci, każdy jako osobny krok z fixtures i bramką:
- `accessibility` (odłożony krok 3 planu `2026-11-08-tf-analyze-i-katalog-tf.md`), `pack-ux`;
- `tech-debt` (TODO/FIXME z wiekiem z gita, martwy kod, przestarzałe zależności), `pack-it`;
- `i18n` (zahardkodowane teksty UI, formatowanie dat i kwot bez `Intl`), `pack-it`;
- `observability` (brak health checków, logi nieustrukturyzowane, brak identyfikatora korelacji), `pack-it`.

#### A7 — reguły modułów (plan realizacji 2026-11-10, decyzja człowieka: „domknij analyzer”)
Każdy moduł: najpierw zestawy `podlozone`/`czyste` i wpis w teście nakładki (czerwony), potem skrypt; bramka recall
1.0 i 0 fałszywych trafień; sprawdzenie szumu na prawdziwym kodzie (repozytoria fabryki i publiczne aplikacje
przykładowe, tylko odczyt). Tylko piętro 0 — reguły, które da się sprawdzić bez modelu i bez sieci.

`accessibility` (`pack-ux`, test `packs/pack-ux/tests/test_analyzers_ux.py`; HTML, JSX/TSX, Vue, Svelte, szablony
Angulara; skaner tagów z obsługą `{…}` i cudzysłowów, element ze spreadem `{...props}` pomijany):
- `img-without-alt` — `<img>` bez `alt` (puste `alt=""` dla grafiki dekoracyjnej jest w porządku), WCAG 1.1.1;
- `control-without-name` — `<button>` lub `<a>` bez tekstu (np. sama ikona) i bez `aria-label`,
  `aria-labelledby`, `title`, WCAG 4.1.2;
- `input-without-label` — `input` (poza hidden/submit/button/reset/image), `select`, `textarea` bez etykiety
  (`<label for>`/`htmlFor`, otaczający `<label>`, `aria-label`, `aria-labelledby`); placeholder nie jest etykietą,
  WCAG 1.3.1 i 3.3.2;
- `click-without-keyboard` — `div`/`span` z obsługą kliknięcia bez `role` i bez obsługi klawiatury lub `tabindex`,
  WCAG 2.1.1;
- `positive-tabindex` — `tabindex` > 0, WCAG 2.4.3;
- `html-without-lang` — `<html>` bez `lang`, WCAG 3.1.1.
Poza piętrem 0: kontrast, fokus, treść dynamiczna (Playwright, później).

`tech-debt` (`pack-it`):
- `marker-without-ticket` — TODO/FIXME/HACK/XXX w komentarzu bez odwołania do zgłoszenia (`#123`, `ABC-123`, URL);
  przy repozytorium git wiek z `git blame` w dowodzie, a starsze niż 180 dni mają wagę średnią;
- `skipped-test` — pominięty test (`it.skip`, `describe.skip`, `xit`, `test.skip`, `@pytest.mark.skip`,
  `@unittest.skip`, `@Disabled`, `@Ignore`) bez powodu; tylko na początku linii (lekcja z triażu ryzyka);
- `suppressed-check` — `@ts-ignore`, `eslint-disable` bez ` -- powód`, gołe `# noqa` i `# type: ignore` bez kodu;
- `large-file` — plik kodu powyżej 1000 linii (bez wygenerowanych i zminifikowanych).
Poza piętrem 0: martwy kod (wymaga grafu wywołań), przestarzałe zależności (wymaga sieci).

`observability` (`pack-it`; dotyczy plików usługi HTTP — Express, Fastify, Koa, NestJS, FastAPI, Flask, Django,
Spring Boot, route handlers Next.js):
- `no-health-endpoint` — usługa bez trasy `health`/`healthz`/`livez`/`readyz`/`ready`/`ping` ani Actuatora;
- `print-instead-of-logger` — `console.log`/`print` w pliku usługi;
- `swallowed-error` — pusty `catch` albo `except …: pass` (błąd znika bez logu i bez ponowienia);
- `no-correlation-id` — usługa z logowaniem bez identyfikatora żądania lub śledzenia (`x-request-id`,
  `correlation`, `traceparent`, OpenTelemetry).

`i18n` (`pack-it`; tylko w projekcie, który już używa biblioteki tłumaczeń — i18next, react-intl, next-intl,
vue-i18n, ngx-translate, `@angular/localize`, Lingui — bo wtedy tekst poza nią jest błędem, a nie decyzją):
- `hardcoded-ui-text` — tekst w JSX/szablonie i w atrybutach `placeholder`, `title`, `aria-label`, `alt` poza
  funkcją tłumaczącą;
- `locale-less-format` — `toLocaleDateString()`/`toLocaleString()`/`toLocaleTimeString()` bez locale; tylko
  z biblioteką tłumaczeń albo SSR (w zwykłej SPA locale przeglądarki to zwykle właściwy wybór — wniosek ze
  sprawdzenia na prawdziwym kodzie);
- `money-without-intl` — w komponencie UI kwota z `toFixed` sklejona z symbolem waluty (`zł`, `PLN`, `€`, `$`)
  zamiast `Intl.NumberFormat` (koszt w logu serwera to nie interfejs).

Zmiany po sprawdzeniu na prawdziwym kodzie (realizacja 2026-11-10): `swallowed-error` w Pythonie i Javie tylko dla
szerokiego wyjątku (wąski, nazwany wyjątek z `pass` to idiom); `input-without-label` uznaje komponent z `label`
(`<Field label="…">`), a `control-without-name` treść z `<ng-content>`/`<slot>`; `tech-debt` pomija napisy
wieloliniowe i rozpoznaje plik wygenerowany po typowych nagłówkach.

### A8. Pytanie o brakującą informację — `ai-agents` (`pack-it`, dopisane 2026-11-09, decyzja człowieka)
Luka: `ai-agents` opisuje zatwierdzanie akcji przez człowieka, ale nie pauzę z pytaniem o brakującą informację
(artykuł R. Gite, „Six Agent Harness Techniques That Actually Worked for Me”, 2026-11-02). Zakres: agent najpierw
szuka informacji narzędziami i w kontekście; dopiero brak, którego nie da się uzupełnić, kończy się konkretnym
pytaniem; stan przebiegu zachowany i wznowienie od miejsca przerwania; bez pytań, gdy odpowiedź jest dostępna.
Nowy scenariusz ewaluacji (agent ma zapytać zamiast zgadywać) i sąsiad, w którym pytać nie należy.

#### A8 — plan realizacji (2026-11-10, decyzja człowieka: „tak”; bez płatnych ewaluacji — limit tygodniowy)
1. Scenariusze (najpierw): `agent-zgaduje-zamiast-pytac` (agent zamówień zgaduje brakujące dane i robi błędy)
   i `agent-pyta-o-dostepne-dane` (agent zasypuje użytkownika pytaniami o rzeczy, które ma w CRM).
2. `references/pytanie-o-brakujace-dane.md`: najpierw narzędzia i kontekst (z listą sprawdzonych miejsc); pytanie
   tylko o decyzję człowieka albo brak nie do uzupełnienia; tanie i odwracalne → wartość domyślna z zapisanym
   założeniem; forma pytania (jedno, z opcjami, rekomendacją, skutkiem i wartością domyślną); pauza z punktem
   kontrolnym i wznowienie od niego (LangGraph `interrupt` — API sprawdzone w paczce); antywzorce; miary i
   ewaluacja (przypadki „trzeba zapytać” i „nie trzeba”).
3. SKILL.md krok 7: odnośnik; `slowa`; bramka bez modelu. Płatna ewaluacja po odnowieniu limitu.

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

- **Plan kroku (2026-11-10, do akceptacji człowieka):**
  Stan: `core/hooks/guard_bash.py` już pyta (ASK) o zależności, polecenia z `prod`, `DROP`/`TRUNCATE`, `terraform
  apply`, `kubectl`, publikację, `git push`, i blokuje (DENY) m.in. `rm -rf /`, `push --force`, `terraform destroy` —
  wzorce wpisane w kod, bez nazwanych typów operacji i bez ustawień projektu. Triażu diffu nie ma.
  - **B1a — polityka `autonomy:`** w `.tf/factory/config.yaml` (wartości domyślne) z nadpisaniem w
    `.tf/config/config.yaml`: nazwane typy operacji (`dependency_add`, `prod_command`, `destructive_sql`,
    `infra_change`, `publish`, `git_push`, `persistence`, `data_upload`) → poziom `confirm` (ASK) albo `deny`.
    `guard_bash` czyta poziom z polityki zamiast stałej listy; **projekt może tylko zaostrzać** (`confirm` → `deny`),
    rozluźnienie poniżej wartości domyślnej jest ignorowane z ostrzeżeniem; lista DENY rdzenia zostaje stała.
    Testy: tabela polecenie → typ → decyzja, nadpisanie z `.tf/config/`, próba rozluźnienia = bez skutku,
    istniejące testy hooka bez zmian.
  - **B1b — triaż ryzyka zmian** `.tf/factory/risk_triage.py` (i `tf risk`): diff `base...HEAD` → poziom
    `high` / `medium` / `low` i lista „co musi zobaczyć człowiek” (z powodem i plikiem). Reguły domyślne
    (ścieżki i treść diffu) w `autonomy.triage`, nadpisanie w `.tf/config/`:
    - `high`: uwierzytelnianie i uprawnienia, płatności i rozliczenia, migracje i schemat bazy, sekrety
      i konfiguracja wdrożenia (CI, IaC, Dockerfile), osłabione testy (usunięte lub zmienione asercje, `skip`,
      usunięte pliki testów) albo zmienione kryteria akceptacji i specyfikacje;
    - `low`: tylko dokumentacja albo tylko manifest i lockfile zależności (przy zielonych testach);
    - `medium`: reszta — dowód: zielone testy i przegląd niezależnego recenzenta.
    Wynik jako sekcja opisu PR (Talos dopisuje ją przy otwarciu PR) i JSON; **doradczy** — nie blokuje merge'a,
    mówi, co człowiek musi przejrzeć. Testy na sztucznych repo z diffami każdej klasy.
  - Kolejność: B1a i B1b jako osobne PR (B1b najpierw — nie dotyka hooków bezpieczeństwa).
  - Decyzje do akceptacji: (D1) polityka tylko zaostrza, (D2) triaż doradczy, bez blokady merge'a,
    (D3) poziom `evidence` w B1 tylko jako punkt na liście triażu (np. „zmiana architektury bez ADR”), bez
    egzekwowania w hooku.

### B2. Mapa pokrycia generowana z katalogu (zamiast ręcznej macierzy wiedzy)
- Plik obszarów (domena → hasła) i skrypt liczący skille z trafieniem dla każdego hasła; raport w `.tf/reports/`
  albo w `docs/`, uruchamiany w CI jako informacja (bez blokowania).
- Nowe skille powstają tam, gdzie mapa pokazuje dziurę, a scenariusz ewaluacji potwierdza, że brak szkodzi.

#### B2 — plan realizacji (2026-11-10, decyzja człowieka: „ruszaj z B2, a potem A6”)
1. Test (najpierw) `tests/test_coverage_map.py`: na sztucznym drzewie skilli (core, pack, mode) hasło trafia
   w `description`, `katalog` i `slowa`, wielkość liter bez znaczenia; hasło bez trafień to dziura, z jednym —
   „cienkie”; raport Markdown z tabelą na obszar; kod wyjścia 0 także przy dziurach (informacja); na prawdziwym
   repo każdy obszar z pliku ma hasła, a raport powstaje.
2. `tools/coverage_areas.json` (obszar → hasła, rdzenie wyrazów zamiast pełnych form) i `tools/coverage_map.py`
   (`--summary` do CI, `--out <plik>` z pełnym raportem, `--areas`, `--root`). Dopasowanie po metadanych, które
   widzi trasowanie (opis, katalog, słowa), nie po treści skilla.
3. Krok w CI (`factory-checks.yml`, job repo) z `--summary` — informacja, bez blokowania. Raport nie jest
   commitowany (starzałby się); generuje się na żądanie.

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

- **Plan kroku (2026-11-10):**
  1. testy (czerwone) `core/tests/test_metrics.py` na sztucznym repo git z datami commitów: zmiany na głównej linii
     (`--first-parent`, bez `chore(release)`), reverty (`Revert "…"` / `This reverts commit <sha>`) w oknie N dni,
     zmiany „w toku” (młodsze niż N dni) poza licznikiem przyjętych, trailer `Rework-Cause:` (4 wartości, inne →
     `nieznana`), koszt z `.tf/logs/usage.jsonl` (cennik jak w `cost_report`), dane PR z `gh` (atrapa w PATH; bez
     `gh` — tylko git), okno bieżące i bazowe, raport `.tf/reports/metrics.md` i `metrics.json`, polecenie `tf metrics`;
  2. kod: `core/factory/metrics.py` (tylko biblioteka standardowa), dyspozycja w `core/factory/tf.py`;
  3. `workspace.py check --packs all` i `--packs none`, `refs`, testy repo.
  Pole przyczyny poprawki w MVP: trailer `Rework-Cause:` w commicie poprawki (Talos i ręczne poprawki); opis PR —
  później. Czas człowieka nie jest mierzony — raport oznacza koszt jako „bez pracy ludzi”.

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
