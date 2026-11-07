# Ewaluacje skilli — 2026-11-07 22:10

Przebiegów: 2 · koszt: $0.34 · zaliczone: 1/2

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| sec-web-vulnerabilities | haiku | 1/1 | 0/0 | 1/1 | 1/1 | $0.17 |
| sec-web-vulnerabilities | sonnet | 1/1 | 0/0 | 0/1 | 0/1 | $0.17 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania.

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne |
|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | strojenie | 1/1 (100%) | 1/1 | 100% | $0.17 | $0.167 | 0 |
| sonnet | ze skillami | strojenie | 0/1 (0%) | 1/1 | 60% | $0.17 | — | 0 |

## Niezaliczone

- `sec-web-vulnerabilities` / cdn-cudza-strona-konta / sonnet: brak: Werdykt\s*:; brak: test\w*[^\n]{0,160}(drug\w*|inn\w*|obc\w*) (sesj|użytkownik|kont) | test\w*[^\n]{0,160}(no-store|HIT|MISS|cf-cache-status|x-cache) | (no-store|HIT|MISS)[^\n]{0,120}test — użyte skille: sec-web-vulnerabilities
