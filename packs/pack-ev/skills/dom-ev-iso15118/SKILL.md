---
name: dom-ev-iso15118
description: Użyj przy komunikacji auto–ładowarka i Plug & Charge — DIN 70121, ISO 15118-2 i -20, SLAC, SDP, certyfikat kontraktu, przez OCPP, awarie.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba zrozumieć lub zdebugować rozmowę pojazdu z ładowarką wysokiego poziomu — DIN 70121 kontra ISO 15118-2 i -20, SLAC i SDP, SupportedAppProtocol i wybór protokołu, kolejność komunikatów sesji DC i AC, timeouty, Plug & Charge i PKI (V2G Root, CPO, CPS, MO, OEM), instalacja i aktualizacja certyfikatu kontraktu i jej przenoszenie przez OCPP 2.0.1 i 1.6, EIM kontra PnC, wygasły certyfikat, brak łańcucha, OCSP, zegar, fallback do DIN. Nie do dwukierunkowego V2G i BPT (dom-ev-v2x), stanów CP i PWM (dom-ev-charger-hardware), szczegółów Authorize i Device Model w OCPP (dom-ev-ocpp-2x), formatu EMAID (dom-ev-identifiers)."
  slowa: "ISO 15118, ISO 15118-2, ISO 15118-20, DIN 70121, DIN SPEC 70121, Plug & Charge, PnC, SLAC, PLC, HomePlug Green PHY, SDP, SECC, EVCC, SupportedAppProtocol, certyfikat kontraktu, contract certificate, V2G Root, CPS, OEM provisioning, CertificateInstallation, CertificateUpdate, Get15118EVCertificate, iso15118CertificateHashData, EIM, ExternalPayment, auto nie rozpoczyna ładowania, PnC nie działa, handshake TLS, wygasły certyfikat, fallback do DIN, EXI, josev, jak działa Plug & Charge, stacja ładowania z Plug & Charge, pojazd elektryczny rozmawia z ładowarką"
---

# ISO 15118 i DIN 70121 — rozmowa auto ↔ ładowarka

Skill prowadzi przez to, **co pojazd (EVCC) i ładowarka (SECC) mówią do siebie ponad sygnałem CP**: od SLAC przez
wybór protokołu po Plug & Charge. Normy ISO 15118 i DIN 70121 są płatne i nie ma ich w bazie wiedzy fabryki. Fakty
o komunikatach, timeoutach i PKI pochodzą z **implementacji josev** (SwitchEV/iso15118, ranga W) i oznaczam je
„wg josev”. Resztę, czego nie potwierdza kod, oznaczam **[do weryfikacji]**.

## Co zostaje poza skillem
| Temat | Skill |
|---|---|
| ładowanie dwukierunkowe, BPT, V2H/V2G, profile ujemne | **dom-ev-v2x** (tu tylko odsyłacz i identyfikatory usług BPT) |
| stany CP A–F, PWM, prąd z wypełnienia, PP | **dom-ev-charger-hardware** |
| `Authorize`, Device Model, `TransactionEvent`, profile bezpieczeństwa OCPP | **dom-ev-ocpp-2x**, **dom-ev-ocpp-16** |
| format EMAID, walidacja, cyfra kontrolna | **dom-ev-identifiers** |
| moc zależna od baterii (krzywa, 400/800 V) | **dom-ev-vehicle-battery** |

## Stos w jednym obrazie
CP + PWM (5 % = zaproszenie do komunikacji cyfrowej; dom-ev-charger-hardware) → SLAC po PLC (ISO 15118-3,
HomePlug Green PHY; komunikaty CM_* **[do weryfikacji]**) paruje auto z właściwym złączem → SDP (UDP, IPv6
link-local) wskazuje adres SECC → V2GTP + EXI nad TCP lub TLS → SupportedAppProtocol → sesja DIN / -2 / -20.
OCPP leży nad tym: wiadomość zrodzona w aucie (certyfikat kontraktu, potrzeby energii, prośba o instalację
certyfikatu) to ISO 15118, a CSMS widzi ją dopiero po przetłumaczeniu przez stację.

## DIN 70121, ISO 15118-2, ISO 15118-20 — kiedy który
| Cecha | DIN 70121 | ISO 15118-2 | ISO 15118-20 |
|---|---|---|---|
| Energia | tylko DC (CCS) | AC i DC | AC, DC, BPT, WPT, ACD (usługi 1–7, wg josev) |
| Autoryzacja | tylko zewnętrzna (`ExternalPayment`) | `ExternalPayment` lub `Contract` (PnC) | `EIM` lub `PnC`, negocjowane w `AuthorizationSetup` |
| Certyfikaty | brak komunikatów | `CertificateInstallation`, `CertificateUpdate` | tylko `CertificateInstallation` (wg josev) |
| TLS | wg josev tylko tryb bez TLS **[do weryfikacji]** | opcjonalny, wymagany dla PnC | wymagany **[do weryfikacji w normie]** |
| Pętla ładowania | `CurrentDemand` | `ChargingStatus` (AC), `CurrentDemand` (DC) | `ChargeLoop` AC i DC |
| Harmonogram | brak | `SAScheduleList` w `ChargeParameterDiscovery` | `ScheduleExchange`, tryby Scheduled i Dynamic |

