# Plan: `tf analyze` (modułowy przegląd projektu) i katalog `.tf/` na wyniki pracy fabryki

Stan: 2026-11-08, do akceptacji człowieka; kodu jeszcze nie ma. Źródła decyzji: rozmowa z człowiekiem 2026-11-08
(porównanie z dev-kitem, wizja Mai jako menedżerki zespołu, moduły analizy, katalog `.tf/`).

## Cel
Wejście fabryki do istniejącego kodu zaczyna się od przeglądu: `tf init` (mapa, stack, dziennik), potem
`tf analyze` — raporty z wymiarów (bezpieczeństwo, architektura, dostępność, prawo…) z listą działań do odhaczania,
które od razu stają się kolejką pracy dla zespołu agentów. Wymiary są modułami: nakładka może dodać własny bez zmian
w rdzeniu. Wszystkie wyniki pracy fabryki mają jedno miejsce: `.tf/`.

## 0. Zasada nadrzędna: fabryka nie zaśmieca projektu
Decyzja człowieka 2026-11-08: wszystko, co fabryka wnosi do projektu, ma być uporządkowane i zrozumiałe. W katalogu
głównym projektu fabryka zostawia tylko to, czego wymaga Claude Code, i jeden katalog `.tf/` na całą resztę.

Stan dziś (zainstalowany projekt, sprawdzone na `tools/workspace.py assemble --packs none`): w katalogu głównym
powstają `.claude/`, `CLAUDE.local.md` i `factory/` (skrypty fabryki, przewodnik, FAQ, CHANGELOG, licencja), a z
pracą także `docs/project/`. Cel:

| Element | Dziś | Docelowo | Dlaczego |
|---|---|---|---|
| skille, agenci, hooki, ustawienia | `.claude/` | `.claude/` | Claude Code czyta je tylko stamtąd |
| instrukcje projektu | `CLAUDE.local.md` w katalogu głównym | bez zmian albo `.claude/` — do sprawdzenia, które lokalizacje Claude Code wczytuje [niezweryfikowane] | plik instrukcji musi być tam, gdzie go szuka Claude Code |
| silnik fabryki (skrypty, przewodnik, FAQ, CHANGELOG, licencja) | `factory/` | `.tf/factory/` | to narzędzie, nie kod projektu |
| wyniki pracy (logi, cache, przebiegi, kopie, raporty, rejestr, punkty kontrolne) | `.claude/logs`, `.claude/cache`, `.claude/runs`, `docs/project/wip`, `*.factory-new` | `.tf/…` (sekcja 1) | jedno miejsce, jasna reguła dla gita |
| dokumentacja projektu (wymagania, decyzje, ADR, zmiany) | `docs/project/` | ścieżka z `.tf/config.yaml`, domyślnie `docs/project/` | to dokumentacja projektu i kontrakt z pdi |

Każdy katalog w `.tf/` ma krótki `README.md` (co tu jest, kto pisze, czy w gicie, czy można usunąć), a `tf init`
wypisuje mapę `.tf/`. `tf remove` usuwa fabrykę z projektu jednym ruchem, pytając tylko o wyniki do zachowania
(raporty, rejestr).

## 1. Katalog `.tf/` — granice
| Gdzie | Co | W gicie? |
|---|---|---|
| `.claude/` | to, co Claude Code musi tam mieć: skille, agenci, hooki, ustawienia | tak (bez logów i cache — te przechodzą do `.tf/`) |
| `docs/project/` | dokumentacja projektu: wymagania, decyzje, ADR, dziennik zmian `changes/CHG-n/` (kontrakt pdi 0.9.0) | tak |
| `.tf/` | wyniki pracy fabryki, które da się odtworzyć albo odświeżyć | według tabeli niżej |

