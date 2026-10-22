# Pomiar skilli na modelu — 2026-10-22 (Haiku)

Runner: `tests/run_skill_evals.py --models haiku --isolated` (część z `--baseline`), przestrzeń `.work` ze wszystkimi
nakładkami. Koszt według `total_cost_usd` z Claude Code; zużycie planu Max 5x: ok. 1 punkt procentowy okna na 2 USD
(odczyt człowieka: 5% → 6% po pilotażu za 2,15 USD; dokładność wskaźnika 1%).

## Przebiegi
| Przebieg | Scenariusze | Przebiegi | Koszt | Zaliczone |
|---|---|---|---|---|
| pilotaż (4 skille) | 19 | 19 | 2,15 USD | 18/19 |
| partia 1 (22 skille, z porównaniem bez skilli) | 100 | 175 | 17,46 USD | 90/100 ze skillami |
| powtórka niezaliczonych po poprawkach opisów | 7 + 2 | 9 | 1,06 USD | 9/9 |

Średni koszt przebiegu: ze skillami 0,131 USD, bez skilli 0,058 USD (koszt sędziego wliczony). Sędzia (Sonnet)
uruchamia się tylko, gdy wyrażenia sprawdzające nie trafią: w pilotażu ani razu, w partii 1 przy 60 ze 175 przebiegów.
Kolumna „treść” niżej obejmuje oceny sędziego.

## Wartość skilli — treść odpowiedzi ze skillem i bez (partia 1)
| Skill | Ze skillem | Bez skilli |
|---|---|---|
| core-delivery-lifecycle | 6/6 | 0/6 |
| core-async-delegation | 4/4 | 1/4 |
| core-problem-routing | 2/3 | 0/3 |
| dom-ev-identifiers | 2/2 | 0/2 |
| core-project-record | 4/4 | 2/4 |
| core-agent-security | 7/8 | 5/8 |
| ddd-archetypes | 5/5 | 4/5 |
| bez różnicy: eng-testing, ddd-tactical-design, arch-privacy-compliance, dom-ev-security, dom-ev-charger-hardware, dom-ev-charging, dom-ev-metering-calibration, eng-continuous-delivery, proc-lean, txt-polish-correctness, ddd-deep-modeling | — | — |

„Bez różnicy” nie znaczy jeszcze „skill zbędny”: scenariusze mogą sprawdzać wiedzę ogólną, którą model ma sam.
Przed decyzją o usunięciu zaostrzyć scenariusze tak, by sprawdzały to, co specyficzne dla skilla.

## Poprawki po pomiarze
- Opisy (`description`) core-agent-security, ddd-deep-modeling, core-source-research, docs-tech-writing nazywają
  wprost sytuacje, w których skill się nie wczytywał (obcy skill, obejście hooka, polecenie w zgłoszeniu, wiele do
  wielu, typy definiowane przez administratora, API biblioteki do planu, kiedy pisać ADR).
- `CLAUDE.md`: reguła o obcych skillach wskazuje core-agent-security — model odpowiadał z samej reguły i gubił
  przypięcie wersji i sprawdzenie sieci.

## Dalej
Pozostałe ok. 670 scenariuszy w partiach po ok. 100 (z porównaniem ok. 20 USD, ok. 10% okna limitu).

## Zaostrzenie scenariuszy „bez różnicy” (bez modelu)
Kryteria 12 skilli sprawdzone offline na zapisanych odpowiedziach partii 1: scenariusz odróżnia, gdy odpowiedź ze
skillem przechodzi, a bez skilli nie. Przed zmianą odróżniało 8 z 37 scenariuszy, po zmianie 33 z 37
(+1 nowy, `txt-polish-correctness/wielkie-litery-2026`, bez zapisanych odpowiedzi).
- Nie odróżniają: `eng-continuous-delivery/tbd-flagi`, `txt-polish-correctness/interpunkcja-nie` i `/kalki` (model zna
  te reguły sam — kandydaci do skrócenia skilla) oraz `ddd-deep-modeling/test-zmiennosci`.
