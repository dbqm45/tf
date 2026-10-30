---
name: dom-ev-simulation-testing
description: Użyj przy testowaniu CSMS bez prawdziwej ładowarki — symulator stacji OCPP, scenariusze awarii, test obciążeniowy bramy, kontrakt OCPI, regresja na nagranych logach.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba przetestować system ładowania bez fizycznej ładowarki albo przed jej podłączeniem — piramida testów CSMS (ramki, schematy, symulator, ładowarka w laboratorium, pilotaż), symulator OCPP 1.6J uruchamiany z linii poleceń, scenariusze awarii (zerwanie w trakcie sesji, offline i kolejka, duplikat CALL, zły zegar, brak StopTransaction, utrata zasilania, reconnect storm), test obciążeniowy bramy WebSocket, testy kontraktowe OCPI, regresja na nagranych i zanonimizowanych logach, łańcuch symulator → log → analizator. Nie do diagnozy awarii na produkcji (dom-ev-diagnostics), onboardingu nowego modelu ładowarki (dom-ev-charger-onboarding) ani projektu architektury CSMS (dom-ev-cpms-architecture)."
  slowa: "symulator ładowarki, charge point simulator, test CSMS bez ładowarki, nie mamy ładowarki, testy OCPP, test obciążeniowy, load test, 5000 ładowarek, reconnect storm, burza połączeń, wiele połączeń WebSocket, scenariusz awarii, chaos, zerwanie połączenia, offline replay, duplikat CALL, zły zegar, clock skew, brak StopTransaction, utrata zasilania, test kontraktowy OCPI, contract test, regresja na logach, replay, odtwarzanie ramek, anonimizacja idTag, EVerest, SteVe, piramida testów, charge_sim"
---

# Testowanie systemów ładowania bez prawdziwej ładowarki

Skill daje **plan testów i sposób ich uruchomienia**. Tworzysz zachowanie stacji w kodzie, więc możesz je powtarzać,
psuć celowo i mierzyć. Protokół — dom-ev-ocpp-16, dom-ev-ocpp-2x; architektura bramy — dom-ev-cpms-architecture;
diagnoza z logu — dom-ev-diagnostics. Nie rekomenduje produktów.

Sieć: skrypty łączą się tylko z adresem WebSocket podanym w wywołaniu (testy lokalne)

## Piramida testów CSMS
| Poziom | Co sprawdza | Czego nie złapie |
|---|---|---|
| 1. Jednostkowe na ramkach | parser CALL/CALLRESULT/CALLERROR, mapowanie na model domeny, idempotencja | zachowania połączenia i czasu |
| 2. Kontraktowe na schematach | ramka zgodna ze schematem JSON wersji OCPP; kontrakt OCPI z partnerem | kolejności komunikatów |
| 3. Symulator end-to-end | pełna sesja przez prawdziwą bramę, awarie wstrzyknięte | odchylenia konkretnego sprzętu |
| 4. Prawdziwa ładowarka w laboratorium | firmware, zegar, buforowanie offline, odchylenia producenta | skala |
| 5. Pilotaż | prawdziwe sieci GSM, kierowcy, taryfy | powtarzalność |

Zasada: błąd łap na najniższym poziomie, który go widzi. Poziom 3 jest tani i powtarzalny, więc na nim zabezpieczaj
regresje; poziom 4 służy do tego, czego symulator nie odtworzy. Szablon akceptacji nowego modelu — dom-ev-charger-onboarding.

## Procedura
1. **Postaw CSMS lokalnie** (bez TLS, `ws://`). Symulator łączy się tylko z adresem z wywołania.
2. **Uruchom** symulator na scenariuszu bazowym i sprawdź kod wyjścia:
   `python3 .claude/skills/dom-ev-simulation-testing/scripts/charge_sim.py ws://localhost:9000/CP1 --scenario session --log <plik>.jsonl`
3. **Uruchom** scenariusze awarii (tabela niżej), każdy z `--log`.
4. **Uruchom analizator** na logu i porównaj ustalenia z oczekiwanymi:
   `python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py <plik>.jsonl`
5. **Zapisz regresję**: scenariusz + oczekiwane ustalenia trafiają do testów CI. Po poprawce błąd ma zniknąć z logu.
6. Obciążenie i reconnect storm — `references/obciazenie-i-storm.md`; kontrakt OCPI i nagrane logi — `references/kontrakt-ocpi-i-regresja.md`.

## Symulator `charge_sim.py` (OCPP 1.6J, jedno złącze, bez zależności)
Składnia: `charge_sim.py <ws://host:port/ID> [--scenario session|boot] [--id-tag T] [--energy-wh N] [--meter-steps K]
[--fault none|offline-replay|duplicate-message|clock-skew|drop-stop] [--log plik.jsonl] [--timeout S]`.

| Kod wyjścia | Znaczenie |
|---|---|
| 0 | scenariusz przeszedł |
| 1 | CSMS odrzucił komunikat albo nie odpowiedział |
| 2 | błąd wywołania lub połączenia |

- `session`: BootNotification → StatusNotification `Available` → Authorize → StatusNotification `Preparing`/`Charging` →
  StartTransaction → MeterValues ×K → StopTransaction → `Available`. `boot`: tylko rejestracja.
