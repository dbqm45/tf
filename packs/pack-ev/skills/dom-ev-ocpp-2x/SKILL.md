---
name: dom-ev-ocpp-2x
description: Użyj przy OCPP 2.0.1 lub 2.1 — Device Model, TransactionEvent i seqNo, profile bezpieczeństwa 1–3, różnice wobec 1.6, flota mieszana 1.6 + 2.x w CSMS.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy praca dotyczy OCPP 2.0.1 lub 2.1 po stronie CSMS albo ładowarki — Device Model (komponenty, zmienne, atrybuty), TransactionEvent Started/Updated/Ended, seqNo i transactionId, offline, StatusNotification z connectorStatus, profile bezpieczeństwa 1–3 (Basic Auth, TLS, mTLS), ISO 15118 przez OCPP w zarysie, rozszerzenia 2.1, rozpoznanie wersji i adaptery we flocie mieszanej 1.6 + 2.x. Nie do OCPP 1.6 (dom-ev-ocpp-16), słownika pojęć (dom-ev-glossary), roamingu OCPI ani szczegółów ISO 15118 (dom-ev-charging)."
  slowa: "OCPP 2.0.1, OCPP 2.1, TransactionEvent, seqNo, triggerReason, Device Model, GetVariables, SetVariables, GetBaseReport, NotifyReport, security profile, mTLS, certyfikat klienta, Sec-WebSocket-Protocol, ocpp2.0.1, flota mieszana, adapter wersji, V2X, DER, edycja specyfikacji, CSMS"
---

# OCPP 2.0.1 i 2.1 — CSMS i ładowarka

OCPP 2.x **nie jest zgodne wstecz z 1.6**: inny model danych (Device Model zamiast płaskiej konfiguracji) i inny
model transakcji (`TransactionEvent` zamiast `StartTransaction`/`StopTransaction`). Nie da się „podbić wersji”
w parserze; potrzebny jest osobny adapter. 2.1 rozszerza 2.0.1 (w dużej mierze zgodne z 2.0.1, nie z 1.6).
Zawsze zapisuj **wersję i edycję** specyfikacji OCA (np. „2.0.1, edycja N”) — numery edycji: [do weryfikacji].

## Mapa 1.6 → 2.x
| Obszar | OCPP 1.6 | OCPP 2.0.1 |
|---|---|---|
| Konfiguracja | `GetConfiguration`/`ChangeConfiguration` (płaskie klucze) | Device Model: `GetVariables`/`SetVariables` |
| Pełny stan urządzenia | brak | `GetBaseReport` → `NotifyReport` |
| Transakcja | `StartTransaction`, `StopTransaction` | `TransactionEvent` (`Started`/`Updated`/`Ended`) |
| Zdalny start/stop | `RemoteStartTransaction`/`RemoteStopTransaction` | `RequestStartTransaction`/`RequestStopTransaction` |
| Status konektora | 9 stanów (w tym `Preparing`, `Charging`) | 5 stanów, stan ładowania niesie `TransactionEvent` |
| Bezpieczeństwo | opcjonalny dodatek (Security Whitepaper) | profile 1–3 w standardzie |
| Podprotokół WebSocket | `ocpp1.6` | `ocpp2.0.1` (2.1: [do weryfikacji] dokładny ciąg) |

Szczegóły Device Model, transakcji i statusów: `references/device-model-i-transakcje.md`.

## TransactionEvent — reguły, które psują integracje
- `eventType`: `Started`, `Updated`, `Ended`. Każde zdarzenie ma `seqNo` **rosnący w obrębie jednej transakcji**
  (nie globalnie, nie per stacja).
- **`transactionId` nadaje stacja**, nie CSMS (w 1.6 nadawał CSMS w odpowiedzi na `StartTransaction`). Klucz
  w bazie: stacja + `transactionId`.
