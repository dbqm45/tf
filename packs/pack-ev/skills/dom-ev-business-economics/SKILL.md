---
name: dom-ev-business-economics
description: Użyj przy opłacalności stacji i sieci ładowania — CAPEX, OPEX, demand charges, marża na kWh, próg rentowności utilization, NPV, okres zwrotu, wrażliwość.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba ocenić ekonomię stacji lub sieci ładowania z perspektywy decyzji inwestycyjnej i produktu — struktura CAPEX (ładowarki, przyłącze, transformator, budowa, projekt, terminale) i OPEX (energia, opłaty za moc, serwis, łączność, software, dzierżawa, roaming i płatności), dotacje, przychód i koszt na kWh, marża po prowizjach, pełny koszt kWh, próg rentowności utilization, wpływ średniej mocy, wpływ modelu cenowego, BESS i smart charging na opłaty za moc, przychody dodatkowe, rozbudowa etapami, NPV, okres zwrotu, wrażliwość, scenariusze, skrypt station_economics.py. Nie do liczenia ceny sesji z taryfy OCPI (dom-ev-tariffs-pricing), wyboru lokalizacji i budowy (dom-ev-site-development), definicji i liczenia KPI operacyjnych (dom-ev-kpi-analytics) ani podziału mocy na lokacji (dom-ev-energy-management)."
  slowa: "opłacalność stacji, czy stacja się zwróci, zwrot z inwestycji, ROI, payback, NPV, CAPEX, OPEX, koszt przyłącza, demand charge, opłata za moc, moc umowna, marża na kWh, koszt kWh, próg rentowności, break-even, utilization a zysk, business case, model biznesowy ładowania, dotacja, grant, NEVI funding, BESS opłacalność, przychody dodatkowe, prowizja roamingowa, unit economics, charging station profitability, wrażliwość, scenariusze, ile kosztuje budowa stacji, ile zarabia stacja"
---

# Ekonomia stacji i sieci ładowania

Skill odpowiada na pytanie „czy ta stacja się opłaca i od czego to zależy”. Cenę sesji z taryfy liczy dom-ev-tariffs-pricing, lokalizację
i budowę opisuje dom-ev-site-development, KPI z danych — dom-ev-kpi-analytics. Liczb rynkowych (ceny ładowarek, przyłączy,
energii, dzierżawy, typowe utilization) fabryka nie ma w bazie wiedzy: podaje je człowiek, ze źródłem, a przedziały z przeglądu
mają znacznik [do weryfikacji].

## Procedura
1. **Zbierz założenia** w jednej walucie, netto, z podpisem źródła każdej liczby (oferta, rachunek, umowa). Brak liczby
   zapisz jako założenie z przedziałem, nie jako fakt.
2. **CAPEX** rozbij na pozycje; osobno oznacz przyłącze jako najbardziej niepewne (`references/capex-opex.md`).
3. **OPEX** rozbij na stały (moc umowna, serwis, łączność, software, dzierżawa) i zmienny (energia, prowizje).
4. **Policz jednostkę:** marża na kWh, pełny koszt kWh, próg rentowności utilization.
5. **Policz decyzję:** `station_economics.py` daje roczny wynik, NPV, okres zwrotu i wrażliwość.
6. **Przetestuj scenariusze** (niski, bazowy, wysoki utilization; cena; energia) i wypisz, czego model nie widzi.
7. **Podaj wynik jako przedział i warunek**, np. „opłaca się powyżej X % utilization przy cenie Y”, nie jedną liczbę.

