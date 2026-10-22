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

## Poprawki po niezaliczonych z partii 2 (bez modelu)
- Opis (wczytywanie): `proc-project-planning` (model cyklu życia: kaskadowy, V, Agile; karta projektu),
  `eng-behavior-preserving-refactoring` (słowo „refaktoryzacja”, czy test wykryje zmianę), `ddd-context-mapping`
  (treść zdarzeń integracyjnych i kopia danych u odbiorcy — przegrywał z be-messaging-outbox).
- Scenariusz: `ops-security-operations/terminy-zgloszen` dopuszcza `sec-eu-regulations` i `arch-privacy-compliance` —
  pytanie o terminy zgłoszeń to ich zakres, a odpowiedź sąsiada spełniła kryteria treści.
- Treść: `txt-polish-correctness` — ściąga w SKILL.md podawała stare zasady wielkich liter (odpowiedź ze skillem
  błędnie uznała „warszawiacy”, „placu Zbawiciela” za poprawne); dopisane zmiany od 2026 z odesłaniem do
  `references/pisownia.md`. `proc-project-planning` — karta projektu do zatwierdzenia przez sponsora.
  `arch-privacy-compliance` — nagłówek punktu o cookies wskazuje SDK analityczne i Prawo komunikacji elektronicznej.
- Bez zmian: `eng-testing/tdd-nowa-regula` (wczytał się w 2 z 3 przebiegów — rozrzut, opis już zawiera TDD),
  `ddd-deep-modeling/status-faktury` (odpowiedź ze skillem ma wynik 5 why — zdarzenie „płatność zaksięgowana”
  i regułę zwolnienia towaru — ale nie nazywa techniki; kryterium zostaje, potwierdzi kolejna partia).
- Skuteczność poprawek opisów potwierdzi dopiero przebieg na modelu (płatny, ok. 1–2 USD za 9 scenariuszy).

## Sprawdzenie poprawek z partii 2 (2026-10-22): 9 scenariuszy, 1,13 USD
Wszystkie 9 niezaliczonych wcześniej scenariuszy przeszło ze skillem (Haiku, jeden przebieg), w tym trzy, w których
wcześniej wczytywał się sąsiad (`ddd-context-mapping`, `proc-project-planning/model-cyklu-zycia`,
`ops-security-operations` przez dopuszczony `sec-eu-regulations`), i `txt-polish-correctness/wielkie-litery-2026`
po dopisaniu zmian zasad od 2026.

## Partia 3 (2026-10-22): 128 scenariuszy, 224 przebiegi, 24,78 USD
31 skilli: rdzeń (11), pozostałe skille nakładki EV (19) i `txt-polish-style`; 96 scenariuszy trigger z porównaniem
bez skilli i 32 no-trigger (wszystkie zaliczone). Ze skillem 89/96 (treść 93/96), bez skilli treść 58/96
(25 z nich dopiero przez sędziego). Koszt: ze skillami 17,88 USD, bez skilli 6,90 USD.

**Największa wartość:** core-knowledge 3/3–0/3, core-plan-interview 3/3–0/3, core-cost-control 8/9–2/9,
core-git-workflow 8/8–3/8, dom-ev-payments 4/4–1/4, core-grounding 3/4–1/4, core-skill-authoring 6/6–3/6.

**Bez różnicy (scenariusze niezaostrzone):** core-semver, core-skill-composition, dom-ev-asset-operations,
dom-ev-certification-testing, dom-ev-charger-onboarding, dom-ev-cpms-architecture, dom-ev-csms-migration,
dom-ev-emsp-platform, dom-ev-fleet-charging, dom-ev-glossary, dom-ev-simulation-testing, dom-ev-v2x,
dom-ev-vehicle-battery, dom-ev-oicp-hubs, dom-ev-site-development, txt-polish-style; core-conventional-commits
gorzej ze skillem (1/2–2/2, bo skill się nie wczytał).

