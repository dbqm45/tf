# Mini-CSMS OCPP 1.6J

Przykład dydaktyczny i cel testów end-to-end fabryki. To nie jest produkcja. Pokazuje, jak w CSMS wyglądają
rejestracja stacji, autoryzacja, transakcja, odczyty licznika i idempotencja po `messageId`. Działa na samej bibliotece
standardowej Pythona (WebSocket z `.claude/skills/dom-ev-simulation-testing/scripts/ocpp_ws.py`).

## Uruchomienie
```bash
python3 examples/mini-csms-ocpp16/csms.py --port 9000 --tokens TAG1,TAG2 --sessions sessions.jsonl
# w drugim terminalu: stacja z symulatora, log dla analizatora
python3 .claude/skills/dom-ev-simulation-testing/scripts/charge_sim.py ws://127.0.0.1:9000/ocpp/CP1 --log sim.jsonl
python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py sim.jsonl
```
Awaria do sprawdzenia: `--fault drop-stop` daje sesję `open` w `sessions.jsonl`, a analizator zgłasza
`open-transaction`. Pełna lista awarii jest w skillu dom-ev-simulation-testing.

## Co obsługuje
| Akcja (stacja → CSMS) | Zachowanie |
|---|---|
| BootNotification | `Accepted`, `interval` 300 s; zapis producenta, modelu i firmware; czyści pamięć `messageId` stacji |
| Heartbeat | `currentTime` |
| StatusNotification | stan złącza stacji |
| Authorize | `Accepted`, gdy `idTag` jest na liście `--tokens`, inaczej `Invalid` |
| StartTransaction | nowy `transactionId`; sesja `open` tylko dla przyjętego tokena |
| MeterValues | ostatni odczyt `Energy.Active.Import.Register` (Wh lub kWh) i licznik odczytów |
| StopTransaction | sesja `closed`, energia = `meterStop − meterStart` |
| inne | CALLERROR `NotImplemented` |

Powtórzony `messageId` tej samej stacji dostaje zapamiętaną odpowiedź i nie daje drugiego skutku.

## Czego brakuje do produkcji
- TLS (`wss://`) i profile bezpieczeństwa OCPP; uwierzytelnienie stacji.
- Trwały magazyn sesji i transakcji, a do tego outbox do rozliczeń i roamingu.
- Domykanie sesji osieroconych (brak StopTransaction): próg czasu, alarm, decyzja operatora.
- Komendy do stacji (RemoteStart/Stop, Reset, ChangeConfiguration) i ich routing przy wielu instancjach bramy.
- OCPP 2.0.1 (TransactionEvent, seqNo) i flota mieszana.
- Kontrola, czy stacja jest znana (Boot `Pending`/`Rejected`, onboarding: dom-ev-charger-onboarding).

Architekturę produkcyjną opisuje dom-ev-cpms-architecture, cykl sesji dom-ev-session-lifecycle.

## Test
`python3 tests/test_mini_csms.py` uruchamia symulator na tym CSMS i sprawdza sesje oraz logi analizatorem. Katalog
`examples/` nie trafia do projektu przy instalacji fabryki, więc w projekcie test się pomija.
