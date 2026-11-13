# Plan zmian: od obecnej fabryki do osi „zadanie → wdrożenie”

Data: 2026-11-12 (22 pozycje w tabeli; po korektach 4a, 4b, 4d, 4e i 4f — 30). Podstawa: stan `main` (rdzeń 9.17.0, tryb Talos 1.3.0) i dokument
`2026-11-12-os-fabryki-od-zadania-do-wdrozenia.md` (dalej „dokument osi”; numery sekcji i decyzji D1–D12 pochodzą
z niego). Status: propozycja; każda pozycja to osobny PR, kod metodą TDD.

## 1. Werdykt: ani kosmetyka, ani przebudowa

**To średnia zmiana o charakterze „spięcia”, nie przepisania.** Silnik zostaje; dochodzi warstwa, która łączy
istniejące części w jeden przebieg, oraz kilka nowych skryptów stanu. Dla użytkownika zmiana będzie duża (jedno
polecenie zamiast wyboru między personą, Talosem i pdi), dla kodu — umiarkowana.

Liczby z repo (2026-11-12):

| Obszar | Dziś | Co się z nim dzieje |
|---|---|---|
| hooki rdzenia | 18 plików, ok. 4,0 tys. linii | bez zmian w logice; 2–3 nowe małe hooki, jeden włączany na czas kawałka |
| silnik (`core/factory/`) | ok. 7,9 tys. linii | `tf.py` (316 linii) dostaje 3 polecenia; `config.yaml` — przypisanie model/effort na krok |
| Talos (skill, 4 skrypty, testy) | ok. 3,0 tys. linii | pętla zostaje; zmienia się miejsce zapisu i sposób eskalacji; `run_state.py` (420 linii) uogólniony |
| pdi (skrypty trybu) | ok. 3,3 tys. linii | bez zmian w kontrakcie |
| lint historyjek, przegląd gotowości, szablon hooka po edycji | ok. 1,3 tys. linii | użyte ponownie jako kroki i części `tf onboard` |
| skille | 20 w rdzeniu, 189 w nakładkach | treść bez zmian; przegląd pod kątem nadmiaru reguł (osobno, później) |
| testy rdzenia | 43 pliki, ok. 7,9 tys. linii | dochodzą testy nowych skryptów |

Szacunek nowego kodu [założenie, do weryfikacji po E1–E2]: 2,5–4 tys. linii skryptów i testów, czyli 10–15% obecnej
bazy skryptów fabryki. Dla porównania: w ostatnich dwóch tygodniach podobny rozmiar miały `tf analyze` z modułami.

Co decyduje, że to nie kosmetyka:
1. **Nowe pojęcie i nowy stan:** „zadanie” z własnym katalogiem, plikami etapów i dowodami (sekcja 5) — dziś nie
   istnieje poza przebiegiem Talosa.
2. **Zmiana publicznego układu:** katalog przebiegu `.tf/runs/talos/<data>-<slug>/` i klucz `tiers` są w
   `PUBLIC_API.md`. Przeniesienie trwałych plików do `docs/project/changes/<KEY>/` i rozdzielenie modelu od effortu
   to zmiany, które bez aliasów oznaczałyby wydanie MAJOR. Plan zakłada aliasy i okres przejściowy (MINOR).
3. **Kontrole włączone domyślnie:** `tf onboard` zmienia zachowanie w każdym projekcie (bramka zaczyna blokować).

Co decyduje, że to nie przebudowa: żaden hook, skill ani skrypt Talosa nie jest wyrzucany; pdi i persony działają
dalej; każdy etap można wydać osobno i zatrzymać się po nim.

## 2. Co zostaje bez zmian

Hooki bezpieczeństwa i TDD, `skill_gate`, `skill_audit`, ewaluacje skilli, `tf analyze`, `tf risk`, `tf metrics`,
instalator i aktualizator, persony i dyspozytorki, kontrakt pdi, dziennik projektu `docs/project/`, wszystkie skille
nakładek, pętla kawałka Talosa (test → kod → weryfikacja → skan → zakres → commit), skan bezpieczeństwa i karencja.

## 3. Zmiany według wielkości

Wielkość: **S** — do ok. 150 linii z testami, jeden PR; **M** — 150–600 linii; **L** — ponad 600 linii albo zmiana
kontraktu. Rodzaj: nowe / rozszerzenie / przeniesienie / treść.

