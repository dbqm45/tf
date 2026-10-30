---
name: dom-ev-certification-testing
description: Użyj przy certyfikacji i zgodności ładowarki oraz CSMS — certyfikat OCA i OCTT, wewnętrzny program CPO, macierz model×firmware×kraj, karta producenta.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba ocenić lub zaplanować certyfikację i testy zgodności sprzętu oraz oprogramowania ładowania — certyfikat OCPP od OCA i OCTT (co obejmuje, czego nie), wewnętrzny program certyfikacji ładowarki u operatora (zakres testów, macierz model × firmware × wersja OCPP × kraj, kryteria wyjścia, re-certyfikacja przy nowym firmware, dowody), skrót o testach ISO 15118 i Plug & Charge, mapa zgodności regulacyjnej produktu jako wejścia (CE, RED, MID, Eichrecht, UDT, UL, HB44) oraz karta producenta w repozytorium projektu. Nie do procedury wprowadzenia modelu do CSMS (dom-ev-charger-onboarding), budowy symulatora (dom-ev-simulation-testing), treści przepisów (dom-ev-regulations-eu, dom-ev-regulations-pl, dom-ev-regulations-us) ani metrologii (dom-ev-metering-calibration)."
  slowa: "certyfikacja ładowarki, certyfikat OCPP, OCA, Open Charge Alliance, OCTT, OCPP Compliance Test Tool, program certyfikacji, testy zgodności, compliance test, conformance, interoperability, interoperacyjność, testival, nowy model DC, nowy kraj, macierz certyfikacji, re-certyfikacja, nowy firmware, kryteria wyjścia, exit criteria, karta producenta, rejestr producentów, vendor register, odchylenia producenta, Kempower, Alpitronic, Huawei, ABB, certyfikat nie gwarantuje, Plug & Charge test, CE RED, odbiór techniczny, UDT, charger certification, vendor qualification"
---

# Certyfikacja i testy zgodności ładowania