**Niezaliczone ze skillem (7):**
- nie wczytał się: core-conventional-commits/zly-typ-commit, core-cost-control/harness-staly-czy-dowolny,
  core-grounding/liczby-w-raporcie-o-kodzie;
- wczytał się sąsiad: dom-ev-knowledge-base/dodaj-dokument-partnera (core-knowledge — po przeniesieniu mechanizmu
  do rdzenia to poprawny wybór, scenariusz do dopuszczenia), dom-ev-site-development/korytarz-afir-nevi
  (dom-ev-regulations-eu i -us), txt-polish-style/komunikaty-ui (ux-content-design);
- brak treści: dom-ev-oicp-hubs/oicp-vs-ocpi-partner (`eRoamingAuthorizeRemoteStart`).

## Zaostrzenie i poprawki po partii 3 (bez modelu)
Kryteria 17 skilli sprawdzone offline na odpowiedziach partii 3: rozróżnia 39 z 40 scenariuszy, przed zmianą 16.
- Nowe grupy sprawdzają reguły skilli, których model bez skilla nie podaje, np. `Pending` z `interval` zamiast
  `Rejected` przy reconnect storm, `GET` Sessions z `date_from` po timeoucie komendy, `whitelist: ALWAYS` i opóźniona
  blokada tokenu, zakaz ponownego użycia EVSE ID, `rc.1` zamiast `rc1`, pojemność użytkowa zamiast nominalnej.
- Poprawione fałszywe odrzucenia: `ChargingStation`, `AuthorizeRemoteStart` bez prefiksu (oicp-hubs to był błąd
  kryterium, nie luka skilla), „domena rozstrzyga”, odmiany przy EVSE ID i harmonogramie OSD.
- Nie rozróżnia: `txt-polish-style/komunikaty-ui` — model zna zasady mikrotekstu sam; kandydat do skrócenia
  albo odesłania do ux-content-design.
- Opisy (wczytywanie): core-conventional-commits (poprawa złego typu w commicie), core-cost-control (porównanie
  wyników benchmarków, zmiana modelu), core-grounding (twierdzenia w raporcie agenta, liczby).
- Scenariusze dopuszczają właściwego sąsiada: `dom-ev-knowledge-base/dodaj-dokument-partnera` → core-knowledge
  (mechanizm w rdzeniu), `dom-ev-site-development/korytarz-afir-nevi` → dom-ev-regulations-eu/-us (pytanie o same
  przepisy), `txt-polish-style/komunikaty-ui` → ux-content-design.
- Kandydaci do skrócenia (model zna temat sam): ogólna architektura bramy OCPP w dom-ev-cpms-architecture, ogólny
  przepływ komend OCPI w dom-ev-emsp-platform.
- Kryteria sprawdzono na jednej odpowiedzi; na granicy surowości: `dom-ev-v2x/bpt-dynamic-vs-scheduled`,
  `dom-ev-fleet-charging/zwrot-za-ladowanie-w-domu`. Skuteczność opisów potwierdzi przebieg na modelu (ok. 0,40 USD).

## Sprawdzenie opisów rdzenia po partii 3 (2026-10-22): 3 scenariusze, 0,38 USD
- `core-conventional-commits/zly-typ-commit`: skill się wczytał, zaliczone.
- `core-cost-control/harness-staly-czy-dowolny`: skill się wczytuje, ale odpowiedź pomija „harness stały czy dowolny”
  (zasada jest w SKILL.md:144) — treść do wysunięcia wyżej.
- `core-grounding/liczby-w-raporcie-o-kodzie`: nadal się nie wczytuje — opis nie wystarcza, do dalszej analizy.

## Partia 4 (2026-10-22): 150 scenariuszy, 254 przebiegi, 24,69 USD
37 skilli: cała nakładka UX oraz `ai-*`, `arch-*`, `be-*`, `data-*` z nakładki IT; 104 scenariusze trigger
z porównaniem bez skilli i 46 no-trigger (45 zaliczonych). Ze skillem 96/104 (treść 98/104), bez skilli treść
71/104 (17 przez sędziego). Koszt: ze skillami 18,81 USD, bez skilli 5,88 USD. Zużycie okna: z 22% do ok. 34%
[szacunek].

