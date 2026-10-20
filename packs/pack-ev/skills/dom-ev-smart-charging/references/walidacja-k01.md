# Walidacja profili przy SetChargingProfile (K01, libocpp)

Źródło: libocpp `doc/v2/ocpp_201_smart_charging_in_depth.md`, sekcja K01 (L258-318 w
`.claude/knowledge/everest-libocpp-smart-charging/doc.txt`), github.com/EVerest/libocpp, pobrane 2026-10-20 (ranga W).
Numery `K01.FR.x` podaje libocpp; ich treści w specyfikacji OCA nie ma w bazie **[do weryfikacji w spec]**.
Błąd walidacji kończy się odpowiedzią `Rejected`; nazwy poniżej to kody libocpp, nie pola ramki.
Przed odpowiedzią stacja sprawdza też, czy `SmartChargingCtrlrAvailable` jest włączone (inaczej błąd `NotSupported`).

| Kod libocpp | Gdy | Wymaganie |
|---|---|---|
| `ChargingProfileFirstStartScheduleIsNotZero` | pierwszy `startPeriod` ≠ 0 | K01.FR.31 |
| `ChargingProfileNoChargingSchedulePeriods` | brak okresów | — |
| `ChargingSchedulePeriodsOutOfOrder` | `startPeriod` nie rosną | K01.FR.35 |
| `ChargingScheduleChargingRateUnitUnsupported` | jednostka spoza `ChargingScheduleChargingRateUnit` | K01.FR.26 |
| `ChargingSchedulePeriodInvalidPhaseToUse` | zły `phaseToUse` | K01.FR.19, K01.FR.48 |
| `ChargingSchedulePeriodPhaseToUseACPhaseSwitchingUnsupported` | `phaseToUse` bez `ACPhaseSwitchingSupported` | K01.FR.20, K01.FR.48 |
| `ChargingProfileMissingRequiredStartSchedule` | `Absolute`/`Recurring` bez `startSchedule` | K01.FR.40 |
| `ChargingProfileExtraneousStartSchedule` | `Relative` z `startSchedule` | K01.FR.41 |
| `ChargingStationMaxProfileCannotBeRelative` | sufit stacji jako `Relative` | K01.FR.38 |
| `ChargingStationMaxProfileEvseIdGreaterThanZero` | sufit stacji z `evseId` > 0 | K01.FR.03 |
| `InvalidProfileType` | do slotu sufitu stacji trafia inny cel | — |
| `EvseDoesNotExist` | nieznany `evseId` | K01.FR.28 |
| `ExistingChargingStationExternalConstraints` | `ExternalConstraints` z już istniejącym `id` | K01.FR.05 |
| `TxProfileEvseIdNotGreaterThanZero` | `TxProfile` z `evseId` = 0 | K01.FR.16 |
| `TxProfileMissingTransactionId` | `TxProfile` bez `transactionId` | K01.FR.03 |
| `TxProfileEvseHasNoActiveTransaction` | brak aktywnej transakcji na EVSE | K01.FR.09 |
| `TxProfileTransactionNotOnEvse` | nieznany `transactionId` | K01.FR.33 |
| `TxProfileConflictingStackLevel` | ten sam `stackLevel` i `transactionId` w innym `TxProfile` | K01.FR.39 |

## Jak użyć w CSMS
- Waliduj te same reguły przed wysłaniem; błąd odkryty lokalnie nie kosztuje ramki ani sesji bez limitu.
- `composite_schedule.py` sprawdza podzbiór (kolejność okresów, `startSchedule`, `Relative` w sufitach, `recurrencyKind`);
  warunki stanowe (aktywna transakcja, konflikt `stackLevel`) zna tylko stacja i CSMS.
- Po `Rejected` nie ponawiaj tej samej ramki: odczytaj stan (`GetCompositeSchedule`), popraw profil, wyślij nowy.
- Przy wymianie profilu o tym samym `id` i celu stacja zastępuje stary (1.6 i 2.0.1) **[do weryfikacji w spec]**;
  `ExternalConstraints` o istniejącym `id` jest odrzucane (K01.FR.05).
