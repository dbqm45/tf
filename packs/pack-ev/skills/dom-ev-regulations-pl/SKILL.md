---
name: dom-ev-regulations-pl
description: Użyj przy polskim prawie dla ładowania EV — ustawa o elektromobilności, numer EIPA i dane do rejestru, badanie UDT, role operatora i dostawcy, kary URE i UDT.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy stacja lub CPMS w Polsce ma spełnić ustawę z 11.01.2018 r. o elektromobilności i paliwach alternatywnych (tekst jednolity Dz.U. 2026 poz. 1243, stan prawny 26.08.2026) — definicje (ogólnodostępna stacja, punkt ładowania, operator, dostawca usługi ładowania), obowiązki operatora i dostawcy, badanie UDT przed oddaniem do eksploatacji, numer EIPA i dane do Ewidencji Infrastruktury Paliw Alternatywnych (dostępność natychmiast, cena w ciągu godziny), rola URE i OSD, kary, przepisy przejściowe, relacja do AFIR i tabela co to znaczy dla CPMS, aplikacji i raportowania. To nie porada prawna. Nie do przepisów UE jako takich (dom-ev-regulations-eu), USA (dom-ev-regulations-us), techniki płatności kartą (dom-ev-payments), liczenia ceny z taryfy (dom-ev-tariffs-pricing) ani sprzętu i licznika (dom-ev-charger-hardware)."
  slowa: "ustawa o elektromobilności, elektromobilność i paliwa alternatywne, Dz.U. 2026 poz. 1243, ogólnodostępna stacja ładowania, operator stacji, dostawca usługi ładowania, punkt ładowania, EIPA, numer EIPA, Ewidencja Infrastruktury Paliw Alternatywnych, UDT, Urząd Dozoru Technicznego, badanie techniczne stacji, oddanie do eksploatacji, wstrzymanie eksploatacji, URE, Prezes URE, OSD, kara pieniężna, art. 45, art. 42, art. 41b, art. 16, dostępność punktu, cena usługi ładowania, dostęp dostawców do stacji, wymóg umowy, polskie przepisy, Polish EV charging law, EIPA registry, public charging station Poland, AFIR a ustawa"
---

# Polskie przepisy dla ładowania EV (ustawa o elektromobilności)

**To nie porada prawna.** Skill mapuje tekst ustawy na decyzje w CPMS, aplikacji i raportowaniu; wiążącą wykładnię daje
prawnik, UDT albo URE. Źródła w bazie wiedzy fabryki:
- `pl-elektromobilnosc` — ustawa z 11.01.2018 r., **tekst jednolity Dz.U. 2026 poz. 1243, stan prawny na 26.08.2026**
  (plik od człowieka, wczytany 2026-10-20). Zmian po 26.08.2026 nie sprawdzono.
- `pl-udt`, `pl-eipa`, `pl-ure` — tylko strony główne; `eu-afir` — AFIR (EN, skonsolidowany 08.01.2026).
- **Rozporządzeń wykonawczych nie ma w bazie** (wymagania techniczne i zakres badań z art. 17, wzór zgłoszenia z art. 42
  ust. 11, stawki opłat EIPA z art. 41b ust. 5, specyfikacja usługi sieciowej z art. 42 ust. 9) — szczegóły z nich to **[do weryfikacji]**.

## Procedura
1. **Ustal rolę wg ustawy**: operator ogólnodostępnej stacji (art. 2 pkt 7) i dostawca usługi ładowania (art. 3 ust. 2) to
   osobne role; operator może pełnić obie (art. 6). Mapowanie na CPO i eMSP to [założenie] (dom-ev-market-roles).
2. **Sprawdź „ogólnodostępność”** (art. 2 pkt 6): dostępna na zasadach równoprawnego traktowania dla każdego posiadacza EV
   i hybrydy. Stacja tylko dla klientów lub floty może nią nie być — **[do weryfikacji]**; AFIR ma szerszą definicję.
3. **Wskaż artykuł i ustęp.** Brak w tekście = nie wymyślaj; odeślij do rozporządzenia albo oznacz **[do weryfikacji]**.
4. **Ułóż kolejność przed startem:** numer EIPA, zgłoszenie danych i wniosek o badanie UDT, badanie, eksploatacja.
5. **Przełóż na CPMS** (tabela niżej) i wskaż, kto dowodzi: operator, dostawca, UDT, URE. Definicje i cytaty: `references/ustawa-artykuly.md`.