| # | Zmiana | Rodzaj | Dotyka | Wielkość | Zgodność wstecz |
|---|---|---|---|---|---|
| 1 | `tf onboard`: raport gotowości, wykrycie poleceń, zapis `quality-gate.json`, hook po edycji, `verify.sh`, PR | nowe (składa istniejące: `readiness_check.py`, `detect_stack.py`, `post_edit_checks.py`) | `tf.py`, nowy `onboard.py`, szablony | M | tak (nowe polecenie) |
| 2 | komunikat „bramka wyłączona” w `tf doctor` i na starcie sesji | rozszerzenie | `tf.py`, `detect_stack.py` | S | tak |
| 3 | strona „Zacznij tutaj” i tabela wyboru w przewodniku | treść | `core/guide/PRZEWODNIK.md`, `GUIDE.md` Talosa | S | tak |
| 4 | katalog zadania i `task_state.py`: stan, nagłówki plików, skróty wejść, nieaktualność, dowody | nowe + uogólnienie `run_state.py` | rdzeń (nowy skrypt), testy | L | nowe; stare przebiegi czytane dalej |
| 5 | Talos pisze do nowego układu (trwałe w `docs/project/changes/<KEY>/`, robocze w `.tf/runs/<KEY>/`) | przeniesienie | `run_report.py`, `SKILL.md`, `PUBLIC_API.md`, `.gitignore`, 9 plików z odwołaniami do `.tf/runs` | M | alias starej ścieżki przez jedno wydanie MINOR; decyzja D1 |
| 6 | etap specyfikacji: `spec.md` (GWT, strażnicy, zachowane, otwarte pytania), lint jako bramka | rozszerzenie | `requirements_lint.py`, skill osi | M | tak |
| 7 | `trace_check.py`: kryterium → test → commit → dowód; tabela w PR | nowe | rdzeń, Talos | M | tak |
| 8 | ochrona specyfikacji i testów akceptacyjnych przed zapisem w trakcie realizacji | rozszerzenie | `guard_paths.py` | S | tak |
| 9 | jedno wejście `/tf`: rozpoznanie zadanie / pytanie / drobna zmiana przez dyspozytorkę, skill osi, dobór wagi z `tf risk`, tryby Plan / zwykły / Auto, punkty stałe | nowe (cienka warstwa nad Talosem i dyspozytorką) | nowy skill w rdzeniu, prompt `maja`, `risk_triage.py`, `pack.yaml` Talosa | L | `/talos-story-run` zostaje jako alias; decyzje D2, D3 |
| 10 | plik komunikatów zatrzymań w prostym języku + pytania przez narzędzie z opcjami | nowe | skill osi, test treści | S | tak |
| 11 | `work_events.py`: zdarzenia, reguła czekać / iść dalej, `parked.md` jako widok; kawałek zablokowany zamiast STOP | nowe + zmiana pętli | rdzeń, `SKILL.md` Talosa | L | zmiana zachowania Talosa za flagą do pomiaru |
| 12 | model i effort na krok; eskalacja: sprawdzalność → effort → model | rozszerzenie | `config.yaml` (`tiers`), `build.py`, skill osi | M | stare `tiers` czytane dalej; decyzje D10, D12 |
| 13 | przegląd z limitem rund, filtr szumu, etykiety ważne / drobne / zastane | rozszerzenie | agent `scope-reviewer`, skill osi | M | tak |
| 14 | podgląd: dashboard otwierany od razu przy każdym użyciu fabryki (jak dziś w Talosie), strona z `task.json` i zdarzeń, panel wszystkich tworzonych i zmienianych plików (zadanie, kod wg kawałka, robocze), lista „czeka na Ciebie”, `tf status` | rozszerzenie | szablon dashboardu, `task_state.py`, `tf.py` | M | tak |
| 15 | podgląd i pytania jako mod w oknie Claude Code | nowe, osobna wtyczka | nowy katalog poza silnikiem | M | opcjonalne; decyzja D9 |
| 16 | wejście z trackera skryptem (`ticket.md`), kwarantanna treści | nowe | moduł źródła (plan 2026-11-08 §9) | M | opcjonalne; decyzja D4 |
| 17 | karta operacyjna wdrożenia, pola PR „jak sprawdzono / ryzyko / jak cofnąć”, obserwacja wydania | nowe + treść | szablony, skill osi | M | tak |
| 18 | zamknięcie: ustalenie → kontrola, zapadki jakości, incydent → test recenzenta | rozszerzenie | `factory_feedback.py` (201 linii), CI projektu | M | tak |
| 19 | `tf work --once` (bez nadzoru, worktree, stany zajęcia, limit wydatku) | nowe | `tf.py`, nowy skrypt | L | opcjonalne |
| 20 | odcisk harnessu w logu, pasmo szumu w raportach ewaluacji, sprawdzenie nazw modeli | rozszerzenie | `log_usage.py`, `run_skill_evals.py`, CI | S–M | tak |
| 21 | przegląd `CLAUDE.md` i skilli pod kątem nadmiaru reguł; pięć kontroli w `tf doctor` | treść + rozszerzenie | `instructions_lint.py`, skille | M (rozłożone) | tak |
| 22 | flaga funkcji na historyjkę: domyślnie wyłączona, włączana tylko na teście po ukończeniu, inne środowiska za zgodą człowieka; testy w obu stanach; kontrola diffu konfiguracji flag | rozszerzenie (stopka `Flag:` i pole `flag` w Talosie już są) | skill osi, `task_state.py`, nowy mały skrypt kontroli, karta operacyjna w `tf onboard` | M | tak |

