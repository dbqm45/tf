# Rubryka: design

Oceniany artefakt: `docs/project/changes/<CHG-n>/design.md`. Sędzia dostaje artefakt, `plan.md`, `requirements.md`,
`decisions.md`.

## correctness (1–5)

Tabela ramek Figmy (`Wymaganie | Ścieżka | Stan | Ramka | Uwagi`) pokrywa wymagania i stany błędu z requirements.

- **1** — brak tabeli albo tabela wymienia tylko stany „ok" bez stanu błędu.
- **3** — tabela obecna, ale niektóre wymagania bez ramek dla stanów błędu.
- **5** — każde wymaganie ma minimum trzy stany: idle, success, ≥1 error.

## decision_adherence (1–5)

- **1** — projekt ignoruje decyzje (np. decyzja „bez modalu" → persona daje modal).
- **3** — decyzje wymienione, ale przepływ ich nie trzyma.
- **5** — każdy przepływ ma odwołanie do decyzji, która go ograniczyła.

## style (1–5)

- **1** — brak nazw ramek, brak przykładów cytatów z Figmy.
- **3** — nazwy ramek zgrubne, kolumna Uwagi pusta.
- **5** — nazwy ramek zgodne z projektem Figmy (gdy MCP podany), Uwagi niosą kontekst.

Kontrola długości (N17): > `length_control_ratio` × średnia bazowa → auto **-1** w `style`. Baseline:
`phase_avg_chars.design`.
