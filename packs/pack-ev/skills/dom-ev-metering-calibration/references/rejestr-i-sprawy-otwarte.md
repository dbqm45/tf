# Rejestr legalizacji i sprawy otwarte

Spis treści: 1. Model zdarzeń legalizacji · 2. HB44 w liczbach · 3. Lista faktów do weryfikacji · 4. Zalecenia tylko założone.

## 1. Model zdarzeń legalizacji (propozycja projektowa, nie przepis)
| Zdarzenie | Pola | Co uruchamia |
|---|---|---|
| `meter_commissioned` | numer seryjny, producent, model, klasa, certyfikat, wersja firmware, data | start terminu ważności |
| `meter_verified` | data, ważny do, numer dokumentu, wykonawca | przesunięcie terminu |
| `meter_replaced` | stary i nowy numer seryjny, data, plomba | `ST=X` w kolejnych rekordach OCMF; nowy klucz publiczny |
| `cable_replaced` | identyfikator kabla, rezystancja `LR`, plomba | zmiana `LC` w rekordzie; ocena, czy kabel jest wymienny wg certyfikatu |
| `seal_broken` | numer plomby, powód | wstrzymanie rozliczenia za kWh do decyzji |
| `firmware_metrological_changed` | `FV`, `CF`, `GV` | ponowna ocena zgodności |
| `deadline_due` | rodzaj terminu, dni do końca | zgłoszenie serwisowe, ostrzeżenie w CSMS |

Reguły: zdarzenia dopisuje się, nie nadpisuje; rekord OCMF wiąże się z zasobem przez `MS` (numer seryjny licznika)
i z kluczem publicznym obowiązującym w dniu odczytu. Skutek po terminie (blokada czy ostrzeżenie) to decyzja
prawna operatora **[do weryfikacji]**.

## 2. HB44 3.40, wydanie 2026 (L141-360, L641-720)
Pełny opis i tabele: dom-ev-regulations-us. Dane metrologiczne przydatne w tym skillu:
| Pozycja | Wartość |
|---|---|
| Jednostki | kWh i podziały dziesiętne (S.1.3.1) |
| Najmniejsza wskazywana wartość | AC ≤ 0,0001 kWh, DC ≤ 0,001 kWh (S.1.3.2) |
| Tolerancje AC (T.2.1) | odbiorcza 1,0 %, utrzymania 2,0 % |
| Tolerancje DC (T.2.2) | 1,0 % / 2,0 %; DC sprzed 2025 oznaczone Class 5: 5,0 % do 01.01.2034; DC sprzed 2025 wyłączone do 01.01.2028 |
| Wskazanie | energia, cena jednostkowa i cena łączna; wskazanie przez co najmniej 15 s przy aktywacji i na starcie i końcu (S.1.2) |
| Wiele cen w sesji | start i stop każdej fazy, energia, cena jednostkowa i łączna (S.1.1(a)) |
| Paragon (S.2.6) | także elektroniczny: m.in. energia, cena łączna, cena jednostkowa, fazy cenowe, opłaty czasowe osobno |
| Utrata zasilania | informacje o transakcji muszą dać się ustalić; paragon wskazuje przerwanie (S.2.3) |

## 3. Lista faktów do weryfikacji
| Fakt | Dlaczego otwarty |
|---|---|
| treść zał. V MID (MI-003) | brak w bazie |
| okres i organ legalizacji liczników w PL | brak aktu w bazie |
| transpozycja 2026/706 w PL i DE | terminy krajowe po 10.04.2028 |
| wymogi Eichrecht: rozporządzenia, PTB, zakres dla AC i DC | brak w bazie; OCMF opisuje tylko format |
| weryfikator podpisu (Transparenzsoftware): wersje, rejestr kluczy | źródło w specyfikacji OCMF to link, nie treść |
| układ rekordu OCMF w polu `value` (1.6) i w `signedMeterData` (2.0.1) u konkretnego producenta | schematy tego nie określają, zależy od ładowarki |
| OCA Signed Meter Values (v1.0, 2025) | wzmianka w dom-ev-charger-hardware, brak treści w bazie |
| status prawny opłat za czas postoju względem MID | zał. Va nie reguluje czasu |
| tolerancja rozjazdu licznik–CSMS w umowach | zależy od umowy i klasy |

## 4. Zalecenia tylko założone
- Przypomnienie o terminie legalizacji z wyprzedzeniem (np. 90 dni) [założenie] — wartość wynika z umowy serwisowej.
- Osobny magazyn na surowe rekordy OCMF, tylko dopisywanie (WORM) [założenie] — dobra praktyka dowodowa, nie wymóg ze źródeł.
- Rejestr kluczy publicznych licznika odrębny od danych sesji [założenie].
