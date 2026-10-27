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
