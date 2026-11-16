# Ewaluacje skilli — 2026-11-16 05:29

Przebiegów: 32 · koszt: $2.71 · zaliczone: 16/32

Uruchomienie = skill wczytany przy pytaniu, które do niego należy. Fałszywe = wczytany przy pytaniu sąsiedniego skilla. Treść = sprawdzenia wiedzy specyficznej w odpowiedzi (także bez uruchomienia).

| Skill | Model | Uruchomienie | Fałszywe | Treść | Zaliczone | Koszt |
|---|---|---|---|---|---|---|
| core-agent-security | haiku | 6/6 | 0/0 | 6/6 | 6/6 | $0.73 |
| core-agent-security | haiku (bez skilli) | 0/6 | 0/0 | 6/6 | 0/6 | $0.37 |
| core-agent-security | sonnet | 6/6 | 0/0 | 6/6 | 6/6 | $0.69 |
| core-agent-security | sonnet (bez skilli) | 0/6 | 0/0 | 6/6 | 0/6 | $0.24 |
| core-git-workflow | haiku | 2/2 | 0/0 | 2/2 | 2/2 | $0.23 |
| core-git-workflow | haiku (bez skilli) | 0/2 | 0/0 | 2/2 | 0/2 | $0.12 |
| core-git-workflow | sonnet | 2/2 | 0/0 | 2/2 | 2/2 | $0.22 |
| core-git-workflow | sonnet (bez skilli) | 0/2 | 0/0 | 1/2 | 0/2 | $0.10 |

## Protokół: wynik czy koszt

Główny wynik: zadania zaliczone w całości (odpowiedź spełnia wszystkie kryteria — ta sama miara w obu ramionach). Uruchomienie: skill wczytany. Średnia kryteriów to diagnostyka. Koszt na rozwiązane zadanie obejmuje wszystkie przebiegi ramienia. Niestabilne: scenariusz z różnym wynikiem między powtórzeniami (--repeats). Holdout to zamknięty zbiór — nie stroimy pod jego pytania. Pasmo szumu: rozpiętość odsetka zaliczeń w całości między powtórzeniami ramienia — różnica między ramionami mniejsza niż pasmo to szum, nie wynik. Powtórzeń: 2 — pasmo jest orientacyjne (pewniejsze od 5).

| Model | Ramię | Zbiór | Zaliczone w całości | Uruchomienie | Średnia kryteriów | Koszt | Koszt na rozwiązane | Niestabilne | Pasmo szumu |
|---|---|---|---|---|---|---|---|---|---|
| haiku | ze skillami | holdout | 8/8 (100%) | 8/8 | 100% | $0.95 | $0.119 | 0 | 0% |
| haiku | bez skilli | holdout | 8/8 (100%) | — | 100% | $0.49 | $0.062 | 0 | 0% |
| sonnet | ze skillami | holdout | 8/8 (100%) | 8/8 | 100% | $0.92 | $0.115 | 0 | 0% |
| sonnet | bez skilli | holdout | 7/8 (88%) | — | 96% | $0.35 | $0.050 | 1 | 25% |

## Wkład skilla

Odsetek scenariuszy trigger z poprawną treścią ze skillami i bez skilli (te same sprawdzenia), tylko scenariusze z przebiegami w obu ramionach. Ramię „ze skillem” liczy tylko przebiegi, w których skill się uruchomił; scenariusze bez uruchomienia są w ostatniej kolumnie (problem opisu lub podpowiedzi, nie treści). Wkład bliski zeru: model radzi sobie bez skilla albo scenariusze są za łatwe. Jeden przebieg to szum — przed decyzją o skillu powtórz pomiar (--repeats 5).

| Skill | Model | Scenariusze | Treść ze skillem | Treść bez skilli | Wkład | Skill się nie uruchomił |
|---|---|---|---|---|---|---|
| core-agent-security | haiku | 3 | 100% | 100% | +0% | 0 |
| core-agent-security | sonnet | 3 | 100% | 100% | +0% | 0 |
| core-git-workflow | haiku | 1 | 100% | 100% | +0% | 0 |
| core-git-workflow | sonnet | 1 | 100% | 50% | +50% | 0 |

## Zaliczane bez skilli

Scenariusze trigger, które bez skilli przechodzą sprawdzenia treści na każdym modelu — nie mierzą wkładu skilla; do zaostrzenia albo zastąpienia trudniejszym.

- `core-agent-security` / h2-issue-curl
- `core-agent-security` / h2-mcp-token
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny

## Niezaliczone

- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / sonnet (bez skilli): nie uruchomił się
- `core-agent-security` / h2-issue-curl / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / h2-issue-curl / sonnet (bez skilli): nie uruchomił się
- `core-agent-security` / h2-mcp-token / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / h2-mcp-token / sonnet (bez skilli): nie uruchomił się
- `core-git-workflow` / ho-pr-agenta-sciezki-chronione / haiku (bez skilli): nie uruchomił się
- `core-git-workflow` / ho-pr-agenta-sciezki-chronione / sonnet (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / ho-serwer-narzedzi-zewnetrzny / sonnet (bez skilli): nie uruchomił się
- `core-agent-security` / h2-issue-curl / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / h2-issue-curl / sonnet (bez skilli): nie uruchomił się
- `core-agent-security` / h2-mcp-token / haiku (bez skilli): nie uruchomił się
- `core-agent-security` / h2-mcp-token / sonnet (bez skilli): nie uruchomił się
- `core-git-workflow` / ho-pr-agenta-sciezki-chronione / haiku (bez skilli): nie uruchomił się
- `core-git-workflow` / ho-pr-agenta-sciezki-chronione / sonnet (bez skilli): nie uruchomił się
