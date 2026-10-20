# Sesja ISO 15118 i DIN 70121 — kolejność komunikatów i timeouty

> **Spis treści:** 1. Uwaga o źródłach · 2. Timeouty (wg josev) · 3. Pętle i stan `Ongoing` · 4. Sesja DC · 5. Sesja AC · 6. Transport · 7. Co z tego wynika dla CSMS

Spis treści: 1. Uwaga o źródłach · 2. Timeouty · 3. Pętle i stan `Ongoing` · 4. Sesja DC · 5. Sesja AC · 6. Transport ·
7. Co z tego wynika dla CSMS.

## 1. Uwaga o źródłach
Wszystkie liczby i nazwy pochodzą z implementacji **josev** (SwitchEV/iso15118, ranga W, pobrane 2026-10-20),
pliki timeouts.py (wspólny, `iso15118_2`, `iso15118_20`, `din_spec`). To kod, a nie norma: wartość w kodzie może
różnić się od wymagania normy lub od zachowania konkretnego auta. Numery wymagań normy (np. tabele 75, 77 w DIN)
josev podaje tylko w komentarzach; samej normy nie ma w bazie, więc wymagania normatywne to **[do weryfikacji]**.
Jednostka: sekundy.

## 2. Timeouty (wg josev)
**Wspólne (-2 i -20):** SDP 0,25 · SupportedAppProtocol 2 · `V2G_EVCC_COMMUNICATION_SETUP_TIMEOUT` 20 ·
`V2G_SECC_SEQUENCE_TIMEOUT` 60 · `V2G_EVCC_ONGOING_TIMEOUT` 60.

| Komunikat / pętla | DIN 70121 | ISO 15118-2 | ISO 15118-20 |
|---|---|---|---|
| SessionSetup | 2 | 2 | 2 |
| ServiceDiscovery | 2 | 2 | 2 |
| ServiceDetail | — | 5 | 5 |
| PaymentServiceSelection / ServicePaymentSelection / ServiceSelection | 2 | 2 | 2 |
| AuthorizationSetup | — | — | 2 |
| ContractAuthentication (DIN) / Authorization | 2 | 2 | 2 |
| PaymentDetails | — | 5 | — |
| CertificateInstallation | — | 5 | 5 |
| CertificateUpdate | — | 5 | — (brak komunikatu) |
| ChargeParameterDiscovery | 2 | 2 | 2 |
| ScheduleExchange | — | — | 2 |
| PowerDelivery | 2 | 5 | 2 |
| CableCheck | 2 | 2 | 2 (DC_CableCheck) |
| PreCharge | 2 | 2 | 2 (DC_PreCharge) |
| CurrentDemand | 0,25 | 0,25 | — |
| ChargingStatus | — | 2 | — |
| AC_ChargeLoop / DC_ChargeLoop | — | — | 0,5 |
| MeteringReceipt / MeteringConfirmation | — | 2 | 2 |
| WeldingDetection | 2 | 2 | 2 |
| SessionStop | 2 | 2 | 2 |

**Pętle całościowe (po stronie auta):**
| Pętla | DIN 70121 | ISO 15118-2 | ISO 15118-20 |
|---|---|---|---|
| CableCheck (łącznie) | 40 | 40 | 40 |
| PreCharge (łącznie) | 7 | 7 | 10 |
| ReadyToCharge | 150 | — | — |
| Wykrycie stanu CP po stronie SECC | 1,5 | — | — |
| Podtrzymanie oscylatora CP po stronie SECC | 1,5 | — | — |

Dodatkowo -20 definiuje timeouty komunikatów ACD (pantograf) 2 s, WPT i `VehicleCheckIn/Out` 2 s — poza zakresem
tego skilla.

## 3. Pętle i stan `Ongoing`
- `Authorization` ma timeout 2 s, a weryfikacja kontraktu (OCSP, odpytanie CSMS) trwa dłużej. Rozwiązanie z normy
  (wg komentarza josev): SECC odpowiada `Ongoing`, a auto **wysyła to samo żądanie ponownie**. SECC musi więc
  obsługiwać wielokrotne `Authorization` bez ponownego liczenia. W DIN dozwolone tylko `Accepted` i `Rejected`.
- `ChargeParameterDiscovery` (-2, DIN) i `CableCheck` używają `EVSEProcessing` = `Ongoing`/`Finished` w pętli;
  sesja kończy pętlę dopiero po `Finished` albo po limicie pętli (40 s dla `CableCheck`).
- W -20 `CertificateInstallationRes` ma `EVSEProcessing`, w -2 `CertificateInstallationRes` go nie ma — odpowiedź
  musi zmieścić się w jednym oknie 5 s.
- `V2G_SECC_SEQUENCE_TIMEOUT` (60 s) liczy czas bezczynności po stronie SECC: brak następnego żądania auta
  zamyka sesję.