**Największa wartość:** arch-privacy-compliance 4/4–1/4, arch-architect-practice 2/3–0/3, ux-feature-design 2/2–0/2,
ux-design-leadership 3/3–1/3, ux-research-methods 3/3–1/3, arch-tech-selection 3/3–1/3, ai-mlops 3/4–1/4.

**Bez różnicy (do zaostrzenia):** ai-model-optimization, ai-prompt-engineering, ai-rag, ai-research-methods,
arch-ai-solutions, arch-eu-product-law, arch-multi-tenancy, arch-system-design, arch-threat-modeling, be-api-design,
be-auth-security, be-billing-subscriptions, be-database, data-engineering, ux-accessibility, ux-design-systems,
ux-information-architecture, ux-visual-design; data-analysis gorzej ze skillem (1/2–2/2, skill się nie wczytał).

**Niezaliczone ze skillem (9):**
- nie wczytał się: ai-research-methods/wyciek-podzial-czasowy, arch-ai-solutions/lock-in-w-wagach,
  arch-architect-practice/test-odpornosci-decyzji, data-analysis/spadek-konwersji;
- wczytał się sąsiad: arch-threat-modeling/ryzyko-ilosciowe (sec-risk-management);
- no-trigger wczytał skill: ai-evals/macierz-promptfoo-podstawy (obok eng-llm-features);
- brak treści: ai-mlops/od-notebooka-do-continuous-training (walidacja danych),
  ai-product-management/wdrozenie-etapowe-i-niepewnosc (A/B, shadow, canary),
  ux-information-architecture/sortowanie-kart-sklep (sortowanie zamknięte).

## Zaostrzenie i poprawki po partii 4 (bez modelu)
Kryteria 19 skilli sprawdzone offline na odpowiedziach partii 4: rozróżnia 44 z 49 scenariuszy, przed zmianą 6.
- Nowe grupy sprawdzają reguły skilli, których model bez skilla nie podaje, np. PFRON jako nadzór EAA i termin
  deklaracji dostępności, DTCG to raport grupy społecznej (nie standard W3C), najemca z uwierzytelnionej tożsamości
  i test z dwoma najemcami, DPoP, wycofanie komendy kolejną komendą zamiast `DELETE`, „jedna zmiana na raz” w promptach.
- Poprawione fałszywe odrzucenia, m.in. `ux-information-architecture/sortowanie-kart-sklep` (skill każe przy nowym
  sklepie sortowanie otwarte — kryterium wymagało zamkniętego), `be-api-design/idempotencja-platnosci`, „Pewność”.
- Nie rozróżniają (model zna temat sam — kandydaci do skrócenia): `be-api-design/paginacja-kolekcji`,
  `be-database/zmiana-nazwy-kolumny`; bez wczytania skilla: `ai-research-methods/wyciek-podzial-czasowy`,
  `arch-ai-solutions/lock-in-w-wagach`, `data-analysis/spadek-konwersji`.
- Opisy (wczytywanie): ai-research-methods (podział losowy/czasowy/grupowy, offline vs po wdrożeniu),
  arch-ai-solutions (lock-in dostawcy), arch-architect-practice (test odporności, adwokat diabła), data-analysis
  (spadek metryki, paradoks Simpsona), core-grounding (liczby z raportu agenta).
- Treść: core-cost-control (wyników z różnych raportów nie porównujesz wprost — na początku sekcji o ocenie modelu),
  ai-mlops (walidacja danych jako pierwszy krok od notebooka do potoku), ai-product-management (stopniowe
  zwiększanie ruchu nie zastępuje A/B ani shadow).
- Scenariusz `arch-threat-modeling/ryzyko-ilosciowe` dopuszcza sec-risk-management (FAIR w jego opisie).
- `ai-evals/macierz-promptfoo-podstawy` (no-trigger) wczytał ai-evals obok eng-llm-features — prompt dotyka
  ewaluacji; do przemyślenia przy następnej zmianie scenariuszy.
