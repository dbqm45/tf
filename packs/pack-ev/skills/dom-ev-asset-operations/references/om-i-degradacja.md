# O&M, degradacja, firmware i cyberbezpieczeństwo

Spis: 1. Prewencyjne i korekcyjne · 2. Zgłoszenie serwisowe · 3. Części zamienne · 4. Analiza degradacji z telemetrii ·
5. Predictive maintenance · 6. Firmware · 7. Cyberbezpieczeństwo w cyklu życia.

## 1. Prewencyjne i korekcyjne
| Typ | Przykłady (ogólnie, wg zaleceń producenta) | Wyzwalacz w systemie |
|---|---|---|
| Prewencyjne | przegląd wizualny i elektryczny, filtry i wentylacja, chłodziwo (stacje DC chłodzone cieczą), stan kabli i złączy, dokręcenie połączeń, czyszczenie, test RCD [do weryfikacji interwały u producenta], legalizacja licznika | kalendarz lub licznik pracy (godziny, sesje, kWh) na assecie |
| Korekcyjne | wymiana modułu mocy, kabla, czytnika, terminala, naprawa złącza | zgłoszenie z alarmu lub od kierowcy |
| Wymuszone | po aktualizacji bezpieczeństwa, po zdarzeniu (uderzenie w stację, powódź, wandalizm) | ręczne zlecenie |
Interwały i zakres bierz z instrukcji producenta i umowy serwisowej; liczb nie zgadujesz. Prewencja wymaga
wyłączenia z ruchu: planuj jako `MAINTENANCE` z terminem, poza godzinami szczytu; zaplanowana konserwacja ma osobny
powód w danych, bo bywa wyłączeniem w uptime (`dom-ev-kpi-analytics`).

## 2. Zgłoszenie serwisowe
Pola: asset (stacja/EVSE/moduł), źródło (alarm, kierowca, przegląd), objaw i kod (`errorCode`, `vendorErrorCode`),
priorytet (wpływ × zasięg), SLA (czas reakcji i naprawy), przypisany wykonawca, znaczniki czasu (zgłoszenie, przyjęcie,
przyjazd, zakończenie, test sesji), użyte części (numer seryjny wymontowanej i zamontowanej), przyczyna (kod
przyczyny z katalogu), czy zgłoszenie dotyczyło gwarancji. Zamknięcie wymaga testu sesji (lub `TriggerMessage` i
statusu `Available`), a nie samej deklaracji technika. Powtórzone zgłoszenie tego samego kodu w oknie N dni to sygnał
dla przyczyny, nie nowy incydent.

## 3. Części zamienne
Stany zapasu: lokalny magazyn, centralny, u dostawcy (czas dostawy z umowy). Rekord części ma ten sam model co asset
(numer seryjny, partia, gwarancja). Reguła: części krytyczne (moduł mocy, czytnik, moduł komunikacji, kabel DC) per
model i region, zapas wyliczony z czasu dostawy i awaryjności kohorty [założenie, parametry do ustalenia]. Część
zwrócona do naprawy/RMA ma własny cykl (`IN_REPAIR`).

## 4. Analiza degradacji z telemetrii — procedura
Cel: zlokalizować ładowarki (lub moduły), które pogarszają się, zanim przerwa wpłynie na dostępność. Bez założeń o
konkretnych producentach: najpierw dane własnej floty.
1. **Kohorta.** Grupuj po (model, firmware, wiek, środowisko/lokalizacja). Porównuj stacje z kohortą, nie z wartością katalogową.
2. **Sygnały** (z `MeterValues`, `StatusNotification`, logów, zgłoszeń):
   - maksymalna moc w sesjach (percentyl 95 lub 99 mocy chwilowej przy warunkach porównywalnych: ten sam typ złącza
     i podobny SoC pojazdu, bo limit często leży po stronie auta; `dom-ev-vehicle-battery`) — trend spadkowy;
   - liczba i czas sesji zakończonych przedwcześnie (`Reason` zakończenia, `Faulted` w trakcie sesji);
   - temperatury (`measurand` temperatura, jeśli stacja je wysyła) i `HighTemperature`; zbliżanie się do limitu;
   - błędy modułów mocy: `PowerSwitchFailure`, `OverCurrentFailure`, `GroundFailure`, `UnderVoltage`/`OverVoltage`,
     `vendorErrorCode` — liczba na tydzień;
   - powtarzające się `errorCode` i `vendorErrorCode` (ten sam kod w odstępach), restarty (`BootNotification` z `reason`);
   - jakość łączności (`WeakSignal`, rozłączenia) — osobno od sprzętu;
   - błędy izolacji i uziemienia, jeśli stacja je raportuje [zależne od modelu].
