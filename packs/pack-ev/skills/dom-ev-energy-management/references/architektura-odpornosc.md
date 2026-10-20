# Gdzie liczyć i jak przetrwać awarię

## 1. Trzy miejsca obliczeń
| Miejsce | Zalety | Wady |
|---|---|---|
| **CSMS** (chmura) | jedna logika dla wielu lokacji, widok floty, ceny i terminy z systemów biznesowych | opóźnienie, zależność od łącza, pomiar budynku trzeba dostarczyć |
| **Lokalny kontroler** (EMS/DLM na miejscu) | bliski pomiar (sekundy), działa offline, zna PV i magazyn | kolejny sprzęt i firmware, własny rejestr zdarzeń |
| **Ładowarka** (master–slave w jednym urządzeniu) | brak dodatkowego kontrolera, szybka reakcja | zwykle tylko grupa jednego producenta, brak terminów i cen |

## 2. Wybór
- Jedna lokacja, jeden producent, pomiar budynku → DLM w ładowarce-masterze lub lokalnym kontrolerze.
- Wielu producentów, PV, magazyn, sygnały OSD → lokalny kontroler jako pierwsza linia i CSMS jako warstwa planowania.
- Zajezdnia z harmonogramem → **podział warstw**: CSMS planuje (terminy, SoC, ceny) i wysyła profile, a lokalny kontroler
  pilnuje limitu w czasie rzeczywistym i obcina, gdy plan przekracza limit.
- Reguła: sekundy → lokalnie, minuty i godziny → CSMS. Decyzje bezpieczeństwa instalacji nigdy nie zależą od chmury.

## 3. Odporność
| Awaria | Zachowanie |
|---|---|
| Brak łącza stacja ↔ CSMS | stacja działa na `TxDefaultProfile` / `ChargePointMaxProfile` obliczonym tak, by **suma domyślnych limitów ≤ limit przyłącza** (limit ÷ liczba stacji, ≥ 6 A albo 0) |
| Brak łącza kontroler ↔ stacja | stacja wraca do limitu domyślnego po upływie czasu ważności (`duration`, `validTo`) ostatniego profilu — **ustaw krótką ważność** profilów dynamicznych |
| Pomiar budynku nieaktualny (brak próbki > T) | kontroler przechodzi na limit fail-safe: założenie najgorszego poboru budynku, np. limit przyłącza minus pobór szczytowy |
| Restart kontrolera | stan startowy = limit fail-safe, nie „ostatni”; dopiero po pierwszym pomiarze podnoś |
| Magazyn lub PV niedostępne | licz limit bez nich |
| Rozjazd zegarów | planuj względnie (`Relative`), mierz czas na kontrolerze; w OCPP synchronizuj czas z `BootNotification`/`Heartbeat` |

Zasady: limit fail-safe jest **zapisany w stacji** (profil trwały lub konfiguracja), nie tylko w pamięci kontrolera; obcinaj szybko,
podnoś wolno (histereza, np. min. kilkadziesiąt sekund między podwyżkami [założenie]); loguj każde obcięcie z przyczyną. Limit „ostatni znany” po
zaniku łącza nie jest bezpieczny: zmienił się budynek, a stacja o tym nie wie.

## 4. Sygnały i limity z zewnątrz w OCPP
- Profil o celu `ChargingStationExternalConstraints` (OCPP 2.0.1) łączy się w composite schedule razem z Max, TxDefault i Tx
  (libocpp, K08). Przeznaczenie: limit narzucony przez zewnętrzny system (EMS, OSD); kto go ustawia i jak rozstrzygać kolizje
  z CSMS — [do weryfikacji w specyfikacji OCA; w bazie tylko libocpp].
- `NotifyChargingLimit` (2.0.1): stacja informuje CSMS o zewnętrznym limicie. Pole `chargingLimitSource` ma wartości
  `EMS`, `Other`, `SO`, `CSO`; `isGridCritical` (boolean) mówi, czy limit jest krytyczny dla sieci (schemat ocpp-json-schemas).
  W OCPP 1.6 takiego komunikatu nie ma [do weryfikacji] — limit z lokalnego kontrolera jest tam widoczny tylko pośrednio
  (niższy composite schedule, MeterValues).
- Składanie profili, `stackLevel`, `GetCompositeSchedule`: dom-ev-smart-charging.
- Architektura bramy OCPP i skalowanie CSMS: dom-ev-cpms-architecture.
