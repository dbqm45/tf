---
name: dom-ev-charger-hardware
description: Użyj przy sprzęcie ładowarki EV z perspektywy software — stany CP, PWM i prąd, PP, tryby, złącza, fazy i moc, RCD, licznik MID i Eichrecht.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy firmware, CSMS lub diagnostyka musi rozumieć sprzęt ładowarki — stany Control Pilot A–F i ich mapowanie na StatusNotification, PWM i przeliczenie wypełnienia na prąd, rezystor Proximity Pilot i limit kabla, Mode 1–4, złącza (Type 1, Type 2, CCS1/CCS2, CHAdeMO, NACS/J3400) wg rynków PL/UE/USA, AC vs DC, fazy i moc, RCD typu A/B i wykrywanie 6 mA DC, licznik (MID, Eichrecht, OCMF, podpisane odczyty, NIST HB44). Nie do komunikatów i pól OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x), ISO 15118 i Plug & Charge w szczegółach (dom-ev-charging), diagnozy incydentu od objawu (dom-ev-diagnostics), wprowadzania modelu do sieci (dom-ev-charger-onboarding) ani projektu profili ładowania."
  slowa: "control pilot, CP, stan CP, stan B, stan C, PWM, duty cycle, wypełnienie, proximity pilot, PP, rezystor PP, limit kabla, Type 2, Type 1, J1772, CCS, CCS1, CCS2, Combo, CHAdeMO, NACS, J3400, Mode 3, Mode 2, tryb ładowania, złącze, gniazdo, kabel, faza, trójfazowo, jednofazowo, 230 V, 400 V, 240 V, kW, ampery, RCD, różnicówka, 6 mA, RDC-DD, typ B, licznik, MID, Eichrecht, OCMF, signed meter values, podpisany licznik, legalizacja, NIST HB44, SuspendedEV, SuspendedEVSE, Preparing, auto nie pobiera prądu, ładuje wolniej niż powinno, charger hardware, EVSE hardware, duty cycle to amps"
---

# Sprzęt ładowarki dla oprogramowania

Skill tłumaczy **fizykę i normy sprzętowe na to, co widzi firmware, CSMS i diagnosta**: stan na linii CP, prąd
z PWM, limit kabla, moc, zabezpieczenia, licznik. Nie opisuje komunikatów OCPP (→ **dom-ev-ocpp-16**,
**dom-ev-ocpp-2x**) ani ISO 15118 (→ **dom-ev-charging**). Wartości z oznaczeniem **[do weryfikacji]** pochodzą ze
źródeł wtórnych lub z wiedzy ogólnej; sprawdź je w wymienionej normie przed decyzją projektową (lista:
`references/fakty-do-weryfikacji.md`).

## Procedura
1. Ustal **rynek** (PL/UE, USA, Japonia), **AC czy DC** i **złącze** — to wyznacza normę, napięcie i tryb.
2. Dla AC ustal sygnały: stan CP (tabela niżej), wypełnienie PWM, rezystor PP (tylko Type 2).
3. Prąd dostępny = **minimum** z: limitu z PWM, limitu kabla z PP, nastawy ładowarki (profil ładowania
   z CSMS), zabezpieczenia instalacji i prądu, który pojazd chce pobrać (ładowarka pokładowa).
4. Mapuj stan sprzętu na status OCPP (tabela niżej); odchylenia producenta zapisuj jako quirk (→ dom-ev-charger-onboarding).
5. Rozliczenie za kWh: zapytaj o wymóg licznika legalnego dla rynku (sekcja „Licznik”).

## Stany Control Pilot (IEC 61851-1, SAE J1772)
Ładowarka podaje na CP sygnał ±12 V; pojazd obciąża go diodą i rezystorem, a ładowarka mierzy napięcie szczytu.

