---
name: dom-ev-smart-charging
description: Użyj przy profilach ładowania OCPP 1.6 i 2.0.1 — SetChargingProfile, stackLevel, composite schedule, limity A i W, TxDefault offline, walidacja, RED III art. 20a.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy CSMS albo ładowarka ustawia, łączy i sprawdza limity mocy przez profile ładowania OCPP 1.6 i 2.0.1 — cele (ChargePointMax, ChargingStationMax, ExternalConstraints, TxDefault, Tx), Absolute, Relative, Recurring, stackLevel, validFrom i validTo, duration, A i W oraz fazy, composite schedule wg libocpp, SetChargingProfile, GetCompositeSchedule, ClearChargingProfile, GetChargingProfiles, NotifyChargingLimit, walidacja K01, offline i restart, minimalny prąd 6 A, test skryptem composite_schedule.py, smart charging w RED III art. 20a i AFIR. Nie do algorytmów podziału mocy, PV, magazynów, taryf dynamicznych i OSD (dom-ev-energy-management), ISO 15118 i V2G (dom-ev-charging), sprzętu CP i PWM (dom-ev-charger-hardware) ani ogólnych ramek OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x)."
  slowa: "smart charging, profil ładowania, charging profile, SetChargingProfile, GetCompositeSchedule, ClearChargingProfile, GetChargingProfiles, NotifyChargingLimit, composite schedule, stackLevel, TxDefaultProfile, TxProfile, ChargePointMaxProfile, ChargingStationMaxProfile, ExternalConstraints, limit prądu, ogranicz moc ładowarki, chargingRateUnit, chargingSchedulePeriod, recurrencyKind, validFrom, numberPhases, load management, ładowarka offline limit, bezpieczny limit, minimalny prąd 6 A, ładowanie inteligentne, RED III 20a, AFIR smart recharging, libocpp, K01"
---

# Profile ładowania OCPP — limity mocy po stronie CSMS i ładowarki

CSMS nie steruje mocą ciągłym strumieniem poleceń. Wysyła **profile ładowania** (`SetChargingProfile`), a ładowarka
sama łączy je w jeden limit w czasie (composite schedule) i stosuje go także bez łączności. Skill opisuje, jak ten
limit powstaje i jak go sprawdzić. Ramki, `BootNotification` i transakcje: **dom-ev-ocpp-16**, **dom-ev-ocpp-2x**.
Kto i ile mocy dostaje (podział przyłącza, PV, magazyn, taryfy): **dom-ev-energy-management**.

## Procedura: od potrzeby do limitu na ładowarce
1. **Wybierz cel** (tabela niżej): sufit stacji, domyślny limit dla przyszłych sesji czy limit trwającej sesji.
2. **Wybierz rodzaj i czas**: `Absolute` (od `startSchedule`), `Relative` (od startu transakcji), `Recurring`
   (`Daily` albo `Weekly`). Ustaw `stackLevel`, `validFrom`/`validTo` i `duration`.
3. **Zapisz limity** w jednej jednostce (`A` albo `W`) z `numberPhases`; pierwszy `startPeriod` to 0.
4. **Zwaliduj lokalnie** i policz wynik: `composite_schedule.py` (sekcja „Testowanie”). Kod 1 = profil odrzucony.
5. **Wyślij**, sprawdź odpowiedź (`Accepted`/`Rejected`), potem `GetCompositeSchedule` — to ładowarka mówi, co
   obowiązuje. Odpowiedź `Accepted` nie oznacza, że pojazd pobiera tyle prądu.
6. **Zaplanuj brak łączności**: zainstaluj `TxDefaultProfile` jako bezpieczny limit.

## Cele profili (purpose)
| Cel | OCPP 1.6 | OCPP 2.0.1 | Zasięg (`connectorId` / `evseId`) | Działa |
|---|---|---|---|---|
| Sufit stacji | `ChargePointMaxProfile` | `ChargingStationMaxProfile` | 0 = cała stacja (2.0.1: tylko 0) | stale, niezależnie od sesji |
| Limit z zewnątrz | — | `ChargingStationExternalConstraints` | 0 = cała stacja | stale; ustawia lokalny EMS, nie CSMS |
| Domyślny limit sesji | `TxDefaultProfile` | `TxDefaultProfile` | 0 = każde złącze/EVSE osobno | od startu kolejnej transakcji |
| Limit trwającej sesji | `TxProfile` (`transactionId`) | `TxProfile` (`transactionId`, `evseId` > 0) | złącze/EVSE z sesją | tylko ta transakcja |