3. **Okno i normalizacja.** Mediana tygodniowa; usuń sesje z ograniczeniem po stronie sieci (DLM, profile `dom-ev-smart-charging`,
   limity przyłącza `dom-ev-energy-management`), bo to nie degradacja sprzętu.
4. **Wykrycie.** Spadek względem własnej bazy sprzed N tygodni i względem kohorty (odchylenie, nie próg bezwzględny);
   alert przy odchyleniu utrzymanym przez kilka okien.
5. **Rozstrzygnięcie przyczyny.** Wspólna dla kohorty (firmware, partia, upał, zasilanie lokacji) czy jednostkowa
   (moduł, chłodzenie, kabel)? Wspólna → eskalacja do producenta i zmiana szablonu/firmware; jednostkowa → zlecenie.
6. **Wynik.** Lista stacji z priorytetem, hipotezą i kodami; zlecenie przeglądu w rejestrze; po naprawie porównanie
   „przed/po” w tych samych warunkach. Pojedyncza anomalia ≠ wniosek.
Ograniczenia: telemetria zależy od tego, co stacja wysyła (część producentów nie raportuje temperatur ani mocy modułów);
jakość danych sprawdzaj przed wnioskiem. Liczby dostępności i MTBF: `dom-ev-kpi-analytics`.

## 5. Predictive maintenance
Etapy: (1) zbiór danych: zdarzenia awarii z katalogu przyczyn + telemetria z okna przed awarią; (2) cechy: trendy
mocy, temperatur, liczby błędów, restarty, wiek, liczba cykli; (3) reguły progowe na kohorcie (zaczynaj od nich);
(4) dopiero potem model statystyczny lub ML, jeśli reguły nie wystarczają i jest dość awarii z opisaną przyczyną;
(5) ocena: ile awarii przewidziano z wyprzedzeniem, ile alarmów fałszywych, koszt przeglądu vs awarii; (6) pętla:
wynik przeglądu wraca do zbioru. Bez etykietowanych przyczyn awarii (kody przyczyny w zgłoszeniach) nie ma czego
przewidywać. Metody trenowania i ocena modelu poza zakresem skilla: opisz czynność (podział po czasie, nie losowy,
żeby uniknąć wycieku z przyszłości).

## 6. Firmware w cyklu życia
- Wersje stacji w rejestrze, katalog dopuszczonych wersji (decyzja po onboardingu: `dom-ev-charger-onboarding`).
- Wdrożenie etapami: pilotaż (jedna stacja), mała fala (np. do kilku procent kohorty), fala główna, reszta; przerwij
  przy wzroście błędów w kohorcie. Okno poza godzinami szczytu, `retries`/`retryInterval` ustawione jawnie.
- Wycofanie: wcześniej sprawdź, czy poprzednia wersja jest dostępna i czy nie ma migracji nieodwracalnej [zależne od
  producenta]. Po aktualizacji stacja zgłasza `BootNotification` (2.0.1: `reason` `FirmwareUpdate`) i nową
  `firmwareVersion`; porównaj z zleceniem (rozjazd = zdarzenie).
- Firmware metrologiczny (licznik) zmienia się z udziałem legalizacji: `dom-ev-metering-calibration`.

## 7. Cyberbezpieczeństwo w cyklu życia
- Podpisany firmware: w schemacie 2.0.1 `UpdateFirmware` niesie `firmware.signature` (Base64) i `signingCertificate`
  (PEM X.509); w schemacie 1.6 `UpdateFirmware` nie ma pól podpisu — podpisany wariant jest w rozszerzeniu
  bezpieczeństwa [do weryfikacji, poza bazą]. Wymagaj weryfikacji podpisu po stronie stacji i nie wdrażaj
  niepodpisanych obrazów. Profile bezpieczeństwa połączenia: `dom-ev-ocpp-2x`.
- Poświadczenia i certyfikaty stacji to elementy rejestru: rotacja przed wygaśnięciem, unieważnienie przy
  `DECOMMISSIONED`/RMA/kradzieży; hasła domyślne zmieniane przy `COMMISSIONING`.
- Logi bezpieczeństwa (`GetLog` `SecurityLog`) i aktualizacje łatek: polityka czasu reakcji dla podatności.
- Przepisy: NIS2 i CRA dotyczą dostawców i operatorów w określonych sytuacjach; mapa obowiązków i terminy:
  `dom-ev-regulations-eu`.
- Koniec wsparcia producenta (EOL) = ryzyko bezpieczeństwa; jest wyzwalaczem przejścia do `OBSOLETE` i planu repoweringu.
