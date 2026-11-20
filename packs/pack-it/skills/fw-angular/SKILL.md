---
name: fw-angular
description: Use for Angular 17–22 code — standalone, signals and resources, zoneless, Signal Forms, DI, HttpClient, routing, tests.
metadata:
  review: "2027-01-17"
  catalog: "Use for Angular code (17–22) — standalone components, signals and resources, zoneless/OnPush, Signal Forms, DI, HttpClient, routing, tests — and when deciding where to place domain concepts in an Angular application. Covers the differences between versions (the Version-dependent section). Not for TypeScript syntax (lang-typescript) or modeling (ddd-*)."
  keywords: "ng update, aktualizacja Angulara, zaktualizować Angulara, przejść na nowszego Angulara, migracja Angulara, przejście na nowszą wersję Angulara, komponent Angulara, szablon, nowa aplikacja w Angularze, formularze w Angularze, detekcja zmian, zoneless, ng new, ng generate, ng add, nowy projekt Angular, SSR w Angularze, prerendering, hydratacja, RenderMode, @defer, animate.enter, animacje w Angularze, Angular Aria, component harness, RouterTestingHarness, migracja do standalone, serwer MCP Angular, Tailwind w Angularze, Angular update, update Angular, move to a newer Angular, Angular migration, moving to a newer Angular version, Angular component, template, new Angular application, Angular forms, change detection, new Angular project, Angular SSR, hydration, Angular animations, migration to standalone, Angular MCP server, Tailwind in Angular"
---

# Angular

**First check the version in the project** (`detect_stack.py` / `package.json`). The conventions below describe modern
Angular; in older versions take from the "Version-dependent" table the equivalent available in the project.

## Conventions
1. **Standalone components** (the default — no need to write `standalone: true`); no new `NgModule`.
2. **Signals for state:** `signal`, `computed`, `linkedSignal`, `input()`/`input.required()`, `output()`, `model()`;
   `effect` only for side effects outside Angular (not for synchronizing state).
3. **Asynchronous reads through resources:** `httpResource` / `resource` / `rxResource` (status idle → loading → resolved/error,
   `reload()`); `debounced()` for search fields. RxJS where there are real streams; `toSignal` at the boundary.
4. **Change detection:** zoneless applications and `OnPush` components — a component depends only on inputs and signals.
   In existing code with the `Eager` strategy (formerly `Default`) do not change it wholesale without tests.
5. **The new control flow** in templates: `@if`, `@for (…; track id)`, `@switch`, `@defer`; no `*ngIf/*ngFor` in new code.
   A template without business logic — even if the syntax allows it (arrow functions, spread), logic goes into `computed`.
6. **DI through `inject()`**; application services `@Service()` (shorthand for `@Injectable({ providedIn: 'root' })`);
   lazy loading of heavy services through `injectAsync()`; feature state provided at the route level.
7. **Forms:** new forms in **Signal Forms** (`@angular/forms/signals`: `form()`, a schema with `validate()`,
   `required()`…, the `[formField]` directive); existing Reactive Forms (typed, `nonNullable`) stay. Validation rules
   as pure domain functions — plugged into both APIs.
8. **HTTP:** `HttpClient` available by default and based on the Fetch API; functional interceptors (auth, errors, correlation);
   mapping DTO → domain types at the edge (e.g. the `parse` option in `httpResource`), not in the component.
9. **Routing:** lazy routes (`loadComponent`, `loadChildren`), functional guards and resolvers, `withComponentInputBinding()`.
10. **Tests:** Vitest (`@angular/build:unit-test`); domain logic without `TestBed`; components `await fixture.whenStable()`.
11. **Updates:** `ng update` (or `nx migrate` in an Nx monorepo) — automatic migrations instead of manual changes;
    code modernization with the `ng generate @angular/core:<migration>` schematics (`references/ui-tests-migrations.md`).
12. **CLI instead of manual files:** a new application `ng new … --interactive=false` with flags from the description, code through
    `ng generate`, libraries through `ng add`; after every change `ng build` and fixing errors before handing over
    (`references/new-application.md`). File names consistent with the style the project already has.
13. **Animations** through CSS and `animate.enter`/`animate.leave` (since v20.2); `@angular/animations` only in older code.
    Host bindings in the `host` field, not `@HostBinding`/`@HostListener`.
14. **SSR:** a rendering mode per route (`RenderMode`), the same DOM on the server and in the browser, browser-only
    work in `afterNextRender`/`afterRenderEffect` (`references/rendering-and-ssr.md`).

