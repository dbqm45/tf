# Przełączenie stacji na nowy CSMS

Spis treści: 1. OCPP 1.6 · 2. OCPP 2.0.1 · 3. Profil bezpieczeństwa i certyfikaty · 4. Fale · 5. Rollback · 6. Stacje bez zdalnej zmiany

## 1. OCPP 1.6 — zmiana adresu
- `ChangeConfiguration`: pola `key` (do 50 znaków) i `value` (do 500 znaków), oba wymagane. Odpowiedź niesie status
  przyjęcia (m.in. wymagany restart i klucz nieznany; dokładne wartości sprawdź w specyfikacji [do weryfikacji]).
- **Standard 1.6 nie definiuje klucza z adresem CSMS** [do weryfikacji w specyfikacji i w `GetConfiguration` modelu]:
  adres jest zwykle ustawiany lokalnie (WWW, aplikacja serwisowa, plik) albo kluczem producenta. Zbierz od każdego producenta:
  nazwę klucza, format (z podprotokołem i ścieżką `chargePointId`), czy zmiana wymaga `Reset` i czy klucz jest `readonly`.
- Poświadczenia Basic Auth i klucz autoryzacji (profile bezpieczeństwa z dodatku Security Whitepaper, opcjonalnego):
  klucz konfiguracji `AuthorizationKey` i `SecurityProfile` z dodatku [do weryfikacji]; po stronie nowego CSMS hasło musi
  być znane przed przełączeniem. Zmiana profilu bezpieczeństwa to osobna zmiana — nie łącz jej z przełączeniem adresu.
- `Reset` 1.6: `type` = `Hard` albo `Soft` (wymagane). Soft zwykle wystarcza do ponownego połączenia; model może
  wymagać Hard [do weryfikacji w karcie typu].
- Ryzyko: błędny adres zapisany na stacji bez zdalnej korekty = stacja traci łączność. Dlatego pierwsze testy w lab i na
  stacjach z dostępem lokalnym; każdy producent najpierw pilotażem.

## 2. OCPP 2.0.1 — profile sieciowe
Kolejność, która pozwala wrócić:
1. `GetBaseReport` / `GetVariables`: stan przed zmianą, istniejące sloty profili i bieżący priorytet.
2. `SetNetworkProfile` z **nowym slotem** (`configurationSlot`) — nie nadpisuj slotu używanego dziś.
3. Pola `connectionData` (`NetworkConnectionProfileType`), wymagane: `ocppVersion` (`OCPP12`, `OCPP15`, `OCPP16`, `OCPP20`),
   `ocppTransport` (`JSON` / `SOAP`), `ocppCsmsUrl` (≤512 znaków), `messageTimeout` (sekundy; schemat podpowiada 30 s
   jako punkt wyjścia), `securityProfile` (liczba), `ocppInterface` (`Wired0`…`Wireless3`). Opcjonalne: `apn`
   (`apn`, `apnUserName`, `apnPassword`, `simPin`, `apnAuthentication`, `preferredNetwork`, `useOnlyPreferredNetwork`)
   i `vpn` (`server`, `user`, `group`, `password`, `key`, `type`). Wartość `OCPP20` w `ocppVersion` oznacza 2.0.x;
   rozróżnienie 2.0.1 / 2.1 przez podprotokół [do weryfikacji].
4. `SetVariables`: pola `component`, `variable`, `attributeValue`, opcjonalnie `attributeType` (domyślnie `Actual`).
   Zmienna priorytetu profili (`NetworkConfigurationPriority` w komponencie komunikacyjnym) przyjmuje listę slotów
   w kolejności prób; **dokładne nazwy i format listy: Device Model wg specyfikacji OCA Part 2 [do weryfikacji]**.
   Sprawdź w odpowiedzi `attributeStatus` per zmienna: `Accepted`, `Rejected`, `UnknownComponent`, `UnknownVariable`, `NotSupportedAttributeType`, `RebootRequired` (schemat SetVariablesResponse 2.0.1). `SetNetworkProfile` odpowiada `Accepted`, `Rejected` albo `Failed`; w 1.6 `ChangeConfiguration` — `Accepted`, `Rejected`, `RebootRequired`, `NotSupported`.
5. `Reset` (2.0.1): pole `type` (wartości widoczne w schemacie: `Immediate`, `OnIdle`), opcjonalne `evseId`. Do przełączenia
   floty używaj `OnIdle` — czeka na koniec sesji, więc nie przerywa ładowania.
6. Weryfikacja po stronie nowego CSMS: `BootNotification` ze znaną stacją, `reason` zgodny z oczekiwanym (np. po `Reset`),
   `Heartbeat`, `StatusNotification` wszystkich EVSE.

Priorytet z nowym slotem **na pierwszym miejscu, stary na drugim**: stacja próbuje nowego, a gdy się nie połączy —
wraca na stary. Zachowanie przy liczbie prób i przerwach zależy od modelu — przetestuj w pilocie, że rzeczywiście wraca.

