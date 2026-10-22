---
name: dom-ev-cpms-architecture
description: Użyj przy projekcie lub ocenie architektury CSMS/CPMS — brama WebSocket OCPP, routing komend do stacji, reconnect storm, multi-tenancy, granice kontekstów.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy projektujesz lub oceniasz backend operatora ładowarek (CSMS/CPMS) niezależnie od języka i frameworka — brama WebSocket OCPP jako osobny komponent, afinicja połączenia do węzła, rejestr połączeń i dostarczanie komend CSMS→ładowarka przez szynę lub kolejkę, heartbeat i martwe połączenia, reconnect storm po awarii lub wdrożeniu, warstwa anty-korupcyjna 1.6/2.0.1 → wspólny model, zdarzenia domenowe i idempotencja, stan stacji i Device Model, OCPI jako osobny kontekst, multi-tenancy i white-label (party_id na najemcę), obserwowalność, granice kontekstów. Nie do treści komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x), kolejności kroków sesji (dom-ev-session-lifecycle), diagnozy konkretnej awarii (dom-ev-diagnostics) ani ról rynku (dom-ev-market-roles)."
  slowa: "architektura CSMS, architektura CPMS, backend ładowarek, brama OCPP, OCPP gateway, WebSocket, trwałe połączenia, kilka instancji, load balancer, sticky session, komenda ginie, RemoteStart ginie, rejestr połączeń, connection registry, szyna wiadomości, kolejka, reconnect storm, burza połączeń, wszystkie ładowarki łączą się naraz, po wdrożeniu, thundering herd, jitter, backoff, BootNotification Pending, heartbeat, martwe połączenie, half-open, skalowanie poziome, horizontal scaling, wiele wersji OCPP, 1.6 i 2.0.1, anti-corruption layer, idempotencja messageId, kolejność per stacja, multi-tenant, white-label CPMS, wielu CPO, izolacja najemców, party_id najemcy, metryki, obserwowalność, ADR"
---

# Architektura CSMS/CPMS — jak zaprojektować i ocenić backend operatora

Skill daje **procedurę z decyzjami (ADR) i checklistą**. Jest niezależny od języka, frameworka i chmury: nie
rekomenduje produktów. Szczegóły protokołu — dom-ev-ocpp-16, dom-ev-ocpp-2x; przebieg sesji —
dom-ev-session-lifecycle; diagnoza awarii na żywo — dom-ev-diagnostics.

Nazewnictwo: CSMS = CPMS = backend operatora (dom-ev-glossary). Stacja to klient OCPP i **sama inicjuje** połączenie
WebSocket; backend nie może otworzyć połączenia do stacji (źródło: `.claude/skills/dom-ev-charging/references/ocpp.md`, sekcja 3).

## Mapa komponentów
| Komponent | Odpowiada za | Nie robi |
|---|---|---|
| **Brama OCPP** (gateway) | TLS/uwierzytelnienie stacji, WebSocket, podprotokół (`ocpp1.6` / `ocpp2.0.1`), ramki CALL/CALLRESULT/CALLERROR, walidacja schematu, heartbeat, rejestr połączeń | reguł domeny: taryf, autoryzacji, sesji |
| **Adapter wersji** (ACL) | mapowanie komunikatów 1.6 i 2.x na **wspólny model zdarzeń** | decyzji biznesowych |
| **Szyna / kolejka** | zdarzenia stacja→domena i komendy domena→stacja, kolejność per stacja | przechowywania stanu domeny |
| **Konteksty domeny** | Asset, Charging Session, Authorization, Pricing, Billing/CDR, Roaming, Energy, Support/NOC | obsługi gniazd |
| **Magazyn stanu stacji** | ostatni znany stan, konfiguracja / Device Model, wersja protokołu, węzeł bramy | historii sesji |
| **Integracja OCPI** | roaming z eMSP/hubem — osobny kontekst i osobny model | protokołu stacji |

