---
name: dom-ev-v2x
description: Użyj przy ładowaniu dwukierunkowym EV — V2G, V2H, V2B, V2L, BPT w ISO 15118-20, ujemne limity w OCPP, rozliczenie energii oddanej, zgoda kierowcy, minimalny SoC.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy pojazd ma oddawać energię z baterii — różnice V2G, V2H, V2B i V2L (kto odbiera energię, czy jest synchronizacja z siecią), BPT w ISO 15118-20 (usługi AC_BPT i DC_BPT, tryb scheduled i dynamic, parametry rozładowania wg implementacji josev), wymagania wobec ładowarki (DC dwukierunkowa, falownik, kod sieci, zgoda OSD), OCPP 2.0.1 a 2.1 i ujemne limity w profilach, RED III art. 20a, rozliczenie energii oddanej (licznik dwukierunkowy, eksport, CDR), zgoda kierowcy, minimalny SoC, gwarancja i degradacja baterii, modele biznesowe (agregator, arbitraż, usługi elastyczności). Nie do jednokierunkowych profili ładowania (dom-ev-smart-charging), mocy lokacji, PV i magazynu (dom-ev-energy-management), ISO 15118 ogólnie i Plug & Charge (dom-ev-iso15118), baterii jako takiej (dom-ev-vehicle-battery)."
  slowa: "V2G, V2H, V2B, V2L, V2X, vehicle to grid, vehicle to home, vehicle to building, vehicle to load, ładowanie dwukierunkowe, bidirectional charging, BPT, bidirectional power transfer, rozładowanie auta, oddawanie energii do sieci, zasilanie domu z auta, zasilanie z baterii auta, falownik, grid-forming, grid-following, kod sieci, grid code, DC_BPT, AC_BPT, EVMaximumDischargePower, ujemny limit, ujemna moc, negative charging profile, Energy.Active.Export.Register, energia oddana, licznik dwukierunkowy, agregator, arbitraż cenowy, minimalny SoC, gwarancja baterii, degradacja baterii, CHAdeMO V2G, ładowarka dwukierunkowa"
---

# Ładowanie dwukierunkowe (V2X) z perspektywy software

Skill porządkuje pojęcia V2X, mapuje BPT z ISO 15118-20 na pola z kodu i wskazuje zmiany w OCPP, rozliczeniu
i zgodach. Pewność: BPT opisuje **implementacja josev** (ranga W, nie norma), RED III
tekst dyrektywy (ranga P). Norm ISO 15118, IEC 61851 i OCPP 2.1 nie ma w bazie — to, co od nich zależy, jest
oznaczone [do weryfikacji].

## 1. Warianty V2X — pytaj o odbiorcę i o sieć
| Wariant | Odbiorca energii | Sieć publiczna | Co musi umieć układ |
|---|---|---|---|
| **V2G** (grid) | sieć dystrybucyjna, rynek | tak, praca równoległa | synchronizacja z siecią, zgodność z kodem sieci, zgoda OSD [do weryfikacji] |
| **V2H** (home) | instalacja domu | zwykle tak (nadwyżka mniejsza od poboru); w trybie awaryjnym może być odcięta | przy awarii sieci: wyspa i tryb grid-forming |
| **V2B** (building) | budynek, biuro, flota | jak V2H, w skali budynku | sterowanie szczytem i mocą umowną (dom-ev-energy-management) |
| **V2L** (load) | wtyczka w aucie lub adapterze | nie — urządzenia podłączone bezpośrednio | brak protokołu do CSMS, bez synchronizacji |

- Granica: **czy energia przechodzi przez licznik przyłącza do sieci.** Tak → V2G, wymogi sieciowe i rozliczenie
  eksportu. Nie → V2H, V2B, V2L: zwykle lżejsze wymogi, ale ochrona przed wsteczną pracą wyspy dalej obowiązuje.
- V2H i V2B bywają „V2G bez eksportu” (zero-export). Zero-export wymaga pomiaru na przyłączu, nie w aucie.
- V2L nie jest funkcją ładowarki: CSMS go nie widzi, nie planuj dla niego sesji OCPP.
- W DC falownik jest w ładowarce (auto oddaje prąd stały). W AC falownik jest w aucie i ładowarka tylko przełącza
  oraz mierzy; sieć „widzi” auto jako źródło. To zmienia, kto odpowiada za certyfikację przyłączeniową [do weryfikacji].

