# Model zagrożeń sieci ładowania EV

Ujęcie defensywne: co może pójść źle i czym to ograniczyć. Bez opisu przebiegu ataków. Wiedza ogólna branży;
liczby i progi to ilustracje **[do weryfikacji]**.

## 1. Aktywa i granice zaufania
| Granica | Co ją przecina | Czego pilnować |
|---|---|---|
| pojazd ↔ stacja | ISO 15118, Control Pilot, kabel | certyfikaty kontraktu (`dom-ev-iso15118`), fizyczny dostęp do złącza |
| stacja ↔ CSMS | WebSocket OCPP przez internet, APN lub VPN | tożsamość stacji, TLS, komendy zdalne, firmware |
| operator ↔ CSMS | konsola, API, integracje | konta, MFA, role, komendy masowe |
| CSMS ↔ eMSP/hub | OCPI (tokeny credentials), OICP | tokeny partnerów, zakres danych, CDR |
| stacja ↔ terminal płatniczy | PED, modem | certyfikacja i ochrona fizyczna (`dom-ev-payments`) |
| CSMS ↔ OSD, EMS lokacji | sygnały mocy, limity | wiarygodność źródła limitu (`dom-ev-energy-management`) |
| producent ↔ operator | firmware, klucze podpisu, zdalna diagnostyka | łańcuch dostaw, dostęp serwisowy producenta |

Najcenniejsze aktywa: konta z prawem do komend masowych, klucze podpisu firmware, magazyn certyfikatów i haseł stacji,
tokeny OCPI partnerów, dane sesji (RODO: minimalizacja i retencja).

## 2. Zagrożenia, skutki i kontrole
| Zagrożenie | Kto jest narażony | Skutek | Kontrole (kolejność zwrotu) | Odsyłacz |
|---|---|---|---|---|
| **Fałszywa stacja** w CSMS | CPO, dostawca CSMS | fałszywe sesje i CDR, wyczerpanie zasobów bramy, wejście do sieci | unikalne poświadczenia na stację; certyfikat klienta; jedno aktywne połączenie na `chargePointId`; limit połączeń z jednego adresu; akceptacja `BootNotification` tylko dla zarejestrowanych (`Pending` dla nieznanych) | `dom-ev-ocpp-2x`, `dom-ev-charger-onboarding` |
| **Fałszywy CSMS** (stacja łączy się z cudzym serwerem) | producent, CPO | przejęcie stacji, komendy i firmware od napastnika | weryfikacja certyfikatu serwera po stronie stacji; przypięte CA; zmiana adresu CSMS wymaga potwierdzenia; brak automatycznej akceptacji obcego certyfikatu | `dom-ev-csms-migration` (bezpieczna zmiana adresu) |
| **Przejęcie sesji** | kierowca, CPO | cudze ładowanie na rachunek ofiary, blokada złącza | sesja powiązana z tokenem i `transactionId`; `RemoteStop` tylko od uprawnionej strony; alert przy stopie sesji innej osoby | `dom-ev-session-lifecycle` |
| **Kradzież i klonowanie tokenów RFID** | kierowca, eMSP | ładowanie na cudzy koszt | UID bez kryptografii jest identyfikatorem, nie sekretem; reguła „dwa miejsca naraz”; limity energii i kwoty na token; szybka blokada tokenu w OCPI Tokens (`valid=false`); tokeny z drugim czynnikiem lub aplikacja | `dom-ev-emsp-platform`, `dom-ev-ocpi` |
| **Nadużycie zdalnego startu** | eMSP, CPO | masowe sesje „widmo”, DoS złączy, koszty | autoryzacja komendy (`START_SESSION`) po stronie CPO; limity na token i partnera; nadzór nad sesjami bez energii | `dom-ev-ocpi` |
| **Manipulacja odczytami** | CPO, eMSP, kierowca | zawyżone kWh, spór, naruszenie Eichrecht | odczyt podpisany (OCMF) i weryfikowany w CSMS, uzgodnienie sesja ↔ CDR, alert na niezgodny podpis | `dom-ev-metering-calibration`, `dom-ev-cdr-settlement` |
| **Złośliwy lub wadliwy firmware** | producent, CPO | przejęcie floty jednego modelu, trwała awaria | podpis firmware sprawdzany przez stację; klucze podpisu w HSM u producenta; aktualizacja falami z kohortą pilotażową; ochrona przed cofnięciem do podatnej wersji | `dom-ev-asset-operations`, `dom-ev-charger-onboarding` |
| **Kompromitacja PKI Plug & Charge** | CPO, eMSP, OEM | fałszywe kontrakty, rozliczenie na cudzy rachunek | zarządzanie korzeniami V2G i MO, unieważnianie, monitorowanie certyfikatów | `dom-ev-iso15118` |
| **Masowe zdalne wyłączenie lub zmiana mocy** | CPO, OSD | utrata przychodu; nagły skok lub spadek obciążenia sieci | zob. punkt 3 | `dom-ev-smart-charging`, `dom-ev-energy-management` |
| **Roaming: kradzież tokenu OCPI credentials** | CPO, eMSP, hub | podszycie się pod partnera, odczyt lokalizacji, tokenów, CDR | token osobny na partnera; TLS; rotacja po wycieku od razu; przechowywanie w sejfie sekretów; zakres modułów zgodny z umową | `dom-ev-ocpi` |
| **Wyciek CDR i danych sesji** | CPO, eMSP | dane osobowe (RODO), ujawnienie tras i nawyków | minimalizacja pól, kontrola dostępu wg partnera, retencja, szyfrowanie archiwów, logowanie dostępu | `dom-ev-cdr-settlement` |
| **Skimming terminala płatniczego** | CPO, kierowca | kradzież kart | kontrola fizyczna (plomby, przeglądy), terminal certyfikowany, wymiana po incydencie | `dom-ev-payments` |
| **Nadużycie dostępu serwisowego** | CPO, producent | trwały dostęp „na wszelki wypadek” | dostęp czasowy, konta imienne, nagrywanie sesji, rozdział kont producenta | `dom-ev-asset-operations` |

