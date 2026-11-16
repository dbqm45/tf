# E2E generowane przez agenta

## Bramka przed napisaniem testu
1. Ryzyko przechodzi przez kilka granic (autoryzacja, routing, API, baza) albo istnieje tylko w wyrenderowanym UI?
   Nie → test niżej (eng-testing, qa-test-design). E2E to najwolniejsza i najbardziej krucha warstwa.
2. Funkcja jest zbudowana i aplikacja startuje? Nie → najpierw implementacja (odwrotnie niż w TDD).
3. Jest już zielony test tego ryzyka? Tak → nie generujesz drugiego. Jest czerwony → to debugowanie (eng-debugging),
   nie generowanie ani „leczenie” testu.

Budżet: zwykle jeden test na ryzyko, 1–3 na fazę strategii testów. Nie „test na każdą stronę”.

## Dwie dźwignie jakości (raz na projekt)
- **Test wzorcowy** `tests/e2e/seed.spec.ts` — agent kopiuje jego styl: co pokażesz, to dostaniesz (`waitForTimeout`
  w seedzie = `waitForTimeout` wszędzie). Seed pokazuje: lokatory wg ról, pełny cykl przygotowanie → akcja → asercja →
  sprzątanie w jednym teście, czekanie na stan, unikalne dane (`Date.now()`), nazwę testu = ryzyko.
- **Reguły E2E** w `CLAUDE.md` projektu: zasady z SKILL.md oraz „asercja na wynik biznesowy”, „unikalne dane
  i sprzątanie w `afterEach`”, „logowanie tylko przez `storageState`”.

Zlecenie dodaje tylko to, czego dźwignie nie znają: ryzyko, ścieżkę, granice prawdziwe i mockowane.

## Szablon zlecenia (bez eksploracji przeglądarki)
Ryzyko (numer i opis z mapy ryzyk) · zakotwiczenie (faza, zmiana) · scenariusz biznesowy = jedno obserwowalne
zachowanie, które staje się asercją · granice prawdziwe (autoryzacja, routing, API, baza — tu siedzi ryzyko) ·
granice mockowane na poziomie sieci (`page.route`: LLM, płatności) · „napisz wg seed i reguł E2E; asercja ma paść,
gdy ryzyko się zmaterializuje; jednym zdaniem podaj, jaką regresję łapie test”.

## Eksploracja przeglądarki przez agenta
- Plan z drzewa dostępności (role, nazwy, stany), nie ze zrzutów. Element bez roli lub nazwy = defekt dostępności.
- Kroki wykonujesz na żywo i piszesz spec z tego, co przeglądarka faktycznie rozwiązała. Jeden test na plik,
  komentarz kroku planu nad akcjami, nagłówek pochodzenia (`// ryzyko: #1 …`, `// wzorzec: tests/e2e/seed.spec.ts`).
- Plan obejmuje ścieżkę główną i przypadek błędu wynikający z ryzyka.
- Transport: **CLI** (`@playwright/cli`, polecenie `playwright-cli`: `open`, `snapshot`, `click`, `fill`, `console`,
  `requests`, `state-save`; migawki na dysku — wyraźnie mniej tokenów w kontekście) przy agencie, który też edytuje
  kod; **MCP** przy sesji poświęconej tylko przeglądarce. Tryb wizyjny wyłącznie dla ryzyk wizualnych.
- Test agents Playwrighta (planner, generator, healer) — SKILL.md, sekcja „Test agents”.

## Przegląd — pięć antywzorców
| # | Antywzorzec | Pytanie kontrolne | Wzorzec docelowy |
|---|---|---|---|
| 1 | asercja pozorna (tytuł strony po przeładowaniu zamiast treści) | czy padnie, gdy ryzyko się zmaterializuje? | asercja na wynik biznesowy |
| 2 | kruchy selektor (CSS, `nth-child`) | czy przeżyje zmianę układu? | `getByRole` / `getByLabel` / `getByText` |
| 3 | stan współdzielony (test B zależy od A) | czy przejdzie sam, w losowej kolejności? | własne przygotowanie w teście lub fixture |
| 4 | czekanie na czas | czy przejdzie na wolnym CI? | `waitForResponse`, `expect(…).toBeVisible()` |
| 5 | brak sprzątania | czy przejdzie dwa razy pod rząd? | unikalne dane + sprzątanie |

Poprawkę zlecasz **po nazwie antywzorca**: co jest źle → dlaczego nie chroni ryzyka (albo daje fałszywe awarie) →
jaki wzorzec go zastępuje. Nigdy samo „popraw ten test”.

## Weryfikacja
Zielony pojedynczy spec → celowe psucie chronionego zachowania (qa-spec-first-testing) → czerwony → przywrócenie.
Zestaw uruchamiasz dwa razy pod rząd (izolacja danych). Pełne E2E w CI; lokalnie tylko nowe specy.

## Sprzątanie danych
Unikalne identyfikatory zapobiegają kolizjom, sprzątanie po teście — gromadzeniu się danych; stosujesz oba.
Sprzątanie w `afterEach` nie wykona się, gdy przygotowanie padnie wcześniej → siatka: projekt `teardown`
w konfiguracji albo „najpierw usuń, potem przygotuj”. Baza z RLS (np. Supabase): klient sprzątający działa na koncie,
które tworzyło dane, albo kluczem serwisowym — inaczej widzi puste tabele i nic nie usuwa.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja 4 (E2E z agentem) — materiał szkoleniowy (dostęp 2026-10-09).
- `@playwright/cli` 0.1.22 — `playwright-cli --help` (polecenia), sprawdzone 2026-10-10.
Opisane własnymi słowami.
