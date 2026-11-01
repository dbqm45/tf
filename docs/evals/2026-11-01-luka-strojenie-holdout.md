# Ewaluacje skilli — 2026-11-01 17:16

Przebiegów: 208 · koszt: $20.06 · zaliczone: 84/208

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| ai-evals | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.31 |
| ai-evals | haiku (bez skilli) | 0/10 | 0/0 | 6/10 | 0/10 | $0.68 |
| be-api-design | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.47 |
| be-api-design | haiku (bez skilli) | 0/10 | 0/0 | 8/10 | 0/10 | $0.66 |
| be-database | haiku | 8/8 | 0/0 | 8/8 | 8/8 | $0.93 |
| be-database | haiku (bez skilli) | 0/8 | 0/0 | 4/8 | 0/8 | $0.49 |
| core-agent-security | haiku | 5/8 | 0/0 | 6/8 | 5/8 | $1.08 |
| core-agent-security | haiku (bez skilli) | 0/8 | 0/0 | 8/8 | 0/8 | $0.40 |
| core-async-delegation | haiku | 8/8 | 0/0 | 8/8 | 8/8 | $1.01 |
| core-async-delegation | haiku (bez skilli) | 0/8 | 0/0 | 1/8 | 0/8 | $0.49 |
| core-delivery-lifecycle | haiku | 4/8 | 0/0 | 5/8 | 3/8 | $1.11 |
| core-delivery-lifecycle | haiku (bez skilli) | 0/8 | 0/0 | 4/8 | 0/8 | $0.65 |
| core-grounding | haiku | 5/8 | 0/0 | 5/8 | 5/8 | $0.99 |
| core-grounding | haiku (bez skilli) | 0/8 | 0/0 | 2/8 | 0/8 | $0.42 |
| ddd-tactical-design | haiku | 8/8 | 0/0 | 7/8 | 7/8 | $1.04 |
| ddd-tactical-design | haiku (bez skilli) | 0/8 | 0/0 | 4/8 | 0/8 | $0.56 |
| dom-ev-ocpp-16 | haiku | 10/10 | 0/0 | 10/10 | 10/10 | $1.37 |
| dom-ev-ocpp-16 | haiku (bez skilli) | 0/10 | 0/0 | 10/10 | 0/10 | $0.50 |
| dom-ev-tariffs-pricing | haiku | 8/8 | 0/0 | 8/8 | 8/8 | $1.07 |
| dom-ev-tariffs-pricing | haiku (bez skilli) | 0/8 | 0/0 | 2/8 | 0/8 | $0.56 |
| eng-testing | haiku | 6/10 | 0/0 | 8/10 | 6/10 | $1.23 |
| eng-testing | haiku (bez skilli) | 0/10 | 0/0 | 6/10 | 0/10 | $0.61 |
| sec-llm-security | haiku | 6/8 | 0/0 | 6/8 | 4/8 | $1.01 |
| sec-llm-security | haiku (bez skilli) | 0/8 | 0/0 | 4/8 | 0/8 | $0.44 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | holdout | 45/56 (80%) | 42/56 | 92% | $7.84 | $0.174 | 3 |
| haiku | ze skillami | strojenie | 46/48 (96%) | 46/48 | 99% | $5.78 | $0.126 | 2 |
| haiku | bez skilli | holdout | 37/56 (66%) | — | 83% | $3.85 | $0.104 | 5 |
| haiku | bez skilli | strojenie | 22/48 (46%) | — | 78% | $2.59 | $0.118 | 4 |

## Luka strojenie − holdout

Zaliczone w całości ze skillami na zbiorze strojenia minus na holdoucie. Duża luka znaczy, że opisy i treść skilli dopasowały się do pytań, na których je stroimy. Przewaga = ze skillami minus bez skilli w tym samym zbiorze; różnica przewag nie zależy od trudności pytań. Zmianę skilla przyjmujemy, gdy poprawia strojenie i nie pogarsza holdoutu.

| Model | Strojenie | Holdout | Luka | Przewaga skilli: strojenie | Przewaga skilli: holdout |
|---|---|---|---|---|---|
| haiku | 96% | 80% | +15% | +50% | +14% |

## Niezaliczone