`ExternalConstraints` ustawia lokalny system (EMS, operator sieci); `NotifyChargingLimit` informuje o tym CSMS.

## Rodzaje, czas i jednostki
| Pole | Zasada |
|---|---|
| `Absolute` | wymaga `startSchedule`; okres liczy się od niego |
| `Relative` | **bez** `startSchedule`; początek = start transakcji (bez niej libocpp bierze początek okna) |
| `Recurring` | wymaga `recurrencyKind`; `startSchedule` powtarza się co dobę albo tydzień, także wstecz |
| `stackLevel` | wyższy wygrywa w obrębie tego samego celu; najniższy = 0 |
| `validFrom`/`validTo` | okno ważności profilu; poza nim profil nie istnieje dla wyniku |
| `duration` (s) | po nim profil w tym przebiegu wygasa; brak = ostatni okres trwa bez końca (TxProfile: do końca transakcji) |
| `chargingSchedulePeriod` | `startPeriod` rosnące od 0, `limit`, `numberPhases` (domyślnie 3) |
| `limit` | jedna cyfra po przecinku |
| `phaseToUse` (2.0.1) | tylko przy `numberPhases` = 1 i stacji z przełączaniem faz (`ACPhaseSwitchingSupported`) |
| `chargingRateUnit` | `A` albo `W`; stacja musi obsługiwać daną jednostkę |

Przeliczenie: **W = A × napięcie fazowe × liczba faz**. 11 kW na 3 fazach 230 V to 11000 / (230 × 3) = 15,9 A
(zaokrąglaj w dół, by nie przekroczyć limitu **[założenie]**). Zawsze podawaj `numberPhases`.

## Composite schedule: jak ładowarka łączy profile
Reguły z libocpp (implementacja referencyjna, nie specyfikacja OCA; szczegóły i przypadki brzegowe:
`references/composite-schedule-libocpp.md`):
1. Profile dzielą się na grupy: `Max`, `ExternalConstraints` (2.0.1), `TxDefault`, `Tx`.
2. W grupie, w każdej chwili, obowiązuje aktywny profil o **najwyższym** `stackLevel`.
3. Limit bazowy: `Tx`, a gdy go brak — `TxDefault`, a gdy go brak — **limit domyślny**.
4. Wynik to minimum z limitu bazowego i `Max` (oraz `ExternalConstraints`). Wynik nigdy nie przekracza `Max`.

**Niespójność dokumentacji libocpp — limit domyślny.** Sekcja „Default limit” notatki
`smart_charging_profiles.md` podaje **48 A**, gdy limit jest nieznany. Sekcja „No valid profiles” tej samej notatki
pokazuje odpowiedź z `limit: 0.0` (brak ładowania), a test `NoSchedulesPresent` oczekuje wartości z konfiguracji
z zapasową stałą. Źródła nie rozstrzygają, co robi dany build **[do weryfikacji na swojej ładowarce]**. Dla CSMS:
nie polegaj na żadnej z wartości, zainstaluj `TxDefaultProfile` o niskim `stackLevel` jako jawny limit domyślny.
Skrypt ma `--default-limit 48` (wg opisu) albo `0`.

## Komunikaty (pola dokładniej: `references/komunikaty-i-pola.md`)
| Komunikat | Kierunek | Sedno |
|---|---|---|
| `SetChargingProfile` | CSMS → stacja | 1.6: `connectorId` + `csChargingProfiles`; 2.0.1: `evseId` + `chargingProfile` (`id`, `chargingSchedule` jako lista 1–3) |
| `GetCompositeSchedule` | CSMS → stacja | okno `duration` s, opcjonalnie `chargingRateUnit`; odpowiedź z listą okresów |
| `ClearChargingProfile` | CSMS → stacja | kasuje po `id` lub kryteriach; `Accepted`/`Unknown` **[do weryfikacji w spec]** |
| `GetChargingProfiles` (2.0.1) | CSMS → stacja | stacja odpowiada `Accepted`/`NoProfiles`, potem `ReportChargingProfiles` |
| `NotifyChargingLimit` (2.0.1) | stacja → CSMS | `chargingLimit.chargingLimitSource` (`EMS`, `Other`, `SO`, `CSO`), `isGridCritical` |

