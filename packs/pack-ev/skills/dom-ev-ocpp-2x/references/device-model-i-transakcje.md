# Device Model, transakcje i statusy w OCPP 2.0.1

## 1. Device Model
Stacja opisuje się jako drzewo: **komponent** (np. stacja, EVSE, złącze) ma **zmienne**, a każda zmienna
ma **atrybuty** (m.in. wartość bieżąca, ustawiona, minimalna, maksymalna — dokładne nazwy [do weryfikacji]).
`GetVariables` czyta, `SetVariables` zapisuje; odpowiedź zawiera wynik per zmienna, więc jedna zmienna może się
nie powieść, a reszta tak. Zamiast płaskiego klucza z 1.6 adresujesz parę komponent + zmienna.
Nazw konkretnych komponentów i zmiennych nie wpisuj z pamięci — [do weryfikacji] w specyfikacji OCA.

## 2. Raporty
`GetBaseReport` prosi stację o raport, a stacja odpowiada porcjami przez `NotifyReport`. Używaj do inwentaryzacji
nowej stacji po `BootNotification` i do porównania stanu z rejestrem urządzeń. Odpowiedź na `GetBaseReport` tylko
potwierdza przyjęcie; dane przychodzą osobnymi komunikatami (obsłuż asynchronicznie).

## 3. Transakcje i offline
- `Started` otwiera, `Updated` niesie zmiany i pomiary, `Ended` zamyka; `seqNo` rośnie w obrębie transakcji.
- `transactionId` nadaje stacja. CSMS odpowiada na każde zdarzenie; brak odpowiedzi → stacja ponawia.
- Offline: stacja zapisuje zdarzenia i wysyła po reconnect (zachowanie wg importu, `ocpp.md` pkt 7 i FAQ).
  CSMS wykrywa brak po lukach w `seqNo`.
- Polityka luk: przyjmij, oznacz niekompletność, czekaj na uzupełnienie, alarmuj po czasie; nigdy nie zgaduj
  energii z interpolacji bez oznaczenia.

## 4. Statusy i mapowanie na 1.6
| `connectorStatus` 2.0.1 | Najbliższe w 1.6 | Uwaga |
|---|---|---|
| `Available` | `Available` | |
| `Occupied` | `Preparing`, `Charging`, `SuspendedEV`, `SuspendedEVSE`, `Finishing` | który — wynika ze stanu transakcji |
| `Reserved` | `Reserved` | |
| `Unavailable` | `Unavailable` | |
| `Faulted` | `Faulted` | |

Odwrotnie (1.6 → 2.0.1) kilka stanów zlewa się w `Occupied`; model domeny przechowuje stan szczegółowy, jeśli
wersja go daje.

Źródło: `.claude/skills/dom-ev-charging/references/ocpp.md` (import, 2026-09-27); reszta wiedza ogólna, oznaczona.
