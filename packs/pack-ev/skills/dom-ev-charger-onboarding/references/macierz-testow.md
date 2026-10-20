# Macierz testów akceptacyjnych i pilotaż

Każdy wiersz: warunki, kroki, oczekiwanie, dowód (log JSON Lines + `ocpp_log_analyze.py`). Test na prawdziwym
egzemplarzu; symulator (**dom-ev-simulation-testing**) uzupełnia, nie zastępuje.

## Macierz
| # | Test | Oczekiwanie | Dowód |
|---|---|---|---|
| T1 | Boot po starcie i po restarcie | `BootNotification` → bramka (Pending/Accepted); dopasowanie vendor/model/firmware | ramka Boot, odpowiedź |
| T2 | Heartbeat | co `interval`; zegar stacji zsynchronizowany z `currentTime` | Heartbeaty; brak `clock-skew` |
| T3 | Sesja RFID: autoryzacja, ładowanie, koniec | sekwencja statusów jak w ocpp-16 (`Preparing`→`Charging`→`Finishing`→`Available`) lub odchylenie w rejestrze; `transactionId` od CSMS (1.6) | statusy, Start/Stop, `meterStart`/`meterStop` |
| T4 | Odrzucony token | stacja nie startuje, status czytelny | `Authorize` z odpowiedzią |
| T5 | Zdalny start i zdalny stop | 1.6 `RemoteStartTransaction`/`RemoteStopTransaction`, 2.0.1 `RequestStartTransaction`/`RequestStopTransaction`; `Accepted` i faktyczny start/stop | odpowiedź + transakcja |
| T6 | Offline i powrót | po zerwaniu sesja trwa; po powrocie ramki zbuforowane z poprawnym czasem, bez duplikatów | brak `duplicate-message-id`, `open-transaction` |
| T7 | Utrata zasilania w trakcie sesji | po starcie: Boot, sesja zamknięta/oznaczona; energia nie ginie | `open-transaction`? sposób zamknięcia |
| T8 | Zgodność energii | kWh na liczniku stacji ↔ `meterStop − meterStart` ↔ sesja w CSMS (Wh vs kWh) | brak `meter-decrease`, różnica w granicach z karty |
| T9 | Aktualizacja firmware | `UpdateFirmware` / 2.0.1: stany z `FirmwareStatusNotification`; po restarcie nowy ciąg w Boot; konfiguracja przeżywa | statusy, Boot po aktualizacji |
| T10 | Zmiana konfiguracji z restartem | `RebootRequired` → po restarcie wartość z odczytu | odczyt przed/po |
| T11 | Smart charging (jeśli deklarowany) | `SetChargingProfile` obniża moc; status `SuspendedEVSE` lub spadek mocy w `MeterValues` | profil + pomiar |
| T12 | Błąd złącza / `Faulted` | status i kod błędu dochodzi do CSMS; po usunięciu przyczyny powrót do `Available` | `StatusNotification` |
| T13 | Połączenie bezpieczne | zerwanie TLS, wygasły certyfikat → stacja nie łączy się bez ważnego certyfikatu (profile 2/3) | log połączenia |
| T14 | Nieznana lub zduplikowana ramka | stacja nie wpada w pętlę ponowień | brak `call-no-response` |

Nazwy kodów błędów i pól — wg **dom-ev-ocpp-16** / **dom-ev-ocpp-2x**; wartości spoza tych skilli:
**[do weryfikacji]** w dokumentacji producenta.

## Kryteria przejścia
- Test krytyczny (T1, T3, T5, T6, T7, T8, T9): musi przejść albo mieć wpis odchylenia z działającym obejściem
  za flagą i powtórzony test z flagą.
- Ustalenia `ocpp_log_analyze.py` o wysokiej wadze (`open-transaction`, `meter-decrease`, `seqno-gap`,
  `call-no-response`) muszą mieć wyjaśnienie w protokole testu.
- Brak testu = „nie sprawdzono”, nie „przeszło”.

## Pilot (jedna stacja)
- Warunki: macierz zakończona, odchylenia z flagami, plan wycofania, osoba dyżurna po stronie serwisu.
- Obserwacja: statusy, sesje osierocone, zgodność kWh, reconnecty, błędy; raport dzienny na początku.
- Wyjście z pilota: kryteria z SKILL.md (krok 9) i podpis człowieka. Progi (liczba sesji, dni, partie floty) —
  **[założenie]**, uzgadniane per projekt.
- Problemy w trakcie: zatrzymaj rollout; diagnoza konkretnej stacji w trakcie pilota — **dom-ev-diagnostics**.

## Wpis w protokole testu
`T7 | stacja <chargePointId> | fw <wersja> | wynik: przeszedł/odchylenie/nie przeszedł | log: <plik> | uwagi`
