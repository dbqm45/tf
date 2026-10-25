# Próba scenariusza „weterynaria” (symulacja Event Stormingu) — 2026-10-25

Decyzja człowieka (2026-10-25): zbudować próbę scenariusza i uruchomić wersję pełną.

- Narzędzie: `packs/pack-it/skills/ddd-es-simulation/scripts/es_probe.py` z plikiem `scenarios/weterynaria/proba.json`
  (9 gotowych wypowiedzi facylitatora i zaproszenie hodowczyni).
- Wariant pełny: każdy uczestnik osobno na Sonnecie, bez narzędzi; coach na Sonnecie (tryb full).
- **Koszt 1,44 USD**, 57 wywołań, 378 s; 46 zdarzeń, 14 hot spotów, 0 odrzuconych kartek, 0 niepoprawnych JSON.

## Wynik
| Oczekiwanie | Wynik |
|---|---|
| wiedza ukryta (18% wizyt przepada, zeszyt, karta rano, 4% leków, pakiety w Excelu, rabat za miot) | 6/6 |
| sprzeczność „kiedy wizyta jest zakończona” → hot spot | ✓ (`hs_004`, `hs_005`) |
| sprzeczność „kto decyduje o przyjęciu w nocy” → hot spot | ✓ (`hs_006`–`hs_008`) |
| Beata pytana po imieniu odpowiada; Jolanta zaproszona mówi | ✓ / ✓ |
| Beata milczy przy pytaniu do całej sali | ✗ w przebiegu — ale wylosowany wariant dnia nr 2 karty brzmi „Ośmielona… powiedz wreszcie o zeszycie”, więc zachowanie było zgodne z kartą. Próba pomija teraz to sprawdzenie przy tym wariancie (`skip_variants`), wynik: 10/10 |

## Uwagi coacha o scenariuszu (z `debrief.md`)
- Karty działają: Kamil projektuje system od rundy 4 i parkuje się dopiero po „odłóżmy na parking”; dr Paweł robi
  dygresje; Halina wraca do przypadku, gdy pytana o konkret; Jolanta narzuca ramę „u nas w hodowli”.
- Gotowe wypowiedzi facylitatora nie zderzają sprzeczności na głos ani nie oznaczają zdarzeń przełomowych — coach
  ocenia to jako błędy prowadzenia; dla próby scenariusza to oczekiwane (sprawdza scenariusz, nie facylitatora).

Pliki: `probe-report.md`, `debrief.md`, `transcript.md`, `board.md`.
