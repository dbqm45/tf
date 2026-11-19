# UI review before handover

The order of importance in conflicts and during a review (higher = more important):
1. accessibility · 2. touch and interaction · 3. performance · 4. style · 5. layout · 6. typography and colour · 7. animation ·
8. forms · 9. navigation · 10. charts.

## The numbers you check
| Area | Threshold |
|---|---|
| text contrast | ≥ 4.5:1 in the light **and** dark theme (3:1 only for large text and non-text elements) |
| touch target | the WCAG 2.2 AA minimum: 24×24 px or adequate spacing; recommended ≥ 44×44 px (WCAG AAA, Apple; Android 48 dp) and ≥ 8 px between targets |
| layout stability | CLS ≤ 0.1 — reserve space for images and content loaded later |
| text | base 16 px, line height about 1.5, nothing below 12 px; a line of 60–75 characters |
| spacing | a 4/8 px rhythm from tokens; dense (dashboard) about 8–32 px, spacious about 24–96 px |

## Rules
- **Colours only from semantic tokens** (fe-css), never raw values in components. You check dark mode
  separately — it does not follow automatically from the light one.
- **Icons:** one family; no emoji as icons; decorative ones with `aria-hidden="true"`; an icon-only button has
  an accessible name and announces its state (`aria-pressed`, `aria-expanded`).
- **Forms:** a visible label (a placeholder is not a label), the error next to the field; with several errors a summary
  with links and focus on it; login fields allow pasting and a password manager.
- **Motion:** `prefers-reduced-motion`; do not animate `width`/`height` (only `transform`, `opacity`); exit faster than
  entry; content that scrolls by itself has a pause.
- **Focus:** pinned elements (header, footer) do not hide the keyboard focus; a drag gesture has an alternative
  in the form of a button.
- Images in WebP/AVIF with dimensions, lazy loading below the first screen.

## The design system in the repository
One main document (e.g. `design-system/MASTER.md`: colours, typography, spacing, components, forbidden patterns) and
overrides per page/area only where they differ. The agent reads the page override first, then the main
document. Changes to the main document only with a human's consent. In Angular, tokens as custom properties in global
styles or in the Angular Material theme.

## The list before handover
- [ ] contrast in both themes, touch targets, focus visible and not hidden
- [ ] no raw colours; icons from one family, accessible names
- [ ] forms with labels and errors next to the fields
- [ ] reduced motion, no animation of dimensions, CLS ≤ 0.1
- [ ] checked at 375 px, 768 px and on a wide screen; no horizontal scrolling

## Source of inspiration
[ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — the order of importance, accessibility thresholds
and the list before handover, the pattern of a main document with overrides (described in our own words; without its style database
and search engine).
