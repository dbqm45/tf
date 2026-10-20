# Cykl życia i publikacja — przejścia, EVSE ID, wymiana, repowering, decommissioning

Spis: 1. Skutki w CSMS · 2. Publikacja OCPI · 3. Dane NEVI i EIPA · 4. EVSE ID i `uid` · 5. Wymiana sprzętu · 6. Wyjątki ·
7. Repowering · 8. Decommissioning.

## 1. Skutki stanu w CSMS
| Stan | Połączenia stacji | Komendy i alarmy |
|---|---|---|
| `PLANNED`, `UNDER_CONSTRUCTION` | brak oczekiwanych | brak alarmów offline |
| `IN_STOCK` | niedozwolone; `BootNotification` → `Rejected` (lub `Pending`) i alarm bezpieczeństwa | brak |
| `COMMISSIONING` | `Pending` → `Accepted` po karcie (`dom-ev-charger-onboarding`) | alarmy offline wyciszone do końca odbioru |
| `OPERATIONAL` | `Accepted` | pełny monitoring, SLA liczy się od tego stanu |
| `MAINTENANCE` | `Accepted` | alarmy wyciszone do terminu zlecenia; po terminie eskalacja |
| `PAUSED` | `Accepted`; `ChangeAvailability` `Inoperative` | alarmy zwykłe, komendy startu odrzucane przez CSMS |
| `OBSOLETE` | jak `OPERATIONAL` | licznik kosztów, plan wymiany |
| `DECOMMISSIONED` | `Rejected` | stacja, która się zgłasza, to incydent (kradzież, błąd demontażu) |

## 2. Publikacja w OCPI (Locations)
- `status` EVSE ma wartości `AVAILABLE`, `BLOCKED`, `CHARGING`, `INOPERATIVE`, `OUTOFORDER`, `PLANNED`, `REMOVED`, `RESERVED`,
  `UNKNOWN`. `PLANNED` = planowane, wkrótce w użyciu; `INOPERATIVE` = jeszcze nieaktywne albo czasowo niedostępne, ale
  nie zepsute; `OUTOFORDER` = awaria; `REMOVED` = wycofane. (OCPI 2.2.1-d2 i 2.3.0, Locations, tabela Status.)
- Chcesz usunąć EVSE z aktywnej listy → ustaw `status: REMOVED` i wyślij `PUT` lub `PATCH` do eMSP. Obiektów Location,
  EVSE i Connector nie usuwa się, bo inne moduły (Sessions) na nie wskazują; `DELETE` nie jest dostępne. Location bez
  ważnego EVSE uchodzi za wygasłą i nie powinna być wyświetlana.
- `StatusSchedule` (okresy przyszłych statusów) jest informacyjny; gdy status faktycznie się zmienia, CPO wypycha
  zmianę pola `status`. Przykład ze specyfikacji: stacja „jutro ruszy, dziś nadal planowana”.
- Lokalizacje prywatne (nie dla publiczności) nie są publikowane w OCPI.
- OCPI nie ma wartości „w budowie”; `UNDER_CONSTRUCTION` mapujesz na `PLANNED` albo nie publikujesz (decyzja
  operatora i umowy z eMSP). Nie publikuj `AVAILABLE` przed odbiorem.
Pola, PUT/PATCH i handshake: `dom-ev-ocpi`.

## 3. Dane NEVI i EIPA
- 23 CFR 680.116(c)(6): status stacji jest jednym z `operational`, `under construction`, `planned`, `decommissioned`
  (eCFR, pobrane 2026-10-20); to cztery wartości dla stanu stacji, osobno od statusu portu w czasie rzeczywistym
  (według OCPI 2.2.1, 680.116(c)(8)(vii)). Stany `MAINTENANCE` i `PAUSED` mapuj na *operational* z chwilowym statusem
  portu, nie na *decommissioned*. Uptime i wyłączenia: `dom-ev-regulations-us`, `dom-ev-kpi-analytics`.
- EIPA w Polsce: numer przed rozpoczęciem działalności, dane do rejestru, zmiany i wycofanie: `dom-ev-regulations-pl`
  (bez szczegółów tutaj). AFIR (dane statyczne i dynamiczne): `dom-ev-regulations-eu`.

## 4. EVSE ID i `uid`
Format i walidacja: `dom-ev-identifiers` (`ev_id_check.py`). Reguły cyklu życia:
1. EVSE ID identyfikuje **punkt ładowania w miejscu**, nie urządzenie. Zostaje przy wymianie 1:1, firmware, module, kablu i liczniku.
2. Nowe ID: przeniesienie do innej lokalizacji, zmiana operatora (ID zawiera identyfikator operatora), nowy punkt (dodatkowy EVSE).
3. Wygaszone ID **nigdy** nie jest nadawane ponownie. Wpływ: eMSP, huby, aplikacje i
   faktury trzymają stare ID; ponowne użycie skleiłoby historię dwóch różnych miejsc (CDR, sesje, opinie kierowców, ulubione).
   Rejestr trzyma listę wygaszonych ID z datą i powodem.
