# KPI sesji, wykorzystania i finansów

Spis: 1. Lejek sesji · 2. Utilization · 3. kWh, sesje, długość · 4. Przychód i marża · 5. MTTR, MTBF · 6. NPS · 7. Progi.

## 1. Lejek sesji i session success rate
Rozdziel etapy, każdy ma własny licznik i mianownik:
| Etap | Zdarzenie źródłowe | Wskaźnik |
|---|---|---|
| próba autoryzacji | `Authorize` (1.6), `authorizationStatus` w `TransactionEvent` (2.0.1), komenda startu z OCPI | skuteczność autoryzacji = zaakceptowane / zażądane |
| uruchomienie sesji | `StartTransaction` / `TransactionEvent` `Started` | sesje uruchomione |
| dostawa energii | energia sesji powyżej progu (np. > 0 kWh albo ≥ ustalony próg) | session success rate = z energią / uruchomione |
| zakończenie | `StopTransaction` / `Ended`, przyczyna zakończenia | sesje zakończone normalnie / uruchomione |
- **Nieudane autoryzacje liczysz osobno:** karta odrzucona to nie sesja. W mianowniku sukcesu sesji są tylko sesje
  uruchomione; inaczej odrzucone RFID obniżą wskaźnik, na który nie ma wpływu sprzęt.
- **Sesje bez energii** (0 kWh, start bez prądu, kabel zablokowany, błąd pojazdu): niepowodzenia, ale podaj przyczynę;
  „wina pojazdu” oddziel od „wina stacji”, bo raport NEVI żąda kodów błędów sesji nieudanych.
- `STOP_FAILED` (nazwa statusu operatora, nie OCPP): zakończenie nie zostało potwierdzone przez stację. Nie wrzucaj do
  sukcesu ani do porażki bez reguły; policz osobno i zapisz, czy sesja miała energię. Sesja wisząca do czasu zamknięcia
  (dom-ev-session-lifecycle, dom-ev-diagnostics) zniekształca czas trwania i utilization — wyłącz ją albo zamknij regułą.
- Sukces portu (skrypt, `ok`/`failed`) i sukces sieci liczysz z tych samych sesji; nie uśredniaj wskaźników portów.

## 2. Utilization
Trzy wersje — wybierz jedną, nazwij i nie mieszaj:
| Wersja | Licznik | Mianownik | Zastosowanie |
|---|---|---|---|
| zajętość | czas od wpięcia do wypięcia | czas dostępności portu | postój, kolejki, opłata za postój |
| ładowanie | czas z przepływem energii | czas dostępności portu | wydajność urządzenia |
| energetyczna | kWh | moc znamionowa × czas dostępności | wykorzystanie mocy |
- **Mianownik:** godziny pracy portu (nie 24 h, jeśli stacja ma godziny pracy), pomniejszone o wyłączone okresy; zapisz,
  czy przestój awaryjny zostaje w mianowniku (kara dla operatora, zgodna z surowym uptime) czy wypada (SLA).
- Jednostką jest EVSE: dwa złącza tego samego EVSE nie ładują jednocześnie, więc licz po EVSE.
- Agregacja: `sum(czas zajętości) / sum(czas dostępności)` po portach grupy, nie średnia procentów.
- Sesje przekraczające granicę okresu tnij na granicy (w strefie stacji), inaczej doby z DST i końca miesiąca kłamią.

## 3. kWh, sesje, długość
- **kWh:** źródło ustal raz. Energia z licznika sesji (MeterValues, odczyt końcowy minus początkowy) vs energia
  z CDR vs energia fakturowana; różnice uzgadnia dom-ev-cdr-settlement, legalny pomiar — dom-ev-metering-calibration.
- **Sesje na EVSE na dzień** = sesje / (EVSE × dni, w których EVSE było w eksploatacji). Port uruchomiony 20. dnia
  miesiąca ma 11 dni w mianowniku, nie 30.
- **Średnia długość sesji:** podawaj osobno czas wpięcia i czas ładowania, **medianę obok średniej**; ogon sesji
  nocnych i wiszących przesuwa średnią.
- Sesje krótkie (np. poniżej ustalonego progu energii) to najczęściej próby, nie ładowanie; oddziel w raporcie.

## 4. Przychód i marża
- **Przychód na EVSE / site** = przychód netto (bez VAT) z CDR (sesje własne) i z rozliczenia roamingu, podzielony
  przez EVSE w eksploatacji w okresie. Zapisz: data sesji (koniec) czy data faktury; waluta; korekty CDR (kredytowe)
  rozlicz w okresie korekty albo cofnij do okresu sesji — jedna zasada. CDR i korekty: dom-ev-cdr-settlement;
  składniki ceny: dom-ev-tariffs-pricing.
- **Marża na kWh** = (przychód netto − koszt energii − opłaty zmienne: roaming, płatności, ewentualnie postojowe)
  / kWh sprzedane. Koszty stałe, CAPEX, zwrot z inwestycji i opłaty za moc szczytową to ekonomia stacji (osobny temat;
  w fabryce faza 4b) — tu ich nie ma. Energię wlicz po cenie kontraktu z okresu, nie średniej z roku.
- Przychód z sesji bez energii (opłata startowa, postojowa) oznacz osobno, by nie psuć ceny za kWh.

## 5. MTTR, MTBF
- Epizod przestoju: od pierwszego zdarzenia „down” do pierwszego „up” po nim (kolejne `Faulted` bez przerwy to jeden epizod).
- **MTTR** = suma czasu przestojów / liczba epizodów (skrypt); wybierz początek: zdarzenie statusu czy zgłoszenie
  serwisowe. Rozbij: czas wykrycia, dojazd, naprawa (dane z dom-ev-asset-operations). Obok średniej podaj medianę.
- **MTBF** = czas „up” / liczba epizodów. Port bez epizodu ma MTBF nieokreślony, nie nieskończony; okres obserwacji jest
  cenzurowany (port nowy, krótkie okno). Nie porównuj MTBF portów o różnych oknach.
- Przestoje wyłączone z uptime liczą się w MTTR, jeśli licząc MTTR mierzysz czas niedostępności dla kierowcy.

## 6. NPS i oceny kierowców (krótko)
NPS = % odpowiedzi 9–10 minus % odpowiedzi 0–6 w skali 0–10. Raportuj liczbę odpowiedzi; mała próba na stację
daje szum. Ankieta po sesji udanej pomija kierowców, którym się nie udało (błąd przeżywalności): wysyłaj też po sesji
nieudanej i po nieudanej autoryzacji. Ocena w aplikacji lub sklepie to osobna miara, nie NPS.

## 7. Progi z przeglądów
Wartości typu „15–20 % utilization dla DC” z przeglądów branżowych to **[do weryfikacji]**; nie wpisuj ich jako
celu bez modelu stacji (moc, cena, koszt energii, miejsce).
