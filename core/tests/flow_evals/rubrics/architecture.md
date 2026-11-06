# Rubryka: architecture

Oceniany artefakt: `docs/project/changes/<CHG-n>/plan.md` (i towarzyszący `release.yaml`, `architecture.md`).
Sędzia dostaje artefakt, `requirements.md`, `decisions.md`.

## correctness (1–5)

Plan cięć (tabela ze słupkami **Wydanie** i **Flaga**) odpowiada wymaganiom i decyzjom.

- **1** — cięcia bez pokrycia wymagań albo z jednym cięciem na wszystko.
- **3** — cięcia pokrywają wymagania, ale ich dowód sprawdzalności (metryka, test akceptacyjny) brakuje.
- **5** — każde cięcie ma dowód (odwołanie do kryterium albo metryki) i konkretne wejście do następnej fazy.

## decision_adherence (1–5)

- **1** — architektura pomija decyzje (np. decyzja „bez SSR" ignorowana).
- **3** — decyzje wymienione w sekcji ADR, ale nie widać ich w planie cięć.
- **5** — każda decyzja znajduje ślad w planie (cięcie, ADR, pominięty alternatywny wariant).

## style (1–5)

- **1** — brak słupków, brak tabeli, akapity zamiast listy cięć.
- **3** — tabela jest, ale słupki Wydanie/Flaga puste albo niekonsekwentne.
- **5** — tabela zgodna z kontraktem, ADR jednoakapitowe, release.yaml walidowalne.

Kontrola długości (N17): > `length_control_ratio` × średnia bazowa → auto **-1** w `style`. Baseline:
`phase_avg_chars.architecture`.