- Pole `triggerReason` mówi, dlaczego zdarzenie wysłano; wartości [do weryfikacji] w specyfikacji — nie zgaduj.
- Offline: stacja kolejkuje zdarzenia i wysyła je po reconnect, więc mogą przyjść **po czasie**; ufaj `seqNo` i
  znaczniku czasu zdarzenia, nie czasowi odbioru.
- Luka w `seqNo` (ostatni zapisany 5, przychodzi 7): **nie odrzucaj** zdarzenia i nie zamykaj sesji. Zapisz je
  z jego `seqNo`, oznacz transakcję jako niekompletną (brak 6), przetwarzaj kolejność po `seqNo`, a brakujący
  numer może jeszcze dotrzeć (opóźnienie, retransmisja). Dopiero `Ended` bez uzupełnienia luki po ustalonym
  czasie → alarm i rozliczenie z oznaczeniem „dane niepełne”, nie ciche zgadywanie energii.
- Duplikat (ten sam `seqNo` i treść) przetwarzaj idempotentnie — odpowiedz sukcesem, nie zapisuj drugi raz.

## Profile bezpieczeństwa
| Profil | Transport | Uwierzytelnienie | Użycie |
|---|---|---|---|
| 1 | `ws://` | Basic Auth | tylko testy i sieci izolowane |
| 2 | `wss://` (TLS) | Basic Auth przez TLS | minimum produkcyjne |
| 3 | `wss://` (mTLS) | certyfikat klienta ładowarki + serwera | wysokie bezpieczeństwo, sieci publiczne |

**Certyfikat klienta po stronie ładowarki wymaga tylko profil 3.** Za nim stoi PKI: wystawianie, rotacja,
unieważnianie i magazyn zaufanych CA. Komunikaty cyklu życia certyfikatów: `SignCertificate`,
`InstallCertificate`, `DeleteCertificate`, `GetInstalledCertificateIds`; zdarzenia: `SecurityEventNotification`.
Certyfikaty i PKI: rotacja przed wygaśnięciem, unieważnianie, bezpieczne przechowywanie kluczy prywatnych na stacji.

## ISO 15118 przez OCPP (zarys)
Plug & Charge w 2.0.1: ładowarka przekazuje certyfikat kontraktu pojazdu; `Get15118EVCertificate` obsługuje
provisioning certyfikatu, `NotifyEVChargingNeeds` niesie potrzeby ładowania pojazdu, CSMS odpowiada profilem
(`SetChargingProfile`). Szczegóły, EMAID i PKI V2G: `.claude/skills/dom-ev-charging/references/iso-15118.md`.

## OCPP 2.1 — poziom pewności
| Fakt | Poziom |
|---|---|
| OCA wydało 2.1 w styczniu 2025 | wtórne — [do weryfikacji] |
| Opublikowane jako IEC 63584-210:2025, data 2025-12-09 | wtórne — [do weryfikacji] |
| Możliwe nowe edycje: 2.0.1 Edition 4 i 2.1 Edition 2 (grudzień 2025) | niepotwierdzone — [do weryfikacji] |
| Zakres: V2X/dwukierunkowość, DER, płatności lokalne | wg importu; szczegóły [do weryfikacji] |

Źródło wtórne: strona OCA była niedostępna przy sprawdzaniu (2026-10-20). Przed dokumentem dla klienta lub
zapisem w umowie sprawdź specyfikację u OCA. Więcej: `references/ocpp-21.md`.

## Procedura: CSMS dla floty mieszanej 1.6 + 2.0.1 (skrót)
1. **Rozpoznaj wersję** przy upgrade WebSocket po nagłówku `Sec-WebSocket-Protocol` (`ocpp1.6` / `ocpp2.0.1`);
   odpowiedz tym samym podprotokołem. Brak zgodnego podprotokołu → odrzuć połączenie.