Skill porządkuje, **co potwierdza dany dokument i test** oraz jak operator (CPO) buduje własny program certyfikacji
ładowarki. Perspektywy: CPO (dopuszcza sprzęt do sieci), producent (zgłasza produkt), dostawca CSMS (dowodzi, że
backend obsługuje dany sprzęt). Fakty o programie OCA są **[do weryfikacji]** — stron OCA nie ma w bazie wiedzy
fabryki (stan 2026-10-20); przed umową lub zamówieniem sprawdź je u OCA.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/karta-producenta.md` | zakładasz lub prowadzisz kartę modelu/producenta w repozytorium albo oceniasz wpis o odchyleniu |
| `references/program-certyfikacji-cpo.md` | układasz zakres testów, macierz, kryteria wyjścia, raport i re-certyfikację |

## Cztery warstwy zgodności (kto co potwierdza)
| Warstwa | Co potwierdza | Czego **nie** potwierdza | Skill |
|---|---|---|---|
| Certyfikat OCPP (OCA) **[do weryfikacji]** | wybrane profile/funkcje OCPP zachowują się wg testów narzędzia OCTT w testowanej konfiguracji | pracy z Twoim CSMS, Twojej konfiguracji, offline w Twoich warunkach, nowszego firmware, kraju, płatności, licznika | tu |
| Wewnętrzna certyfikacja CPO | że **ten** model + firmware + wersja OCPP działa z **naszym** CSMS i w naszych krajach | zgodności z prawem produktu (to wejście, nie wynik) | tu + dom-ev-charger-onboarding |
| ISO 15118 / Plug & Charge | rozmowa auto ↔ ładowarka, PKI | OCPP, rozliczenia | dom-ev-iso15118 |
| Zgodność regulacyjna produktu | wprowadzenie do obrotu i użytku (CE, MID, UDT…) | zachowania protokołu | dom-ev-regulations-eu / -pl / -us |

Certyfikat jest **wejściem** do decyzji, nie jej zastępstwem. Brak certyfikatu OCA nie dyskwalifikuje modelu, a jego
obecność nie zwalnia z testów — różni się tylko ryzyko i zakres.

## 1. Certyfikat OCPP od OCA (wszystko **[do weryfikacji]**)
Wyjaśnij zamawiającemu, co przy takim certyfikacie sprawdzić:
| Pytanie do producenta | Dlaczego |
|---|---|
| wersja OCPP i **edycja** specyfikacji, której dotyczy certyfikat | 1.6, 2.0.1 i 2.1 to osobne certyfikaty; edycje różnią się poprawkami |
| które profile/zakresy funkcji w zakresie (Core, Smart Charging, Firmware Management, Security itd.) | funkcja poza zakresem = brak dowodu, choćby ładowarka ją „miała” |
| wersja **firmware** i sprzętu w teście | certyfikat dotyczy konkretnego wydania; nowy firmware wymaga własnego dowodu |
| narzędzie i metoda (OCTT, laboratorium, samodzielny test) i data | wersja narzędzia i edycji testów wpływa na wynik |
| raport z testu, nie samo logo | raport pokazuje przypadki pominięte i konfigurację |
| zakres wobec **Twojego** CSMS | OCTT symuluje stronę CSMS; nie zna Twoich reguł, tokenów, taryf ani trybu offline |
Tabela jest listą pytań, nie opisem programu: strukturę programu, poziomy, koszty i listę certyfikowanych produktów
weryfikujesz na stronach OCA. Szczegóły komunikatów — dom-ev-ocpp-16, dom-ev-ocpp-2x (pola w schematach z bazy).

## 2. Wewnętrzna certyfikacja ładowarki u operatora
**Czym różni się od onboardingu** (dom-ev-charger-onboarding):
| | Certyfikacja (ten skill) | Onboarding |
|---|---|---|
| pytanie | czy typ **spełnia nasze kryteria** w danym kraju i wersji | jak **wprowadzić** dopuszczony typ do CSMS |
| jednostka | wiersz macierzy: model × firmware × OCPP × kraj | stacja i jej konfiguracja |
| wynik | status typu w karcie producenta + raport + decyzja człowieka | działająca stacja w sieci, pilot |
| rytm | raz na kombinację, powtarzana przy zmianie firmware | przy każdym wdrożeniu partii |
Wspólna jest macierz testów akceptacyjnych T1–T14 z dom-ev-charger-onboarding;
certyfikacja dodaje zakres krajowy, metrologię, płatności, bezpieczeństwo i kryteria wyjścia. Nie dubluj testów:
raz zdefiniowane przypadki odsyłaj z jednego miejsca.

### Zakres testów (grupy)
| Grupa | Przykładowe przypadki | Gdzie szczegóły |
|---|---|---|
| Boot i konfiguracja | `BootNotification`, `Pending`/`Accepted`, odczyt i zmiana konfiguracji, `RebootRequired` | onboarding |
| Autoryzacja | RFID, aplikacja (zdalny start), odrzucony token, lista lokalna | dom-ev-ocpp-16/-2x |
| Sesje | start, stop, koniec przez odpięcie, `transactionId`, `seqNo` (2.0.1), sesje równoległe na 2 EVSE | dom-ev-session-lifecycle |
| Pomiar | `MeterValues`, jednostki, znacznik czasu, rozjazd licznik ↔ CSMS, **odczyt podpisany** (OCMF) tam, gdzie wymaga go kraj | dom-ev-metering-calibration |
| Smart charging | profile, limit w A i W, zachowanie offline | dom-ev-smart-charging |
| Firmware | `UpdateFirmware`, statusy, powrót po restarcie, zachowanie konfiguracji, błędna aktualizacja | onboarding (T9) |
| Offline | zerwanie, kolejka, powrót, utrata zasilania | dom-ev-simulation-testing (scenariusze), test na sprzęcie |
| Błędy | `Faulted`, kody błędów, mapowanie stanów złącza | dom-ev-charger-hardware |
| Płatności | terminal kartowy, preautoryzacja, zwrot po przerwanej sesji | dom-ev-payments |
| Bezpieczeństwo | profil 2/3, wygasły certyfikat, rotacja kluczy, podpis firmware | dom-ev-ocpp-2x, dom-ev-ocpp-16 |
| Wymogi kraju | metrologia, odbiór techniczny, rejestry, znakowanie | tabela w pkt 4 |

Symulator sprawdza Twój CSMS; **egzemplarz fizyczny** sprawdza zachowanie producenta — certyfikacja wymaga obu.

### Macierz i kryteria
- Wiersz = **model × firmware × wersja OCPP × kraj** (kolumny dodatkowe: profil bezpieczeństwa, licznik, terminal
  płatniczy). Nowy kraj dla znanego typu = nowy wiersz, ale **tylko** testy zależne od kraju (pomiar, płatność,
  odbiór, rejestry), jeśli firmware i OCPP się nie zmieniły — uzasadnienie zapisz w raporcie.
- **Kryteria wyjścia** (przykład, progi **[założenie]**, uzgodnij per projekt): wszystkie testy krytyczne przeszły lub
  mają odchylenie z obejściem za flagą; ustalenia wysokiej wagi z `ocpp_log_analyze.py` wyjaśnione; zgodność energii
  w granicach z karty; brak sesji osieroconych w pilocie; wymagania kraju potwierdzone dokumentem; decyzja człowieka.
- **Statusy typu:** `laboratorium` → `pilot` → `dopuszczony` → `wycofany`; osobno **per kraj**.
- **Re-certyfikacja:** nowy firmware, nowa edycja OCPP, zmiana licznika lub terminala, zmiana modułu łączności =
  nowy wiersz. Zakres: pełna macierz, gdy notatki wydania dotykają OCPP, statusów, licznika, bezpieczeństwa lub
  smart charging; w innym razie podzbiór regresyjny (T1, T3, T5, T6, T8, T9) z uzasadnieniem. Notatek wydania nie
  przepisuj jako faktów — porównaj zachowanie na stacji.
- **Dowody:** surowy log JSON Lines każdego testu, wynik `ocpp_log_analyze.py`, zdjęcia/numery seryjne licznika
  i terminala, dokumenty krajowe, wersja i suma kontrolna firmware, data i wykonawca. Brak dowodu = „nie sprawdzono”.

## 3. ISO 15118 i Plug & Charge (skrót)
Zakres i procedury — **dom-ev-iso15118**. Do planu certyfikacji wpisz: (a) testy zgodności strony ładowarki
(SECC) — sekwencja komunikatów, timeouty, DIN 70121 jako fallback; (b) PKI: łańcuch certyfikatów, instalacja
i aktualizacja certyfikatu kontraktu przez OCPP, wygasły certyfikat, zegar; (c) **interoperacyjność z autami** —
lista modeli pojazdów i wersji ich oprogramowania, bo ta sama ładowarka dogaduje się z jednymi i nie z innymi.
Formalne testy zgodności wg serii ISO 15118 oraz wydarzenia interoperacyjności (testivale) organizuje środowisko
branżowe — zakres, daty i zasady **[do weryfikacji]** u organizatora; wyniki z testivalu dopisz do karty z datą
i wersjami, ale nie traktuj ich jako gwarancji dla innego auta.

## 4. Zgodność regulacyjna jako wejście (tylko mapa)
| Obszar | Co ładowarka ma mieć od producenta | Szczegóły |
|---|---|---|
| UE: znak CE, RED, cyberbezpieczeństwo radia (EN 18031, okres przejściowy do CRA) | deklaracja zgodności UE, lista dyrektyw | dom-ev-regulations-eu |
| UE: licznik MID/MI-011, Niemcy: Eichrecht | certyfikat badania typu licznika, klasa, odczyt podpisany | dom-ev-metering-calibration |
| PL: badanie UDT przed oddaniem do eksploatacji, numer EIPA | dokumenty do wniosku, harmonogram | dom-ev-regulations-pl |
| USA: UL (np. 2594, 2202), NRTL, NIST HB44 3.40, NEVI | listing NRTL, zgodność z HB44 | dom-ev-regulations-us |
Dokument producenta jest **wejściem**: sprawdź numer, zakres i datę, ale ocena prawna należy do prawnika/jednostki.
Daty graniczne i progi — z tych skilli, nie z pamięci. Wymogi krajowe poza UE, PL i USA — **[do weryfikacji]**.

## 5. Karta producenta
Rejestr żyje **w repozytorium projektu** (`docs/project/vendors/<producent>-<model>.md`), nie w fabryce. Szablon
i zasady: `references/karta-producenta.md`. Różnica wobec karty onboardingu: karta onboardingu opisuje decyzję
o jednym typie; karta producenta zbiera historię modelu (firmware, odchylenia z dowodami, statusy per kraj, kontakt).

## Przykład
Wejście: „Nowy model DC 150 kW producenta Z, OCPP 1.6, wchodzimy do kraju K. Producent ma certyfikat OCA.”
Wynik: (1) karta `docs/project/vendors/<producent>-<model>.md`: model, firmware 1.2.3 (z Boot), OCPP 1.6, profil 2; status
`laboratorium`; (2) pytania do producenta o certyfikat OCA: wersja i edycja, profile, firmware w teście, raport —
wpis „deklarowane, [do weryfikacji]”; (3) wiersz macierzy: DC150 × 1.2.3 × 1.6 × K; testy z grup powyżej na
egzemplarzu, symulator uzupełnia; (4) wymogi K: certyfikat licznika, odbiór techniczny — dokumenty jako dowód;
(5) odchylenie „po `StopTransaction` status `Finishing` 90 s” wpisane z ramką, datą i wersją firmware, obejście
za flagą; (6) raport + decyzja człowieka → `pilot` w K; (7) firmware 1.3.0 → nowy wiersz i podzbiór regresyjny.

## Pułapki
- **„Mamy certyfikat OCA, więc pomijamy test”:** certyfikat nie obejmuje Twojego CSMS, firmware po teście ani trybu offline.
- **Certyfikat bez wersji firmware i profili** — nie wiadomo, co przetestowano.
- **Jedna certyfikacja dla wszystkich krajów:** pomiar, odbiór i płatności są krajowe.
- **Zmiana firmware „tylko poprawki” bez re-certyfikacji** — zmiany statusów i licznika bywają w poprawkach.
- **Test tylko na symulatorze albo tylko na jednym egzemplarzu** — pierwszy nie zna sprzętu, drugi nie zna serii.
- **Odchylenie producenta z opinii** („wszyscy wiedzą”) — bez ramki, logu i daty nie wchodzi do karty.
- **Mylenie deklaracji zgodności CE z certyfikatem protokołu** — to dwie różne rzeczy.
- **Brak dowodów w repozytorium** — po roku nikt nie odtworzy decyzji.
- **Sukces testivalu ISO 15118 jako gwarancja dla każdego auta.**

## Checklista
- [ ] Karta producenta w `docs/project/vendors/<producent>-<model>.md` z modelem, firmware i wersją OCPP
- [ ] Certyfikat OCA (jeśli jest): wersja, edycja, profile, firmware, raport — oznaczone jako deklarowane
- [ ] Macierz model × firmware × OCPP × kraj z statusem per kraj
- [ ] Testy na fizycznym egzemplarzu plus symulator; logi i `ocpp_log_analyze.py` zachowane
- [ ] Wymogi kraju (licznik, odbiór, rejestry) udokumentowane dowodem
- [ ] Odchylenia: ramka/log, wersja firmware, data, obejście za flagą
- [ ] Kryteria wyjścia spełnione, decyzja człowieka z datą
- [ ] Plan re-certyfikacji przy nowym firmware

## Źródła
- Program OCA, OCTT, zakresy certyfikatów, testivale i serie testów ISO 15118: wiedza ogólna autora skilla,
  **[do weryfikacji]** — stron OCA i organizatorów nie ma w bazie (stan 2026-10-20).
- `.claude/skills/dom-ev-charger-onboarding/` (SKILL.md i jego pliki references), stan 2026-10-20: macierz T1–T14,
  pilot, rejestr odchyleń, karta onboardingu.
- `.claude/skills/dom-ev-regulations-eu/SKILL.md` (RED/EN 18031 do 2027-12-10, potem CRA), `dom-ev-regulations-pl`
  (badanie UDT, EIPA; `pl-elektromobilnosc`, pobrane 2026-10-20), `dom-ev-regulations-us` (NRTL, HB44 3.40),
  `dom-ev-metering-calibration` (MI-011 od 2028-10-10): terminy i zakresy tylko tam.
- Progi kryteriów wyjścia i zasady re-certyfikacji: praktyka ogólna autora skilla, **[założenie]**, nie norma.
