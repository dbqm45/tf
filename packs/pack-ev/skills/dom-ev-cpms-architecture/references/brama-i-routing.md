# Brama OCPP, rejestr połączeń i reconnect storm

Wzorce poniżej to wiedza ogólna o systemach rozproszonych zastosowana do OCPP; źródło domenowe
(`.claude/skills/dom-ev-charging/references/ocpp.md`) nie opisuje takich wzorców. Liczby: [do weryfikacji].

## 1. Rejestr połączeń
| Zdarzenie | Działanie w rejestrze |
|---|---|
| handshake udany (po uwierzytelnieniu) | zapis `stationId → {węzeł, wersja, connectionId, od kiedy}`; jeśli wpis istnieje u innego węzła — zleć mu zamknięcie starego gniazda |
| każdy ruch lub Heartbeat | odnowienie TTL |
| zamknięcie gniazda | usunięcie wpisu **tylko jeśli** `connectionId` zgadza się (stare gniazdo nie kasuje wpisu nowego) |
| awaria węzła | wpisy wygasają po TTL; do tego czasu komendy kończą się timeoutem — to akceptowana luka, opisz ją w ADR |

Rejestr musi być wspólny dla węzłów (pamięć współdzielona lub magazyn klucz-wartość z TTL — wybór produktu poza tym skillem).
Czytanie rejestru nie może być jedyną ścieżką: komenda na szynie z kluczem `stationId` ma dotrzeć do właściciela także
gdy wpis właśnie się zmienił (węzeł odrzuca komendę dla stacji, której nie trzyma, i zwraca ją z wynikiem „nie moje”).

## 2. Kontrakt komendy CSMS→stacja
| Pole | Znaczenie |
|---|---|
| `commandId` | klucz korelacji; trafia do logów i metryk |
| `stationId`, `tenantId` | adresat i najemca (sprawdzane przez bramę względem połączenia) |
| `action` + payload | nazwa komunikatu OCPP w oryginale, treść: dom-ev-ocpp-16 / dom-ev-ocpp-2x |
| `expiresAt` | po terminie komenda nie jest wysyłana (RemoteStart sprzed minut nie może ruszyć ładowania) |
| wynik | `delivered`/`accepted`/`rejected` (odpowiedź stacji), `callError`, `offline`, `expired`, `timeout` |

`RemoteStart` zaakceptowany przez stację to jeszcze nie sesja — sesję potwierdza dopiero zdarzenie transakcji
(dom-ev-session-lifecycle). Ponowienie komendy po `timeout` wymaga ostrożności: stacja mogła ją wykonać.

## 3. Martwe połączenia
- Źródła sygnału: brak ruchu ponad wielokrotność interwału Heartbeat (interwał zwraca CSMS w BootNotification), brak pong
  na ping WebSocket, błąd zapisu do gniazda.
- Po wykryciu: zamknij gniazdo, wyczyść wpis, wyemituj zdarzenie `StationDisconnected`; sesje otwarte NIE są kończone
  automatycznie — stacja nadal może ładować offline i odeśle transakcję po powrocie (ocpp.md, sekcja 12).
- Interwał zbyt krótki = obciążenie przy wielu tysiącach stacji; zbyt długi = późne wykrycie. Wartość: [do weryfikacji], mierz.

## 4. Reconnect storm krok po kroku
1. **Przed wdrożeniem:** zaplanuj drenaż — węzeł wstrzymuje przyjmowanie nowych połączeń i zamyka istniejące partiami
   w oknie czasu; kolejne węzły restartuj po ustabilizowaniu się poprzednich.
2. **W trakcie:** monitoruj tempo handshake’ów; limit nowych połączeń na sekundę per węzeł, nadmiar → odrzucenie
   (stacja ponowi z backoffem).
3. **BootNotification:** pod obciążeniem odpowiadaj `Pending` z `interval` zamiast ciężkiej rejestracji; stację
   wprowadzaj etapami (konfiguracja, zaległe dane). `Rejected` rezerwuj dla stacji nieznanych lub zablokowanych.
4. **Zaległości offline:** po powrocie stacja odsyła zbuforowane transakcje i wartości liczników. Wpuszczaj je przez
   kolejkę z ograniczoną współbieżnością i idempotencją, nie bezpośrednio do bazy.
5. **Po fakcie:** test „wszystkie stacje wracają” w środowisku testowym (symulatory flot — ocpp.md, sekcja 11) przed
   zmianą bramy; wynik zapisz jako warunek wydania.
6. **Firmware:** zachowanie ponowień (backoff, jitter, limity) różni się u producentów — [do weryfikacji] per model, nie zakładaj.

## 5. Walidacja i CALLERROR
Brama waliduje ramkę względem schematu **właściwej wersji** (podprotokół z handshake). Ramka niepoprawna →
CALLERROR z kodem błędu (kody: dom-ev-ocpp-16, dom-ev-ocpp-2x), zdarzenie dalej nie idzie, a licznik CALLERROR
(po producencie i akcji) trafia do metryk. Polityka „tolerancyjnego czytelnika” dla znanych odchyleń producentów
żyje w adapterze, jawnie, z listą wyjątków — nie jako ciche luzowanie schematu.

## 6. Źródła
`.claude/skills/dom-ev-charging/references/ocpp.md` (sekcje 3, 11, 12); wiedza ogólna inżynierii systemów rozproszonych — oznaczona w tekście.
