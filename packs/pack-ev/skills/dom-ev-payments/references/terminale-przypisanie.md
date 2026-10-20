# Terminale płatnicze: przypisanie do stacji i EVSE
> Spis: 1. Model danych · 2. Wybór EVSE · 3. Cykl życia terminala · 4. Tap-to-pay i terminal offline · 5. AFIR · 6. Pułapki · 7. Źródła

Wiedza ogólna branży; pola OCPI 2.3.0 i artykuły AFIR sprawdzone w bazie (zob. Źródła). Procesy własne operatora
(kolejność kroków, role) opisano bez nazw firm i systemów.

## 1. Model danych
```
Terminal (fizyczny, ma serial / reference PTP)
   └── przypisanie ──> Lokacja (location_id)  i/lub  EVSE (evse_uid)
                        Lokacja ──< Stacja (charger) ──< EVSE ──< Connector
```
| Relacja | Reguła | Uwaga |
|---|---|---|
| Terminal → EVSE | wiele-do-wielu w modelu własnym; w OCPI 2.3.0 lista `evse_uids` i `location_ids` w jednym Terminal | gdy podano oba zbiory, obowiązuje suma EVSE z obu list |
| Jeden terminal, kilka EVSE | typowy słupek płatniczy przy 2–8 złączach | kierowca musi wskazać, które EVSE płaci |
| Jedno EVSE, kilka terminali | dopuszczalne technicznie (np. terminal we wnętrzu stacji i na słupku) | sesja i tak ma jedno `authorization_reference`; zapisz, który terminal ją zainicjował |
| Terminal wbudowany w stację | przypisany do EVSE tej stacji z produkcji | aktywacja u PTP po referencji od producenta stacji |

Zapisz w modelu własnym (CSMS/CPMS), niezależnie od OCPI: `terminal_id`, `reference` (serial), PTP, status
(`zamówiony`, `aktywowany`, `przypisany`, `wycofany`), przypisania z datą od–do (**historia przypisań**, nie nadpisywanie),
`invoice_creator`. Bez historii nie ustalisz po fakcie, który terminal obsługiwał EVSE w dniu spornej płatności.

## 2. Wybór EVSE przez kierowcę
| Wariant | Jak działa | Ryzyko |
|---|---|---|
| Wybór na terminalu | kierowca wpisuje lub wybiera numer EVSE/złącza na klawiaturze albo ekranie terminala | pomyłka numeru; numer na słupku inny niż w systemie |
| Wybór na ekranie stacji | stacja z ekranem pokazuje QR lub kod; terminal dostaje wybór | rozjazd między ekranem a terminalem |
| Terminal na jedno EVSE | brak wyboru | koszt sprzętu |

Etykieta na stacji, numer pokazywany na terminalu i EVSE w systemie muszą być **tym samym identyfikatorem**
(dom-ev-identifiers; do kierowcy pokazuj krótką etykietę, w systemie trzymaj EVSE ID). Terminal po wyborze pokazuje
cenę EVSE (`tariff_id` z konektora → taryfa, zob. dom-ev-tariffs-pricing), więc zła zależność terminal→EVSE
oznacza złą cenę **i** złą sesję.

## 3. Cykl życia terminala
| Etap | Co robi operator | Dowód / odsyłacz |
|---|---|---|
| Zamówienie i rejestracja | zamówienie u producenta stacji albo PTP; referencja (serial) trafia do rejestru | rejestr assetów: dom-ev-asset-operations |
| Aktywacja u PTP | `POST …/terminals/activate` z referencją; PTP konfiguruje terminal (m.in. identyfikator dla adresu instalacji) i zakłada Terminal u CPO | `mod_payments`, Terminal Activation |
| Przypisanie | `PATCH` Terminal z `location_ids` / `evse_uids`; test: płatność próbna na każdym przypisanym EVSE | wynik testu zapisz przy terminalu |
| Eksploatacja | monitoruj łączność terminala, wersję, status u PTP; `capabilities` EVSE w Locations (`CHIP_CARD_SUPPORT`, `CONTACTLESS_CARD_SUPPORT`, `CREDIT_CARD_PAYABLE`, `DEBIT_CARD_PAYABLE`, `PED_TERMINAL`) zgodne ze stanem faktycznym | Locations, Capability |
| Wymiana | nowy terminal: aktywacja → przypisanie tych samych EVSE → test → dopiero potem dezaktywacja starego; okno bez terminala = brak płatności ad hoc (AFIR) | dom-ev-asset-operations (wymiana komponentu) |
| Wycofanie | `POST …/{terminal_id}/deactivate`; usuń przypisania (z datą końca), zdejmij `capabilities` płatności w Locations, rozlicz otwarte autoryzacje | dom-ev-asset-operations (decommissioning) |

Wymiana i wycofanie to procesy rejestru assetów — tu tylko skutki dla płatności. Kolejność „nowy najpierw, stary potem”
chroni przed lukami w obowiązku płatności ad hoc.