## 3. Skutek masowy i sieć energetyczna
Skala floty zmienia charakter ryzyka. Jeden błąd lub jedno przejęte konto może jednocześnie:
- **wyłączyć** tysiące stacji (utrata przychodu, brak ładowania w kryzysie);
- **włączyć lub podnieść moc** jednocześnie (skok obciążenia w sieci rozdzielczej);
- **zmienić profile** tak, że wiele pojazdów zacznie ładować w tej samej chwili po odblokowaniu (efekt odbicia).

Kontrole specyficzne dla tego ryzyka: próg komend masowych i zatwierdzenie drugiej osoby; fale z przerwą (np. 2–5 %
floty na falę — ilustracja **[do weryfikacji]**); losowe opóźnienia przy wznowieniu; domyślne zachowanie stacji po
utracie CSMS (offline, `TxDefaultProfile`), tak aby awaria łączności nie zmieniała mocy skokowo; ustalona z OSD
ścieżka kontaktu. Granica odpowiedzialności za limity z OSD: `dom-ev-energy-management`.

## 4. Ocena ryzyka
Dla każdego zagrożenia zapisz: aktywo, aktor (zewnętrzny, wewnętrzny, partner), skutek dla **jednej stacji** i **floty**
(niski/średni/wysoki), prawdopodobieństwo, istniejące kontrole, ryzyko resztkowe, właściciel i termin. Zagrożenia o
wysokim skutku masowym zgłaszaj zarządowi — NIS2 Art. 20 wymaga zatwierdzenia środków przez organ zarządzający.
Format wyniku: tabela jak w punkcie 2 plus kolumny „ryzyko resztkowe” i „termin”.

## Źródła
- `eu-nis2` Art. 20–21, `.claude/knowledge/eu-nis2/doc.txt:L3095-3160`, eur-lex.europa.eu/eli/dir/2022/2555/oj, pobrane 2026-10-20.
- `us-nevi` 680.106(h), `.claude/knowledge/us-nevi/doc.txt:L124-128`, ecfr.gov, pobrane 2026-10-20 (lista tematów strategii cyber).
- Wiedza ogólna branży; progi i wartości liczbowe [do weryfikacji].
