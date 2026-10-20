# Uptime: wzór NEVI, raportowanie, statusy, AFIR i Polska

Spis: 1. Wzór i wyłączenia · 2. Raportowanie 680.112 · 3. Statusy źródłowe · 4. Decyzje definicji · 5. Raporty per
jednostka, kraj, model · 6. AFIR i Polska.

## 1. Wzór i wyłączenia (23 CFR 680.116(b))
- Wymóg: każdy port ma średnioroczny uptime **powyżej** 97 % (wynik równy 97,000 nie spełnia).
- „Up”: sprzęt i oprogramowanie online i dostępne albo w użyciu, **i** port skutecznie dostarcza energię zgodnie z mocą
  minimalną z 680.106(d). Wartość mocy minimalnej i terminy: dom-ev-regulations-us.
- Liczenie: co miesiąc, za poprzednie 12 miesięcy, dla każdego portu osobno.
- `µ = ((525,600−(T_outage−T_excluded))/525,600) × 100`; `T_outage` — minuty przestoju w poprzednim roku;
  `T_excluded` — minuty przestoju z przyczyn poza kontrolą operatora, **o ile operator wykaże**, że port byłby sprawny:
  przerwy w dostawie od zakładu energetycznego, brak ładowania z winy pojazdu (nie spełnił oczekiwań klienta co do
  dostawy mocy), planowana konserwacja, wandalizm, klęski żywiołowe. Wyłączone są też godziny poza godzinami pracy stacji.
- 525 600 to minuty roku 365-dniowego. Rok przestępny ma 527 040 min; wzór w tekście ma stałą — porównując z raportem
  NEVI używaj stałej, a własne okno kalendarzowe oznacz (skrypt ostrzega `nevi-window`).

## 2. Raportowanie (680.112)
| Kiedy | Co (wybór związany z KPI) |
|---|---|
| kwartalnie | id stacji i portu (te same co w API 680.116(c)); start, koniec i kody błędów sesji nieudanej per port; kWh per sesja i port; szczytowa moc sesji; metoda płatności; uptime, `T_outage`, `T_excluded` za każdy z 3 poprzednich miesięcy; czas trwania (min) każdej awarii |
| rocznie do 1 marca (od 2024) | koszt utrzymania i napraw per stacja za poprzedni rok |
| jednorazowo (stacje AFC) | operator, zasoby DER, koszty nabycia i przyłączenia |
Dane publikowane przez FHWA są zagregowane i zanonimizowane. 680.114(a)(4): sieć i ładowarki mają bezpiecznie mierzyć,
przekazywać, przechowywać i raportować energię i moc, status portu w czasie rzeczywistym, cenę oraz **historyczny
uptime portu** — stąd wymóg trzymania zdarzeń, nie samego stanu. Raport wymaga więc: czasu trwania każdej awarii
(epizody, nie suma), kodów błędów sesji nieudanych i rozbicia przestoju na wyłączony/niewyłączony.

## 3. Statusy źródłowe
| Źródło | Statusy | Uwaga dla KPI |
|---|---|---|
| OCPP 1.6 `StatusNotification` | `Available`, `Preparing`, `Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing`, `Reserved`, `Unavailable`, `Faulted` | `errorCode` osobno; `Unavailable` bywa decyzją operatora (`ChangeAvailability`) |
| OCPP 2.0.1 | `Available`, `Occupied`, `Reserved`, `Unavailable`, `Faulted` | stan ładowania wynika z transakcji; mapowanie: dom-ev-ocpp-2x |
| OCPI Locations (EVSE `status`) | `AVAILABLE`, `BLOCKED`, `CHARGING`, `INOPERATIVE`, `OUTOFORDER`, `PLANNED`, `REMOVED`, `RESERVED`, `UNKNOWN` | `UNKNOWN` także przy offline; `PLANNED`/`REMOVED` to cykl życia, nie przestój |
| CSMS (pochodne) | `Offline` (brak połączenia), `PAUSED` (decyzja operatora) | nazwy własne systemu; nie ma ich w OCPP |
API NEVI (680.116(c)(8)(vii)) wymaga statusu portu w czasie rzeczywistym w terminach OCPI 2.2.1. Status stacji
(680.116(c)(6)): *operational*, *under construction*, *planned*, *decommissioned*. Port `PLANNED`/`REMOVED`/stacja
przed uruchomieniem lub po wycofaniu leży **poza** mianownikiem uptime, a nie w przestoju.

