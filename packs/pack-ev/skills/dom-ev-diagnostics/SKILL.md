---
name: dom-ev-diagnostics
description: Użyj przy diagnozie problemu sieci ładowania od objawu do przyczyny — ładowarka offline, sesja nie startuje, wisząca sesja, rozjazd kWh, Faulted; dowód z ramek.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy ładowarka traci połączenie, nie startuje sesji, sesja wisi bez CDR, energia różni się między licznikiem, CSMS i CDR albo złącze jest Faulted/Unavailable — zasada najpierw dowody (ramki OCPP i logi), drzewa decyzyjne per objaw, skrypt analizy logu ramek, raport diagnozy z osią czasu i dowodem oraz wpis odchylenia producenta. Nie do przebiegu sesji, jaki powinien być (dom-ev-session-lifecycle), katalogu komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x) ani projektu CSMS (dom-ev-cpms-architecture)."
  slowa: "ładowarka offline, ładowarka się rozłącza, zrywa połączenie, nie odpowiada, nie startuje ładowania, RemoteStart nie działa, wisząca sesja, sesja nie kończy się, brak CDR, rozjazd energii, 12 kWh a 12000, licznik malejący, Faulted, Unavailable, errorCode, vendorErrorCode, BootNotification Rejected, Pending, certyfikat TLS wygasł, handshake, analiza logów OCPP, diagnoza, root cause, charger offline, session not starting, stuck session, missing CDR, energy mismatch, troubleshooting, debug OCPP"
---

# Diagnoza sieci ładowania — od objawu do przyczyny z dowodem

Skill prowadzi od zgłoszenia („ładowarka nie działa”) do przyczyny, którą da się pokazać w konkretnej ramce lub
linii logu. Granice: jak sesja **powinna** wyglądać → `dom-ev-session-lifecycle`; budowa komunikatów i statusów →
`dom-ev-ocpp-16`, `dom-ev-ocpp-2x`; architektura i routing komend między instancjami CSMS → `dom-ev-cpms-architecture`;
nazwy pojęć → `dom-ev-glossary`.

Sieć: brak — skrypt działa lokalnie.

## Zasada: najpierw dowody, potem hipotezy
1. **Zbierz dowody, zanim cokolwiek zrestartujesz lub zmienisz:** surowe ramki OCPP z czasem i kierunkiem, log
   połączeń (WebSocket, TLS), logi CSMS z tego samego okna, odczyt licznika (jeśli sprawa dotyczy energii).
   Restart kasuje stan, który jest dowodem (bufor offline, kolejka, status).
2. **Ustal objaw jednym zdaniem** z czasem i stacją/złączem („stacja X, złącze 2, od 06:10 RemoteStart bez efektu”).
3. **Uruchom skrypt** na logu ramek (sekcja niżej) — daje ustalenia z numerami linii, od których zaczynasz czytanie.
4. **Wybierz drzewo** z tabeli, przejdź pytania, przy każdej hipotezie wskaż ramkę lub linię, która ją potwierdza
   albo obala. Hipoteza bez dowodu trafia do raportu jako **[założenie]**, nie jako przyczyna.
5. **Napisz raport** (format niżej). Naprawa po raporcie, a komendy zdalne na sprzęcie tylko z planem i akceptacją.

## Skrypt analizy logu
**Uruchom** go, zamiast czytać log ręcznie od początku:

```
python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py <log.jsonl | -> [--ocpp auto|1.6|2.0.1] [--timeout 30] [--skew 300] [--json]
```
- Wejście: JSON Lines, jedna ramka na linię: `{"ts": "<ISO 8601>", "cp": "<id stacji>", "dir": "cp>csms" | "csms>cp",
  "frame": [<ramka OCPP-J>]}`. `-` czyta ze standardowego wejścia. Jak przygotować log z bramy:
  `references/log-i-skrypt.md`.
- Wynik: tekst pogrupowany po stacji albo `--json`. Kod wyjścia 0 = przeanalizowano (także gdy są ustalenia),
  2 = błąd wywołania. Brak ustaleń nie dowodzi, że jest dobrze — dowodzi tylko, że log nie zawiera tych wzorców.
- Przed raportem **sprawdź 2–3 ustalenia ręcznie** w surowym logu pod podanymi numerami linii; skrypt wskazuje,
  gdzie patrzeć, nie zastępuje czytania.
- Ustalenia, waga i drzewo, od którego zacząć: `references/log-i-skrypt.md`.

