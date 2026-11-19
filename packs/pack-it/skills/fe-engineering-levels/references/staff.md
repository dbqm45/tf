# Staff / Senior Staff Frontend Engineer

> **Contents:** Architecture at the scale of many teams · Developer Experience (DevEx) · Standards binding the whole organization · Business communication and ROI · Summary — how Staff differs from Principal

Level: responsibility goes beyond one repo/one team — decisions affect **many teams or
the company's whole frontend domain**. Lens: **many teams, one organization**.

## Architecture at the scale of many teams

**Micro-frontends** — definition, integration variants and trade-offs: fe-architecture
(`.claude/skills/fe-architecture/references/architecture-styles.md`); team boundaries: proc-team-topologies. At the Staff level what additionally matters is:
- **Contracting the boundaries between teams** — micro-frontends solve an organizational problem
  (independent deployments of many teams) at the cost of a technical problem (a shared runtime, duplicated
  dependencies, UX consistency) — the decision to adopt this style is in practice an **organizational** decision
  (a Conway-style mapping of the team structure onto the system structure), not a purely technical one; a Staff engineer must
  be able to justify this decision in business terms, not only technical ones (see "Business communication" below).
- **Maintenance cost** — every extra boundary (repo, deployment, framework version) is a cost forever,
  not a one-off — a decision to split a monolith into micro-frontends should have a clearly named pain threshold
  (e.g. "one team's deployment time blocked by another"), whose resolution justifies this cost.

### Design Systems

A shared library of UI components, design tokens (colours, spacing, typography) and interaction
patterns, used by many teams/applications in the organization — the technical implementation of brand
and UX consistency at company scale.

- **Design tokens** — the lowest level of abstraction: values (`color.primary.500`, `spacing.md`) separated
  from **where** they are used, usually as a source of truth generating CSS custom properties / Sass
  variables / JS objects for many platforms (web, mobile) from one place — a brand change (rebranding) becomes
  a change of token values, not a search through the code of every application.
- **Component levels** (terminology close to Atomic Design, used pragmatically, not dogmatically):
  primitives (Button, Input) → composite components (Card, Modal, a complex Form) → page patterns/templates.
  A Design System is usually responsible only for the first two levels — page templates remain the responsibility
  of the product team (see Feature-Sliced Design — fe-architecture `.claude/skills/fe-architecture/references/fsd-screaming-architecture.md`).