| Stan | CP (szczyt) | Znaczenie | Status OCPP 1.6 |
|---|---|---|---|
| A | +12 V **[do weryfikacji]** | brak pojazdu (bez PWM) | `Available` |
| B | +9 V | pojazd wpięty, niegotowy | `Preparing` (bez transakcji); w transakcji `SuspendedEV` |
| C | +6 V | pojazd gotowy, ładowanie (zamknięty przekaźnik) | `Charging`; gdy ładowarka daje 0 A: `SuspendedEVSE` |
| D | +3 V | pojazd wymaga wentylacji | wg producenta; rzadkie, zwykle `Faulted` lub odmowa **[do weryfikacji]** |
| E | zwarcie CP–PE, ok. 0 V | błąd, brak sygnału | `Faulted` |
| F | −12 V **[do weryfikacji]** | ładowarka niedostępna / błąd | `Faulted` lub `Unavailable` |

- Napięcia B, C, D i E pochodzą ze źródła wtórnego; A i F to wiedza ogólna. Tolerancje progów — IEC 61851-1 **[do weryfikacji]**.
- `Finishing`: transakcja zakończona w CSMS, kabel nadal wpięty (CP wciąż B lub C do odpięcia), po odpięciu → A → `Available`.
- `SuspendedEV` = pojazd nie zamyka obwodu mimo PWM (B przy otwartej transakcji); `SuspendedEVSE` = ładowarka
  wstrzymała pobór (limit z profilu, brak zasilania, przekaźnik otwarty). Pomiar prądu 0 A to za mało — sprawdź stan CP.
- Statusy i przejścia → dom-ev-ocpp-16. W OCPP 2.x konektor ma mniej wartości (`Occupied`), a stan ładowania
  przekazuje `TransactionEvent` **[do weryfikacji]** → dom-ev-ocpp-2x.
- Mapowanie jest konwencją producentów, nie normą — nowy model sprawdź na testach akceptacyjnych.

## PWM i prąd (AC)
PWM 1 kHz, ±12 V; wypełnienie D mówi pojazdowi **maksymalny dozwolony prąd** (nie prąd zmierzony).

| Wypełnienie D | Prąd |
|---|---|
| 10–85 % | I = D[%] × 0,6 A |
| 85–96 % | I = (D[%] − 64) × 2,5 A |
| 3–7 % (typowo 5 %) | komunikacja cyfrowa (PLC, ISO 15118); prąd uzgadniany wyżej |
| 8–<10 % | traktowane jak 10 % (6 A) wg źródła wtórnego |
| 100 % (stałe +12 V) / 0 % | stan A bez PWM / stan F (−12 V) |

Przeliczenie odwrotne (firmware ustawia wypełnienie): D = I / 0,6 dla I ≤ 51 A.
6 A = 10 %, 16 A = 26,7 %, 20 A ≈ 33,3 %, 32 A = 53,3 %, 63 A ≈ 89,2 % (z wzoru drugiego zakresu), 80 A = 96 %.
Wzory z kopii SAE J1772 (źródło wtórne) — **[do weryfikacji]** w IEC 61851-1 Annex A i SAE J1772. Wartość 5 % jako
sygnał ISO 15118 **[do weryfikacji]** w ISO 15118-2/-3.

## Proximity Pilot i limit kabla (Type 2)
Rezystor między PP a PE w wtyczce mówi ładowarce (i pojazdowi), **jaki prąd kabel wytrzyma**.

| Rezystor PP | Prąd kabla |
|---|---|
| 1,5 kΩ | 13 A |
| 680 Ω | 20 A |
| 220 Ω | 32 A |
| 100 Ω | 63 A (3 fazy) lub 70 A (1 faza) |

Tabela pochodzi z wpisu na forum, przypisanie do IEC 61851-1 Annex B i tolerancja ±3 % — **[do weryfikacji]**.
Type 1 (J1772) nie ma PP; kabel jest na stałe w stacji, a przycisk zatrzasku ma osobny obwód. Stacja z gniazdem
Type 2 odczytuje PP i **obcina PWM do limitu kabla**; stacja z kablem na stałe ustawia limit z konstrukcji.

## Tryby ładowania (IEC 61851-1)
| Tryb | Opis | Uwagi dla software |
|---|---|---|
| Mode 1 | zwykłe gniazdo, bez kontroli | AC do 16 A wg źródła wtórnego; nie dotyczy CSMS |
| Mode 2 | kabel z urządzeniem kontrolnym (ICCB) | do 32 A; brak OCPP |
| Mode 3 | stała stacja z CP/PWM | wallboxy i stacje AC; to tu działa OCPP |
| Mode 4 | DC z zewnętrznej ładowarki | zakres opisuje IEC 61851-23; źródła rozbieżne |
Opisy trybów — źródło wtórne, **[do weryfikacji]** w IEC 61851-1.

