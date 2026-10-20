# Kontrole: tożsamość, uprawnienia, firmware, detekcja, OCPI, SBOM

Zmienne i komunikaty profili: `dom-ev-ocpp-2x`. Tu: decyzja, kolejność i organizacja. Liczby to ilustracje **[do weryfikacji]**.

## 1. Migracja profili OCPP
Pola w schematach: `SetNetworkProfile` ma `securityProfile` (liczba całkowita) wewnątrz profilu połączenia
(`ocpp-json-schemas`, SetNetworkProfileRequest.json, pobrane 2026-10-20).
| Krok | Działanie | Dowód ukończenia |
|---|---|---|
| 1 | Inwentarz: model, firmware, obsługiwany profil, SIM/sieć | tabela kohort w rejestrze assetów |
| 2 | Unikalne, losowe hasło na stację; magazyn sekretów po stronie CSMS | brak haseł wspólnych w audycie |
| 3 | TLS na bramie CSMS obok `ws://`; sprawdzenie łańcucha na stacji pilotażowej | stacja pilotażowa łączy się `wss://` |
| 4 | Przełączanie kohortami z rollbackiem (stary adres zostaje do końca fali) | kohorta stabilna przez uzgodniony okres |
| 5 | Profil 3 tam, gdzie model go obsługuje: wystawianie certyfikatów, rotacja, unieważnianie | rejestr certyfikatów z terminami |
| 6 | Wyłączenie `ws://` na bramie przy zerowym ruchu | licznik połączeń `ws://` = 0 |
Stacje, które nie obsługują TLS: izolowana sieć prywatna (APN/VPN), plan wymiany; wyjątek ma datę końca.
Zmiana adresu CSMS to operacja wysokiego ryzyka (fałszywy CSMS): `dom-ev-csms-migration`.

## 2. Rotacja haseł i certyfikatów
- Rotacja hasła stacji: okresowa i po każdym podejrzeniu; CSMS przyjmuje stare i nowe hasło przez okno przejściowe.
- Certyfikaty: monitoruj terminy ważności (alert z wyprzedzeniem, np. 60 i 30 dni — ilustracja), automatyczne odnowienie
  gdzie model pozwala; unieważnienie przy wymianie lub kradzieży sprzętu.
- Wymiana sprzętu: nowy numer seryjny = nowe poświadczenia, stare unieważnione (`dom-ev-asset-operations`).
- Wygaszenie stacji (decommissioning): usuń poświadczenia i certyfikaty przed odstawieniem.

## 3. Firmware
| Zasada | Szczegół |
|---|---|
| podpis | `UpdateFirmware` w 2.0.1 ma pole `firmware.signature` (Base64); stacja ma sprawdzać podpis i odrzucić niepodpisany obraz |
| źródło | adres pobierania (`location`) krótkożyjący, z kontrolą pobrań, bez haseł w ścieżce |
| fale | kohorta pilotażowa → 5 % → 25 % → reszta; kryterium przejścia: brak wzrostu `Faulted`/offline, udane sesje |
| rollback | poprzednia wersja dostępna; ochrona przed wymuszeniem cofnięcia do wersji z known-podatnością (polityka producenta) |
| klucze podpisu | po stronie producenta, w module sprzętowym; plan wymiany klucza |
| dowód | wersja po aktualizacji potwierdzona w `BootNotification`/raporcie, nie tylko status „Installed” |
CRA wymaga od producenta m.in. aktualizacji bezpieczeństwa i wsparcia (`references/regulacje-cyber.md`).

## 4. Uprawnienia i komendy masowe
Zasada: im szerszy zasięg komendy, tym więcej warunków. Rozdziel role (odczyt, wsparcie, operacje, administrator,
konto integracji). Dla `Reset`, `ChangeAvailability`, `SetChargingProfile`, `UpdateFirmware`, zmiany konfiguracji sieci:
- **próg masowości** (np. > kilkadziesiąt stacji lub > 5 % floty): drugi zatwierdzający, który nie jest autorem;
- **limit fali** i przerwa (rate limiting po stronie CSMS), jednoczesność ograniczona per lokacja i region;
- **powód i zgłoszenie** w dzienniku, niezmienialnym dla operatora;
- **tryb „zamrożenia”**: jeden przełącznik wstrzymuje wszystkie komendy masowe (używany w incydencie);
- **MFA** i sesje krótkie dla konsoli; konta usług z minimalnym zakresem; przegląd uprawnień co kwartał (ilustracja).
Komendy od eMSP (OCPI `Commands`) przechodzą tę samą autoryzację: partner może zlecić start/stop tylko własnych tokenów.

