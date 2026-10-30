---
name: dom-ev-site-development
description: Użyj przy budowie lokalizacji ładowania od pomysłu do uruchomienia — wybór miejsca, punktacja, przyłącze od OSD, budowa, pozwolenia, dzierżawa, pipeline.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy zespół rozwoju sieci lub software go wspierający buduje nową lokalizację ładowania — wybór miejsca (popyt, czas postoju, typ ładowarki, konkurencja, dostęp vanów, przyczep, ciężarówek), punktacja z wagami, ograniczenia korytarzowe AFIR TEN-T i NEVI 680.106, przyłącze od OSD, budowa, pozwolenia, dzierżawa, pipeline lead → operacje z bramkami go/no-go, future-proofing, przekazanie do rejestru assetów i CSMS, publikacja w OCPI (facilities, opening_times, parking). Nie do podziału mocy i limitu przyłącza w eksploatacji (dom-ev-energy-management), NPV i marży (dom-ev-business-economics), sprzętu ładowarki (dom-ev-charger-hardware), pełnej mapy przepisów (dom-ev-regulations-eu, dom-ev-regulations-pl) ani rejestru assetów w eksploatacji (dom-ev-asset-operations)."
  slowa: "nowa lokalizacja, budowa stacji ładowania, wybór lokalizacji, site selection, pipeline lokalizacji, warunki przyłączenia, wniosek o przyłączenie, moc przyłączeniowa, kVA, stacja transformatorowa, czas oczekiwania OSD, site host, gospodarz lokalizacji, dzierżawa, podział przychodu, miejsca parkingowe, pull-through, przyczepa, ciężarówki, MCS, bollardy, CCTV, światłowód, pozwolenie na budowę, parking podziemny, przeciwpożarowe, go/no-go, future-proofing, punktacja lokalizacji, TEN-T, AFIR 60 km, NEVI 680.106, facilities, opening_times, parking_places, commissioning"
---

# Budowa lokalizacji ładowania — od leada do operacji

Skill prowadzi lokalizację przez etapy i bramki oraz mówi, jakie dane zbiera zespół i software na każdym etapie.
Kolejność: **twarde ograniczenia → punktacja → przyłącze → umowa → projekt i budowa → commissioning → przekazanie**.
Liczby z [do weryfikacji] pochodzą z przeglądu wiedzy ogólnej, nie z bazy. Cen sprzętu, przyłączy, energii i stawek
dzierżawy tu nie ma — wpisujesz własne, ze źródłem.

## Etapy i bramki
| # | Etap | Wynik (artefakt) | Bramka wyjścia |
|---|---|---|---|
| 1 | lead | adres, właściciel, powód (ruch, flota, korytarz) | nie ma knock-outu (tabela niżej) |
| 2 | ocena | karta punktacji, wstępne zapytanie do OSD | wynik ≥ progu, ekonomia wstępna |
| 3 | umowa | LOI, dzierżawa lub zgoda właściciela | podpisana, z prawem do przyłącza i dostępu 24/7 (jeśli publiczna) |
| 4 | projekt | układ miejsc, schemat jednokreskowy, wniosek o przyłączenie | **go/no-go z ekonomią** (dom-ev-business-economics) |
| 5 | przyłącze | warunki i umowa o przyłączenie, realizacja przez OSD | energia na rozdzielnicy głównej |
| 6 | budowa | roboty, montaż, łączność | odbiór, badania (UDT w PL) |
| 7 | commissioning | testy ładowarek w CSMS, publikacja | dom-ev-charger-onboarding, wpis w rejestrze |
| 8 | operacje | stacja w eksploatacji | przekazanie (sekcja „Przekazanie”) |

Przyłącze rusza **równolegle** z umową i projektem, nie po pozwoleniu.
Etap 5 bywa najdłuższy [do weryfikacji]; termin wpisujesz tylko z pisma OSD.

## 1. Wybór lokalizacji
Najpierw **knock-outy** (odrzuć bez punktacji), potem punktacja:
| Knock-out | Dlaczego |
|---|---|
| brak zgody właściciela lub tytułu do gruntu | bez niej nie ma przyłącza ani pozwolenia |
| OSD nie przewiduje mocy w horyzoncie biznesowym | stacja bez energii; rozważ BESS albo odpuść |
| korytarz: układ łamie ograniczenia AFIR lub NEVI (niżej) | utrata dotacji lub statusu stacji korytarzowej |
| brak dojazdu dla typu pojazdów celu (van, przyczepa, ciężarówka) | miejsca nieużyteczne dla segmentu |
| ryzyko prawne (konserwator, powódź, brak dostępu 24/7 przy ofercie publicznej) | odmowa na etapie pozwoleń |