## Złącza wg rynku
| Rynek | AC | DC |
|---|---|---|
| PL / UE | Type 2 (IEC 62196-2) | CCS2 / Combo 2 (IEC 62196-3); CHAdeMO coraz rzadziej |
| USA | Type 1 (SAE J1772), AC 1-fazowe, ok. 19 kW | CCS1 (Combo 1); NACS (SAE J3400) rośnie |
| Japonia | Type 1 | CHAdeMO (brak normy międzynarodowej wg źródła wtórnego) |
Status SAE J3400: Technical Information Report z 2023-12-18, Recommended Practice J3400_202409 z 2024-09-30
(źródła wtórne, strona SAE niedostępna) — **[do weryfikacji]** w SAE J3400. CCS2 = Type 2 + dwa piny DC. W OCPP
jeden **Connector** to jedno złącze fizyczne; ładowarka z CCS2 i CHAdeMO ma dwa konektory, ale zwykle jeden EVSE
nie ładuje obu naraz (pojęcia → dom-ev-glossary).

## AC, DC, fazy i moc
- AC: konwersja w pojeździe (ładowarka pokładowa, często limit 3,7–11 kW); stacja jest „inteligentnym wyłącznikiem”.
- DC: konwersja w stacji; sterowanie prądem przez komunikację cyfrową (ISO 15118 lub DIN 70121), nie przez PWM.
- Moc 1 faza: P = U × I. Moc 3 fazy: P = U × I × √3 (U międzyfazowe 400 V) = 3 × 230 V × I.
- UE: 230 V / 400 V. USA: 120 V (Level 1), 240 V split-phase (Level 2) — zwykle 1 faza.

| Przypadek | Obliczenie | Moc |
|---|---|---|
| UE, 1 faza, 32 A | 230 × 32 | 7,36 kW |
| UE, 3 fazy, 16 A | 400 × 16 × 1,732 | 11,1 kW |
| UE, 3 fazy, 32 A | 400 × 32 × 1,732 | 22,2 kW |
| USA, 240 V, 48 A | 240 × 48 | 11,5 kW |
Pojazd z jednofazową ładowarką pokładową na stacji 3-fazowej pobierze 1/3 mocy — to nie błąd stacji. W OCPP
limity w amperach i watach (`chargingRateUnit`) to osobna warstwa — „profile ładowania”: ładowarka przelicza je na PWM.

## RCD i ochrona
Ładowarka AC Mode 3 musi wykryć prąd upływu DC, którego RCD typu A nie widzi. Dopuszczalne rozwiązania wg
źródła wtórnego (IEC 61851-1 §8.5): **RCD typu B** albo **RCD typu A + wykrywanie DC > 6 mA** z odłączeniem (norma
IEC 62955, moduł RDC-DD). Instalację opisuje IEC 60364-7-722. **[do weryfikacji]** (wydanie IEC 62955: 2018 czy 2023
— źródła rozbieżne). Dla software: zadziałanie RDC-DD lub RCD to `Faulted` (kod błędu producenta), a ponowne
załączenie często wymaga odpięcia kabla — to nie awaria komunikacji.