Podsumowanie: 4 zmiany duże (4, 9, 11, 19), 13 średnich, 5 małych. Dwie z dużych (11, 19) są opcjonalne na start.

## 4. Kolejność i zależności

| Krok | Pozycje | Wymaga decyzji | Efekt po wydaniu |
|---|---|---|---|
| A. Pomiar bazowy i start | E0: pomiar na repo testowym, test laika; 3 | — | wiemy, od czego mierzymy; nowy użytkownik ma jedną stronę |
| B. Kontrole od pierwszego dnia | 1, 2 | — | bramki działają bez ręcznej konfiguracji — największy zysk jakości najmniejszym kosztem |
| C. Jedno miejsce na zadanie i podgląd od startu | 4, 5, 14 (część: otwieranie od razu i panel plików) | D1, D5 | przebieg wznawia się z plików; dowody ukończenia; dashboard z plikami od pierwszej chwili |
| D. Specyfikacja, ślad i flagi | 6, 7, 8, 22 | — | Given/When/Then → testy, tabela w PR |
| E. Jedno polecenie | 9, 10, 12 | D2, D3, D12 | `/tf KEY` z trybami; fabryka sama dobiera wagę i model |
| F. Płynność i podgląd | 11, 13, 14 | — (15 po D9) | pytanie nie zatrzymuje całości; widać, co czeka na człowieka |
| G. Wejście i wyjście | 16, 17, 18 | D4, D6 | od numeru zadania do wdrożenia i zamknięcia |
| H. Bez nadzoru i higiena | 19, 20, 21 | D10, D11 | pilotaż na zadaniach niskiego ryzyka; powtórka pomiaru z A |

Kroki A i B nie zależą od żadnej decyzji i nie zmieniają publicznego układu — można je zrobić od razu. Krok C jest
punktem, od którego zmiana staje się „duża”: po nim cofnięcie kosztuje migrację plików.

## 4a. Korekta po przeglądzie dokumentacji Claude Code (2026-11-12)

Sekcja 18 dokumentu osi pokazuje, że część mechanizmów istnieje w Claude Code. Skutki dla tego planu:

| Pozycja | Było | Jest |
|---|---|---|
| 9 (jedno wejście, tryby) | L — własna obsługa trybów i zatrzymań | M — konfiguracja trybów Plan i Auto, reguł `ask`/`deny` i pytań z opcjami; własny pozostaje dobór wagi i spięcie z plikami zadania |
| 11 (zdarzenia, kawałek zablokowany) | L | M — stan „czeka na człowieka” i wstrzymanie przebiegu daje harness; `work_events.py` zapisuje decyzje i zależności kawałków |
| 12 (model i effort na krok) | M | M, prostsze — etap jako skill w osobnym kontekście z `model` i `effort` w nagłówku; do zmiany ostrzeżenie w `build.py` |
| 14 (podgląd) | M | M — dochodzi linia stanu z odświeżaniem; źródłem kosztu przestają być transkrypty |
| 19 (praca bez nadzoru) | L | M — sesje w tle i `claude agents --json` zamiast własnych stanów zajęcia, ze skryptem zapasowym |
| nowa 23 | — | S–M — hooki etapów w nagłówkach skilli i podagentów zamiast globalnych; reguły w `.claude/rules/` ze ścieżkami |
| nowa 24 | — | M — pomiar z telemetrii (model, effort, skill, cache) zamiast parsowania transkryptów |
| nowa 25 | — | S — poprawka reguły o efforcie w `CLAUDE.md` fabryki i w `core-cost-control` (za zgodą człowieka — to zmiana instrukcji) |

