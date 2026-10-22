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
