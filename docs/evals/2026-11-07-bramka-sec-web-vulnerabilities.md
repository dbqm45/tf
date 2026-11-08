# Ewaluacje skilli — 2026-11-07 21:53

Przebiegów: 16 · koszt: $2.31 · zaliczone: 13/16

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| sec-web-vulnerabilities | haiku | 4/5 | 0/3 | 4/5 | 6/8 | $1.19 |
| sec-web-vulnerabilities | sonnet | 4/5 | 0/3 | 5/5 | 7/8 | $1.12 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 4/5 (80%) | 4/5 | 94% | $0.72 | $0.179 | 0 |
| sonnet | ze skillami | strojenie | 5/5 (100%) | 4/5 | 100% | $0.66 | $0.133 | 0 |

## Niezaliczone

- `sec-web-vulnerabilities` / kupon-jednorazowy-wyscig / haiku: nie uruchomił się
- `sec-web-vulnerabilities` / kupon-jednorazowy-wyscig / sonnet: nie uruchomił się
- `sec-web-vulnerabilities` / audyt-zaawansowany-format / haiku: brak: CWE-\d+ — użyte skille: sec-web-vulnerabilities