- Inne kandydaty do skrócenia: migracja promptów w ai-prompt-engineering (pokrywa wbudowany skill `claude-api`),
  formaty GGUF w ai-model-optimization, ogólne zasady idempotencji i CDC w data-engineering.

## Sprawdzenie poprawek po partii 4 (2026-10-22): 9 scenariuszy, 1,18 USD
6/9 zaliczonych: wczytują się teraz ai-research-methods, arch-architect-practice, core-grounding, data-analysis;
ai-mlops i ai-product-management podają dopisaną treść. Nadal niezaliczone: `core-cost-control/harness-staly-czy-dowolny`
(skill wczytany, zasada o harnessie dalej pomijana — trzeci raz), `arch-ai-solutions/lock-in-w-wagach` (skill
wczytany, brak „testu wymiany w obu kierunkach”), `arch-threat-modeling/ryzyko-ilosciowe` (sec-risk-management bez
ryzyka rezydualnego).

## Partia 5 (2026-10-22): 135 scenariuszy, 234 przebiegi, 21,84 USD
33 skille `ddd-*`, `eng-*`, `fe-*`, `fw-*`, `lang-*`; 99 scenariuszy trigger z porównaniem bez skilli i 36 no-trigger
(35 zaliczonych). Ze skillem 90/99 (treść 95/99), bez skilli treść 60/99 (13 przez sędziego). Koszt: ze skillami
16,29 USD, bez skilli 5,55 USD. Zużycie okna: z 45% do ok. 57% [szacunek].

**Największa wartość:** ddd-connascence-analysis 3/3–0/3, ddd-legacy-modernization 3/3–0/3, eng-repo-readiness
3/3–0/3, ddd-strategic-analysis 2/2–0/2, eng-module-depth 2/2–0/2, eng-codebase-mapping 5/5–2/5, fw-angular
6/6–3/6, ddd-facilitation 3/3–1/3, eng-refactor-planning 3/4–1/4.

**Bez różnicy (do zaostrzenia):** eng-algorithms-data-structures, eng-debugging, eng-design-patterns, eng-i18n,
fe-architecture, fe-css, fe-engineering-levels, fw-nextjs, fw-react, fw-spring-boot, lang-java, lang-javascript,
lang-python; gorzej ze skillem: eng-clean-code (2/3–3/3) i eng-design-principles (1/2–2/2).

**Niezaliczone ze skillem (10):**
- nie wczytał się: eng-debugging/regresja-200-commitow, eng-refactor-planning/weryfikacja-liczb-rankingu,
  fe-engineering-levels/devex-build;
- wczytał się sąsiad: ddd-discovery-intake/krytyka-pytan-wywiadu (ux-research-methods), eng-clean-code/null-jako-znaczenie
  (eng-design-patterns), fe-architecture/rsc-cve (ops-security-operations, fw-nextjs);
- no-trigger wczytał skill: ddd-algorithm-recognition/klasa-problemu (obok ddd-deep-modeling);
- treść: eng-design-principles/dry-przypadkowe („duplikacja tańsza niż zła abstrakcja”), fw-spring-boot
  (`@WebMvcTest`), eng-tech-debt-audit/hotspoty-i-tani-dlug (wyrażenie `none` „tightly coupled”).

## Zaostrzenie i poprawki po partii 5 (bez modelu)
Kryteria 15 skilli sprawdzone offline na odpowiedziach partii 5: rozróżnia 33 z 42 scenariuszy, przed zmianą 5.
- Nowe grupy sprawdzają reguły skilli, których model bez skilla nie podaje, np. pułapki bisekcji (`--first-parent`,
  test czerwony na HEAD), sprawdzenie `null` raz na granicy, KISS/YAGNI przed DRY, przyszłe zdarzenia jako czas
  lokalny ze strefą IANA, `use cache: remote` i autoryzacja poza proxy w Next.js, typowane identyfikatory w Javie.