Odpowiedź `GetCompositeSchedule`: `status` `Accepted`/`Rejected` (2.0.1 dodaje `statusInfo`); `evseId` = 0 w 2.0.1
to oczekiwany pobór całej stacji.

## Walidacja (reguły K01 z libocpp)
Stacja odpowiada `Rejected`, gdy m.in.: pierwszy `startPeriod` ≠ 0 albo okresy nie rosną; `Absolute`/`Recurring` bez
`startSchedule`; `Relative` z `startSchedule`; sufit stacji jako `Relative` lub z `evseId` > 0; `TxProfile` bez
`transactionId`, bez aktywnej transakcji lub z `evseId` = 0; dwa `TxProfile` o tym samym `stackLevel` w jednej
transakcji; nieobsługiwana jednostka. Pełna tabela z numerami: `references/walidacja-k01.md`.

## Offline, restart i bezpieczny limit
- Ładowarka stosuje zapisane profile bez łączności z CSMS; nowego limitu w tym czasie nie dostanie. Jedyna
  gwarancja bezpiecznego limitu offline to profil **zainstalowany wcześniej**.
- `TxDefaultProfile` (i sufit stacji) obowiązują także dla sesji startowanych offline, bo nie wymagają
  `transactionId`. `TxProfile` dotyczy konkretnej transakcji CSMS i znika z nią **[do weryfikacji w spec]**.
- Po restarcie stacja powinna odtworzyć profile z pamięci trwałej (libocpp trzyma je w bazie sqlite) **[do weryfikacji
  na ładowarce]**. Po `BootNotification` odczytaj stan: `GetCompositeSchedule` (1.6, 2.0.1) i `GetChargingProfiles`
  (2.0.1), porównaj z oczekiwanym i wyślij brakujące profile.
- Limit offline dobierz tak, by suma limitów wszystkich stacji na przyłączu mieściła się w jego mocy, gdy żadna
  nie ma łączności (obliczenie: dom-ev-energy-management). Zegar stacji synchronizuj z `currentTime` z `BootNotification`.

## Minimalny prąd i rzeczywisty pobór
- Limit poniżej **6 A** (10 % PWM) pojazd traktuje jak brak zgody na ładowanie; stacja zwykle wstrzymuje wtedy
  ładowanie (`SuspendedEVSE`). Szczegóły PWM: **dom-ev-charger-hardware**. Planista powinien przydzielać 0 albo
  co najmniej 6 A, nie wartości pośrednie. `minChargingRate` w schemacie to minimum pojazdu, nie stacji.
- Profil to **sufit**, nie wartość zadana: pojazd często pobiera mniej. Prawdziwy pobór czytaj z `MeterValues`
  (`Current.Import`, `Power.Active.Import`); suma limitów nie mówi, ile przyłącze obciążono.

## Przykład: zajezdnia 63 A i profile na EVSE
Zajezdnia z `examples/depot-smart-charging/`: przyłącze 63 A (3 fazy, 230 V), cztery pojazdy. CSMS planuje prąd co
15 minut i wysyła `TxProfile` (`Absolute`, `stackLevel` 0), a stacji daje `ChargePointMaxProfile` 63 A jako bezpiecznik.
Profil EVSE-1 (30 kWh do 22:00, maks. 32 A): `0 s: 32 A`, `4500 s: 13,9 A`, `5400 s: 6 A`, `6300 s: 0 A`.
```bash
python3 .claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py <profil>.json \
  --start 2026-10-20T18:00:00Z --duration 14400
```
Wynik (kod 0): 32,0 A, 13,9 A od +4500 s, 6,0 A od +5400 s, 0 A od +6300 s, wszystko ze `TxProfile#1001`, bo sufit
stacji jest wyższy. Z błędem w profilu (pierwszy `startPeriod` = 10) skrypt zwróci kod 1 i pominie go; stacja
odpowiedziałaby `Rejected`, a pojazd zostałby bez limitu od CSMS. EVSE-4 (60 kWh w 2 h przy 16 A) dostanie ok. 22 kWh:
CSMS ma to zgłosić dyspozytorowi. Drugi przykład (sufit 11 kW w `W` kontra `TxDefault` 16 A daje 15,9 A):
`references/testowanie-i-prawo.md`.