## Procedura: zaprojektuj lub oceń CSMS
Dla każdego kroku zapisz decyzję jako ADR (kontekst, opcje, wybór, konsekwencje) — docs-tech-writing.

1. **Wymagania i skala.** Liczba stacji, liczba najemców (CPO), mieszanka wersji OCPP, oczekiwany udział
   offline, RTO/RPO. Liczb wydajnościowych (ile połączeń na węzeł, ile komunikatów na sekundę) **nie przyjmuj
   z głowy** — ustal je pomiarem własnym (test obciążeniowy z symulatorem stacji) albo ze źródła z datą; w tym skillu: **[do weryfikacji]**.
   Źródło ogólne mówi tylko o „horizontal scalability” i skali tysięcy–milionów sesji, bez wzorców.
2. **Wydziel bramę.** ADR: brama jako osobny deployment od logiki domeny; wdrożenie logiki nie rozłącza stacji.
3. **Afinicja połączenia.** Połączenie stacji żyje na jednym węźle bramy, więc potrzebny jest **rejestr połączeń**
   `stationId → (węzeł, wersja, czas połączenia)` z TTL odnawianym heartbeatem.
4. **Routing komend CSMS→stacja.** Domena nie woła bramy „na ślepo”: publikuje **komendę** na szynę z kluczem
   `stationId`; brama węzła-właściciela konsumuje i wysyła CALL. Stacja nie połączona → jawny wynik
   „offline” (nie cichy zanik). Komenda ma `commandId`, termin ważności i **korelację**: CALLRESULT/CALLERROR wraca
   jako zdarzenie z tym `commandId`. Komenda (CSMS → stacja) i zdarzenie (stacja → CSMS) trzymaj osobno; publikacja przez outbox, odbiór idempotentny (inbox).
5. **Heartbeat i martwe połączenia.** Heartbeat z BootNotification i ping/pong WebSocket; brak ruchu → zamknij,
   wyczyść rejestr, zdarzenie „stacja offline” (krotność dobierz pomiarem). Nowe połączenie tej samej stacji
   **wypiera** stare, inaczej dostaniesz dwa „właściwe” węzły.
6. **Reconnect storm.** Po awarii węzła lub wdrożeniu wszystkie stacje wracają jednocześnie (nowe TLS + BootNotification
   + zaległe kolejki offline). Projektuj obronę warstwowo — tabela niżej. Szczegóły: `references/brama-i-routing.md`.
7. **Walidacja i warstwa anty-korupcyjna.** Brama waliduje ramkę względem schematu wersji i odpowiada CALLERROR;
   dopiero poprawna ramka wchodzi dalej. Adapter mapuje 1.6 i 2.x na wspólny model (np. transakcja ze `Started/Updated/
   Ended`), a **domena nie zna wersji protokołu**. Odchylenia producentów — w adapterze, nie w domenie
   (dom-ev-ocpp-16, dom-ev-ocpp-2x).
8. **Zdarzenia, kolejność, idempotencja.** Ramka → zapis → zdarzenie domenowe (outbox, spójność zapisu i publikacji).
   Kolejność gwarantuj **per stacja** (klucz partycji = `stationId`), nie globalnie. Duplikaty (retransmisja po
   reconnect) odrzucaj po kluczu idempotencji: `stationId + messageId` dla ramek, a dla transakcji 2.x dodatkowo
   `transactionId + seqNo`. Luki w `seqNo` oznacz, nie ukrywaj.
9. **Stan stacji i Device Model.** Jedno źródło prawdy o stanie stacji (połączona?, ostatni status złącza, wersja
   firmware, konfiguracja). Dla 2.x trzymaj Device Model (komponent/zmienna/atrybut); dla 1.6 — płaską konfigurację
   za tym samym interfejsem. Stan z ramek nadpisuj tylko nowszym znacznikiem czasu/sekwencją.
