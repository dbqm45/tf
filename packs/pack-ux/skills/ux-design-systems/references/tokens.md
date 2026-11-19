# Tokens — layers, names, format, themes

## Contents
Layers · Names · DTCG · Style Dictionary · Themes and brands · Pitfalls

## Layers
| Layer | Example | Who uses it | Changes with |
|---|---|---|---|
| primitive (reference) | `color.blue.600` = `#2563EB`, `space.4` = 16 px | only the semantic layer | a palette change |
| semantic (system) | `color.action.bg`, `space.inset.md` | components and products | theme, brand |
| component | `button.primary.bg` | one component | the component departing from the role |

- You add the component layer only when a component must have a value different from the role; in a small system the pair
  primitive + semantic is often enough. Sources differ on strictness (whether a semantic token may point to a
  semantic one); adopt a one-direction rule and keep it across all teams.
- The primitive scale: color 10–12 tones per family, spacing on a 4 px scale, typography on a modular scale (values
  decided by ux-visual-design).

## Names
- Pattern: `category.[subcategory].property.role.[state]`, e.g. `color.text.secondary`, `color.border.input.focus`,
  `space.inset.md`, `radius.control`, `motion.duration.short`.
- The name says **what for**, not **how it looks**: `color.feedback.error`, not `color.red`; sizes on an
  `xs–xl` or numeric scale, not `big`/`bigger`.
- One letter-case and separator convention (e.g. a dot in DTCG, kebab-case in CSS: `--color-text-secondary`);
  the conversion is a job for Style Dictionary, not a manual one.
- A token name is public API: renaming is a backwards-incompatible change (versioning-and-governance.md).

## DTCG — the format
- The *Design Tokens Format Module* specification has its first stable version 2025.10 (Final Community Group Report,
  2025-10-28). The group is not on the W3C standards track — it is a community group report, so do not call it
  "a W3C standard". Further, superseding versions are announced.
- A token is an object with `$value`; `$type` (e.g. `color`, `dimension`, `duration`) can be set on the token or the group
  (inheritance); `$description` optional; `$extensions` for tool data (a key with the vendor name).
- An alias: the value `{path.to.token}` [unverified in this session, syntax from earlier versions of the specification].
- Media type: preferred `application/design-tokens+json`, allowed `application/json`; file extension
  `.tokens` or `.tokens.json` [unverified in the specification text, secondary sources].
- Token deprecation: the `$deprecated` field [unverified in this session]; until certain, record the deprecation also
  in `$description` and in the changelog.
- Fields starting with `$` are reserved; token names do not start with `$` and do not contain `{`, `}`, `.`.
  [unverified]

## Style Dictionary
- Transforms tokens into platform artifacts: CSS custom properties, JS/TS, XML for Android, Swift for iOS.
  Configuration: sources (`source`), platforms, transforms (color, units, names), formats, output files.
- Version 5 adopts DTCG 2025.10 as the base format (secondary source) [unverified]; check the number and the support for composite types
  in the documentation and the repository's `package.json` before you plan a migration from version 3/4.
- Pipeline: Figma (variables) → export/plugin → `*.tokens.json` in the repository → Style Dictionary in CI → a
  versioned package. One direction; manual edits in generated files are forbidden.

## Themes and brands
- A theme (light/dark) and a brand (A/B) are **axes** of the semantic layer's values. Two axes = a matrix (brand × mode);
  generate it, do not maintain it by hand. In Figma: a semantic collection with modes; in CSS: a set of custom properties under
  an attribute (`[data-theme]`, `[data-brand]`) — the implementation in fe-css.
- Brand scope: colors, typeface, radii, possibly icons; layout and behaviour shared. A brand that changes
  a component's behaviour is a separate component.
- Every combination passes contrast (ux-visual-design): an automated test computing text/background pairs from the tokens.

## Pitfalls
- A raw value in a component bypasses themes. Forbid it in linting (e.g. a stylelint rule for colors and spacing).
- Too many component tokens: hundreds of names without a user. Add them on demand of use.
- A semantic token named after one use (`color.header.bg`) — it does not carry over; name the role.
