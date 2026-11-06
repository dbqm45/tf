# Rubryka: requirements

Oceniany artefakt: `docs/project/changes/<CHG-n>/requirements.md`. Sędzia dostaje: artefakt, `intent.md`,
`decisions.md`, zapytanie o ocenę na 3 osiach w JSON.

## correctness (1–5)

Kryteria akceptacji odpowiadają zamiarowi z `intent.md` i decyzjom.

- **1** — kryteria oderwane od zamiaru albo sprzeczne z decyzją (mimo że decyzja jest w decisions.md).
- **3** — kryteria pasują, ale część bez przykładu (Given/When/Then) albo bez stanu błędu.
- **5** — każde kryterium ma przykład i co najmniej jeden stan błędu; odwołania do decyzji przy spornych
  wymaganiach.

## decision_adherence (1–5)

- **1** — decyzje pominięte albo obchodzone („alternatywa poza decyzją").
- **3** — decyzje wymienione, ale nie widać, jak ograniczają kryteria.
- **5** — każda wiążąca decyzja ma widoczne zastosowanie w którymś z kryteriów (ref CHG-n/Dk).

## style (1–5)

- **1** — kryteria bez przykładów, spór „powinno działać" / „musi działać" bez czytelnego oznaczenia wagi.
- **3** — kryteria zorganizowane, ale nagłówki niekonsekwentne; priorytety opcjonalne.
- **5** — nagłówki jednolite, priorytety przy każdym kryterium (`must` / `should`), przykład krótki.

Kontrola długości (N17): > `length_control_ratio` × średnia bazowa → auto **-1** w `style`. Baseline:
`phase_avg_chars.requirements`.