```
.tf/
  factory/           # silnik fabryki (dziś factory/ w katalogu głównym projektu) — instaluje i aktualizuje tf
  config.yaml        # moduły analyze, budżety, adresy do testów w przeglądarce, ścieżka dziennika projektu
  reports/           # raporty tf analyze (git)
    README.md        # przegląd: werdykt modułów, liczba otwartych działań, data, commit
    security.md, architecture.md, accessibility.md, legal.md, …
  register/          # rejestr pracy: zgłoszenia, zadania, blokady, pytania, decyzje (git)
  wip/               # punkty kontrolne pracy w toku (git; dziś docs/project/wip/)
  runs/              # przebiegi wykonawcze (dziś .claude/runs/) — poza gitem
  logs/              # zużycie, podpowiedzi, stan bramki jakości, ewaluacje (dziś .claude/logs/) — poza gitem
  cache/             # odciski analiz, wyniki pośrednie (dziś .claude/cache/) — poza gitem
  backup/            # kopie z aktualizacji i usuwania nakładek (dziś .claude/factory-backup/, *.factory-new) — poza gitem
```
- `docs/project/` zostaje, bo to dokumentacja projektu i kontrakt z pdi i ci_for_sdlc. W `.tf/config.yaml` ścieżka
  dziennika jest ustawieniem (domyślnie `docs/project`); zmiana domyślnej lokalizacji tylko z nową wersją kontraktu
  pdi, osobną decyzją.
- `tf init` dopisuje do README projektu odnośnik do `.tf/reports/README.md` (katalog z kropką łatwo przeoczyć),
  a `.gitignore` dostaje `logs/`, `cache/`, `runs/`, `backup/` z `.tf/`.

## 2. Rdzeń `tf analyze` (core)
Polecenia: `tf init`, `tf analyze [--only m1,m2] [--since <commit>] [--budget USD] [--list]`.
Rdzeń robi rzeczy wspólne — żaden moduł ich nie implementuje sam:
1. **Wybór modułów:** jawnie (`--only`) albo po cechach repo (stack z `detect_stack.py`, obecność UI, danych
   osobowych, komponentu AI); `--list` pokazuje dostępne moduły i ich zastosowanie.
2. **Piętra:** 0 — skrypty bez modelu; 1 — tani model na miejscach wskazanych przez piętro 0; 2 — przeglądarka
   (Playwright, MCP przeglądarki) tam, gdzie moduł tego wymaga; 3 — weryfikacja ustaleń drugim agentem, który nie
   widzi rozumowania pierwszego. Budżet na moduł z twardym STOP; koszt w raporcie.
3. **Przyrostowość:** cache w `.tf/cache/` z odciskiem commita; `--since` bada tylko zmienione pliki.
4. **Wspólny format ustalenia:** `id` (odcisk: reguła + plik + znormalizowany fragment), moduł, waga
   (krytyczna/wysoka/średnia/niska), pewność, `plik:linia`, dowód, podstawa (norma, artykuł, reguła z datą wersji),
   sugestia działania.
5. **Deduplikacja i ranking:** sklejanie po `id`; w raporcie top N na moduł, pełna lista w pliku obok.
6. **Raport** (sekcja 4) i wpis każdego działania do rejestru (sekcja 5); `claims_check.py` i `grounding_check.py`
   bez błędów przed zapisem.
7. **Zakres w raporcie:** co zbadano, czego nie, które piętra pominięto i dlaczego — brak ustaleń w niesprawdzonej
   części nie jest wynikiem.

## 3. Kontrakt modułu analizy (wkład nakładki)
Moduł to katalog w nakładce (`packs/<nakładka>/analyzers/<nazwa>/`), dołączany przez `pack.yaml` jak skille:
- `analyzer.yaml`: nazwa, opis, warunek zastosowania, piętra (skrypty, skille dla modelu, potrzeba przeglądarki),
  pytania wejściowe (to, czego kod nie powie), szacunek kosztu, termin przeglądu treści (`przeglad`, jak w skillach);
- `scripts/` piętra 0 (deterministyczne, TDD);
- `fixtures/`: repozytorium z podłożonymi problemami i oczekiwanymi ustaleniami.