Po korekcie zostaje jedna zmiana duża (pozycja 4: katalog zadania i stan). Szacunek nowego kodu spada do
ok. 2–3 tys. linii [założenie]. Rośnie za to zależność od wersji Claude Code: plan wymaga zapisania minimalnej wersji
w `PUBLIC_API.md` i sprawdzania jej w `tf doctor`.

## 4b. Korekta po sprawdzeniu OKF v0.2 i OWASP ASI (2026-11-12)

Źródła otwarte bezpośrednio: specyfikacja Open Knowledge Format v0.2 (treść pliku z katalogu `okf/` repozytorium
GoogleCloudPlatform/knowledge-catalog, przekazana przez człowieka w rozmowie), ogłoszenie Google z 2026-06-12
(opisuje jeszcze v0.1) oraz ogłoszenie OWASP z 2025-12-09 z nazwami ASI01–ASI10. Pełny dokument OWASP (PDF) jest
za formularzem i nie został otwarty, więc przypisania poniżej opierają się na nazwach i jednozdaniowych opisach
z ogłoszenia [własne przypisanie, do przeglądu po lekturze PDF].

### Co bierzemy z OKF

Fabryka nie staje się paczką OKF. Bierzemy nazwy i reguły tam, gdzie plan i tak wymagał własnych pól — zamiast
wymyślać je od nowa.

| Co | Skąd (OKF v0.2) | Gdzie w planie |
|---|---|---|
| nagłówek plików zadania: `generated: { by, at }`, `verified: [{ by, at }]`, `status`, `stale_after` | §5.2, §5.4, §5.5 | pozycja 4 (nagłówki plików, nieaktualność) |
| `stale_after` jako konkretna chwila; plik jest nieaktualny, gdy `teraz >= stale_after` | §5.5 | pozycja 4 |
| poziom zaufania wyliczany, nie zapisywany: brak `verified` → niesprawdzone; sam automat → potwierdzone maszynowo; `human:<id>` → sprawdzone przez człowieka | §5.3 | pozycje 4 i 14 (podgląd pokazuje poziom) |
| zapis wykonawcy: `<narzędzie>/<wersja>`, `human:<id>`, `process:<id>` | §7 | pozycje 4, 11 (zdarzenia), 20 (odcisk harnessu) |
| stałe identyfikatory zamiast pozycji na liście (kryterium `AC-1`, źródło `id`), bo agent przepisuje pliki i numer pozycji się rozjeżdża | §5.1 | pozycje 6 i 7 (kryterium → test → commit) |
| `sources` w `ticket.md` i `spec.md`: skąd pochodzi treść zgłoszenia | §5.1 | pozycja 16 (wejście z trackera) |
| dowód jako pokwitowanie sprawdzane kodem bez modelu: wykonanie zwraca ustalone pola (polecenie, kod wyjścia, SHA, czas), a skrypt porównuje je z tym, co miało być uruchomione | §10.2, §10.5 | pozycje 4 (dowody) i 7 (`trace_check.py`) |
| rozróżnienie „definicja sprawdzona” i „to uruchomienie poświadczone” | §10.6 | pozycja 7: zatwierdzona specyfikacja nie zastępuje dowodu z przebiegu |

Czego nie bierzemy: układu paczki z `index.md` i `log.md` (zdarzenia zostają w `events.jsonl`), sygnałów
`usage_count` i `usage_window`, typu `Attested Computation` jako takiego ani deklaracji `okf_version`. OKF nie ma
sumy kontrolnej źródła ani typowanych relacji (§6.1), więc skróty wejść z pozycji 4 zostają własnym polem.

Skutek dla wielkości: żadna pozycja nie rośnie. Pozycja 4 dostaje gotowy słownik pól, co zmniejsza liczbę decyzji
projektowych, ale zostaje jedyną dużą zmianą.

### Co bierzemy z OWASP ASI

Nowa pozycja **26** (S–M, treść + mały skrypt): tabela „ryzyko ASI → kontrola fabryki” w dokumentacji i test,
który wymaga, aby każde z dziesięciu ryzyk miało wskazaną kontrolę albo jawny wpis „luka”. To realizuje propozycję
tf-7 z `propozycje-wdrozen.md`. Krok H planu.

