# Model danych do KPI i pułapki liczenia

Spis: 1. Zasada jednych danych · 2. Tabele · 3. Idempotencja · 4. Czas · 5. Opóźnienia i przeliczanie · 6. Tożsamość
portu · 7. Porty nowe · 8. Agregacja · 9. Przykład liczbowy.

## 1. Zasada jednych danych
KPI i raport regulacyjny (NEVI kwartalnie, rejestr krajowy, API) czytają **te same tabele** i tę samą definicję.
Dwa potoki dadzą dwie liczby uptime i spór o to, która jest prawdziwa. Dashboard to widok nad tabelami zdarzeń,
a nie osobna kopia stanu.

## 2. Tabele (szkic, nazwy własne)
| Tabela | Klucz i pola | Uwagi |
|---|---|---|
| `port` (wymiar z historią) | `port_id` (stały, wewnętrzny), `evse_id` od–do, jednostka biznesowa, kraj, model, firmware, godziny pracy, strefa, data uruchomienia i wycofania | wiersze o ważności od–do; aliasy `evse_id` |
| `status_event` | `event_id` / klucz naturalny (`port_id`, `status_ts`, `status`, `source`), `status_ts` (czas zdarzenia, UTC), `received_ts` (odbiór), `status`, `reason`, `error_code`, `source` (ocpp, csms, ocpi) | tylko dopisywanie; nie nadpisuj stanu |
| `outage_exclusion` | `port_id`, `start`, `end`, `reason`, dowód (adres dokumentu), kto zatwierdził | podstawa `T_excluded`; bez dowodu brak wyłączenia |
| `session` | `session_id`, `port_id`, `start_ts`, `end_ts`, `kwh`, `peak_kw`, `outcome`, `stop_reason`, `error_code`, `auth_result` | dom-ev-session-lifecycle; sesje osierocone oznacz |
| `cdr` | `cdr_id`, `session_id`, kwoty netto i brutto, waluta, `kwh`, korekta (`credit_of`) | niezmienny, korekta nowym wierszem; dom-ev-cdr-settlement |
| `kpi_snapshot` | `definition_version`, `period`, `data_cutoff_ts`, `port_id`, wartości | zamrożony wynik raportu, do audytu |
Przedziały statusów (`status_interval`: `port_id`, `from`, `to`, `status`) wyprowadzaj widokiem ze `status_event`
(okno `LEAD(status_ts)`), nie zapisuj ręcznie: to jedyne miejsce, gdzie trzeba obsłużyć dziury i offline.

## 3. Idempotencja
- Stacja po reconnect powtarza `StatusNotification`; CSMS bywa dwukrotnie zasilany z kolejki. Klucz naturalny
  (`port_id`, `status_ts`, `status`, `source`) z ograniczeniem unikalności i `INSERT … ON CONFLICT DO NOTHING`
  zamiast sprawdzania w kodzie.
- Zdarzenie z tym samym `status_ts` i innym statusem to konflikt danych: zapisz oba, oznacz, nie wybieraj po cichu.
- Przetwarzanie wsadowe (przeliczenie okresu) ma być powtarzalne: ten sam wsad, ta sama liczba. `DELETE` + wstaw
  okresu w jednej transakcji albo zapis wersji w `kpi_snapshot`.
- Zdarzenia `Heartbeat` nie są statusem; użyj ich do wykrycia offline po stronie CSMS, a offline zapisz jako zdarzenie
  `Offline` ze źródłem `csms`.

## 4. Czas
- Przechowuj UTC (ISO 8601 z `Z`). Granicę dnia, miesiąca i godzin pracy wylicz w strefie stacji (nazwa IANA),
  nie w przesunięciu stałym — przesunięcie nie zna DST.
- Doba z przejściem czasu ma 23 lub 25 godzin (Polska 2026: 2026-03-29 i 2026-10-25). Utilization dzienne liczone
  jako „godziny zajętości / 24” w takie dni jest błędne; mianownik to rzeczywista długość doby w strefie.
- Zegar stacji bywa przesunięty; porównuj `status_ts` z `received_ts` i oznacz zdarzenia o dużej różnicy. Który czas
  wiążesz (stacji czy CSMS), jest częścią definicji.
- NEVI liczy minuty; raport miesięczny w strefie lokalnej ma 28–31 dób — przy porównaniu z NEVI trzymaj osobno
  minuty absolutne i procenty.

## 5. Opóźnienia i przeliczanie
- Offline stacja buforuje zdarzenia i wysyła je po powrocie z oryginalnym czasem. Uptime policzony dzień po dniu
  zmienia się po odebraniu zaległości. Przeliczaj okno wsteczne (np. 7–30 dni, ustal) i zapisuj `data_cutoff_ts`.
- Do czasu odebrania zaległości stan „offline” to przestój, a po dobraniu danych część może okazać się wyłączona
  (dowód OSD) albo wcale nie była awarią; raport końcowy zamykaj po upływie okna korekt.
- Dane kwartalne dla regulatora zamrażaj jako `kpi_snapshot`; późniejsza korekta to nowa wersja z powodem.

## 6. Tożsamość portu
- Zmiana `evse_id` (przeniesienie, zmiana operatora w ID, wymiana urządzenia) nie przerywa historii: wewnętrzny
  `port_id` zostaje, `evse_id` dostaje nowy przedział ważności (formaty: dom-ev-identifiers).
- W raporcie regulacyjnym identyfikator portu ma być taki sam jak w API danych; sprawdź, który `evse_id` obowiązywał
  w okresie raportu.
- Zamiana urządzenia na to samo EVSE: port ten sam, sprzęt inny; model i firmware w wymiarze z historią (dom-ev-asset-operations).
- Złącza: jeden `port_id` na EVSE; złącze to atrybut. Statusy złączy agreguj do portu regułą z definicji (np. port
  „up”, gdy każde złącze, które może się ładować, nie jest `Faulted`).

## 7. Porty nowe (okres krótszy niż rok)
- Czas przed uruchomieniem (stan `PLANNED`, commissioning) nie jest ani „up”, ani „down”. Okno portu zaczyna się
  w dacie uruchomienia, a nie w dacie rozpoczęcia raportu.
- Wzór NEVI ma stałą 525 600 min: port uruchomiony w połowie roku ze stałą w mianowniku wypada sztucznie dobrze.
  Jak ma być liczony do raportu — **[do weryfikacji]** w wytycznych odbiorcy. Do własnej analizy licz na oknie portu
  (`--unknown exclude` w skrypcie) i oznacz „niepełny rok”.
- Przy porównaniach portów podawaj długość okna obok procentu; port z 10 dniami i jedną awarią wygląda gorzej
  od portu z rokiem danych.

## 8. Agregacja
Zasada: sumuj liczniki i mianowniki, potem dziel. Dotyczy uptime, utilization, session success, marży na kWh.
Średnia procentów jest dopuszczalna tylko jako „średnia portu”, nazwana tak w raporcie. Podział po jednostce
biznesowej, kraju i modelu: te same zapytanie i definicja, inny `GROUP BY`; nie licz osobnych potoków.

## 9. Przykład liczbowy (ilustracja)
Lokalizacja A: 10 EVSE, utilization 30 %. Lokalizacja B: 2 EVSE, utilization 10 %.
- Średnia procentów: (30 + 10) / 2 = 20 %.
- Ważona czasem dostępności: (10 × 30 + 2 × 10) / 12 = 26,7 %.
Dla uptime: 100 portów po 99 % i jeden port 40 % daje średnią 98,4 %, a próg NEVI jest per port — raport musi
wskazać ten jeden port.