- Ustalenia o samych skillach: w `ddd-deep-modeling/test-zmiennosci` odpowiedź ze skillem pominęła test zmienności
  i zasadę „klasę wyznacza skutek dla stanu, nie liczba reguł”; w `eng-testing/jakosc-testow` — zasadę „wartości
  oczekiwane z wymagania, nie z uruchomienia”. Treść skilla do wzmocnienia.
- Błąd w starym kryterium: `dom-ev-security/reset-calej-floty-i-profile` szukał „fale”, odpowiedzi piszą „fali”.
- Kryteria sprawdzono na jednej odpowiedzi na scenariusz; następny płatny przebieg pokaże, czy są stabilne.

## Poprawka treści dwóch skilli
- `ddd-deep-modeling`: test zmienności i zasada „klasę wyznacza skutek dla stanu, nie liczba reguł” stoją teraz przed
  tabelą klas; tabela to „sygnały pomocnicze”, a przy sprzeczności rozstrzyga test.
- `eng-testing`: nowa sekcja „Jakość testów i skąd oczekiwany wynik” łączy pokrycie, testy mutacyjne i oparte na
  właściwościach z zasadami „wartość oczekiwana z wymagania, nie z uruchomienia” i „czerwony test zgodny
  z wymaganiem to defekt w kodzie”.
- Powtórka wszystkich scenariuszy obu skilli (Haiku, 10 przebiegów, 1,19 USD): 10/10, wszystkie przez wyrażenia,
  bez sędziego. `test-zmiennosci` i `jakosc-testow` model obsłużył skillami dopuszczonymi w scenariuszu
  (`ddd-algorithm-recognition`, `qa-spec-first-testing`), więc nowy układ `ddd-deep-modeling` i `eng-testing` nie
  był w nich wczytany — potwierdzi go dopiero kolejna partia.

## Partia 2 (2026-10-22): 141 scenariuszy, 244 przebiegi, 25,71 USD
89 nowych scenariuszy (23 skille) i 52 z 12 zaostrzonych skilli, z porównaniem bez skilli. Zużycie okna: z 3% do
ok. 15% [szacunek]. Koszt przebiegu: ze skillami 18,51 USD łącznie, bez skilli 7,19 USD.

**Zaostrzone skille na świeżych odpowiedziach** (treść ze skillem / bez): dom-ev-security 3/3–1/3, eng-testing
4/4–1/4, ddd-tactical-design 4/4–2/4, ddd-archetypes 5/5–3/5, dom-ev-charging 2/2–1/2, dom-ev-metering-calibration
2/2–1/2, eng-continuous-delivery 2/2–1/2, dom-ev-charger-hardware 3/3–2/3, arch-privacy-compliance 3/4–2/4,
ddd-deep-modeling 3/4–2/4; bez różnicy nadal proc-lean 2/2–2/2 i txt-polish-correctness 2/3–2/3. Zaostrzenie
działa, ale sędzia (Sonnet) bywa łagodny dla odpowiedzi bez skilli.

**Największa wartość nowych skilli:** ddd-model-stress-test 2/2–0/2, dom-ev-tariffs-pricing 4/4–1/4,
dom-ev-regulations-pl 3/3–1/3, eng-behavior-preserving-refactoring 3/3–1/3, core-agent-instructions 4/4–2/4.

**Bez różnicy (scenariusze jeszcze niezaostrzone):** ddd-context-mapping, dom-ev-diagnostics, dom-ev-iso15118,
dom-ev-kpi-analytics, dom-ev-market-roles, dom-ev-ocpp-16, dom-ev-ocpp-2x, dom-ev-regulations-eu,
dom-ev-regulations-us, ops-kubernetes, proc-product-discovery.

