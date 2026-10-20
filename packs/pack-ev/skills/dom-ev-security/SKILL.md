---
name: dom-ev-security
description: Użyj przy bezpieczeństwie sieci ładowania EV — model zagrożeń, uprawnienia do komend masowych, detekcja anomalii, NIS2 i CRA, incydent w sieci stacji.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy CPO, producent ładowarki albo dostawca CSMS ocenia lub buduje bezpieczeństwo ekosystemu ładowania — model zagrożeń (fałszywa stacja i fałszywy CSMS, przejęcie sesji, klonowanie tokenów RFID, nadużycie zdalnego startu, złośliwy firmware, masowy Reset lub zmiana mocy jako ryzyko dla sieci energetycznej, wyciek tokenów OCPI i CDR), decyzja i migracja profili bezpieczeństwa OCPP, rotacja haseł i certyfikatów stacji, podpisany firmware i aktualizacje falami, separacja uprawnień w CSMS, logowanie i reguły detekcji, SBOM i podatności, NIS2 (czy CPO jest podmiotem, zgłoszenia 24 h i 72 h), CRA, NEVI 680.106(h), runbook incydentu w sieci ładowania. Podejście defensywne: zagrożenia na poziomie modelu i kontrole, bez technik ataku. Nie do komunikatów i zmiennych profili OCPP (dom-ev-ocpp-2x), PKI Plug & Charge (dom-ev-iso15118), podpisu odczytów (dom-ev-metering-calibration), PCI i terminali (dom-ev-payments), mapy przepisów UE (dom-ev-regulations-eu) ani diagnozy awarii bez podejrzenia ataku (dom-ev-diagnostics)."
  slowa: "bezpieczeństwo ładowarek, cyberbezpieczeństwo CPO, cybersecurity EV charging, model zagrożeń, threat model, fałszywa ładowarka, fałszywy CSMS, przejęcie stacji, przejęcie sesji, klonowanie karty RFID, skopiowany UID, nadużycie remote start, złośliwy firmware, podpisany firmware, masowy reset, wyłączenie floty, atak na sieć energetyczną, botnet ładowarek, wyciek tokenu OCPI, wyciek CDR, rotacja haseł stacji, rotacja certyfikatów, profil bezpieczeństwa migracja, separacja uprawnień, dwie osoby, four-eyes, rate limiting komend, detekcja anomalii, ten sam numer seryjny, sesje bez energii, SBOM, podatność, PSIRT, NIS2 CPO, podmiot ważny, zgłoszenie incydentu CSIRT, CRA ładowarka, NEVI cyberbezpieczeństwo, incydent w sieci ładowania, izolacja stacji, security incident, compromised charger, rogue charger"
---

# Bezpieczeństwo ekosystemu ładowania EV

Skill pomaga **bronić** sieci ładowania: nazwać zagrożenie, dobrać kontrolę, ustalić obowiązki prawne i przeprowadzić
incydent. Opisuje zagrożenia na poziomie modelu; nie podaje technik ataku ani narzędzi ofensywnych. Perspektywy:
**CPO** (flota stacji i CSMS), **dostawca CSMS** (system z dostępem do tysięcy stacji), **producent** (firmware, klucze).
Szczegóły profili OCPP, PKI i przepisów mają sąsiednie skille — tu decyzja, kolejność i obowiązki.

## Granice
| Pytanie | Skill |
|---|---|
| zmienne i komunikaty profili 1–3, `SignCertificate`, Device Model | `dom-ev-ocpp-2x` (1.6: `dom-ev-ocpp-16`) |
| certyfikat kontraktu, PKI V2G, Plug & Charge | `dom-ev-iso15118` |
| podpisany odczyt, OCMF, Eichrecht | `dom-ev-metering-calibration` |
| terminal kartowy, PCI DSS, chargeback | `dom-ev-payments` |
| mapa aktów UE (AFIR, RED, Data Act) | `dom-ev-regulations-eu` (PL: `dom-ev-regulations-pl`, USA: `dom-ev-regulations-us`) |
| stacja offline bez śladów ataku | `dom-ev-diagnostics` |

