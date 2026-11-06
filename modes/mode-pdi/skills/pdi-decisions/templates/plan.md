# Plan zmiany {CHG}

Cięcia (TSK) — każde daje wartość samo i kończy się weryfikacją. Klucze cięć dopisz też do `tasks` w nagłówku,
a linię wydania (R1 = MVP) i flagę — do `release.yaml` (te same wartości co w kolumnach poniżej).

Rodzaj: „cięcie” (wartość: „użytkownik może …”) albo „fundament” (wartość: „(fundament) … jest gotowe”). Fundament
musi mieć w „Odblokowuje” cięcia tej zmiany (TSK), których wymaga; cięcie — dosłowne ID wymagań w „Wymagania”
(`US-02`, `FR-007`) albo weryfikację. To samokontrola planu cięć; `decision_record.py check` i REL-008 w ci_for_sdlc
sprawdzają ją tak samo.

| Cięcie | Rodzaj | Wydanie | Flaga | Wartość | Wymagania | Odblokowuje | Pliki | Weryfikacja |
|---|---|---|---|---|---|---|---|---|
| TSK-? | cięcie | R1 | — | użytkownik może … | US-? | — | | <polecenie i oczekiwany wynik> |

## Rozważone opcje

Co najmniej dwie opcje z plusami, minusami i kosztem; wskaż wybór i powód (N20; `arch-tech-selection` §3). Odrzucone
opcje trafiają do uzasadnienia decyzji B3 i karty bramki (N11). `decision_record.py check` odrzuca plan z jedną
opcją.

### Opcja A — <nazwa>

- Plusy: …
- Minusy: …
- Koszt: … (nauka, złożoność, utrzymanie)

### Opcja B — <nazwa>

- Plusy: …
- Minusy: …
- Koszt: …

**Wybór:** Opcja <A/B> — <powód odwołujący się do czynników z `arch-quality-attributes` i do domeny>.

## Cele zmiany (`targets`)

Mierzalne progi, które zmiana musi spełnić przed B4 (Z7b-1, DZ7). Architekt proponuje je tutaj, człowiek
zatwierdza na B3; sprawdza ci_for_sdlc (Z7b-1b). Te same wartości wpisz do `release.yaml` pod kluczem `targets` —
ten dokument jest dla człowieka, plik YAML dla maszyn. Dla produktu AI progi ewaluacji są obowiązkowe (DZ7).

| Nazwa                      | Rodzaj      | Próg       | Narzędzie | Uzasadnienie (czynnik / ryzyko)          |
|----------------------------|-------------|------------|-----------|-------------------------------------------|
| pokrycie zmienionych linii | coverage    | >= 90%     | …         | … (N4)                                    |
| mutacje zmienionego kodu   | mutation    | >= 70%     | …         | StrykerJS (JS/TS) albo mutmut (Python); N4|
| p95 dla ścieżki X          | performance | <= 400ms   | …         | wynika z SLO 99,5% w 28 dni (opcjonalnie) |
| <nazwa ewaluacji>          | evaluation  | >= <wynik> | <zestaw>  | **wymagane dla produktu AI (DZ7)**         |