## Pozycje kosztów
| Pozycja | Rodzaj | Uwaga |
|---|---|---|
| Ładowarki (DC, AC, moduły mocy) | CAPEX | cena rośnie z mocą; moc nominalna nie jest mocą sprzedaną |
| Przyłącze i warunki OSD | CAPEX | często największa i najbardziej niepewna pozycja; zależy od odległości do sieci i wymaganej mocy |
| Transformator, rozdzielnia, kable | CAPEX | skok kosztu przy przekroczeniu mocy istniejącej stacji |
| Budowa, fundamenty, wiaty, oznakowanie | CAPEX | lokalne koszty robót i pozwoleń |
| Projekt, pozwolenia, uruchomienie | CAPEX | w tym commissioning i testy |
| Terminale płatnicze | CAPEX | wymóg płatności ad hoc: dom-ev-regulations-eu |
| Energia | OPEX zmienny | cena zakupu zależy od taryfy i profilu poboru |
| Opłata za moc szczytową / umowną (demand charge) | OPEX stały lub półstały | płacisz za zdolność lub szczyt, nie za sprzedane kWh |
| Serwis, gwarancja, naprawy | OPEX stały | zwykle jako procent CAPEX sprzętu [założenie] |
| Łączność, CSMS, software, licencje | OPEX stały | często za punkt ładowania |
| Dzierżawa lub udział właściciela terenu | OPEX stały lub % przychodu | zależy od umowy |
| Prowizje roamingu i hubów, opłaty płatnicze | OPEX zmienny | % przychodu lub stawka za transakcję |

Dotacje obniżają CAPEX netto (kolumna `grants` w skrypcie), ale mają warunki: dostępność, raportowanie, okres trwałości.
Konkretnych programów tu nie ma: nazwę, intensywność i warunki sprawdź w aktualnym naborze [do weryfikacji].
Jako fakt o finansowaniu: w USA NEVI to program formułowy, którego projekty podlegają minimalnym wymogom z 23 CFR 680
(eCFR, 680.100 i 680.102), szczegóły: dom-ev-regulations-us. Wymogi dotacji często wymuszają konfigurację stacji (porty, moc,
uptime), więc wpływają na CAPEX i OPEX, a nie tylko na przychód.

## Ekonomia jednostkowa
Wzory (kWh rocznie = EVSE × 8760 × utilization × moc średnia, marża i pełny koszt kWh, próg rentowności) liczy
skrypt `station_economics.py`; podawaj wynik skryptu z założeniami, nie licz ręcznie.

Trzy wnioski, które model często pomija:
- **Koszty stałe dominują przy niskim utilization.** Opłata za moc umowną i OPEX stały płacisz tak samo przy 3 %
  i przy 15 % wykorzystania, więc pełny koszt kWh gwałtownie spada wraz z utilization. Dodatnia marża na kWh nie wystarcza.
- **Moc średnia, nie nominalna** — skrypt przyjmuje `avg_power_kw` w czasie ładowania (dom-ev-vehicle-battery).
- **Utilization ma definicję.** W skrypcie to udział czasu ładowania w roku. Inne definicje (czas zajęcia portu, kWh
  względem maksimum) dają inne liczby; porównuj tylko tę samą definicję (dom-ev-kpi-analytics).
- Próg „15–20 % utilization dla DC” z przeglądu jest orientacyjny [do weryfikacji]; własny próg policz skryptem.

## Modele cenowe a ekonomia
Szczegóły składników i liczenia: dom-ev-tariffs-pricing. Tu liczy się skutek dla przychodu.
| Model | Skutek ekonomiczny |
|---|---|
| Za kWh | przychód skaluje się z energią; przy wolnych autach nie rekompensuje czasu zajęcia portu |
| Za minutę | chroni przychód przy wolnym ładowaniu, ale kierowca płaci więcej za słabe auto; zwiększa ryzyko reklamacji |
| Opłata startowa | podnosi przychód z krótkich sesji, wpływa na odbiór ceny |
| Idle fee (opłata za postój) | zwalnia port; przychód jest uboczny, celem jest dostępność |
| Subskrypcja | stały przychód, niższa cena kWh; ryzyko dla marży przy dużym poborze |
| Ceny dynamiczne | wyrównują obciążenie i marżę; wymagają jasnej komunikacji ceny przed startem |
| Ad hoc | cena własna CPO, brak prowizji huba, ale koszt płatności kartą |
| Roaming | cena z kontraktu, prowizja eMSP lub huba obniża marżę; role: dom-ev-market-roles |

Marżę policz osobno dla ad hoc i roamingu, potem ważoną udziałem sesji. Prowizje podaje umowa — fabryka nie zna ich stawek.

## Obniżanie kosztów
- **Opłaty za moc:** smart charging i limit mocy obniżają moc umowną i szczyt (dom-ev-smart-charging, dom-ev-energy-management);
  BESS ścina szczyty lub zastępuje droższe przyłącze, ale ma własny CAPEX i degradację. Policz oba warianty w tym samym
  modelu: zmiana `contracted_kw` i dodatkowa pozycja w `capex`.
