---
name: dom-ev-charger-onboarding
description: Użyj przy wprowadzaniu nowego modelu ładowarki lub firmware do CSMS — karta onboardingu, Pending vs Accepted, testy akceptacyjne, odchylenia producenta, pilotaż.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy nowy model ładowarki albo nowa wersja firmware ma wejść do sieci operatora — karta onboardingu (producent, model, firmware, OCPP i edycja, profil bezpieczeństwa, EVSE, licznik), konfiguracja połączenia, BootNotification Pending vs Accepted jako bramka, odczyt i ustawienie konfiguracji, macierz testów akceptacyjnych, analiza logów z testów, rejestr odchyleń producenta, decyzja o dopuszczeniu i pilotaż na jednej stacji przed flotą. Nie do awarii stacji w produkcji (dom-ev-diagnostics), sprzętu i złączy (dom-ev-charger-hardware), treści komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x) ani budowy symulatora (dom-ev-simulation-testing)."
  slowa: "onboarding ładowarki, nowy model ładowarki, nowy producent, nowy firmware, aktualizacja firmware, dopuszczenie do sieci, homologacja, certyfikacja OCPP, akceptacja stacji, testy akceptacyjne, pilotaż, pilot, 200 sztuk, wdrożenie na flotę, rollout, odchylenia producenta, quirks, Pending, Accepted, karta onboardingu, raportują inne statusy, DC 150 kW, new charger model, firmware rollout, acceptance test, vendor deviation"
---

# Onboarding ładowarki — nowy model lub nowy firmware w CSMS

Procedura dopuszczenia **typu** ładowarki (model + wersja firmware + wersja OCPP) do sieci. Każda zmiana któregoś
z tych trzech elementów to nowy wpis w karcie i nowa runda testów. Cecha **safety-critical**: ładowarka steruje
prądem i blokadą złącza, więc flotę poprzedza pilotaż na jednej stacji, a decyzję o dopuszczeniu podejmuje człowiek.
Sprzęt, CP i złącza → **dom-ev-charger-hardware**; komunikaty → **dom-ev-ocpp-16**, **dom-ev-ocpp-2x**; awaria
w produkcji → **dom-ev-diagnostics**; symulator → **dom-ev-simulation-testing**.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/karta-onboardingu.md` | wypełniasz kartę typu ładowarki lub oceniasz, czego w niej brakuje |
| `references/macierz-testow.md` | planujesz testy akceptacyjne, kryteria przejścia, pilotaż, wpis odchylenia |

## Procedura
| # | Krok | Wynik / dowód |
|---|---|---|
| 1 | Zbierz dokumentację producenta: arkusz danych, deklaracja zgodności OCPP, lista kluczy konfiguracji, notatki wydania firmware | karta onboardingu (szkielet) |
| 2 | Ustal identyfikatory: `chargePointId` / stationId, EVSE ID dla każdego punktu — zasady i walidacja w **dom-ev-identifiers** (`ev_id_check.py`) | tabela stacja → EVSE ID, bez duplikatów |
| 3 | Skonfiguruj połączenie: URL, podprotokół (`ocpp1.6` / `ocpp2.0.1`), profil bezpieczeństwa, certyfikaty | udane otwarcie WebSocket |
| 4 | Bramka przyjęcia: `BootNotification` → `Pending` lub `Accepted` | zapis ramki Boot i odpowiedzi |
| 5 | Odczytaj konfigurację i ustaw wartości operatora | zapis odpowiedzi przed i po zmianie |
| 6 | Testy akceptacyjne wg macierzy | log każdego testu |
| 7 | Analiza logów z testów (`ocpp_log_analyze.py`) | lista ustaleń, każde wyjaśnione |
| 8 | Wpis odchyleń producenta do rejestru | wpisy w formacie z tabeli niżej |
| 9 | Decyzja o dopuszczeniu, pilotaż na jednej stacji, dopiero potem flota | decyzja człowieka z datą |

Kroki 1–2 mogą iść równolegle; 3–9 idą po kolei. Nie przeskakuj kroku 6, nawet gdy producent „ma certyfikat”.

## Krok 3: połączenie
- Wersja OCPP i edycja specyfikacji z karty (nie zgadujesz z nagłówka). Podprotokół i układ ścieżki URL —
  **[do weryfikacji]** w dokumentacji producenta; reguły rozpoznania wersji we flocie mieszanej: **dom-ev-ocpp-2x**.
- Profil bezpieczeństwa: 1 (Basic Auth przez `ws://`) tylko w laboratorium; produkcja minimum profil 2 (TLS + Basic
  Auth); profil 3 (mTLS) wymaga PKI — wystawianie, rotacja, unieważnianie. W 1.6 profile pochodzą z dodatku Security
  Whitepaper (opcjonalnego), w 2.0.1 są w standardzie. Czy model je obsługuje, wynika z karty, nie z założenia.