## 5. Logowanie i detekcja
Loguj: uwierzytelnienia stacji (sukces i porażka, adres), zmiany konfiguracji, komendy zdalne z autorem, firmware,
zmiany uprawnień, dostęp do danych osobowych. Dziennik poza zasięgiem operatora (zapis jednokierunkowy).
| Reguła | Próg (ilustracja) | Reakcja |
|---|---|---|
| ten sam `chargePointId` z dwóch adresów | każdy przypadek | zachowaj aktywne połączenie, blokuj nowe, alarm |
| komendy masowe z jednego konta | > próg w oknie 10 min | automatyczne wstrzymanie, alarm |
| zmiana modelu/numeru seryjnego dla znanego EVSE | każdy przypadek | `Pending`, weryfikacja człowieka |
| sesje bez przyrostu energii | > N % sesji lokacji | alert do O&M i bezpieczeństwa |
| token w dwóch krajach | w odstępie krótszym niż dojazd | blokada tokenu, kontakt z eMSP |
| nieudane uwierzytelnienia stacji | seria z jednego adresu | limit i czasowa blokada adresu |
| nagły wzrost ruchu na bramie | ponad ustalony poziom | ochrona bramy (limit połączeń), nie uznawaj za awarię |
Analiza logów OCPP: `.claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py`. Detekcja nie zastępuje reakcji:
każda reguła ma właściciela i runbook.

## 6. OCPI
- Token credentials (A, B, C) to sekret wymieniany poza OCPI; **osobny token na partnera**, przechowywany w sejfie sekretów.
- Rotacja: `PUT` na `credentials` z nowym tokenem (cykl np. miesięczny wg `dom-ev-ocpi`), **natychmiast** po wycieku.
- TLS obowiązkowy; weryfikacja certyfikatu partnera; allowlista adresów, gdzie umowa pozwala.
- Zakres modułów i danych zgodny z umową (np. CDR tylko własne); minimalizacja danych osobowych w CDR i sesjach.
- Przy wycieku: unieważnij token, powiadom partnera, przejrzyj żądania z tego tokenu, oceń wyciek CDR (RODO).

## 7. Podatności i SBOM
- Inwentarz komponentów (SBOM) dla firmware i CSMS: wersje bibliotek, licencje; aktualizowany przy każdym wydaniu.
- Proces przyjmowania zgłoszeń (adres do zgłoszeń, polityka ujawniania), ocena, poprawka, informowanie klientów (CPO).
- Skan zależności w CI; wersje ze znaną podatnością blokują wydanie. Łańcuch dostaw: wymagania wobec producentów
  ładowarek i dostawców CSMS w umowie (czas reakcji na podatności, SBOM, wsparcie).
- CRA: zestawienie komponentów jest elementem dokumentacji (Aneks I część II), zgłoszenie aktywnie wykorzystywanej luki 24 h.

## 8. Kolejność wdrożeń (zwrot z wysiłku)
1. Unikalne hasła i TLS; zamrożenie i próg komend masowych; MFA w konsoli.
2. Reguły detekcji: duplikat serialu, komendy masowe, sesje bez energii, klon tokenu.
3. Rotacja tokenów OCPI i sejf sekretów; dziennik komend niezmienialny.
4. Podpisany firmware i fale; SBOM; proces podatności.
5. Profil 3 i PKI; ćwiczenia incydentu z OSD i partnerami.

## Źródła
- `ocpp-json-schemas`: SetNetworkProfileRequest.json, UpdateFirmwareRequest.json (`signature`), `.claude/knowledge/ocpp-json-schemas/doc.txt:L3614-3653` i `L4046-4085`, github.com/mobilityhouse/ocpp, pobrane 2026-10-20.
- `eu-cra` Aneks I, `.claude/knowledge/eu-cra/doc.txt`, pobrane 2026-10-20.
- Skille fabryki: `dom-ev-ocpp-2x` (profile), `dom-ev-ocpi` (rotacja credentials), `dom-ev-asset-operations` (komendy), stan 2026-10-20.
- Progi, okna, odsetki fal: wiedza ogólna, ilustracje [do weryfikacji].