**Bramka modułu** (odpowiednik `skill_gate.py`): moduł wchodzi, gdy na swoim zestawie testowym znajduje podłożone
problemy (czułość) i nie przekracza progu fałszywych trafień (precyzja); progi w `analyzer.yaml`, wynik w rejestrze
bramek. Bez bramki nowy moduł jest generatorem szumu.

## 4. Raport `.tf/reports/<moduł>.md` i lista działań
```
# Bezpieczeństwo — raport tf analyze
Werdykt: DO POPRAWY · 2026-11-08 · commit abc1234 · zakres: … · koszt: … USD
## Stan obecny
## Ustalenia
## Rekomendowane działania
- [ ] SEC-3f2a — IDOR w GET /api/invoices/:id (src/routes/invoices.ts:14) — wysoka
  notatka człowieka (zostaje przy ponownej analizie)
## Historia analiz
```
Scalanie przy ponownej analizie po `id`:
- odhaczone, a problem nadal jest → zostaje odhaczone z adnotacją „analiza wciąż widzi problem”;
- nieodhaczone, a problem zniknął → adnotacja „wygląda na naprawione — potwierdź”;
- nowe ustalenia → na końcu listy; notatki człowieka i kolejność ręczna — bez zmian.
Lista działań jest widokiem rejestru (sekcja 5): odhaczenie w raporcie i zmiana statusu w rejestrze to ta sama
pozycja.

## 5. Rejestr pracy `.tf/register/`
Pozycje: zgłoszenie, zadanie, blokada (na co i od kiedy), pytanie (do kogo), decyzja (źródło) — ze statusem
(otwarte, w toku, zablokowane, czeka na człowieka, rozstrzygnięte) i odwołaniami (`id` ustalenia, CHG/TSK, PRB z pdi).
Piszą do niego persony i `tf analyze`; czyta i przydziela Maja (sekcja 8). Format plikowy (Markdown z nagłówkiem
albo JSONL + widok Markdown) do ustalenia w kroku 1 realizacji.

## 6. Moduły startowe
| Moduł | Nakładka | Piętro 0 (skrypty) | Piętro 1–2 (model, przeglądarka) | Skille |
|---|---|---|---|---|
| `security` | pack-it | sekrety, zależności z podatnościami, niebezpieczne API, nagłówki w konfiguracji | klasy z sec-web-vulnerabilities na wskazanych miejscach; w przeglądarce nagłówki, CSP, ciasteczka | sec-web-vulnerabilities, arch-threat-modeling, ops-supply-chain-security, sec-appsec-devsecops |
| `architecture` | pack-it | mapa importów, cykle, węzły centralne, sprzężenia | rekonstrukcja architektury, zgodność z dokumentacją w repo | eng-codebase-mapping, eng-project-reconstruction, arch-quality-attributes, ddd-connascence-analysis |
| `accessibility` | pack-ux | statyka szablonów (alt, etykiety, role, kontrast z tokenów — `tools/ui-deconstruct.py`) | Playwright + reguły WCAG (np. axe-core) na liście ścieżek; agent przez Playwright MCP / Chrome DevTools MCP: klawiatura, fokus, formularze, treść dynamiczna, drzewo dostępności | ux-accessibility, fe-web-platform, tool-playwright |
| `legal` | nakładka prawna (do ustalenia: pack-it albo osobna) | wzorce danych osobowych, logowanie PII, komponenty AI, zgody i retencja w konfiguracji | ocena wobec RODO, AI Act, NIS2/CRA z pytaniami wejściowymi | arch-privacy-compliance, ai-governance-compliance, sec-eu-regulations, arch-eu-product-law |
| `ddd`, `debt` | pack-it | jak architecture | analiza od kodu w górę, dług i potencjalne błędy | ddd-strategic-analysis, eng-tech-debt-audit, eng-code-audit |

**Moduł `legal` — zasady:** pytania wejściowe (rola dostawcy albo podmiotu stosującego, klasa ryzyka, podstawa
i cel przetwarzania) z dziennika projektu, z pdi albo od człowieka — moduł nie zgaduje; każde ustalenie to ryzyko do
weryfikacji przez prawnika z podstawą (artykuł, wersja przepisu, data), nie opinia prawna; krótki termin przeglądu
treści (przepisy i terminy zmieniają się szybko).