## Obowiązki — kto i co
| Podmiot | Obowiązek (artykuł) | Skutek dla CPMS i aplikacji |
|---|---|---|
| Operator | na stacji działa co najmniej jeden dostawca (art. 3 ust. 1 pkt 1 lit. a); stacja spełnia wymagania techniczne, badania UDT (pkt 1 lit. b, pkt 2) | model: stacja ↔ dostawcy (1:N) |
| Operator | oprogramowanie: ładowanie oraz **przekazywanie do rejestru dostępności punktu i ceny** (pkt 4 lit. a) | integracja z EIPA to wymóg stacji |
| Operator | **system pomiarowy w każdym punkcie**, dane do systemu stacji w czasie zbliżonym do rzeczywistego (pkt 4 lit. b) | kWh per punkt w CPMS; metrologia: dom-ev-charger-hardware |
| Operator | dane do rozliczenia dla dostawcy (pkt 6); informacje o zasadach i instrukcja na stacji (pkt 9) | eksport sesji; treść na stacji |
| Operator | **dostęp dostawców do stacji na zasadach rynkowych** (pkt 10; od 2023-01-01, art. 85a) | brak odmów bez uzasadnienia |
| Operator | energia tylko na ładowanie, wymianę akumulatora i funkcjonowanie stacji (art. 8) | brak odsprzedaży energii |
| Dostawca | usługa: ładowanie oraz rejestracja użytkownika, autoryzacja, ewidencja i informacja o sesji, naliczanie i pobieranie płatności, dokumenty sprzedaży, zgłoszenia i reklamacje (art. 3 ust. 2 pkt 2) | lista funkcji CPMS/aplikacji dostawcy |
| Dostawca | **cena i warunki usługi na swojej stronie internetowej** (art. 3 ust. 2 pkt 3) | publikacja poza aplikacją |
| Dostawca | **nie uzależnia usługi od uprzedniej umowy pisemnej, papierowej lub elektronicznej** (art. 7) | zakaz wymuszania konta przed ładowaniem |

## EIPA — dane, kto i kiedy (art. 41b, 42)
| Krok | Wymóg wg tekstu | Artykuł |
|---|---|---|
| Numer EIPA | wniosek do Prezesa UDT **przed rozpoczęciem działalności**, przez rejestr; składa operator **i** dostawca; można wnosić o uznanie kodu z innego państwa UE | 41b ust. 1-2 |
| Opłata | miesięczna: operator max 25 zł × liczba stacji; dostawca max 50 zł; stawki w rozporządzeniu | 41b ust. 3, 5 |
| Wniosek o badanie | zawiera numer EIPA lub uznany kod | 41b ust. 4 |
| Zgłoszenie danych | firma, adres, dane teleadresowe, rodzaj infrastruktury, **współrzędne stacji** — najpóźniej w dniu wniosku o badanie przed oddaniem do eksploatacji i przy każdej zmianie; wycofanie — najpóźniej w dniu końca usługi | 42 ust. 5 |
| Kto zgłasza | tylko podmiot z numerem EIPA lub uznanym kodem | 42 ust. 5a |
| Dostępność punktu | usługą sieciową **natychmiast** po zmianie stanu (w czasie wynikającym z usługi) | 42 ust. 6 pkt 1 |
| Cena usługi | usługą sieciową **w ciągu godziny** od zmiany ceny | 42 ust. 6 pkt 2 |
| Mapa i dane | mapa pokazuje tylko stacje po badaniu UDT i oznacza wstrzymane; dane udostępnia się każdemu zainteresowanemu | 42 ust. 4a, 8, 10 |

Rejestr zawiera też metody płatności (art. 42 ust. 3 pkt 3). Specyfikacja usługi sieciowej jest w BIP UDT —
**[do weryfikacji]**: pola, format i układ współrzędnych (ustawa: państwowy system odniesień przestrzennych, współrzędne
płaskie prostokątne; OCPI: szerokość i długość geograficzna). Strona `pl-eipa`: stacja z błędnym lub brakującym numerem EIPA
we wniosku o badanie nie trafi na mapę mimo wyniku pozytywnego; numer poprawia się w panelu lub przez API.

