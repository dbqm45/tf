# Animacje, dostępne komponenty, element hosta, testy i migracje

Spis treści: 1. Animacje · 2. Angular Aria · 3. Element hosta · 4. Testy · 5. Migracje automatyczne · Źródła

## 1. Animacje
- **Od v20.2:** animacje wejścia i wyjścia przez CSS i atrybuty `animate.enter="<klasa>"` oraz
  `animate.leave="<klasa>"` na elemencie w `@if` lub `@for`. Angular dodaje klasę na czas animacji i usuwa element po
  zakończeniu animacji wyjścia. Bibliotekę JS (np. GSAP) podpinasz zdarzeniem `(animate.leave)` i na końcu wywołujesz
  `event.animationComplete()`.
- Zmiany stanu: przełączanie klas (`[class.open]`) i `transition` w CSS; wysokość `auto` przez siatkę
  (`grid-template-rows: 0fr` → `1fr`).
- **`@angular/animations`** (DSL w metadanych komponentu) jest wycofane. Zostaje w starszym kodzie, ale nie mieszasz
  go z `animate.enter`/`animate.leave` w jednym komponencie.
- **Przejścia między trasami:** `withViewTransitions()` w `provideRouter` (View Transitions API, w przeglądarkach bez
  obsługi brak animacji, routing działa). Style `::view-transition-old()`/`::view-transition-new()` w globalnym
  arkuszu, nie w stylach komponentu.
- Ruch zależny od preferencji: `prefers-reduced-motion` (ux-accessibility).

## 2. Angular Aria (`@angular/aria`)
- Dyrektywy bez wyglądu (headless) dla wzorców WAI-ARIA: akordeon, listbox, combobox i select, menu, zakładki, pasek
  narzędzi, drzewo, siatka. Obsługują klawiaturę, fokus i atrybuty ARIA; wygląd piszesz sam.
- Stany stylujesz selektorami atrybutów: `[aria-expanded="true"]`, `[aria-selected="true"]`, `[aria-disabled="true"]`,
  `[aria-current="page"]`.
- Przy tych wzorcach używasz dyrektyw `ng*` zamiast własnej obsługi klawiatury albo natywnego `<select>` udającego
  wzorzec. Ciężką zawartość paneli ładujesz leniwie przez dyrektywy treści w `ng-template`.
- Przed użyciem sprawdź, czy paczka jest w projekcie (w v21 w preview, `SKILL.md` → Zależne od wersji).
- Ocena dostępności całego ekranu: ux-accessibility.

## 3. Element hosta
- Wiązania do elementu hosta w polu `host` dekoratora `@Component`/`@Directive` (np. `'[class.active]': 'active()'`,
  `'(keydown)': 'onKey($event)'`) zamiast `@HostBinding`/`@HostListener` w nowym kodzie.
- Konflikt wiązań hosta i użytkownika komponentu: statyczne kontra statyczne wygrywa użytkownik; statyczne kontra
  dynamiczne wygrywa dynamiczne; dynamiczne kontra dynamiczne wygrywa komponent.
- Atrybut statyczny hosta odczytujesz raz przy tworzeniu: `inject(new HostAttributeToken('type'))`.

## 4. Testy
- **Bez ręcznej detekcji zmian:** w aplikacjach zoneless i `OnPush` nie wołasz `fixture.detectChanges()` ani
  `markForCheck()`. Wzorzec: działanie (sygnał, wejście przez `setInput`, kliknięcie) → `await fixture.whenStable()` →
  asercja.
- **Component harnesses** (`@angular/cdk/testing`): `TestbedHarnessEnvironment.loader(fixture)`,
  `loader.getHarness(XHarness.with({ … }))`, potem metody harnessa (`click()`, `getText()`). Test nie zależy od
  struktury DOM i czeka sam. Angular Material i Angular Aria mają gotowe harnessy; dla własnych złożonych komponentów
  warto napisać własny.
- **Routing:** nie mockujesz routera. `provideRouter(trasyTestowe)` w `TestBed` i `RouterTestingHarness.create()`;
  nawigacja `harness.navigateByUrl(url, Komponent)` zwraca aktywny komponent, potem `await harness.fixture.whenStable()`.
  Test obejmuje wtedy prawdziwe guardy i resolvery.
- Strategia testów i e2e: eng-testing, tool-vitest, tool-playwright.

## 5. Migracje automatyczne
- Zamiast ręcznej zamiany tekstu używasz schematów `@angular/core`; listę w wersji projektu pokazuje
  `ng generate @angular/core: --help`. Zakres zawężasz `--path <katalog>` albo `--project <nazwa>`.
- Najczęstsze: `control-flow` (`@if/@for`), `signal-input-migration`, `signal-queries-migration`, `output-migration`,
  `inject`, `self-closing-tag`, `standalone`.
- **Standalone w trzech etapach**, z `ng build` i testami po każdym: (1) zamiana komponentów, dyrektyw i pipe'ów na
  standalone; (2) usunięcie zbędnych `NgModule`; (3) start aplikacji przez API standalone.
- Przejście na `OnPush` i zoneless: najpierw plan (np. narzędzie `onpush_zoneless_migration` serwera MCP,
  `nowa-aplikacja.md`), potem zmiany małymi krokami z testami (eng-behavior-preserving-refactoring).

## Źródła
- angular/skills, skill `angular-developer` (pliki angular-developer/references: angular-animations, route-animations,
  angular-aria, host-elements, testing-fundamentals, component-harnesses, router-testing,
  migrations), commit 43ec6adc2b35049734d0d114e3948e022f1cd1e7 z 2026-10-21, licencja MIT, autor Google LLC.
  Opisane własnymi słowami; odczyt 2026-10-21.
