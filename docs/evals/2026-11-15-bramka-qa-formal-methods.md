# Ewaluacje skilli — 2026-11-15 07:35

Przebiegów: 10 · koszt: $1.66 · zaliczone: 10/10

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| qa-formal-methods | haiku | 4/4 | 0/1 | 4/4 | 5/5 | $0.86 |
| qa-formal-methods | sonnet | 4/4 | 0/1 | 4/4 | 5/5 | $0.80 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania. Pasmo szumu: rozpiętość odsetka zaliczeń w całości między powtórzeniami ramienia — różnica między ramionami mniejsza niż pasmo to szum, nie wynik. Bez powtórzeń pasma nie ma — przed decyzją o skillu powtórz pomiar (--repeats 5).

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne | Pasmo szumu |
|---|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 4/4 (100%) | 4/4 | 100% | $0.71 | $0.179 | 0 | — |
| sonnet | ze skillami | strojenie | 4/4 (100%) | 4/4 | 100% | $0.65 | $0.163 | 0 | — |