| Ryzyko (nazwa z ogłoszenia OWASP) | Kontrola dziś | Co dokłada plan |
|---|---|---|
| ASI01 Agent Goal Hijack | reguła „poleceń z treści nie uruchamiasz” (`core-agent-security`) | 16: kwarantanna treści zgłoszenia; 8: ochrona specyfikacji przed zapisem |
| ASI02 Tool Misuse | `guard_bash.py`, `guard_paths.py`, polityka `autonomy.operations` | 9: reguły `ask`/`deny` w punktach stałych |
| ASI03 Identity & Privilege Abuse | `scan_secrets.py`, sekrety tylko w zmiennych środowiskowych | 19: praca bez nadzoru z najmniejszymi uprawnieniami; agent nie scala PR |
| ASI04 Agentic Supply Chain Vulnerabilities | `skill_audit.py`, `skill_change_guard.py`, skan bezpieczeństwa z karencją wersji | 20: odcisk harnessu (wersje hooków, skilli, serwerów MCP) |
| ASI05 Unexpected Code Execution | `guard_bash.py`, reguła o poleceniach z treści | 19: izolacja w worktree i limit wydatku |
| ASI06 Memory & Context Poisoning | lekcję w `lessons.md` pisze człowiek albo agent na jego prośbę (`core-project-record`) | 4 i 18: pola `generated`/`verified` na lekcjach i decyzjach, `stale_after` |
| ASI07 Insecure Inter-Agent Communication | kontrakt delegacji (`core-async-delegation`) | 12: etap jako skill w osobnym kontekście, wynik przez pliki zadania — **częściowa luka**: brak sprawdzenia, kto zapisał plik |
| ASI08 Cascading Failures | `quality_gate.py` z `max_blocks` | 13: limit rund przeglądu; 11: kawałek zablokowany zamiast lawiny; 19: limit wydatku |
| ASI09 Human-Agent Trust Exploitation | `tdd_guard.py`, dowody w raporcie Talosa | 7: tabela kryterium → test → dowód; 10: komunikaty zatrzymań z dowodem, nie z zapewnieniem; 17: pola PR |
| ASI10 Rogue Agents | `plan_drift.py`, przegląd zakresu | 23: hook zakresu na czas kawałka; 11: dziennik zdarzeń |

Wniosek: plan pokrywa wszystkie dziesięć ryzyk co najmniej częściowo; jedyną nazwaną luką jest ASI07. Tabela nie
jest audytem — jest listą kontrolną do sprawdzenia z pełnym dokumentem OWASP.

## 4c. Granice wobec Delivery Intelligence Suite (2026-11-12)

Podstawa: strona propozycji Suite z 2026-11-10 (sześć produktów i dwie usługi wspólne; fabryka to „DI Agent
Factory”, krok „Budowa”). Stan pozostałych produktów znany tylko z tej strony [niezweryfikowane w ich repozytoriach].

**Zasada:** fabryka powstaje raz, jako samodzielna. Nie ma osobnej wersji „pod Suite”. Jedynym stykiem jest
repozytorium projektu: fabryka zapisuje w nim pliki zadania, PR-y i stopkę `Flag:` w commitach, a produkty Suite to
czytają. Fabryka nie wywołuje żadnego z nich i działa bez nich.

### Co należy do fabryki, a co do pozostałych części

| Część Suite | Odpowiada za | Co zostaje w fabryce |
|---|---|---|
| DI Agent Factory (tf) | budowę: kawałki, TDD, bramki, przegląd, PR, pliki zadania, lokalny podgląd | całość pozycji 1–5, 7–10, 12–15, 19, 21, 23, 25, 26 |
| DI Definition | gotowość zgłoszenia, konflikty między źródłami, czytanie Jiry i Confluence | lint scenariuszy jako kontrola wejścia (6); czytanie zgłoszenia skryptem przy pracy samodzielnej (16) |
| DI Decision | bramki B1–B5, rejestr decyzji, konsola „czyja kolej” | pytanie w sesji i `decisions.md` jako zapis w repo (9–11); dashboard tylko jako lokalny widok zadań i plików (14) |
| DI Release Control | stan flagi na środowiskach, kolejność test → QA → PROD, audyt | flaga w kodzie, stopka `Flag:`, testy w obu stanach (22) |
| DI Release | co wdrożone i widoczne, rollback, metryki przepływu | pola PR „jak sprawdzono / ryzyko / jak cofnąć” (17), lekcje i zapadki jakości (18) |
| DI Assistant (planowany) | pytania o proces [założenie — strona tego nie precyzuje] | pytania o kod przez `/tf` (9) |
| DI Model Gateway, DI AI Registry (planowane) | zatwierdzone modele, koszt, dziennik agentów | dobór modelu i effortu na krok (12), odcisk harnessu i telemetria jako dane do oddania (20, 24) |

