# Ruch i nałożenie marki

## Ruch — decyzje
1. **Cel:** wskazuje związek (skąd się wzięło okno), potwierdza zmianę stanu, kieruje uwagę. Brak celu → bez ruchu.
2. **Czas** (praktyka projektowa; Material 3 podaje własne tokeny, np. `md.motion.duration.short1` = 50 ms):

   | Typ | Czas |
   |---|---|
   | zmiana stanu kontrolki, przełącznik | 100–150 ms |
   | menu, podpowiedź, rozwinięcie | 150–200 ms |
   | panel boczny, okno modalne | 200–300 ms |
   | przejście całego widoku | 300–500 ms |

   Dystans rośnie → czas rośnie (nie liniowo). Wyjście ok. 70–80% czasu wejścia. Powyżej 500 ms tylko dla
   rzadkich, wyróżnionych momentów.
3. **Krzywa:** wejście ease-out (szybki start, łagodne hamowanie), wyjście ease-in, ruch w obrębie ekranu
   ease-in-out. Liniowa tylko dla obrotu wskaźnika ładowania. Własna krzywa jako token, nie wartość w komponencie.
4. **Reduced motion** (`prefers-reduced-motion: reduce`): zamień ruch przestrzenny (przesunięcie, skalowanie,
   paralaksa, obrót) na przenikanie krótsze niż 150 ms albo brak; zostaw informację o zmianie (podświetlenie,
   zmiana tekstu). Ruch wywołany akcją użytkownika dotyczy SC 2.3.3 (AAA). Ruch automatyczny trwający ponad 5 s wymaga pauzy
   (SC 2.2.2), a miganie nie może przekraczać 3 razy na sekundę (SC 2.3.1) [niezweryfikowane w tej sesji].
5. **Specyfikacja:** czas, krzywa, właściwości (`transform`, `opacity`), stan początkowy i końcowy, wersja
   reduced motion. Prototyp w Figmie ≠ ruch w produkcie; ruch weryfikujesz na wdrożeniu.

## Marka
- **Dostawa od marki:** logo (pole ochronne, minimalny rozmiar), kolor główny i pomocnicze, krój, ton fotografii
  i ilustracji, zasady użycia. Brak któregoś elementu → zapisz założenie i zapytaj.
- **Konflikt marka ↔ dostępność:** dostępność wygrywa. Kolor marki za jasny na tekst → wariant do tekstu i przycisków
  o kontraście ≥ 4,5:1, kolor oryginalny na dużych powierzchniach, nagłówkach ≥ 24 px i w ilustracjach.
- **Przeniesienie marki do UI:** marka → role semantyczne (akcent, tło, powierzchnia), nie bezpośrednio do komponentów.
  Dzięki temu zmiana marki lub druga marka to wymiana wartości, nie przebudowa (ux-design-systems, motywy).
- **Czego unikać:** logo jako tła powtarzalnego wzoru za tekstem; dziesięć kolorów marki w interfejsie roboczym;
  ilustracji w innym stylu niż reszta.