Co z tego wynika w praktyce:
- **PnC wymaga co najmniej ISO 15118-2.** DIN 70121 w josev nie ma `PaymentDetails` ani `CertificateInstallation`
  (brak ich na liście timeoutów DIN), więc sesja DIN kończy się autoryzacją zewnętrzną (karta, aplikacja).
- Starsze auta DC bywają tylko DIN; SECC tylko z -20 ich nie obsłuży. Wystaw wszystkie trzy protokoły.
- -2 i -20 nie są zgodne na poziomie komunikatów; wybór następuje w SupportedAppProtocol.

## SDP i SupportedAppProtocol (wg josev)
**SDP** — auto wysyła UDP na port **15118** (adres multicast link-local **[do weryfikacji]**) żądanie z dwoma bajtami:
`Security` (TLS = `0x00`, brak TLS = `0x10`) i `Transport` (TCP = `0x00`; UDP `0x10` tylko dla samego SDP).
Odpowiedź SECC ma 20 bajtów: IPv6 (16) + port (2, w kodzie 49152–65535) + `Security` + `Transport`.
Typy ładunku V2GTP: SDP `0x9000`/`0x9001`; EXI w DIN i -2 `0x8001`; w -20 `0x8001` (SAP), `0x8002` (Mainstream),
`0x8003` (AC), `0x8004` (DC). Adres musi być **link-local IPv6**; adres globalny nie działa (README josev).
Timeout żądania SDP: 0,25 s; po `sdpRetryCycles` nieudanych cyklach auto wraca do ładowania na samym PWM (README josev).

**SupportedAppProtocolReq** — lista `AppProtocol`: `ProtocolNamespace`, `VersionNumberMajor`/`Minor`, `SchemaID`
(0–255), `Priority` (1–20). Przestrzenie nazw: `urn:din:70121:2012:MsgDef`, `urn:iso:15118:2:2013:MsgDef`,
`urn:iso:std:iso:15118:-20:*` (osobno Common, AC, DC...). Odpowiedź `SupportedAppProtocolRes`: `ResponseCode`
(`OK_SuccessfulNegotiation`, `OK_SuccessfulNegotiationWithMinorDeviation`, `Failed_NoNegotiation`) i `SchemaID`.
Wybiera **SECC**: ze wspólnych wpisów bierze ten o najwyższym priorytecie auta (`Priority` 1 = najwyższy
**[do weryfikacji]**). Brak wspólnego wpisu = `Failed_NoNegotiation` i koniec sesji. Timeout: 2 s.

## Przebieg sesji (nazwy komunikatów wg josev)
**ISO 15118-2, kolejność wspólna:** `SessionSetup` → `ServiceDiscovery` (opcjonalnie `ServiceDetail`) →
`PaymentServiceSelection` (wybór `ExternalPayment` albo `Contract`) → dla PnC: ewentualnie `CertificateInstallation`
lub `CertificateUpdate`, potem `PaymentDetails` (EMAID + łańcuch kontraktu; SECC zwraca `GenChallenge` 16 B) →
`Authorization` (podpis wyzwania; odpowiedź może być `Ongoing`, bo timeout to 2 s) → `ChargeParameterDiscovery`
(pętla, gdy `EVSEProcessing` = `Ongoing`).
- **AC:** `PowerDelivery`(Start) → pętla `ChargingStatus` (+ `MeteringReceipt`) → `PowerDelivery`(Stop) →
  `SessionStop`.
- **DC:** `CableCheck` (pętla do `Finished`) → `PreCharge` → `PowerDelivery`(Start) → pętla `CurrentDemand` →
  `PowerDelivery`(Stop) → `WeldingDetection` → `SessionStop`.