### Co robimy teraz ze względu na Suite

1. **D1 rozstrzygnięte: pliki zadania w gicie** (przyjęte 2026-11-12 razem z tą sekcją). DI Decision i DI Release
   czytają repozytorium, więc pliki poza gitem byłyby dla nich niewidoczne.
2. **Układ `docs/project/changes/<KEY>/` jest kontraktem.** Pozycje 4 i 5 dostają test zgodności z kontraktem pdi
   (obok istniejącego `tools/sync_contract.py check`); zmiana układu wymaga aliasu jak każda zmiana publicznego API.
3. **Etap 7 (wdrożenie) i dashboard zostają cienkie.** Fabryka nie buduje własnej obserwacji wydań ani konsoli
   procesu.

### Co odkładamy (adaptery)

Powstają dopiero wtedy, gdy istnieje produkt po drugiej stronie. Do tego czasu fabryka używa wersji minimalnej.

| Adapter | Wersja minimalna w fabryce | Produkt |
|---|---|---|
| prośba o bramkę zamiast pytania w sesji | pytanie z opcjami i wpis w `decisions.md` | DI Decision |
| uruchomienie fazy z zewnątrz | `tf work --once` (19) — to samo wejście posłuży Suite | DI Decision |
| ustawianie flagi na środowisku | plik konfiguracji flag i kontrola jego diffu (22) | DI Release Control |
| przyjęcie gotowej definicji | `ticket.md` pobrany skryptem albo wklejony przez człowieka (16) | DI Definition |
| eksport dziennika agenta | `events.jsonl` w katalogu zadania (11) | DI AI Registry |
| lista zatwierdzonych modeli | sprawdzenie nazw modeli w CI (20) | DI Model Gateway |
| macierz uprawnień | polityka `autonomy.operations` | DI AI Registry |

Skutek dla planu: liczba pozycji i ich wielkość się nie zmieniają. Zmienia się kolejność jednej: pozycja 19
przesuwa się z kroku H bliżej kroku E, jeśli Suite ma uruchamiać fazy w CI — do decyzji, gdy tor Suite będzie tego
potrzebował.

## 4d. Dwie pozycje z porównania z dev-kitem (2026-11-12)

Źródło: AI Playbook (szkic do przeglądu) opisujący dev-kit. Dev-kit ma dwie rzeczy, których plan nie miał.

| # | Zmiana | Rodzaj | Dotyka | Wielkość | Zgodność wstecz |
|---|---|---|---|---|---|
| 27 | próba na działającej aplikacji po ostatnim kawałku: uruchomienie, przejście głównego scenariusza z kryteriów, zrzut ekranu lub odpowiedź API jako dowód w `evidence/` | nowe (opcjonalny krok etapu 5) | skill osi, `tf onboard` (polecenie uruchomienia aplikacji), `task_state.py` | M | tak; krok pomijany, gdy projekt nie poda polecenia uruchomienia |
| 28 | personalizacja w trzech warstwach — konfiguracja, własne skille, własne nakładki — z jedną ścieżką tworzenia i sprawdzania | rozszerzenie (większość części istnieje) | `tf.py`, szablony, `PRZEWODNIK.md` | M | tak |

### Pozycja 28: co już jest, a czego brakuje

Zasada: zespół nie edytuje plików fabryki, tylko dokłada swoje obok. Dzięki temu aktualizacja fabryki nie gubi
zmian zespołu (plik fabryki zmieniony ręcznie przestaje dostawać aktualizacje — nowa wersja ląduje obok jako
`*.factory-new`).

| Warstwa | Co już jest | Czego brakuje |
|---|---|---|
| 1. Konfiguracja rdzenia | `.tf/config/config.yaml` (m.in. `tiers`, `autonomy`, `limits`), `.claude/factory-settings.json` (języki); aktualizacja ich nie rusza | jedna strona „co mogę ustawić” z listą kluczy i przykładami; `tf config show` pokazujący wartości i ich źródło |
| 2. Własny skill | szablon `core/factory/templates/SKILL.template.md`, zasady `core-skill-authoring` (najpierw scenariusze), bramka `skill_gate.py` z rejestrem projektu `.claude/skill-gate.json`, migracje nazw stosowane do skilli projektu | sposób rozszerzenia skilla fabryki bez jego edycji (do zaprojektowania: dopisek projektu wczytywany razem ze skillem). Korekta 2026-11-13: szkielet ze scenariuszami już istniał (`build.py new-skill`), a bramka łączy strukturę, scenariusze i audyt — dodane zostały tylko krótkie polecenia `tf new skill`, `tf skill check`, `tf skill audit` i `tf config show` |
| 3. Własna nakładka | generator `tools/workspace.py new-pack` i skill `tf-new-pack` — tylko w repozytorium fabryki; własne role, persony i cechy projektu mają pierwszeństwo przed nakładkami | to samo w projekcie: `tf new pack <id>`; opis, jak nakładkę zespołu współdzielić między repozytoriami [do sprawdzenia, jak instalator traktuje nakładkę spoza fabryki] |
| Sprawdzenie i poprawki | `skill_gate.py` (format, scenariusze), `skill_audit.py` (bezpieczeństwo), `run_skill_evals.py` (ewaluacja na modelu) | jedna ścieżka `tf skill check <nazwa>`: bramka → audyt → ewaluacja na modelu za zgodą na koszt → lista poprawek → ponowna bramka; wynik zapisany w rejestrze projektu |