4. Rezerwacja ID na etapie `PLANNED` jest dozwolona; ID rezerwowane i niewykorzystane trafia do wygaszonych.
5. `uid` w OCPI: unikalny w platformie CPO, stały; nie używaj numeru sprzętu, bo przy wymianie złamiesz unikalność albo
   regułę „EVSE nie jest usuwane”. `evse_id` jest polem opcjonalnym i osobnym od `uid` (OCPI 2.2.1-d2, EVSE Object).
6. Roaming: zmiana EVSE ID u partnera wymaga ponownej synchronizacji Locations u każdego eMSP/huba, a sesje trwające
   w chwili zmiany ją tracą. Planuj zmianę poza ruchem i potwierdź `GET` po stronie eMSP.
7. CDR: zawsze zawiera ID z chwili sesji; nie przepisujesz historii na nowe ID (`dom-ev-cdr-settlement`).

## 5. Wymiana sprzętu pod tym samym EVSE
Kolejność: (1) zlecenie wymiany z numerem seryjnym starej i nowej stacji; (2) EVSE `MAINTENANCE`, publikacja
`INOPERATIVE`; (3) nowa stacja wchodzi jako asset ze stanem `COMMISSIONING` przypisany do **tego samego EVSE**;
(4) stara — zamknięcie pozycji, stan `OBSOLETE`/magazyn/utylizacja; (5) `BootNotification` nowej stacji musi zgadzać się
z rejestrem (numer seryjny, model) — wtedy `Accepted`; (6) szablon konfiguracji nowego modelu, nowy licznik z legalizacją;
(7) test sesji, `OPERATIONAL`, publikacja `AVAILABLE`. Gdy nowy model ma inną liczbę EVSE lub inne złącza, to nie
jest 1:1: nowe punkty dostają nowe ID. Licznik energii nowego urządzenia zaczyna od innej wartości: nie licz
różnicy między starym a nowym odczytem (`dom-ev-diagnostics`, rozjazd kWh).

## 6. Wyjątki
- **RMA/naprawa u producenta:** asset opuszcza lokalizację; dodaj stan roboczy `IN_REPAIR` [założenie], EVSE zostaje
  `MAINTENANCE`; po powrocie stacja przechodzi `COMMISSIONING` (inny firmware lub konfiguracja po naprawie).
- **Sprzęt z demontażu:** wraca do `IN_STOCK` jako ten sam asset; reset do ustawień fabrycznych, usunięcie certyfikatów
  i danych dostępowych zanim opuści lokalizację; nowe przypisanie = nowa pozycja, nowe EVSE ID.
- **Stacja wycofana z jednej lokalizacji i uruchomiona w innej:** nowa lokalizacja = nowe EVSE ID.

## 7. Repowering
Wymiana przestarzałego sprzętu na nowszy w tym samym miejscu. Przy zachowaniu liczby i typu punktów ID zostaje (pkt 5).
Gdy rośnie moc, sprawdź przyłącze i DLM (`dom-ev-energy-management`), zgodność protokołu i profili (`dom-ev-ocpp-2x`),
dane w rejestrach (moc w EIPA i AFIR), taryfy zależne od mocy (`dom-ev-tariffs-pricing`). Plan wymiany napędza
`OBSOLETE`: koniec wsparcia producenta, brak części, brak łatek bezpieczeństwa, spadek dostępności.

## 8. Decommissioning
Kolejność: (1) decyzja i data; (2) wyłączenie z ruchu, zakończenie trwających sesji, `ChangeAvailability` `Inoperative`;
(3) publikacja `REMOVED` do wszystkich eMSP/hubów, aktualizacja map i rejestrów publicznych; (4) ostatnie CDR rozliczone,
zamknięcie sesji osieroconych (`dom-ev-session-lifecycle`); (5) odczyt końcowy licznika i zdarzenie legalizacji;
(6) CSMS: stan `DECOMMISSIONED`, `Rejected` dla połączeń, unieważnienie certyfikatów i poświadczeń (hasło Basic,
certyfikat klienta); (7) reset fabryczny i usunięcie danych (karty autoryzacyjne, lokalna lista, logi, dane płatnicze
terminala, SIM dezaktywowana); (8) demontaż, utylizacja zgodnie z odpadami elektronicznymi, dokument przekazania
[założenie: przepisy krajowe poza bazą]; (9) EVSE ID do listy wygaszonych; (10) rozliczenie kosztowe i amortyzacja.
Nie usuwaj rekordów z bazy: rejestr, sesje i CDR zostają (retencja według zasad danych osobowych).