10. **OCPI jako osobny kontekst.** Roaming ma własny model (Location/EVSE/Connector, Session, CDR, Tariff, Token),
    własne wersje i własny cykl wdrożeń. Komunikacja z domeną przez zdarzenia/porty; model OCPI nie przecieka do
    domeny ani do bramy OCPP (warstwa anty-korupcyjna na granicy). Role i przepływy — dom-ev-market-roles;
    model OCPI — `.claude/skills/dom-ev-charging/references/ocpi.md`.
11. **Multi-tenancy i white-label.** ADR: poziom izolacji (współdzielone vs osobne zasoby), po czym najemca jest
    rozpoznawany **na bramie** (ścieżka URL, certyfikat, identyfikator stacji → najemca w rejestrze) i jak kontekst
    najemcy płynie przez szynę. Zasady: `tenantId` w każdej wiadomości i zapytaniu; `country_code` + `party_id`
    na najemcę (dom-ev-identifiers); osobne klucze partycji lub limity, żeby hałaśliwy najemca nie zagłodził
    innych. Szczegóły i testy izolacji: `references/konteksty-i-tenancy.md`.
12. **Obserwowalność.** Minimalny zestaw w tabeli niżej; alerty z SLO (cel dostępności i czasu odpowiedzi).
13. **Ocena istniejącego CSMS.** Przejdź checklistę; każdą lukę opisz scenariuszem awarii („co się stanie, gdy węzeł X padnie
    w trakcie transakcji”), nie ogólnikiem.

## Obrona przed reconnect storm
| Warstwa | Środek | Uwaga |
|---|---|---|
| Wdrożenie | rolling z **drenażem** (węzeł przestaje przyjmować nowe, zamyka połączenia partiami) | nie restartuj wszystkich węzłów bramy naraz |
| Stacja | backoff wykładniczy z **jitterem** | zależy od firmware; sprawdź ustawienia, nie zakładaj |
| Brama | limit nowych handshake’ów / TLS na sekundę, kolejka oczekujących, odrzucenie z 503 | przy braku limitu storm przenosi się na CPU TLS |
| Protokół | odpowiedź `Pending` na BootNotification z `interval` rozkładającym kolejne próby | `Pending` = nie wykonuj jeszcze operacji; `Rejected` zablokuje stację dłużej |
| Domena | zaległe wiadomości z kolejki offline przetwarzaj ze współbieżnością ograniczoną per najemca | idempotencja chroni przed duplikatami |
| Pojemność | bufor węzłów na utratę strefy; test obciążeniowy „wszyscy wracają” | liczby: **[do weryfikacji]**, mierz |

## Obserwowalność — minimum
| Sygnał | Po co | Uwaga |
|---|---|---|
| liczba aktywnych połączeń (węzeł, najemca, wersja) | pojemność, wykrycie masowego rozłączenia | gwałtowny spadek = alarm |
| tempo nowych połączeń i handshake’ów | wykrycie storm | porównuj z oknem sprzed wdrożenia |
| opóźnienie odpowiedzi na CALL (percentyle) | zdrowie bramy i domeny | osobno dla `Authorize` i transakcji |
| odsetek CALLERROR (po kodzie błędu, producencie) | błędy schematu, odchylenia sprzętu | rosnący po wdrożeniu = regresja walidacji |
| otwarte sesje i sesje bez aktualizacji | wykrycie sesji-duchów | próg „bez aktualizacji” wg interwału MeterValues |
| opóźnienie komenda→CALLRESULT, odsetek „offline” | niezawodność RemoteStart/Stop | dołącz `commandId` do logów |
| głębokość kolejki i opóźnienie konsumenta per partycja | zator w domenie | |

Logi i ślady niosą `stationId`, `tenantId`, `messageId`, `commandId` — bez danych osobowych kierowców (RODO).