- Poprawione fałszywe odrzucenia: `eng-tech-debt-audit` (`none` łapało cytat „tightly coupled” z reguły skilla),
  `core-cost-control/harness-staly-czy-dowolny` (odpowiedź oddaje zasadę innymi słowami — skill był w porządku),
  `arch-threat-modeling/ryzyko-ilosciowe` (strata po kontroli = ryzyko rezydualne), `fw-spring-boot` (`@WebMvcTest`
  tylko jako jedna z alternatyw), odmiany w eng-debugging i fw-react.
- Nie rozróżniają (model zna temat sam — kandydaci do skrócenia): lang-javascript (2 z 3), `lang-java/money-bigdecimal`,
  `lang-python/bez-plikow-nowy-serwis`, `fw-nextjs/hydratacja-daty`, `fw-react/efekt-ponownie-laczy`,
  `fw-spring-boot/test-repozytorium-h2`, `eng-algorithms-data-structures/kolejka-shift`, `eng-design-patterns/switch-strategia`.
- Opisy (wczytywanie): eng-debugging (regresja po wielu commitach), eng-refactor-planning (sprawdzenie liczb rankingu),
  fe-engineering-levels (inwestycja w DevEx), ddd-algorithm-recognition (klasyfikacja CRUD to ddd-deep-modeling).
- Treść: arch-ai-solutions (pogrubiony test wymiany w obu kierunkach), sec-risk-management (wynik FAIR po kontroli
  nazwany ryzykiem rezydualnym).
- Scenariusze dopuszczają właściwego sąsiada: ddd-discovery-intake/krytyka-pytan-wywiadu → ux-research-methods,
  eng-clean-code/null-jako-znaczenie → eng-design-patterns, fe-architecture/rsc-cve → fw-nextjs, ops-security-operations.
- Do rozważenia: w fe-engineering-levels kroki „najpierw diagnoza z trzech źródeł danych, potem próg decyzji”
  przenieść z references/devex.md do SKILL.md.

## Sprawdzenie poprawek po partii 5 (2026-10-22): 10 scenariuszy, 1,21 USD
9/10 zaliczonych, w tym wczytanie eng-debugging, eng-refactor-planning, fe-engineering-levels, brak wczytania
ddd-algorithm-recognition przy klasyfikacji (no-trigger) oraz core-cost-control, arch-ai-solutions
i arch-threat-modeling po poprawkach. Nadal niezaliczone: `eng-design-principles/dry-przypadkowe` — odpowiedź nie
podaje kolejności KISS/YAGNI przed DRY.

## Partia 6 (2026-10-22): 181 scenariuszy, 311 przebiegów, 29,39 USD — koniec pierwszego pomiaru
47 skilli `ops-*`, `proc-*`, `qa-*`, `sec-*`, `tool-*`; 130 scenariuszy trigger z porównaniem bez skilli i 51 no-trigger
(wszystkie zaliczone). Ze skillem 120/130 (treść 121/130), bez skilli treść 91/130 (19 przez sędziego). Koszt: ze
skillami 22,28 USD, bez skilli 7,11 USD. Zużycie okna: od 0% (po resecie) do ok. 14% [szacunek].

**Największa wartość:** qa-change-review 3/3–0/3, proc-issue-triage 2/2–0/2, ops-setup-wizard 2/2–0/2,
tool-playwright 4/4–1/4, tool-vitest 4/4–1/4, qa-spec-first-testing 3/3–1/3, sec-security-leadership 3/3–1/3,
proc-requirements-shaping 4/4–2/4.

