# Log ramek i skrypt ocpp_log_analyze.py

## Przygotowanie logu z bramy
Skrypt czyta **surowe ramki OCPP-J z czasem i kierunkiem**. Brama WebSocket (lub proxy przed CSMS) powinna
zapisywać każdą ramkę przed jej interpretacją: moment odbioru/wysłania, identyfikator stacji, kierunek i całą ramkę.
Format wejścia — JSON Lines, jedna ramka na linię:

```
{"ts": "2026-10-20T06:12:03Z", "cp": "PL-A-007", "dir": "csms>cp", "frame": [2, "c41", "RemoteStartTransaction", {"idTag": "ABC123"}]}
{"ts": "2026-10-20T06:12:04Z", "cp": "PL-A-007", "dir": "cp>csms", "frame": [2, "h9", "Heartbeat", {}]}
```
- `ts` — ISO 8601; zapisuj czas **odbioru po stronie bramy** (zegar ładowarki bywa błędny).
- `cp` — id stacji z adresu połączenia; `dir` — `cp>csms` (od stacji) lub `csms>cp` (do stacji).
- `frame` — ramka bez zmian: `[2, id, akcja, payload]`, `[3, id, payload]` lub `[4, id, kod, opis, szczegóły]`.
- Zapis zawiera dane osobowe i identyfikatory (np. `idTag`) — przechowuj i udostępniaj zgodnie z RODO (minimalny zakres, ograniczony dostęp, retencja);
  nie wklejaj logu produkcyjnego do narzędzi zewnętrznych bez zgody.
- Gdy brama zapisuje inny format, przekształć go do powyższego prostym skryptem; nie zmieniaj treści ramek.

## Uruchomienie
```
python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py <log.jsonl | -> [--ocpp auto|1.6|2.0.1] [--timeout 30] [--skew 300] [--json]
```
| Opcja | Znaczenie |
|---|---|
| `<log.jsonl>` / `-` | plik albo standardowe wejście |
| `--ocpp` | wersja protokołu; `auto` rozpoznaje po akcjach w ramkach (ustaw jawnie, gdy log jest krótki) |
| `--timeout` | sekundy, po których CALL bez odpowiedzi jest ustaleniem `call-no-response` (domyślnie 30) |
| `--skew` | sekundy dopuszczalnej różnicy czasu ramki i odbioru dla `clock-skew` (domyślnie 300) |
| `--json` | wynik maszynowy zamiast tekstu |

Kod wyjścia: **0** — log przeanalizowano (także z ustaleniami); **2** — błąd wywołania (np. brak pliku, zła opcja).
Sieć: brak — skrypt działa lokalnie.

## Ustalenia
Każde ustalenie ma wagę, stację, czas, opis i numery linii logu jako dowód. Wagi i kolejność czytania:

| Kod | Co wykrywa | Co zwykle znaczy | Drzewo |
|---|---|---|---|
| `call-no-response` | CALL bez odpowiedzi w czasie `--timeout` | komenda nieobsłużona, zerwane połączenie, zawieszona stacja | 1, 2 |
| `callerror` | CALLERROR (kod z ramki) | ramka niepoprawna lub nieobsłużona; odmowa biznesowa to CALLRESULT, nie to | 1, 2, 3 |
| `duplicate-message-id` | powtórzone `messageId` od tego samego nadawcy | retry po zerwaniu albo błąd generatora id; ryzyko podwójnego skutku | 1, 3 |
| `open-transaction` | transakcja bez końca w oknie logu | wisząca sesja (okno logu może być po prostu za krótkie) | 3 |
| `unknown-transaction` | zdarzenie dla transakcji bez startu w logu | zgubiony start lub okno logu zaczyna się w środku sesji | 3 |
| `seqno-gap` | luka w `seqNo` w obrębie transakcji (2.x) | zdarzenie zgubione lub opóźnione | 3, 4 |
| `seqno-duplicate` | powtórzony `seqNo` | retransmisja, jeśli treść identyczna; konflikt, jeśli różna | 3 |
| `meter-decrease` | wartość licznika energii maleje | wymiana/reset licznika, błąd odczytu | 4 |
| `clock-skew` | czas ramki vs odbioru > `--skew` | zły zegar stacji lub zbuforowane ramki | 3, 4 |
| `reboot` | ponowny BootNotification | restart stacji, utrata zasilania, flapowanie | 1, 3 |
| `invalid-line` | linia nie jest poprawnym wpisem | uszkodzony zapis logu; zgłoś, ile linii pominięto | log |

Dokładne progi wag odczytaj z wyniku skryptu (`--json`) — nie zakładaj ich z pamięci.

## Czytanie wyniku
1. Zacznij od stacji, której dotyczy zgłoszenie; reszta to kontekst (czy problem jest szerszy).
2. Ułóż ustalenia na osi czasu (czas + numer linii) i otwórz surowy log w tych liniach — **dowód w raporcie to
   linia logu**, nie sama etykieta skryptu.
3. Szukaj **pierwszego** ustalenia w łańcuchu (np. `reboot` → `open-transaction` → `unknown-transaction`), nie
   ostatniego skutku.
4. Brak ustaleń przy realnym objawie: okno logu za krótkie, objaw w innej warstwie (OCPI, aplikacja, sprzęt) albo
   brama nie zapisała ramek — wpisz to do raportu jako ograniczenie, nie jako „wszystko w porządku”.

## Ograniczenia
- Skrypt nie zna konfiguracji stacji ani wymagań producenta; nie ocenia treści payloadu poza wymienionymi wzorcami.
- Ustalenia zależą od okna logu (transakcja zaczęta przed oknem wygląda jak `unknown-transaction`).
- Przy `--ocpp auto` wersja jest rozpoznawana osobno dla każdej stacji, po pierwszej akcji transakcyjnej (`StartTransaction`/`StopTransaction` → 1.6, `TransactionEvent` → 2.0.1); stacja bez transakcji w logu ma wersję „nieznana”.