**ISO 15118-20:** `SessionSetup` → `AuthorizationSetup` (SECC ogłasza usługi `EIM`/`PnC` i flagę
`CertificateInstallationService`) → opcjonalnie `CertificateInstallation` → `Authorization` (pętla `Ongoing`) →
`ServiceDiscovery` → `ServiceDetail` → `ServiceSelection` → `AC_`/`DC_ChargeParameterDiscovery` →
`ScheduleExchange` → (DC: `DC_CableCheck`, `DC_PreCharge`) → `PowerDelivery`(Start, z `EVPowerProfile` po
`EVProcessing` = `Finished`) → `AC_`/`DC_ChargeLoop` → `PowerDelivery`(Stop) → (DC: `DC_WeldingDetection`) →
`SessionStop`. Identyfikatory usług: AC 1, DC 2, WPT 3, DC_ACDP 4, AC_BPT 5, DC_BPT 6, DC_ACDP_BPT 7,
Internet 65, ParkingStatus 66 (wg josev). Warianty BPT: dom-ev-v2x.

**DIN 70121:** jak DC w -2, ale `ServicePaymentSelection` → `ContractAuthentication` (odpytanie o wynik
autoryzacji zewnętrznej), bez komunikatów certyfikatów.

Pełne tabele i timeouty: `references/sesja-i-timeouty.md`.

## Timeouty (wartości z implementacji josev, nie z normy)
SDP 0,25 s; SupportedAppProtocol 2 s; typowa para żądanie–odpowiedź 2 s; `CurrentDemand` 0,25 s; pętla
ładowania w -20 0,5 s; `CertificateInstallation`/`Update` i `PaymentDetails` 5 s; start komunikacji po stronie
auta 20 s; bezczynność SECC 60 s; `CableCheck` 40 s. Tabele: `references/sesja-i-timeouty.md`.

## Plug & Charge i PKI
Auto przedstawia **łańcuch certyfikatu kontraktu** i podpisuje wyzwanie kluczem kontraktu. SECC lub CSMS sprawdza
łańcuch, ważność i unieważnienie, a potem mapuje **EMAID** (format: dom-ev-identifiers) na token i konto eMSP
(dom-ev-ocpi, Tokens).

Cztery drzewa certyfikatów (skrypt create_certs.sh w josev, tylko do testów):
| Drzewo | Łańcuch | Do czego |
|---|---|---|
| V2G → CPO | V2GRootCA → CPOSubCA1 → CPOSubCA2 → liść SECC | TLS: ładowarka przedstawia się autu |
| V2G → CPS | V2GRootCA → CPSSubCA1 → CPSSubCA2 → liść CPS | podpis odpowiedzi przy instalacji certyfikatu |
| MO | MORootCA → MOSubCA1 → MOSubCA2 → liść kontraktu | tożsamość kierowcy (EMAID) |
| OEM | OEMRootCA → OEMSubCA1 → OEMSubCA2 → liść provisioning | auto przedstawia się przy instalacji kontraktu |
Zasady ze skryptu: krzywa eliptyczna, DER, `pathLen 0` na sub-CA 2, liść `CA=false`.
Okresy ważności w skrypcie: liść SECC 60 dni, CPS 90, kontrakt 730, korzeń V2G 3650 — to wartości testowe,
w produkcji zależą od polityki PKI (CharIN, Hubject, Gireve **[do weryfikacji]**). Topologia produkcyjna
(czy korzeń MO leży pod V2G Root) różni się między ekosystemami **[do weryfikacji]**.

Instalacja kontraktu: auto wysyła `CertificateInstallationReq` z certyfikatem OEM i listą zaufanych korzeni;
odpowiedź niesie łańcuch CPS, łańcuch kontraktu, **zaszyfrowany klucz prywatny**, klucz DH i EMAID. W -2 jest też
`CertificateUpdateReq` (odnowienie), w -20 odnowienie to ponowna instalacja. Budżet czasu: **5 s**, a w -2
odpowiedź nie ma stanu „w toku”.

## PnC w OCPP
| Krok | OCPP 2.0.1 (pola żądań wg schematów JSON; odpowiedzi **[do weryfikacji]**) |
|---|---|
| autoryzacja kontraktu | `Authorize` z `idToken` typu `eMAID` i `certificate` (PEM, do 5500 znaków) albo `iso15118CertificateHashData` (do 4 wpisów, dane do OCSP) |
| instalacja/aktualizacja kontraktu | `Get15118EVCertificate`: `action` (Install/Update), `iso15118SchemaVersion`, `exiRequest` (do 5600 znaków) → `status` (Accepted/Failed) + `exiResponse` |
| certyfikat stacji | `SignCertificate` (`csr`, `certificateType`) → `CertificateSigned` (`certificateChain`) |
| zaufane korzenie | `InstallCertificate` (V2GRoot, MORoot), `GetInstalledCertificateIds`, `DeleteCertificate` |
| potrzeby auta | `NotifyEVChargingNeeds` (`evseId`, `chargingNeeds`) → `SetChargingProfile` (dom-ev-smart-charging) |
**OCPP 1.6:** brak natywnych komunikatów; wg whitepaper OCA te same operacje jadą w `DataTransfer` z
`vendorId` OCA **[do weryfikacji]**. Szczegóły i konfiguracja (`ISO15118Ctrlr`): `references/pki-i-ocpp.md`.