**Bez różnicy (do zaostrzenia):** ops-ai-inference, ops-ci-cd, ops-cloud-landing-zones, ops-cloud-migration,
ops-dependency-upgrades, ops-docker, ops-iac-terraform, ops-linux-performance, ops-supply-chain-security,
ops-virtualization-storage, proc-agile, qa-performance-testing, qa-regression, sec-appsec-devsecops,
sec-cloud-security, sec-cryptography-pki, sec-eu-regulations, sec-malware-analysis, sec-risk-management,
sec-zero-trust-identity, tool-jest, tool-pytest, tool-stripe; gorzej ze skillem: ops-linux-networking (1/2–2/2),
ops-platform-engineering (0/3–1/3), sec-governance-compliance (1/2–2/2).

**Niezaliczone ze skillem (10):**
- nie wczytał się: ops-linux-networking/dysk-inody;
- treść albo kryterium (skill wczytany): ops-platform-engineering — wszystkie 3 scenariusze (model dojrzałości CNCF,
  złota ścieżka, GitOps), ops-cloud-migration/cutover-bazy (budżet przestoju), ops-linux-performance/sysctl-tuning
  (nie kopiować tuningu bez hipotezy), ops-multi-region-resilience/replikacja-konflikty-gameday (blast radius),
  sec-governance-compliance/soc2-typ2-mapowanie (Trust Services Criteria), sec-risk-management/rejestr-i-akceptacja
  (apetyt i tolerancja), sec-zero-trust-identity/zt-zamiast-vpn (PDP/PEP).

## Podsumowanie pierwszego pomiaru (partie 1–6)
Wszystkie skille z plikami scenariuszy zmierzone na Haiku z porównaniem bez skilli. Zaostrzenie kryteriów
i poprawki opisów po każdej partii robione offline (bez kosztu); poprawki sprawdzane małymi przebiegami (ok. 1 USD).
Skille, które nie wnoszą treści ponad wiedzę modelu, są wypisane w sekcjach „bez różnicy” i „kandydaci do skrócenia”.

## Zaostrzenie i poprawki po partii 6 (bez modelu)
Kryteria 27 skilli sprawdzone offline na odpowiedziach partii 6: rozróżnia 65 z 74 scenariuszy, przed zmianą 6.
- Nowe grupy sprawdzają reguły skilli, których model bez skilla nie podaje, np. Java 17 przed Spring Boot 3, rejestr
  CIDR przed pierwszą siecią, autoskalowanie inferencji po kolejce zamiast CPU, karencja nowych wersji paczek,
  „0 znalezisk” zakazane bez listy pominiętych, Checkout Sessions zamiast samego Payment Element, termin PQC 2027-01-01.
- Większość porażek ze skillem to były za wąskie kryteria: ops-cloud-migration (budżet przestoju jako „okno 30 min”),
  ops-linux-performance (jeden parametr naraz), ops-platform-engineering (złota ścieżka jako szablon serwisu, GitOps jako
  „przez PR”), ops-multi-region-resilience (limit zasięgu), sec-governance-compliance (kryteria Security/CC),
  eng-design-principles (DRY wygrywa przy jednej wiedzy biznesowej).
- Treść: ops-platform-engineering (samoocena CNCF przy raporcie miar), sec-zero-trust-identity (PEP i PDP na początku),
  sec-risk-management (ryzyka ponad tolerancję nie akceptuje się podpisem); opis ops-linux-networking (pełny dysk
  i i-węzły — skill się nie wczytywał).
- Nie rozróżniają (model zna temat sam — kandydaci do skrócenia): proc-agile/ciecie-historyjek, tool-jest/jest30-aliasy,
  sec-cryptography-pki/szyfrowanie-pii-kms, sec-malware-analysis/podejrzany-plik-triage, dwa scenariusze
  sec-zero-trust-identity; ogólne części ops-docker, ops-iac-terraform, SPF/DKIM/DMARC w ops-linux-networking.

