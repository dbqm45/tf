# Normy SAE i UL oraz przepisy stanowe USA — co jest, a co do sprawdzenia

W bazie wiedzy fabryki **nie ma** pełnego tekstu żadnej pozycji z tej listy. Poniżej: co wynika z części 680 i HB44 (źródła
w bazie) oraz co jest wiedzą ogólną. Wiedza ogólna bez dowodu = **[do weryfikacji]**. Sprawdzenie: `kb.py sources --area regulations-us`,
a dla brakujących pozycji dodaj źródło do rejestru przed użyciem w decyzji (core-source-research).

## Spis treści
- SAE J1772 i J3400
- UL 2594, UL 2202 i certyfikacja
- Przepisy stanowe
- Zestaw pytań do sprawdzenia

## SAE J1772 i J3400
| Fakt | Źródło | Status |
|---|---|---|
| NEVI wymaga na stałe złącza J1772 dla AC Level 2 i CCS Type 1 dla DCFC | § 680.106(c), `us-nevi` L102 | potwierdzone w tekście |
| Tekst części 680 nie wymienia SAE J3400 ani NACS | `us-nevi` doc.txt (brak trafień w pełnym tekście, 2026-10-20) | potwierdzone grepem |
| Czy stacja z samym złączem NACS spełnia § 680.106(c) | wymaga wykładni FHWA lub stanu | **[do weryfikacji]**, id `us-nevi` nie rozstrzyga |
| Status J3400: TIR z 2023-12-18, RP J3400_202409 z 2024-09-30 | źródła wtórne w skillu dom-ev-charger-hardware | **[do weryfikacji]**, id `sae-j3400` (niepobrane, płatne) |
| J1772: sygnał CP/PWM, PP, Type 1 | wiedza ogólna; opis sygnałów w dom-ev-charger-hardware | **[do weryfikacji]**, brak id w rejestrze |

Złącze to temat sprzętu (CP, PP, stany): dom-ev-charger-hardware. W CPMS złącze to pole `connector` w modelu lokalizacji
(dom-ev-glossary); wymóg „co najmniej jedno stałe CCS1” sprawdzaj per port, nie per stację.

## UL 2594, UL 2202 i certyfikacja
- Część 680 wymaga certyfikatu NRTL dla wszystkich ładowarek i ENERGY STAR dla AC Level 2 (§ 680.106(g), „must”). Zalecenie
  „odpowiednie normy UL dla sprzętu do ładowania” jest „should”, bez numerów norm (L122).
- HB44 A.4: NTEP przyjmuje do oceny typu tylko EVSE z certyfikatem NRTL (L136-138) — dwa wymagania spotykają się na tej samej etykiecie.
- UL 2594 (EVSE, w tym AC) i UL 2202 (system ładowania DC) jako normy produktowe, a UL 2231 jako ochrona osobista:
  **[do weryfikacji]**, brak id w rejestrze; NRTL (np. UL Solutions, Intertek, TÜV) wystawia certyfikat — nazwa jednostki do sprawdzenia.
- Numer certyfikatu i listę norm trzymaj w karcie modelu ładowarki (onboarding: dom-ev-charger-onboarding).

## Przepisy stanowe
Federalny HB44 i NEVI nie zastępują prawa stanu. Każdy stan może:
- przyjąć HB44 3.40 w całości, z modyfikacjami albo z odroczeniami; organ metrologiczny (Weights and Measures) nadzoruje urządzenia i rejestruje usługodawców;
- ustalić własne wymogi cen, ujawniania, niezawodności i raportowania dla stacji publicznych;
- dodać wymogi do dofinansowania (umowa stanu z operatorem, § 680.106(a) wymaga jawności ustalania ceny).

| Stan | Co może dotyczyć | Status |
|---|---|---|
| Kalifornia | nadzór metrologiczny (CDFA, Division of Measurement Standards), wymogi niezawodności i raportowania stacji (CEC), przepisy o cenie za kWh | **[do weryfikacji]**, brak id w rejestrze |
| Inne stany | przyjęcie HB44 3.40, ceny i dostępność | **[do weryfikacji]**, brak id w rejestrze |

Zasada: nie podawaj liczb stanowych (progi uptime, terminy) bez źródła. Zapisz je w rejestrze źródeł i dopiero wtedy cytuj.

## Zestaw pytań do sprawdzenia
1. Czy stan przyjął HB44 3.40 i w którym wydaniu (2026 vs wcześniejsze)?
2. Czy stan ma własne progi uptime lub raportowania nad federalnymi 97 % i kwartalnymi danymi?
3. Czy wykładnia FHWA lub stanu dopuszcza NACS jako jedyne złącze w projekcie NEVI?
4. Czy po 2026-10-20 zmieniono część 680 (nowy eCFR)?
5. Jaka jednostka NRTL i jakie normy UL są na etykiecie modelu?
