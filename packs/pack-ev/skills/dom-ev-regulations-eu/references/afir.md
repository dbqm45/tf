# AFIR — szczegóły dla oprogramowania ładowania

> **Spis treści:** 1. Definicje (Art. 2, linie 70-513) · 2. Płatność ad hoc (Art. 5(1)-(2), linie 921-972) · 3. Cena (Art. 5(3)-(6), linie 973-1042) · 4. Cyfrowe połączenie, smart charging, kabel (Art.… · 5. Dane i NAP (Art. 20, linie 1911-2147) · 6. Aneks II: złącza i komunikacja (linie 2505-3073) · 7. Cele infrastruktury (Art. 3-4, linie 514-920) · 8. Akty delegowane, wykonawcze, przegląd

Źródło: `eu-afir`, AFIR (UE) 2023/1804, wersja skonsolidowana EN z 08.01.2026 (02023R1804-002.001), wczytana 2026-10-20.
Plik: `.claude/knowledge/eu-afir/doc.txt` (3183 linii). Tekst skonsolidowany nie ma mocy prawnej (zastrzeżenie na początku
pliku); wiążąca jest wersja w Dzienniku Urzędowym. To nie porada prawna.

## Spis treści
1. Definicje, które rozstrzygają zakres
2. Płatność ad hoc (Art. 5(1)-(2))
3. Cena (Art. 5(3)-(6))
4. Cyfrowe połączenie, smart charging, kabel (Art. 5(7)-(11))
5. Dane i NAP (Art. 20)
6. Aneks II: złącza i komunikacja
7. Cele infrastruktury (Art. 3, 4)
8. Akty delegowane, wykonawcze, przegląd

## 1. Definicje (Art. 2, linie 70-513)
| Pojęcie | Znaczenie wg tekstu | Pkt, linia |
|---|---|---|
| ad hoc price | cena, którą operator pobiera od użytkownika za ładowanie ad hoc | (2), 80 |
| recharge on an ad hoc basis | usługa kupiona bez rejestracji, umowy ani relacji handlowej z operatorem poza zakupem usługi | (47), 360 |
| bi-directional recharging | smart charging, w którym prąd może płynąć z baterii do punktu | (11), 153 |
| digitally-connected recharging point | wysyła i odbiera informacje w czasie rzeczywistym, komunikuje się dwukierunkowo z siecią i pojazdem, jest zdalnie monitorowany i sterowany (start i stop sesji, pomiar przepływów) | (17), 183 |
| smart recharging | natężenie prądu do baterii dostosowywane w czasie rzeczywistym na podstawie informacji z komunikacji elektronicznej | (65), 462 |
| normal power / high-power | do 22 kW włącznie / powyżej 22 kW | (37), (31): 304, 268 |
| recharging point | interfejs ładujący tylko jeden pojazd naraz (może mieć kilka złączy); stacja = instalacja z jednym lub wieloma punktami; pula = stacje w jednym miejscu | (48), (52), (51): 367, 394, 390 |
| publicly accessible | miejsce otwarte dla ogółu, także na terenie prywatnym i z ograniczeniami lub warunkami dostępu | (45), 340 |
| operator of a recharging point | podmiot odpowiedzialny za zarządzanie i działanie punktu, także w imieniu i na rzecz eMSP | (39), 311 |
| mobility service provider | osoba prawna świadcząca za wynagrodzeniem usługi użytkownikowi, w tym sprzedaż ładowania | (36), 300 |
| static data / dynamic data | rzadko zmieniane / zmieniane często lub regularnie | (66), (20): 468, 198 |

Wniosek: parking sklepowy z bramą otwartą dla klientów jest „publicznie dostępny”. Flota z dostępem tylko dla własnych
pojazdów za zamkniętą bramą wymaga oceny prawnej **[do weryfikacji]**.

## 2. Płatność ad hoc (Art. 5(1)-(2), linie 921-972)
- Operator musi umożliwić ładowanie ad hoc w każdym publicznym punkcie.
- Punkty uruchomione od 13.04.2024: płatność instrumentem powszechnym w UE; co najmniej jedno z: (a) czytniki kart,
  (b) urządzenia bezstykowe czytające karty, (c) tylko dla punktów **< 50 kW**: urządzenie z internetem i bezpieczną płatnością,
  np. kod QR.
- Od **01.01.2027**: punkty **≥ 50 kW** na sieci TEN-T lub na parkingu bezpiecznym (safe and secure parking area), także
  uruchomione przed 13.04.2024, muszą spełniać (a) lub (b). QR nie liczy się. Linia 945.
- Jeden terminal może obsługiwać kilka punktów w puli. Punkty bezpłatne nie podlegają wymogowi.
- Art. 5(2) (linia 960): przy automatycznej autoryzacji użytkownik zawsze może z niej zrezygnować i ładować ad hoc albo na
  innej umowie; opcja ma być jasno pokazana i wygodna na każdym takim punkcie.
- Art. 5(11) (linia 1066): właściciel nie będący operatorem musi dać operatorowi punkt, który technicznie pozwala spełnić
  Art. 5(2), (7), (8) i (10).
- Dla CPMS: ścieżka „sesja bez konta” po płatności na terminalu; technika płatności w dom-ev-payments.

## 3. Cena (Art. 5(3)-(6), linie 973-1042)
| Ustęp | Treść | Dla CPMS |
|---|---|---|
| 5(3) | ceny rozsądne, łatwo porównywalne, przejrzyste, niedyskryminujące; bez dyskryminacji między użytkownikami i eMSP oraz między eMSP; poziom cen można różnicować tylko proporcjonalnie i obiektywnie uzasadnione | reguły taryf per eMSP muszą mieć uzasadnienie, które da się udokumentować |
| 5(4) pierwszy akapit | punkty ≥ 50 kW: cena ad hoc oparta na cenie za kWh; dodatkowo opłata za zajęcie jako cena za minutę | element ENERGY jest podstawą, minutowy to dodatek |
| 5(4) drugi akapit | ≥ 50 kW: na stacji pokazać cenę za kWh i ewentualną opłatę za minutę przed rozpoczęciem sesji | wyświetlacz, naklejka, ekran aplikacji |
| 5(4) trzeci akapit | < 50 kW: informacja o cenie ze wszystkimi składnikami, jasno i łatwo dostępna przed startem; kolejność: za kWh, za minutę, za sesję, inne | kolejność składników w UI |
| 5(4) ostatni akapit | „pierwszy i drugi akapit” stosuje się do wszystkich punktów uruchomionych od 13.04.2024 | punkty starsze i akapit trzeci: wykładnia **[do weryfikacji]** |
| 5(5) | eMSP: cena rozsądna, przejrzysta, niedyskryminująca; przed startem sesji wszystkie informacje o cenie tej sesji, wolno dostępnymi, powszechnie obsługiwanymi środkami elektronicznymi, ze składnikami rozdzielonymi, w tym koszty roamingu i inne opłaty eMSP; brak dopłaty za roaming transgraniczny | ekran „cena tej sesji” przed Start; roaming jako osobna pozycja |
| 5(6) | organy państw członkowskich monitorują zgodność z 5(3) i 5(5) | audyt cen może przyjść od organu krajowego (PL: dom-ev-regulations-pl) |

Liczenie ceny z taryfy OCPI i zaokrąglanie: dom-ev-tariffs-pricing. Przegląd Art. 24(2) obejmie m.in. adekwatność składników
ceny z Art. 5(4) i środków płatności z Art. 5(1) (termin przeglądu: 31.12.2026).

## 4. Cyfrowe połączenie, smart charging, kabel (Art. 5(7)-(10), linie 1043-1065)
| Ustęp | Obowiązek | Od kiedy |
|---|---|---|
| 5(7) | wszystkie publiczne punkty operatora są cyfrowo połączone | 14.10.2024 |
| 5(8) | publiczne punkty zbudowane po 13.04.2024 lub odnowione po 14.10.2024 zdolne do smart charging | 13.04.2024 / 14.10.2024 |
| 5(10) | punkty DC mają zainstalowany stały kabel | 14.04.2025 |

Dla firmware i CSMS: zdalny start i stop, pomiar przepływów, sterowanie mocą (profile ładowania w OCPP). Bidirectional w AFIR
to tylko definicja i raport państw (Art. 15(3)); obowiązku V2G dla punktów publicznych Art. 5 nie nakłada.

## 5. Dane i NAP (Art. 20, linie 1911-2147)
- **IDRO (ust. 1):** państwo wyznacza organizację, która nadaje unikalne kody ID co najmniej operatorom punktów i eMSP,
  do 14.04.2025. Formaty identyfikatorów: dom-ev-identifiers.
- **Ust. 2 (od 14.04.2025, dane bez opłat):** operator lub właściciel zapewnia dostępność:
  - statyczne (a): nazwa prawna i handlowa, liczba punktów, wsparcie, telefon helpdesku, udogodnienia, GNSS i adres,
    godziny otwarcia, strefa czasowa, zgodność pojazdów, miejsca parkingowe, formy płatności (czytnik, bezstykowa, inne ad
    hoc, dostawcy, umowa);
  - statyczne (b) dla ładowania: ID punktu (złącza), liczba i typ złączy, rodzaj prądu, maksymalna moc stacji i punktu,
    eMSP z umową, **Plug-and-charge**, **smart recharging services**, 100 % OZE;
  - dynamiczne (f): **operational status, availability, ad hoc price** (linia 2031).
  Lista (a)-(b) ma zmianę oznaczoną M2: rozp. (UE) 2025/671 (treść aktu poza tekstem skonsolidowanym nie była czytana **[do weryfikacji]**).
- **Ust. 3 (linia 2047):** operator lub właściciel ustanawia **API** z darmowym i nieograniczonym dostępem do tych danych
  i zgłasza informacje o API do krajowych punktów dostępu; API ma spełniać wspólne wymogi techniczne z aktów delegowanych (ust. 6).
- **Ust. 4:** państwa udostępniają dane przez NAP na zasadach otwartych i niedyskryminujących (rozp. delegowane (UE) 2022/670),
  do 31.12.2024. **Ust. 5:** wspólny europejski punkt dostępu do 31.12.2026 (za 2 miesiące od dziś, 2026-10-20).
- **Ust. 6-8:** Komisja może zmieniać listę danych i ustalić wspólny interfejs API; akty wykonawcze (format, częstotliwość,
  jakość) z rozsądnymi okresami przejściowymi. Czy przyjęto akt o wspólnym API: **[do weryfikacji]**, w tekście nie ma odniesienia.
- Dla CPMS: lokalizacje OCPI Locations mapują się na dane statyczne, statusy na dynamiczne (dom-ev-ocpi); eksport do NAP
  to zadanie osobne od roamingu; ad hoc price musi być spójna z ceną na stacji.

## 6. Aneks II: złącza i komunikacja (linie 2505-3073)
| Pkt | Wymóg | Od kiedy |
|---|---|---|
| 1.1-1.2 | AC: Type 2 (EN IEC 62196-2:2022); DC: Combo 2 (EN IEC 62196-3:2022) dla punktów zainstalowanych lub odnowionych | 08.01.2026 |
| 1.6 | DC dla pojazdów lekkich i ciężkich: Combo 2 | 08.01.2026 |
| 2.1.1 | publiczne AC i DC: EN ISO 15118-1, -2, -3, -4, -5 | 08.01.2026 |
| 2.1.2 | publiczne: EN ISO 15118-20:2022; z automatyczną autoryzacją (np. Plug & Charge): jednocześnie -2 i -20 | 01.01.2027 |
| 2.1.3 | prywatne: EN IEC 61851-1 (Mode 2), ISO 15118-20 (Mode 3 i 4) | 01.01.2027 |
| 2.2-2.4 | komunikacja punkt–CPMS, operator–eMSP–roaming, operator–OSD: w tekście bez treści | brak |

„Zainstalowany” = pierwsze ustawienie całego sprzętu, „odnowiony” = poważna lub pełna wymiana (pkt 0). Pozostałe punkty (L-category, autobusy,
wireless) w liniach 2585-2783. ISO 15118: dom-ev-charging.

## 7. Cele infrastruktury (Art. 3-4, linie 514-920)
To zobowiązania państw (moc łączna na pojazd: 1,3 kW na BEV i 0,80 kW na PHEV; pule co 60 km na TEN-T, 150 kW i 350 kW dla
ciężkich), nie obowiązki CPO. Dla CPMS ważne jako kontekst biznesowy (koncesje, dotacje); szczegóły w linii 514 i 719.

## 8. Akty delegowane, wykonawcze, przegląd
| Co | Gdzie | Uwaga |
|---|---|---|
| zmiany listy danych i wspólne API | Art. 20(6), 22 | delegacja na 5 lat od 13.04.2024, domyślnie przedłużana |
| zmiany Aneksu II | Art. 21(3), 22 | w tym normy dla pkt 2.2-2.4; z okresami przejściowymi (Art. 21(6)) |
| akty wykonawcze o formacie danych | Art. 20(7) | uzupełniają rozp. delegowane (UE) 2022/670 |
| przegląd rozporządzenia | Art. 24(2) | do 31.12.2026 i co 5 lat |
| stosowanie | Art. 26 | od 13.04.2024; uchylenie dyrektywy 2014/94/UE: Art. 25 |