- **Governance** — who can add/change a component in the Design System and how product teams report
  the need for a new component/variant is in practice the same **tight-loose** model described in `devex.md` —
  the API and appearance of a base component are usually "tight" (a shared standard), the way it is used in a particular
  view stays "loose" (the product team's decision).
- **Risk: the Design System as a bottleneck** — if the only team able to change a component becomes
  the central queueing point for all the other teams, the System starts to harm the pace it was meant to
  improve — common solutions: a co-ownership model (contributions from product teams with review by the
  central team), a clear SLA for reviewing contributions, or splitting into layers (a core not changed
  widely + a composition layer that product teams can extend freely).
- **The technical side of tokens and styles** (`@layer` layers, themes, isolation) — fe-css; component accessibility
  (WCAG AA as the "definition of done") — fe-web-platform.
- **Documentation and a "living style guide"** — a Design System without living, always current documentation
  (Storybook or an equivalent) is in practice not used — product teams copy code from older
  places in the codebase instead of reaching for the System, because they do not know what is available.

### Internal frameworks and tooling

At the Staff level a decision to standardize tooling (bundler, test framework, monorepo tooling) for many
teams at once has a different risk profile from a choice in one repo — a mistake is **multiplied** by the number of teams
that later have to migrate it.

- **Vite** — a dev server on native ESM modules (without bundling the whole application at startup — a fast start
  regardless of project size); since Vite 8 it uses **Rolldown** (Rust) for production builds instead of
  Rollup + esbuild. The default choice for new projects (Angular CLI also builds through esbuild/Vite), mainly thanks to
  the speed of the development loop (a DevEx cost — `devex.md`, "flow efficiency").
- **Nx** — a monorepo with a dependency graph, module boundaries (lint), generators, cache and remote cache.
- **Turborepo** — a monorepo management tool with **task caching** (build/test/lint) — a task is
  re-run only when its real inputs (code, dependencies) have changed, with the option of
  a cache shared by the team/CI (remote cache), not only locally. Key for a monorepo of many
  teams, because without it CI time grows linearly with the number of packages, even when only one has changed.
- **Rspack** — a bundler compatible with the Webpack ecosystem/API, but written in Rust — positioned as
  a migration path for large, existing Webpack projects that want the speed gain without rewriting
  the configuration from scratch (unlike moving to Vite, which usually requires a different configuration
  model).
- **The selection rule at the Staff level:** the cost of migrating existing teams to new tooling must be
  explicitly calculated and communicated **before** the decision, not discovered after the fact — this is a direct
  application of the DevEx rule "diagnose the friction before choosing a tool" (`devex.md`) at the level of
  infrastructure, not process.

### Reducing technical debt at the scale of many teams

Technical debt at the Staff level is usually not "this one file needs refactoring" but a **systemic
pattern** repeated in many repos (an outdated framework version used by 10 teams, no
shared testing standard). Practical approaches:
- **Strangler fig** (a migration pattern; safe refactoring — eng-behavior-preserving-refactoring) — gradually replacing the old
  system with a new one while keeping the whole working, instead of a big-bang rewrite.
- **A technical debt budget** as an explicit, negotiated part of the team's capacity (e.g. 20% of a sprint), not
  a task done "when there is time" (which in practice never comes).
- **Migration automation** (codemods, AST-transforming scripts) for repetitive changes across many repos —
  at the scale of many teams, manual repo-by-repo migration does not scale in time.

## Developer Experience (DevEx)

The full content is in `devex.md` (of this skill) — definition, FLOW/DORA metrics, anti-patterns, 9 improvement practices, the
AI-readiness model, the rollout plan. Staff is usually the first level with a real mandate to
**roll out** DevEx changes for many teams (not only report the pain in one's own).

## Standards binding the whole organization

### Accessibility (WCAG)

The A/AA/AAA levels, WCAG 2.2 and legal requirements (European Accessibility Act since 06.2025, ADA) — fe-web-platform
(`.claude/skills/fe-web-platform/references/accessibility/wcag-levels.md`); patterns — same place, `accessibility/`. At the Staff level this is about
**the organization's standard**: **AA as the default requirement** of every new design system component and the "definition of
done" of a feature (not an aspirational goal), an a11y lint and automated tests in the CI of every repo, periodic manual tests with
a screen reader, AAA selectively on critical paths (payment, security).

### Security at the organization level: XSS, CSRF, CSP

Definitions and implementation patterns — fe-architecture (`references/security/`), the server side — be-auth-security.
At the Staff level the key is **enforcing the practices as a standard for many teams**, not only knowing them:

- **XSS** (reflected, stored, DOM-based): a ban on `innerHTML`/`dangerouslySetInnerHTML`/`bypassSecurityTrust*` with
  unsanitized data enforced by **a lint rule in every repo** (and Trusted Types where possible), one
  approved sanitizer for the whole organization. Content from AI models treated like user data.
- **CSRF**: a shared HTTP client adding the token, `SameSite` + the `__Host-` prefix on session cookies, checking
  Fetch Metadata on the server side — one standard instead of per-team solutions.
- **CSP**: rolled out in stages — first `Content-Security-Policy-Report-Only` with report collection, then
  enforcement; ultimately strict CSP (nonce + `strict-dynamic`). Without the report-only stage you risk breaking production
  through an unforeseen, legitimate source.
- Dependencies: SCA/updates (Renovate/Dependabot) and SRI for resources from third-party CDNs as a policy, not an initiative.

### i18n (internationalization)

Technical rules (ICU, plurals, `Intl`, RTL) — fe-web-platform (`.claude/skills/fe-web-platform/references/i18n.md`). The Staff decision:
**one library and message format for all applications**, a shared translation process (TMS, keys with
context for the translator), pseudolocalization in CI; i18n planned as architectural work from the start, because
a retrofit across many repos costs many times more.

## Business communication and ROI

At the Staff level technical decisions (an architecture rebuild, a framework migration, an investment in a Design
System) must be **justified to someone who does not read code** — usually in product/business terms. Practical
rules:

- **Translate a technical cost into a metric the business already tracks** — not "this code is ugly" but "this
  technical debt lengthens the lead time of new features by X days/sprint" (see the DORA/FLOW metrics in `devex.md`) —
  this is the shared language in which a decision becomes calculable, not subjective.
- **The ROI of a technical investment** — for a large investment (a migration, a new Design System, a refactor) give:
  the cost (person-time, the risk of a delivery interruption along the way), the expected benefit (measurable — faster
  deployment, fewer incidents, shorter onboarding), and **the payback time horizon** — a decision without these
  three elements is hard to compare with an alternative use of the same budget of team time.
- **Not every technical decision requires a business justification** — the distinction from the tight-loose model
  (`devex.md`): decisions within "loose" (code style, choice of a local library for one team) do not
  require business escalation; "tight" decisions (affecting many teams/budget/schedule) do
  — the ability to recognize which decision is which is itself part of the Staff competency.

## Summary — how Staff differs from Principal

Staff acts **within one organization/company**, although it affects many teams. When the horizon of a decision
goes beyond one company (influence on industry standards, platforms at the scale of millions of external
users, the company's technological positioning in the market) — that is already the Principal lens, see
`principal.md`.
