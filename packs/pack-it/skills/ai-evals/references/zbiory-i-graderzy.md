# Zbiory i graderzy

Spis treści: 1. Warstwy zbioru · 2. Pozyskiwanie zadań · 3. Kontaminacja · 4. Dobór gradera · 5. Sędzia LLM · 6. Kalibracja · 7. Pułapki

## 1. Warstwy zbioru
| Warstwa | Zawartość | Oczekiwany wynik | Odświeżanie |
|---|---|---|---|
| złoty | 20–50 zadań ze wzorcowym rozwiązaniem, sprawdzonych ręcznie | rośnie z jakością | przy zmianie wymagań |
| regresyjny | każdy naprawiony błąd jako zadanie | blisko 100% | dopisujesz po każdej poprawce |
| brzegowy | puste wejście, za długie, niejednoznaczne, obcy język, brak danych | zależnie od przypadku | przy nowych odkryciach |
| adwersaryjny | wstrzyknięcie polecenia w danych, próba obejścia reguł | odmowa lub ignorowanie | z przeglądów bezpieczeństwa |
| próbki z ruchu | zanonimizowane, losowe i z negatywnych sygnałów | monitoruj trend | co tydzień lub miesiąc |

Ewaluacje o niskim początkowym wyniku (*capability*) to „wzgórze do wspinania”; gdy dojdą do wysokiego wyniku,
przechodzą do regresyjnych.

## 2. Pozyskiwanie zadań
- Źródła: ręczne próby, tracker błędów, kolejka supportu, ocenione przez ludzi odpowiedzi z produkcji.
- Zadanie jednoznaczne: dwóch ekspertów daje ten sam werdykt; jest rozwiązanie wzorcowe. 0% sukcesów w wielu
  próbach zwykle oznacza błąd w zadaniu lub graderze.
- Dane z ruchu: RODO — anonimizacja, podstawa prawna, retencja (arch-privacy-compliance).

## 3. Kontaminacja
- Zbiór ewaluacyjny nie trafia do promptu, przykładów few-shot, danych strojenia ani publicznego repozytorium.
- Przykłady do promptu bierz z osobnej puli; po dołączeniu przykładu do promptu wyłącz go ze zbioru.
- Publiczny benchmark mógł trafić do danych modelu; wynik na nim nie zastępuje własnego zbioru.
- Objaw: wynik skacze po dodaniu przykładów podobnych do zbioru, a na świeżych próbkach z ruchu nie rośnie.

## 4. Dobór gradera
| Typ | Kiedy | Zalety | Wady |
|---|---|---|---|
| kod | format, dokładna odpowiedź, testy, stan środowiska | szybki, tani, powtarzalny | kruchy, nie ocenia niuansów |
| sędzia LLM | ton, zgodność z faktami, kompletność, podsumowania | elastyczny, skalowalny | niedeterministyczny, kosztowny, wymaga kalibracji |
| człowiek | kalibracja, spory przypadek, audyt próbek | wzorzec jakości | drogi, wolny |

Wynik zadania może być binarny (wszyscy graderzy muszą zaliczyć), ważony albo mieszany. Grader odporny na obejścia:
zaliczenie wymaga faktycznego rozwiązania, nie spełnienia litery sprawdzenia.

## 5. Sędzia LLM
- Rubryka: osobny opis każdego poziomu skali z przykładem; liczby bez opisu dają szum.
- Jeden wymiar na sędziego (ton, fakty, kompletność osobno), potem agregacja w kodzie.
- Sędzia widzi wejście, odpowiedź i kryterium; nie widzi nazwy kandydata ani kolejności (losuj pozycje w porównaniach parami).
- Wynik w stałym formacie (JSON: `uzasadnienie`, `ocena`), uzasadnienie przed oceną; opcja „nieznane”.
- Inny model niż generujący (stronniczość wobec własnych odpowiedzi) [założenie z praktyki; docs Anthropic zalecają inny model].
- Temperatura sędziego niska; jedna wersja sędziego przypięta do zbioru, bo zmiana sędziego zmienia wszystkie wyniki.

## 6. Kalibracja
1. 30–50 odpowiedzi różnej jakości; dwóch ludzi ocenia niezależnie [rozmiar to praktyka, nie reguła].
2. Policz zgodność ludzi między sobą (sufit) i sędziego z ludźmi: odsetek zgodnych lub kappa Cohena.
3. Przeczytaj rozbieżności; typowe przyczyny: niejasna rubryka, zbyt surowy lub łagodny sędzia, dwa wymiary w jednym.
4. Popraw rubrykę, powtórz. Zatrzymaj się, gdy sędzia zgadza się z ludźmi prawie tak jak ludzie między sobą.
5. Cyklicznie wracaj: próbka produkcyjna do ręcznej oceny co tydzień lub miesiąc wykrywa dryf sędziego.

## 7. Pułapki
- Średnia z jednego uruchomienia traktowana jak prawda (wariancja).
- Sędzia oceniający dłuższe odpowiedzi wyżej (stronniczość długości) — dodaj do rubryki, że długość nie jest zaletą.
- Zmiana zbioru i modelu naraz — nie wiadomo, co zmieniło wynik.
- Ewaluacja tylko ścieżki szczęśliwej.
