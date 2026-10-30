# Ewaluacje skilli — 2026-10-30 10:51

Przebiegów: 48 · koszt: $5.19 · zaliczone: 17/48

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| ai-evals | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.28 |
| ai-evals | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.24 |
| be-api-design | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.34 |
| be-api-design | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.16 |
| be-database | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.25 |
| be-database | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.14 |
| core-agent-security | haiku | 1/2 | 0/0 | 1/2 | 1/2 | $0.31 |
| core-agent-security | haiku (bez skilli) | 0/2 | 0/0 | 1/2 | 0/2 | $0.14 |
| core-async-delegation | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.25 |
| core-async-delegation | haiku (bez skilli) | 0/2 | 0/0 | 0/2 | 0/2 | $0.16 |
| core-delivery-lifecycle | haiku | 0/2 | 0/0 | 1/2 | 0/2 | $0.28 |
| core-delivery-lifecycle | haiku (bez skilli) | 0/2 | 0/0 | 0/2 | 0/2 | $0.13 |
| core-grounding | haiku | 0/2 | 0/0 | 0/2 | 0/2 | $0.25 |
| core-grounding | haiku (bez skilli) | 0/2 | 0/0 | 0/2 | 0/2 | $0.14 |
| ddd-tactical-design | haiku | 2/2 | 0/0 | 1/2 | 1/2 | $0.30 |
| ddd-tactical-design | haiku (bez skilli) | 0/2 | 0/0 | 1/2 | 0/2 | $0.17 |
| dom-ev-ocpp-16 | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.28 |
| dom-ev-ocpp-16 | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.13 |
| dom-ev-tariffs-pricing | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.28 |
| dom-ev-tariffs-pricing | haiku (bez skilli) | 0/2 | 0/0 | 0/2 | 0/2 | $0.20 |
| eng-testing | haiku | 1/2 | 0/0 | 2/2 | 1/2 | $0.24 |
| eng-testing | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.12 |
| sec-llm-security | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.26 |
| sec-llm-security | haiku (bez skilli) | 0/2 | 0/0 | 1/2 | 0/2 | $0.13 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | holdout | 19/24 (79%) | 18/24 | 92% | $3.33 | $0.175 | 0 |
| haiku | bez skilli | holdout | 13/24 (54%) | — | 82% | $1.86 | $0.143 | 0 |

## Niezaliczone

- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku: nie uruchomił się — użyte skille: core-git-workflow, core-async-delegation
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku: nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku: nie uruchomił się — użyte skille: core-async-delegation
- `core-grounding` / ho-dlugi-regulamin-notatka / haiku: nie uruchomił się
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku: nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku: brak: typ\w* krok\w* | jawn\w+ (typ|krok) | step type | rodzaj\w* krok\w* — użyte skille: ddd-tactical-design, be-messaging-outbox
- `eng-testing` / ho-testing-akceptacyjne-warstwy / haiku: nie uruchomił się — użyte skille: qa-spec-first-testing
- `ai-evals` / ho-evals-kontaminacja-fewshot / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-limit-ruchu-partnera / haiku (bez skilli): nie uruchomił się
- `ai-evals` / ho-evals-saturacja-zepsute-zadanie / haiku (bez skilli): nie uruchomił się
- `be-api-design` / ho-import-czesciowy / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-retencja-duzej-tabeli / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / haiku (bez skilli): nie uruchomił się
- `be-database` / ho-pula-polaczen / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-noc-porazka-bramki / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-pr-agenta-sciezki-chronione / haiku (bez skilli): nie uruchomił się
- `core-async-delegation` / ho-tura-konczy-sie-tekstem / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-zmiana-kontraktu-w-kroku / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / ho-warunek-konca-kroku / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-dlugi-regulamin-notatka / haiku (bez skilli): nie uruchomił się
- `core-grounding` / ho-zuzyty-kontekst-sesji / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-czysta-decyzja / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-offline-rozliczenie / haiku (bez skilli): nie uruchomił się
- `ddd-tactical-design` / ho-tactical-proces-wieloetapowy / haiku (bez skilli): nie uruchomił się
- `dom-ev-ocpp-16` / ho-ocpp16-tolerancyjna-walidacja / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-step-size-postoj / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-akceptacyjne-warstwy / haiku (bez skilli): nie uruchomił się
- `eng-testing` / ho-testing-czesciowa-awaria / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-system-prompt-sekrety / haiku (bez skilli): nie uruchomił się
- `dom-ev-tariffs-pricing` / ho-tariffs-brak-elementu-domyslnego / haiku (bez skilli): nie uruchomił się
- `sec-llm-security` / ho-llmsec-zatwierdzenie-przez-czlowieka / haiku (bez skilli): nie uruchomił się