**Niezaliczone ze skillem (10, w tym 1 błąd kryterium):**
- nie wczytał się: eng-testing/tdd-nowa-regula, eng-behavior-preserving-refactoring/zapis-pozycyjny-wartownicy;
  wczytał się sąsiad: ddd-context-mapping/event-carried-state (be-messaging-outbox),
  ops-security-operations/terminy-zgloszen (sec-eu-regulations), proc-project-planning/model-cyklu-zycia
  (core-delivery-lifecycle);
- brak treści: arch-privacy-compliance/nowa-funkcja-dane (PKE), ddd-deep-modeling/status-faktury (5 why),
  proc-project-planning/plan-dla-sponsora (karta projektu), txt-polish-correctness/wielkie-litery-2026 (wzmianka
  o zmianie zasad); `dom-ev-regulations-eu/afir-adhoc-terminal-cena` okazał się błędem kryterium (sekcja niżej).

## Zaostrzenie scenariuszy partii 2 (bez modelu)
Kryteria 11 skilli „bez różnicy” sprawdzone offline na odpowiedziach partii 2 (same wyrażenia, bez sędziego).
Rozróżnia 22 z 28 scenariuszy, przed zmianą 4: ddd-context-mapping 2/3, ops-kubernetes 2/2,
proc-product-discovery 3/3, dom-ev-kpi-analytics 3/3, dom-ev-diagnostics 2/2, dom-ev-iso15118 2/2,
dom-ev-market-roles 2/2, dom-ev-ocpp-16 1/2, dom-ev-ocpp-2x 2/2, dom-ev-regulations-eu 2/4, dom-ev-regulations-us 1/3.
- Nowe grupy sprawdzają reguły skilli, których model bez skilla nie podaje, np. dowody przed `Reset`, utilization
  na EVSE zamiast złącza, fakty ISO 15118 z implementacji a nie z normy, okno 12 miesięcy i definicja „up” w NEVI.
- Poprawione fałszywe odrzucenia: odmiany i zapisy dat (CRA), „Aneks I”, „np.” w zdaniu (liveness), seqNo „w obrębie”
  transakcji, uruchomione w trakcie okresu (utilization).
- `dom-ev-regulations-eu/afir-adhoc-terminal-cena` to był błąd wyrażenia `none` (łapało „QR nie wystarcza”), nie
  treści skilla — pozycja schodzi z listy „brak treści”.
- Nie rozróżniają: `ddd-context-mapping/event-carried-state` (wczytał się sąsiad be-messaging-outbox — punkt 2),
  `dom-ev-ocpp-16/status-kabel-bez-autoryzacji` (wiedza podręcznikowa — do zastąpienia trudniejszym scenariuszem),
  `dom-ev-regulations-eu/cra-firmware-terminy` i `/nis2-cpo-zakres`, `dom-ev-regulations-us/nevi-protokoly-cena`
  i `/hb44-kwh-paragon` (model zna CRA i NIS2 albo pobiera eCFR i HB44 sam — kandydaci do skrócenia).
- Kryteria sprawdzono na jednej odpowiedzi; kolejna płatna partia pokaże ich stabilność (na granicy surowości:
  `dom-ev-ocpp-2x/luka-seqno`).

## Dalej
1. ~~Zaostrzyć scenariusze 11 skilli „bez różnicy” z partii 2~~ — zrobione (sekcja wyżej).
2. Poprawić wczytywanie i treść skilli z listy niezaliczonych (opis, kolejność zasad, jak w PR #17 i #19).
3. Kolejne partie: zostało ok. 580 scenariuszy (ok. 100 na partię, ok. 25 USD, ok. 12% okna).
4. Skrócić skille, które po zaostrzeniu nadal nie wnoszą treści (kandydaci: proc-lean, txt-polish-correctness).
Surowe wyniki partii są w scratchpadzie sesji i nie trafiają do repozytorium; ten raport jest ich podsumowaniem.
