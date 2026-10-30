---
name: dom-ev-vehicle-battery
description: Użyj przy pojeździe jako stronie ładowania — bateria, BMS, krzywa ładowania, 400 V i 800 V, ładowarka pokładowa, ETA w aplikacji, zgłoszenie „ładuje wolno”.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba zrozumieć, co robi auto w sesji ładowania z perspektywy CSMS, eMSP i aplikacji — BEV i PHEV, bateria trakcyjna i BMS jako decydent mocy, krzywa ładowania i spadek mocy przy wysokim SoC, temperatura i preconditioning, SoH, ładowarka pokładowa jako limit AC (moc, fazy), architektura 400 V i 800 V, dlaczego CSMS widzi moc niższą niż nominalna, SoC w danych sesji, szacowanie czasu ładowania i ETA, dane z auta przez API producenta. Nie do profili ładowania i limitów A lub W (dom-ev-smart-charging), sygnalizacji CP i PWM po stronie stacji (dom-ev-charger-hardware), komunikatów ISO 15118 (dom-ev-iso15118), przebiegu diagnozy awarii z ramek (dom-ev-diagnostics) ani V2G (dom-ev-v2x)."
  slowa: "ładuje wolno, auto ładuje wolno, moc niższa niż ładowarka, 150 kW a bierze 50, bateria, BMS, krzywa ładowania, charging curve, SoC, stan naładowania, 80 procent, spadek mocy, SoH, zdrowie baterii, temperatura baterii, preconditioning, zimno ładowanie, 400 V, 800 V, ładowarka pokładowa, OBC, auto jednofazowe, ETA ładowania, czas do 80 procent, ile będzie ładować, PHEV, hybryda plug-in, dane z auta, API producenta, battery, slow charging, charging power lower than nominal"
---

# Pojazd jako strona sesji ładowania

Z punktu widzenia software ładowarka **oferuje** limit, a auto **decyduje**, ile weźmie. Sesja ma więc trzy
sufity mocy naraz: ładowarka (oraz profile CSMS), kabel i złącze, **pojazd** (BMS, ładowarka pokładowa, napięcie
baterii). Ten skill opisuje trzeci sufit. Reszta — odsyłacze w tabeli „Granice”.

## Mapa pojęć
| Pojęcie | Co znaczy dla software |
|---|---|
| **BEV** | tylko bateria trakcyjna; może ładować AC i DC |
| **PHEV** | mała bateria + silnik spalinowy; ładuje głównie AC, DC rzadziej; sesje krótkie, kończą się „pełne” szybko |
| **HEV, RE-EV** | HEV nie ma wtyczki, więc nie występuje w sesjach; RE-EV ładuje się jak BEV (szczegóły: `.claude/skills/dom-ev-charging/references/pojazdy-elektryczne.md`) |
| **FCEV** | wodór, nie ładuje się z punktu EVSE — poza zakresem CSMS |
| **Bateria trakcyjna** | pojemność nominalna ≠ użytkowa (netto); do obliczeń energii bierz **użytkową**; rząd wielkości 40–100+ kWh [do weryfikacji dla modeli] |
| **BMS** | układ pojazdu, który pilnuje napięć ogniw, prądu i temperatury i **wyznacza maksymalny dozwolony prąd/moc** w danej chwili |
| **SoC** | stan naładowania, % pojemności użytkowej; wiedza o nim zależy od łączności z autem (patrz niżej) |
| **SoH** | stopień zużycia (pojemność względem nowej); mała pojemność = wcześniejsze „pełne” i szybszy spadek mocy |
| **OBC** | ładowarka pokładowa AC→DC; limit mocy w AC |

## Zasada: auto decyduje, ładowarka podaje maksimum
| Tryb | Kto co podaje | Jak widać w danych |
|---|---|---|
| **AC** | stacja sygnalizuje dostępny prąd sygnałem PWM na Control Pilot; auto pobiera do tej wartości, nie więcej (kody PWM i stany: dom-ev-charger-hardware) | `Current.Import` i moc ≤ oferta, często dużo mniej |
| **DC** | auto przez komunikację wysyła żądanie prądu i napięcia (DIN 70121 albo ISO 15118-2/-20), stacja je realizuje w swoich limitach; pola i przebieg: dom-ev-iso15118 | żądany prąd maleje z SoC i temperaturą |

