# Jakość danych zdarzeń

## Rozjazd analityki z bazą — sprawdzaj po kolei
1. **Definicja** — czy liczysz to samo: konta testowe, konta usunięte, rejestracje przez API lub import, zaproszeni
   użytkownicy.
2. **Strefa czasowa i okno** — narzędzie w UTC lub strefie projektu, baza w innej; granice miesiąca przesunięte.
3. **Źródło zdarzenia** — zdarzenie z klienta: blokery reklam, brak zgody, zamknięcie karty przed wysłaniem,
   aplikacja mobilna bez sieci. Typowo kilka do kilkunastu procent mniej niż w bazie.
4. **Tożsamość** — duplikaty po złym `identify` (jedna osoba jako dwie), scalenie dwóch osób w jedną po wspólnym
   urządzeniu.
5. **Ruch nieludzki** — boty i testy automatyczne zawyżają zdarzenia z klienta.
6. **Opóźnienie** — dane z ostatnich godzin lub dni jeszcze nie dotarły (kolejki, przetwarzanie wsadowe).
Wynik: tabela przyczyna → szacowany wpływ → jak sprawdzić → poprawka. Kluczowe fakty biznesowe przenieś na serwer.

## Testy instrumentacji
- Test e2e lub integracyjny przechwytuje wysłane zdarzenia i sprawdza nazwę i właściwości wg planu.
- Walidacja schematu (narzędzie albo własna) odrzuca lub oznacza zdarzenia spoza planu.
- Codzienny raport: liczba kluczowych zdarzeń wobec bazy, alert przy odchyleniu ponad ustalony próg.