**Czas postoju → typ ładowarki** (progi z przeglądu [do weryfikacji]):
| Postój | Typ | Typowe miejsce |
|---|---|---|
| trasa, 5–40 min | DC 150–400 kW | korytarz, MOP, stacja paliw |
| 1–3 h | AC 22 kW albo DC 50 kW | handel, gastronomia, kino |
| 8 h i więcej | AC 7–11 kW | biuro, hotel, parking nocny |
Auto bierze tyle, ile pozwala krzywa baterii, nie tyle, ile ma ładowarka (dom-ev-vehicle-battery).

**Punktacja jako model z wagami.** Cechy oceniasz 0–5, wynik = Σ(waga × ocena) / 5 (skala 0–100). Wagi poniżej to
**ilustracja**, każdy operator dobiera własne i kalibruje je na wynikach istniejących stacji:
| Cecha | Waga | Wskazówka do oceny |
|---|---|---|
| popyt (ruch, EV w okolicy, flota, tranzyt) | 25 | dane o ruchu i rejestracjach EV z zewnątrz; nie z przeczucia |
| przyłącze (dostępna moc, koszt, czas) | 25 | pismo OSD > szacunek |
| dopasowanie czasu postoju do oferty | 10 | czy ludzie i tak tu stoją |
| konkurencja (odległość, moc, uptime konkurentów) | 10 | brak konkurenta bywa sygnałem braku popytu |
| udogodnienia i bezpieczeństwo (oświetlenie, WC, kawa, CCTV) | 10 | atrybuty trafią do OCPI `facilities` |
| dostęp pojazdów (van, przyczepa, ciężarówka) | 5 | patrz niżej |
| umowa i gospodarz | 10 | długość, wyłączność, dostęp 24/7 |
| rezerwa na rozbudowę | 5 | miejsce, rury, moc |
Sprawdź **wrażliwość**: czy kolejność zmienia się po ±20 % wagi popytu i przyłącza.

**Dostęp pojazdów.** Van (wysokość, szlaban, garaż), auto z przyczepą (miejsca **pull-through**: wjazd i wyjazd bez
cofania), ciężarówka (promienie skrętu, nośność nawierzchni, ładowarki MCS [do weryfikacji] — dla ciężkich szukaj
miejsc na bezpiecznych parkingach, art. 4 AFIR). W OCPI 2.3.0 te cechy opisuje obiekt `Parking` (sekcja 5).

### Ograniczenia korytarzowe (twarde, gdy stacja ma być w sieci korytarzowej)
| Akt | Wymóg (własnymi słowami) | Źródło |
|---|---|---|
| AFIR art. 3 ust. 4 lit. a | sieć bazowa TEN-T, lekkie pojazdy: pula co najwyżej co 60 km w każdym kierunku; do 31.12.2025 pula ≥ 400 kW i ≥ 1 punkt ≥ 150 kW; do 31.12.2027 ≥ 600 kW i ≥ 2 punkty ≥ 150 kW | eu-afir |
| AFIR art. 3 ust. 4 lit. b | sieć kompleksowa: ≥ 300 kW i ≥ 1 punkt ≥ 150 kW (2027 dla ≥ 50 % długości, 2030 dla całości); od 31.12.2035 ≥ 600 kW i ≥ 2 punkty ≥ 150 kW | eu-afir |
| AFIR art. 3 ust. 6–9 | jedna pula na oba kierunki, jeśli łatwo dostępna z obu i oznakowana; odstępstwa (do 100 km przy małym ruchu) tylko przez państwo | eu-afir |
| AFIR art. 4 | ciężkie: pule ≥ 1 400 kW z punktem ≥ 350 kW (2025); sieć bazowa od 2027 ≥ 2 800 kW i 2 punkty ≥ 350 kW; bezpieczne parkingi ≥ 2 stacje ≥ 100 kW (2027), ≥ 4 (2030) | eu-afir |
| NEVI 680.106(b) | stacja korytarzowa: ≥ 4 podłączone porty DC, jednoczesne ładowanie ≥ 4 pojazdów | us-nevi |
| NEVI 680.106(d)(1), (e) | DC 250–920 V, ≥ 150 kW ciągle na port (podział mocy dozwolony, jeśli port nadal spełnia żądanie do 150 kW); korytarz 24/7 przez cały rok | us-nevi |
AFIR zobowiązuje **państwa**, nie pojedynczego CPO (dom-ev-regulations-eu); ograniczeniem staje się przez koncesje,
dotacje i plan krajowy. Sprawdzaj z aktualnym tekstem i warunkami konkursu.

