# Ewaluacje skilli — 2026-11-02 16:59

Przebiegów: 208 · koszt: $21.07 · zaliczone: 84/208

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| ai-evals | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.31 |
| ai-evals | haiku (bez skilli) | 0/10 | 0/0 | 6/10 | 0/10 | $0.84 |
| be-api-design | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.50 |
| be-api-design | haiku (bez skilli) | 0/10 | 0/0 | 8/10 | 0/10 | $0.63 |
| be-database | haiku | 8/8 | 0/0 | 7/8 | 7/8 | $1.02 |
| be-database | haiku (bez skilli) | 0/8 | 0/0 | 6/8 | 0/8 | $0.47 |
| core-agent-security | haiku | 6/8 | 0/0 | 6/8 | 6/8 | $1.15 |
| core-agent-security | haiku (bez skilli) | 0/8 | 0/0 | 5/8 | 0/8 | $0.45 |
| core-async-delegation | haiku | 8/8 | 0/0 | 8/8 | 8/8 | $1.08 |
| core-async-delegation | haiku (bez skilli) | 0/8 | 0/0 | 2/8 | 0/8 | $0.50 |
| core-delivery-lifecycle | haiku | 5/8 | 0/0 | 7/8 | 5/8 | $1.12 |
| core-delivery-lifecycle | haiku (bez skilli) | 0/8 | 0/0 | 2/8 | 0/8 | $0.54 |
| core-grounding | haiku | 6/8 | 0/0 | 6/8 | 6/8 | $1.00 |
| core-grounding | haiku (bez skilli) | 0/8 | 0/0 | 1/8 | 0/8 | $0.50 |
| ddd-tactical-design | haiku | 8/8 | 0/0 | 6/8 | 6/8 | $1.16 |
| ddd-tactical-design | haiku (bez skilli) | 0/8 | 0/0 | 3/8 | 0/8 | $0.68 |
| dom-ev-ocpp-16 | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.45 |
| dom-ev-ocpp-16 | haiku (bez skilli) | 0/10 | 0/0 | 10/10 | 0/10 | $0.52 |
| dom-ev-tariffs-pricing | haiku | 8/8 | 0/0 | 6/8 | 6/8 | $1.20 |
| dom-ev-tariffs-pricing | haiku (bez skilli) | 0/8 | 0/0 | 0/8 | 0/8 | $0.65 |
| eng-testing | haiku | 6/10 | 0/0 | 10/10 | 6/10 | $1.21 |
| eng-testing | haiku (bez skilli) | 0/10 | 0/0 | 10/10 | 0/10 | $0.54 |
| sec-llm-security | haiku | 7/8 | 0/0 | 5/8 | 4/8 | $1.10 |
| sec-llm-security | haiku (bez skilli) | 0/8 | 0/0 | 6/8 | 0/8 | $0.45 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | holdout | 45/56 (80%) | 46/56 | 92% | $8.22 | $0.183 | 3 |
| haiku | ze skillami | strojenie | 46/48 (96%) | 46/48 | 100% | $6.08 | $0.132 | 2 |
| haiku | bez skilli | holdout | 34/56 (61%) | — | 81% | $3.98 | $0.117 | 4 |
| haiku | bez skilli | strojenie | 25/48 (52%) | — | 80% | $2.80 | $0.112 | 5 |

## Luka strojenie − holdout

Zaliczone w całości ze skillami na zbiorze strojenia minus na holdoucie. Duża luka znaczy, że opisy i treść skilli dopasowały się do pytań, na których je stroimy. Przewaga = ze skillami minus bez skilli w tym samym zbiorze; różnica przewag nie zależy od trudności pytań. Zmianę skilla przyjmujemy, gdy poprawia strojenie i nie pogarsza holdoutu.

| Model | Strojenie | Holdout | Luka | Przewaga skilli: strojenie | Przewaga skilli: holdout |
|---|---|---|---|---|---|
| haiku | 96% | 80% | +15% | +44% | +20% |

## Niezaliczone

