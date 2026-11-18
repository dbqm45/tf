# Components, documentation, accessibility, tests

## A component — when and how
- **When:** a pattern used in ≥ 3 places or products, with stable behaviour. The first use stays in the product.
- **API** (Figma = code): variants only for mutually exclusive differences (kind, size), the rest as properties
  (icon yes/no, text, icon swap) and slots. Identical names: `variant=primary`, `size=md`, `disabled`.
  Keep the Figma property → props mapping in Code Connect or in a table in the documentation.
- **States:** default, hover, focus, pressed, disabled, error, loading; a component missing any state
  is not ready.
- **Complexity:** a component with more than about 10 properties you split (e.g. `Button` + `IconButton`) instead of
  adding another flag.

## Accessibility in the component
- A native semantic element before a `div` with a role; the accessible name enforced in the API (no `aria-label` on an icon
  button → a type error or a warning in development mode).
- Keyboard: order, Enter/Space/Esc/arrows by the pattern; focus visible and not obscured; a focus trap
  in a modal dialog with focus returning after closing.
- Touch targets ≥ 24×24 px (WCAG 2.2 SC 2.5.8), 44×44 px recommended; contrast in both themes and brands.
- Automation (axe in Storybook) catches only part of the problems — Storybook says up to 57% — so every component also has
  a manual review with the keyboard and a screen reader (qa-exploratory-manual).

## Component documentation
A fixed page structure, so that it can be checked:
1. What for and when to use it; when **not** (with a pointer to the right component).
2. Anatomy (named parts), variants, states — images from live stories, not manual screenshots.
3. Do / don't — a pair of images with one sentence of justification each.
4. Content: labels, length, tone (ux-content-design, if available).
5. Accessibility: role, keys, announcement, content requirements.
6. API: props with types and default values, component tokens, a code example.
7. Changes: a link to the changelog, the status (experimental, stable, deprecated).
- Storybook: a story per variant and state, `args` for properties, the accessibility panel, interaction tests for complex
  components. The stories are also the data for snapshot tests.

## Snapshot tests (visual regression)
- A snapshot of every story in CI (e.g. Chromatic or Playwright) in both themes and brands; a difference threshold set
  (e.g. 0.1% of pixels) and a stable environment (fonts, browser, no animations).
- A difference = a human review: approval of an intended change (it goes into the changelog) or a bug fix.
  Never automatic approval.
- Exclude variable data from snapshots (dates, random images); animations off or stopped in the final state.
- Snapshots do not replace behaviour or accessibility tests (tool-playwright, qa-regression).
