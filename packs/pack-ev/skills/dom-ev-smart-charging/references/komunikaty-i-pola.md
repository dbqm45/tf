# Komunikaty smart charging — pola wg schematów JSON

Źródło pól: schematy JSON `mobilityhouse/ocpp` (`.claude/knowledge/ocpp-json-schemas/doc.txt`: 1.6 SetChargingProfile
L1-125, GetCompositeSchedule L126-233; 2.0.1 SetChargingProfileRequest L234-608, GetCompositeScheduleResponse L609-765,
NotifyChargingLimitRequest L766-1087), pobrane 2026-10-20, ranga W. Schematów `ClearChargingProfile`,
`GetChargingProfiles`, `ReportChargingProfiles`, `ClearedChargingLimit` i `GetCompositeScheduleRequest` 2.0.1 nie ma
w bazie — pola oznaczone **[do weryfikacji w spec]**. Nazwy w oryginale; znaczenia własnymi słowami.

## 1. SetChargingProfile
**1.6** — `connectorId` (wymagane) + `csChargingProfiles` (wymagane): `chargingProfileId`, `stackLevel`,
`chargingProfilePurpose`, `chargingProfileKind`, `chargingSchedule` (wymagane); opcjonalnie `transactionId` (liczba),
`recurrencyKind` (`Daily`/`Weekly`), `validFrom`, `validTo`. `chargingSchedule`: `chargingRateUnit` i
`chargingSchedulePeriod` wymagane; `duration`, `startSchedule`, `minChargingRate` opcjonalne. Okres: `startPeriod`,
`limit` (krok 0,1), `numberPhases`. Odpowiedź (nie ma w bazie): `Accepted`/`Rejected`/`NotSupported` **[do weryfikacji w spec]**.

**2.0.1** — `evseId` + `chargingProfile` (wymagane oba). Profil: `id`, `stackLevel`, `chargingProfilePurpose`,
`chargingProfileKind`, `chargingSchedule` (**lista 1-3 harmonogramów**; kolejne dotyczą ISO 15118) wymagane;
opcjonalnie `recurrencyKind`, `validFrom`, `validTo`, `transactionId` (tekst do 36 znaków). Harmonogram: `id`,
`chargingRateUnit`, `chargingSchedulePeriod` (1-1024 okresów) wymagane; `startSchedule`, `duration`,
`minChargingRate`, `salesTariff` opcjonalne. Okres: `startPeriod`, `limit`, `numberPhases`, `phaseToUse`.
- `evseId` = 0: `TxDefaultProfile` dotyczy każdego EVSE osobno; `ChargingStationMaxProfile` i
  `ChargingStationExternalConstraints` to limit całej stacji (opis w schemacie).
- `startPeriod` to sekundy od początku harmonogramu i zarazem koniec poprzedniego okresu.
- `salesTariff` (taryfa cenowa dla pojazdu, ISO 15118) — poza tym skillem; taryfy rozliczeniowe: dom-ev-tariffs-pricing.

## 2. GetCompositeSchedule
**1.6 żądanie:** `connectorId`, `duration` (wymagane), `chargingRateUnit` (opcjonalnie). **Odpowiedź:** `status`
(`Accepted`/`Rejected`) wymagane; `connectorId`, `scheduleStart`, `chargingSchedule` (jak wyżej).
**2.0.1 odpowiedź:** `status` (`Accepted`/`Rejected`), `statusInfo` (`reasonCode`, `additionalInfo`), `schedule`:
`evseId`, `duration`, `scheduleStart`, `chargingRateUnit`, `chargingSchedulePeriod` (wszystko wymagane). Żądanie
2.0.1: `duration`, `evseId`, `chargingRateUnit` opcjonalnie **[do weryfikacji w spec]**.
`scheduleStart` to punkt, względem którego liczą się wszystkie `startPeriod` odpowiedzi.

## 3. ClearChargingProfile i GetChargingProfiles
Według diagramów libocpp (K09, K10):
- `ClearChargingProfile`: stacja usuwa profile pasujące do kryteriów; brak pasujących → `Unknown`, inaczej `Accepted`.
  Kryteria (id profilu, cel, `stackLevel`, `evseId`) **[do weryfikacji w spec]**. W 1.6 podobnie (`id`, `connectorId`,
  `chargingProfilePurpose`, `stackLevel`) **[do weryfikacji w spec]**.
- `GetChargingProfiles` (2.0.1): filtr po kryteriach; brak profili → `NoProfiles`; w przeciwnym razie `Accepted`,
  a profile stacja wysyła osobnym `ReportChargingProfiles` (z `requestId` żądania **[do weryfikacji w spec]**).
  W 1.6 nie ma tego komunikatu; stan odczytujesz tylko przez `GetCompositeSchedule` — zapisz więc u siebie, co wysłałeś.

## 4. NotifyChargingLimit (2.0.1, stacja → CSMS)
Wymagane: `chargingLimit` {`chargingLimitSource` — `EMS`, `Other`, `SO`, `CSO`; `isGridCritical` opcjonalne}. Opcjonalne:
`evseId` (> 0) i `chargingSchedule` (lista, min. 1). Stacja zgłasza limit narzucony z zewnątrz (lokalny EMS, operator
sieci) i harmonogram, który z niego wynika. Gdy limit ustaje, służy temu `ClearedChargingLimit` **[do weryfikacji w spec]**.
CSMS powinien zapisać źródło i `isGridCritical`, bo limit krytyczny dla sieci ma pierwszeństwo przed celami komercyjnymi.

## 5. Różnice 1.6 i 2.0.1 (skrót)
| Temat | 1.6 | 2.0.1 |
|---|---|---|
| Adres | `connectorId` (0 = stacja) | `evseId` (0 = stacja) |
| Id profilu | `chargingProfileId` | `id` |
| `transactionId` | liczba | tekst ≤ 36 |
| Harmonogramy w profilu | jeden | lista 1-3 |
| Limit zewnętrzny | brak | `ExternalConstraints`, `NotifyChargingLimit` |
| Fazy | `numberPhases` | + `phaseToUse` |
| Odczyt profili | tylko composite | + `GetChargingProfiles` |