2. **Osobny adapter na wersję** (ramki, walidacja schematów, kody błędów — różnią się, np. `FormationViolation`
   w 1.6 i `FormatViolation` w 2.0.1). Adapter nie wycieka typów protokołu do domeny.
3. **Wspólny model domeny**: Station, EVSE, Connector, ChargingSession, MeterReading, Availability. Adaptery
   tłumaczą do niego i z niego (warstwa anty-korupcyjna).
4. **Statusy**: 2.0.1 `Occupied` → w 1.6 odpowiada jednemu z `Preparing`/`Charging`/`SuspendedEV`/`SuspendedEVSE`/
   `Finishing`; rozstrzygnij po stanie transakcji. W domenie trzymaj model własny, nie słownik żadnej wersji.
5. **Transakcje**: 1.6 `StartTransaction` → sesja otwarta, `StopTransaction` → zamknięta; 2.0.1 `Started`/`Ended`
   i `Updated` jako telemetria. Kluczem sesji jest para (stacja, id transakcji) niezależnie od tego, kto nadał id.
6. **Wersja i edycja** stacji zapisana w rejestrze urządzeń; testy kontraktowe osobno na wersję.
Pełna migracja floty 1.6 → 2.x nie jest tu opisana.

## Przykład
Wejście: `[2,"m9","TransactionEvent",{"eventType":"Updated","seqNo":7,...}]`, w bazie dla tej stacji i
transakcji `abc-1` ostatnie `seqNo` = 5.
Wynik: zapisz zdarzenie `seqNo` 7, transakcja `abc-1` → „niekompletna, brak 6”, odpowiedz `CallResult`
(nie `CallError`), ustaw timer na uzupełnienie. Przyjdzie 6 → luka zamknięta; `Ended` z lukami po timerze →
alarm i rozliczenie oznaczone jako niepełne.

## Pułapki
- Założenie, że `transactionId` nadaje CSMS (tak było w 1.6).
- Mapowanie 1:1 statusów 1.6 ↔ 2.0.1; `Charging` nie istnieje w `connectorStatus` 2.0.1.
- `seqNo` traktowane jako globalny licznik stacji.
- Odrzucanie spóźnionych zdarzeń offline jako „błędnych”.
- Profil 1 lub 2 opisywany jako „bezpieczny, bo ma hasło” bez oceny sieci; certyfikat klienta tylko w profilu 3.
- Podawanie „OCPP 2.0.1” bez edycji; zakładanie, że wszystko z 2.1 dotyczy 2.0.1.

## Checklista
- [ ] Wersja **i edycja** specyfikacji zapisana
- [ ] Wersja rozpoznana z `Sec-WebSocket-Protocol`, adapter osobny na wersję
- [ ] `transactionId` od stacji, klucz (stacja, id), obsługa luk i duplikatów `seqNo`
- [ ] Mapowanie statusów przez model domeny, nie 1:1
- [ ] Profil bezpieczeństwa wybrany świadomie; PKI zaplanowane dla profilu 3
- [ ] Fakty o 2.1 oznaczone [do weryfikacji] do czasu sprawdzenia u OCA

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| komponenty/zmienne/atrybuty, `GetBaseReport`, statusy i mapowanie na 1.6, offline | `references/device-model-i-transakcje.md` |
| 2.1: V2X, DER, płatności, data wydania, IEC 63584-210, edycje | `references/ocpp-21.md` |
| ramki, kody błędów, katalog komunikatów, smart charging | `.claude/skills/dom-ev-charging/references/ocpp.md` |

## Źródła
- `.claude/skills/dom-ev-charging/references/ocpp.md` (import 2024–2025, włączony 2026-09-27).
- `fakty-1a.md` (researcher, 2026-10-20): wiersz o OCPP 2.1 i IEC 63584-210 — poziom wtórny.
- Wiedza ogólna oznaczona w tekście jako [do weryfikacji] (wartości `triggerReason`, ciąg podprotokołu 2.1).