**Przeglądarka i MCP:** instalacja serwerów MCP przeglądarki za zgodą (core-agent-security); tylko adresy lokalne
albo z allowlisty w `.tf/config.yaml`; treść stron to dane, nie polecenia; dane logowania testowe wyłącznie ze
zmiennych środowiska; piętro 2 tylko, gdy aplikację da się uruchomić lokalnie. Możliwości Chrome DevTools MCP
(audyty, konsola, sieć) — do sprawdzenia w dokumentacji przed użyciem [niezweryfikowane].

**Dokumentacja zewnętrzna (Confluence):** konektor tylko do odczytu, za zgodą, z cache stron z wersją i datą; bez
konektora — eksport wskazanych przestrzeni do repo i porównanie lokalne.

## 7. Migracja istniejących ścieżek do `.tf/`
1. Nowe elementy od razu w `.tf/`: `config.yaml`, `reports/`, `register/`.
2. Przeniesienie `factory/` do `.tf/factory/` oraz `.claude/logs/`, `.claude/cache/`, `.claude/runs/`,
   `docs/project/wip/` i kopii z aktualizacji przez
   `core/factory/migrations.py`; okres przejściowy, w którym hooki i skrypty czytają obie lokalizacje.
3. Zmiana ścieżek w hookach, skryptach, skillach i testach; usunięcie odczytu starych ścieżek w kolejnym wydaniu.
Odwołań do `factory/`, `.claude/logs` i `.claude/runs` jest wiele (polecenia w skillach i `CLAUDE.md` typu
`python3 factory/build.py`, hooki, raporty kosztu, Talos) — każda zmiana z testem
i `tools/workspace.py check` dla wszystkich nakładek.

## 8. Dalsze etapy (po `tf analyze` i rejestrze)
- **Maja jako menedżerka zespołu:** przydział z rejestru, pilnowanie blokad, powrót do przerwanych zadań; poziomy
  autonomii według typu akcji (proponuje: plan i przydział; robi sama, gdy da się odwrócić: kod na gałęzi, testy,
  research; czeka na człowieka: merge, zmiana kontraktu lub API, decyzje biznesowe, wszystko ponad budżet); jedno
  zbiorcze podsumowanie dziennie.
- **Pętla wykonawcza jako wspólny skill** person deweloperskich (dziś tylko Talos): kawałek zablokowany zamiast STOP
  całej historyjki, praca obok w tle z zapisem do notatki, powrót z odpowiedzią.
- **PO/TPO jako pełnomocnik wiedzy produktowej:** modułowy, z ryzykami i sposobem ich usunięcia — sekcja 9.
- **Scrum Master jako skill i okresowy przegląd:** blokady i ich wiek, limity WIP, metryki przepływu, Definition of
  Done, retro (core-agent-retro) — bez stale działającego agenta.
- **Talos:** zostaje do czasu pomiaru `tools/flow_compare.py` (protokół `docs/evals/protokol-porownania-przeplywow.md`);
  wygaszenie jako osobnej persony dopiero po danych.

## 9. PO/TPO — modułowy pełnomocnik wiedzy produktowej
Decyzja człowieka 2026-11-08: PO/TPO ma być modułowe jak `tf analyze`, a plan ma wymienić ryzyka do usunięcia
i — gdzie się da — usuwać je projektem, nie regułą w prompcie.

### 9.1. Zmiana projektu wobec „persony PO z wiedzą”
Persona, która „zna produkt” (wiedza wczytana do kontekstu), zgaduje, gdy wiedzy brakuje, starzeje się po cichu
i jest podatna na treść źródeł. Dlatego PO to **usługa odpowiedzi z dowodów**, a nie nowa persona:
- wiedza leży w **banku dowodów** (format `ddd-discovery-intake`: cytat dosłowny, źródło, ranga, data, wersja),
  zbudowanym przez moduły źródeł;
