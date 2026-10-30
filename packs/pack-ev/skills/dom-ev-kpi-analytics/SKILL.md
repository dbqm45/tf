---
name: dom-ev-kpi-analytics
description: Użyj przy KPI sieci ładowania — uptime NEVI vs surowy vs SLA, session success rate, utilization, MTTR, MTBF, przychód na EVSE, pułapki liczenia i model danych.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy analityk lub backend liczy wskaźniki sieci ładowania — uptime i availability (wzór NEVI 23 CFR 680.116(b), wyłączenia, trzy definicje, port up tylko przy dostarczaniu energii, offline, czas nieznany, PAUSED), session success rate, utilization, kWh, sesje na EVSE, średnia długość sesji, przychód i marża na kWh, MTTR, MTBF, NPS, a także pułapki (złącza zamiast EVSE, DST, zdarzenia z opóźnieniem, duplikaty, zmiana EVSE ID, porty nowe, średnia średnich) i model danych (zdarzenia statusu, sesje, CDR, idempotencja). Nie do samych wymogów NEVI (dom-ev-regulations-us), rejestru assetów i serwisu (dom-ev-asset-operations), uzgadniania CDR z fakturą (dom-ev-cdr-settlement) ani ekonomii stacji i zwrotu inwestycji."
  slowa: "uptime, availability, dostępność ładowarek, dostępność portów, uptime 97, NEVI uptime, SLA serwisowe, wyłączenia z uptime, port up, offline jako przestój, status PAUSED, raport statusów, uptime per kraj, historia uptime, session success rate, skuteczność sesji, nieudane sesje, utilization, wykorzystanie ładowarek, obłożenie, sesje na EVSE dziennie, średnia długość sesji, przychód na EVSE, marża na kWh, MTTR, MTBF, NPS, ocena kierowców, KPI sieci ładowania, charging network KPI, dashboard KPI, średnia ze średnich, DST, strefa czasowa raport, duplikaty zdarzeń, zmiana EVSE ID"
---

# KPI sieci ładowania — definicje i pułapki liczenia

Wskaźnik bez zapisanej definicji nie jest liczbą, tylko opinią. Skill podaje definicje, wybory do podjęcia **przed**
kodem oraz pułapki. Sieć: brak. Wymogi NEVI (moc minimalna, terminy, API) → **dom-ev-regulations-us**; rejestr
assetów, serwis i SLA wykonawców → **dom-ev-asset-operations**; uzgadnianie CDR z sesją i fakturą →
**dom-ev-cdr-settlement**; przebieg sesji i statusy → **dom-ev-session-lifecycle**, **dom-ev-ocpp-16**, **dom-ev-ocpp-2x**.

## Procedura
1. **Nazwij odbiorcę liczby:** regulator (NEVI, rejestr krajowy), umowa serwisowa (SLA), zarząd, kierowca. Każdy chce
   innej definicji tego samego słowa „uptime”.
2. **Zapisz definicję** (jednostka liczenia, przyczyny wyłączeń, status nieznany, offline, PAUSED, okno, strefa) i nadaj
   jej wersję. Dopiero potem pisz zapytanie.
3. **Licz z tych samych danych co raport regulacyjny** (model: `references/model-danych-i-pulapki.md`).
4. **Uruchom skrypt** na próbce i porównaj z ręcznym rachunkiem dla jednego portu.
5. **Przy raporcie podaj:** definicję, okno, liczbę portów w mianowniku, odcięcie danych (kiedy ostatnio zebrano zdarzenia)
   i listę ostrzeżeń.

## Uptime — trzy definicje obok siebie
Jednostką jest **port**, czyli punkt ładowania (EVSE), nie złącze i nie stacja. Minuty okna `W`, minuty przestoju
`T_out`, minuty przestoju z przyczyn wyłączonych `T_ex`.

| Definicja | Wzór | Komu służy |
|---|---|---|
| surowa | (W − T_out) / W | kierowca widzi port niedostępny, niezależnie od winy |
| NEVI | (W − (T_out − T_ex)) / W | 23 CFR 680.116(b): rok = 525 600 min, każdy port osobno, wynik **powyżej** 97 % |
| SLA | (W − T_out) / (W − T_ex) | umowy serwisowe: wyłączenia znikają też z mianownika (zwykle wynik wyższy od NEVI) |

