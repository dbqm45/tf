---
name: fe-css
description: Use for styling — flex/grid, responsiveness, design tokens, themes, animations, style isolation.
metadata:
  review: "2027-10-17"
  catalog: "Use when styling components, layouts (flex/grid), responsiveness, design tokens, light/dark themes, animations and style isolation (CSS Modules, scoped, @scope, @layer). Not for JavaScript logic (fe-web-platform) or component structure (fe-architecture)."
---

# CSS

## Tokens first
- Colours, spacing, radii, typography only from tokens (CSS custom properties or the project's theme).
- No "magic" values (`#3a7bd5`, `13px`) in components. A token is missing → add the token.
- Dark mode: you override tokens, not component styles (`color-scheme` + `light-dark()` or `[data-theme]`).

## Layout
- Grid for 2D layouts, flex for 1D. `gap` instead of margins between children.
- Mobile-first: base styles for a narrow screen, `@media (min-width: …)` extends them.
- Prefer container queries for reusable components.
- Units: `rem` for typography and spacing, `%`/`fr`/`min()`/`clamp()` for widths.
- Logical properties (`margin-inline-start`, `padding-block`, `inset-inline`) instead of `left/right` — a layout ready for RTL (fe-web-platform, i18n).

## Architecture
- Stick to the repo's approach (CSS Modules / Tailwind / styled / the framework's encapsulation). Do not introduce a second one.
- Isolation: CSS Modules, `scoped` (Vue), Angular's encapsulation, Shadow DOM or native `@scope`; layer order through `@layer` (reset → tokens → components → utilities).
- Low specificity: classes, no IDs and no `!important` (exception: overriding utilities).
- A component's styles next to the component.

## Accessibility
- Text contrast ≥ 4.5:1 (large text ≥ 3:1).
- A visible `:focus-visible` — never `outline: none` without a replacement.
- `prefers-reduced-motion`: turn off or shorten animations.
- Touch targets ≥ 44×44 px (the WCAG 2.2 AA minimum: 24×24).
- Do not convey meaning by colour alone; respect `forced-colors` (high contrast mode).

## Performance
- Animate `transform` and `opacity`, not `width/height/top/left`.
- `content-visibility: auto` for long off-screen sections.

## References
- `references/css-modules-and-scoped-styles.md` — CSS Modules, `scoped`, `:global`, `composes`, types, build configuration, equivalents in frameworks and `@scope`. Read it when choosing or configuring style isolation.

- `references/ui-review.md` — the order of importance, thresholds (contrast, touch targets, CLS, typography), the list before handing over UI, the main design system document with overrides. Read it when reviewing or handing over a screen.

## Checklist
- [ ] no hard-coded colours/spacing
- [ ] works from 320 px width without horizontal scrolling
- [ ] focus visible, reduced-motion handled
- [ ] dark theme checked