## 2. Przyłącze — wąskie gardło
| Pojęcie | Co zrobić |
|---|---|
| moc w kVA vs kW | zamów kVA; kW ≈ kVA × współczynnik mocy; marża na straty i sprawność modułów |
| wniosek do OSD | moc, napięcie (nN lub SN), lokalizacja punktu przyłączenia, harmonogram; odpowiedź = warunki przyłączenia |
| stacja transformatorowa SN/nN | przy dużej mocy (DC wielopunktowe) stacja własna albo OSD; to największy koszt i czas |
| rozdzielnice, licznik, uziemienie | rozdzielnica główna z zapasem pól; licznik OSD wyznacza limit w eksploatacji; uziemienie z projektu |
| etapowanie | zamów moc docelową, uruchom część; rury i miejsce pod resztę |
Szczegóły: `references/przylacze-i-budowa.md`. Przy słabym przyłączu:
**BESS** buforujący szczyt, **load management** (dom-ev-energy-management), mniej szybkich punktów, odsunięcie terminu.
Polska ustawa o elektromobilności: art. 12b ust. 9–10 (budynki: koszty zmiany umowy o przyłączenie ponosi wnioskodawca,
OSD montuje układ pomiarowy punktu), art. 62 (plan gminy i program przyłączania OSD z „technicznymi i ekonomicznymi
warunkami” oraz „przewidywanymi terminami”). Terminów przyłączenia ustawa **nie** zawiera — nie wpisuj ich z pamięci.

## 3. Budowa
Fundamenty, miejsca (wymiary, dostępność, pull-through), bollardy, zadaszenie, oświetlenie, odwodnienie, oznakowanie,
CCTV, łączność (LTE + światłowód, redundancja). Ustawa art. 13: Polskie Normy, w tym bezpieczeństwo pożarowe i **dostęp
dla osób niepełnosprawnych**; badanie UDT przed oddaniem do eksploatacji (art. 16, dom-ev-regulations-pl). Przepisy
przeciwpożarowe i parkingi podziemne: [do weryfikacji] — brak aktu w bazie. Szczegóły: `references/przylacze-i-budowa.md`.

## 4. Pozwolenia i umowy
Ścieżka: ustalenia planistyczne → pozwolenie na budowę lub zgłoszenie [do weryfikacji] → zgoda właściciela → dzierżawa
i podział przychodu z gospodarzem. Typowa długość dzierżawy [do weryfikacji]; bez prawa do terenu na okres zwrotu nie
przechodzisz bramki go/no-go. Klauzule: `references/pozwolenia-umowy-pipeline.md`.

## 5. Dane lokalizacji i publikacja (OCPI)
Atrybuty z projektu stają się polami `Location` (dom-ev-ocpi, baza `ocpi-2.2.1-d2` i `ocpi-2.3.0`):
| Cecha z projektu | Pole OCPI |
|---|---|
| typ miejsca | `parking_type` (ALONG_MOTORWAY, PARKING_GARAGE, PARKING_LOT, ON_DRIVEWAY, ON_STREET, UNDERGROUND_GARAGE) |
| udogodnienia | `facilities` (m.in. HOTEL, RESTAURANT, CAFE, MALL, SUPERMARKET, FUEL_STATION, WIFI; brak wartości dla toalet) |
| dostęp 24/7 lub godziny | `opening_times`: `twentyfourseven`, `regular_hours`, `exceptional_openings`, `exceptional_closings` |
| ograniczenia miejsca | `parking_restrictions` na EVSE (EV_ONLY, PLUGGED, DISABLED, CUSTOMERS, MOTORCYCLES) |
| poziom w garażu | `floor_level` na EVSE |
| wymiary, pull-through, zadaszenie | 2.3.0: `parking_places` (`Parking`: `vehicle_types`, `parking_space_length` i `_width` w cm, `drive_through`, `roofed`, `lighting`) + `EVSEParking` na EVSE |
`Parking` jest **nowe w 2.3.0**, nie ma go w 2.2.1. `vehicle_types` obejmuje m.in. VAN, PERSONAL_VEHICLE_WITH_TRAILER,
TRUCK_WITH_TRAILER, BUS. Zakres po stronie danych: dom-ev-ocpi.

