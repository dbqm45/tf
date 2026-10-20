# Karta onboardingu typu ładowarki

Jedna karta na (producent, model, wersja firmware, wersja OCPP). Pole bez danych: „brak danych — dopytać
producenta”, nigdy puste. Wartości z dokumentacji oznacz źródłem (plik, wersja, data).

## Pola
| Grupa | Pole | Uwagi |
|---|---|---|
| Tożsamość typu | producent, model | dokładnie jak w `BootNotification` (`chargePointVendor`, `chargePointModel`) — z ramki, nie z ulotki |
| | wersja firmware | dokładny ciąg z Boot; osobna karta (lub wiersz) na każdą wersję |
| Protokół | wersja OCPP i edycja specyfikacji | np. „1.6” albo „2.0.1, edycja N” — numer edycji **[do weryfikacji]** u producenta i OCA |
| | profile/funkcje | 1.6: Core, Firmware Management, Local Auth List, Reservation, Smart Charging, Remote Trigger; deklaracja vs wynik testu |
| | znane odchylenia | odsyłacz do rejestru odchyleń |
| Bezpieczeństwo | profil bezpieczeństwa (1/2/3) | który obsługuje, który włączamy; PKI dla profilu 3 |
| | certyfikaty | kto wystawia, termin ważności, rotacja — bez kluczy w karcie |
| Struktura | liczba EVSE i złączy | typy złączy i normy CP — **dom-ev-charger-hardware** |
| | numeracja `connectorId` / EVSE | zgodność z wzorcem 1.6 / 2.0.1 |
| Moc | moc znamionowa AC/DC, kW | kW to moc, kWh to energia |
| Pomiar | licznik: producent, klasa, legalizacja | typ legalizacji i termin — **[do weryfikacji]** wg wymogów kraju; czy licznik podaje wartości w `MeterValues` i w jakich jednostkach |
| Łączność | LAN, Wi-Fi, LTE; APN, reconnect | zachowanie przy zerwaniu → test offline |
| Konfiguracja | klucze/zmienne istotne dla operatora | „klucz wg dokumentacji producenta” + nazwa z odpowiedzi stacji |
| Firmware | sposób aktualizacji (`UpdateFirmware`, lokalnie), podpis | w 2.0.1 podpisany firmware wymagany (wg `ocpp.md`) |
| Status w sieci | laboratorium / pilot / dopuszczony / wycofany | decyzja człowieka, data |

## Minimalny szkielet
```
typ: <producent> / <model> / fw <wersja>
ocpp: <wersja, edycja>   bezpieczenstwo: profil <n>
evse: <n>  zlacza: <typy>  moc: <kW>
licznik: <typ, klasa, legalizacja do ...>   lacznosc: <rodzaj>
funkcje: <profile, smart charging tak/nie>
odchylenia: <odsylacz>   status: <laboratorium|pilot|dopuszczony|wycofany>   decyzja: <kto, data>
```

## Gdy dokumentacja milczy
Zapytaj producenta pisemnie i zapisz pytanie z datą. Do odpowiedzi stosuj zachowanie zmierzone na stacji, nie
domniemane. Deklaracje zgodności nie zastępują testu (macierz: `macierz-testow.md`).
