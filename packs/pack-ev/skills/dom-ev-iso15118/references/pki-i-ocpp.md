# PKI, certyfikat kontraktu i OCPP dla ISO 15118

> **Spis treści:** 1. Źródła i pewność · 2. Drzewa certyfikatów · 3. Instalacja certyfikatu kontraktu · 4. Aktualizacja certyfikatu kontraktu · 5. OCPP 2.0.1 — przeniesienie przez CSMS (żądania i… · 6. OCPP 1.6 — **[do weryfikacji]** · 7. Weryfikacja kontraktu i OCSP · 8. EIM kontra PnC · 9. Awarie krok po kroku · 10. Fallback

Spis treści: 1. Źródła i pewność · 2. Drzewa certyfikatów · 3. Instalacja kontraktu · 4. Aktualizacja · 5. OCPP 2.0.1 ·
6. OCPP 1.6 · 7. Weryfikacja i OCSP · 8. EIM kontra PnC · 9. Awarie krok po kroku · 10. Fallback.

## 1. Źródła i pewność
- Struktura komunikatów -2 i -20 i skrypt PKI: josev (ranga W, pobrane 2026-10-20).
- Nazwy i pola komunikatów OCPP dla ISO 15118: w bazie `ocpp-json-schemas` są tylko schematy smart charging, więc
  pola żądań `Authorize`, `Get15118EVCertificate`, `CertificateSigned`, `SignCertificate`, `NotifyEVChargingNeeds` sprawdzone w schematach JSON 2.0.1 (`ocpp-json-schemas`, pobrane 2026-10-20). Odpowiedzi `AuthorizeResponse` i `Get15118EVCertificateResponse` też w schematach; zmiany w 2.1 — **[do weryfikacji]**.
- Polityka PKI (CharIN, Hubject, Gireve) nie jest w bazie: ważności i topologię produkcyjną weryfikuje się u
  operatora PKI.

## 2. Drzewa certyfikatów
Skrypt create_certs.sh (josev) tworzy komplet do testów (krzywa eliptyczna, podpis SHA-2, klucze zaszyfrowane
hasłem, wynik DER dla ISO 15118; PEM tylko pośrednio):

| Drzewo | Łańcuch | Ważność w skrypcie (dni) |
|---|---|---|
| V2G Root | samopodpisany `V2GRootCA` | 3650 |
| CPO (TLS ładowarki) | CPOSubCA1 → CPOSubCA2 → liść SECC | 1460 → 365 → **60** |
| CPS (Certificate Provisioning Service) | CPSSubCA1 → CPSSubCA2 → liść CPS (pod V2G Root) | 1460 → 730 → **90** |
| MO / eMSP | `MORootCA` (samopodpisany) → MOSubCA1 → MOSubCA2 → liść kontraktu | 3650 → 1460 → 1460 → **730** |
| OEM | `OEMRootCA` → OEMSubCA1 → OEMSubCA2 → liść provisioning | 3650 → 1460 → 1460 → 1460 |

Wartości to dane testowe; skrypt zachęca, by skracać okresy i cofać zegar, aby wygenerować wygasłe certyfikaty
(przydatne w testach negatywnych). Zasady dobre również w produkcji:
- `pathLen` 0 na sub-CA 2 — za nim musi stać liść;
- liść: `CA=false`, `digitalSignature`; sub-CA: `keyCertSign`, `crlSign`;
- osobne klucze i certyfikaty dla SECC (TLS) i dla stacji w OCPP (profil 3, dom-ev-ocpp-2x);
- łańcuch SECC wysyłany w kolejności liść → sub-CA2 → sub-CA1.

Role:
| Rola | Co robi z certyfikatami |
|---|---|
| operator V2G Root | wystawia sub-CA CPO i CPS |
| CPO | wystawia certyfikat SECC; zarządza zaufanymi korzeniami stacji |
| CPS | podpisuje odpowiedź instalacji kontraktu; zwykle po stronie eMSP lub huba |
| MO / eMSP | wystawia certyfikaty kontraktu powiązane z EMAID |
| OEM | wgrywa do auta certyfikat provisioning (klucz fabryczny) |

## 3. Instalacja certyfikatu kontraktu
Kiedy: auto nowe, kontrakt dodany później, kontrakt wygasł, a auto nie ma zapasowego łańcucha.

ISO 15118-2 (wg josev):
1. `CertificateInstallationReq`: `Id`, `OEMProvisioningCert` (do 800 B), `ListOfRootCertificateIDs`.
2. SECC przekazuje żądanie dalej (OCPP, niżej) i odsyła `CertificateInstallationRes`:
   `SAProvisioningCertificateChain` (CPS), `ContractSignatureCertChain`, `ContractSignatureEncryptedPrivateKey`,
   `DHpublickey`, `eMAID`.
3. Klucz prywatny kontraktu jedzie zaszyfrowany kluczem uzgodnionym przez DH. Stacja i CSMS **nie widzą klucza
   w postaci jawnej** — nie loguj ładunku EXI poza zaszyfrowanymi polami, bo zawiera materiał kluczowy.

ISO 15118-20 (wg josev): `CertificateInstallationReq` z `OEMProvisioningCertificateChain`, `ListOfRootCertificateIDs`,
`MaximumContractCertificateChains` (0–65535) i opcjonalnymi `PrioritizedEMAIDs`. Odpowiedź: `EVSEProcessing`,
`CPSCertificateChain`, `SignedInstallationData` (łańcuch kontraktu, krzywa ECDH, klucz DH, zaszyfrowany klucz
prywatny: SECP521, X448 albo TPM) i `RemainingContractCertificateChains`. Usługa jest ogłaszana flagą
`CertificateInstallationService` w `AuthorizationSetupRes`.

W obu wersjach auto trzyma kilka łańcuchów (`maxContractCerts` = 3 w README josev dla EVCC).

## 4. Aktualizacja certyfikatu kontraktu
- ISO 15118-2: `CertificateUpdateReq` zawiera obecny łańcuch kontraktu, `eMAID` i listę korzeni; odpowiedź ma te
  same pola co instalacja oraz `RetryCounter` (−1 lub 0–32767), którym backend prosi o ponowienie.
- ISO 15118-20: osobnego komunikatu update nie ma (w josev tylko `CertificateInstallation`) — odnowienie jest
  kolejną instalacją; `RemainingContractCertificateChains` informuje, ile łańcuchów auto jeszcze może przyjąć.
- Odnawiaj przed wygaśnięciem, nie po: wygasły kontrakt nie przejdzie `PaymentDetails`/`Authorization`, a auto bez
  ważnego łańcucha spada na EIM.

## 5. OCPP 2.0.1 — przeniesienie przez CSMS (żądania i odpowiedzi wg schematów)
```
EV --CertificateInstallationReq (EXI)--> stacja
stacja --Get15118EVCertificate {iso15118SchemaVersion, action: Install, exiRequest (base64)}--> CSMS
CSMS --> eMSP/CPS (wewnętrzny kanał lub hub)
CSMS --Get15118EVCertificate response {status, exiResponse (base64)}--> stacja
stacja --CertificateInstallationRes (EXI)--> EV
```
`action` = `Install` lub `Update` (odpowiada `CertificateInstallation`/`CertificateUpdate` z -2). Stacja **nie
dekoduje** ładunku; CSMS przekazuje EXI do CPS bez zmian. Cała ścieżka musi zmieścić się w 5 s okna auta.

Pozostałe komunikaty:
| Komunikat | Rola |
|---|---|
| `Authorize` | `idToken` typu `eMAID` + `certificate` (PEM, do 5500 znaków) lub `iso15118CertificateHashData` (do 4 wpisów: `hashAlgorithm` SHA256/384/512, `issuerNameHash`, `issuerKeyHash`, `serialNumber`, `responderURL`); odpowiedź ma `idTokenInfo` i `certificateStatus` (m.in. Accepted, CertificateExpired, CertificateRevoked, CertChainError, SignatureError, NoCertificateAvailable, ContractCancelled) |
| `SignCertificate` / `CertificateSigned` | `csr` → `certificateChain` (do 10000 znaków); `certificateType`: certyfikat stacji (OCPP, TLS profil 3) albo `V2GCertificate` (SECC, TLS z autem) |
| `InstallCertificate` | wgranie korzenia: V2G Root, MO Root, CSMS Root, korzeń producenta |
| `GetInstalledCertificateIds`, `DeleteCertificate` | inwentarz i usuwanie; usunięcie korzenia MO wyłącza PnC dla jego kontraktów |
| `GetCertificateStatus` | stacja prosi CSMS o status OCSP certyfikatu (`ocspRequestData`) — schemat 2.0.1 |
| `TriggerMessage` | wymuszenie `SignCertificate`/`SignChargingStationCertificate` |
| `NotifyEVChargingNeeds` | `evseId`, `chargingNeeds` (tryb: DC, AC_single_phase, AC_two_phase, AC_three_phase; limity, `departureTime`) → `SetChargingProfile` (dom-ev-smart-charging) |

Konfiguracja w Device Model (komponent `ISO15118Ctrlr`; nazwy zmiennych **[do weryfikacji]**): włączenie PnC,
instalacji kontraktu, centralnej walidacji kontraktu, walidacji offline, czasu podglądu OCSP. Obsługę `Authorize`
i Device Model opisuje dom-ev-ocpp-2x; tu tylko, co z tego wynika dla sesji auta.

Odpowiedzialność za weryfikację kontraktu:
| Wariant | Kto sprawdza łańcuch i OCSP | Skutek |
|---|---|---|
| lokalnie na stacji | stacja (korzenie MO w magazynie) | działa offline; stacja musi mieć świeże korzenie i CRL/OCSP |
| centralnie | CSMS lub eMSP po `Authorize` | jedno miejsce prawdy; wymaga łączności i mieści się w pętli `Ongoing` |

## 6. OCPP 1.6 — **[do weryfikacji]**
OCPP 1.6 nie ma natywnych komunikatów PnC. Whitepaper OCA „ISO 15118 Plug & Charge with OCPP 1.6” opisuje te same
operacje (`Authorize`, `Get15118EVCertificate`, `SignCertificate`, `CertificateSigned`, `InstallCertificate`,
`GetCertificateStatus` itd.) jako `DataTransfer` z identyfikatorem dostawcy OCA i `messageId` równym nazwie operacji.
Dokładny `vendorId`, nazwy i mapowanie pól sprawdź w whitepaperze (dokument nie jest w bazie). Praktyka:
sprawdź, czy firmware stacji w ogóle implementuje ten profil; często oferuje własne rozszerzenie producenta.
Mieszana flota 1.6 + 2.x: dom-ev-ocpp-2x.

## 7. Weryfikacja kontraktu i OCSP
Co sprawdza się po drodze (katalog kontroli, nie wymóg normy):
1. łańcuch kończy się zaufanym korzeniem (MO lub V2G Root w magazynie);
2. okresy ważności wszystkich ogniw względem czasu **stacji**;
3. podpis wyzwania `GenChallenge` (16 B) kluczem kontraktu;
4. status unieważnienia (OCSP) — hash wystawcy, hash klucza, numer seryjny, URL respondera;
5. kontrakt powiązany z aktywnym EMAID u eMSP (dom-ev-ocpi Tokens; format: dom-ev-identifiers).
Gdy OCSP jest nieosiągalny, polityka (przyjąć z ostrzeżeniem czy odrzucić) to decyzja CPO i eMSP; zapisz ją i
testuj. Skrypt josev wspomina tylko „OCSP stapling” (JEP 249 w Javie) — nie opisuje samego protokołu.

## 8. EIM kontra PnC
| Aspekt | EIM / `ExternalPayment` | PnC / `Contract` / `PnC` |
|---|---|---|
| Tożsamość | RFID, aplikacja, terminal | certyfikat w aucie |
| Zależność od PKI | brak | pełna (V2G, MO, OEM) |
| Obsługa w DIN 70121 | tak | nie |
| W OCPP | `Authorize` z tokenem RFID lub `RequestStartTransaction`/OCPI `START_SESSION` | `Authorize` z eMAID i certyfikatem |
| Wartość `AuthEnum` w josev | -20: `EIM`; -2: `ExternalPayment` | -20: `PnC`; -2: `Contract` |
Sesja może zacząć od PnC i po odrzuceniu zakończyć się bez ładowania; automatycznego powrotu do EIM w tej samej
sesji nie zakładaj — auto musi ponownie negocjować (zachowanie zależy od modelu **[do weryfikacji]**).

## 9. Awarie krok po kroku
| Objaw w logu | Przyczyna | Co zrobić |
|---|---|---|
| SDP bez odpowiedzi | brak adresu link-local na interfejsie SECC, Docker z siecią wewnętrzną, brak PLC | sprawdź IPv6 link-local; w kontenerze tryb sieci hosta (README josev) |
| `Failed_NoNegotiation` | brak wspólnego `ProtocolNamespace`/wersji | dodaj DIN lub -2 w SECC |
| TLS: `certificate expired` po stronie auta | liść SECC (w teście 60 dni) lub sub-CA wygasły | `SignCertificate` ponownie; alarm na 14 dni przed końcem |
| TLS: `unable to get local issuer` | SECC nie wysłała sub-CA (zły plik łańcucha) | złóż łańcuch liść + sub-CA2 + sub-CA1 |
| błędny czas stacji | brak NTP po restarcie, bateria RTC | synchronizuj czas; auto ocenia ważność certyfikatów wg czasu z SECC lub własnego **[do weryfikacji]** |
| `Authorize` → `CertificateExpired` | kontrakt po terminie | uruchom `Get15118EVCertificate` z `Update` (-2) lub instalację (-20) |
| `Authorize` → `CertChainError`/brak korzenia | w magazynie stacji brak MO Root eMSP | `InstallCertificate` korzenia, sprawdź `GetInstalledCertificateIds` |
| `CertificateRevoked` / `ContractCancelled` | kontrakt unieważniony u eMSP | kierowca korzysta z EIM; zgłoszenie do eMSP |
| OCSP timeout | responder niedostępny, firewall | polityka offline, cache odpowiedzi, monitoring URL |
| instalacja kontraktu trwa > 5 s | wolny CPS, łańcuch hub–eMSP | mierz każdy przeskok; w -20 użyj `Ongoing` |
| powtarzające się sesje bez PnC, a z kartą OK | PnC wyłączone w konfiguracji stacji lub CSMS | Device Model, `ISO15118Ctrlr` |

## 10. Fallback
- Brak SLAC/SDP: po `sdpRetryCycles` auto wraca do ładowania „nominalnym PWM” (README josev) — AC pójdzie z
  prądem z CP (dom-ev-charger-hardware), DC wymaga komunikacji i nie ruszy.
- Brak wspólnego protokołu: stacja z DIN i -2 prowadzi sesję w DIN, ale **bez PnC**.
- PnC odrzucone: kierowca przechodzi na EIM; w komunikacie dla klienta wskaż przyczynę (kontrakt, nie auto).
- Rejestruj w logu stacji: negocjowany protokół, wybraną opcję autoryzacji, wynik `Authorize`, czas
  `Get15118EVCertificate` — bez tego awarii PnC nie odtworzysz (dom-ev-diagnostics, dom-ev-simulation-testing).