Nazwy pól, które pokazują tę zasadę w implementacji josev (ranga W, nie norma): ISO 15118-2 DC — `EVTargetCurrent`,
`EVTargetVoltage`, `EVMaximumVoltageLimit`, `EVMaximumCurrentLimit`, `EVMaximumPowerLimit`, `BulkChargingComplete`,
`ChargingComplete`, `RemainingTimeToFullSoC`, `RemainingTimeToBulkSoC`; ISO 15118-20 DC — `EVMaximumChargePower`,
`EVMinimumChargePower`, `EVMaximumChargeCurrent`, `EVMaximumVoltage`, `EVMinimumVoltage`, `TargetSOC`; AC -20 —
`EVMaximumChargePower` z wariantami `_L2` i `_L3` dla faz. Z tego wynika, że **limit w CSMS to nie żądanie**: profil
`SetChargingProfile` zawęża ofertę, a auto i tak może brać mniej (dom-ev-smart-charging).

## Krzywa ładowania
- DC: moc rośnie do szczytu, trzyma się go w środkowym zakresie SoC, potem **maleje wraz ze wzrostem SoC** (napięcie
  ogniw rośnie, BMS tnie prąd). Powyżej ok. 80 % spadek jest zwykle gwałtowny — stąd zasada na trasie: **ładuj
  10–80 %**, bo ostatnie 20 % zajmuje nieproporcjonalnie dużo czasu [kształt zależy od modelu — do weryfikacji].
- AC: prawie płaska (limit OBC lub oferty), spada dopiero na samym końcu.
- Kształt krzywej zależy od temperatury ogniw, SoH i modelu — **nie ma jednej krzywej**. Konkretnych liczb dla modeli
  aut w skillu nie ma; potrzebujesz ich z danych producenta lub z własnych sesji.
- Dlatego „moc ładowarki 300 kW” nie daje 300 kW w aucie: auto z maksymalną mocą DC 150 kW pobierze najwyżej 150 kW
  (ilustracja, nie model auta).

## Temperatura i preconditioning
- Zimna bateria: BMS ogranicza prąd, bo ładowanie w niskiej temperaturze szkodzi ogniwom; moc jest niska na początku
  sesji i rośnie, gdy ogniwa się nagrzeją własnym ciepłem ładowania.
- Gorąca bateria (po jeździe z dużą mocą, upał, kolejna sesja szybko po poprzedniej): BMS też tnie moc.
- **Preconditioning** to ogrzanie baterii przed przyjazdem na szybką ładowarkę. Część aut robi to po wskazaniu
  ładowarki w nawigacji; to funkcja auta, nie CSMS. Aplikacja eMSP może tylko **podpowiedzieć** kierowcy [do weryfikacji
  po stronie producenta, czy da się to wywołać zdalnie].
- Temperatura otoczenia i czas od poprzedniej sesji pogarszają dokładność ETA.

## Ładowarka pokładowa (OBC) i AC
| Cecha | Skutek |
|---|---|
| moc OBC | sufit mocy w AC niezależnie od mocy stacji (np. stacja 22 kW, auto z OBC 11 kW — dom-ev-charger-hardware) |
| liczba faz | auto **1-fazowe** na stacji 3-fazowej używa jednej fazy: 230 V × 32 A ≈ 7,4 kW, nie 22 kW |
| nierównomierne fazy | gdy auto używa tylko jednej fazy z trzech, w lokacji z DLM jedna faza się przeciąża; obciążenie liczysz **na fazę** (dom-ev-energy-management) |
| minimalny prąd | poniżej minimum auto wstrzymuje ładowanie (stąd „zawieszone” przy bardzo niskich limitach — dom-ev-smart-charging) |

W OCPI `PowerType` (`AC_1_PHASE`, `AC_3_PHASE`, `DC`) opisuje **ładowarkę**, nie auto; dla kierowcy z autem
1-fazowym oferta „AC_3_PHASE 22 kW” jest zawyżona (dom-ev-ocpi).

## 400 V i 800 V
| Cecha | Co robi ładowarka/CSMS |
|---|---|
| auto 400 V (zakres napięcia baterii zwykle niższy) | ładowarka DC o zakresie np. 150–500 V działa; limitem bywa prąd |
| auto 800 V | ta sama moc przy **połowie prądu**; ładowarka musi mieć zakres napięcia obejmujący ~800 V [do weryfikacji dla konkretnej stacji] |
| ładowarka z maksymalnym napięciem poniżej napięcia baterii | auto może podnieść napięcie własnym przetwornikiem (boost) albo ładować połową baterii; moc spada, bo ogranicza prąd stacji [zależy od auta i stacji — do weryfikacji] |