- odpowiedź powstaje z pozycji banku wyszukanych dla pytania i przechodzi **walidator bez modelu**: każdy cytat musi
  dosłownie występować w źródle w cache, z datą nie starszą niż TTL źródła — inaczej odpowiedź nie wychodzi, a pytanie
  trafia do człowieka;
- z usługi korzystają istniejące persony i role (natalia, patrycja, lena, `product-manager`, Maja przy przydziale);
  osobna persona „PO” nie jest potrzebna, co najwyżej cienki profil roli (9.2).

### 9.2. Moduły (wkład nakładek, jak `analyzers/`)
Jeden wspólny kontrakt modułu w rdzeniu (`module.yaml` z polem `kind`: `analyzer` | `po-source` | `po-skill`),
jedna bramka i jeden rejestr bramek — PO nie dostaje osobnego mechanizmu.

| Rodzaj | Gdzie | Co zawiera | Przykłady |
|---|---|---|---|
| źródło wiedzy | `packs/<nakładka>/po-sources/<nazwa>/` | sygnały wykrycia w repo, sposób dostępu (konektor tylko do odczytu albo eksport), skrypt pobrania do cache, mapowanie na typy pozycji banku, ranga domyślna (normatywne / opisowe / nieformalne), TTL, `fixtures/` | `docs-project`, `pdi` (PRB, decyzje, metryki), `jira`, `confluence`, `github-issues`, `openapi`, `figma`, `metrics` (ShipScope) |
| umiejętność | `packs/<nakładka>/po-skills/<nazwa>/` | skill + kontrakt wejścia i wyjścia + zestaw ewaluacyjny | odpowiedź na pytanie, doprecyzowanie zgłoszenia (kryteria jako przykłady, poza zakresem), przegląd PR wobec kryteriów akceptacji, propozycja priorytetu (RICE, wynik zamiast funkcji) |
| profil roli | `packs/<nakładka>/po-profiles/<nazwa>.yaml` | zestaw umiejętności, wymagane i zalecane źródła, poziomy autonomii | `po` (pack-it), `tpo` = `po` + `openapi`, atrybuty jakości, fakty integracyjne; nakładki domenowe dokładają źródła (pack-ev: regulacje, słownik EV) |

Polecenia (rdzeń): `tf po setup [--profile po|tpo]` — wykrycie źródeł po sygnałach (klucze zgłoszeń w commitach
i gałęziach, adresy `*.atlassian.net`, Notion, Figma w README i `docs/`, specyfikacje OpenAPI, zainstalowany mode-pdi),
propozycja konektora dla każdego, instalacja za zgodą, krótki wywiad tylko o to, czego repo nie powie (gdzie są
wymagania, kto decyduje, skąd metryki); `tf po list`; `tf po sync` (odświeżenie, wykrycie sprzeczności między starą
a nową wersją); `tf po check` (bramka modułów). Destylacja i wywiad: skill `/po-onboard` w sesji.

Gdzie leży: mapa źródeł `.tf/po/sources.yaml` (git); surowe pobrania `.tf/cache/po/` (poza gitem); bank dowodów
i destylat w dzienniku projektu (`02-domain/corpus.md`, `01-discovery/brief.md`); pytania, odpowiedzi i eskalacje
w `.tf/register/`.