## Procedura
1. **Aktywa i granice zaufania.** Narysuj przepływ: pojazd ↔ stacja ↔ CSMS ↔ konsola operatora ↔ eMSP/hub ↔ OSD.
   Wypisz, co przejęcie każdego elementu pozwala zrobić (komenda, odczyt, pieniądze, moc w sieci).
2. **Model zagrożeń** wg tabeli niżej i `references/model-zagrozen.md`; ocena = skutek × prawdopodobieństwo, osobno
   dla jednej stacji i dla **całej floty** (skutek masowy dominuje).
3. **Kontrole** w kolejności zwrotu: tożsamość stacji i transport, uprawnienia do komend masowych, detekcja, firmware,
   łańcuch dostaw (`references/kontrole-i-migracja.md`).
4. **Obowiązki prawne**: NIS2, CRA, NEVI, RED (`references/regulacje-cyber.md`). Sprawdź prawo krajowe.
5. **Gotowość na incydent**: runbook, role, kanały, ćwiczenie (`references/incydent-w-sieci.md`).

## Model zagrożeń (skrót)
| Zagrożenie | Skutek | Główne kontrole |
|---|---|---|
| Fałszywa stacja (podszycie się pod `chargePointId`) | fałszywe sesje i odczyty, zaśmiecone dane, wejście do sieci | profil 3 (certyfikat klienta) albo unikalne hasło na stację; unikalność identyfikatora; jedno aktywne połączenie na stację |
| Fałszywy CSMS (stacja łączy się z cudzym serwerem) | przejęcie stacji, złośliwe komendy i firmware | TLS z weryfikacją łańcucha, przypięte CA, zmiana adresu CSMS tylko z potwierdzeniem |
| Przejęcie sesji, nadużycie zdalnego startu | ładowanie na cudzy koszt, blokada złącza | autoryzacja komend po stronie CSMS, powiązanie komendy z kontem, limity i alerty |
| Klonowanie tokenu RFID | ładowanie na cudzy rachunek | UID bez kryptografii = identyfikator, nie sekret; limity na token, reguła „dwa miejsca naraz”, tokeny z drugim czynnikiem (aplikacja, PIN) |
| Manipulacja odczytami | zawyżone lub zaniżone kWh, spór o CDR | odczyt podpisany i weryfikowany (`dom-ev-metering-calibration`), uzgodnienie sesja ↔ CDR |
| Złośliwy firmware | pełne przejęcie stacji, atak na flotę jednego modelu | podpis firmware sprawdzany przez stację, aktualizacje falami, klucze podpisu u producenta |
| Masowy Reset, `ChangeAvailability`, `SetChargingProfile` | utrata przychodu; skok lub spadek obciążenia sieci | separacja uprawnień, zatwierdzenie dwóch osób, limity wielkości fali, tryb bezpieczny stacji |
| Roaming: wyciek tokenu OCPI, wyciek CDR | podszycie się pod partnera, dane osobowe | rotacja tokenu, TLS, osobne tokeny na partnera, minimalny zakres danych |
| Skimming terminala płatniczego | kradzież kart | kontrola fizyczna i certyfikowany terminal (`dom-ev-payments`) |
| Kompromitacja PKI Plug & Charge | fałszywe kontrakty | zarządzanie PKI (`dom-ev-iso15118`) |

## Profile OCPP: decyzja i migracja
| Profil | Co daje | Decyzja |
|---|---|---|
| 1 (`ws://`, Basic Auth) | hasło jawnie w sieci | tylko laboratorium i sieć zamknięta |
| 2 (`wss://`, Basic Auth) | szyfrowanie, tożsamość stacji = hasło | minimum produkcyjne; hasło **unikalne na stację**, losowe |
| 3 (mTLS) | tożsamość kryptograficzna stacji | cel dla nowych modeli i stacji w sieciach publicznych; wymaga PKI i rotacji |

Migracja falami: inwentarz (model, firmware, obsługiwany profil) → uzupełnienie unikalnych haseł → włączenie TLS na
CSMS równolegle z `ws://` → przełączanie kohort (jedna kohorta = jeden model + firmware) z rollbackiem → wyłączenie
`ws://` dopiero przy zerowym ruchu. Stacje bez TLS: osobna sieć (APN/VPN), nie „wyjątek na stałe”.
Przy 1.6 profile pochodzą z dodatku (Security Whitepaper) — obsługa zależy od modelu **[do weryfikacji u producenta]**.