- **Przychody dodatkowe:** sklep, gastronomia, reklama, usługi dla floty — pole `other_revenue_per_year`. Traktuj je
  ostrożnie: zależą od ruchu i od umowy z najemcą.
- **Rozbudowa etapami:** przyłącze i transformator dla końcowej mocy, ładowarki w etapach według rzeczywistego utilization.
  Obniża ryzyko, ale późniejsze zwiększenie przyłącza trzeba policzyć osobno.

## Decyzja
- **NPV** z przepływów EBITDA po rocznej stopie dyskonta; **okres zwrotu** z przepływów niedyskontowanych. Oba mają sens
  tylko przy jawnych założeniach (horyzont, stopa, wzrost utilization).
- **Wrażliwość:** skrypt przelicza NPV dla utilization ×0,8 i ×1,2, ceny ×0,9 i ×1,1 oraz energii ×1,2. Szeroka rozpiętość
  pokazuje, które założenie trzeba najpierw potwierdzić.
- **Scenariusze:** zmieniaj kilka założeń naraz (np. wolny wzrost utilization i droższa energia) i zapisz je w kilku plikach.
- **Czego model nie widzi:** ryzyko i czas przyłącza, konkurencję w pobliżu, zmianę regulacji i cen energii, awarie
  i uptime, wartość rezydualną sprzętu. Lista i szczegóły: `references/decyzja-i-ryzyka.md`.
- **KPI finansowe z danych:** przychód i kWh na EVSE, utilization, koszt na kWh liczy się z sesji i CDR (dom-ev-kpi-analytics,
  dom-ev-cdr-settlement); porównaj je z założeniami modelu, zanim zaufasz prognozie.

## Skrypt station_economics.py
Uruchom (nie czytaj kodu):

`python3 .claude/skills/dom-ev-business-economics/scripts/station_economics.py <stacja>.json [--json]`

Sieć: brak. Tylko biblioteka standardowa.

Pola wejścia (kwoty netto, jedna waluta): `years`, `discount_rate`, `evse`, `avg_power_kw`, `utilization` (liczba 0–1 albo lista
na każdy rok), `price_per_kwh`, `energy_cost_per_kwh`, `revenue_fees_pct` (prowizje jako udział przychodu z ładowania),
`demand_charge_per_kw_month`, `contracted_kw`, `opex_per_year` (obiekt pozycja: kwota), `capex` (obiekt), `grants`,
`other_revenue_per_year`. Wymagane: `years`, `evse`, `avg_power_kw`, `utilization`, `price_per_kwh`, `energy_cost_per_kwh`.

Wzór roku: przychód = kWh × cena + przychód dodatkowy; EBITDA = przychód − energia − prowizje − opłata za moc × moc umowna × 12 −
OPEX. Rok 0: −(CAPEX − dotacje). Wynik: CAPEX netto, NPV, okres zwrotu, marża na kWh, pełny koszt kWh (rok 1), próg
utilization, tabela lat, wrażliwość i ostrzeżenia (`grants-exceed-capex`, `breakeven-above-100`).

| Kod wyjścia | Znaczenie |
|---|---|
| 0 | NPV ≥ 0 |
| 1 | NPV < 0 (wynik poprawny, projekt nie spełnia kryterium) |
| 2 | błąd wejścia (brak pola, zły typ, wartość poza zakresem) |

**Czego skrypt nie liczy:** podatków, amortyzacji, finansowania (kredyt, dźwignia), inflacji i wzrostu cen, wymiany sprzętu,
degradacji, wartości rezydualnej. Stały utilization i cena bez indeksacji. To model do decyzji „liczyć dalej czy nie”.
Próg rentowności dotyczy EBITDA ≥ 0, a nie NPV ≥ 0: próg NPV jest wyższy, bo wymaga też spłaty CAPEX.

## Przykład
Założenia (ilustracja do ćwiczenia, nie dane rynkowe): 4 punkty DC, średnia moc 70 kW, cena 2,00 netto, energia 0,90, prowizje
8 % przychodu, opłata za moc 40 za kW miesięcznie przy 300 kW umownych, OPEX 66 000 rocznie, przychód dodatkowy 10 000,
CAPEX 1 970 000 (ładowarki 1 200 000, przyłącze 500 000, budowa i projekt 250 000, terminale 20 000), dotacja 300 000,
10 lat, 8 %, utilization rośnie z 5 % do 15 % w sześć lat.