- `core-agent-security` / wstrzykniecie-w-raporcie-researchera / haiku: nie uruchomił się
- `core-delivery-lifecycle` / refinement-i-miary-agentow / haiku: brak: własnymi słowami | opowi\w+ rozwiązani\w+ | wyjaśni\w+, jak — użyte skille: core-delivery-lifecycle
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku: nie uruchomił się — użyte skille: core-git-workflow, core-async-delegation
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku: nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku: nie uruchomił się — użyte skille: core-async-delegation
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku: nie uruchomił się
- `eng-testing` / ho-testing-czesciowa-awaria / haiku: nie uruchomił się
- `eng-testing` / ho-testing-od-razu-zielony / haiku: nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku: brak: LLM07 — użyte skille: sec-llm-security
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku: nie uruchomił się
- `core-grounding` / agent-zmysla-wersje / haiku: nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku: nie uruchomił się — użyte skille: core-git-workflow, core-async-delegation
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku: nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku: nie uruchomił się — użyte skille: core-async-delegation
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku: nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku: brak: typ\w* krok\w* | jawn\w+ (typ|krok) | step type | rodzaj\w* krok\w* — użyte skille: ddd-tactical-design, be-messaging-outbox
- `eng-testing` / ho-testing-akceptacyjne-warstwy / haiku: nie uruchomił się — użyte skille: qa-spec-first-testing
- `eng-testing` / ho-testing-od-razu-zielony / haiku: nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku: brak: LLM07 — użyte skille: sec-llm-security
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku: nie uruchomił się — użyte skille: ai-agents
- `ai-evals` / sedzia-llm-kalibracja / haiku (bez skilli): nie uruchomił się
- `ai-evals` / klasyfikator-decyzji-llm / haiku (bez skilli): nie uruchomił się
- `be-api-design` / idempotencja-platnosci / haiku (bez skilli): nie uruchomił się
- `be-api-design` / paginacja-kolekcji / haiku (bez skilli): nie uruchomił się
- `be-database` / zmiana-nazwy-kolumny / haiku (bez skilli): nie uruchomił się
- `be-database` / masowy-update-wersja / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / wstrzykniecie-w-raporcie-researchera / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / piaskownica-tylko-http / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / telefon-czy-sandbox / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / inwentarz-przebiegow-wylacznik / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / bramki-wdrozenie / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / refinement-i-miary-agentow / haiku (bez skilli): nie uruchomił się
- `core-grounding` / falszywa-opcja-postgres / haiku (bez skilli): nie uruchomił się
- `core-grounding` / agent-zmysla-wersje / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / connascence-magiczne / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / polityka-zmienna-w-czasie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / stop-nieznany-transactionid / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / status-kabel-bez-autoryzacji / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / step-size-zmiana-elementu / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / kalkulator-strefa-i-cdr / haiku (bez skilli): nie uruchomił się
- `eng-testing` / mock-vs-fake / haiku (bez skilli): nie uruchomił się
- `eng-testing` / jakosc-testow / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / sql-od-modelu-tylko-odczyt / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / wzorce-agenta-maile-i-wysylka / haiku (bez skilli): nie uruchomił się
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
- `core-agent-security` / wstrzykniecie-w-raporcie-researchera / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / piaskownica-tylko-http / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / telefon-czy-sandbox / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / inwentarz-przebiegow-wylacznik / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / bramki-wdrozenie / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / refinement-i-miary-agentow / haiku (bez skilli): nie uruchomił się
- `core-grounding` / falszywa-opcja-postgres / haiku (bez skilli): nie uruchomił się
- `core-grounding` / agent-zmysla-wersje / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / connascence-magiczne / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / polityka-zmienna-w-czasie / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / stop-nieznany-transactionid / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / status-kabel-bez-autoryzacji / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / step-size-zmiana-elementu / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / kalkulator-strefa-i-cdr / haiku (bez skilli): nie uruchomił się
- `eng-testing` / mock-vs-fake / haiku (bez skilli): nie uruchomił się
- `eng-testing` / jakosc-testow / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / sql-od-modelu-tylko-odczyt / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / wzorce-agenta-maile-i-wysylka / haiku (bez skilli): nie uruchomił się
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
