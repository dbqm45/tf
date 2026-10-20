---
name: dom-ev-session-lifecycle
description: Użyj przy sesji ładowania end-to-end — OCPP i OCPI razem, autoryzacja, sesja vs transakcja vs CDR, sesje osierocone, offline, duplikaty, idempotencja.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba połączyć OCPP (ładowarka-CSMS) i OCPI (CPO-eMSP) w jedną sesję — etapy od podłączenia do rozliczenia, cztery ścieżki autoryzacji (aplikacja eMSP przez Commands, RFID, terminal płatniczy, Plug & Charge w zarysie), kolejność komunikatów w 1.6 i 2.0.1, różnica i własność OCPI Session, transakcji OCPP i CDR, sesje osierocone, późne transakcje po offline, duplikaty i klucze idempotencji, moment i niezmienność CDR, licznik jako źródło prawdy o energii oraz procedura projektu obsługi sesji w CSMS. Obejmuje też tryb free vend / kiosk i stan operatorski STOP_FAILED. Nie do szczegółów komunikatów i statusów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x), diagnozy awarii z logów (dom-ev-diagnostics), architektury CSMS (dom-ev-cpms-architecture) ani korekt CDR i modułów OCPI (dom-ev-charging)."
  slowa: "sesja ładowania, cykl sesji, session lifecycle, end-to-end, START_SESSION, RemoteStartTransaction, RequestStartTransaction, response_url, OCPI Session, transakcja OCPP, CDR, kiedy powstaje CDR, sesja osierocona, wisząca sesja, brak StopTransaction, ładowarka offline, późna transakcja, zbuforowane ramki, duplikat, idempotencja, seqNo, transactionId, messageId, licznik MID, meterStop, energia sesji, rozliczenie sesji, RFID, Authorize, terminal płatniczy, ad hoc, Plug & Charge, free vend, ładowanie bez autoryzacji, kiosk, STOP_FAILED, nie można zatrzymać sesji, RemoteStop odrzucony, zamknięcie administracyjne, AuthorizeRemoteTxRequests, LocalPreAuthorize, NoAuthorization"
---

# Sesja ładowania end-to-end — OCPP + OCPI

