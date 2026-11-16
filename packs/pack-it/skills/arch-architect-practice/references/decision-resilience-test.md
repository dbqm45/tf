# Test odporności decyzji

Po co: modele językowe (i ludzie) skłaniają się ku potwierdzeniu tego, co już zostało powiedziane. Pytanie „czy X
pasuje do Y?” prawie zawsze dostaje „tak”. Test zmusza do szukania powodów, dla których decyzja się nie uda —
zanim zostanie zapisana w ADR lub `stack-decision.md`.

## Kiedy
- przed zapisem decyzji architektonicznej lub wyboru stacku/platformy (arch-tech-selection, krok 8);
- gdy wszyscy (ludzie i model) zgadzają się od pierwszej minuty;
- gdy rekomendacja powstała z badania źródeł (core-source-research) — przed jej przekazaniem.

## Trzy soczewki
| Soczewka | Polecenie dla siebie | Dobry wynik | Słaby wynik |
|---|---|---|---|
| adwokat diabła | „Podaj 3–5 powodów, dla których X to zły wybór dla tego projektu” | „limit 100 połączeń w planie podstawowym przy 3 instancjach i puli 50” | „może być drogo” |
| pre-mortem | „Minęło 6 miesięcy, decyzja okazała się porażką. Co poszło nie tak?” | narracja z konkretnym łańcuchem: założenie → zdarzenie → skutek | lista ogólników |
| nieznane niewiadome | „Jakich klas ryzyka nie objęła ocena?” | zgodność, kopie, wyjście od dostawcy, beta, zależność od innego zespołu — każda z pytaniem kontrolnym | „zawsze coś może się zdarzyć” |

## Wynik i zapis
Dla każdego ryzyka: **akceptuję** / **znane ograniczenie** (rejestr ryzyk) / **zmieniam wybór**. Tabela w ADR lub
`stack-decision.md`:

| Ryzyko | Źródło (soczewka / badanie) | Prawdop. | Wpływ | Działanie |
|---|---|---|---|---|
| brak kopii bazy w planie podstawowym | pre-mortem | średnie | wysoki | nocna kopia do storage, test odtworzenia |

## Uzupełnienia bez procedury
- **Trzy alternatywy w tabeli** (koszt wdrożenia, koszt utrzymania, krzywa uczenia, kluczowe ograniczenie) zamiast
  oceny jednej opcji w próżni.
- **Rotacja ról:** spójrz na decyzję oczami frontendu, bezpieczeństwa, operacji, kosztów. Gdy któraś rola reaguje
  źle, podaj realną alternatywę, a nie tylko zastrzeżenie.
- Sygnał, że test stał się rytuałem: w ostatnich decyzjach nic nie zostało zmienione ani zapisane jako ograniczenie.

## Przykład
**Decyzja:** zarządzany PostgreSQL u dostawcy platformy aplikacji. **Adwokat diabła:** limit połączeń w planie
startowym, brak replik do odczytu, wyjście wymaga zrzutu i przerwy. **Pre-mortem:** po kampanii marketingowej pula
połączeń wyczerpana, zapytania raportowe blokują zapisy, migracja do innej bazy pod presją. **Nieznane
niewiadome:** region danych kopii zapasowych, zasady usuwania danych po rezygnacji, status bety dla
rozgałęziania bazy. **Wynik:** wybór zostaje; dwa znane ograniczenia (pula połączeń → pooler od pierwszego dnia;
raporty → osobny read model później), jedno działanie (sprawdzić region kopii przed startem).
