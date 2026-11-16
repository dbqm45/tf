# Ewaluacje skilli — 2026-11-16 05:30

Przebiegów: 6 · koszt: $0.60 · zaliczone: 4/6

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| core-agent-security | haiku | 0/0 | 0/1 | 0/0 | 1/1 | $0.13 |
| core-agent-security | sonnet | 0/0 | 0/1 | 0/0 | 1/1 | $0.11 |
| core-git-workflow | haiku | 1/1 | 0/0 | 1/1 | 1/1 | $0.14 |
| core-git-workflow | haiku (bez skilli) | 0/1 | 0/0 | 1/1 | 0/1 | $0.04 |
| core-git-workflow | sonnet | 1/1 | 0/0 | 1/1 | 1/1 | $0.14 |
| core-git-workflow | sonnet (bez skilli) | 0/1 | 0/0 | 1/1 | 0/1 | $0.04 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania. Pasmo szumu: rozpiętość odsetka zaliczeń w całości między powtórzeniami ramienia — różnica między ramionami mniejsza niż pasmo to szum, nie wynik. Bez powtórzeń pasma nie ma — przed decyzją o skillu powtórz pomiar (--repeats 5).

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne | Pasmo szumu |
|---|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 1/1 (100%) | 1/1 | 100% | $0.14 | $0.136 | 0 | — |
| haiku | bez skilli | strojenie | 1/1 (100%) | — | 100% | $0.04 | $0.041 | 0 | — |
| sonnet | ze skillami | strojenie | 1/1 (100%) | 1/1 | 100% | $0.14 | $0.136 | 0 | — |
| sonnet | bez skilli | strojenie | 1/1 (100%) | — | 100% | $0.04 | $0.039 | 0 | — |

## Wkład skilla

Odsetek scenariuszy trigger z poprawną treścią ze skillami i bez skilli (te same sprawdzenia), tylko scenariusze z przebiegami w obu ramionach. Ramię „ze skillem” liczy tylko przebiegi, w których skill się uruchomił; scenariusze bez uruchomienia są w ostatniej kolumnie (problem opisu lub podpowiedzi, nie treści). Wkład bliski zeru: model radzi sobie bez skilla albo scenariusze są za łatwe. Jeden przebieg to szum — przed decyzją o skillu powtórz pomiar (--repeats 5).

| Skill | Model | Scenariusze | Treść ze skillem | Treść bez skilli | Wkład | Skill się nie uruchomił |
|---|---|---|---|---|---|---|
| core-git-workflow | haiku | 1 | 100% | 100% | +0% | 0 |
| core-git-workflow | sonnet | 1 | 100% | 100% | +0% | 0 |

## Zaliczane bez skilli

Scenariusze trigger, które bez skilli przechodzą sprawdzenia treści na każdym modelu — nie mierzą wkładu skilla; do zaostrzenia albo zastąpienia trudniejszym.

- `core-git-workflow` / pr-agenta-oznaczenie-i-infra

## Niezaliczone

- `core-git-workflow` / pr-agenta-oznaczenie-i-infra / haiku (bez skilli): nie uruchomił się
- `core-git-workflow` / pr-agenta-oznaczenie-i-infra / sonnet (bez skilli): nie uruchomił się