## EIM kontra PnC
EIM (External Identification Means): kierowca autoryzuje się poza protokołem — karta RFID, aplikacja, terminal
(w -2 `ExternalPayment`). PnC: tożsamość dostarcza auto (`Contract`). Ładowarka **ogłasza**, co oferuje (-2: lista
opcji płatności, -20: `AuthorizationServices`, maks. 2); auto wybiera. Bez PnC sesja idzie na EIM.

## Typowe awarie
SDP bez odpowiedzi, `Failed_NoNegotiation`, wygasły liść SECC, brak sub-CA w łańcuchu, zły zegar, `Authorize` z
`CertificateExpired`/`CertChainError`, OCSP nieosiągalny, instalacja kontraktu powyżej 5 s, powrót auta do
samego PWM po `sdpRetryCycles` — przyczyny i naprawy krok po kroku: `references/pki-i-ocpp.md` (sekcja 9).

## Przykład
**Wejście:** log SECC: `SDPRequest(TLS, TCP)` → `SDPResponse` → `SupportedAppProtocolReq` z wpisami DIN
(Priority 3), -2 (Priority 2), -20 DC (Priority 1). SECC w firmware zna DIN i -2. Po `SessionSetup` lista
płatności w `ServiceDiscoveryRes` zawiera tylko `ExternalPayment`. Kierowca z kontraktem PnC pyta, czemu musi
przyłożyć kartę.

**Wynik:** SECC nie zna -20, więc z wspólnych wpisów bierze -2 (Priority 2 jest wyższy niż 3 dla DIN) —
`OK_SuccessfulNegotiation` i `SchemaID` wpisu -2. PnC nie jest wyłączone przez protokół (-2 je ma). Brak
`Contract` wynika z konfiguracji stacji: `ISO15118PnCEnabled` wyłączone albo brak ważnego certyfikatu SECC
**[do weryfikacji w Device Model]**. Naprawa: włączyć PnC, sprawdzić łańcuch SECC i korzenie V2G/MO w
`GetInstalledCertificateIds` (dom-ev-ocpp-2x).

## Pułapki
- SLAC/SDP nie są OCPP; `Authorize` z certyfikatem to dopiero efekt rozmowy -2/-20.
- Założenie, że PnC działa w DIN 70121 — nie działa.
- Timeouty z josev to implementacja, nie norma; testuj na sprzęcie referencyjnym.
- Krótko żyjący certyfikat SECC (60 dni w skrypcie testowym) bez automatycznego `SignCertificate`.
- Zegar stacji psuje ocenę okresów ważności.
- SoC bywa niedostępny (AC, brak ISO 15118) — model sesji go nie wymaga.
- EMAID, RFID i konto to różne identyfikatory (dom-ev-identifiers).

## Checklista
- [ ] Wersja protokołu zapisana per sesja (DIN / -2 / -20) i powód wyboru (`Priority`, wspólne wpisy)
- [ ] EIM i PnC rozróżnione; wiadomo, co stacja ogłosiła
- [ ] Budżet 5 s dla `CertificateInstallation` zmierzony na całej ścieżce auto–stacja–CSMS–CPS
- [ ] Daty ważności SECC, korzeni V2G/MO i kontraktu monitorowane; odnowienie zautomatyzowane
- [ ] Zegar stacji synchronizowany (NTP); wynik OCSP i tryb offline określone

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| tabele timeoutów -2/-20/DIN, pełna kolejność komunikatów, pętle `Ongoing` | `references/sesja-i-timeouty.md` |
| PKI, instalacja i aktualizacja kontraktu, OCPP 2.0.1 i 1.6, konfiguracja, awarie krok po kroku | `references/pki-i-ocpp.md` |

## Źródła
- josev-iso15118 (SwitchEV/iso15118, Apache 2.0, ranga W): pliki timeouts.py (wspólne, -2, -20, DIN), sdp.py,
  app_protocol.py, enums.py, iso15118_2/body.py, iso15118_20/common_messages.py, dc.py, ac.py,
  pki/create_certs.sh, README — github.com/SwitchEV/iso15118, pobrane 2026-10-20 (baza: `.claude/knowledge/josev-iso15118/doc.txt`).
- Import dom-ev-charging (stary plik iso-15118, 2026-09-27). Norm ISO 15118,
  DIN 70121 i OCPP 2.1 nie ma w bazie; pola żądań OCPP dla 15118 sprawdzone w `ocpp-json-schemas` (2.0.1), odpowiedzi nie.
