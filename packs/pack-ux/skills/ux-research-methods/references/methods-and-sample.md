# Dobór metody i wielkość próby

## Tabela metod
| Metoda | Odpowiada na | Kiedy | Uwaga |
|---|---|---|---|
| Wywiad pogłębiony | dlaczego, jak działają dziś, motywacje | początek, rozumienie kontekstu | pytaj o konkretne zdarzenia z przeszłości, nie o opinie i przyszłe zamiary |
| Test moderowany | gdzie i dlaczego się mylą | prototyp lub produkt | zadania realistyczne, bez słów z interfejsu |
| Test niemoderowany | ilu ukończy, ile czasu | gotowy przepływ, więcej osób | brak dopytania; zadania muszą być jednoznaczne |
| Ankieta | ile osób, jak często, jak ocenia | gdy znasz już pytania i odpowiedzi | źle ułożone pytania dają pewne, ale błędne liczby; ankieta nie wyjaśnia „dlaczego” |
| Badanie dzienniczkowe | zachowania w czasie i kontekście | proces trwający dni lub tygodnie | koszt: motywacja uczestników, rośnie rezygnacja; krótkie wpisy, przypomnienia |
| Benchmark konkurencji | jak wypadamy na tle | przed przebudową, cyklicznie | te same zadania i miary u wszystkich; analiza ekspercka tylko uzupełnia testy |
| Badanie włączające | bariery dostępności i niskich umiejętności | zawsze, od wczesnych etapów | osoby z czytnikiem ekranu, sterowaniem głosem, niską biegłością cyfrową |

Dane z analityki mówią, **co** się dzieje; badanie, **dlaczego**. Zaczynaj od danych, jeśli istnieją.

## Wielkość próby — heurystyki
- **Test jakościowy: ok. 5 osób na segment.** Nielsen i Landauer: odsetek problemów wykrytych przez n osób
  ≈ 1−(1−L)^n, przy L≈31% pięć osób daje ok. 85%. Zastrzeżenia: L różni się między produktami i zadaniami;
  grupa musi być jednorodna (kolejne segmenty = kolejne próby); wynik to „większość częstych problemów”, nie
  wszystkie; zasada dotyczy **rund z poprawkami**, nie jednego dużego badania.
- **Test z pomiarem** (czas, odsetek ukończeń): więcej osób, kilkadziesiąt (NN/g podaje ok. 40 [niezweryfikowane]);
  przy małej próbie podawaj przedział ufności lub nie podawaj procentów, tylko liczby („6 z 8”).
- **Wywiady:** nasycenie tematyczne — kończysz, gdy kolejne 2–3 sesje nie dają nowych wątków. 5–8 na segment
  to punkt startowy [założenie], nie norma.
- **Sortowanie kart i test drzewa:** `.claude/skills/ux-information-architecture/SKILL.md`.
- **Ankieta:** liczba wynika z żądanej precyzji i wielkości populacji — policz (data-analysis); nie dobieraj „na oko”.
- Próba celowa nie jest reprezentatywna: nie uogólniaj procentów z 8 wywiadów na wszystkich użytkowników.

## Benchmark UX
Stały zestaw zadań i miar (ukończenie, czas, błędy, SEQ po zadaniu, SUS na końcu), podobni uczestnicy, powtarzany
co wydanie lub kwartał. Zmiana zestawu zadań unieważnia porównanie. SUS i SEQ opisuje ux-feature-design.