- Log w formacie analizatora: JSON Lines `{ts, cp, dir, frame}`.
- Tylko `ws://`. Do TLS i profili bezpieczeństwa użyj ładowarki z poziomu 4 albo własnego klienta.
- Do własnych testów jest `ocpp_ws.py` (ten sam katalog): minimalny klient i serwer WebSocket (RFC 6455) na asyncio.

## Scenariusze awarii, które musi przejść każdy CSMS
| Scenariusz | Jak wywołać | Oczekiwanie wobec CSMS |
|---|---|---|
| Zerwanie połączenia w trakcie sesji | zabij proces symulatora po StartTransaction | CSMS oznacza stację offline, sesja nie jest zamykana „z głowy” |
| Offline i odtworzenie kolejki | `--fault offline-replay` | zaległe ramki przyjęte, stan liczony z czasu zdarzeń, nie z kolejności odbioru |
| Duplikat CALL | `--fault duplicate-message` | drugi skutek się nie pojawia (idempotencja po stacji i `messageId`); analizator: `duplicate-message-id` |
| Zły zegar | `--fault clock-skew` | czas odbioru zapisany osobno; analizator: `clock-skew` |
| Brak StopTransaction | `--fault drop-stop` | sesja nie wisi bez końca; analizator: `open-transaction` |
| Utrata zasilania | `drop-stop` + ponowne `--scenario boot` tej stacji | po BootNotification CSMS domyka starą transakcję heurystyką albo zgłasza ją operatorowi |
| Reconnect storm | wiele symulatorów naraz (obciążenie) | brama trzyma limit handshake’ów, nie gubi sesji |

Zachowanie ładowarek w offline — dom-ev-ocpp-16 (`.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`).

## Przykład
**Wejście:** „Nie mamy ładowarki. Czy nasz CSMS domyka sesję, gdy ładowarka zniknie przed StopTransaction?”
**Wynik:** (1) postaw CSMS na `ws://localhost:9000`; (2) uruchom
`charge_sim.py ws://localhost:9000/CP1 --fault drop-stop --log <plik>.jsonl` i sprawdź kod wyjścia; (3) uruchom
`ocpp_log_analyze.py <plik>.jsonl` — oczekiwane ustalenie `open-transaction`; (4) sprawdź w CSMS, czy transakcja ma stan
„niedomknięta” i alarm po progu czasu; (5) dopisz test CI: ten sam scenariusz + asercja na stanie sesji.
Jeśli kod wyjścia to 1, CSMS odrzucił komunikat — najpierw napraw to, potem testuj awarię.

## Pułapki
- „Symulator przeszedł, więc ładowarka też przejdzie” — symulator nie odtwarza odchyleń firmware ani zegara bez RTC.
- Test obciążeniowy z jednego procesu na jednym laptopie: mierzysz generator, nie bramę. Sprawdź jego CPU i limity deskryptorów.
- Wszystkie symulatory startują w tej samej milisekundzie: to test peak’u, nie prawdopodobnego storm. Zrób oba warianty.
- Liczby pojemności z cudzych blogów zamiast własnego pomiaru; zapisuj warunki pomiaru (sprzęt, wersja, skala).
- Log z produkcji wklejony do testów bez anonimizacji `idTag` i identyfikatorów (RODO).
- Wynik `0` traktowany jako dowód, że stan domeny jest poprawny — sprawdź też bazę po scenariuszu.
- Test na adresie produkcyjnym: symulator tworzy prawdziwe sesje i CDR; używaj środowiska testowego.

## Checklista
- [ ] Poziomy 1–2 pokrywają ramki i schematy przed użyciem symulatora
- [ ] Scenariusz bazowy `session` zwraca 0, log przechodzi analizator bez ustaleń wagi wysokiej
- [ ] Każda awaria z tabeli ma test w CI z oczekiwanym ustaleniem
- [ ] Test obciążeniowy ma plan (liczba połączeń, rampa, czas) i zapisane wyniki pomiaru
- [ ] Reconnect storm sprawdzony w wariancie z rampą i bez
- [ ] Kontrakt OCPI uruchomiony na sandboxie partnera lub atrapie opartej na specyfikacji
- [ ] Regresja na logach tylko po anonimizacji tokenów
- [ ] Środowisko testowe odseparowane od produkcji

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| test obciążeniowy bramy, plan, metryki, reconnect storm | `references/obciazenie-i-storm.md` |
| kontrakt OCPI, regresja na nagranych logach, anonimizacja, narzędzia open source | `references/kontrakt-ocpi-i-regresja.md` |

## Źródła
- `.claude/skills/dom-ev-charging/references/ocpp.md` (cykl połączenia, offline, reconnect) i `ocpi.md` (moduły OCPI); import 2024–2025.
- `.claude/skills/dom-ev-diagnostics/references/log-i-skrypt.md` — format logu i ustalenia analizatora.
- Opis `charge_sim.py` i `ocpp_ws.py` — z briefu fabryki z 2026-10-20; po instalacji sprawdź `--help`.
- Wzorce testów (piramida, obciążenie, replay) to wiedza ogólna, nie fakt ze specyfikacji. Liczby: [do weryfikacji] własnym pomiarem.
Opracowane własnymi słowami, stan na 2026-10-20.
