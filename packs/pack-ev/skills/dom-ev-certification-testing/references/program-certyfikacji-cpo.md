# Program certyfikacji ładowarki u operatora — szczegóły

Zakres ogólny i granice wobec onboardingu: `SKILL.md`. Przypadki testowe T1–T14 i pilot:
`.claude/skills/dom-ev-charger-onboarding/references/macierz-testow.md`. Symulator i scenariusze awarii:
dom-ev-simulation-testing. Progi i liczby poniżej to **[założenie]** do uzgodnienia per projekt.

## 1. Fazy
| Faza | Wynik | Dowód |
|---|---|---|
| 0. Kwalifikacja | czy producent ma dokumentację (OCPP, klucze konfiguracji, licznik, certyfikaty), serwis w kraju, przykładowy egzemplarz | karta producenta, pytania i odpowiedzi z datą |
| 1. Laboratorium | testy T1–T14 na egzemplarzu; symulator uzupełnia | logi JSON Lines, `ocpp_log_analyze.py` |
| 2. Wymogi kraju | licznik, odbiór techniczny, rejestry, płatności | dokumenty z numerem i datą |
| 3. Pilot | jedna stacja w terenie (procedura w onboardingu) | raport pilotażu |
| 4. Decyzja | `dopuszczony` per kraj albo odmowa z powodem | podpis człowieka, data |
| 5. Utrzymanie | re-certyfikacja przy zmianach, przegląd odchyleń | karta, dziennik |

## 2. Macierz — przykład
| Model | Firmware | OCPP | Kraj | Licznik/terminal | Status | Raport |
|---|---|---|---|---|---|---|
| <model-A> | 1.2.3 | 1.6 | PL | <licznik>, <terminal> | pilot | <ścieżka> |
| <model-A> | 1.2.3 | 1.6 | DE | j.w. + odczyt podpisany | laboratorium | <ścieżka> |
| <model-A> | 1.3.0 | 1.6 | PL | j.w. | do ponownego sprawdzenia | — |
Kolumny dodaj wg potrzeb: profil bezpieczeństwa, moduł łączności, wersja sprzętu. Liczba wierszy rośnie
iloczynowo — ogranicz ją regułą: jeden **firmware referencyjny** na model dla pełnej macierzy, inne wersje i kraje
tylko podzbiorem zależnym od zmiany (pkt 3).

## 3. Zakres regresji przy zmianie
| Co się zmieniło | Minimum |
|---|---|
| nowy firmware, notatki wspominają OCPP, statusy, licznik, bezpieczeństwo, smart charging | pełna macierz |
| nowy firmware, inne zmiany (UI, łączność) | T1, T3, T5, T6, T8, T9 + test dotkniętej funkcji |
| zmiana licznika lub terminala | T8 (energia), grupa pomiar/płatność, dokumenty kraju |
| nowa edycja lub wersja OCPP | pełna macierz |
| nowy kraj, ten sam firmware | grupa „wymogi kraju”, pomiar, płatność, jedna sesja end-to-end |
| nowa wersja CSMS | regresja na nagranych logach (dom-ev-simulation-testing) dla dopuszczonych typów |
Wniosek „to tylko poprawka” wymaga dowodu: porównanie sekwencji `StatusNotification` i energii sprzed/po.

## 4. Raport i dowody
Raport (jeden plik na wiersz macierzy) zawiera: tożsamość (vendor/model/firmware z Boot), wersję OCPP i profil,
wersję CSMS, listę testów z wynikiem (przeszedł / odchylenie / nie przeszedł / nie sprawdzono), odnośniki do logów,
ustalenia analizatora z wyjaśnieniem, odchylenia (linki do karty), decyzję i podpis, datę. Pierwsza linia:
`Werdykt: dopuszczony | pilot | odmowa | do uzupełnienia` — żeby następny krok mógł sprawdzić ją skryptem. Logi
anonimizuj przed zapisem w repozytorium.

## 5. Wymogi kraju
| Pytanie | Kto odpowiada | Skill |
|---|---|---|
| czy licznik ma ważny certyfikat typu i czy wymagany jest odczyt podpisany | producent + dokumenty, ocena w metrologii | dom-ev-metering-calibration |
| czy stacja przeszła odbiór/badanie wymagane do eksploatacji | operator + właściwy organ (PL: UDT) | dom-ev-regulations-pl |
| CE, RED, cyberbezpieczeństwo, AFIR | producent (deklaracje), operator (płatność ad hoc, dane) | dom-ev-regulations-eu |
| listing NRTL, HB44, NEVI | producent, operator | dom-ev-regulations-us |
| kraj spoza tych skilli | prawnik/lokalny partner — **[do weryfikacji]** | — |

## 6. Role
- **CPO:** program, kryteria, decyzja o statusie.
- **Producent:** dokumentacja, firmware, egzemplarze, odpowiedzi na odchylenia, certyfikaty.
- **Dostawca CSMS:** dowód, że backend obsługuje typ (flagi per model, regresja na logach), wersje CSMS w raporcie.
- **Człowiek podpisujący:** decyzja o `dopuszczony`; agent przygotowuje raport i nie zmienia statusu sam.
