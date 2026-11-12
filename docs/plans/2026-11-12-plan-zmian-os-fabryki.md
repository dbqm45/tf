# Plan zmian: od obecnej fabryki do osi „zadanie → wdrożenie”

Data: 2026-11-12 (22 pozycje w tabeli; po korektach 4a i 4b — 26). Podstawa: stan `main` (rdzeń 9.17.0, tryb Talos 1.3.0) i dokument
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

Do kroków A–B: nic. Do kroku C: **D1** (pliki zadania w gicie czy poza) i **D5** (co z folderem po zamknięciu).
Do kroku E: **D2**, **D3**, **D12**. Reszta decyzji (D4, D6, D8–D11) może poczekać na wyniki pierwszych kroków.