- Certyfikaty i sekrety (hasło Basic Auth, klucze) trzymaj w magazynie sekretów, nie w karcie ani w repo.

## Krok 4: Pending vs Accepted
| Odpowiedź CSMS | Znaczenie przy onboardingu |
|---|---|
| `Pending` | CSMS zna stację, ale jej jeszcze nie przyjął — czas na konfigurację z naszej strony. Użyj jako bramki: w `Pending` czytasz konfigurację (krok 5), a `Accepted` dajesz dopiero po sprawdzeniu karty. Co stacja może wysyłać w `Pending` — **[do weryfikacji]** w specyfikacji danej edycji |
| `Accepted` | normalna praca; `interval` to odstęp Heartbeatów |
| `Rejected` | stacja nieznana lub niedopuszczona; ponawia po `interval` — to oczekiwany wynik dla typu spoza listy dopuszczonych |

Bramka w CSMS: dopasuj (vendor, model, wersja firmware) z `BootNotification` do karty. Brak dopasowania → `Pending`
albo `Rejected` i alert; pasuje do typu ze statusem „pilot” → `Accepted` tylko dla stacji z listy pilotażowej.
Pola Boot (vendor, model, numer seryjny, firmware) producent bywa wypełniać niespójnie — zapisz dokładne wartości
z ramki i dopasuj do nich, nie do nazw z dokumentacji.

## Krok 5: konfiguracja
- **1.6:** `GetConfiguration` bez listy kluczy; zapisz pełną odpowiedź (klucze, `readonly`, `unknownKey`). Zapis:
  `ChangeConfiguration` po jednym kluczu; odpowiedź (`Accepted` / `Rejected` / `RebootRequired` / `NotSupported`)
  zapisz przy kluczu.
- **2.0.1:** `GetBaseReport` → `NotifyReport` daje pełny obraz Device Model; zapis przez `SetVariables`.
- **Nazw kluczy nie wymyślasz.** Jeśli klucza lub zmiennej nie ma w `references` skilli dom-ev-ocpp-16 /
  dom-ev-ocpp-2x, w karcie piszesz „klucz wg dokumentacji producenta” i wpisujesz nazwę dokładnie z odpowiedzi stacji.
- Wartości operatora (interwał Heartbeatu, zachowanie offline, limity mocy, autoryzacja lokalna) ustalasz w
  dokumencie standardu sieci; karta zapisuje, co faktycznie przyjęła stacja (`Accepted` ≠ zastosowano po restarcie).
- Po zmianach wymagających restartu: restart, ponowny Boot, ponowny odczyt — wartość z odczytu jest dowodem.

## Krok 6: testy akceptacyjne
Macierz (kryteria przejścia i wymagany dowód): `references/macierz-testow.md`. Zakres minimum:
sesja RFID, zdalny start i stop, offline i powrót, utrata zasilania w trakcie sesji, aktualizacja firmware,
smart charging (jeśli model go deklaruje). Budowa symulatora i scenariuszy — **dom-ev-simulation-testing**; ale
**odbiorczy test na prawdziwym egzemplarzu jest obowiązkowy** — symulator nie ma zachowań sprzętu producenta.
Pomiar energii i legalizacja licznika (MID i odpowiedniki) — wartości z karty, weryfikacja u dostawcy sprzętu
(**dom-ev-charger-hardware**).

## Krok 7: analiza logów
Każdy test zapisuje surowy log JSON Lines (`{ts, cp, dir, frame}`). Uruchom:
`python3 .claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py <log.jsonl> --ocpp 1.6` (albo `2.0.1`).
Wynik: ustalenia z numerami linii (np. `open-transaction`, `meter-decrease`, `clock-skew`, `seqno-gap`).
Reguła: ustalenie wysokiej wagi w teście, który miał przejść, = test nieprzejęty, dopóki ustalenie nie jest
wyjaśnione (błąd stacji → odchylenie; błąd testu → powtórka). Format i odczyt ustaleń: **dom-ev-diagnostics**.

## Krok 8: rejestr odchyleń
Jeden wpis = jedno zachowanie. Format:
| Pole | Przykład |
|---|---|
| producent | „Vendor X” (dokładnie jak w `chargePointVendor`) |
| model | „DC150-A” |
| firmware | „2.4.1” (dokładny ciąg z Boot) |
| zachowanie | „po `StopTransaction` wysyła `Finishing` zamiast `Available` przez 90 s” |
| obejście za flagą | `tolerate_finishing_delay` (flaga per model w CSMS, domyślnie wyłączona) |
| data | 2026-10-20 |
Obejście **zawsze za flagą** ograniczoną do (producent, model, firmware) — nie zmieniasz globalnej logiki dla jednej
marki. Odchylenie przy nowym firmware sprawdzasz od nowa: wpis dotyczy konkretnej wersji. Wzorce odchyleń 1.6:
`.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`.