## 3. Profil bezpieczeństwa i certyfikaty po stronie nowego CSMS
- Profil nie może się obniżyć w trakcie migracji (z 2 do 1 — nie). Podniesienie (np. 2 → 3) to osobna zmiana po migracji.
- Profil 2: nowy CSMS ma certyfikat serwera, któremu stacja ufa. Jeśli stacje ufają **tylko** CA poprzedniego dostawcy,
  trzeba najpierw doinstalować zaufane CA (2.0.1: `InstallCertificate`) lub certyfikat serwera podpisać tą samą CA [do weryfikacji
  możliwości danego modelu]. To najczęstszy powód „stacja łączy się, ale handshake TLS pada”.
- Profil 3 (mTLS): certyfikaty klienta stacji wydane przez CA starego dostawcy; nowy CSMS musi je zaufać albo stacje
  dostają nowe (`SignCertificate` → `CertificateSigned`). Wystawianie i rotacja: PKI operatora.
- Hasła Basic Auth: nowe hasło per stacja wygenerowane i zapisane w magazynie sekretów; nie wysyłaj ich w e-mailu.
- Szczegóły profili: **dom-ev-ocpp-2x**; PKI dla Plug & Charge: **dom-ev-iso15118**.
- Sieć: whitelista adresów nowego CSMS w firewallach lokalizacji i APN-ach, port, DNS (stacje często trzymają nazwę, nie IP).

## 4. Fale
| Etap | Skład | Kryterium przejścia do następnego |
|---|---|---|
| Laboratorium | stacje testowe każdego modelu | pełny cykl; rollback działa |
| Pilot produkcyjny | 1–3 stacje na model, o niskim ruchu, z dostępem serwisu | 48–72 h bez nieoczekiwanych odłączeń [liczba robocza] |
| Fala 1 | ~5% floty modelu | 100% stacji `Accepted`; sesje testowe i prawdziwe bez błędów; OCPI bez zmian |
| Fale kolejne | po modelu → firmware → lokalizacji/regionie, rosnące | jak wyżej + brak wzrostu zgłoszeń od kierowców |
| Ogon | stacje trudne | wizyty serwisu |

Przed falą: okno serwisowe uzgodnione z site hostem i dyżurem; lista stacji z aktualnym statusem; brak aktywnych sesji
i rezerwacji (w 1.6 `ReserveNow`/`CancelReservation`; zdalne starty z kolejki anuluj). W trakcie: jedna osoba steruje,
druga obserwuje. Po fali: zatrzymaj kolejną, jeśli odsetek stacji niepołączonych po 30 min przekracza ustalony próg
[próg do ustalenia z operacjami; przykład: 2%].

Kryteria przejścia fali zapisz **przed** falą: odsetek `Accepted`, czas do pierwszego `Heartbeat`, sesja testowa, zgodność
liczników (`MeterValues` rosną), brak `Faulted` wywołanych przełączeniem, brak zgłoszeń o dublach sesji.

## 5. Rollback
- Wyzwalacze: stacje nie łączą się w limicie czasu, błędy autoryzacji, brak `MeterValues`, rozbieżność CDR, awaria OCPI.
- 2.0.1: przywróć priorytet (`SetVariables`) ze starym slotem na pierwszym miejscu → `Reset OnIdle`. Stary CSMS musi nadal
  przyjmować te stacje (nie wyłączaj go i nie usuwaj stacji z niego w trakcie fali).
- 1.6: powrót wymaga tego samego klucza producenta ze starym adresem, więc **zachowaj stare wartości z `GetConfiguration`** przed zmianą.
- Rollback po wystawieniu CDR w nowym systemie wymaga ustalenia, do którego systemu należy każda sesja (granica = czas
  `Ended` albo przełączenia). Sesji nie dzielisz.
- Tylko jedna strona publikuje do eMSP w danym czasie (references/ciaglosc-i-plan.md).

## 6. Stacje, których nie da się przełączyć zdalnie
Lista z inwentarza: brak klucza adresu, stary firmware bez `SetNetworkProfile`, brak łączności (SIM), uszkodzone, zamknięte
lokalizacje. Dla każdej: przyczyna, wymagana wizyta (lokalna konfiguracja, aktualizacja firmware, wymiana SIM), termin
i kto płaci. Gdy ogon przekracza ~5% floty, rozważ **tymczasowy most**: stary CSMS w trybie przekazywania (proxy OCPP) do
nowego — to dodatkowy komponent z własnym ryzykiem [wariant opcjonalny, ocena przy projekcie]. Stacje wycofywane w ciągu
najbliższego roku: nie wydawaj na nie wizyt, wycofaj je (status `decommissioned`; w OCPI `REMOVED`, dom-ev-ocpi).
