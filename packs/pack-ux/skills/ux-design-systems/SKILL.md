---
name: ux-design-systems
description: Use for a design system — token layers, names, the DTCG format, Style Dictionary, components, Storybook, versions, deprecation, themes, contribution.
metadata:
  review: "2027-10-17"
  catalog: "Use when building and maintaining a design system — token layers (primitive, semantic, component), the naming convention, the Design Tokens format (DTCG) and Style Dictionary, components and variants in Figma and in code, documentation (Storybook, usage rules, do/don't), accessibility built into the component, visual regression tests, library versioning, the changelog and the deprecation policy, the contribution model, governance, adoption metrics, multiple brands and themes. Not for an accessibility audit (ux-accessibility), decisions on look, contrast and motion (ux-visual-design), CSS and CSS variables in code (fe-css), version numbering rules (core-semver) or the structure of a frontend application (fe-architecture)."
  keywords: "system projektowy, design system, biblioteka komponentów, tokeny, design tokens, DTCG, Style Dictionary, nazewnictwo tokenów, motyw, ciemny motyw, wiele marek, white label, Storybook, dokumentacja komponentów, wycofanie komponentu, deprecation, breaking change w bibliotece, changelog, adopcja, governance, współtworzenie, zmienne Figma do kodu, regresja wizualna, Chromatic, component library, tokens, token naming, theme, dark mode, multiple brands, component documentation, component deprecation, library breaking change, adoption, contribution, Figma variables to code, visual regression"
---

# Design system — tokens, components, maintenance

Goal: a shared language of design and code that teams want to use and that can grow without breaking products.
A system is a product with an audience (teams), versions and a roadmap. Decisions on look (contrast, scale, motion):
**ux-visual-design**; implementing variables in CSS: **fe-css**; version number rules: **core-semver**; application structure:
**fe-architecture**.

## Procedure
1. **Input.** How many teams and products, which platforms (web, iOS, Android), how many brands and modes, who maintains it, what
   already exists (an audit: how many unique colors, sizes, button variants in the code). A small system with one team
   does not need the same structure as a system for six — start from what repeats.
2. **Token layers** (details and names: `references/tokens.md`):
   - **primitive** — raw values without meaning (`color.blue.600`, `space.4`);
   - **semantic** — a role, points to a primitive (`color.text.primary`, `color.action.bg`); these are what themes change;
   - **component** — only when a component must depart from the role (`button.primary.bg`), always points to a semantic one.
   References go in one direction (component → semantic → primitive). Components do not use primitives.
3. **Names.** The pattern `category.property.role.state` (`color.border.input.focus`); the name describes the role, not the value
   (not `color.red`, but `color.feedback.error`); one letter-case convention; names in code and in Figma
   identical (up to the separator).
4. **Format and pipeline.** The source of truth in the DTCG format (`$value`, `$type`, aliases `{color.blue.600}`), a
   `*.tokens.json` file; from it Style Dictionary generates CSS, JS/TS, iOS, Android. Which is the source — Figma or the repository
   — decide once; the other side is generated or synchronized one way. Specification status and versions:
   `references/tokens.md`.
5. **Components.** First patterns from the products (the rule of three uses), then a component with an API: variants (kind, size),
   states, slots, usage rules. Variant and property names consistent in Figma and code. Accessibility in the component, not
   "on the user's side": role and accessible name, keyboard, visible focus, touch targets, contrast in both themes.
6. **Documentation.** Storybook (stories for every variant and state, the accessibility panel), a rules page: when to use
   and when not, do/don't with images, button copy, code to copy, accessibility, changes. Format:
   `references/components-and-documentation.md`.
7. **Tests.** An automated accessibility test (axe) on every story — it catches only part of the problems, the rest manually
   (qa-exploratory-manual); visual snapshots of the stories in CI with a difference threshold and changes approved by a human.
8. **Versions and changes.** The library's SemVer (core-semver): the public API is the components, their props, token names
   and classes. A visual token value change = minor or patch by an agreed rule; removal or renaming
   = major. Deprecation policy and changelog: `references/versioning-and-governance.md`.
9. **Contribution and governance.** Acceptance criteria (useful to many teams, unique), the submission route,
   a review rota, who decides. Adoption metrics: `references/versioning-and-governance.md`.
10. **Multiple brands and themes.** A theme = swapping the values of the semantic layer; components unchanged. Scope, names
    and pitfalls: `references/tokens.md` § Themes and brands.

## Example
Input: "Three products, two brands, a dark theme; the button has 11 shades of blue in the code today."
Result (a fragment of `tokens/semantic.tokens.json`):

```json
{
  "color": {
    "action": {
      "bg": {
        "$type": "color",
        "$value": "{color.blue.600}",
        "$description": "Primary button background"
      }
    }
  }
}
```

The dark theme overrides `color.action.bg` to `{color.blue.400}`; brand B to `{color.teal.600}`. The `Button`
component reads only `color.action.bg`. Plan: audit of the 11 shades → 1 semantic token; release 1.0.0 with
the old variables marked as deprecated (until 2.0.0, a transition period of 2 minor releases); a snapshot test of the
`Button` stories in both themes and both brands (6 snapshots).

## Checklist
- [ ] three token layers, references in one direction, components without primitives
- [ ] names describe the role, one convention, the same in Figma and in code
- [ ] the token source of truth decided, the pipeline generates the platforms (DTCG + Style Dictionary or an equivalent)
- [ ] every component: variants, states, accessibility, usage rules, stories
- [ ] accessibility and snapshot tests in CI; a human approves snapshot changes
- [ ] SemVer, changelog, a deprecation policy with a transition period and migration
- [ ] the contribution model and adoption metrics described

## Additional materials
- `references/tokens.md` — layers, names, DTCG and Style Dictionary (status), themes and brands.
- `references/components-and-documentation.md` — components in Figma and code, Storybook, accessibility, snapshot tests.
- `references/versioning-and-governance.md` — library SemVer, deprecation, contribution, metrics.

## Sources
- Design Tokens Community Group, *Design Tokens Format Module 2025.10* — Final Community Group Report, 2025-10-28:
  w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/ (accessed 2026-10-17).
- Design Tokens CG, "Design Tokens specification reaches first stable version" (2025-10-28) and the designtokens.org FAQ
  (accessed 2026-10-17).
- Style Dictionary — v5 adopts DTCG 2025.10 as the base format [unverified, secondary source: zeroheight Help
  Center, accessed 2026-10-17; the latest version number [unverified]].
- GOV.UK Design System: Contribution criteria, Propose a component or pattern (accessed 2026-10-17).
- Figma Help Center: Guide to variables, Explore component properties (accessed 2026-10-17).
- Storybook: "Automate accessibility tests with Storybook" (axe-core detects up to 57% of WCAG issues, according to Storybook;
  accessed 2026-10-17); Chromatic documentation (accessed 2026-10-17).
Described in our own words.