## Krok 9: decyzja i pilotaż
1. Warunki dopuszczenia do pilota: karta kompletna, macierz bez otwartych testów krytycznych, ustalenia z logów
   wyjaśnione, odchylenia mają flagi. Decyzję podpisuje człowiek (kto, kiedy — w dzienniku projektu).
2. **Pilot: jedna stacja** w lokalizacji z dostępem serwisu, przez okres ustalony z góry (liczba sesji i dni —
   **[założenie]** do uzgodnienia, np. ≥ kilkadziesiąt sesji w różnych warunkach), z monitoringiem statusów i energii.
3. Kryteria wyjścia z pilota: brak sesji osieroconych, zgodność kWh licznik ↔ sesja, brak nowych odchyleń.
4. Flota partiami (np. 5%, 25%, reszta — **[założenie]**), przerwa na obserwację po każdej partii, wycofanie
   (firmware poprzedni, `Rejected` w bramce) opisane przed startem.
Nowy firmware znanego modelu: ta sama ścieżka, pilot na jednej stacji; pełna macierz, gdy notatki wydania wspominają
zmiany w OCPP, statusach, liczniku, bezpieczeństwie lub smart charging.

## Przykład
Wejście: „po firmware 3.1.0 modelu DC150-A stacje wysyłają `Preparing` zamiast `Available` po zakończeniu sesji.”
Wynik: (1) jedna stacja testowa na 3.1.0, reszta zostaje na 3.0.x, bramka Boot trzyma pozostałe `Accepted` tylko
dla 3.0.x; (2) test „zakończ sesję i odepnij kabel” z logiem, `ocpp_log_analyze.py` na logu; (3) porównanie sekwencji
`StatusNotification` 3.0.x ↔ 3.1.0; (4) wpis: producent, model DC150-A, firmware 3.1.0, zachowanie „`Preparing`
po odpięciu kabla”, obejście za flagą (nie traktuj `Preparing` bez transakcji jako zajętego złącza dłużej niż
N s), data; (5) zgłoszenie do producenta; (6) rollout 3.1.0 dopiero po pilocie i podpisie człowieka.

## Pułapki
- **„Certyfikat OCPP producenta wystarczy”:** certyfikat nie obejmuje Twojego CSMS, konfiguracji ani pracy offline.
- **Pominięty pilot:** błąd w blokadzie złącza lub liczniku na 200 sztukach to koszt serwisu i spory o rozliczenia.
- **Mylenie `Accepted` odpowiedzi na `ChangeConfiguration` z zastosowaniem** — sprawdź odczytem, po restarcie.
- **Odchylenie bez wersji firmware:** po aktualizacji wpis jest nieaktualny; zawsze wersja w polu.
- **Obejście globalne** zamiast flagi per (producent, model, firmware).
- **Test tylko na symulatorze** — symulator potwierdza Twój CSMS, nie sprzęt.
- **Zgadywanie nazw kluczy** z innego modelu tego samego producenta.
- **Nowy firmware „tylko poprawki”** wdrożony bez testów — zmiana statusów lub liczenia energii bywa w „poprawkach”.
- **Identyfikatory nadawane ręcznie bez walidacji** → duplikaty EVSE ID w OCPI (**dom-ev-identifiers**).

## Checklista
- [ ] Karta onboardingu kompletna (pola bez danych: „brak danych”, nie puste)
- [ ] Wersja i edycja OCPP oraz profil bezpieczeństwa zapisane
- [ ] Identyfikatory zwalidowane `ev_id_check.py`
- [ ] Bramka Boot dopasowuje (vendor, model, firmware); typ nieznany → `Pending`/`Rejected`
- [ ] Konfiguracja odczytana przed i po zmianie, odpowiedzi zapisane
- [ ] Macierz testów wykonana na prawdziwym egzemplarzu, logi zachowane
- [ ] `ocpp_log_analyze.py` uruchomiony na każdym logu, ustalenia wyjaśnione
- [ ] Odchylenia w rejestrze: producent, model, firmware, zachowanie, flaga, data
- [ ] Decyzja człowieka, pilot na jednej stacji, plan wycofania przed flotą

## Źródła
- `.claude/skills/dom-ev-charging/references/ocpp.md` (import 2024–2025, włączony 2026-09-27): Boot, statusy,
  firmware, offline.
- `.claude/skills/dom-ev-ocpp-16/SKILL.md`, `.claude/skills/dom-ev-ocpp-2x/SKILL.md` (stan 2026-10-20): konfiguracja,
  Security Whitepaper, profile bezpieczeństwa.
- `.claude/skills/dom-ev-diagnostics/scripts/ocpp_log_analyze.py`: format logu i kody ustaleń.
- Procedura pilotażu, progi partii i format rejestru: praktyka ogólna autora skilla, **[założenie]**, nie norma.