Skill łączy dwa protokoły w jedną sesję: **kto, w jakiej kolejności i z jakim kluczem** tworzy obiekty po obu
stronach CSMS. Komunikaty i statusy OCPP: `dom-ev-ocpp-16`, `dom-ev-ocpp-2x`. Korekty CDR i moduły OCPI:
`dom-ev-charging`. Pojęcia (sesja vs transakcja): `dom-ev-glossary`. Role stron: `dom-ev-market-roles`. Awaria z logów:
`dom-ev-diagnostics`. Architektura systemu CSMS: `dom-ev-cpms-architecture`.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/sekwencje.md` | potrzebujesz pełnego diagramu kolejności komunikatów dla 1.6 albo 2.0.1, ścieżek RFID i terminala |
| `references/free-vend-i-stop-failed.md` | free vend, kiosk, `STOP_FAILED`: konfiguracja stacji, przyczyny, ponowienie, zamknięcie administracyjne, wpływ na CDR |
| `references/projekt-obslugi-sesji.md` | projektujesz model danych sesji, maszynę stanów, zamykanie osieroconych, obsługę offline |

## Trzy obiekty, które wolno rozróżnić
| Obiekt | Protokół | Powstaje, gdy | Właściciel | Klucz |
|---|---|---|---|---|
| **Transakcja** | OCPP | ładowarka zgłasza start (`StartTransaction` / `TransactionEvent` `Started`) | ładowarka i CSMS | 1.6: `transactionId` nadaje **CSMS**; 2.0.1: `transactionId` nadaje **stacja** |
| **Session** | OCPI | CPO zaczyna raportować trwające ładowanie do eMSP | CPO (Sender), eMSP czyta | `session id` w trójce `country_code`/`party_id`/`id` |
| **CDR** | OCPI | sesja jest **zakończona** i energia ustalona | CPO; po wysłaniu niezmienny | `CDR id` |

- Jedna transakcja OCPP zwykle odpowiada jednej Session i jednemu CDR, ale **nie jest to tożsamość**: sesja
  OCPI istnieje tylko, gdy jest roaming (ładowanie własnymi tokenami CPO nie wysyła nic do eMSP), a w 2.0.1
  zdarzenia jednej transakcji mogą zasilić kilka aktualizacji Session.
- CSMS przechowuje **własną sesję domenową** i mapuje na nią oba obiekty (`dom-ev-ocpp-2x`: wspólny model
  domeny). Nie przepisuj `transactionId` do OCPI jako `session id`; wystaw osobny identyfikator i trzymaj tabelę
  powiązań.

## Etapy
1. **Podłączenie** — kabel wpięty, status złącza zmienia się (`Preparing` w 1.6, `Occupied` w 2.0.1).
2. **Autoryzacja** — jedna z czterech ścieżek (niżej).
3. **Ładowanie** — start transakcji, `MeterValues` (1.6) / `TransactionEvent Updated` (2.0.1); Session `ACTIVE` w OCPI.
4. **Zakończenie** — `StopTransaction` / `TransactionEvent Ended`; Session przechodzi w stan zakończony.
5. **CDR** — CPO ustala energię i koszt, wysyła CDR do eMSP.
6. **Rozliczenie** — eMSP fakturuje kierowcę, CPO i eMSP rozliczają się hurtowo na CDR (nie per sesja na żywo).

## Cztery ścieżki autoryzacji
| Ścieżka | Kto inicjuje | Łańcuch komunikatów | Uwaga |
|---|---|---|---|
| Aplikacja eMSP | kierowca w aplikacji | OCPI `START_SESSION` (eMSP→CPO) → OCPP `RemoteStartTransaction` (1.6) / `RequestStartTransaction` (2.0.1) → ładowarka | wynik komendy wraca asynchronicznie na `response_url` |
| RFID | karta przy czytniku | OCPP `Authorize(idTag)` (1.6) / `Authorize(idToken)` (2.0.1) → CSMS | CSMS sprawdza token z OCPI `Tokens`, lokalną listę albo pyta eMSP w czasie rzeczywistym (real-time authorization **[do weryfikacji]** w danej integracji) |
| Terminal płatniczy (ad hoc) | karta płatnicza | terminal blokuje kwotę (preautoryzacja) → system płatności zleca start CSMS | rozliczenie bezpośrednie B2C, bez eMSP i bez OCPI **[założenie]** |
| Plug & Charge | pojazd | ISO 15118: certyfikat kontraktu → ładowarka → `Authorize` w OCPP 2.0.1 | zarys; mechanizm: `.claude/skills/dom-ev-charging/references/iso-15118.md` |

Aplikacja a OCPP: **`RemoteStartTransaction` / `RequestStartTransaction` nie tworzy transakcji.** Odpowiedź
`Accepted` znaczy „ładowarka przyjęła polecenie”. Transakcja powstaje dopiero, gdy ładowarka sama wyśle
`StartTransaction` / `TransactionEvent Started` (po wpięciu kabla, jeśli jeszcze go nie ma). Brak tego
komunikatu w czasie oczekiwania = komenda nie zakończyła się startem; odpowiedz eMSP wynikiem `FAILED` lub
`TIMEOUT` (nazwy wartości `CommandResult` **[do weryfikacji]** w OCPI 2.2.1).

## Kolejność komunikatów
Skrót: START_SESSION (OCPI) → `RemoteStartTransaction` → `CommandResult` → `StartTransaction` → Session `ACTIVE` →
`MeterValues` → `StopTransaction` → Session zakończona → CDR (dopiero po `Stop` i ustaleniu energii). Pełne diagramy 1.6 i
2.0.1, RFID i terminal: `references/sekwencje.md`. Metody HTTP i adresy Sendera/Receivera: `dom-ev-charging` (`ocpi.md`).

## Free vend, kiosk i STOP_FAILED
- **Free vend** (stacja ładuje bez autoryzacji): to nadal transakcja z `MeterValues`; w CSMS potrzebny **token techniczny**
  (1.6: stały `idTag`; 2.0.1: `idToken` opcjonalny, typ `NoAuthorization` istnieje), sesja oznaczona `free_vend`, bez Session/CDR dla eMSP.
  Konfiguracja leży po stronie stacji (1.6: klucze autoryzacji przez `ChangeConfiguration`, 2.0.1: `AuthCtrlr`/`TxCtrlr` przez
  `SetVariables`; nazwy [do weryfikacji]) i jest wpisana do rejestru. **Kiosk** (terminal/ekran jako punkt startu): sesja wiąże się z płatnością lub tokenem technicznym.
- **`STOP_FAILED` to stan operatorski, nie OCPP:** CPO próbował zakończyć sesję, stacja nie potwierdziła (brak `StopTransaction`
  / `Ended`): offline, stop odrzucony, firmware, pojazd. Obsługa: `TriggerMessage` (`StatusNotification`, `MeterValues`), ponowienie
  z limitem, a po upływie okna **zamknięcie administracyjne z wpisem** (kto, dowód, `meterStop`, flaga szacunku). CDR dopiero po
  zamknięciu. Diagnoza z ramek: `dom-ev-diagnostics`. Szczegóły i tabela przyczyn: `references/free-vend-i-stop-failed.md`.

## Źródło prawdy o energii
Energię sesji wyznacza **licznik w ładowarce** (w EU licznik z legalizacją, MID **[do weryfikacji]** wymagania
w danym kraju), nie wyliczenie CSMS z mocy × czasu. Podstawa: `meterStop − meterStart` (1.6, w **Wh**) albo
odczyty licznika w `TransactionEvent` (2.0.1). Zapisuj **oba odczyty surowe** razem z jednostką; kWh liczysz
dopiero w CDR. Odczyty `MeterValues` w trakcie to podgląd (Session), nie podstawa rozliczenia. Brak
`meterStop` (sesja osierocona) → energia **szacowana**, oznaczona w danych i w CDR jako szacowana; nie
udawaj odczytu z licznika.

## CDR: kiedy i niezmienność
- Wystaw CDR **po** zakończeniu transakcji i zamknięciu sesji (znany `meterStop`, czas końca, taryfa
  zastosowana). Nie wystawiaj CDR na `Preparing`, ani na pierwszy brak `MeterValues`.
- Po wysłaniu do eMSP CDR jest **niezmienny**. Błąd po wysłaniu to korekta (CDR kredytowy + nowy CDR) wg
  `dom-ev-charging`; w CSMS pilnuj, żeby późny `StopTransaction` nie przeliczał już wysłanego CDR.
- Zwłoka między `Stop` a CDR jest normalna (luka `seqNo`, okno na spóźnione ramki); ustal ją jawnie [założenie].

## Klucze idempotencji
| Poziom | Klucz | Chroni przed |
|---|---|---|
| Ramka OCPP | (`chargePointId`, `messageId`) | ponowieniem tego samego CALL po zerwaniu |
| Transakcja 1.6 | `transactionId` nadany przez CSMS; zapasowo (`connectorId`, `idTag`, `timestamp`, `meterStart`) | drugą transakcją z tego samego `StartTransaction` |
| Transakcja 2.0.1 | (stacja, `transactionId`) + `seqNo` | podwójnym zapisem zdarzenia, lukami |
| Session OCPI | `session id` (trójka z `country_code`/`party_id`) | dwiema sesjami u eMSP; `PUT` tego samego id jest bezpieczny |
| CDR OCPI | `CDR id` | podwójną fakturą |

Ponowienie kończy się **tą samą odpowiedzią**, nie drugim skutkiem ubocznym. Szczegóły ramek: `dom-ev-ocpp-16`.

## Sesje osierocone i późne transakcje
- **Osierocona** (brak `StopTransaction`/`Ended`): utrata zasilania, reset, awaria łączności po stronie
  ładowarki. Zamykaj po sygnale (nowy `BootNotification`, `StatusNotification Available` na tym złączu, albo
  limit czasu bez `MeterValues`) i oznacz jako **szacowaną**. Nie zamykaj wcześniej niż po limicie — ładowarka
  może być po prostu offline i jeszcze wyśle prawdziwy `Stop`.
- **Późna transakcja po offline:** start i stop sprzed godzin przychodzą razem. Zapisz **czas z ramki**
  (skorygowany zegarem, `dom-ev-ocpp-16` → odchylenia) obok **czasu odbioru**. Do CDR idzie czas
  zdarzenia, nie czas odbioru. Do eMSP możesz wysłać Session od razu w stanie zakończonym (bez fazy `ACTIVE`),
  a po niej CDR.
- **Późny `Stop` po zamknięciu szacunkiem:** jeśli CDR jeszcze nie wysłano — zastąp szacunek odczytem z licznika.
  Jeśli wysłano — nie zmieniaj CDR, przekaż różnicę do ścieżki korekt (`dom-ev-charging`).

## Procedura: projekt obsługi sesji w CSMS odpornej na offline i duplikaty
Dziewięć kroków (pełna lista w `references/projekt-obslugi-sesji.md`, sekcja 6): (1) sesja domenowa z własnym id i powiązaniami;
(2) ramka + klucz idempotencji + zmiana stanu + outbox w jednej transakcji; (3) `czas_zdarzenia` osobno od `czas_odbioru`,
kolejność po `seqNo`; (4) nieoczekiwane ramki do kwarantanny, nigdy odrzucone; (5) Session i CDR z outboxa; (6) zamykacz
osieroconych z konfigurowalnym T; (7) energia surowa z licznika, kWh w CDR; (8) CDR po oknie na spóźnione ramki, potem tylko do odczytu;
(9) testy na nagranych ramkach (offline po 2 h, duplikat, `Stop` bez `Start`, luka `seqNo`, restart).

## Przykład
Wejście: ładowarka 1.6 wraca po 3 h offline i wysyła, w tej kolejności: `StartTransaction` (timestamp
`2026-10-20T06:05:00Z`, `meterStart` 120400) oraz `StopTransaction` (timestamp `2026-10-20T07:10:00Z`,
`meterStop` 131900). Odbiór: 09:00. Tej sesji nie było u eMSP.
Wynik: (1) `StartTransaction` → CSMS nadaje `transactionId`, tworzy sesję domenową ze `czas_zdarzenia` 06:05;
(2) `StopTransaction` → zamyka ją: energia = 131900 − 120400 = 11500 Wh = 11,5 kWh, czas 06:05–07:10; (3) oba
CALL z tym samym `messageId` ponowione = ta sama odpowiedź, bez drugiej sesji; (4) do eMSP: Session od razu w
stanie zakończonym z czasami zdarzeń, potem CDR z energią 11,5 kWh (po oknie na spóźnione ramki).

## Pułapki
- **Czas odbioru jako czas sesji:** po offline sesja „zaczyna się” o 09:00 zamiast 06:05 — zła taryfa czasowa.
- **Start komendą = transakcja:** `RemoteStart` `Accepted` nie jest startem sesji.
- **`transactionId` jako `session id` OCPI:** w 1.6 i 2.0.1 nadaje go inna strona, a zakres unikalności jest inny.
- **CDR z szacunku bez flagi:** eMSP fakturuje kierowcę za energię, której nikt nie zmierzył.
- **CDR przed `Stop`:** ładowanie trwa dalej, a rekord jest już niezmienny.
- **Odrzucenie zbuforowanej ramki:** pętla ponowień blokuje kolejkę ładowarki.
- **Wyliczanie energii z mocy × czasu** zamiast z licznika.
- **Mieszanie `seqNo` i `messageId`:** `messageId` identyfikuje ramkę (ponowienie), `seqNo` kolejność zdarzeń
  w transakcji 2.0.1; jedno nie zastępuje drugiego.
- **Zamykanie sesji po Heartbeatach:** Heartbeat nie dowodzi ładowania.
- **`STOP_FAILED` jako stan z OCPP** albo zamknięcie administracyjne bez odczytu i wpisu; free vend bez tokenu technicznego.

## Checklista
- [ ] Sesja domenowa z osobnymi id: transakcja OCPP, Session OCPI, CDR.
- [ ] Klucze idempotencji na każdym poziomie, unikalne indeksy, powtórka = ta sama odpowiedź.
- [ ] `czas_zdarzenia` i `czas_odbioru` osobno; kolejność po `seqNo`/czasie zdarzenia.
- [ ] Energia z licznika (Wh surowo, kWh w CDR); szacunek oznaczony.
- [ ] Zamykacz sesji osieroconych z konfigurowalnym limitem.
- [ ] CDR dopiero po zakończeniu i oknie na spóźnione ramki; po wysłaniu tylko do odczytu.
- [ ] Skutki uboczne (Session, CDR) przez outbox.
- [ ] Free vend: token techniczny i wpis konfiguracji; `STOP_FAILED`: próby stopu, okno, zamknięcie z wpisem
- [ ] Testy: offline po 2 h, duplikat, `Stop` bez `Start`, luka `seqNo`, restart w trakcie sesji.

## Źródła
- `.claude/skills/dom-ev-charging/references/cykl-sesji-ladowania.md` (import 2024–2025, włączony 2026-09-27):
  fazy, cztery ścieżki autoryzacji, moment CDR, niezmienność CDR.
- `ocpp.md`, `ocpi.md` w tym samym katalogu (offline, `seqNo`, Sender/Receiver, `response_url`).
- Schematy JSON OCPP (`ocpp-json-schemas`, pobrane 2026-10-20) dla free vend i STOP_FAILED: `references/free-vend-i-stop-failed.md`.
- Skille `dom-ev-ocpp-16` i `dom-ev-ocpp-2x` (stan: 2026-10-20): idempotencja, kwarantanna, `transactionId`, `seqNo`.
- Wiedza ogólna autora o OCPI 2.2.1 i OCPP — oznaczona **[do weryfikacji]** lub **[założenie]**; sprawdź w
  specyfikacjach OCA i EVRoaming Foundation przed użyciem w umowie (stan: 2026-10-20).