## 4. Sesja DC
| Krok | DIN 70121 | ISO 15118-2 | ISO 15118-20 |
|---|---|---|---|
| 1 | SupportedAppProtocol | SupportedAppProtocol | SupportedAppProtocol |
| 2 | SessionSetup | SessionSetup | SessionSetup |
| 3 | ServiceDiscovery | ServiceDiscovery | AuthorizationSetup |
| 4 | ServicePaymentSelection | PaymentServiceSelection | (CertificateInstallation) |
| 5 | ContractAuthentication | (CertificateInstallation/Update) → PaymentDetails | Authorization (pętla) |
| 6 | ChargeParameterDiscovery | Authorization (pętla) | ServiceDiscovery → ServiceDetail → ServiceSelection |
| 7 | CableCheck | ChargeParameterDiscovery | DC_ChargeParameterDiscovery |
| 8 | PreCharge | CableCheck | ScheduleExchange |
| 9 | PowerDelivery (Start) | PreCharge | DC_CableCheck |
| 10 | CurrentDemand (pętla) | PowerDelivery (Start) | DC_PreCharge |
| 11 | PowerDelivery (Stop) | CurrentDemand (pętla) | PowerDelivery (Start) |
| 12 | WeldingDetection | PowerDelivery (Stop) | DC_ChargeLoop (pętla) |
| 13 | SessionStop | WeldingDetection | PowerDelivery (Stop) |
| 14 | — | SessionStop | DC_WeldingDetection → SessionStop |

Uwagi:
- W -2 `PowerDelivery` ma `ChargeProgress` (Start/Stop/Renegotiate) i, dla DC, `DC_EVPowerDeliveryParameter`.
- W -20 `PowerDeliveryReq` niesie `EVProcessing`; po `Finished` i `ChargeProgress` = `Start` auto musi dołączyć
  `EVPowerProfile` (walidator w josev). `ChargeProgress` w -20: `Start`, `Stop`, `Standby`, `ScheduleRenegotiation`.
- `CableCheck` sprawdza izolację; stany izolacji w josev: `Invalid`, `Valid`, `Warning`, `Fault`, `No_IMD`.
- Błędy po stronie auta w DIN/-2 DC: `DCEVErrorCode`, m.in. `FAILED_RESSTemperatureInhibit`,
  `FAILED_EVShiftPosition`, `FAILED_ChargerConnectorLockFault`, `FAILED_EVRESSMalfunction`,
  `FAILED_ChargingVoltageOutOfRange`, `FAILED_ChargingSystemIncompatibility`.
- Sterowanie mocą DC w -20: tryby `Scheduled` i `Dynamic` w `DC_ChargeLoop`; warianty BPT → dom-ev-v2x.
- Granica napięcia, krzywa i limity baterii: dom-ev-vehicle-battery.

## 5. Sesja AC
| Krok | ISO 15118-2 | ISO 15118-20 |
|---|---|---|
| ... do autoryzacji | jak w tabeli DC | jak w tabeli DC |
| ChargeParameterDiscovery | `ChargeParameterDiscovery` (AC: limity prądu i faz) | `AC_ChargeParameterDiscovery` |
| harmonogram | `SAScheduleList` w odpowiedzi | `ScheduleExchange` |
| start | `PowerDelivery` (Start) | `PowerDelivery` (Start) |
| pętla | `ChargingStatus` (2 s), `MeteringReceipt` | `AC_ChargeLoop` (0,5 s) |
| koniec | `PowerDelivery` (Stop) → `SessionStop` | `PowerDelivery` (Stop) → `SessionStop` |

DIN 70121 nie obejmuje AC. Tryby energii w -2: `AC_single_phase_core`, `AC_three_phase_core`, `DC_core`,
`DC_extended`, `DC_combo_core`, `DC_unique`. W -20 tryb to usługa (AC 1, DC 2, ...), nie `EnergyTransferMode`.
AC bez PnC (EIM) jest zwyczajnym przypadkiem: auto i tak może prowadzić pętlę -2/-20, jeśli stacja ma PLC; bez PLC
ładowanie idzie na samym PWM (dom-ev-charger-hardware).

## 6. Transport
- V2GTP: wersja protokołu `0x01` (`0xFE` = nieprawidłowa); po nagłówku typ ładunku (DIN i -2: EXI `0x8001`;
  -20: SAP `0x8001`, Mainstream `0x8002`, AC `0x8003`, DC `0x8004`, ACDP `0x8005`, WPT `0x8006`; zdarzenia
  `0x8101` ScheduleRenegotiation, `0x8102` MeteringConfirmation).
- TCP lub TLS wg odpowiedzi SDP; w josev `useTls` (preferencja auta) i `enforceTls` (auto akceptuje tylko TLS)
  są ustawieniami EVCC.
- Każdy komunikat to XML kodowany **EXI**; wersje schematu różnią się między DIN, -2 i -20, więc debugowanie wymaga
  dekodera właściwego dla negocjowanego protokołu (SchemaID).

## 7. Co z tego wynika dla CSMS
- Czas na `Authorize` (PnC) wlicza się w pętlę `Authorization`; nie ma sensu odpowiadać po wielu sekundach —
  ładowarka i tak odpowie `Ongoing` w ramach okna.
- `Get15118EVCertificate` w całości musi zmieścić się w 5 s razem z transportem (auto–stacja, stacja–CSMS, CSMS–CPS).
  Mierz każdy przeskok osobno (dom-ev-diagnostics).
- Nie próbuj wywnioskować protokołu z OCPP: wersja protokołu 15118 negocjowana w sesji nie jest w standardowym
  `TransactionEvent` **[do weryfikacji]**; zapisuj ją z logów stacji.