Praktyka: model ładowarki w CSMS powinien przechowywać zakres napięcia i prąd maksymalny wyjścia DC (z onboardingu,
dom-ev-charger-onboarding), bo „150 kW” nie mówi, jaką moc dostanie auto 800 V albo 400 V. Lista modeli aut 800 V
zmienia się szybko — nie wpisuj jej w kod [do weryfikacji].

## Dlaczego CSMS widzi mniej niż moc nominalna
1. **BMS tnie** moc (SoC, temperatura, SoH) — najczęstsza przyczyna.
2. **OBC** albo liczba faz auta (AC).
3. **Profil** SetChargingProfile lub DLM ustawił niższy limit.
4. **Podział mocy w hubie** — dwa auta na jednej szafie mocy (dom-ev-charger-hardware).
5. **Napięcie** auta względem zakresu ładowarki (tabela wyżej).
6. **Kabel i zabezpieczenie** (kabel o niższym prądzie, termiczny derating stacji).
7. **Pomiar:** `MeterValues` to próbki; średnia moc z `Energy.Active.Import.Register` w oknie ≠ chwilowa
   `Power.Active.Import`. Przy porównaniu liczysz z tego samego okna (dom-ev-ocpp-16).

Co trafia do CSMS w trakcie sesji (measurandy z enumeracji schematów OCPP 1.6 `MeterValues` i 2.0.1
`MeterValuesRequest`): `Energy.Active.Import.Register` (energia), `Power.Active.Import` (moc), `Current.Import`,
`Voltage`, `SoC`, a także `Current.Offered` i `Power.Offered` (oferta). **SoC** raportuje stacja tylko wtedy, gdy ma go
od auta: w DC przez DIN 70121 albo ISO 15118, w AC zwykle **brak**. W AC nie zakładaj SoC; w modelu dopuszczaj `null`
(dom-ev-glossary). W OCPP 2.0.1 stacja może dodatkowo zgłosić potrzeby auta komunikatem `NotifyEVChargingNeeds`
(`ChargingNeedsType` z parametrami AC albo DC i trybem transferu energii; dom-ev-ocpp-2x).

## ETA i czas ładowania w aplikacji
Model prosty, który wystarcza do ekranu „do X % za N minut”:
1. Energia do dostarczenia: `E = (SoC_cel − SoC_start) / 100 × pojemność_użytkowa`.
2. Podziel zakres SoC na odcinki (np. 20–50, 50–70, 70–80 %).
3. Moc w odcinku: `P = min(moc_ładowarki, moc_z_krzywej_auta(odcinek), limit_profilu)`; w AC `min(oferta, OBC × fazy)`.
4. Czas odcinka = energia odcinka / P. Suma = ETA. Dodaj margines na temperaturę.
5. Gdy w sesji pojawi się prawdziwa moc (`Power.Active.Import`) lub SoC, **przelicz od bieżącego punktu**.

Szczegóły, przykład liczbowy i źródła krzywej (producent, własna historia sesji): `references/krzywa-i-eta.md`.
Oznacz w UI, że to **szacunek**; cena zależy od taryfy, nie od ETA (dom-ev-tariffs-pricing).

## Zgłoszenie „ładuje wolno”
Zacznij od pytania, **co konkretnie widać**: moc, SoC, temperaturę, tryb (AC/DC). Drzewo przyczyn z kolejnością pytań
do kierowcy i do CSMS: `references/ladowanie-wolno-drzewo.md`; dowód z ramek: dom-ev-diagnostics.

## Dane z auta przez API producenta
Aplikacja może pobierać SoC, zasięg, stan złącza i czasem SoH z chmury producenta po zgodzie właściciela. To osobny
kanał niż sesja OCPP: opóźniony, bez gwarancji dostępności i w formatach każdego producenta, więc traktuj dane jako
podpowiedź, nie dowód rozliczeniowy [do weryfikacji]. RED III (art. 20a ust. 3) wymaga od państw członkowskich
udostępniania w czasie rzeczywistym m.in. SoH, SoC, zadanej mocy baterii i pojemności właścicielom i podmiotom przez
nich upoważnionym — konsekwencje dla eMSP: dom-ev-regulations-eu. Paszport baterii (rozporządzenie (UE) 2023/1542)
istnieje, ale aktu nie ma w bazie [do weryfikacji]; nie zakładaj, że da się z niego czytać krzywą ładowania.