## UDT, URE i OSD
- **Badanie UDT** (art. 16): obowiązkowe **przed oddaniem do eksploatacji** i po każdej naprawie lub modernizacji, także
  przy dodaniu lub przeniesieniu punktu; wyjątek: wymiana części na takie same parametrami. Wniosek składa operator.
  UDT może wstrzymać eksploatację (art. 16 ust. 4, art. 29f); powrót wymaga badania jak przed oddaniem. Opinia o
  dokumentacji przed budową jest dobrowolna (art. 15, 30 dni). Czy aktualizacja firmware to „modernizacja”, ustawa nie mówi — **[do weryfikacji]** u UDT.
- **OSD** nie może być operatorem, właścicielem ani dostawcą usługi (art. 3a); wyjątki przez przetarg lub decyzję Prezesa URE
  (art. 3a-3c). Umowy dystrybucji i sprzedaży energii: art. 3 ust. 1 pkt 5, 7. **Warunki przyłączenia i taryfy OSD są w
  Prawie energetycznym** — nie w tej ustawie i nie w bazie: **[do weryfikacji]**.
- **Prezes URE** wymierza kary za brak dostępu dostawców, wymóg umowy i użycie energii (art. 46 ust. 1 pkt 1).

## Kary (art. 45-47) — tylko przypadki istotne dla software
| Naruszenie | Kara | Organ |
|---|---|---|
| brak dostępu dostawców (art. 3 ust. 1 pkt 10) | 5 000-150 000 zł | Prezes URE |
| wymóg umowy (art. 7) | 1 000-50 000 zł | Prezes URE |
| energia niezgodnie z art. 8 | 5 000-50 000 zł | Prezes URE |
| brak badania UDT (art. 16 ust. 1) lub eksploatacja mimo decyzji z art. 16 ust. 4 | 20 000 zł za stację | Prezes UDT |
| eksploatacja mimo decyzji z art. 29f ust. 7 | 100 000 zł | Prezes UDT |
| brak oznakowania i informacji (art. 41 ust. 1-4) | 500-2 000 zł | Inspekcja Handlowa |
| brak zgłoszenia do rejestru (art. 42 ust. 5) | 2 000 zł | Prezes UDT |

Limit: 15 % przychodu z poprzedniego roku podatkowego (art. 45 ust. 3). **W tekście nie ma kar za niedostępność punktu,
nieaktualną cenę w rejestrze ani za naruszenie AFIR.** Sankcje spoza ustawy: **[do weryfikacji]**.

## Terminy i przepisy przejściowe
Art. 42 i 69 (EIPA) działają od 2019-01-01 (art. 86 pkt 7); art. 3 ust. 1 pkt 10 od 2023-01-01 (art. 85a). Przepisy art. 74 i 79
(dostosowanie stacji sprzed rozporządzeń, pierwsze zgłoszenia do 2019-01-15) oraz art. 60 (cele dla gmin do 2021-03-31) są historyczne;
dla nowej stacji liczą się art. 16, 41b, 42. Tabela i daty: `references/ustawa-artykuly.md`.

## Relacja do AFIR (rozporządzenie UE 2023/1804)
AFIR wiąże **wprost** od 2024-04-13 (art. 26); ustawa go nie powtarza. Tabela z liniami: `references/afir-relacja.md`; treść AFIR: dom-ev-regulations-eu.
| Temat | Ustawa | AFIR |
|---|---|---|
| Płatność ad hoc | brak przepisu; art. 7 zakazuje wymogu umowy | art. 5 ust. 1: czytnik kart lub bezstykowe; QR poniżej 50 kW |
| Cena | art. 3 ust. 2 pkt 3, art. 42 ust. 6 | art. 5 ust. 3-4: nie dyskryminująca; od 50 kW za kWh |
| Dane i API | rejestr EIPA: dostępność, cena | art. 20: dane statyczne i dynamiczne, API, punkty dostępu |
| Identyfikatory | numer EIPA nadaje UDT | art. 20 ust. 1 (IDRO); czy UDT jest IDRO — **[do weryfikacji]** |
| Dostęp dostawców, badanie UDT | art. 3 ust. 1 pkt 10, art. 16 | brak odpowiednika |