## 4. Tap-to-pay i terminal offline
Tap-to-pay = płatność zbliżeniowa kartą lub telefonem. Przebieg jak w SKILL.md (preautoryzacja → sesja → capture),
z rozszerzeniem o utratę łączności:
| Sytuacja | Zachowanie bezpieczne | Status |
|---|---|---|
| Terminal bez łączności z PTP przed płatnością | nie startuj sesji; komunikat „płatność niedostępna”, wskaż inne EVSE | zalecenie [do weryfikacji] |
| Terminal offline w trakcie sesji (po preautoryzacji) | sesja trwa do limitu `preauthorize_amount`; capture po powrocie łączności; zapisz kto zatrzymuje przy limicie | tryb terminala zależy od PTP [do weryfikacji] |
| Stacja offline, terminal online | start wymaga komendy do stacji; bez niej brak sesji → void preautoryzacji | wynika z przebiegu |
| Offline terminalowe (autoryzacja lokalna bez banku) | większość umów PTP/PSP tego nie dopuszcza lub ogranicza limitem | [do weryfikacji] z PTP i PSP |

Nie wprowadzaj „darmowego ładowania, gdy terminal nie działa” bez decyzji biznesowej: to utrata przychodu i precedens.
Sesje bez zapłaty dla kierowcy to osobny, jawny tryb (dom-ev-session-lifecycle: free vend), nie awaria płatności.

## 5. AFIR i terminale (rozporządzenie (UE) 2023/1804, art. 5 ust. 1)
Sprawdzone w tekście (`eu-afir`, wersja skonsolidowana 08.01.2026):
- Ust. 1 akapit 1: operatorzy zapewniają ładowanie ad hoc w publicznie dostępnych punktach.
- Ust. 1 akapit 2: w punktach uruchomionych od 13 kwietnia 2024 ładowanie ad hoc ma być możliwe instrumentem płatniczym
  szeroko używanym w Unii; operator przyjmuje płatności elektroniczne przez terminale i urządzenia płatnicze, **co najmniej
  jedno z**: (a) czytnik kart płatniczych, (b) urządzenie zbliżeniowe czytające co najmniej karty, (c) tylko dla punktów
  poniżej 50 kW — urządzenie z internetem i bezpieczną płatnością, np. kod QR.
- Ust. 1 akapit 3: od 1 stycznia 2027 punkty ≥ 50 kW na sieci TEN-T lub na bezpiecznym parkingu, także uruchomione
  przed 13.04.2024, mają spełniać (a) lub (b) — sam QR nie wystarczy.
- Ust. 1 akapit 4: **pojedynczy terminal może obsługiwać wiele publicznie dostępnych punktów w puli ładowania.**
  To uzasadnia model „jeden terminal — kilka EVSE”. „Pula” (art. 2 pkt 51) to jedna lub więcej stacji w jednym miejscu,
  więc terminal wspólny dla stacji z różnych lokalizacji nie ma oparcia w tym akapicie [wniosek własny — [do weryfikacji]].
- Ust. 1 akapit 5: wymogi nie dotyczą punktów, które nie pobierają opłaty.
- Ust. 2: przy automatycznym uwierzytelnianiu (np. Plug & Charge) kierowca zawsze może z niego nie skorzystać i zapłacić
  ad hoc albo użyć innego rozwiązania kontraktowego, a ta opcja ma być jasno pokazana.
- Ust. 4: w punktach ≥ 50 kW cena ad hoc oparta na kWh (+ opcjonalnie opłata za zajęcie w cenie za minutę), pokazana
  na stacji przed startem; poniżej 50 kW kolejność składników: kWh, minuta, sesja, inne.
Znaczenie dla terminala: wskazanie EVSE, cena widoczna **przed** zbliżeniem karty, brak przymusu konta lub aplikacji.

## 6. Pułapki
- Terminal przypisany do złego EVSE: cena z innego `tariff_id`, preautoryzacja na inną kwotę, start na innym złączu,
  **obciążenie karty za cudzą lub nieistniejącą sesję** → zwrot, korekta dokumentu, ewentualny chargeback.
  Zapobiegaj: test płatności próbnej na każdym EVSE po zmianie przypisań, alert na rozjazd rejestru i PTP.
- Przypisanie terminala do lokacji (`location_ids`) obejmuje **wszystkie** EVSE lokacji, także dodane później —
  sprawdź, czy tak ma być (nowe EVSE bez fizycznego dostępu do terminala).
- Wymiana terminala bez aktualizacji `capabilities` w Locations: aplikacje pokazują płatność kartą, której nie ma.
- Wycofanie bez zakończenia przypisań: terminal-widmo w rejestrze, `PATCH` na nieistniejący terminal.
- Różne etykiety portów na słupku, w aplikacji i w systemie.
- Brak historii przypisań: nie da się ustalić terminala dla starej sesji spornej.

## 7. Źródła
- OCPI 2.3.0, `mod_payments.asciidoc` (Terminal: `location_ids`, `evse_uids`, `reference`; PATCH przypisanie; Terminal
  Activation) i `mod_locations.asciidoc` (`Capability`: `CHIP_CARD_SUPPORT`…`PED_TERMINAL`), github.com/ocpi/ocpi tag v2.3.0,
  baza `ocpi-2.3.0`, pobrane 2026-10-20. OCPI 2.2.1-d2 nie ma modułu Payments (brak w bazie `ocpi-2.2.1-d2`).
- AFIR (UE) 2023/1804, art. 5 ust. 1–4, EUR-Lex, wersja skonsolidowana 08.01.2026, baza `eu-afir`, pobrane 2026-10-20.
- Tryby offline terminali i warunki umów PTP/PSP: praktyka branży, [do weryfikacji].
