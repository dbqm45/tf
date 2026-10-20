# Ciągłość biznesowa i plan migracji

> **Spis treści:** 1. Sesje w toku, transakcje offline, CDR · 2. OCPI: ta sama tożsamość publiczna, bez przerwy w… · 3. Taryfy, płatności ad hoc, smart charging · 4. Raporty, uptime, monitoring · 5. Rejestr ryzyk i zależności · 6. Komunikacja z partnerami OCPI i hubem · 7. Kryteria zakończenia i wyłączenie starego systemu · 8. Typowe porażki

Spis treści: 1. Sesje i CDR · 2. OCPI i tożsamość · 3. Taryfy, płatności, smart charging · 4. Raporty i monitoring · 5. Rejestr ryzyk · 6. Komunikacja · 7. Zakończenie · 8. Typowe porażki

## 1. Sesje w toku, transakcje offline, CDR
- **Sesja w toku w chwili przełączenia**: najprościej nie przełączać stacji z aktywną transakcją (`Reset OnIdle`, kontrola
  `StatusNotification`). Gdy konieczne, sesja kończy się w starym systemie, a nowa zaczyna w nowym; nie dzielisz jednej
  sesji między dwa systemy.
- **Transakcje offline**: stacja kolejkuje zdarzenia (1.6: `StartTransaction` / `StopTransaction` z zapisanym czasem;
  2.0.1: `TransactionEvent` z `seqNo`, `offline`) i wysyła je do tego CSMS, z którym połączy się pierwszy raz po powrocie.
  Zaległe z okresu sprzed migracji mogą trafić do nowego systemu, który nie zna transakcji → przygotuj import: przyjmij
  zdarzenie z własnym znacznikiem czasu, oznacz źródło „zaległe sprzed migracji”, nie wystawiaj CDR dla sesji, którą
  stary system już rozliczył. Reguły sesji i duplikatów: **dom-ev-session-lifecycle**.
- **CDR**: wystawiony CDR jest niezmienny (dom-ev-cdr-settlement); zmiana systemu nie zmienia jego treści. Podział:
  CDR za sesje zakończone przed przełączeniem wystawia stary system, po — nowy; granica to `Ended` sesji. Nowy system
  zachowuje **ciągłość identyfikatorów CDR** (brak kolizji id), a eMSP nie dostaje dwóch CDR za jedną sesję.
- Historia sesji w nowym systemie służy do raportów i sporów; jej import nie generuje ponownych CDR ani powiadomień do eMSP.
- Zamknięcie rozliczeń okresu sprzed migracji (uzgodnienie CDR z sesjami i fakturami eMSP) przed wyłączeniem starego systemu.

## 2. OCPI: ta sama tożsamość publiczna, bez przerwy w publikacji
- `country_code` + `party_id`, Location ID, `evse.uid`, `evse_id`, Connector ID: **bez zmian** (dom-ev-identifiers, dom-ev-ocpi).
- Przejęcie roamingu przez nowy system to osobny tor: nowy system rejestruje się u partnerów (wymiana poświadczeń
  tokenów A/B/C w `credentials` przy nowym adresie `versions`), albo dostawca przekazuje poświadczenia [uzgodnienie
  per partner]. Partner może wymagać okna na zmianę whitelisty adresów IP i endpointów.
- **Tylko jedna platforma publikuje** `Locations`, `Tariffs`, `Sessions`, `CDRs` w danym czasie. Dwie publikujące naraz = nadpisywanie
  statusów i duble. Wyłącz publikację starego w tym samym oknie, w którym włączasz nową; stary **nie wysyła `REMOVED`**.
- Statusy EVSE w OCPI w czasie przełączenia: nie zostawiaj EVSE jako `UNKNOWN`/`OUTOFORDER` na dłużej niż okno; uzgodnij z partnerami,
  że krótka zmiana to przełączenie.
- **Tokeny i whitelisty**: nowy system musi mieć komplet tokenów z OCPI Tokens (lub pobrać pełny zestaw od eMSP przy starcie),
  inaczej `Authorize` offline po stronie stacji i lokalna lista odrzucą znane karty. Autoryzacja w czasie rzeczywistym
  (`POST authorize`) musi działać od pierwszej minuty. Własne karty operatora (lokalne) eksportuj ze starego systemu.
- Komendy z eMSP (`START_SESSION`, `STOP_SESSION`) trafiają do platformy, która ma stację online; trasę ustala jej adres w OCPI,
  więc zmiana platformy wymaga zmiany endpointów commands u partnera.
- Hub (dom-ev-oicp-hubs): konto u huba i `OperatorID` zostają przy operatorze; zmienia się punkt podłączenia [do uzgodnienia z hubem].

## 3. Taryfy, płatności ad hoc, smart charging
- **Taryfy** i przypisania do EVSE: eksport w formacie OCPI Tariffs, test kalkulatorem na tych samych sesjach przed i po
  (`.claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py`); różnica kwot = blokada fali. Cena widoczna kierowcy przed
  sesją musi być ta sama (dom-ev-regulations-eu: AFIR).
- **Terminale płatnicze ad hoc**: sprawdź, czy terminal jest sparowany ze stacją przez dostawcę CSMS. Zmiana oznacza nowy
  flow preautoryzacji i rozliczenia; przeprowadź testową płatność i zwrot (dom-ev-payments). Terminal, który przestaje działać
  przy zdrowej stacji, to utrata obowiązku płatności ad hoc na stacjach publicznych.
- **Smart charging**: profile ustawione przez stary CSMS (`SetChargingProfile`) bywają trwałe w stacji lub kasowane po restarcie.
  Odczytaj `GetCompositeSchedule`, zapisz limity lokacji, ustaw od nowa i zweryfikuj skryptem
  `.claude/skills/dom-ev-smart-charging/scripts/composite_schedule.py`. Przy lokacjach z limitem przyłącza (DLM) to bramka
  bezpieczeństwa: dom-ev-energy-management.
