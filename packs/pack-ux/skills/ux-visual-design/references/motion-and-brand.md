# Motion and applying the brand

## Motion — decisions
1. **Purpose:** it shows a relationship (where the window came from), confirms a state change, directs attention. No purpose → no motion.
2. **Duration** (design practice; Material 3 gives its own tokens, e.g. `md.motion.duration.short1` = 50 ms):

   | Type | Duration |
   |---|---|
   | a control state change, a toggle | 100–150 ms |
   | a menu, a tooltip, an expansion | 150–200 ms |
   | a side panel, a modal dialog | 200–300 ms |
   | a whole-view transition | 300–500 ms |

   Distance grows → duration grows (not linearly). Exit about 70–80% of the entrance time. Above 500 ms only for
   rare, highlighted moments.
3. **Curve:** entrance ease-out (a fast start, gentle braking), exit ease-in, movement within the screen
   ease-in-out. Linear only for the rotation of a loading indicator. A custom curve as a token, not a value in the component.
4. **Reduced motion** (`prefers-reduced-motion: reduce`): replace spatial motion (movement, scaling,
   parallax, rotation) with a cross-fade shorter than 150 ms or none; keep the information about the change (a highlight,
   a text change). Motion triggered by a user action falls under SC 2.3.3 (AAA). Automatic motion lasting more than 5 s requires a pause
   (SC 2.2.2), and flashing must not exceed 3 times per second (SC 2.3.1) [unverified in this session].
5. **Specification:** duration, curve, properties (`transform`, `opacity`), start and end state, a reduced
   motion version. A Figma prototype ≠ motion in the product; you verify motion on the implementation.

## Brand
- **Delivered by the brand:** the logo (clear space, minimum size), the primary and secondary colors, the typeface, the tone of photography
  and illustration, usage rules. Any element missing → record an assumption and ask.
- **Brand ↔ accessibility conflict:** accessibility wins. A brand color too light for text → a variant for text and buttons
  with contrast ≥ 4.5:1, the original color on large surfaces, headings ≥ 24 px and in illustrations.
- **Carrying the brand into the UI:** brand → semantic roles (accent, background, surface), not directly into components.
  Thanks to that, a brand change or a second brand is a swap of values, not a rebuild (ux-design-systems, themes).
- **What to avoid:** the logo as a repeating background pattern behind text; ten brand colors in a work interface;
  illustrations in a style different from the rest.
