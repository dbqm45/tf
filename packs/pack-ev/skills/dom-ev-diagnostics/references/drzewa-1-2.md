# Drzewa 1–2: połączenie i start sesji

Fakty z `ocpp.md` (dom-ev-charging): cykl połączenia (DNS → TCP → TLS → upgrade WebSocket → BootNotification),
`Accepted`/`Pending`/`Rejected`, Heartbeat co `interval`, reconnect z backoffem, jedno niezakończone CALL naraz,
timeout ~30 s. Pozostałe punkty to wiedza ogólna — **[do weryfikacji]** u producenta lub w specyfikacji OCA.

## Drzewo 1 — ładowarka offline albo zrywa połączenie

### Pytania
1. Czy stacja **kiedykolwiek** połączyła się z tym CSMS (nowa instalacja), czy działała i przestała (zmiana)?
2. Od kiedy i **co zmieniono** w tym czasie: certyfikat, adres/DNS, firmware, konfiguracja sieci, SIM/APN?
3. Dotyczy jednej stacji, grupy (ta sama lokalizacja, ten sam operator sieci, ten sam model) czy wszystkich?
4. Połączenie nie powstaje wcale, powstaje i pada, czy jest „żywe”, ale CSMS nie widzi ruchu?

### Co sprawdzić w logu (kolejno wg warstw cyklu połączenia)
| Warstwa | Dowód | Brak / błąd oznacza |
|---|---|---|
| DNS/TCP | log bramy: próby połączenia ze stacji, źródłowy IP | sieć, APN, firewall, zły adres w ładowarce |
| TLS | log bramy/proxy: błąd handshake, komunikat o certyfikacie | certyfikat serwera lub klienta (patrz niżej) |
| Upgrade WebSocket | odpowiedź na upgrade (kod HTTP, nagłówek `Sec-WebSocket-Protocol`) | zły podprotokół (`ocpp1.6` vs `ocpp2.0.1`), błędna ścieżka/id stacji, odrzucone Basic Auth |
| BootNotification | pierwsza ramka stacji i odpowiedź (`status`, `interval`) | `Rejected`, `Pending`, brak odpowiedzi |
| Heartbeat | odstępy między ramkami względem `interval` | cisza = połączenie martwe lub ładowarka zawieszona |
| Rozłączenia | czas i kod zamknięcia WebSocket, częstość | cykliczne (co N min) → timeout bezczynności po drodze lub wygasanie sesji NAT |

### Typowe przyczyny
- **Certyfikat TLS** (profile 2 i 3 — `dom-ev-ocpp-2x`; dla 1.6 Security Whitepaper — `dom-ev-ocpp-16`): wygasły
  certyfikat serwera lub klienta, niepełny łańcuch, nazwa hosta niezgodna z certyfikatem, CA nieobecne w magazynie
  ładowarki, **zły zegar ładowarki** (certyfikat „jeszcze nieważny” albo „już wygasły”). Zegar sprawdź pierwszy —
  ładowarka bez RTC po zaniku zasilania często startuje ze starą datą (`.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`).
- **Podprotokół:** ładowarka zgłasza `ocpp1.6`, serwer oczekuje `ocpp2.0.1` albo odwrotnie → połączenie odrzucone
  lub zamknięte przy upgrade.
- **BootNotification `Rejected`:** stacja nieznana w CSMS (brak rejestracji, literówka w id, zmieniony numer seryjny).
  Stacja ponawia Boot po `interval` — w logu zobaczysz powtarzające się CALL i `Rejected`.
- **BootNotification `Pending`:** CSMS jeszcze nie przyjął stacji (konfiguruje ją). Utknięcie w `Pending` = proces
  po stronie CSMS się nie zakończył. Co wolno stacji w `Pending` — według specyfikacji **[do weryfikacji]**.
- **Brak Heartbeatów przy otwartym połączeniu:** ładowarka zawieszona, zbyt długi `interval`, albo sieć „połyka”
  ruch (połączenie połowicznie otwarte). Odróżnij po tym, czy CSMS widzi jakąkolwiek ramkę po stronie `cp>csms`.
- **Zrywa się cyklicznie:** idle timeout w balancerze/proxy krótszy niż `interval`; reconnect z `reboot`
  (ponowny BootNotification) — skrypt zgłosi `reboot`.
- **Awaria po naszej stronie:** CSMS/brama zrestartowana, limit połączeń, wyczerpane zasoby — wtedy offline dotyczy
  wielu stacji jednocześnie (pytanie 3).