| Kod ustalenia | Znaczy | Drzewo |
|---|---|---|
| `call-no-response` | CALL bez CALLRESULT/CALLERROR w czasie `--timeout` | 1, 2 |
| `callerror` | odpowiedź błędu protokołu | 1, 2 |
| `duplicate-message-id` | to samo `messageId` użyte ponownie | 1, 3 |
| `open-transaction` | transakcja bez zakończenia | 3 |
| `unknown-transaction` | zdarzenie dla transakcji bez startu | 3 |
| `seqno-gap`, `seqno-duplicate` | luka lub powtórka `seqNo` (2.x) | 3, 4 |
| `meter-decrease` | licznik energii maleje | 4 |
| `clock-skew` | czas ramki odbiega od czasu odbioru o więcej niż `--skew` | 3, 4 |
| `reboot` | ponowny BootNotification w trakcie logu | 1, 3 |
| `invalid-line` | linia logu nie jest poprawnym wpisem | log wejściowy |

## Którego drzewa użyć
| Objaw | Drzewo | Czytaj |
|---|---|---|
| ładowarka offline, zrywa połączenie, Boot Rejected/Pending, brak Heartbeatów | 1 | `references/drzewa-1-2.md` |
| sesja nie startuje: karta, aplikacja, RemoteStart | 2 | `references/drzewa-1-2.md` |
| brak CDR, sesja wisi, transakcja osierocona | 3 | `references/drzewa-3-5.md` |
| energia: licznik ≠ CSMS ≠ CDR, kWh vs Wh, licznik maleje | 4 | `references/drzewa-3-5.md` |
| `Faulted`, `Unavailable`, `errorCode`, zdalne komendy naprawcze | 5 | `references/drzewa-3-5.md` |

Objaw dotyczy kilku warstw naraz (np. roaming + OCPP) → rozbij go po warstwach i każdą diagnozuj osobno
(`core-skill-composition`, `dom-ev-charging`).

## Drzewa w skrócie (szczegóły w references)
| # | Pierwsze pytanie | Pierwszy dowód | Najczęstsze przyczyny |
|---|---|---|---|
| 1 | Czy jest otwarte połączenie WebSocket i czy był BootNotification? | handshake/upgrade w logu bramy; pierwsza ramka po połączeniu | sieć/DNS/APN, certyfikat TLS (termin, łańcuch, nazwa), zły podprotokół, `Rejected`/`Pending` w Boot, ładowarka nieznana w CSMS |
| 2 | Czy komenda/autoryzacja **dotarła** do ładowarki i co odpowiedziała? | CALL `RemoteStart…`/`Authorize` i odpowiedź z tym samym `messageId` | status złącza (nie `Available`/`Preparing`), `idTagInfo` ≠ `Accepted`, `Rejected` w CALLRESULT, brak odpowiedzi (połączenie „zombie”), lista lokalna/cache |
| 3 | Czy jest ramka kończąca transakcję? | brak `StopTransaction` / `TransactionEvent Ended` po ostatnim `MeterValues` | zasilanie/restart ładowarki, offline bez kolejkowania, odrzucenie zbuforowanej ramki, zamknięcie bez CDR w CSMS |
| 4 | Gdzie powstaje różnica: pomiar, przesył czy przeliczenie? | `meterStart`/`meterStop` albo `MeterValues` z jednostką, potem pole CDR | Wh vs kWh (×1000), zły `measurand`/`unit`, licznik malejący po wymianie, zegar, zaokrąglenia |
| 5 | Jaki `errorCode` i `vendorErrorCode` niesie `StatusNotification`? | ramka `StatusNotification` + log producenta | usterka sprzętu, ochrona (temperatura, prąd), zdalne `ChangeAvailability` zostawione w `Inoperative`, odchylenie producenta |

## Komendy zdalne — safety-critical
`Reset`, `UnlockConnector`, `ChangeAvailability`, `RemoteStopTransaction`, `UpdateFirmware`, `SetChargingProfile`
zmieniają stan sprzętu pod napięciem i z pojazdem. Zasady:
- **Plan i akceptacja człowieka przed wysłaniem** — co, do której stacji/złącza, skutek, jak cofnąć. Nie z poziomu
  „spróbuję, może pomoże”.
- Najpierw komendy odczytu (`GetConfiguration`, `TriggerMessage` dla `StatusNotification`/`MeterValues` w 1.6;
  odpowiedniki w 2.x → `dom-ev-ocpp-2x`) — nie zmieniają stanu.
- `UnlockConnector` przy aktywnej sesji lub pod obciążeniem to ryzyko dla ludzi i sprzętu — wymaga potwierdzenia,
  że ładowanie jest zakończone.