Wynik uruchomienia (skrót, rok 1 i 6):
```
CAPEX netto 1670000.00 · NPV -1201270.76 · zwrot brak w horyzoncie
  marża na kWh 0.9400 · pełny koszt kWh 2.7723 · próg utilization 8.67 %
    1   5.0%     122640   255280.00  110376.00  19622.40 144000.00  66000.00  -84718.40
    6  15.0%     367920   745840.00  331128.00  58867.20 144000.00  66000.00  145844.80
  wrażliwość NPV: utilization_x1.2 -839121.65, price_x1.1 -846826.95, energy_cost_x1.2 -1548009.26
```
Odczyt: marża na kWh jest dodatnia (0,94), a pełny koszt kWh w roku 1 (2,77) przewyższa cenę (2,00), bo opłata za moc 144 000
dzieli się na mało kWh. EBITDA jest dodatnia od utilization około 8,7 %, ale NPV nadal ujemne: przy tych liczbach CAPEX nie
zwraca się w 10 lat. Ten sam plik z `contracted_kw` 180 (mniejsza moc umowna dzięki smart charging, bez kosztu BESS) daje NPV
-814 770,07 i próg 6,18 %: obniżenie opłaty za moc działa, ale nie ratuje projektu. Wniosek: najpierw zakwestionuj CAPEX przyłącza,
cenę i prognozę utilization, nie kolejne procenty marży.

## Pułapki
- Marża na kWh bez kosztów stałych wygląda dobrze; liczy się pełny koszt kWh i próg utilization.
- Moc nominalna zamiast średniej zawyża kWh, a więc przychód, nawet dwukrotnie [założenie].
- Prowizje roamingu pominięte albo policzone od kWh zamiast od przychodu (sprawdź umowę).
- Cena z VAT w polu `price_per_kwh`, a koszty netto: wszystkie kwoty muszą być netto.
- Utilization z innej definicji (zajęcie portu) wstawione do wzoru na kWh.
- Jedna liczba zamiast przedziału: NPV z jednej ścieżki utilization udaje pewność.
- Dotacja wpisana jako pewna, choć nabór, warunki i trwałość nie są potwierdzone.
- Przyłącze ujęte jako stała, choć jego koszt i termin zależą od OSD.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/capex-opex.md` | rozbijasz pozycje kosztów, pytasz o przyłącze, dotacje, opłaty za moc, BESS, rozbudowę etapami |
| `references/decyzja-i-ryzyka.md` | budujesz scenariusze, interpretujesz NPV i wrażliwość, spisujesz ryzyka spoza modelu, liczysz KPI finansowe z danych |

## Checklista
- [ ] każda liczba ma źródło albo oznaczenie założenia; przedziały z przeglądu mają [do weryfikacji]
- [ ] kwoty netto w jednej walucie; moc średnia, nie nominalna
- [ ] policzone: marża na kWh, pełny koszt kWh, próg utilization
- [ ] `station_economics.py` uruchomiony, kod wyjścia i wrażliwość odczytane
- [ ] sprawdzone co najmniej trzy scenariusze (utilization, cena, energia)
- [ ] wypisane ryzyka spoza modelu: przyłącze, konkurencja, regulacje
- [ ] dotacje oznaczone [do weryfikacji], jeśli bez aktualnego naboru

## Źródła
- `.claude/skills/dom-ev-business-economics/scripts/station_economics.py` (docstring i kod, wzory i kody wyjścia), uruchomienie 2026-10-20.
- us-nevi, 23 CFR 680.100 i 680.102 (cel i zakres programu NEVI), ecfr.gov, pobrane 2026-10-20 (`.claude/knowledge/us-nevi/doc.txt`, L12-19).
- `docs/backlog-wiedza-ogolna-ev.md`, sekcja 12 (luki: CAPEX, OPEX, opłaty za moc, ekonomia jednostkowa); progi z przeglądu wiedzy ogólnej [do weryfikacji].
- Danych rynkowych o kosztach i utilization w bazie wiedzy fabryki nie ma (stan na 2026-10-20).