### Działanie
- Przyczyna po stronie sieci/certyfikatu: napraw źródło (rotacja certyfikatu, korekta adresu) według zasad
  rotacja przed wygaśnięciem i bezpieczne przechowywanie kluczy; weryfikuj powrotem BootNotification `Accepted` i Heartbeatów.
- Zegar: popraw przez Heartbeat/Boot `currentTime`; trwały błąd zegara → odchylenie producenta.
- Komendy zdalne (np. `Reset`) tylko z planem i akceptacją (sekcja w SKILL.md).

## Drzewo 2 — sesja nie startuje

### Pytania
1. **Jaki wyzwalacz:** karta/tag (`Authorize`), aplikacja (`RemoteStart…`), Plug & Charge, terminal płatniczy?
2. Czy stacja jest online (drzewo 1) i jaki jest **ostatni status złącza**?
3. Czy dotyczy jednego tokena/kierowcy, jednego złącza, całej stacji czy całej sieci?
4. Czy komenda lub autoryzacja **doszła** do stacji i co **odpowiedziała**?

### Co sprawdzić w logu
| Wyzwalacz | Ramka-dowód | Interpretacja |
|---|---|---|
| karta/tag | CALL `Authorize` (`idTag`) i odpowiedź `idTagInfo.status` | inny niż `Accepted` (`Blocked`, `Expired`, `Invalid`, `ConcurrentTx` — pełna lista **[do weryfikacji]**) = odmowa autoryzacji |
| karta/tag, brak `Authorize` w logu | log ładowarki; lista lokalna (`SendLocalList`) i cache | stacja zdecydowała lokalnie albo czytnik nie odczytał karty — sprawdź wersję listy lokalnej |
| aplikacja | CALL `RemoteStartTransaction` (1.6) / `RequestStartTransaction` (2.x) i odpowiedź | `Rejected` w CALLRESULT = ładowarka odmówiła; CALLERROR = ramka nieobsłużona; **brak odpowiedzi** = `call-no-response` |
| aplikacja, `Accepted` | czy po nim jest `StartTransaction` / `TransactionEvent Started` | `Accepted` to przyjęcie komendy, nie start energii; brak startu = kabel niewpięty, zły status, zablokowane złącze |
| każdy | ostatni `StatusNotification` złącza | start możliwy zwykle ze stanu `Available`/`Preparing`; `Faulted`, `Unavailable`, `Reserved` (inny `idTag`) blokują |

### Typowe przyczyny
- **Status złącza:** `Faulted`/`Unavailable` (w tym zostawione `ChangeAvailability`) → drzewo 5. `Reserved` dla innego tagu.
  Kabel niewpięty przy `RemoteStart` bez wymuszonego startu (zachowanie zależy od konfiguracji **[do weryfikacji]**).
- **Autoryzacja:** token nieznany, wygasły, zablokowany; rozjazd synchronizacji tokenów z eMSP (moduł OCPI Tokens
  — `dom-ev-charging`); lista lokalna nieaktualna po powrocie z offline; `ConcurrentTx` — token ma już aktywną sesję
  (często osierocona, drzewo 3).
- **RemoteStart `Rejected`:** złącze zajęte transakcją, zły `connectorId`, nieobsługiwany parametr, profil mocy
  niedozwolony.
- **Brak odpowiedzi na komendę przy żywych Heartbeatach:** ładowarka przetwarza ramki wolno albo wcale (zawieszona
  obsługa komend), złącze w `Faulted`, kolejka komend po stronie ładowarki zablokowana jednym niezakończonym CALL.
  Sprawdź, czy **inny** CALL wysłany przed komendą nie czeka na odpowiedź (jedno niezakończone CALL naraz).
- **Komenda nie wyszła z CSMS:** w logu `csms>cp` nie ma CALL — problem w routingu komend (`dom-ev-cpms-architecture`),
  nie w ładowarce. Pierwsze rozróżnienie: **czy ramka wyszła**.
- **Plug & Charge:** certyfikat kontraktu, łańcuch PKI — `dom-ev-charging/references/iso-15118.md`.

### Działanie
- Odmowa autoryzacji: napraw dane (token, lista), nie obchodź autoryzacji.
- Komenda bez odpowiedzi: najpierw odczyt (`TriggerMessage` dla `StatusNotification`), potem decyzja o resecie z planem.
- Zapisz ramki (CALL, odpowiedź lub jej brak, ostatni status) w raporcie z `messageId`.