Kolejność: warstwa 1 i `tf new skill` ze ścieżką sprawdzenia (krok B lub E), własne nakładki później (krok H).

## 4e. Dodatki z przeglądu katalogu fab1 (2026-11-13)

Źródło: `propozycje-wdrozen-2.md` (przegląd 70 PDF z katalogu fab1; plik spoza repozytorium, przekazany przez
człowieka). Autor przeglądu zastrzega, że żadnego artykułu nie czytał w całości i że to głównie wpisy blogowe —
traktujemy je jako hipotezy. Z pliku wzięte są tylko rzeczy dotyczące fabryki.

| Z pliku | Co robimy w planie | Wielkość |
|---|---|---|
| **tf-20: brak dowodu liczy się jako porażka** — gdy artefakt dowodu nie istnieje albo jest starszy niż ostatnia edycja, stan to „niezweryfikowane”, nie „zielone” | bez nowej pozycji: reguła wchodzi do pozycji 4 (`task_state.py`) i 7 (`trace_check.py`). Stan kawałka i zadania ma trzy wartości: zweryfikowane / niezweryfikowane / czerwone; bramka etapu przepuszcza tylko „zweryfikowane”; podgląd (14) pokazuje „niezweryfikowane” osobnym kolorem. Zgodne z regułą OKF z sekcji 4b (poziom zaufania wyliczany z dowodu) | wlicza się w 4 i 7 |
| **tf-19: wersjonowany harness z wycofaniem po degradacji** | nowa pozycja **29**: `tf doctor` i `tf metrics` ostrzegają, gdy odsetek revertów albo liczba blokad hooków po aktualizacji fabryki przekroczy próg, i podają gotowe polecenie powrotu do poprzedniej wersji (`tf update` ze źródłem `#vX.Y.Z` już to umożliwia). Korzysta z odcisku harnessu (20). Krok H | M |
| **mało blokujących kontroli i jawna reguła eskalacji** (3–5 kontroli; bramka, którą wszyscy obchodzą, jest gorsza niż jej brak) | bez nowej pozycji: doprecyzowanie pozycji 1. `tf onboard` włącza jako blokujące najwyżej pięć kontroli (testy, sekrety, lint, typy, skan zależności — tylko te, dla których wykrył polecenie), resztę jako ostrzeżenia; raport gotowości mówi, kiedy ma spojrzeć człowiek | wlicza się w 1 |

Nowa decyzja **D13** (do pozycji 29): czy fabryka ma wracać do poprzedniej wersji sama, czy tylko ostrzegać.
Rekomendacja: tylko ostrzegać. `metrics.py` liczy odsetek revertów z gita, a przy małej liczbie zmian ten wskaźnik
jest zbyt zaszumiony, żeby na jego podstawie automatycznie zmieniać instalację; samoczynna zmiana hooków i skilli
w trakcie pracy zespołu byłaby też trudna do wytłumaczenia laikowi.

Potwierdzenia bez działań (plik, sekcja 3):
- agent nie zaświadcza o własnej pracy — odpowiada pozycji 13 (przegląd w świeżym kontekście) i 7 (dowód ze skryptu);
- kontrakt zwrotny podagentów z dowodami i niepewnością — jest w `core-async-delegation`;
- zmiany promptów, narzędzi i harnessu przechodzą ewaluacje przed wdrożeniem — jest `flow-evals.yml`, pozycja 20
  dokłada pasmo szumu.

Plik odwołuje się do pozycji tf-14…tf-18 z nowszej wersji pliku głównego, której ta sesja nie widziała; nie są
tu uwzględnione.