Wzór NEVI w oryginale: `µ = ((525,600−(T_outage−T_excluded))/525,600) × 100`. Wyłącza się **przestój** z przyczyny,
nie czas: przerwa w dostawie od zakładu energetycznego, wina pojazdu, planowany serwis, wandalizm, klęska żywiołowa;
osobno godziny poza godzinami pracy stacji. Operator musi **wykazać**, że port byłby sprawny — to dowód (zgłoszenie
OSD, log serwisowy, zdjęcie), nie flaga w bazie. 3 % z 525 600 to 15 768 min (ok. 10,95 doby) przestoju
niewyłączonego na port w roku.

### Co znaczy „port up”
Tekst NEVI: sprzęt i oprogramowanie online i dostępne albo w użyciu **i** port faktycznie dostarcza energię z mocą
minimalną (680.106(d)). Konsekwencje dla kodu:
- `Available` mówi, że port może wystartować, nie że dostarczy energię. Port w `Available` z błędem przy każdej sesji
  nie jest „up”. Dowód: sesje bez energii i nieudane starty (zob. skuteczność sesji) — decyzję, kiedy port uznajesz za
  „down” mimo `Available`, zapisz w definicji (np. N kolejnych sesji bez energii).
- **Offline z CSMS** (brak połączenia, brak `Heartbeat`) liczysz jako przestój, bo stan portu jest nieznany, a operator
  nie dowiedzie, że działał. Wyjątek tylko z udokumentowaną przyczyną z listy wyłączeń (np. przerwa w dostawie).
- **Czas nieznany** (brak statusu przed początkiem okna, port nowy): zasada jawna w raporcie — przestój (ostrożnie) albo
  poza oknem; skrypt ma `--unknown outage|exclude`.
- **PAUSED** (wyłączenie portu decyzją operatora w CSMS, zob. dom-ev-asset-operations; to status operatora, nie OCPP): to decyzja definicji.
  Przestój, bo kierowca nie naładuje — domyślnie tak. Wyłączenie tylko wtedy, gdy mieści się w liście (planowany
  serwis, poza godzinami pracy) i masz dowód. Nie rozstrzygaj tego w kodzie przez „bo tak wyszło”.
- Raportowanie 680.112(a): co kwartał uptime, `T_outage` i `T_excluded` za każdy z 3 ostatnich miesięcy, czas trwania
  każdej awarii, sesje z kodami błędów, kWh, szczytowa moc, metoda płatności. Identyfikatory stacji i portu takie
  same jak w API 680.116(c). Wzór liczysz co miesiąc dla poprzednich 12. Szczegóły: `references/uptime-i-regulacje.md`.

AFIR (Art. 20) wymaga danych dynamicznych: *operational status*, *availability*, *ad hoc price*, bezpłatnie przez API
zgłoszone do NAP. W tekście AFIR w bazie nie ma progu uptime. Polska: operator przekazuje dostępność punktu do rejestru
UDT natychmiast po zmianie stanu (art. 42 ustawy o elektromobilności); progu uptime także nie znalazłem. Status
w czasie rzeczywistym nie jest tym samym co uptime z historii: **trzymaj zdarzenia statusu, nie tylko bieżący stan**.

## Skrypt `scripts/uptime_kpi.py`
Uruchom, nie czytaj. Biblioteka standardowa, bez sieci. Liczy z zdarzeń statusu uptime w trzech definicjach, przestoje,
MTTR, MTBF i skuteczność sesji dla każdego portu.

`python3 .claude/skills/dom-ev-kpi-analytics/scripts/uptime_kpi.py <plik>.json [--threshold 97] [--unknown outage|exclude] [--up-status S ...] [--down-status S ...] [--json]`

- **Wejście JSON:** `window {start, end}` (ISO), `events [{ts, port, status, reason?}]`, `exclusions [{port?, start,
  end, reason}]?`, `sessions [{port, outcome: ok|failed}]?`. Status obowiązuje do następnego zdarzenia portu; stan na
  starcie okna bierze z ostatniego zdarzenia przed oknem. Statusy `Available`, `Occupied`, `Charging`, `Preparing`,
  `SuspendedEV`, `SuspendedEVSE`, `Finishing`, `Reserved` to „up”; `Faulted`, `Unavailable`, `Offline` to przestój.
  Inny status (np. `PAUSED`) kończy się błędem, dopóki go nie zmapujesz opcją `--up-status` albo `--down-status`.
