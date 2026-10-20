# Ustawa o elektromobilności a AFIR — co gdzie jest

AFIR = rozporządzenie (UE) 2023/1804, wersja skonsolidowana EN z 08.01.2026 (`eu-afir`, `.claude/knowledge/eu-afir/doc.txt`, pobrane
2026-10-20). Rozporządzenie wiąże w całości i stosuje się bezpośrednio od 2024-04-13 (art. 26, L2368-2376); ustawa z 2018 r. wdrażała
poprzednią dyrektywę 2014/94/UE (przypis 1 tekstu jednolitego, L92-99), którą AFIR uchyla od 2024-04-13 (art. 25, L2357-2362). Treść AFIR
jako prawa UE opisuje dom-ev-regulations-eu; tu tylko styk z ustawą. To nie porada prawna.

## Spis treści
- Definicje: różnice
- Co ustawa doprecyzowuje, a co AFIR reguluje wprost
- Dane i identyfikatory
- Lista rzeczy do weryfikacji

## Definicje: różnice
| Pojęcie | Ustawa | AFIR | Skutek |
|---|---|---|---|
| publicznie dostępna | ogólnodostępna: równoprawne traktowanie dla każdego posiadacza EV i hybrydy (art. 2 pkt 6, L88) | infrastruktura w miejscu otwartym dla ogółu, także na terenie prywatnym i z ograniczeniami dostępu (art. 2 pkt 45, L340-346) | stacja może podlegać AFIR, a nie ustawie; **[do weryfikacji]** |
| punkt ładowania | jeden pojazd; także wymiana akumulatora (pkt 17) | jeden pojazd naraz; wyłącza urządzenia do 3,7 kW o innym podstawowym celu (pkt 48, L367-372) | podobna idea, inny zakres |
| stacja | obiekt z oprogramowaniem, stanowiskami i instalacją do przyłącza (pkt 27) | fizyczna instalacja z jednym lub więcej punktów (pkt 52, L394) | ustawa wlicza oprogramowanie |
| operator | odpowiada za budowę, zarządzanie, bezpieczeństwo, eksploatację (pkt 7) | zarządza i obsługuje punkt oraz świadczy usługę użytkownikom, także w imieniu MSP (pkt 39, L311) | operator AFIR bliższy dostawcy usługi z ustawy |
| usługa ładowania | zadania dostawcy w art. 3 ust. 2 | sprzedaż lub dostarczenie energii i usług powiązanych (pkt 53, L398) | |
| MSP | brak pojęcia | osoba prawna świadcząca za wynagrodzeniem usługi użytkownikowi (pkt 36, L300) | ustawa nie reguluje eMSP |

## Co ustawa doprecyzowuje, a co AFIR reguluje wprost
| Temat | Ustawa (artykuł) | AFIR (artykuł, linie) | Wniosek |
|---|---|---|---|
| płatność ad hoc | brak; art. 7 zakazuje wymogu umowy | art. 5 ust. 1: ładowanie ad hoc, czytnik kart lub urządzenie bezstykowe, QR poniżej 50 kW; od 2027-01-01 także punkty od 50 kW przy TEN-T sprzed 2024-04-13 (L921-960) | obowiązek tylko z AFIR |
| automatyczne uwierzytelnianie | brak | art. 5 ust. 2: prawo użytkownika do ładowania ad hoc lub innego kontraktu (L960-972) | AFIR |
| cena | strona dostawcy (art. 3 ust. 2 pkt 3), rejestr (art. 42 ust. 6) | art. 5 ust. 3-5: rozsądna, przejrzysta, bez dyskryminacji; od 50 kW za kWh plus opłata za zajęcie za minutę; pokazana przed sesją; kolejność składników poniżej 50 kW (L973-1033) | ustawa określa miejsce publikacji, AFIR treść ceny |
| nadzór nad cenami | URE nie ma w art. 45 kary za cenę | art. 5 ust. 6: państwa monitorują zgodność (L1034-1042) | organ i sankcje **[do weryfikacji]** |
| łączność i smart charging | brak (poza oprogramowaniem i pomiarem, art. 3 ust. 1 pkt 4) | art. 5 ust. 7-8, 10: punkty połączone cyfrowo do 2024-10-14, smart charging dla nowych, stały kabel DC do 2025-04-14 (L1043-1065) | AFIR; sprzęt: dom-ev-charger-hardware |
| właściciel a operator | brak | art. 5 ust. 11: właściciel zapewnia operatorowi punkt umożliwiający spełnienie obowiązków | AFIR |
| dostęp dostawców do stacji | art. 3 ust. 1 pkt 10 | brak odpowiednika | tylko ustawa |
| badanie techniczne przed startem | art. 15-16 | brak | tylko ustawa |

## Dane i identyfikatory
| Temat | Ustawa | AFIR | Uwaga |
|---|---|---|---|
| dane o stacji | rejestr EIPA: współrzędne, ceny, metody płatności, dostępność (art. 42 ust. 3) | art. 20 ust. 2: dane statyczne (operator, liczba punktów, lokalizacja, godziny, płatności, ID punktu, moc, złącza) i dynamiczne (status, dostępność, cena ad hoc), bezpłatnie, do 2025-04-14 (L1911-2046) | zakres AFIR szerszy niż rejestr |
| API | usługa sieciowa EIPA | art. 20 ust. 3: API operatora z bezpłatnym i nieograniczonym dostępem, zgłoszone do krajowych punktów dostępu (L2047-2067) | dwa kanały — EIPA i API |
| krajowy punkt dostępu | brak | art. 20 ust. 4: dane dostępne w NAP do 2024-12-31; wspólny punkt europejski do 2026-12-31 (L2068-2090) | który organ prowadzi NAP w Polsce — **[do weryfikacji]** |
| identyfikatory | numer EIPA (art. 41b) | art. 20 ust. 1: IDRO nadaje ID operatorom i MSP do 2025-04-14 (L1911-1916) | czy UDT = IDRO oraz zgodność numeru EIPA z formatem ID — **[do weryfikacji]** (dom-ev-identifiers) |

## Lista rzeczy do weryfikacji
1. Rozporządzenia wykonawcze do ustawy (art. 17, art. 41b ust. 5, art. 42 ust. 9 i 11) — nie ma ich w bazie.
2. Kto wymusza AFIR art. 5 w Polsce i jakie sankcje stosuje (ustawa w tym tekście ich nie zawiera).
3. Czy stacja „dla klientów” jest ogólnodostępna w rozumieniu art. 2 pkt 6; dla AFIR — art. 2 pkt 45.
4. Format i układ współrzędnych w usłudze sieciowej EIPA oraz zgodność z formatem danych AFIR i OCPI.
5. Wyznaczenie IDRO i krajowego punktu dostępu w Polsce.
6. Wpływ aktualizacji firmware na obowiązek ponownego badania UDT.
7. Ustawy późniejsze niż 26.08.2026.
