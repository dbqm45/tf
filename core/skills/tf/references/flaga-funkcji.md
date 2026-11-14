# Flaga funkcji na historyjkę

Czytasz przy planie (§2 SKILL.md), gdy `run_state.py flag <katalog> mode` zwraca `auto`. Przebieg cięcia pdi ma
flagę z planu wydania — patrz `.claude/skills/tf/references/ciecia-pdi.md`.

## Decyzja (bez niej etap `pr` jest odrzucany)
| Zmiana | Co zapisujesz |
|---|---|
| nowe zachowanie widoczne dla użytkownika | `run_state.py flag <katalog> set <klucz> --remove-by <RRRR-MM-DD>` |
| poprawka błędu, refaktor, dokumentacja, konfiguracja albo projekt bez mechanizmu flag | `run_state.py flag <katalog> none --reason "bez flagi, bo …"` |

**Nazwa flagi:** pytasz człowieka, podając propozycję od klucza zadania (np. `proj_123_eksport_csv`). Z `--auto` nie
ma kogo zapytać — bierzesz propozycję i zapisujesz ją w planie i w opisie PR jako
**[założenie: nazwa flagi do potwierdzenia]**.

Wynik `manual` (człowiek wyłączył automatyczne flagi, `feature_flags.auto: false`): flagi nie zakładasz i niczego
o niej nie zapisujesz; w opisie PR piszesz „flagę dodaje człowiek”.

## Jak prowadzisz kawałki z flagą
- flagę zakłada pierwszy kawałek; każdy kawałek chowa za nią swoje zachowanie;
- testy idą w obu stanach: włączona — kryteria `AC-n`; wyłączona — stare zachowanie bez zmian;
- commity mają stopkę `Flag: <klucz>`;
- ostatni commit włącza flagę **tylko na środowisku testowym** (plik i środowiska: `.tf/config/operations.json`).

Flagi na innym środowisku nie włączasz i zgody na to nie zapisujesz (`tf task flag <KEY> allow …`) — to decyzja
człowieka. Kontrola: `tf flag check <KEY>`; włączenie poza środowiskiem testowym bez zapisanej zgody odrzuca etap `pr`.