## 2. BPT w ISO 15118-20 (wg implementacji josev)
Usługi: w josev `ServiceV20` ma `AC_BPT = 5`, `DC_BPT = 6`, `DC_ACDP_BPT = 7` obok jednokierunkowych `AC = 1`, `DC = 2`.
Pojazd i ładowarka wybierają usługę w `ServiceDetail`/`ServiceSelection`; parametry usługi BPT to m.in. `ControlMode`,
`MobilityNeedsMode`, `BPTChannel` (`UNIFIED`, `SEPARATED`), `GeneratorMode` (`GRID_FOLLOWING`, `GRID_FORMING`)
i `GridCodeIslandingDetectionMethod` (`ACTIVE`, `PASSIVE`).

| Etap | Jednokierunkowo | BPT (nazwy z josev) |
|---|---|---|
| Parametry stron | `DC_CPDReqEnergyTransferMode` | `BPT_DC_CPDReqEnergyTransferMode`, `BPT_DC_CPDResEnergyTransferMode`; AC: `BPT_AC_…` |
| Moc rozładowania pojazdu | — | `EVMaximumDischargePower`, `EVMinimumDischargePower`, `EVMaximumDischargeCurrent`, `EVMinimumDischargeCurrent` |
| Moc rozładowania stacji | — | `EVSEMaximumDischargePower`, `EVSEMinimumDischargePower`, `EVSEMaximumDischargeCurrent`, `EVSEMinimumDischargeCurrent` |
| Pętla — scheduled | `Scheduled_DC_CLReqControlMode` | `BPT_Scheduled_DC_CLReqControlMode` / `…ResControlMode` |
| Pętla — dynamic | `Dynamic_DC_CLReqControlMode` | `BPT_Dynamic_DC_CLReqControlMode` / `…ResControlMode` |
| Energia V2X | — | `EVMaximumV2XEnergyRequest`, `EVMinimumV2XEnergyRequest` (w josev tylko oba naraz) |
| Kanał | — | `PowerDeliveryReq.BPT_ChannelSelection` = `Charge` albo `Discharge` |

Reguły z kodu josev: w odpowiedzi/żądaniu ma być ustawione **dokładnie jedno** z pól jednokierunkowego lub BPT
(`one_field_must_be_set`); `MinimumSOC` nie może przekraczać `TargetSOC` (odwołanie [V2G20-1640] w komentarzu);
`DepartureTime`, `MinimumSOC`, `TargetSOC` jadą w `ScheduleExchange`. Moc w `DischargingSchedule` ma być ujemna —
w josev jest to tylko TODO bez walidatora, więc sprawdź to sam.

**Scheduled a dynamic.** W trybie *scheduled* ładowarka (SECC) wysyła `ScheduleTuple` (do 3 w josev), każda krotka ma
`ChargingSchedule` i opcjonalnie `DischargingSchedule` z `PowerSchedule` oraz cenami; auto wybiera krotkę
i podąża za harmonogramem. W trybie *dynamic* auto podaje potrzeby (`DepartureTime`, `MinimumSOC`, `TargetSOC`,
`EVTargetEnergyRequest`, `EVMaximumEnergyRequest`, `EVMinimumEnergyRequest`, energię V2X), a SECC steruje w pętli
`ChargeLoop` aktualnym limitem mocy (też rozładowania). Dynamic daje reakcję w sekundach (usługi sieciowe), scheduled — działa przy słabej łączności z backendem. Pełna tabela pól i fragmenty: `references/bpt-iso15118-20.md`.

Obowiązki pojazdu w normie (np. czy auto wystawia usługę BPT) i numery wymagań spoza kodu: [do weryfikacji].

## 3. Wymagania po stronie ładowarki i sieci
| Wymóg | Wniosek dla projektu |
|---|---|
| DC dwukierunkowa | moduły mocy wsteczne, falownik sieciowy w ładowarce, pomiar po obu stronach |
| Falownik i kod sieci | zgodność z kodem sieci i krajowymi wymogami przyłączeniowymi OSD [do weryfikacji] |
| Ochrona przed pracą wyspową | `GridCodeIslandingDetectionMethod` (ACTIVE/PASSIVE) to parametr usługi w ISO 15118-20 |
| Tryb awaryjny V2H | `GeneratorMode` = `GRID_FORMING` (stacja tworzy wyspę) vs `GRID_FOLLOWING` (idzie za siecią) |
| Zgoda i zgłoszenie do OSD | procedura zależy od kraju i mocy; w Polsce [do weryfikacji] — poza bazą |
| CHAdeMO | historyczna droga V2G (japońskie auta, V2X przez CHAdeMO) [do weryfikacji]; nowe projekty idą w ISO 15118-20 |

CSMS nie zastąpi sprzętu: gdy ładowarka nie ma certyfikacji dwukierunkowej, `SetChargingProfile` z ujemnym limitem
musi zostać odrzucony. Wprowadzenie takiej stacji: dom-ev-charger-onboarding; sprzęt: dom-ev-charger-hardware.