- Po komendzie zapisz ramkę i wynik w raporcie jako dowód; brak odpowiedzi to kolejne ustalenie, nie powód do powtórki.

## Przykład
Zgłoszenie: „stacja PL-A-007 od 06:10 nie startuje sesji z aplikacji, w logach same Heartbeaty”.
1. Log ramek z okna 05:50–07:30 → `ocpp_log_analyze.py log.jsonl --ocpp 1.6`.
2. Wynik (przykładowy): ustalenie `call-no-response` dla PL-A-007, 06:12:03 — `RemoteStartTransaction` (id "c41")
   bez odpowiedzi w 30 s, linia 212. Heartbeaty (linie 213–240) idą dalej.
3. Drzewo 2: komenda **wyszła** (linia 212), ładowarka **nie odpowiedziała**, a Heartbeaty działają → kanał żyje,
   obsługa komend po stronie ładowarki nie. Ostatni `StatusNotification` złącza 1: `Faulted` o 06:09 (linia 198),
   `errorCode` = `OtherError`, `vendorErrorCode` = `E-17` (wartości przykładowe).
4. Przyczyna z dowodem: złącze `Faulted` od 06:09 (linia 198); komenda bez odpowiedzi (linia 212). Przyczyna
   źródłowa błędu producenta — **[założenie]** do czasu odczytu `E-17` z dokumentacji producenta.
5. Działanie: `TriggerMessage` na `StatusNotification` (odczyt, bez planu), potem — z planem i akceptacją —
   decyzja o `Reset`. Wpis odchylenia: ładowarka nie odpowiada na CALL przy `Faulted`, a Heartbeat działa.

## Pułapki
- **Restart przed zebraniem dowodów** — znika bufor offline i stan złącza; pierwszy krok to log, nie `Reset`.
- **Heartbeat = „wszystko działa”** — Heartbeat potwierdza kanał i pętlę czasu, nie obsługę komend ani sprzętu.
- **Zegar jako dowód** — znaczniki z ładowarki bywają błędne (1970, drift); porównuj z czasem odbioru po stronie bramy.
- **Wniosek z braku ramki w *swoim* logu** — brama, balancer lub inna instancja mogły ją obsłużyć; sprawdź, czyj to log.
- **Jedna przyczyna za wcześnie** — rozjazd energii bywa złożeniem Wh/kWh **i** zaokrągleń; sprawdź każdy etap.
- **Naprawa na produkcji bez planu** — komendy zdalne to zmiana stanu sprzętu (sekcja wyżej).
- **Ukryte odchylenie producenta** — jeśli ładowarka łamie specyfikację, nie łatamy tego po cichu w jednym miejscu;
  zapisz w raporcie (`.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`).

## Checklista
- [ ] objaw w jednym zdaniu z czasem, stacją i złączem
- [ ] dowody zebrane przed jakąkolwiek zmianą (ramki, logi bramy, logi CSMS)
- [ ] skrypt uruchomiony; co najmniej część ustaleń potwierdzona ręcznie w surowym logu
- [ ] każda przyczyna z dowodem (plik:linia lub ramka z `messageId`), reszta oznaczona [założenie]
- [ ] raport: oś czasu, przyczyna, kroki naprawy, odchylenie producenta (jeśli jest)
- [ ] komendy zdalne tylko z planem i akceptacją człowieka

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/drzewa-1-2.md` | ładowarka offline/zrywa połączenie (TLS, Boot, Heartbeat) albo sesja nie startuje (autoryzacja, RemoteStart) |
| `references/drzewa-3-5.md` | brak CDR i wisząca sesja, rozjazd energii, statusy Faulted/Unavailable i komendy zdalne |
| `references/log-i-skrypt.md` | przygotowanie logu z bramy, opis ustaleń skryptu, wagi, czytanie wyniku |
| `references/raport-diagnozy.md` | format raportu, wpis odchylenia producenta, przykład wypełniony |

## Źródła
- `.claude/skills/dom-ev-charging/references/ocpp.md` i `cykl-sesji-ladowania.md` (import 2024–2025, włączony
  2026-09-27): ramki, Boot, statusy, offline, kolejność sesji.
- `.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md` oraz `status-i-transakcje.md` w tym samym katalogu (stan 2026-10-20).
- Wiedza ogólna autora skilla o diagnozie sieci i TLS — nazwy kodów i wartości spoza powyższych źródeł oznaczone
  **[do weryfikacji]** w references; sprawdź w specyfikacji OCA i dokumentacji producenta (stan: 2026-10-20).