## Licznik
| Obszar | Wymóg | Co robi software |
|---|---|---|
| UE | MID 2014/32/UE; od 10.10.2028 dyrektywa (UE) 2026/706 dodaje **MI-011 — system pomiarowy EVSE** (AC i DC mierzone w punkcie przekazania, klasy A/B/C = 2/1/0,5 %, MMQ ≤ 0,1 kWh AC i ≤ 1 kWh DC, kabel z wtykiem plombowany albo wymienny z oznaczeniem; zał. Va) | karta ładowarki: klasa, MMQ, certyfikat; wynik w aplikacji tylko jako odczyt powiązany z licznikiem i odporny na manipulację (zał. I pkt 10.6) — przenoś podpisany rekord bez zmian (dom-ev-regulations-eu) |
| Niemcy | Mess- und Eichrecht: odczyt podpisany, weryfikowalny przez klienta | przechowuj rekord podpisany **bez zmian** |
| Format | OCMF: `OCMF|<payload JSON>|<podpis JSON>`, podpis domyślnie ECDSA-secp256r1-SHA256, klucz publiczny poza rekordem | nie parsuj i nie przeliczaj podpisanej części |
| OCPP | Signed Meter Values (OCA, v1.0, 2025) — transport podpisanych odczytów ładowarka → CSMS | zachowaj surową kopertę razem z sesją |
| USA | NIST HB44 §3.40 „Electric Vehicle Fueling Systems” (energia sprzedawana jako paliwo) | wymóg stanowy — sprawdź stan |
Eichrecht dla DC, szczegóły OCA Signed Meter Values i wydanie HB44 — **[do weryfikacji]**
(MID 2014/32/UE + 2026/706, PTB, OCMF, NIST HB44 §3.40). Licznik legalny to licznik **całej sesji**: rozjazd kWh
między CSMS a rozliczeniem diagnozuj w dom-ev-diagnostics.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/fakty-do-weryfikacji.md` | trzeba wiedzieć, co jest potwierdzone, a co wtórne, i gdzie sprawdzić |

## Przykład
**Wejście:** Wallbox z gniazdem Type 2, nastawa z CSMS 32 A, kabel klienta z rezystorem 680 Ω na PP. Auto ładuje
się wolno. Na CP: PWM 1 kHz, wypełnienie 33 %.

**Wynik:** 33 % × 0,6 = 19,8 ≈ **20 A**; rezystor 680 Ω daje limit kabla 20 A. Ładowarka poprawnie obcięła
nastawę 32 A (53,3 %) do limitu kabla. Moc 3-fazowa: 400 × 20 × 1,732 ≈ 13,9 kW (auto jednofazowe: 4,6 kW). To nie
błąd stacji ani CSMS; status OCPP to `Charging`. Rada: kabel 32 A (220 Ω) albo wyjaśnienie klientowi.

## Pułapki
- Wypełnienie PWM to **limit**, nie pomiar prądu; prąd pobiera pojazd.
- Stan B przy otwartej transakcji to `SuspendedEV`, nie `Charging`; prąd 0 A nie rozróżnia `SuspendedEV` od `SuspendedEVSE`.
- Kabel z innym PP niż nastawa: obowiązuje **mniejszy** limit; Type 1 nie ma PP.
- 5 % to nie „5 A” — to sygnał komunikacji cyfrowej.
- 3 fazy: mnożysz przez √3 przy napięciu międzyfazowym 400 V, nie przy 230 V.
- Podpisanego odczytu licznika nie zaokrąglasz ani nie konwertujesz jednostek w rekordzie.
- Napięcia stanów A i F, tabela PP i opisy trybów nie są potwierdzone u źródła — nie wpisuj ich do umowy ani certyfikacji bez normy.

## Checklista
- [ ] Rynek, AC/DC, złącze i tryb ustalone.
- [ ] Prąd liczony jako minimum z PWM, PP, nastawy i pojazdu.
- [ ] Stan CP zmapowany na status OCPP i potwierdzony testem na modelu.
- [ ] Moc policzona z właściwego napięcia i liczby faz.
- [ ] RCD/RDC-DD i licznik (MID/Eichrecht/HB44) opisane w karcie ładowarki.
- [ ] Fakty **[do weryfikacji]** sprawdzone w normie lub oznaczone w wyniku.

## Źródła
Wiedza ogólna o sygnale CP/PWM; tabela researchera `fakty-1c` z 2026-10-20 (źródła wtórne: einfochips, kopia SAE
J1772 na mynissanleaf.com, Wikipedia, jointcharging.com, SAFE-eV OCMF-en.md v1.4.1 z 2025-01-15, globalspec,
voltimum, METAS); `.claude/skills/dom-ev-charging/references/` (import 2024–2025). Strony IEC, SAE, EUR-Lex, NIST
i PTB były niedostępne z sesji researchera.
