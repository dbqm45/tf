# MID i zmiana 2026/706: MI-011 dla liczników EVSE

Spis treści: 1. Co dodaje 2026/706 · 2. Terminy · 3. Parametry MI-011 · 4. Wymogi zał. I dla EVSE · 5. Czego nie ma w bazie.

Źródła: `eu-mid-2026-706` (dyrektywa (UE) 2026/706, OJ L 20.3.2026, EUR-Lex, pobrane 2026-10-20),
`eu-mid` (MID 2014/32/UE, art. 1–4 i zał. I, wklejone 2026-10-20). Zakresy linii w `.claude/knowledge/<id>/doc.txt`.
Streszczenie własnymi słowami; to nie jest porada prawna. Mapa pozostałych aktów UE: dom-ev-regulations-eu.

## 1. Co dodaje 2026/706
- Nowy załącznik szczegółowy **Va, MI-011: systemy pomiarowe EVSE** (L556+): wszystkie funkcje metrologiczne przy
  przekazaniu energii czynnej (w obu kierunkach) w określonym punkcie przekazania między EVSE a pojazdem. Nie są
  przyrządami „utility” z zał. I.
- Funkcje metrologiczne może pełnić licznik energii czynnej już ocenionym wg zał. V (MI-003); jego wynik uwzględnia się
  w ocenie systemu (L569-572). Treść zał. V (MI-003) w brzmieniu bazowym jest poza bazą **[do weryfikacji]**; zmiana
  2026/706 (L441-552) dodaje m.in. liczniki prądu stałego (zakresy napięć, brak rejestracji bez prądu, rozruch).
- Zmiany zał. I: wskazanie wyniku, patrz sekcja 4.

## 2. Terminy (art. 2–4, L182-232)
| Co | Data |
|---|---|
| Państwa członkowskie przyjmują i publikują przepisy | do 10.04.2028 |
| Stosowanie przepisów krajowych | od **10.10.2028** |
| Przyrządy zgodne z MID z 08.04.2026, wprowadzone do obrotu przed 10.10.2028 | dalej można udostępniać i używać |
| Przyrządy z zał. Va i VIIa zgodne z prawem krajowym, wprowadzone przed 10.04.2030 | dalej można udostępniać i używać |
| Certyfikaty wydane przed 10.10.2028 | ważne do końca ważności, najdalej do 10.04.2038 |
| Jednostki notyfikowane | mogą być notyfikowane i wydawać certyfikaty przed 10.10.2028 (art. 4) |

Jak to przełożyć na produkt: ładowarka DC wprowadzana do obrotu po 10.10.2028 potrzebuje oceny MI-011; starsze
egzemplarze działają dalej na zasadach przejściowych. Krajowa transpozycja (w tym polska) jest poza bazą **[do weryfikacji]**.

## 3. Parametry MI-011 (L650-925)
| Parametr | Wartość |
|---|---|
| Klasy dokładności | A (2 %), B (1 %), C (0,5 %) — deklaruje producent |
| Mierzona wielkość | przy prądzie stałym energia DC, przy zmiennym energia czynna AC, w punkcie przekazania |
| MMQ (minimalna mierzona ilość) | AC: ≤ 0,1 kWh; DC: ≤ 1 kWh |
| BMPE przy `Itr ≤ I < Imax` | A ±2 %, B ±1 %, C ±0,5 % |
| BMPE przy `Imin ≤ I < Itr` | A ±2,5 %, B ±1,5 %, C ±1 % |
| BMPE przy `Ist ≤ I < Imin` | A ±25 %, B ±15 %, C ±10 % |
| Zakresy AC | `0,9·Un ≤ U ≤ 1,1·Un`, `0,98·fn ≤ f ≤ 1,02·fn`, `PF ≥ 0,9` |
| Kabel z wtykiem | nierozłączny i plombowany albo wymienny: wskazany w ocenie jako wymienny, oznaczony, osobna plomba |
| Zakłócenia | dane legalne poprawne albo przesunięcie ≤ 1,0 BMPE; przerwanie transakcji: kończy się albo kontynuuje po ustaniu |
| Jednostka | kWh i wielokrotności dziesiętne |
| Ocena zgodności | B + F, B + D, G albo H1 (wybór producenta) |

Pomiar „nie wykorzystuje BMPE i nie faworyzuje systematycznie żadnej strony”.

## 4. Wymogi zał. I zmienione dla EVSE (L246-282)
- Pkt 10.2: wskazanie wyniku zabezpieczone przed przypadkowym skasowaniem lub zmianą.
- Pkt 10.6: wynik i dane z nim związane dostępne **bez narzędzi** przez (a) lokalny wyświetlacz, wydruk lub zapis
  pod kontrolą metrologiczną, (b) wyświetlacz zdalny albo (c) **urządzenie konsumenta**.
  Wynik musi być powiązany z przyrządem pod kontrolą metrologiczną, zabezpieczenia mają dawać dowód ingerencji,
  a wynik jest podstawą ceny do zapłaty.
- Definicja „transakcji zawartej”: dla EVSE strony akceptują wynik w chwili zakończenia pomiaru.
- Z tekstu bazowego (zał. I, `eu-mid`): oprogramowanie metrologiczne identyfikowalne i zabezpieczone (8.3), dane
  pomiarowe zabezpieczone przed zafałszowaniem (8.4), trwały zapis wyników z identyfikacją transakcji (11.1).

## 5. Czego nie ma w bazie **[do weryfikacji]**
Treść zał. V (MI-003), krajowe przepisy wykonawcze (PL, DE), wymogi Eichrecht (rozporządzenia, wytyczne PTB),
normy EN/OIML dla systemów pomiarowych EVSE, harmonogram wejścia MI-011 do wymogów AFIR.
