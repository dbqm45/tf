# Operacje OICP 2.3 — szczegóły

Spis: [Wdrożenie po stronie EMP](#wdrożenie-po-stronie-emp) · [Kody statusu](#kody-statusu) ·
[Zmiany w 2.3](#zmiany-w-23) · [Pola obowiązkowe 2.1 / 2.2 / 2.3](#pola-obowiązkowe) · [Powiadomienia i ceny](#powiadomienia-i-ceny)

Źródło: OICP 2.3 EMP i CPO (`.claude/knowledge/oicp/doc.txt`, github.com/hubject/oicp, pobrane 2026-10-20). Opis własnymi słowami.

## Wdrożenie po stronie EMP
| Operacja | Kierunek EMP | Wdrożenie wg specyfikacji |
|---|---|---|
| `eRoamingPullEvseData` | wysyła | obowiązkowe |
| `eRoamingPullEvseStatus` (+ByID do 100 EVSE, +ByOperatorID) | wysyła | obowiązkowe |
| `eRoamingPushAuthenticationData` | wysyła | obowiązkowe (usługa tylko po stronie Hubject) |
| `eRoamingAuthorizeRemoteStart/Stop` | wysyła | obowiązkowe |
| `eRoamingAuthorizeStart/Stop` | odbiera i odpowiada | zależnie od modelu: EMP online odpowiada na zapytania huba |
| `eRoamingChargeDetailRecord` | odbiera | obowiązkowe tylko dla EMP online |
| `eRoamingGetChargeDetailRecords` | wysyła | EMP offline obowiązkowe, online opcjonalne |
| `eRoamingChargingNotifications` | odbiera | opcjonalne |
| `eRoamingPullPricingProductData`, `eRoamingPullEVSEPricing` | wysyła | opcjonalne |

EMP „online” odpowiada hubowi na żywo (autoryzacja, CDR); EMP „offline” wypycha dane uwierzytelniające do huba,
a CDR pobiera sam. Rozróżnienie wynika ze specyfikacji; szczegóły kontraktowe ustal z hubem [do weryfikacji].

## Kody statusu
Wybrane z `CodeType` (pole `StatusCode` w odpowiedziach, w tym `eRoamingAcknowledgement`):

| Kod | Znaczenie | Typowa przyczyna |
|---|---|---|
| 000 | sukces | — |
| 017 | Unauthorized Access | ID partnera niezgodne z certyfikatem klienta |
| 018 | Inconsistent EvseID | EVSE w pushu nie pasuje do OperatorID lub pod-operatora |
| 019 | Inconsistent EvcoID | EvcoID niezgodne z ProviderID |
| 101–122 | błędy uwierzytelnienia (QR, RFID, Plug & Charge) | zły PIN, UID, certyfikat, time-out |
| 200 | EvcoID locked | kontrakt zablokowany |
| 210 | No valid contract | brak kontraktu CPO–EMP dla usługi |
| 300 / 310 / 320 | partner nie znaleziony / nie odpowiedział / usługa niedostępna | routing huba |
| 400 | Session is invalid | zły lub obcy SessionID |
| 501 / 510 | brak komunikacji z EVSE / brak EV | zdalny start |
| 601 / 602 | EVSE zarezerwowany / w użyciu lub zły token | zdalny start, rezerwacja |
| 603 / 604 | nieznany EVSE ID / EVSE niezgodny z Hubject | `IsHubjectCompatible = false` |
| 700 | EVSE out of service | status EVSE |

Do logiki obsługi bierz kod, a nie opis; pole `AdditionalInfo` jest dla człowieka. Status EVSE (`EvseStatusType`):
`Available`, `Reserved`, `Occupied`, `OutOfService`, `EvseNotFound`, `Unknown`.

## Zmiany w 2.3
Wersje operacji: `ChargeDetailRecord` i `GetChargeDetailRecord` 2.1→2.2, `PushEvseData` i `PullEvseData` 2.2→2.3,
`ChargingNotification` 1.0→1.1.

- **CDR:** usunięte `MeteringSignature`; nowe `SignedMeteringValues` i `CalibrationLawVerificationInfo`
  (typy `SignedMeteringValuesType`, `CalibrationLawVerificationType`); obowiązkowe `ChargingStart`, `ChargingEnd`,
  `ConsumedEnergy`. Powód: przepisy o legalizacji w Niemczech — dane do weryfikacji sesji przez klienta
  (`dom-ev-charger-hardware` o liczniku MID i Eichrecht; formaty podpisu: źródło `ocmf` w bazie).
- **GetChargeDetailRecords:** nowe filtry `SessionID`, `OperatorID`, `CDRForwarded`; paginacja (domyślnie 20,
  maksimum 2000 na stronę).
- **EVSE Data:** paginacja pull (`page`, `size`, domyślnie 20), nowy typ `PullEvseDataRecordType`, w odpowiedzi
  nie ma już `OperatorEvseData`; `ChargingStationNames` (typ `InfoTextType`) zastępuje `ChargingStationName`;
  `ChargingModes` przeniesione do `ChargingFacilityType`; wartości „Unspecified” nie są przyjmowane w push (w pull
  stare dane wracają jako `null`); nowe pola m.in. `HardwareManufacturer`, `SubOperatorName`, `RenewableEnergy`,
  `EnergySource`, `CalibrationLawDataAvailability`, `DynamicPowerLevel`, `AccessibilityLocation`.
- **ChargingNotification:** nowe `ChargingDuration`, `ConsumedEnergyProgress`, `PenaltyTimeStart`, `ErrorType`,
  `ErrorAdditionalInfo`; klasy błędu (`ErrorClassType`): `Connector Error`, `Critical Error`.

## Pola obowiązkowe
Różnice, które psują integrację z partnerem na starszej wersji (O = opcjonalne, M = obowiązkowe):

| Pole | 2.1 | 2.2 | 2.3 |
|---|---|---|---|
| `OperatorName`, `ChargingStationName(s)` | O | O | M |
| `HouseNum`, `PostalCode` (adres) | O | O | M |
| `Power`, `PowerType` (ChargingFacilities) | O | O | M |
| `PaymentOptions` | O | O | M |
| `RenewableEnergy`, `CalibrationLawDataAvailability` | — | — | M |
| `ChargingStart`, `ChargingEnd` (CDR) | O | O | M |

EMP na 2.3 może więc dostać `null` z pull dla rekordów wypchniętych przez CPO na 2.1/2.2. Model wewnętrzny musi
dopuszczać brak tych pól po stronie odbioru.

## Powiadomienia i ceny
- `ChargingNotifications` typu Start, Progress, End, Error; Progress nie częściej niż co 5 minut na sesję. Hub przekazuje
  EMP i odsyła jego `Acknowledgement` do CPO. Nie zastępuje CDR.
- `DynamicPricing` (od 2.2): CPO wypycha produkty cenowe (`PricingProductData`) i przypisuje je do EVSE
  (`EVSEPricing`); EMP pobiera tylko od CPO, z którymi ma kontrakt cenowy (filtr `LastCall` dla zmian). W CDR i
  `AuthorizeStart` identyfikuje taryfę `PartnerProductID`; zalecane wartości, gdy ceny są zróżnicowane: `AC1`,
  `AC3`, `DC`, `Free`. Liczenie ceny z produktu: `dom-ev-tariffs-pricing`.