## 4. OCPP
| Wersja | V2X |
|---|---|
| 1.6 | brak; limit nieujemny |
| 2.0.1 | brak pełnego V2X. Schemat `ChargingSchedulePeriod.limit` to `number` bez `minimum` (ocpp-json-schemas, v201 SetChargingProfileRequest, L379–394), ale znaczenie ujemnej wartości zależy od specyfikacji OCA [do weryfikacji] |
| 2.1 | dodaje V2X i DER (zarządzanie źródłami rozproszonymi), w tym rozładowanie [do weryfikacji] — specyfikacji 2.1 nie ma w bazie |

Ujemny limit w profilu = polecenie oddawania mocy (przy założeniu, że stacja i auto to obsługują). Zasady przy
wdrożeniu: sprawdź capability stacji przed wysłaniem, waliduj znak limitu po stronie CSMS, loguj `chargingRateUnit`,
nie mieszaj z limitami przyłącza (limit eksportu jest osobnym ograniczeniem). Składanie profili: dom-ev-smart-charging;
różnice wersji i `NotifyEVChargingNeeds`: dom-ev-ocpp-2x; rola ISO 15118 w stosie: dom-ev-iso15118.

## 5. Prawo UE
RED III (dyrektywa 2023/2413) **art. 20a ust. 4**: państwa członkowskie zapewniają, że nowe i wymieniane
**niepubliczne** normalne punkty ładowania mogą obsługiwać smart recharging, w stosownych przypadkach interfejs
z inteligentnym licznikiem i **funkcje ładowania dwukierunkowego** zgodnie z art. 15 ust. 3 i 4 rozporządzenia
2023/1804 (AFIR) (`eu-red-iii`, doc.txt L2924–2985). Odesłanie do AFIR nie pasuje do tekstu AFIR z 2026-01-08
(zob. dom-ev-energy-management) — nie wyprowadzaj z niego dodatkowych obowiązków. **Art. 20a ust. 3**: producenci
aut udostępniają SoC, SoH, power set point, pojemność i lokalizację w czasie rzeczywistym właścicielowi i stronom
trzecim działającym w jego imieniu. **Ust. 5**: prawo krajowe dopuszcza małe i mobilne zasoby (w tym EV) do rynków,
także przez agregację. Mapa terminów i transpozycja w PL: dom-ev-regulations-eu, dom-ev-regulations-pl.

## 6. Rozliczenie energii oddanej
- Licznik musi mierzyć **oba kierunki** osobno; jeden rejestr netto nie pozwala rozliczyć przepływów po różnych cenach.
- OCPP: dla energii oddanej oczekuj measurandu `Energy.Active.Export.Register` obok `…Import.Register` w `MeterValues`
  (enumeracja measurandów w schematach 1.6 i 2.0.1, ocpp-json-schemas doc.txt L1089+, L1456+).
- OCPI nie ma osobnego pola energii oddanej. `total_energy` w CDR jest pojedynczą liczbą, więc eksport wymaga
  umowy między stronami (osobny CDR, rozszerzenie lub kanał poza OCPI) [do weryfikacji]. CDR/korekty: dom-ev-cdr-settlement.
- Licznik pod rozliczenia prawne: dom-ev-metering-calibration (MID, OCMF; reguły dla energii oddanej [do weryfikacji]).
- Cena kupna i sprzedaży to dwie taryfy; taryfy OCPI opisują cenę dla kierowcy, nie wynagrodzenie za eksport
  (dom-ev-tariffs-pricing). Podatki od energii sprzedanej do sieci: [do weryfikacji].

## 7. Kierowca i bateria
- **Zgoda kierowcy** na rozładowanie jest warunkiem oddzielnym od zgody na ładowanie: zapisz kto, kiedy, na jaki
  zakres (okno, moc, minimalny SoC), możliwość wycofania.
- **Minimalny SoC i odjazd:** `DepartureTime` i `MinimumSOC` w ISO 15118-20 wyrażają potrzeby auta. Nie sprzedawaj
  mocy poniżej zasięgu zapewnionego kierowcy; bez ISO 15118 SoC jest nieznany.
- **Gwarancja i degradacja:** producent może ograniczać V2X lub ją wyłączać. Wpływ cyklowania na degradację i koszt
  zużycia na kWh zależy od chemii i warunków [do weryfikacji]; wlicz go w opłacalność. Baterię opisuje dom-ev-vehicle-battery.

