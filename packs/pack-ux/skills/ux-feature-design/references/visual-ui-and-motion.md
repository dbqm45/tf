# Visual interface, states and motion

Implementation in CSS and tokens: fe-css. Here the design principles.

## Visual hierarchy
- One primary action per screen or section; highlighted by size, contrast, accent color and position. Secondary
  actions visually weaker, dangerous ones separated and described directly ("Delete account", not "OK").
- Reading order: from what the user needs first. Group by proximity and a shared background (Gestalt laws:
  proximity, similarity, common region), not lines everywhere.
- The squint or blur test: can you still see what is most important?

## Typography
- A scale from tokens (e.g. modular, a ratio of about 1.2–1.25), 3–5 sizes in use, not ten. Base 16 px,
  line height about 1.5 for text, tighter for headings; a line of 60–75 characters.
- You build hierarchy with size **and** weight **and** spacing — not with color alone.
- Numbers in tables aligned (`tabular-nums`), to the right; Polish characters (and other diacritics) in all typefaces and weights.

## Color
- Roles instead of hues: background, surface, text, secondary text, accent, states (success, warning, error, info).
  Color is never the only carrier of meaning — add an icon, text, a pattern (color blindness).
- Contrast and dark mode by the thresholds from fe-css (`ui-review.md`).

## Layout and grid
- A spacing rhythm of 4/8 px from tokens; a column grid for content pages, a flexible layout for applications.
- Design from the smallest screen: what stays, what collapses, what turns into another form (table → cards).
- Multi-platform: platform conventions (navigation, gestures, system buttons) matter more than an identical look.

## Component states
Every interactive element: default, hover, focus (visible, not only color), pressed, disabled
(with an explanation why, if unclear), loading, error, selected. A screen: empty, loading (a skeleton for content,
an indicator for actions), partial, error with a fix action, success. Implementation patterns: fe-architecture.

## Microinteractions
Structure (D. Saffer): **trigger** (a user or system action) → **rules** (what happens) → **feedback**
(what is seen and heard) → **loops and modes** (what on repetition). Examples: a toggle with immediate
saving and a message, a character counter, a copy confirmation, undoing a deletion instead of a confirmation dialog.
Feedback within ≤ 100 ms of the action; longer operations — a progress indicator.

## Motion
- Motion has a purpose: it shows a relationship (where the window came from), a state change, a direction. No decorative motion in work
  applications.
- Durations: small elements about 100–200 ms, entrances and larger transitions about 200–300 ms, rarely > 500 ms. Exit shorter
  than entrance. Acceleration at the start and deceleration at the end (ease-out for entrances).
- `prefers-reduced-motion`: replace movement and scaling with a cross-fade or no motion. Animate `transform`
  and `opacity` (fe-css).

## Sources
- [Material Design 2 — Understanding layout](https://m2.material.io/design/layout/understanding-layout.html),
  [States](https://m2.material.io/design/interaction/states.html), [Understanding motion](https://m2.material.io/design/motion/understanding-motion.html)
- D. Saffer, *Microinteractions* (2013); NN/g, [Microinteractions in User Experience](https://www.nngroup.com/articles/microinteractions/)
- [roadmap.sh — Product Design](https://roadmap.sh/product-design) (visual foundations, hierarchy, typography,
  color, layout & grid, interface states, micro-interactions, motion principles)
Described in our own words.
