# Statusy złącza i transakcje (1.6J)

Lista statusów pochodzi z `ocpp.md`. Przejścia i kolejność ramek to wiedza ogólna o OCPP 1.6 — **[do weryfikacji]**
w specyfikacji OCA (tabela przejść statusów w Core).

## Statusy i znaczenie
| Status | Znaczenie |
|---|---|
| `Available` | wolne, gotowe |
| `Preparing` | kabel wpięty lub autoryzacja wykonana, ładowanie jeszcze nie ruszyło |
| `Charging` | energia płynie |
| `SuspendedEV` | pojazd wstrzymał pobór (np. bateria pełna) |
| `SuspendedEVSE` | ładowarka wstrzymała (np. limit z profilu mocy) |
| `Finishing` | transakcja zakończona, kabel jeszcze wpięty |
| `Reserved` | zarezerwowane dla `idTag` |
| `Unavailable` | wyłączone z użycia (np. `ChangeAvailability`) |
| `Faulted` | usterka (kod błędu w polu `errorCode` `StatusNotification` — lista kodów **[do weryfikacji]**) |

## Typowe przejścia **[do weryfikacji]**
| Z | Do | Wyzwalacz |
|---|---|---|
| `Available` | `Preparing` | wpięty kabel lub przyłożona karta |
| `Preparing` | `Charging` | autoryzacja + kabel + start energii (`StartTransaction`) |
| `Preparing` | `Available` | kabel wypięty / autoryzacja wygasła bez startu |
| `Charging` | `SuspendedEV` / `SuspendedEVSE` | wstrzymanie przez pojazd / ładowarkę |
| `Suspended*` | `Charging` | wznowienie |
| `Charging` / `Suspended*` | `Finishing` | `StopTransaction`, kabel wpięty |
| `Finishing` | `Available` | kabel wypięty |
| dowolny | `Faulted` | usterka; po usunięciu powrót do właściwego stanu |
| `Available` | `Reserved` | `ReserveNow` |

`connectorId` 0 w `StatusNotification` opisuje ładowarkę jako całość (dopuszczalne statusy ograniczone —
**[do weryfikacji]**).

## Kolejność ramek sesji z RFID (typowo)
1. `StatusNotification` `Preparing` (kabel) · 2. `Authorize` (`idTag`) → `Accepted` · 3. `StartTransaction`
(`meterStart` w Wh) → odpowiedź z `transactionId` nadanym przez CSMS · 4. `StatusNotification` `Charging` ·
5. `MeterValues` okresowo · 6. `StopTransaction` (`meterStop`, `reason`) · 7. `StatusNotification` `Finishing` →
`Available`. Kolejność kroków 1/2 i 3/4 różni się między producentami.

## Sesja z aplikacji
CSMS wysyła `RemoteStartTransaction` (`idTag`, opcjonalnie `connectorId`); ładowarka odpowiada `Accepted`/`Rejected`
(to tylko przyjęcie komendy), a dopiero potem sama inicjuje `StartTransaction`. Nie traktuj odpowiedzi
`Accepted` jako startu energii.

## MeterValues
Rekordy z listą `sampledValue`: wartość, `measurand`, jednostka, opcjonalnie fazy i kontekst. Nazwy measurandów,
jednostki i domyślny zestaw — **[do weryfikacji]**. Energia na rachunek: różnica `meterStop − meterStart` z
`StopTransaction`; `MeterValues` służą do telemetrii i kontroli, nie zastępują liczników rozliczeniowych
(wymogi prawne/MID — poza zakresem skilla).
