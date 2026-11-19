# Animations, accessible components, the host element, tests and migrations

Contents: 1. Animations · 2. Angular Aria · 3. The host element · 4. Tests · 5. Automatic migrations · Sources

## 1. Animations
- **Since v20.2:** enter and leave animations through CSS and the `animate.enter="<class>"` and
  `animate.leave="<class>"` attributes on an element in `@if` or `@for`. Angular adds the class for the duration of the animation and removes the element after
  the leave animation ends. You plug in a JS library (e.g. GSAP) with the `(animate.leave)` event and at the end you call
  `event.animationComplete()`.
- State changes: toggling classes (`[class.open]`) and `transition` in CSS; `auto` height through a grid
  (`grid-template-rows: 0fr` → `1fr`).
- **`@angular/animations`** (a DSL in component metadata) is deprecated. It stays in older code, but you do not mix
  it with `animate.enter`/`animate.leave` in one component.
- **Transitions between routes:** `withViewTransitions()` in `provideRouter` (the View Transitions API; in browsers without
  support there is no animation, routing works). The `::view-transition-old()`/`::view-transition-new()` styles in the global
  stylesheet, not in component styles.
- Motion that depends on preferences: `prefers-reduced-motion` (ux-accessibility).

## 2. Angular Aria (`@angular/aria`)
- Directives without a look (headless) for WAI-ARIA patterns: accordion, listbox, combobox and select, menu, tabs,
  toolbar, tree, grid. They handle the keyboard, focus and ARIA attributes; you write the look yourself.
- You style states with attribute selectors: `[aria-expanded="true"]`, `[aria-selected="true"]`, `[aria-disabled="true"]`,
  `[aria-current="page"]`.
- For these patterns you use the `ng*` directives instead of your own keyboard handling or a native `<select>` imitating the
  pattern. You load heavy panel content lazily through content directives in `ng-template`.
- Before use check whether the package is in the project (in v21 in preview, `SKILL.md` → Version-dependent).
- Assessing the accessibility of a whole screen: ux-accessibility.

## 3. The host element
- Bindings to the host element in the `host` field of the `@Component`/`@Directive` decorator (e.g. `'[class.active]': 'active()'`,
  `'(keydown)': 'onKey($event)'`) instead of `@HostBinding`/`@HostListener` in new code.
- A conflict between host bindings and the component user's bindings: static versus static — the user wins; static versus
  dynamic — dynamic wins; dynamic versus dynamic — the component wins.
- You read a static host attribute once at creation: `inject(new HostAttributeToken('type'))`.

## 4. Tests
- **No manual change detection:** in zoneless and `OnPush` applications you do not call `fixture.detectChanges()` or
  `markForCheck()`. The pattern: an action (a signal, an input through `setInput`, a click) → `await fixture.whenStable()` →
  an assertion.
- **Component harnesses** (`@angular/cdk/testing`): `TestbedHarnessEnvironment.loader(fixture)`,
  `loader.getHarness(XHarness.with({ … }))`, then the harness methods (`click()`, `getText()`). The test does not depend on
  the DOM structure and waits by itself. Angular Material and Angular Aria have ready harnesses; for your own complex components
  it is worth writing your own.
- **Routing:** you do not mock the router. `provideRouter(testRoutes)` in `TestBed` and `RouterTestingHarness.create()`;
  navigation `harness.navigateByUrl(url, SomeComponent)` returns the active component, then `await harness.fixture.whenStable()`.
  The test then covers the real guards and resolvers.
- Test strategy and e2e: eng-testing, tool-vitest, tool-playwright.

## 5. Automatic migrations
- Instead of manual text replacement you use the `@angular/core` schematics; the list for the project's version is shown by
  `ng generate @angular/core: --help`. You narrow the scope with `--path <directory>` or `--project <name>`.
- The most common: `control-flow` (`@if/@for`), `signal-input-migration`, `signal-queries-migration`, `output-migration`,
  `inject`, `self-closing-tag`, `standalone`.
- **Standalone in three stages**, with `ng build` and tests after each: (1) converting components, directives and pipes to
  standalone; (2) removing the unnecessary `NgModule`s; (3) bootstrapping the application through the standalone API.
- Moving to `OnPush` and zoneless: first a plan (e.g. the `onpush_zoneless_migration` tool of the MCP server,
  `new-application.md`), then changes in small steps with tests (eng-behavior-preserving-refactoring).

## Sources
- angular/skills, the `angular-developer` skill (angular-developer/references files: angular-animations, route-animations,
  angular-aria, host-elements, testing-fundamentals, component-harnesses, router-testing,
  migrations), commit 43ec6adc2b35049734d0d114e3948e022f1cd1e7 of 2026-10-21, MIT licence, author Google LLC.
  Described in our own words; accessed 2026-10-21.
