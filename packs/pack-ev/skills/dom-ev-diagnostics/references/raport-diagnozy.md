# Raport diagnozy

## Format
Pierwsza linia raportu: `Diagnoza: <objaw w jednym zdaniu> — stacja <id>`. Sekcje w tej kolejności:

1. **Objaw** — co zgłoszono, od kiedy, kogo dotyczy (stacja/złącze/token/sieć).
2. **Zakres dowodów** — jakie logi i okno czasu przeanalizowano, wersja OCPP, czego brakuje.
3. **Oś czasu** — tabela: czas (UTC) · źródło (plik:linia lub `messageId`) · zdarzenie. Tylko fakty z logu.
4. **Przyczyna** — jedno zdanie + **dowód** (plik:linia lub ramka z `messageId`). Przyczyna źródłowa bez dowodu
   jest oznaczona **[założenie]**.
5. **Wykluczone hipotezy** — co sprawdzono i czym obalono (krótko).
6. **Kroki naprawy** — numerowane; przy komendach zdalnych: cel, skutek, ryzyko, cofnięcie i **akceptacja człowieka**.
7. **Weryfikacja** — po czym poznamy, że naprawione (np. BootNotification `Accepted`, `Available`, CDR z energią X).
8. **Odchylenie producenta** — wpis, jeśli stacja łamie specyfikację (format niżej); inaczej „brak”.
9. **Skutki dla rozliczeń/klientów** — sesje, CDR, eMSP, które wymagają korekty.

## Wpis odchylenia producenta
Zapisuj w jednym miejscu (np. `docs/project/` lub rejestr odchyleń sieci), żeby rozwiązania obejściowe nie rozlewały
się po kodzie:

| Pole | Treść |
|---|---|
| Producent / model / firmware | z `BootNotification` |
| Zachowanie zgodne ze specyfikacją | co powinno być (wersja OCPP, komunikat) — **[do weryfikacji]** w specyfikacji OCA |
| Zachowanie stacji | co faktycznie jest, z ramką-dowodem (plik:linia / `messageId`) |
| Skutek | co psuje po stronie CSMS lub rozliczeń |
| Obejście | co zrobiono i gdzie (jeden moduł/adapter) |
| Zgłoszenie do producenta | numer, data, odpowiedź |
| Warunek usunięcia obejścia | wersja firmware, w której poprawiono |

## Przykład wypełniony (dane przykładowe)
```
Diagnoza: sesje na PL-A-007 wiszą po zaniku zasilania — stacja PL-A-007 (złącze 1)

Objaw: od 2026-10-18 trzy sesje zostają „aktywne” po restarcie stacji; token kierowców dostaje ConcurrentTx.
Zakres dowodów: log bramy 2026-10-18 00:00 – 2026-10-20 08:00, OCPP 1.6 (--ocpp 1.6); brak logów producenta.

Oś czasu (UTC):
| czas | źródło | zdarzenie |
| 2026-10-19 21:40:11 | log.jsonl:1480 | MeterValues, złącze 1, transakcja 4521 |
| 2026-10-19 21:52:03 | log.jsonl:1502 | BootNotification (reboot) bez wcześniejszego StopTransaction |
| 2026-10-19 21:52:05 | log.jsonl:1504 | StatusNotification złącze 1: Available |

Przyczyna: stacja nie wysyła StopTransaction dla transakcji 4521 po restarcie (log.jsonl:1502–1504); CSMS nie
zamyka sesji po Available na złączu. Pierwotna przyczyna restartu (zasilanie) — [założenie].
Wykluczone: odrzucenie ramki Stop przez CSMS (brak callerror w oknie), offline (Heartbeaty ciągłe).
Kroki naprawy: 1. Zamknąć transakcje 4521, 4533, 4540 jako „zakończone szacunkowo” z energią ostatniego MeterValues
 (decyzja o rozliczeniu: człowiek). 2. Dodać w CSMS regułę zamknięcia po BootNotification + Available (test na
 ramkach z log.jsonl:1502–1504). 3. Zgłosić producentowi.
Weryfikacja: kolejny restart testowej stacji kończy sesję w CSMS bez ręcznej interwencji.
Odchylenie producenta: model/firmware z BootNotification — brak StopTransaction po utracie zasilania (obejście: reguła w adapterze 1.6).
Skutki: 3 sesje, CDR do wystawienia jako szacunkowe; uzgodnić z eMSP (dom-ev-session-lifecycle).
```

## Jakość dowodu
| Poziom | Przykład | Jak oznaczyć |
|---|---|---|
| Bezpośredni | ramka w logu z numerem linii | plik:linia, `messageId` |
| Pośredni | brak ramki w oknie logu | „brak X w oknie A–B” + sprawdzenie, że brama zapisuje ten typ ramek |
| Założenie | przyczyna wynikająca z wiedzy ogólnej | **[założenie]** + co by je potwierdziło |
