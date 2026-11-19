# Ewaluacje skilli — 2026-11-13 17:26

Przebiegów: 18 · koszt: $2.35 · zaliczone: 10/18

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| core-problem-routing | haiku | 4/4 | 0/1 | 4/4 | 5/5 | $0.89 |
| core-problem-routing | haiku (bez skilli) | 0/4 | 0/0 | 1/4 | 0/4 | $0.39 |
| core-problem-routing | sonnet | 4/4 | 0/1 | 4/4 | 5/5 | $0.89 |
| core-problem-routing | sonnet (bez skilli) | 0/4 | 0/0 | 1/4 | 0/4 | $0.18 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 4/4 (100%) | 4/4 | 100% | $0.74 | $0.185 | 0 |
| haiku | bez skilli | strojenie | 1/4 (25%) | — | 50% | $0.39 | $0.390 | 0 |
| sonnet | ze skillami | strojenie | 4/4 (100%) | 4/4 | 100% | $0.74 | $0.184 | 0 |
| sonnet | bez skilli | strojenie | 1/4 (25%) | — | 50% | $0.18 | $0.182 | 0 |

## Wkład skilla

Odsetek scenariuszy trigger z poprawną treścią ze skillami i bez skilli (te same sprawdzenia), tylko scenariusze z przebiegami w obu ramionach. Ramię „ze skillem” liczy tylko przebiegi, w których skill się uruchomił; scenariusze bez uruchomienia są w ostatniej kolumnie (problem opisu lub podpowiedzi, nie treści). Wkład bliski zeru: model radzi sobie bez skilla albo scenariusze są za łatwe. Jeden przebieg to szum — przed decyzją o skillu powtórz pomiar (--repeats 3).

| Skill | Model | Scenariusze | Treść ze skillem | Treść bez skilli | Wkład | Skill się nie uruchomił |
|---|---|---|---|---|---|---|
| core-problem-routing | haiku | 4 | 100% | 25% | +75% | 0 |
| core-problem-routing | sonnet | 4 | 100% | 25% | +75% | 0 |

## Niezaliczone

- `core-problem-routing` / release-monorepo / haiku (bez skilli): nie uruchomił się
- `core-problem-routing` / release-monorepo / sonnet (bez skilli): nie uruchomił się
- `core-problem-routing` / decyzja-trudna / haiku (bez skilli): nie uruchomił się
- `core-problem-routing` / decyzja-trudna / sonnet (bez skilli): nie uruchomił się
- `core-problem-routing` / problem-miedzy-nakladkami / haiku (bez skilli): nie uruchomił się
- `core-problem-routing` / problem-miedzy-nakladkami / sonnet (bez skilli): nie uruchomił się
- `core-problem-routing` / szerokie-szukanie-opcji / haiku (bez skilli): nie uruchomił się
- `core-problem-routing` / szerokie-szukanie-opcji / sonnet (bez skilli): nie uruchomił się