## 4. Decyzje definicji (zapisz w dokumencie definicji KPI)
| Sytuacja | Opcja A | Opcja B | Uwaga |
|---|---|---|---|
| `Faulted` | przestój | — | zawsze; przyczyna z listy (np. wandalizm) wyłącza, jeśli jest dowód |
| `Unavailable` ustawiony przez operatora | przestój | wyłączenie (planowany serwis) | wyłączenie tylko z dowodem i zgodnie z listą |
| `PAUSED` | przestój | wyłączenie | brak pozycji „decyzja operatora” na liście wyłączeń w tekście 680.116(b) |
| offline CSMS | przestój | wyłączenie (przerwa w dostawie, dowód) | nieznany stan nie jest dowodem sprawności |
| `Available` + kolejne nieudane starty | up (status) | down (nie dostarcza energii) | tekst „up” wymaga dostarczania energii |
| brak statusu na początku okna | przestój | poza oknem | `--unknown outage` albo `exclude` |
| `Reserved`, `Preparing`, `Finishing` | up | — | port zajęty przez użytkownika nie jest awarią |
| `BLOCKED` (OCPI) | up | przestój | zajęty przez auto; decyzja zależy od odbiorcy, zapisz |
Dla `PAUSED` i podobnych interpretację prawną pozostaw prawnikowi lub FHWA **[do weryfikacji]**; w kodzie jest tylko
mapowanie `--down-status` / `--up-status` i okna `exclusions`.

## 5. Raporty per jednostka biznesowa, kraj, model
- Atrybuty (jednostka biznesowa, kraj, model, firmware, godziny pracy) trzymaj w wymiarze portu **z historią ważności**
  (od–do); port zmienia jednostkę biznesową, model po wymianie, godziny pracy po zmianie umowy.
- Uptime grupy = suma minut przestoju i okna wszystkich portów grupy (ważenie minutami), nie średnia uptime portów.
  Dodatkowo podaj **liczbę portów poniżej progu** — średnia ukrywa pojedyncze porty, a próg NEVI jest per port.
- Model i firmware pozwalają wyłapać wzorzec awarii (dom-ev-diagnostics) i podać do kart onboardingu producenta.
- Kraj: strefa i godziny pracy pochodzą ze stacji, nie z raportu; waluta przychodu osobno (`kpi-sesji-i-finanse.md`).

## 6. AFIR i Polska
- AFIR Art. 20 ust. 2: do 2025-04-14 operatorzy punktów ogólnodostępnych zapewniają dane statyczne i **dynamiczne**
  bezpłatnie; dane dynamiczne (f): *operational status*, *availability*, *ad hoc price*. Ust. 3: API bez opłat i bez
  ograniczeń, zgłoszone do krajowych punktów dostępu (NAP). Definicja „availability of data” w AFIR (art. 2 pkt 9)
  dotyczy istnienia danych w formacie maszynowym, a nie dostępności ładowarki. Progu uptime w tekście z bazy nie znalazłem.
- Polska (ustawa o elektromobilności, art. 42): rejestr UDT zawiera m.in. dostępność punktów ładowania; operator
  przekazuje ją usługą sieciową **natychmiast po zmianie stanu**, ceny w ciągu godziny. Progu uptime w tekście nie ma.
- Wniosek dla KPI: dane dynamiczne wymagają **latencji** statusu (mierz opóźnienie od zdarzenia do publikacji), a uptime
  NEVI — **historii**. To dwa produkty z jednego strumienia zdarzeń. Szczegóły: dom-ev-regulations-eu, dom-ev-regulations-pl.
