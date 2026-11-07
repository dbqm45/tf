# Ewaluacje skilli — 2026-11-07 22:03

Przebiegów: 4 · koszt: $0.51 · zaliczone: 2/4

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| sec-web-vulnerabilities | haiku | 1/2 | 0/0 | 2/2 | 1/2 | $0.25 |
| sec-web-vulnerabilities | sonnet | 1/2 | 0/0 | 2/2 | 1/2 | $0.25 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 2/2 (100%) | 1/2 | 100% | $0.25 | $0.127 | 0 |
| sonnet | ze skillami | strojenie | 2/2 (100%) | 1/2 | 100% | $0.25 | $0.126 | 0 |

## Niezaliczone

- `sec-web-vulnerabilities` / cdn-cudza-strona-konta / haiku: nie uruchomił się
- `sec-web-vulnerabilities` / cdn-cudza-strona-konta / sonnet: nie uruchomił się
