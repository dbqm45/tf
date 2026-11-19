---
name: ux-visual-design
description: Use for the look of an interface — hierarchy, typography, WCAG contrast, grid, motion, brand, Figma, fidelity of the implementation to the design.
metadata:
  review: "2027-10-17"
  catalog: "Use for the visual design of an interface and its evaluation — visual hierarchy, the type scale, line length and line height, a color system with a computed WCAG contrast, the grid and the spacing scale, icons and images, motion principles (purpose, duration, reduced motion), applying the brand, practice in Figma (components, variants, auto layout, variables), a review of the implementation's fidelity to the design and a critique of the visual design. Not for flows, screen states and tests with users (ux-feature-design), an accessibility audit and statement (ux-accessibility), CSS code and tokens in code (fe-css) or building a component library, token naming and versioning (ux-design-systems)."
  keywords: "wygląd, UI, ładne, brzydkie, nieczytelne, hierarchia wizualna, font, krój pisma, skala typograficzna, kolory, paleta, kontrast, kontrast WCAG, siatka, odstępy, ikony, animacja, czas animacji, reduced motion, brand, księga znaku, Figma, auto layout, warianty, makieta wizualna, zgodność z projektem, pixel perfect, przegląd wizualny, krytyka projektu, look, pretty, ugly, unreadable, visual hierarchy, typeface, type scale, colors, palette, contrast, WCAG contrast, grid, spacing, icons, animation, animation duration, brand book, variants, visual mockup, design fidelity, visual review, design critique"
---

# Visual interface design — decisions with numbers

Goal: a look that guides the eye, is readable and can be implemented faithfully. The basic principles (one primary action,
states, microinteractions) are in **ux-feature-design** (`.claude/skills/ux-feature-design/references/visual-ui-and-motion.md`) — here you deepen them with a procedure
and compute. Implementation in CSS and tokens in code: **fe-css**; building and maintaining the library: **ux-design-systems**.

## Procedure
1. **Input.** Establish: platforms and widths, modes (light, dark), the brand (brand book, colors, typeface) and the existing
   design system. If there is a system — its tokens and components take precedence over a new idea. No brand
   → ask, do not invent a logo or a palette.
2. **Hierarchy.** List the screen's elements in order of importance for the user's task (1 = primary, max 3 levels).
   You differentiate each level by at least two means: size, weight, contrast, spacing. Test: blur the screen —
   is level 1 still visible? Details and typical mistakes: `references/typography-color-grid.md`.
3. **Typography.** A modular scale (ratio 1.2–1.25) of 5–7 steps on tokens; body text 16 px, line height
   1.4–1.6, headings 1.1–1.3; a line of 45–75 characters (hard ceiling 80). Separate a heading by spacing rather than color.
4. **Color and contrast — you compute, you do not judge by eye.** Roles (background, surface, text, accent, states) instead of hues.
   For every text/background pair give the ratio and the threshold: text ≥ 4.5:1 (SC 1.4.3); large text (≥ 18 pt = 24 px or
   ≥ 14 pt bold ≈ 18.7 px) ≥ 3:1; field borders, icons carrying meaning, focus ≥ 3:1 against the background (SC 1.4.11).
   You compute both palettes (light and dark) separately. Color is never the only carrier of meaning. Fix: darken the tone, do not
   embolden the text.
5. **Grid and spacing.** A 4 px spacing scale (4, 8, 12, 16, 24, 32, 48, 64) from tokens; proximity matters:
   spacing within a group smaller than between groups (at least twice). A 12-column grid for content, flexible for
   applications. Touch targets ≥ 24×24 px (SC 2.5.8), 44×44 px recommended.
6. **Icons and images.** One icon family, one grid (e.g. 24 px, stroke 1.5–2 px), optical alignment; an icon
   carrying meaning has a label. Images: proportions set up front, the focal point of the crop, text on a photo only on a layer
   ensuring contrast; text alternatives are set by the content, not by the visual designer.
7. **Motion.** First the purpose (relationship, state change, direction, attention), then the duration: micro 100–150 ms, panels and dialogs
   200–300 ms, large transitions ≤ 500 ms; exit about 70–80% of the entrance time; entrance ease-out, exit ease-in.
   `prefers-reduced-motion`: replace movement and scaling with a cross-fade or no motion (do not remove the
   information about the change itself). Details: `references/motion-and-brand.md`.
8. **Brand.** The brand gives the accent color, the typeface, the tone of illustrations and photos; it does not override the contrast thresholds or the touch
   sizes. A brand color that fails contrast → a darker variant for text and buttons, the original for large
   surfaces. Multiple brands: `ux-design-systems`.
9. **Figma.** Working rules (components, variants vs properties, auto layout, variables, layer names, handoff)
   in `references/figma.md`.
10. **Implementation fidelity review and critique.** The overlay procedure, tolerances and the comment format:
    `references/visual-review.md`. Write comments against the goal and the threshold ("contrast 3.45:1 < 4.5:1"), not taste.

## Example
Input: helper text `#8A8A8A` on `#FFFFFF`, a button `#3B82F6` with white 14 px text.
Result:

| Pair | Contrast | Threshold | Verdict |
|---|---|---|---|
| `#8A8A8A` / `#FFFFFF`, 14 px text | 3.45:1 | 4.5:1 | fails; change to `#767676` (4.54:1) or the darker `#6B6B6B` (5.33:1) |
| `#FFFFFF` / `#3B82F6`, 14 px text | 3.68:1 | 4.5:1 | fails; use `#2563EB` (5.17:1) |

Additionally: spacing within a card 8 px, between cards 24 px (three times), the type scale 14/16/20/25/31 (×1.25).
Side panel: entrance 250 ms ease-out, exit 200 ms ease-in; with reduced motion only a 100 ms cross-fade.

## Checklist
- [ ] hierarchy in 3 levels, each differing by at least two means
- [ ] the type and spacing scales from tokens; a line ≤ 75 characters (ceiling 80), line height ≥ 1.4 for text
- [ ] contrast computed for every pair in both themes: 4.5:1 / 3:1 / 3:1 for UI elements
- [ ] color is not the only carrier of meaning; touch targets ≥ 24 px
- [ ] motion has a purpose, durations from the thresholds, a reduced motion variant
- [ ] the brand does not break the thresholds; an implementation review with tolerances and a list of differences

## Additional materials
- `references/typography-color-grid.md` — scale, line length, contrast and its fixes, grid, spacing, icons.
- `references/motion-and-brand.md` — durations and curves, reduced motion, applying the brand.
- `references/figma.md` — components, variants, auto layout, variables, handoff.
- `references/visual-review.md` — implementation fidelity to the design and critique.

## Sources
- W3C, WCAG 2.2: Understanding SC 1.4.3 Contrast (Minimum), 1.4.12 Text Spacing, 2.4.11 Focus Not Obscured (Minimum),
  2.5.8 Target Size (Minimum), 2.3.3 Animation from Interactions (accessed 2026-10-17). SC 1.4.11 Non-text Contrast
  (3:1), 2.2.2 and 2.3.1 [unverified in this session, values from WCAG 2.1].
- Material Design 3 — motion tokens (`md.motion.duration.short1` = 50 ms); the other durations in the skill are practice,
  not values from Material [unverified] (accessed 2026-10-17).
- Figma Help Center: Guide to variables, Explore component properties (accessed 2026-10-17).
- Bringhurst, *The Elements of Typographic Style* (45–75 characters per line, after a secondary source [unverified]).
Described in our own words; contrast ratios computed with the WCAG formula (sRGB relative luminance).
