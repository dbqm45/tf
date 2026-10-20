# PV, magazyn energii, taryfy dynamiczne i sygnały OSD

## 1. Punkt pomiaru i bilans
Limit przyłącza dotyczy **punktu przyłączenia (licznik OSD)**. Bilans na każdej fazie:
`pobór z sieci = budynek + EV + ładowanie BESS − PV − rozładowanie BESS`. Mierz w punkcie przyłączenia (licznik lub przekładniki
tam), nie sumuj szacunków z urządzeń. Pamiętaj o kierunku: nadwyżka PV oddawana do sieci też jest ograniczona umową [do weryfikacji].

## 2. PV
- **Nadwyżka PV** = produkcja − budynek. Ładuj z nadwyżki tylko wtedy, gdy przekracza minimum: 1,38 kW (1 faza, 6 A)
  albo 4,14 kW (3 fazy, 6 A). Niżej nie ma ładowania, tylko pobór z sieci.
- Zmiany chmur: filtruj pomiar (średnia z kilkudziesięciu sekund [założenie]) i stosuj histerezę, żeby nie przełączać
  co kilka sekund; pojazd i stacja mają czas reakcji.
- PV **nie zmniejsza limitu przyłącza** w obliczeniach bezpieczeństwa: o 16:00 chmura zabiera 40 kWp w sekundy. Limit liczysz tak,
  jakby PV nie było, a nadwyżkę traktujesz jako bonus (tańsza energia, mniej poboru).
- Tryby: tylko nadwyżka, nadwyżka + minimum z sieci (np. 6 A do terminu), pełna moc.

## 3. Magazyn energii (BESS)
- **Peak shaving:** magazyn pokrywa szczyt ponad moc umowną lub limit przyłącza. Moc szczytowa = limit przyłącza + moc falownika BESS
  (przy SoC > rezerwa).
- Zostaw rezerwę SoC na zanik sieci lub na priorytetowe ładowanie; nie zakładaj, że magazyn jest zawsze pełny.
- Ograniczenia: moc falownika, SoC min/max, sprawność cyklu, degradacja. Koszt cyklu wlicz w arbitraż cenowy.
- Sterowanie magazynem jest osobną pętlą w EMS; CSMS dostaje z niej „dostępną moc dla EV”, nie steruje falownikiem.

## 4. Ceny energii
- Plan kosztowy: dla każdego pojazdu wybierz najtańsze sloty przed odjazdem, przy czym **wykonalność terminu ma pierwszeństwo przed ceną**
  (najpierw sprawdź, czy da się naładować pod limit, dopiero potem przesuwaj w tanie sloty).
- Dane: ceny dzień-przód (godzinowe lub 15-minutowe), taryfy strefowe OSD (G12, C12 itp. [do weryfikacji]), udział OZE i emisyjność
  sieci co ≤ 1 h (RED III art. 20a ust. 1–2). Opłaty mocowe i dystrybucyjne zależą od mocy szczytowej — peak shaving obniża koszt.
- Zmiana ceny w ostatniej chwili: przelicz plan na następne N slotów; nie zmieniaj profilu aktywnej sesji częściej niż potrzeba.
- Cena dla kierowcy (taryfa OCPI, ceny dynamiczne w CDR) → dom-ev-tariffs-pricing; tu liczysz **koszt energii operatora**.

## 5. Sygnały OSD i elastyczność
Tylko role i nazwy; szczegóły protokołów [do weryfikacji] — nie ma ich w bazie wiedzy fabryki.
| Nazwa | Rola |
|---|---|
| OpenADR | sygnały demand response (zdarzenia, ceny, limity) od operatora/agregatora do VEN u odbiorcy [do weryfikacji] |
| IEEE 2030.5 | protokół zasobów rozproszonych (DER) i DR, popularny w USA [do weryfikacji] |
| EEBUS | komunikacja pomiędzy urządzeniami a zarządzaniem energią w budynku, m.in. limity mocy z sieci [do weryfikacji] |
| OCPP | `NotifyChargingLimit`, `ChargingStationExternalConstraints` — jak limit trafia do CSMS i stacji (architektura-odpornosc.md) |

Zasada: sygnał OSD zamień na **limit w amperach lub kW na okres**, dodaj do wspólnego rachunku jako kolejne ograniczenie
(minimum ze wszystkich) i zapisz źródło (`SO`, `EMS`). Sygnał krytyczny dla sieci (`isGridCritical`) ma pierwszeństwo przed cenami i terminami floty.
Uczestnictwo w rynku elastyczności i agregacja: RED III art. 20a ust. 5 — przepisy krajowe [do weryfikacji].