## Separacja uprawnień w CSMS
| Operacja | Zakres | Wymóg |
|---|---|---|
| odczyt statusu, logi | cała flota | rola odczytu |
| `TriggerMessage`, `GetLog` | jedna stacja | rola wsparcia |
| `Reset`, `ChangeAvailability` | jedna stacja | rola operacyjna + wpis w dzienniku z powodem |
| te same komendy **masowo** (> próg, np. 5 % floty lub kilkadziesiąt stacji — próg ustal sam) | wiele stacji | zatwierdzenie drugiej osoby, limit fali, przerwa między falami |
| `SetChargingProfile` zmieniający moc całej lokacji lub regionu | wiele lokacji | jak wyżej + kontrola z OSD/energią (`dom-ev-energy-management`) |
| `UpdateFirmware`, zmiana adresu CSMS, zmiana haseł | flota | proces zmian, zatwierdzenie, fale, okno serwisowe |

Konta usług (integracje) mają własne role, nie dzielą kont ludzi; MFA dla konsoli; dostęp wygasa przy zmianie roli.

## Detekcja (reguły do logów CSMS)
| Anomalia | Interpretacja |
|---|---|
| ten sam numer seryjny/`chargePointId` z dwóch adresów jednocześnie | podszycie albo duplikat konfiguracji; blokuj nowe połączenie, zachowaj stare |
| nagła zmiana konfiguracji u wielu stacji | błąd procesu albo nadużycie konta |
| `BootNotification` z nowym modelem/numerem seryjnym dla znanego EVSE | wymiana sprzętu albo podszycie — alarm, nie cicha aktualizacja rejestru |
| sesje bez przyrostu energii, pętle start/stop | nadużycie albo awaria licznika |
| ten token w dwóch krajach w krótkim czasie | klon albo współdzielenie |
| fala nieudanych uwierzytelnień | zgadywanie haseł |
| skok `SetChargingProfile`/`Reset` z jednego konta | alert natychmiast |
| zdarzenia bezpieczeństwa stacji (`SecurityEventNotification` w 2.x) | zbieraj osobno, typy zdarzeń **[do weryfikacji]** w specyfikacji |

## Obowiązki prawne (skrót)
| Akt | Dla kogo | Najważniejsze |
|---|---|---|
| NIS2 (UE) 2022/2555, Aneks I pkt 1(a) | CPO jako „operator punktu ładowania”, średni lub większy | środki Art. 21(2); zgłoszenia Art. 23: ostrzeżenie 24 h, zgłoszenie 72 h, raport końcowy do miesiąca; kary Art. 34 |
| CRA (UE) 2024/2847 | producent ładowarki i oprogramowania | Art. 14 od 11.09.2026 (24 h / 72 h / 14 dni), całość od 11.12.2027; SBOM; wsparcie ≥ 5 lat |
| NEVI 23 CFR 680.106(h), 680.114 | stacje z funduszy federalnych (USA) | strategia fizyczna i cyber, bezpieczna komunikacja, zdalne aktualizacje |
| RED (EN 18031) | producent z radiem | `dom-ev-regulations-eu` |

NIS2 to dyrektywa: obowiązek wynika z ustawy krajowej. To nie porada prawna.

## Reagowanie na incydent (skrót)
1. **Stwierdź i zapisz czas „uzyskania wiedzy”** (start zegara 24 h).
2. **Wstrzymaj komendy masowe** i zamroź konta podejrzane; zachowaj logi.
3. **Izoluj** podejrzane stacje (kwarantanna sieciowa, blokada połączenia), nie kasuj dowodów.
4. **Oceń skutek dla sieci energetycznej** i uprzedź OSD, jeśli zmieniono moc na dużą skalę.
5. **Zgłoś** (NIS2 Art. 23 / CRA Art. 14), poinformuj partnerów roamingowych i klientów.
6. **Przywracaj falami**, z weryfikacją konfiguracji i firmware; rotacja wszystkich sekretów z zasięgu incydentu.
7. **Przegląd po incydencie**. Szczegóły: `references/incydent-w-sieci.md`.