## 8. Modele biznesowe
| Model | Kto zarabia | Wymaga |
|---|---|---|
| Arbitraż cenowy (ładuj tanio, oddawaj drogo) | kierowca, flota | taryfa dynamiczna, pomiar dwukierunkowy |
| Usługi elastyczności i bilansowania | agregator, kierowca | agregacja (RED III art. 20a ust. 5), prekwalifikacja u OSP/OSD [do weryfikacji] |
| Peak shaving w budynku (V2B) | właściciel budynku | sterowanie mocą umowną (dom-ev-energy-management) |
| Zasilanie awaryjne (V2H) | właściciel domu | falownik grid-forming, przełącznik sieć/wyspa |

Role rynku: dom-ev-market-roles.

## Przykład
Wejście: operator floty ma stację DC 30 kW i bus na ISO 15118-20; w `ServiceDetail` bus pokazuje `DC_BPT`, `ControlMode` = 2
(dynamic). Chcemy oddawać w szczycie 15 kW.

Wynik: (1) w `BPT_DC_CPDResEnergyTransferMode` stacja podaje `EVSEMaximumDischargePower` ≥ 15 kW i prąd odpowiednio;
auto w `BPT_DC_CPDReqEnergyTransferMode` podaje własne `EVMaximumDischargePower`. Realne okno to mniejsza z wartości.
(2) W `ChargeLoop` auto wysyła `BPT_Dynamic_DC_CLReqControlMode`, a stacja odpowiada `BPT_Dynamic_DC_CLResControlMode` z bieżącymi limitami rozładowania (`EVSEMaximumDischargePower` itd.). (3) Backend (2.1) wysyła
profil z ujemnym limitem; w 2.0.1 [do weryfikacji] zamiast tego własny kanał do stacji. (4) Zapis w `MeterValues`
osobno import i export. (5) `MinimumSOC` kierowcy nie schodzi poniżej ustalonego pułapu; zgoda kierowcy zapisana
przed pierwszą sesją.

## Pułapki
- Utożsamianie V2H i V2G: V2H nie musi mieć eksportu do sieci, ale tryb awaryjny wymaga innego falownika (grid-forming).
- Założenie, że zmiana znaku limitu w profilu OCPP 2.0.1 wystarczy. Pełna obsługa V2X wymaga 2.1 i certyfikowanej stacji [do weryfikacji].
- Walidowanie tylko `MaximumDischargePower` stacji, bez wartości auta. Obowiązuje przecięcie obu zakresów.
- Brak osobnego rejestru eksportu: energia oddana wchodzi do `total_energy` z dodatnim znakiem i zawyża rachunek.
- Planowanie V2G z SoC, którego auto nie podaje (AC bez ISO 15118).
- Cytowanie kodu josev jako normy: to implementacja (ranga W).

## Checklista
- [ ] Wariant (V2G/V2H/V2B/V2L) i odbiorca energii ustalone, wiadomo, czy jest synchronizacja z siecią
- [ ] Stacja i auto mają usługę BPT (`AC_BPT`/`DC_BPT`), tryb `ControlMode` uzgodniony
- [ ] Zakres rozładowania = przecięcie wartości pojazdu i stacji (moc i prąd)
- [ ] Ujemne limity tylko do stacji z potwierdzoną zdolnością; CSMS odrzuca resztę
- [ ] Osobny pomiar importu i eksportu; eksport nie ginie w `total_energy`
- [ ] Zgoda kierowcy, minimalny SoC, godzina odjazdu i warunki gwarancji zapisane
- [ ] Wymogi OSD i kodu sieci sprawdzone u operatora [do weryfikacji]
- [ ] Pozycje [do weryfikacji] przekazane do `researcher`

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| pola BPT w AC i DC, ScheduleExchange, PowerDelivery, walidacje josev z numerami linii | `references/bpt-iso15118-20.md` |
| co jest pewne, a co do weryfikacji (OCPP 2.1, OCPI, OSD, degradacja), jak to sprawdzić | `references/luki-i-weryfikacja.md` |

## Źródła
- Baza wiedzy fabryki, pobrane 2026-10-20: `josev-iso15118` (SwitchEV/iso15118, github.com/SwitchEV/iso15118, iso15118_20: common_messages.py, dc.py, ac.py, doc.txt L725–830, L2410–2460, L2686–2930, L3322–3670, L3815–4230; ranga W — implementacja), `eu-red-iii` (dyrektywa 2023/2413, eur-lex.europa.eu/eli/dir/2023/2413/oj, doc.txt L2924–2985, ranga P), `ocpp-json-schemas` (v201 SetChargingProfileRequest, doc.txt L379–394, ranga W).
- Skille fabryki: dom-ev-energy-management (przepisy i przyłączenie), dom-ev-charging (fragmenty o V2G, import 2026-09-27).
- Brak w bazie: ISO 15118-20, IEC 61851, OCPP 2.1, wymogi OSD, kody sieci — [do weryfikacji].
