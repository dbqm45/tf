# Implementation fidelity review and design critique

## Implementation fidelity to the design
1. **Scope:** screens, widths (375, 768, 1280), themes, states (default, hover, focus, error, empty, loading).
2. **Material:** a screenshot from the test environment in fixed conditions (the same browser, 100% scale, the same
   content) and the Figma frame at the same width. An overlay (difference mode) or a side-by-side comparison.
3. **Check in order:** (a) tokens — values from the system, not raw (color, spacing, radius, shadow); (b) typography —
   size, weight, line height, wrapping; (c) spacing and alignment; (d) states and focus; (e) motion; (f) the dark theme;
   (g) extreme content (long, empty).
4. **Tolerances:** spacing and sizes ±1 px (a result of rounding), color 0 (the token value), font — the same typeface
   and weight. Differences below the tolerance are not comments. A difference caused by a design error (e.g. 7 px off
   the scale) goes back to the designer, not to the developer.
5. **Result:** a table `No. | Screen/state | Expected (token) | Found | Severity | Owner`. Severity: blocking
   (accessibility, contrast, focus), fix in this release, cosmetic. Visual regression of repeated components
   is automated with snapshot tests (ux-design-systems).

## Critique of the visual design
- You start from the goal and the author's question; then three categories: hierarchy (what is seen first), readability (contrast,
  scale, line), consistency (system, brand). Every comment: observation → consequence for the user → proposal.
- Format: "The secondary button has 2.6:1 against the background, it does not meet SC 1.4.11; darken the border to ≥ 3:1", not
  "it is too pale". Separate what is measurable (a threshold) from preferences (mark "taste", the author decides).
- You close with a list of agreements with owners; you do not rework someone else's design during the critique.