- **Przyczyny wyłączeń** (pole `reason` zdarzenia albo okno w `exclusions`): `utility`, `vehicle`, `maintenance`,
  `vandalism`, `disaster`, `outside_hours`. Inna przyczyna daje ostrzeżenie i nie wyłącza przestoju.
- **Kody wyjścia:** 0 — każdy port ≥ próg (wg NEVI); 1 — co najmniej jeden port poniżej; 2 — błąd wejścia
  (zła data, nieznany status, brak okna).
- **Czego nie robi:** nie sprawdza, czy port dostarczał energię (`Available` = up); nie ocenia dowodu wyłączenia;
  nie deduplikuje zdarzeń, nie przelicza stref ani DST (daty ISO ze strefą, bez strefy = UTC); nie liczy kroczących
  12 miesięcy ani raportu kwartalnego; nie wyprowadza sukcesu sesji z energii (bierze `ok`/`failed` z wejścia);
  nie wie nic o złączach, kraju ani modelu (pogrupuj wyniki sam). Okno ≈ 365 dni inne niż 525 600 min dostaje ostrzeżenie `nevi-window`.

## Pozostałe KPI (wzory i decyzje: `references/kpi-sesji-i-finanse.md`)
| KPI | Skrót definicji | Decyzja do zapisania |
|---|---|---|
| session success rate | sesje, które dostarczyły energię / sesje uruchomione | próg energii, co z `STOP_FAILED`, 0 kWh |
| skuteczność autoryzacji | zaakceptowane / zażądane | **osobno** od sukcesu sesji |
| utilization | czas zajętości (albo ładowania) / czas dostępności portów | mianownik: godziny pracy, wyłączenia |
| kWh, sesje na EVSE/dzień | suma energii; sesje / (EVSE × dni pracy) | licznik legalny czy sesyjny, dni od uruchomienia |
| średnia długość sesji | wpięcie–wypięcie i ładowanie osobno; mediana obok średniej | start i koniec wg zdarzeń transakcji |
| przychód na EVSE/site | z CDR, netto bez VAT | data sesji czy wystawienia, własne i roamingowe |
| marża na kWh | (przychód − koszt energii − opłaty zmienne) / kWh | bez CAPEX; ekonomia stacji to osobny temat |
| MTTR, MTBF | średni czas przywrócenia; czas „up” / liczba przestojów | od zgłoszenia czy od zdarzenia; mediana |
| NPS, ocena | % promotorów (9–10) − % krytyków (0–6) | próba, odpowiedzi po sesji tylko udanej |

Progi rentowności z przeglądów branżowych (np. „15–20 % utilization dla DC”) to **[do weryfikacji]**: zależą od mocy,
ceny, kosztu energii i miejsca; nie stawiaj ich jako celu bez modelu stacji.

## Przykład
Okno: wrzesień 2026 (43 200 min), 3 porty, dane w pliku `<dane>.json`. Port `E1*1`: awaria 12 h bez przyczyny
i 6 h offline z przerwą w dostawie energii. Port `E1*2`: 4 h serwisu planowego (`maintenance`) i 48 h awarii. Port
`E2*1`: pierwsze zdarzenie 2 września (doba nieznana). Wynik faktycznego uruchomienia:

```
Okno 2026-09-01T00:00:00Z → 2026-10-01T00:00:00Z, próg 97.0 % (NEVI)
  port             surowy     NEVI      SLA   przestój     wył.     MTTR   sesje
  PL*ABC*E1*1      97.500   98.333   98.319     1080.0    360.0    540.0   75.0%
  PL*ABC*E1*2      92.778   93.333   93.296     3120.0    240.0   1560.0   50.0% ✗
  PL*ABC*E2*1      96.667   96.667   96.667     1440.0      0.0        —       — ✗
  średnia NEVI: 96.111 %; poniżej progu: PL*ABC*E1*2, PL*ABC*E2*1
  ⚠ [unknown-start] port PL*ABC*E2*1: brak statusu przed początkiem okna — czas do pierwszego zdarzenia nieznany
```
Kod wyjścia 1. `E1*1`: surowo 97,5 %, wg NEVI 98,333 % (360 min wyłączone). Z `--unknown exclude` `E2*1` ma 100 %,
bo doba nieznana wypada z okna — ta sama dana, inna liczba; dlatego reguła idzie do raportu. Średnia NEVI z portów
(96,111 %) to tylko podsumowanie: próg dotyczy **każdego** portu, nie średniej. To jeden miesiąc, nie 12.

