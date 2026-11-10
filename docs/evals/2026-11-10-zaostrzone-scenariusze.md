# Ewaluacje skilli — 2026-11-10 12:47

Przebiegów: 36 · koszt: $3.46 · zaliczone: 18/36

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| arch-privacy-compliance | haiku | 1/1 | 0/0 | 1/1 | 1/1 | $0.17 |
| arch-privacy-compliance | haiku (bez skilli) | 0/1 | 0/0 | 0/1 | 0/1 | $0.07 |
| arch-privacy-compliance | sonnet | 1/1 | 0/0 | 1/1 | 1/1 | $0.15 |
| arch-privacy-compliance | sonnet (bez skilli) | 0/1 | 0/0 | 0/1 | 0/1 | $0.05 |
| be-business-app-patterns | haiku | 5/5 | 0/0 | 5/5 | 5/5 | $0.65 |
| be-business-app-patterns | haiku (bez skilli) | 0/5 | 0/0 | 5/5 | 0/5 | $0.29 |
| be-business-app-patterns | sonnet | 5/5 | 0/0 | 5/5 | 5/5 | $0.64 |
| be-business-app-patterns | sonnet (bez skilli) | 0/5 | 0/0 | 4/5 | 0/5 | $0.19 |
| core-delivery-lifecycle | haiku | 1/1 | 0/0 | 1/1 | 1/1 | $0.18 |
| core-delivery-lifecycle | haiku (bez skilli) | 0/1 | 0/0 | 0/1 | 0/1 | $0.07 |
| core-delivery-lifecycle | sonnet | 1/1 | 0/0 | 1/1 | 1/1 | $0.16 |
| core-delivery-lifecycle | sonnet (bez skilli) | 0/1 | 0/0 | 0/1 | 0/1 | $0.04 |
| eng-repo-readiness | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.28 |
| eng-repo-readiness | haiku (bez skilli) | 0/2 | 0/0 | 1/2 | 0/2 | $0.12 |
| eng-repo-readiness | sonnet | 2/2 | 0/0 | 2/2 | 2/2 | $0.28 |
| eng-repo-readiness | sonnet (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.11 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 9/9 (100%) | 9/9 | 100% | $1.28 | $0.142 | 0 |
| haiku | bez skilli | strojenie | 6/9 (67%) | — | 93% | $0.55 | $0.092 | 0 |
| sonnet | ze skillami | strojenie | 9/9 (100%) | 9/9 | 100% | $1.23 | $0.137 | 0 |
| sonnet | bez skilli | strojenie | 6/9 (67%) | — | 95% | $0.39 | $0.066 | 0 |

## Wkład skilla

Odsetek scenariuszy trigger z poprawną treścią ze skillami i bez skilli (te same sprawdzenia), tylko scenariusze z przebiegami w obu ramionach. Ramię „ze skillem” liczy tylko przebiegi, w których skill się uruchomił; scenariusze bez uruchomienia są w ostatniej kolumnie (problem opisu lub podpowiedzi, nie treści). Wkład bliski zeru: model radzi sobie bez skilla albo scenariusze są za łatwe. Jeden przebieg to szum — przed decyzją o skillu powtórz pomiar (--repeats 3).

| Skill | Model | Scenariusze | Treść ze skillem | Treść bez skilli | Wkład | Skill się nie uruchomił |
|---|---|---|---|---|---|---|
| arch-privacy-compliance | haiku | 1 | 100% | 0% | +100% | 0 |
| arch-privacy-compliance | sonnet | 1 | 100% | 0% | +100% | 0 |
| be-business-app-patterns | haiku | 5 | 100% | 100% | +0% | 0 |
| be-business-app-patterns | sonnet | 5 | 100% | 80% | +20% | 0 |
| core-delivery-lifecycle | haiku | 1 | 100% | 0% | +100% | 0 |
| core-delivery-lifecycle | sonnet | 1 | 100% | 0% | +100% | 0 |
| eng-repo-readiness | haiku | 2 | 100% | 50% | +50% | 0 |
| eng-repo-readiness | sonnet | 2 | 100% | 100% | +0% | 0 |

## Zaliczane bez skilli

Scenariusze trigger, które bez skilli przechodzą sprawdzenia treści na każdym modelu — nie mierzą wkładu skilla; do zaostrzenia albo zastąpienia trudniejszym.

- `be-business-app-patterns` / audit-log-zamowien
- `be-business-app-patterns` / impersonacja-supportu
- `be-business-app-patterns` / soft-delete-a-rodo
- `be-business-app-patterns` / usuniecie-projektu-nieodwracalne
- `eng-repo-readiness` / dx-testy-wymagaja-uslug

## Niezaliczone

- `arch-privacy-compliance` / klasyfikacja-danych / haiku (bez skilli): nie uruchomił się
- `arch-privacy-compliance` / klasyfikacja-danych / sonnet (bez skilli): nie uruchomił się
- `be-business-app-patterns` / usuniecie-projektu-nieodwracalne / haiku (bez skilli): nie uruchomił się
- `be-business-app-patterns` / usuniecie-projektu-nieodwracalne / sonnet (bez skilli): nie uruchomił się
- `be-business-app-patterns` / audit-log-zamowien / haiku (bez skilli): nie uruchomił się
- `be-business-app-patterns` / audit-log-zamowien / sonnet (bez skilli): nie uruchomił się
- `be-business-app-patterns` / soft-delete-a-rodo / haiku (bez skilli): nie uruchomił się
- `be-business-app-patterns` / soft-delete-a-rodo / sonnet (bez skilli): nie uruchomił się
- `be-business-app-patterns` / impersonacja-supportu / haiku (bez skilli): nie uruchomił się
- `be-business-app-patterns` / impersonacja-supportu / sonnet (bez skilli): nie uruchomił się
- `be-business-app-patterns` / edge-operacja-masowa-50-tys / haiku (bez skilli): nie uruchomił się
- `be-business-app-patterns` / edge-operacja-masowa-50-tys / sonnet (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / przeglad-specyfikacji-panel / haiku (bez skilli): nie uruchomił się
- `core-delivery-lifecycle` / przeglad-specyfikacji-panel / sonnet (bez skilli): nie uruchomił się
- `eng-repo-readiness` / dx-wejscie-do-projektu / haiku (bez skilli): nie uruchomił się
- `eng-repo-readiness` / dx-wejscie-do-projektu / sonnet (bez skilli): nie uruchomił się
- `eng-repo-readiness` / dx-testy-wymagaja-uslug / haiku (bez skilli): nie uruchomił się
- `eng-repo-readiness` / dx-testy-wymagaja-uslug / sonnet (bez skilli): nie uruchomił się
