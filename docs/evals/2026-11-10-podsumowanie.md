# Ewaluacja skilli z 2026-11-10 — podsumowanie

Zakres: nowe scenariusze z A3, A4, A5, A9 i zaostrzenie scenariuszy A2a (`be-business-app-patterns`). Modele
Haiku i Sonnet, ze skillami i bez (`--baseline`), po jednym przebiegu. Koszt łącznie **6,13 USD** (limit uzgodniony
z człowiekiem: 10 USD). Surowe wyniki i raporty: `2026-11-10-a3-a4-a5-a9.{md,jsonl}` (pomiar 1, 2,67 USD),
`2026-11-10-zaostrzone-scenariusze.{md,jsonl}` (pomiar 2, 3,46 USD).

Miara: „Wkład skilla” — odsetek scenariuszy z poprawną treścią ze skillem (tylko przebiegi, w których się
uruchomił) minus bez skilli, przy tych samych sprawdzeniach (B4). Jeden przebieg to szum; wnioski są kierunkowe.

| Skill / scenariusz | Pomiar 1 | Zmiana | Pomiar 2 |
|---|---|---|---|
| core-delivery-lifecycle / `mapa-artefaktow` (A4) | +100% oba modele | — | — |
| be-database / `erd-z-migracji` (A4) | +100% oba modele | — | — |
| core-delivery-lifecycle / `przeglad-specyfikacji-panel` (A9) | skill się nie uruchomił (model wybierał qa-change-review) | słowa kluczowe w core-delivery-lifecycle; granica w opisie qa-change-review | uruchamia się na obu; treść 100% vs 0% |
| arch-privacy-compliance / `klasyfikacja-danych` (A5) | +0% (za łatwy) | sprawdzenie `data-inventory`, `tf analyze --only data-classification` | +100% oba modele |
| eng-repo-readiness / `dx-wejscie-do-projektu` (A3) | +0% | `--wait`/`service_healthy`, pomiar na świeżym klonie | Haiku: zaliczany tylko ze skillem; Sonnet: także bez |
| eng-repo-readiness / `dx-testy-wymagaja-uslug` (A3) | +0% | `--wait`/`service_healthy`, konkretne polecenia testów powiązanych | nadal zaliczany bez skilla |
| be-business-app-patterns, 5 scenariuszy (A2a) | +0% (z przebiegu 2026-11-09) | po jednej–dwóch grupach sprawdzeń z reguł skilla | Haiku +0%, Sonnet +20%; 4/5 zaliczane bez skilla |

## Wnioski
- **A4 i A9 dodają wiedzę, której modele nie mają** — ścieżki i zasady fabryki (mapa, ERD w dzienniku, panel
  recenzentów). A9 wymagał poprawki wyboru skilla, nie treści.
- **A5** dodaje wiedzę dopiero na poziomie fabryki (inwentarz, moduł analizy); ogólną klasyfikację danych modele
  znają same.
- **A3 i A2a**: modele, zwłaszcza Sonnet, znają tę wiedzę bez skilla. Dalsze zaostrzanie sprawdzeń pod treść skilla
  mierzyłoby dopasowanie do testu, nie pomoc. Wartość tych skilli, jeśli jest, leży w procedurze (ustal fakty,
  checklista, testy) i w spójności między personami — tego te scenariusze nie mierzą. Decyzja: scenariusze zostają
  jako ochrona przed regresją, bez kolejnych rund strojenia. Ewentualny pomiar procedury: ewaluacja przebiegu
  (flow-evals) na zadaniu z kodem, a nie pytanie i odpowiedź — do decyzji człowieka.