## Przegląd scenariuszy nierozróżniających (bez modelu)
Wszystkie 143 scenariusze, w których odpowiedź ze skillem i bez skilli przechodziła albo odpadała tak samo (ocena
samymi wyrażeniami, bez sędziego), przejrzane jeden po drugim. Po zmianach rozróżnia 522 z 562 scenariuszy z zapisanymi
odpowiedziami (przed: 420).
- A — za wąskie lub za ogólne kryterium, poprawione: ok. 100 scenariuszy.
- B — model zna temat, scenariusz zastąpiony trudniejszym: `dom-ev-energy-management/dlm-fazy-budynek-v2` (L1 ogranicza
  do 11 A, czyli 5,5 A na auto — poniżej minimum 6 A).
- C — luka treści skilla, uzupełniona: dom-ev-regulations-eu (wiersz RED 2022/30 i EN 18031 w tabeli głównej),
  ai-governance-compliance (nadzór człowieka u podmiotu stosującego, art. 26 ust. 2); wcześniej w #30:
  ops-platform-engineering, sec-zero-trust-identity.
- D — model zna temat, skill nie wnosi nic więcej (33 scenariusze) — kandydaci do skrócenia, m.in. proc-lean
  (zasady i WSJF), lang-javascript, tool-nx (tagi i depConstraints), be-api-design (kolekcje), be-database
  (expand/contract), ops-sre-incidents (progi burn rate), sec-llm-security (lista Top 10), txt-polish-correctness
  (imiesłów, kalki), fw-react (`useEffectEvent`), fw-nextjs (hydratacja), core-agent-security (podstawy prompt injection).
- Skażenie porównania: w 2 z 607 przebiegów bez skilli model przeczytał pliki fabryki z dysku poza katalogiem testu
  (`dom-ev-knowledge-base/terminy-przepisow`, `dom-ev-cdr-settlement/sprawdzenie-kosztu-cdr-kalkulatorem`) — przebieg
  „bez skilli” nie jest odcięty od reszty dysku; wyniki tych dwóch porównań pominięte.

## Potwierdzenie poprawek na modelu (2026-10-22): 10 przebiegów, 1,20 USD
8/8 poprawek ze skillem zaliczonych: ops-platform-engineering (samoocena CNCF), sec-zero-trust-identity (PEP/PDP),
sec-risk-management (tolerancja), ai-governance-compliance (nadzór człowieka), dom-ev-regulations-eu (RED/EN 18031),
ops-linux-networking (skill wczytany po zmianie opisu), arch-ai-solutions (test wymiany w obu kierunkach),
eng-design-principles. Nowy `dom-ev-energy-management/dlm-fazy-budynek-v2` zaliczony ze skillem, ale odpowiedź bez
skilli też spełniła kryteria treści — scenariusz nie rozróżnia.

## Skrócenie skilli (bez modelu)
26 skilli krótszych o łącznie ok. 130 linii netto (−201, +74): usunięta wiedza podręcznikowa, którą model zna sam
(m.in. proc-lean 44→25 linii, eng-local-quality-gates, data-engineering, cpms-architecture, sec-llm-security,
ops-observability). Zostały reguły fabryki, nowości wersji i każde zdanie, na którym opiera się kryterium scenariusza
rozróżniającego (sprawdzone narzędziem). Bez zmian, bo wskazany fragment jest podstawą kryteriów albo nowością wersji:
ops-iac-terraform, sec-cryptography-pki, fw-react, fw-angular, lang-python, lang-java, tool-jest. Zysk kosztowy jest
mały — fragmenty z listy były w większości krótkie; główna wartość: mniej treści, która nie zmienia odpowiedzi.

## Dalej
1. ~~Zaostrzyć scenariusze 11 skilli „bez różnicy” z partii 2~~ — zrobione (sekcja wyżej).
2. ~~Poprawić wczytywanie i treść skilli z listy niezaliczonych~~ — zrobione (sekcja wyżej).
3. Partie 1–6 zrobione, zaostrzenie i poprawki po każdej też; poprawki po partii 6 potwierdzone na modelu.
4. ~~Skrócić skille, które nie wnoszą treści~~ — zrobione (sekcja wyżej).
Surowe wyniki partii są w scratchpadzie sesji i nie trafiają do repozytorium; ten raport jest ich podsumowaniem.