## Testowanie
- **Skrypt** `.claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py <profil>.json --start <ISO>
  --duration <s> [--tx-start <ISO>] [--unit A|W] [--default-limit 48] [--voltage 230] [--json]`. Uruchom go; jego
  kod czytaj tak: 0 policzone, 1 profil odrzucony, 2 błąd wejścia. Sieć: brak. Skrypt odwzorowuje reguły libocpp,
  więc zgodność z konkretną ładowarką sprawdź `GetCompositeSchedule` na stacji.
- **Symulator** stacji i ramki `SetChargingProfile`/`GetCompositeSchedule`: **dom-ev-simulation-testing**. Przypadki
  testowe po zmianie firmware: `references/testowanie-i-prawo.md`.

## Wymogi prawne (UE)
- **AFIR** (UE) 2023/1804, Art. 5 ust. 8: publiczne punkty zbudowane po 13.04.2024 lub odnowione po 14.10.2024 mają
  być zdolne do smart recharging (definicja: Art. 2 pkt 65 — natężenie regulowane w czasie rzeczywistym na podstawie
  informacji przesyłanych elektronicznie).
- **RED III** (UE) 2023/2413, Art. 20a ust. 4: nowe i wymieniane normalne punkty niepubliczne mają obsługiwać smart
  recharging; transpozycja do 21.05.2025. Przepisy nie wskazują protokołu; profile OCPP to typowa realizacja
  **[wniosek, nie cytat]**. Brzmienie, numery linii, nieścisłe odesłanie do AFIR Art. 15: `references/testowanie-i-prawo.md`;
  mapa obowiązków: **dom-ev-regulations-eu**, **dom-ev-regulations-pl**.

## Pułapki
| Błąd | Skutek |
|---|---|
| Brak `TxDefaultProfile` | limit domyślny jest nieznany (0 albo 48 A) |
| `TxProfile` ze starym `transactionId` | `Rejected`; po restarcie CSMS id nie pasuje |
| Dwa profile o tym samym celu i `stackLevel` | wynik zależy od stacji; może być `Rejected` |
| Limit w `W` bez `numberPhases` | stacja zakłada 3 fazy; pojazd 1-fazowy dostaje za mało |
| Limit 1-5 A | pojazd nie ładuje; użyj 0 albo ≥ 6 A |
| `Accepted` uznane za działający limit | sprawdź `GetCompositeSchedule` i `MeterValues` |

## Checklista
- [ ] Cel, rodzaj, `stackLevel`, czas i `numberPhases` wybrane świadomie; pierwszy `startPeriod` = 0; limity 0 albo ≥ 6 A.
- [ ] `composite_schedule.py` zwraca 0, a `GetCompositeSchedule` na stacji zgadza się ze skryptem.
- [ ] `TxDefaultProfile` zainstalowany; test odcięcia łączności wykonany.
- [ ] Po restarcie profile odtworzone albo wysłane ponownie po `BootNotification`.
- [ ] Rzeczywisty pobór mierzony z `MeterValues`, nie zakładany z profilu.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/composite-schedule-libocpp.md` | liczysz wynik ręcznie, spór o limit domyślny, `validFrom`/`validTo`, `Recurring` z `duration` |
| `references/komunikaty-i-pola.md` | budujesz lub parsujesz ramki profili (pola ze schematów 1.6 i 2.0.1) |
| `references/walidacja-k01.md` | stacja zwraca `Rejected` albo piszesz walidację w CSMS |
| `references/testowanie-i-prawo.md` | drugi przykład z liczbami, scenariusze testowe, brzmienie przepisów z artykułem |

## Źródła
- EVerest libocpp (Apache 2.0, ranga W): `doc/common/smart_charging_profiles.md`, `doc/v2/ocpp_201_smart_charging_in_depth.md`,
  `tests/lib/ocpp/v16/test_composite_schedule.cpp`, github.com/EVerest/libocpp, pobrane 2026-10-20.
- Schematy JSON OCPP 1.6 i 2.0.1, github.com/mobilityhouse/ocpp, pobrane 2026-10-20.
- AFIR (UE) 2023/1804, Art. 2 pkt 65 i Art. 5 ust. 7-10, eur-lex.europa.eu/eli/reg/2023/1804/oj, pobrane 2026-10-20.
- RED III (UE) 2023/2413, pkt 14m i Art. 20a, eur-lex.europa.eu/eli/dir/2023/2413/oj, pobrane 2026-10-20.
- Przykład: `examples/depot-smart-charging/`. Specyfikacji OCPP (OCA) nie ma w bazie; miejsca z **[do weryfikacji]**
  sprawdź w niej. Linie w plikach bazy: `references/`.