## Przykład
**Wejście:** „3 instancje backendu za LB, RemoteStart czasem ginie.”
**Diagnoza:** komenda trafia na instancję, która nie trzyma połączenia stacji (afinicja).
**Wynik (ADR-03/04):** (1) rejestr `stationId → węzeł` zapisywany przez bramę przy handshake, TTL odnawiany heartbeatem;
(2) domena publikuje komendę na szynę z kluczem `stationId`; (3) brama-właściciel wysyła CALL i publikuje wynik
z `commandId`; (4) brak wpisu w rejestrze → natychmiastowy wynik „offline”, a domena decyduje o ponowieniu;
(5) metryka: odsetek komend „offline” i opóźnienie komenda→CALLRESULT. Odrzucona opcja: sticky session na LB
(dotyczy nowych połączeń, nie rozwiązuje komend inicjowanych przez backend).

## Pułapki
- „Backend łączy się do stacji” — połączenie zawsze inicjuje stacja.
- Sticky session jako cały routing komend; rejestr połączeń bez TTL (zombie wpisy → komendy w próżnię).
- Brama i logika domeny w jednym deploymencie: każde wdrożenie rozłącza wszystkie stacje i wywołuje storm.
- Wersja OCPP przeciekająca do domeny (`if version == "1.6"` w taryfach).
- Globalna kolejność zamiast per stacja albo brak idempotencji po reconnect (duplikaty transakcji i CDR).
- Odpowiedź `Rejected` na BootNotification „dla ochłonięcia” — stacja uznaje się za nieautoryzowaną; do spowolnienia służy `Pending`.
- Brak limitów per najemca w multi-tenancy; `tenantId` ustalany z treści ramki zamiast z uwierzytelnionego połączenia.
- Liczby wydajnościowe z blogów bez daty i warunków pomiaru.

## Checklista
- [ ] Brama jest osobnym komponentem; wdrożenie domeny nie rozłącza stacji
- [ ] Rejestr połączeń z TTL; nowe połączenie wypiera stare
- [ ] Komendy idą szyną z kluczem `stationId`, mają `commandId`, termin i jawny wynik „offline”
- [ ] Heartbeat + ping/pong; martwe połączenia zamykane, zdarzenie „offline” emitowane
- [ ] Obrona przed reconnect storm: drenaż, jitter, limit handshake’ów, `Pending`, test „wszyscy wracają”
- [ ] Walidacja schematu na bramie; adapter wersji; domena nie zna wersji OCPP
- [ ] Kolejność per stacja, idempotencja (`messageId`, `transactionId`+`seqNo`), luki `seqNo` widoczne
- [ ] Stan stacji w jednym miejscu; Device Model dla 2.x za wspólnym interfejsem
- [ ] OCPI osobnym kontekstem z własnym modelem
- [ ] `tenantId` z uwierzytelnionego połączenia, limity per najemca, `party_id` na najemcę
- [ ] Metryki z tabeli, alerty z SLO; liczby pojemności zmierzone, nie zgadnięte
- [ ] Każda decyzja jako ADR

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| szczegóły bramy: rejestr, wypieranie połączeń, kontrakt komendy, storm krok po kroku | `references/brama-i-routing.md` |
| mapa kontekstów, zdarzenia, multi-tenancy, szablon ADR | `references/konteksty-i-tenancy.md` |

## Źródła
- `.claude/skills/dom-ev-charging/references/ocpp.md` (sekcje 3, 5, 10, 12; import 2024–2025): topologia, cykl połączenia,
  BootNotification `Accepted/Pending/Rejected`, Heartbeat, reconnect z backoffem, skalowanie poziome i wiele wersji OCPP.
  Źródło **nie** opisuje wzorców (sharding, kolejki, orkiestracja) — wzorce w tym skillu to wiedza ogólna inżynierii
  systemów rozproszonych, nie fakt ze specyfikacji.
- `.claude/skills/dom-ev-charging/references/ocpi.md` (rola OCPI jako roaming).
- Liczby wydajnościowe, wartości timeoutów i zachowanie backoffu konkretnych producentów: [do weryfikacji].
Opracowane własnymi słowami, stan na 2026-10-20.