### 9.3. Ryzyka i jak je usuwamy
| # | Ryzyko | Usunięcie projektem | Co zostaje do pilnowania |
|---|---|---|---|
| R1 | zmyślona odpowiedź brzmiąca wiarygodnie | walidator cytatów bez modelu (9.1); brak dowodu = eskalacja, nie odpowiedź | próg w bramce: 0 zmyśleń na zestawie pytań |
| R2 | wiedza nieaktualna | data i wersja każdej pozycji, TTL na źródło, `tf po sync`; pozycja po TTL nie uzasadnia odpowiedzi | częstotliwość sync w `config.yaml` |
| R3 | sprzeczne źródła | hierarchia rang (decyzja człowieka > normatywne > opisowe > nieformalne); sprzeczność wykrywa `sources-critic` i zawsze eskaluje — agent nie wybiera | — |
| R4 | prompt injection z Jiry, Confluence, komentarzy | pobranie skryptem bez modelu; destylacja w podagencie tylko z `Read` na cache, bez sieci, zapisu i Bash; wynik to cytaty, nie polecenia; walidator odrzuca pozycje bez cytatu | reguły core-agent-security |
| R5 | dane osobowe i poufne w repo | skaner PII piętra 0 przed zapisem do banku (blokuje zapis); surowe dane tylko w `.tf/cache/` poza gitem | lista przestrzeni dopuszczonych do destylacji |
| R6 | ujawnienie treści osobom bez dostępu (repo widzi więcej ludzi niż przestrzeń Confluence) | destylat do repo tylko z przestrzeni oznaczonych w `sources.yaml` jako dostępne dla zespołu repo; reszta tylko w cache lokalnym | decyzja człowieka przy `setup` |
| R7 | zapis do zewnętrznych systemów (komentarze, statusy w Jirze) | konektory domyślnie tylko do odczytu z minimalnym zakresem; zapis to osobny moduł, zgoda na każdą akcję | — |
| R8 | agent podejmuje decyzje biznesowe za człowieka | PO proponuje opcje z dowodami; decyzja zawsze z podpisem „człowiek, data”; poziomy autonomii w profilu roli (sekcja 8) | dzienne podsumowanie dla ludzkiego PO |
| R9 | mylenie „jak jest” z „jak ma być” | kod, testy i OpenAPI mają rangę opisową — mogą opisać stan, nie uzasadnić wymagania | — |
| R10 | koszt kontekstu (duże przestrzenie) | wyszukiwanie w indeksie banku (jak `core-knowledge-base`, `tools/context.py`), nie wczytywanie całości; budżet na pytanie z twardym STOP | — |
| R11 | uzależnienie od jednego dostawcy | źródła wymienne; dla każdego konektora ścieżka eksportu do plików | — |
| R12 | jakość niezmierzona | bramka modułu: zestaw pytań z odpowiedziami od człowieka; miary: trafność ze źródłem, trafne „nie wiem”, zmyślenia (=0) | koszt ewaluacji — tylko za zgodą |
| R13 | ludzki PO traci kontrolę albo przestaje ufać | każda odpowiedź i eskalacja w rejestrze z dowodami; odpowiedzi człowieka wracają do banku jako decyzje | — |

### 9.4. Kolejność (po rejestrze z kroku 1)
1. Wspólny kontrakt `module.yaml` i bramka dla `po-source`; moduły `docs-project` i `pdi` (bez sieci).
2. Walidator cytatów, skaner PII, `tf po setup` (wykrywanie, mapa, wywiad) i umiejętność „odpowiedź na pytanie”
   z eskalacją do rejestru; zestaw pytań i pierwszy pomiar (za zgodą).
3. Moduły `jira`, `confluence` (konektor tylko do odczytu + eksport), `tf po sync`, `sources-critic` w pętli.
4. Umiejętności: doprecyzowanie zgłoszenia, przegląd PR wobec kryteriów, priorytety; profil `tpo` z `openapi`.

## Kolejność realizacji (każdy krok osobny PR, TDD, bramki)
1. `.tf/` (config, reports, register) + format ustalenia + rdzeń `tf analyze` z piętrem 0 i raportem ze scalaniem
   checkboxów.
2. Bramka modułów i moduły `security`, `architecture` (piętra 0–1).
3. `accessibility` z piętrem 2 (Playwright; MCP za zgodą) i `legal` z pytaniami wejściowymi.
4. Migracja istniejących ścieżek do `.tf/`, w tym `factory/` → `.tf/factory/` (sekcje 0 i 7).
5. Maja na rejestrze, pętla wykonawcza, SM jako skill (sekcja 8) — każdy osobno, po pomiarze.
6. PO/TPO według kolejności z sekcji 9.4.
Płatne przebiegi (piętra 1–3 na prawdziwych repozytoriach, pomiar przepływów) tylko za zgodą człowieka z budżetem.