## Przekazanie do eksploatacji
Po commissioningu lokalizacja ma: wpis w rejestrze assetów (stacje, szafy, moduły, transformator, BESS, modemy, liczniki
z datą legalizacji, elementy budowlane — dom-ev-asset-operations), identyfikatory EVSE (dom-ev-identifiers), ładowarki
zaakceptowane w CSMS (dom-ev-charger-onboarding), limit przyłącza dla zarządzania energią (dom-ev-energy-management),
numer EIPA i badanie UDT w PL (dom-ev-regulations-pl), dokumentację powykonawczą.

## Przykład
Wejście: trzy leady (A hipermarket, B stacja przy krajowej, C parking biurowca), wagi jak wyżej.
Oceny (popyt, przyłącze, postój, konkurencja, udogodnienia, dostęp, umowa, rozbudowa): A = 4,3,5,3,5,3,4,3;
B = 3,2,4,4,4,5,3,4. Wynik: A = (100+75+50+30+50+15+40+15)/5 = **75**, B = (75+50+40+40+40+25+30+20)/5 = **64**.
Decyzja: A idzie do etapu 3. B przegrywa głównie na przyłączu (ocena 2); jeśli celem są vany i przyczepy, podnieś wagę
dostępu pojazdów i przelicz. Wynik poniżej progu to „nie teraz”, nie „nigdy”. Przed bramką 4 policz ekonomię:
`python3 .claude/skills/dom-ev-business-economics/scripts/station_economics.py <stacja>.json` (kod wyjścia 1 = NPV < 0).

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| model punktacji, dane popytu, konkurencja, korytarz | `references/wybor-lokalizacji.md` |
| przyłącze krok po kroku, rozdzielnice, wymiary miejsc, łączność, przeciwpożarowe | `references/przylacze-i-budowa.md` |
| pozwolenia, dzierżawa, podział przychodu, tabela pipeline i pola danych, future-proofing | `references/pozwolenia-umowy-pipeline.md` |

## Pułapki
- Punktacja bez knock-outów: lokalizacja z wysokim popytem i bez energii wygrywa ranking, którego nie da się zbudować.
- Moc ładowarek = moc przyłącza: dodaj współczynnik mocy, straty i potrzeby własne (chłodzenie, oświetlenie).
- Wniosek o przyłączenie po pozwoleniu na budowę: tracisz miesiące; start równolegle.
- Termin OSD z przeglądu w harmonogramie zamiast terminu z pisma.
- AFIR jako obowiązek CPO; to zobowiązanie państw, ale warunek dotacji i planów.
- `Parking` w OCPI 2.2.1: pole jest dopiero w 2.3.0.
- Brak rur i miejsca pod rozbudowę: druga faza to drugi wykop.

## Checklista
- [ ] knock-outy sprawdzone przed punktacją; wagi zapisane jako ilustracja lub kalibracja
- [ ] typ ładowarki dobrany do czasu postoju; progi oznaczone [do weryfikacji]
- [ ] korytarz: odległość i moc puli (AFIR art. 3–4) lub konfiguracja NEVI 680.106 sprawdzone w aktualnym tekście
- [ ] wniosek do OSD złożony równolegle; termin tylko z pisma OSD
- [ ] umowa daje prawo do terenu na okres zwrotu; dostęp 24/7 zapisany, jeśli stacja publiczna
- [ ] go/no-go z ekonomią przed budową
- [ ] rury, miejsce i moc pod rozbudowę zapisane w projekcie
- [ ] atrybuty gotowe do OCPI; przekazanie do rejestru assetów i CSMS wykonane

## Źródła
- AFIR (rozp. UE 2023/1804, tekst 08.01.2026), art. 3–4, eur-lex.europa.eu/eli/reg/2023/1804/oj, pobrane 2026-10-20 (baza `eu-afir`, linie 561–800).
- NEVI, 23 CFR 680.106, ecfr.gov, pobrane 2026-10-20 (baza `us-nevi`, linie 80–119).
- Ustawa o elektromobilności i paliwach alternatywnych (Dz.U. 2026 poz. 1243), art. 12b, 12c, 13, 15, 16, 62, isap.sejm.gov.pl, pobrane 2026-10-20 (baza `pl-elektromobilnosc`).
- OCPI 2.2.1-d2 i 2.3.0, mod_locations.asciidoc, github.com/ocpi/ocpi, pobrane 2026-10-20 (bazy `ocpi-2.2.1-d2`, `ocpi-2.3.0`).
- Przegląd wiedzy ogólnej EV od użytkownika, 2026-10-20 (progi, praktyki) — [do weryfikacji].