## Przykład
Wejście: auto z baterią użytkową 77 kWh (ilustracja, nie konkretny model), ładowarka 150 kW, 20 → 80 %.
Podejście naiwne: 46,2 kWh / 150 kW ≈ 18,5 min. Z krzywą (ilustracja, [do weryfikacji] dla każdego auta):

| Odcinek SoC | Energia | Moc z krzywej | Czas |
|---|---|---|---|
| 20–50 % | 23,1 kWh | 130 kW | 10,7 min |
| 50–70 % | 15,4 kWh | 100 kW | 9,2 min |
| 70–80 % | 7,7 kWh | 60 kW | 7,7 min |

Wynik: ok. 28 min, średnio ok. 100 kW. Aplikacja z naiwnym wzorem obiecałaby 18 minut i wygenerowałaby zgłoszenia „wolno”.

## Granice
| Pytanie | Skill |
|---|---|
| profile, limity A/W, stackLevel | dom-ev-smart-charging |
| CP, PWM, stany A–F, złącza, moduły mocy | dom-ev-charger-hardware |
| komunikaty DIN 70121 i ISO 15118, certyfikaty | dom-ev-iso15118 |
| diagnoza od objawu do przyczyny | dom-ev-diagnostics |
| moc lokacji, DLM, fazy | dom-ev-energy-management |
| V2G, V2H | dom-ev-v2x |

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| liczysz ETA, projektujesz krzywą w aplikacji, kalibrujesz z historii sesji | `references/krzywa-i-eta.md` |
| kierowca pisze „ładuje wolno” i trzeba ustalić przyczynę | `references/ladowanie-wolno-drzewo.md` |

## Pułapki
- Utożsamianie mocy ładowarki z mocą w aucie; „22 kW” na stacji AC i 1-fazowe auto 7,4 kW.
- Pojemność nominalna zamiast użytkowej w obliczeniach energii.
- Wymaganie SoC w sesji AC; SoC jako pole obowiązkowe w modelu sesji.
- ETA liniowe do 100 %: ostatnie 20 % SoC zajmuje nieproporcjonalnie dużo czasu.
- Zgłaszanie awarii ładowarki, gdy objaw to zimna bateria albo SoC powyżej 80 %.
- Liczby konkretnych modeli aut w kodzie lub dokumentacji bez źródła i daty.
- Profil z limitem uważany za gwarancję poboru: auto może brać mniej.
- Zakładanie, że moc nominalna ładowarki DC jest dostępna przy każdym napięciu baterii.

## Checklista
- [ ] Czy w modelu energię liczę od pojemności użytkowej?
- [ ] Czy SoC może być `null` (AC, brak 15118)?
- [ ] Czy ETA bierze `min` z mocy ładowarki, krzywej auta i profilu?
- [ ] Czy ETA przelicza się od bieżącej mocy i jest oznaczone jako szacunek?
- [ ] Czy model ładowarki zna zakres napięcia i prąd maksymalny DC?
- [ ] Czy przy „ładuje wolno” sprawdziłem SoC, temperaturę, tryb i fazy, zanim zgłosiłem awarię?
- [ ] Czy liczby modeli aut mają źródło albo [do weryfikacji]?

## Źródła
- `.claude/skills/dom-ev-charging/references/pojazdy-elektryczne.md` (import 2026-09-27): typy pojazdów, komponenty.
- josev-iso15118 (SwitchEV/iso15118, ranga W: implementacja, nie norma), `.claude/knowledge/josev-iso15118/doc.txt`:
  ISO 15118-2 body.py L1527-1566 (pola DC), ISO 15118-20 dc.py L3362-3390 i L3432-3471, ac.py L3735-3775,
  common_messages.py L2390-2443 (`TargetSOC`, `EVTargetEnergyRequest`); github.com/SwitchEV/iso15118, pobrane 2026-10-20.
- eu-red-iii, dyrektywa (UE) 2023/2413, art. 20a ust. 3 (dane z pojazdu), `.claude/knowledge/eu-red-iii/doc.txt` L2960-2970,
  eur-lex.europa.eu/eli/dir/2023/2413/oj, pobrane 2026-10-20.
- ocpp-json-schemas (mobilityhouse/ocpp, schematy OCA), `.claude/knowledge/ocpp-json-schemas/doc.txt`: measurandy
  v16 MeterValues.json L1089+ i v201 MeterValuesRequest.json `MeasurandEnumType` L1456+, NotifyEVChargingNeedsRequest.json
  L2495+, pobrane 2026-10-20. us-afdc: nie wnosi danych o krzywych.
- Liczby w przykładzie ETA to ilustracja własna, nie dane pojazdu.