## Przykład
Wejście: CPO, 150 pracowników, 800 stacji dostaje z konsoli `ChangeAvailability` na `Inoperative` po zalogowaniu skradzionego konta.
Wynik: (1) zamrożenie konta i komend masowych, odtworzenie dostępności falami po 5 % floty; (2) CPO to prawdopodobnie
podmiot ważny NIS2 (Aneks I, średnie przedsiębiorstwo) — wczesne ostrzeżenie do CSIRT w 24 h od uzyskania wiedzy,
zgłoszenie w 72 h, raport końcowy do miesiąca po zgłoszeniu; (3) powiadomienie partnerów roamingowych o niedostępności;
(4) poprawka: zatwierdzenie drugiej osoby i limit fali dla komend masowych, MFA, alert na skok komend z jednego konta.

## Pułapki
- „TLS włączony” uznane za zamknięcie tematu: hasło wspólne dla wszystkich stacji lub ważne bez końca podważa profil 2.
- UID karty RFID traktowany jak sekret; kontrola tylko „token na białej liście”.
- Jedna rola „admin” z prawem do `Reset` całej floty; brak progu dla komend masowych.
- Aktualizacja firmware na całą flotę naraz; stacja nie sprawdza podpisu.
- Brak rejestru czasu „uzyskania wiedzy” — nie da się wykazać terminu 24 h.
- Zgłoszenie incydentu tylko do regulatora, bez informacji dla partnerów roamingowych i OSD.
- Kasowanie logów stacji „na czas diagnozy” przed zabezpieczeniem dowodów.
- Założenie, że przepisy dotyczą tylko producenta albo tylko CPO: dostawca CSMS bywa też podmiotem (usługa zarządzana) **[do weryfikacji]**.

## Checklista
- [ ] Przepływ i granice zaufania narysowane; skutek oceniony dla pojedynczej stacji i floty
- [ ] Profil OCPP wybrany świadomie; hasła unikalne na stację; plan wyłączenia `ws://`
- [ ] Komendy masowe: próg, drugi zatwierdzający, limit fali, dziennik z powodem
- [ ] Firmware podpisany i wdrażany falami; SBOM i proces zgłaszania podatności
- [ ] Reguły detekcji (duplikat serialu, sesje bez energii, klon tokenu, skok komend) działają i mają właściciela
- [ ] Ustalono status NIS2 i CRA; rejestr czasu „uzyskania wiedzy”; kanał do CSIRT
- [ ] Runbook incydentu z kontaktami do OSD i partnerów, ćwiczony

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| szczegółowy model zagrożeń: aktywa, aktor, skutek, kontrola, odsyłacz | `references/model-zagrozen.md` |
| rotacja, firmware, uprawnienia, detekcja, OCPI, SBOM, kolejność wdrożeń | `references/kontrole-i-migracja.md` |
| NIS2, CRA, NEVI, RED: artykuły, terminy, linie w bazie | `references/regulacje-cyber.md` |
| runbook incydentu w sieci stacji, komunikacja, przywracanie | `references/incydent-w-sieci.md` |

## Źródła
- `eu-nis2`: NIS2 (UE) 2022/2555, Art. 20–23, 34, Aneks I pkt 1(a); eur-lex.europa.eu/eli/dir/2022/2555/oj, pobrane 2026-10-20.
- `eu-cra`: CRA (UE) 2024/2847, Art. 13, 14, 71, Aneks I; eur-lex.europa.eu/eli/reg/2024/2847/oj, pobrane 2026-10-20.
- `us-nevi`: 23 CFR 680.106(h), 680.114, ecfr.gov, pobrane 2026-10-20.
- `ocpp-json-schemas`: `UpdateFirmwareRequest` (pole `signature`), `SetNetworkProfileRequest` (`securityProfile`), pobrane 2026-10-20.
- Skille fabryki: `dom-ev-ocpp-2x`, `dom-ev-ocpi`, `dom-ev-asset-operations`, `dom-ev-regulations-eu` (stan repozytorium 2026-10-20).
- Wiedza ogólna branży (modele zagrożeń, progi, praktyki rotacji) — [do weryfikacji] przed użyciem w audycie.
