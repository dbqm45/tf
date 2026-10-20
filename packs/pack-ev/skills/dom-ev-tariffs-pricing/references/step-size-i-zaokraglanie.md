# step_size i zaokrąglanie
> 5. Zaokrąglanie ceny · 6. Źródła

## 1. Reguła (2.2.1-d2 i 2.3.0, rozdział o CDR)
1. `step_size` stosuje się **raz na sesję** dla `ENERGY` oraz **raz** dla `TIME` i `PARKING_TIME` łącznie.
2. Nie stosuje się przy przejściu: z `TIME` na `PARKING_TIME`; z jednego elementu `ENERGY` na inny; z `TIME` na `TIME`;
   z `PARKING_TIME` na `PARKING_TIME`; między dwiema taryfami.
3. Używa się kroku **ostatniego istotnego** składnika (ostatniego użytego w sesji w danym wymiarze).
4. Krok działa na **łącznej ilości** wymiaru w sesji, nie na ostatnim okresie. Nadwyżka z zaokrąglenia jest doliczana do
   ostatniego okresu z tym wymiarem.
5. Gdy są i `TIME`, i `PARKING_TIME`, zaokrągla się łączny czas postoju; ładowanie przed postojem liczy się dokładnie.

## 2. Przykłady ze specyfikacji
| Sytuacja | Wynik |
|---|---|
| 115,2 Wh, 0,25 EUR/kWh, krok 1 | rozliczone 116 Wh, 0,029 EUR |
| to samo, krok 25 | 125 Wh, 0,031 EUR |
| to samo, krok 500 | 500 Wh, 0,125 EUR |
| energia 4,3 kWh przed 17:00 i 1,1 kWh po (krok 500 Wh) | łącznie 5,4 → 5,5 kWh; nie „1,5 kWh po 17:00” |
| czas 6 min przed 17:00 i 22 min po (krok 10 min) | łącznie 28 → 30 min; po 17:00 płatne 24 min, nie 30 |
| ładowanie 21 min, postój 7 min, kroki po 5 min | ładowanie 21 min (nie 25), postój 10 min |
| postój 8 min, krok 300 s | płatne 10 min |

## 3. Sprzeczność przykładów w specyfikacji
Przykład „zmiana elementu #1” (`tariff_14_step_size`, plug-in 16:55, 10 min ładowania, 2 min postoju):
- **2.2.1 pierwotne:** 0,10 + 0,20 + 0,083 = **0,383 EUR** (postój liczony jako „5 min”, co nie wynika z kroku 900 s).
- **2.2.1-d2 i 2.3.0:** 0,10 + 0,20 + 0,25 (15 min postoju po 1,00/h) = **0,55 EUR**.

Przykład „zmiana elementu #3” w d2 (plug-in 19:40, 12 min ładowania, 20 min postoju, postój darmowy po 20:00): podaje
ładowanie 12 min po 1,20/h (0,20) i 15 min po 2,40/h (0,60), razem 0,80. Z JSON `tariff_14_step_size` wynika inaczej:
w oknie 17:00–20:00 ładowanie kosztuje 2,40/h (12 min = 0,48), a postój 1,00/h (8 min płatnych → 15 min = 0,25), razem
0,73 [moje przeliczenie z JSON, 2026-10-20; liczby w opisie przykładu niezgodne z JSON]. Przykłady #2 (1,30 EUR) i #1 d2
(0,55 EUR) zgadzają się z JSON.

Co z tym robić: nie kopiuj liczb z przykładów do testów bez przeliczenia z JSON-a; w testach kalkulatora opieraj się na
regule z punktu 1 i na przykładach, które się zgadzają (zob. `references/przyklady.md`). Gdy partner liczy wg 2.2.1
pierwotnego, rozbieżność w CDR będzie systematyczna przy zmianie elementów; zapytaj o wersję i edycję.

## 4. Algorytm (jak liczy kalkulator fabryki)
1. Dla każdego okresu wyznacz element dla każdego wymiaru po restrykcjach na **początku okresu**.
2. Zsumuj ilość per wymiar; dla czasu: osobno suma `TIME` i suma `PARKING_TIME`.
3. Zaokrąglij w górę sumę `ENERGY` i sumę `PARKING_TIME` do kroku **ostatniego** użytego składnika. `TIME` zaokrąglij
   tylko wtedy, gdy w sesji nie było `PARKING_TIME` (po ładowaniu nie następuje postój).
4. Różnicę (zaokrąglenie minus suma rzeczywista) dolicz do **ostatniego** okresu tego wymiaru, po cenie z tego okresu.
5. Koszt okresu = ilość × cena; VAT per składnik.

Konsekwencje: dla restrykcji zależnych od chwili w środku okresu (próg prądu, energia `min_kwh`) wynik jest poprawny
tylko wtedy, gdy CPO podzielił okres w chwili przekroczenia progu; zob. wymóg dzielenia okresów w CDR.

## 5. Zaokrąglanie ceny
- OCPI nie ma parametrów zaokrąglania ani wymagań w tekście modułu: decydują prawo, umowy stron i waluta.
- Wolumen (godziny, kWh) w CDR jest liczbą, często z 3 miejscami: `1.973 h` to 7102,8 s, więc zaokrąglenie do kroku zmienia
  wynik. Licz z pełną precyzją wolumenów z JSON, dopiero kwoty zaokrąglaj.
- Rekomendacja (nie wymóg OCPI): licz kwoty w `Decimal`, zaokrąglaj raz, na końcu, osobno netto i brutto, i zapisz
  zasadę w umowie z partnerem. Jeśli faktura wymaga kwot per pozycja, zaokrąglaj per pozycja i sumuj zaokrąglone.
- Przykład tolerancji: specyfikacja podaje 13,861 EUR brutto (trzy miejsca), faktura będzie mieć 13,86.
- Porównanie z CDR: różnica do `--tolerance` (domyślnie 0,01) to zaokrąglenie; większa wymaga analizy (zła wersja,
  strefa, brak elementu domyślnego, krok).

## 6. Źródła
`mod_cdrs.asciidoc` (sekcja `step_size`) i `mod_tariffs.asciidoc` (PriceComponent, przykłady) w tagach `2.2.1`,
`v2.2.1-d2`, `v2.3.0`; `230/changelog.asciidoc`. Sprawdzone 2026-10-20.