## Pułapki
- **Złącza zamiast EVSE.** Port z dwoma złączami (jedno ładuje naraz) policzony po złączach zawyża mianownik i zaniża
  utilization; uptime złącza ≠ uptime portu. Klucz to EVSE (dom-ev-glossary).
- **Strefy i DST.** Przechowuj UTC, granice dnia i miesiąca w strefie stacji. W Polsce doba 2026-10-25 ma 25 h,
  2026-03-29 ma 23 h; NEVI liczy minuty, dzienne raporty muszą to znać.
- **Zdarzenia z opóźnieniem.** Stacja po powrocie online wysyła zaległe `StatusNotification`. Sortuj po czasie zdarzenia,
  nie odbioru; zamknięty okres po zaległych danych przelicz i zapisz wersję raportu.
- **Duplikaty** (retransmisja, dwa źródła statusu) liczą przestój podwójnie. Klucz idempotencji w modelu danych.
- **Zmiana EVSE ID w trakcie okresu** rwie historię. Trzymaj stały wewnętrzny identyfikator portu i tabelę aliasów
  (dom-ev-identifiers); w raporcie regulacyjnym obowiązuje identyfikator zgłoszony w API.
- **Port nowy** (< 12 miesięcy): stałe 525 600 w mianowniku daje wynik sztucznie wysoki; czas przed uruchomieniem
  nie jest „up” ani „down”. Jak to ma być liczone w raporcie, ustal z odbiorcą **[do weryfikacji]**.
- **Średnia ze średnich:** uśrednienie utilization lokalizacji o różnej liczbie portów kłamie. Licz sumę liczników przez
  sumę mianowników (ważone), nigdy średnią procentów. Dotyczy też uptime po kraju i modelu.
- **Jedna liczba „availability”** dla regulatora, SLA i kierowcy. Zawsze nazwij wariant.

## Checklista
- [ ] Definicja zapisana i wersjonowana: jednostka (port), wyłączenia, offline, nieznany, PAUSED, okno, strefa.
- [ ] Dowody wyłączeń przechowywane; zdarzenia statusu historyczne, z kluczem idempotencji.
- [ ] Uptime, session success i kWh liczone z tych samych tabel co raport regulacyjny.
- [ ] Agregaty ważone sumami; podział po jednostce biznesowej, kraju i modelu bez przeliczania średnich.
- [ ] Skrypt uruchomiony i porównany z ręcznym rachunkiem; kod wyjścia i ostrzeżenia w raporcie.
- [ ] Progi z przeglądów oznaczone [do weryfikacji].

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| wzór NEVI, raportowanie 680.112, statusy OCPP i OCPI, AFIR i PL, PAUSED, raport per jednostka, kraj, model | `references/uptime-i-regulacje.md` |
| session success rate, utilization, kWh, sesje, długość, przychód, marża, MTTR, MTBF, NPS | `references/kpi-sesji-i-finanse.md` |
| tabele zdarzeń statusu, sesji i CDR, idempotencja, opóźnienia, DST, zmiana EVSE ID, porty nowe | `references/model-danych-i-pulapki.md` |

## Źródła
- 23 CFR 680.112, 680.114, 680.116 — eCFR, baza `us-nevi` (`.claude/knowledge/us-nevi/doc.txt`, L180–312),
  ecfr.gov/api/renderer/v1/content/enhanced/current/title-23?part=680, pobrane 2026-10-20.
- AFIR (UE) 2023/1804, Art. 20 ust. 2–3 — baza `eu-afir` (`doc.txt`, L1924–2060), eur-lex.europa.eu/eli/reg/2023/1804/oj,
  pobrane 2026-10-20.
- Ustawa o elektromobilności, art. 42 (rejestr dostępności) — baza `pl-elektromobilnosc` (`doc.txt`, L1170–1232),
  pobrane 2026-10-20.
- OCPI 2.2.1 d2 i 2.3.0, Locations, `Status` — bazy `ocpi-2.2.1-d2`, `ocpi-2.3.0`, pobrane 2026-10-20.
- `docs/backlog-wiedza-ogolna-ev.md`, sekcja 11; `docs/procesy-cpo.md` (monitoring dostępności).
