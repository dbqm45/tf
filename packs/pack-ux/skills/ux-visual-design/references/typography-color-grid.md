# Typography, color, grid, icons

## Typography
- **Scale:** base 16 px × a ratio of 1.2 (minor third, dense UI) or 1.25 (major third, content pages). At 1.25:
  16 → 20 → 25 → 31 → 39. Fewer steps = more consistent; more than 7 is a sign of a mess. Round values to whole px.
- **Line length:** 45–75 characters, ceiling 80 (WCAG 1.4.8, level AAA). You compute the width in `ch` (e.g. `max-width: 66ch`)
  for the typeface and size, not by eye. Columns narrower than 30 characters give ragged paragraphs.
- **Line height:** body text 1.4–1.6; headings 1.1–1.3; the longer the line, the larger the line height. The layout must withstand
  an override per WCAG 1.4.12: line height 1.5, paragraph spacing 2× the size, letters +0.12 em, words +0.16 em — without
  clipping or overlapping (no fixed heights on text).
- **Typeface:** one, at most two; check Polish characters (ą ć ę ł ń ó ś ź ż) and other diacritics in all weights, and tabular
  figures in tables. Weight and size carry hierarchy; small caps and `uppercase` only for short labels.
- **Typical mistakes:** hierarchy with grey color alone; justified text without hyphenation; a heading closer
  to the previous paragraph than to its own; more than 3 weights in one view.

## Contrast — how to compute
1. The WCAG formula: (L1 + 0.05) / (L2 + 0.05), where L is the sRGB relative luminance, L1 of the lighter color.
2. Thresholds: text 4.5:1; large text 3:1; interface elements and focus 3:1 (SC 1.4.11); inactive text is exempt,
   but still leave a readable equivalent.
3. Rounding up is not allowed: 4.49:1 fails.
4. Text on a photo or a gradient: compute at the worst point or add a semi-transparent layer.
5. You compute states (hover, pressed, selected) separately; the focus indicator must not be obscured by sticky
   elements (SC 2.4.11).
- **Color fix:** change the lightness (L in OKLCH or HSL), keep the hue. A set of 10–12 tones per family:
  tones 50–200 backgrounds, 500–600 accent, 700–900 text.
- **Dark mode:** do not invert the light one; lighten surfaces with elevation, lighten and desaturate the accent,
  replace pure black and pure white on large surfaces with intermediate tones.
- **Semantic color:** success, warning, error, information + an icon and text. Yellow rarely passes as text
  on white — use a dark brown on a yellow background.

## Grid and spacing
- A 4 px scale: 4, 8, 12, 16, 24, 32, 48, 64, 96. Within a component 4–16, between components 16–32, between sections
  48–96. The proximity rule: spacing within a group ≤ half the spacing between groups.
- A content page: 12 columns, a 16–24 px gutter, a 16 px margin on a phone. An application: flexible areas
  with minimum widths. Choose breakpoints by the content (when the layout breaks), not by devices.
- Consistent control heights (e.g. 32/40/48 px); horizontal inner padding ≥ vertical.

## Icons and images
- One family, one grid (24 px, a 2 px safe area), one stroke weight; filled icons only for the "active"
  state. An icon without a label only for universal meanings (close, search); the rest with text.
- The size of an icon inline with text: from the cap height to the line height; the touch area independent of the drawing.
- Photos: fixed proportions (16:9, 4:3, 1:1), a defined focal point; illustrations in one palette with the brand.
  Export WebP/AVIF with dimensions (CLS ≤ 0.1) — implementation details in fe-css.