## 4f. Doprecyzowania z materiału o harnessie produkcyjnym (2026-11-13)

Źródło: spis treści i diagramy kursu o harnessie agentów w produkcji (pętla, narzędzia, kontekst, pamięć,
wyszukiwanie), przekazane przez człowieka; sama treść kursu nie była czytana [niezweryfikowane]. Większość tematów
dostarcza Claude Code (pętla agenta, cache promptu, kompaktowanie) albo fabryka już ma (limit opisów i budżet listy
skilli, widoczność według stacku, podpowiedź skilla, dziennik projektu z TL;DR, wyszukiwanie w kodzie zamiast RAG).
Własnej pętli, własnego kompaktowania ani bazy wektorowej fabryka nie buduje.

| Co | Zmiana w planie | Wielkość |
|---|---|---|
| **Ograniczone wyjście skryptów: początek i koniec, pełny wynik w pliku** | nowa pozycja **30**: bramka jakości oddaje dziś agentowi tylko ostatnie 3000 znaków wyjścia (`TAIL` w `core/hooks/quality_gate.py`), więc przy długim logu ginie początek z pierwszym błędem. Bramka ma oddawać początek i koniec, a całość zapisywać do pliku w `.tf/logs/` ze ścieżką w komunikacie. Ta sama reguła dla skryptów fabryki, których wynik trafia do kontekstu. Krok C albo wcześniej — nie zależy od decyzji | S |
| **Indeks zadań** | doprecyzowanie pozycji 4: `task_state.py` utrzymuje jeden plik z wierszem na zadanie (klucz, tytuł, etap, stan, data), żeby agent nie przeglądał folderów zadań; folder czyta dopiero po wybraniu zadania. Archiwizacja z decyzji D5 usuwa wiersz z indeksu bieżącego | wlicza się w 4 |
| **Porządkowanie pamięci skryptem** | doprecyzowanie pozycji 18: wygaszanie po dacie (`stale_after` z sekcji 4b) i wykrywanie duplikatów w `lessons.md` robi skrypt bez modelu; model scala i przeredagowuje tylko to, co skrypt wskaże | wlicza się w 18 |
| **Stała część na początku briefu etapu** | doprecyzowanie pozycji 12: brief każdego etapu zaczyna się od części wspólnej (zasady, format wyniku), a treść zadania idzie po niej — kolejne etapy korzystają wtedy z cache promptu | wlicza się w 12 |

## 5. Ryzyka samej zmiany

| Ryzyko | Jak ograniczamy |
|---|---|
| złamanie publicznego API (ścieżki Talosa, `tiers`) | aliasy i odczyt starego układu przez jedno wydanie MINOR; wpis `Deprecated` w `CHANGELOG`; `migrations.py` przenosi stare przebiegi |
| oś gorsza od Talosa uruchamianego ręcznie | Talos zostaje jako alias; porównanie `flow_compare` przed wygaszeniem (za zgodą na koszt) |
| bramka włączona przez `tf onboard` blokuje zespół z czerwonymi testami | raport gotowości najpierw; bramka z `max_blocks` i jawnym wyłącznikiem lokalnym — jak dziś |
| rozrost instrukcji razem z osią (wbrew S6) | skill osi opisuje cel i punkty stałe, a kroki pilnują skrypty; limit długości w bramce skilla |
| dwa układy plików zadań w okresie przejściowym | jeden skrypt stanu czyta oba; nowy zapis tylko w nowym układzie |
| koszt pomiarów (ewaluacje, `flow_compare`) | tylko za zgodą człowieka; dziś wstrzymane |
| oparcie na funkcjach Claude Code w podglądzie badawczym (sesje w tle, hooki `agent`, zdalny przegląd) | każda ma zapas w postaci skryptu fabryki; funkcje eksperymentalne nie są warunkiem żadnej bramki |

## 6. Co musi zdecydować człowiek, żeby ruszyć

Do kroku C nic już nie brakuje: **D1** — pliki zadania w gicie (sekcja 4c); **D5** — folder zadania zostaje
w repozytorium, a po 90 dniach skrypt przenosi go do archiwum (decyzja człowieka z 2026-11-13).

Stan na 2026-11-13: kroki A i B są zrobione (#214–#219), pomiar bazowy i powtórka po poprawkach Talosa są
w `docs/evals/2026-11-13-pomiar-bazowy-e0.md` (#220, #221). Następny jest krok C.
Do kroku E: **D2**, **D3**, **D12**. Reszta decyzji (D4, D6, D8–D11, D13) może poczekać na wyniki pierwszych kroków.