## Domain concepts in Angular — where things live
| Concept (glossary) | Place in an Angular application |
|---|---|
| **value object** | pure TS in `domain/` (lang-typescript); in the UI a **pipe** for formatting (e.g. `money`), a custom form control (`FormValueControl` in Signal Forms / `ControlValueAccessor`) when the field repeats in many forms |
| **entity** | a domain type in `domain/`; the component receives it through `input()` and does not modify it |
| **variants** | `@switch` on `kind` in the template; separate presentational components for strongly different variants |
| **operation result** | the command state in the store (`idle / pending / done / rejected`); a rejection (409/422) as a message, not an exception |
| **aggregate** | usually **on the backend**; in the frontend only when it works offline/locally — a class in `domain/`, the store calls its methods |
| **state machine** | a union of states in the store's signal; the view depends on `computed` over the state |
| **event** | UI events through `output()`; domain events from the backend (WebSocket/SSE) update the read model in the service |
| **policy** | a pure function in `domain/`; injected with a token (`InjectionToken`) when the variant depends on configuration |
| **specification / rules** | pure functions in `domain/` → `validate()` in a Signal Forms schema, `ValidatorFn` or `computed` |
| **repository / port** | a data service (`@Service()`) with `HttpClient`/`httpResource`, mapping DTO ↔ domain types — the feature's **edge** |
| **read model** | `httpResource`/`resource` in the feature store; views read through `computed` |
| **module** | a feature directory (`features/<name>/`) with a route and a public `index.ts` (in Nx — a library with tags); `domain/` without imports from `@angular/*` |

Tested adapters (Angular 22, `ngc` + `strictTemplates`): the `money` pipe, a characteristic field in Signal Forms and a Reactive
Forms validator from the same rule, a store with `@Service` + `httpResource` + command state, a Party variant component:
`references/domain-adapters.md` (with equivalents for older versions).

## Materials (read only the file you need)
- `references/new-application.md` — `ng new` and flags, `ng generate`, `ng add`, Tailwind v4, file names since v20,
  environments, the Angular CLI MCP server.
- `references/rendering-and-ssr.md` — CSR/SSG/SSR, `RenderMode` per route, hydration, server-compatible code, request
  tokens, transfer cache, `@defer` (triggers, `hydrate on`, layout stability).
- `references/ui-tests-migrations.md` — animations, route transitions, Angular Aria, the host element, tests without
  `detectChanges`, component harnesses, `RouterTestingHarness`, migration schematics.
- `references/domain-adapters.md` — tested domain adapters (below).

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 17 | the new control flow (`@if/@for/@switch`), `@defer`; the `application` builder (esbuild); in 17.1–17.3 `input()`, `model()`, `output()` in developer preview |
| 18 | zoneless experimentally; `@let` (18.1); form events (`events`) in Reactive Forms |
| 19 | **standalone by default**; `input`/`output`/`model` and signal queries stable; `linkedSignal`, `resource`/`httpResource` (19.2) experimental; incremental hydration (preview); TS ≥5.5 <5.9 |
| 20 | stable `effect`, `linkedSignal`, `toSignal`; zoneless in developer preview; file names without the role suffix in the style guide; `animate.enter`/`animate.leave` (20.2); structural `*ngIf/*ngFor/*ngSwitch` deprecated; TS ≥5.8 <6.0 |
| 21 | **zoneless by default** (Zone.js only through `provideZoneChangeDetection()`); **Vitest the default runner** (`await fixture.whenStable()`); **HttpClient available by default**; Signal Forms experimental (`@angular/forms/signals`); `@angular/aria` in preview; TS ≥5.9 <6.1 |
| 22 | **`OnPush` by default** (`ChangeDetectionStrategy.Default` → `Eager`; the migration adds `Eager` where needed); **Signal Forms stable**; `resource`/`httpResource` stable; `@Service()`, `injectAsync()`, `debounced()`; HttpClient on the Fetch API (`withFetch()` deprecated, `withXhr()` as an option); `?.` in templates returns `undefined` as in TS; `strictTemplates` by default; incremental hydration by default; `canMatch` with a third parameter; `paramsInheritanceStrategy: 'always'`; Webpack and the `@angular-devkit/build-angular` builder deprecated; **TS ≥6.0 <6.1** (TS 7 not supported — no compiler API); Node ^22.22 / ^24.15 / ≥26 |

Equivalents for older versions: `@Service()` → `@Injectable({ providedIn: 'root' })` (<22); `httpResource` →
a service with `HttpClient` + `toSignal` (<19, experimental 19–21); Signal Forms → typed Reactive Forms (<21, experimental in 21);
zoneless → Zone.js + `OnPush` (<20).

## Checklist
- [ ] the Angular version in the project checked; the APIs used are available in that version
- [ ] no new `NgModule` and `*ngIf/*ngFor`
- [ ] `domain/` does not import `@angular/*`; DTO → domain mapping at the edge
- [ ] command states explicit (pending/rejected), conflicts handled in the UI
- [ ] `ng build` passes after the changes; tests without `detectChanges` (`await fixture.whenStable()`)

## Sources
- angular/skills (`angular-developer`, `angular-new-app`), commit 43ec6adc2b35049734d0d114e3948e022f1cd1e7
  of 2026-10-21, MIT licence, author Google LLC — CLI, SSR, animation, test and migration conventions in the
  `references/` files; described in our own words, accessed 2026-10-21.