- `be-database` / masowy-update-wersja / haiku: niepożądane: częściow\w* (sukces|zapis)\w*.{0,120}(zatwierd|commit) — użyte skille: be-database
- `eng-testing` / gen-testing-2 / haiku: nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku: nie uruchomił się — użyte skille: core-git-workflow, core-async-delegation
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku: nie uruchomił się — użyte skille: core-async-delegation
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku: nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku: brak: typ\w* krok\w* | jawn\w+ (typ|krok) | step type | rodzaj\w* krok\w* — użyte skille: ddd-tactical-design, be-messaging-outbox
- `dom-ev-tariffs-pricing` / ho-tariffs-brak-elementu-domyslnego / haiku: brak: domyśln\w+ | default | fallback; brak: pierwsz\w+ (pasując|element) | first (matching|element) | każd\w+ wymiar\w* | osobno (dla|per) .{0,20}wymiar | per dimension | each dimension — użyte skille: dom-ev-tariffs-pricing
- `eng-testing` / ho-testing-od-razu-zielony / haiku: nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku: brak: LLM07 — użyte skille: sec-llm-security
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku: nie uruchomił się
- `dom-ev-tariffs-pricing` / kalkulator-strefa-i-cdr / haiku: niepożądane: okno .{0,30} w UTC — użyte skille: dom-ev-tariffs-pricing, dom-ev-cdr-settlement
- `eng-testing` / gen-testing-2 / haiku: nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku: nie uruchomił się — użyte skille: core-git-workflow, core-async-delegation
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku: nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku: nie uruchomił się — użyte skille: core-async-delegation
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku: nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku: brak: typ\w* krok\w* | jawn\w+ (typ|krok) | step type | rodzaj\w* krok\w* — użyte skille: ddd-tactical-design, be-messaging-outbox
- `eng-testing` / ho-testing-od-razu-zielony / haiku: nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku: brak: LLM07 — użyte skille: sec-llm-security
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku: brak: manipul\w+ | spreparow\w+ | wprowadz\w+ w błąd | mislead\w* | sfałszowa\w+ — użyte skille: sec-llm-security
- `ai-evals` / sedzia-llm-kalibracja / haiku (bez skilli): nie uruchomił się
- `ai-evals` / klasyfikator-decyzji-llm / haiku (bez skilli): nie uruchomił się
- `be-api-design` / idempotencja-platnosci / haiku (bez skilli): nie uruchomił się
- `be-api-design` / paginacja-kolekcji / haiku (bez skilli): nie uruchomił się
- `be-database` / zmiana-nazwy-kolumny / haiku (bez skilli): nie uruchomił się
- `be-database` / masowy-update-wersja / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / clickfix-base64 / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / gen-agent-security-4 / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / telefon-czy-sandbox / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / inwentarz-przebiegow-wylacznik / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / utrzymanie / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / refinement-i-miary-agentow / haiku (bez skilli): nie uruchomił się
- `core-grounding` / agent-zmysla-wersje / haiku (bez skilli): nie uruchomił się
- `core-grounding` / wynik-skryptu-to-twierdzenie / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / connascence-magiczne / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / polityka-zmienna-w-czasie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / stop-nieznany-transactionid / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / status-kabel-bez-autoryzacji / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / step-size-zmiana-elementu / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / kalkulator-strefa-i-cdr / haiku (bez skilli): nie uruchomił się
- `eng-testing` / gen-testing-2 / haiku (bez skilli): nie uruchomił się
- `eng-testing` / gen-testing-4 / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / sql-od-modelu-tylko-odczyt / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / gen-llm-security-1 / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-kontaminacja-fewshot / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-saturacja-zepsute-zadanie / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-ocena-sciezki / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-limit-ruchu-partnera / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-import-czesciowy / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-api-rownolegla-edycja / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-pula-polaczen / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-retencja-duzej-tabeli / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-noc-porazka-bramki / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-tura-konczy-sie-tekstem / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-dlugi-regulamin-notatka / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-czysta-decyzja / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-offline-rozliczenie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-tolerancyjna-walidacja / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-ponowiony-start / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-step-size-postoj / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-brak-elementu-domyslnego / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-akceptacyjne-warstwy / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-czesciowa-awaria / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-od-razu-zielony / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku (bez skilli): nie uruchomił się
- `ai-evals` / sedzia-llm-kalibracja / haiku (bez skilli): nie uruchomił się
- `ai-evals` / klasyfikator-decyzji-llm / haiku (bez skilli): nie uruchomił się
- `be-api-design` / idempotencja-platnosci / haiku (bez skilli): nie uruchomił się
- `be-api-design` / paginacja-kolekcji / haiku (bez skilli): nie uruchomił się
- `be-database` / zmiana-nazwy-kolumny / haiku (bez skilli): nie uruchomił się
- `be-database` / masowy-update-wersja / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / clickfix-base64 / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / gen-agent-security-4 / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / telefon-czy-sandbox / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / inwentarz-przebiegow-wylacznik / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / utrzymanie / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / refinement-i-miary-agentow / haiku (bez skilli): nie uruchomił się
- `core-grounding` / agent-zmysla-wersje / haiku (bez skilli): nie uruchomił się
- `core-grounding` / wynik-skryptu-to-twierdzenie / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / connascence-magiczne / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / polityka-zmienna-w-czasie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / stop-nieznany-transactionid / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / status-kabel-bez-autoryzacji / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / step-size-zmiana-elementu / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / kalkulator-strefa-i-cdr / haiku (bez skilli): nie uruchomił się
- `eng-testing` / gen-testing-2 / haiku (bez skilli): nie uruchomił się
- `eng-testing` / gen-testing-4 / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / sql-od-modelu-tylko-odczyt / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / gen-llm-security-1 / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-kontaminacja-fewshot / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-saturacja-zepsute-zadanie / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-ocena-sciezki / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-limit-ruchu-partnera / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-import-czesciowy / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-api-rownolegla-edycja / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-pula-polaczen / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-retencja-duzej-tabeli / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-noc-porazka-bramki / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-tura-konczy-sie-tekstem / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-dlugi-regulamin-notatka / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-czysta-decyzja / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-offline-rozliczenie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-tolerancyjna-walidacja / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-ponowiony-start / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-step-size-postoj / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-brak-elementu-domyslnego / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-akceptacyjne-warstwy / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-czesciowa-awaria / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-od-razu-zielony / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku (bez skilli): nie uruchomił się