## Co to znaczy dla CPMS, aplikacji i raportowania
| Obszar | Reguła | Podstawa |
|---|---|---|
| Model danych | numer EIPA operatora i dostawcy, współrzędne, data i wynik badania UDT | art. 41b, 42 |
| Integracja EIPA | zmiana statusu punktu wysyłana bez opóźnienia; zmiana ceny najpóźniej w godzinę, alarm przy przekroczeniu, kolejka ponowień | art. 42 ust. 6 |
| Cena | ta sama kwota w aplikacji, u dostawcy i w EIPA; wielu dostawców na stacji — którą cenę zgłosić, ustawa nie mówi **[do weryfikacji]** | art. 3, 42 |
| Ad hoc | ładowanie bez konta i akceptacji umowy jako warunku; płatność wg AFIR (dom-ev-payments) | art. 7 |
| Uruchomienie | punkt produkcyjny dopiero po badaniu UDT; zadanie „badanie” przy dodaniu lub przeniesieniu punktu | art. 16 |
| Dostęp dostawców | umowa lub API dla kolejnych dostawców, log odmów z uzasadnieniem | art. 3 ust. 1 pkt 10 |
| Raportowanie | ustawa nie wymaga okresowego raportu uptime; dane publiczne są w rejestrze; okres retencji sesji **[do weryfikacji]** | art. 42 |

## Przykład
Stacja z czterema punktami DC, start 1 grudnia, jedna spółka jest operatorem i dostawcą (art. 6). 1) Składa wnioski o numer EIPA
(art. 41b ust. 2). 2) Z numerem składa wniosek o badanie UDT (art. 41b ust. 4) i tego dnia zgłasza dane oraz współrzędne (art. 42 ust. 5).
3) Po badaniu stacja trafia na mapę. 4) Po starcie: stan punktu do rejestru natychmiast, cena najpóźniej w godzinę (art. 42 ust. 6).
Brak badania przed oddaniem: 20 000 zł za stację (art. 45 ust. 2 pkt 4 lit. a).

## Pułapki
- Operator i dostawca z ustawy to nie dokładnie CPO i eMSP; eMSP w roamingu może nie być dostawcą — **[do weryfikacji]**.
- Wymuszenie konta w aplikacji może naruszać art. 7; czy rejestracja to „umowa”, rozstrzyga prawnik.
- Numer EIPA trzeba mieć **przed** wnioskiem o badanie; błąd w numerze = brak stacji na mapie.
- Brak kar za AFIR w ustawie nie znosi obowiązku: AFIR wiąże bezpośrednio; egzekucję sprawdź **[do weryfikacji]**.
- Stan na 26.08.2026: rozporządzenia mogły się zmienić; szczegóły techniczne bierz z aktualnych rozporządzeń.

## Checklista
- [ ] Rola wg ustawy i „ogólnodostępność” ustalone; każde twierdzenie ma artykuł.
- [ ] Szczegóły z rozporządzeń oznaczone **[do weryfikacji]**; podany stan prawny 26.08.2026 i zastrzeżenie „to nie porada prawna”.
- [ ] Kolejność: numer EIPA, dane i wniosek UDT, badanie, eksploatacja; dostępność natychmiast, cena do godziny.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/ustawa-artykuly.md` | trzeba definicji, cytatu z numerem linii w `doc.txt`, przepisów przejściowych albo pełnej tabeli kar |
| `references/afir-relacja.md` | pytanie o granicę ustawa ↔ AFIR, numery linii AFIR, lista rzeczy **[do weryfikacji]** |

## Źródła
- `pl-elektromobilnosc`: ustawa z 11.01.2018 r., tekst jednolity Dz.U. 2026 poz. 1243, stan na 26.08.2026 (isap.sejm.gov.pl, plik od człowieka, wczytany 2026-10-20).
- `pl-udt`, `pl-eipa`, `pl-ure`: strony główne (udt.gov.pl, eipa.udt.gov.pl, ure.gov.pl), pobrane 2026-10-20.
- `eu-afir`: rozporządzenie (UE) 2023/1804, wersja skonsolidowana EN z 08.01.2026 (eur-lex.europa.eu, pobrane 2026-10-20).