- **Lista lokalna autoryzacji**: po przełączeniu zsynchronizuj `SendLocalList` albo wyczyść; wersja listy jest związana ze stacją.

## 4. Raporty, uptime, monitoring
- Uptime za okres migracji liczony z obu systemów: sklej oś czasu po stacjach. Okno bez danych z żadnego systemu to
  „nieznany”, nie „dostępny” ani „niedostępny”. Zasady i skrypt: **dom-ev-kpi-analytics**
  (`.claude/skills/dom-ev-kpi-analytics/scripts/uptime_kpi.py`, opcja `--unknown`); wymóg uptime w USA: dom-ev-regulations-us.
- **Podwójny monitoring** na czas migracji: stary i nowy system jako źródła statusu + test niezależny (ping stacji, status OCPI
  z perspektywy eMSP). Alert „stacja na żadnym CSMS” > próg.
- Zmiany statusu z samego przełączenia (Boot, `Unavailable` na czas `Reset`) oznacz w danych jako „migracja”, żeby nie
  zaśmiecały analizy awarii (dom-ev-diagnostics).
- Raportowanie regulacyjne za okres migracji (NAP, dane dynamiczne): publikacja nie może zniknąć na czas przejścia
  (dom-ev-regulations-eu, dom-ev-regulations-pl).

## 5. Rejestr ryzyk i zależności
| Ryzyko / zależność | Właściciel | Środek |
|---|---|---|
| Dostawca opóźnia eksport lub wyłącza funkcje przed końcem umowy | zakupy/prawny | harmonogram w umowie, próbka eksportu, okres równoległy |
| Brak klucza adresu w stacjach 1.6 | wykonawca/OEM | lista kluczy od producenta, pilot na modelu |
| Utrata stacji po błędnym adresie | operacje | lab, rollback, wizyty serwisu w budżecie |
| Certyfikaty/CA nie pasują | bezpieczeństwo/PKI | doinstalowanie CA przed falą |
| Zmiany firewalli i APN | sieć/DevOps | zlecenie z wyprzedzeniem, test z lokalizacji |
| Partner roamingowy nie zdąży ze zmianą endpointów | roaming | harmonogram z partnerami, okno wspólne |
| Dwie platformy publikują naraz | roaming | jeden przełącznik publikacji, kontrola |
| Terminal płatniczy przestaje działać | płatności | test przed falą, rezerwa terminala |
| Rozbieżność CDR/taryf | rozliczenia | kalkulator, uzgodnienie |
| Producent ładowarki nie wspiera nowej konfiguracji | OEM | wymóg w kontrakcie, lista wsparcia |
| Wyciek poświadczeń w migracji | bezpieczeństwo | magazyn sekretów, rotacja po migracji |

## 6. Komunikacja z partnerami OCPI i hubem
1. Powiadomienie z wyprzedzeniem (czas uzgodniony z partnerem; typowo tygodnie) z datą okna, listą Location ID i informacją, że
   identyfikatory się nie zmieniają.
2. Prośba o: nowe endpointy i whitelistę adresów, ponowną wymianę poświadczeń lub przejęcie, okno testowe w sandboxie partnera.
3. Kontakt dyżurny w dniu przełączenia po obu stronach; kanał do zgłoszeń.
4. Po przełączeniu: potwierdzenie widoczności lokalizacji i statusów u każdego partnera; zgłoszenia o brakujących EVSE → kontrola
   `Locations`, nie zgadywanie.
5. Informacja dla kierowców tylko, jeśli zmienia się numer infolinii, aplikacja lub sposób płatności.

## 7. Kryteria zakończenia i wyłączenie starego systemu
- Zero stacji produkcyjnych łączących się ze starym (min. kilka tygodni obserwacji, w tym pełen cykl rozliczeniowy eMSP) [okres do ustalenia].
- Wszystkie CDR starego systemu wystawione, uzgodnione i zaakceptowane lub wyjaśnione; sesje bez CDR rozstrzygnięte.
- Pełny, zweryfikowany eksport (dane, konfiguracje, logi do retencji prawnej); kopia z kluczem szyfrowania u operatora.
- Roaming: publikacja tylko z nowej platformy, potwierdzenia partnerów.
- Certyfikaty, hasła i tokeny starego systemu unieważnione; konta usunięte; DNS starego adresu zarządzany (nie oddawaj go komuś obcemu).
- Usunięcie danych u dostawcy z potwierdzeniem (zgodnie z umową i RODO), koszty zamknięte, umowa wypowiedziana.
- Decyzję o wyłączeniu podejmuje człowiek; w protokole zamknięcia: data, kryteria, podpisy.

## 8. Typowe porażki
1. Stacje przełączone, lecz bez taryf/tokenów/smart charging: sesje działają, kierowca dostaje złą cenę lub brak autoryzacji.
2. Zmiana EVSE ID lub `uid`: eMSP traci historię, aplikacje nie widzą punktów.
3. Dwie platformy publikują OCPI: nadpisywane statusy.
4. Brak CA nowego dostawcy na stacjach: masowa utrata łączności po `Reset`.
5. Zbyt wcześnie wyłączony stary system: brak miejsca na dosyłane CDR i zaległe transakcje.
6. Fala po wszystkich modelach naraz, bez pilota: wada jednego modelu kładzie całość.
7. Migracja OCPP 1.6 → 2.0.1 razem ze zmianą systemu: nie wiadomo, co zawiodło.
8. Raport uptime z okresu migracji z luką policzoną jako awaria (lub jako dostępność).
