# WCAG — conformance levels and legal requirements

Moved from the frontend-developer import (`staff.md`, "WCAG — conformance levels"), updated to WCAG 2.2 and
the legal situation of 2026.

## Version

- The current W3C recommendation: **WCAG 2.2** (October 2023). WCAG 3.0 is
  a working draft — do not design conformance for it.
- WCAG 2.2 added, among others: **2.4.11 Focus Not Obscured (AA)** — focus must not be entirely hidden (a sticky header,
  a cookie banner); **2.5.7 Dragging Movements (AA)** — an alternative to dragging; **2.5.8 Target Size Minimum (AA)** —
  targets ≥ 24×24 CSS px (or spacing); **3.2.6 Consistent Help (A)**; **3.3.7 Redundant Entry (A)** — do not make people enter
  the same thing a second time; **3.3.8 Accessible Authentication (AA)** — no cognitive tests (allow pasting passwords,
  password managers, passkeys). 4.1.1 Parsing was removed (obsolete).

## Levels

- **A (minimum)** — barriers that block access completely (no alternative text, content not reachable from
  the keyboard). Below this level the product is unusable for some people, not "inconvenient".
- **AA (the legal standard)** — the reference level of regulations: text contrast **4.5:1** (large text **3:1**), the contrast
  of UI elements and the focus indicator **3:1** (1.4.11), zoom to 200% and reflow from 320 px without loss of function,
  a visible focus, touch targets ≥ 24×24 px (the internal standard is often 44×44 — fe-css). **The default requirement for
  every new component and design system**, not an aspirational goal.
- **AAA** — e.g. contrast **7:1**, 2.4.13 Focus Appearance; some criteria cannot be met for certain content
  (e.g. sign language for all recordings) — apply selectively on critical paths, not globally.

## Law (2026)

- **EU — European Accessibility Act** applied since **28 June 2025** (in Poland: ustawa o zapewnianiu spełniania
  wymagań dostępności niektórych produktów i usług — the act on ensuring that certain products and services meet accessibility requirements): e-commerce, banking, transport, e-books, communications.
  The point of reference: the **EN 301 549** standard (it refers to WCAG 2.1 AA; the next version — to 2.2). The public sector:
  directive 2016/2102 (in PL the ustawa o dostępności cyfrowej — the digital accessibility act).
- **USA** — ADA Title II (the 2024 DOJ rule: WCAG 2.1 AA for state/local government, deadlines 2026–2027);
  Section 508; for private entities — ADA Title III case law.

## How to verify

- Automated tools (axe, Lighthouse, Playwright `toMatchAriaSnapshot` — tool-playwright) catch approx. 30–40% of problems.
- The rest manually: the keyboard alone, a screen reader (NVDA/JAWS, VoiceOver, TalkBack), zoom of 200–400%,
  `prefers-reduced-motion`, high contrast mode (`forced-colors`).
- At the organization level: AA as the "definition of done" criterion of a component, lint (e.g. `eslint-plugin-jsx-a11y`,
  `@angular-eslint/template` accessibility rules), a11y tests in CI — fe-engineering-levels (Staff).
