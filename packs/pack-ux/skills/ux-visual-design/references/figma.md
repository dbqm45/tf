# Practice in Figma

Documentation: Figma Help Center, "Guide to variables in Figma", "Explore component properties". The component
library as a product (names, versions, releases): ux-design-systems.

## Components
- First a pattern in the screens, then a component when it is used ≥ 2 times. A base component + instances; do not detach
  instances for one difference — add a property.
- A **variant** for large, mutually exclusive changes (kind, size, state); **properties** for small ones:
  boolean (show the icon), text, instance swap (an icon from a list). A slot — a flexible area for content (a newer feature,
  check availability on your plan [unverified]).
- Property names as in code (`size=md`, `state=hover`, `hasIcon`), so that the handoff needs no translation.
- States: default, hover, focus, pressed, disabled, error, loading — each as a variant.

## Auto layout
- Every component with auto layout: direction, gap and padding from variables; the sizing behaviour "hug" (content)
  or "fill" (container) chosen consciously. Test: shorten and lengthen the text (1 word, 3 lines) — the layout must hold.
- Min/max width constraints reflect the CSS; screen frames at widths of 375, 768, 1280 px.

## Variables
- A collection contains variables and modes (e.g. light/dark, brand A/B); a variable can point to another (an alias) of the same
  type. Layers: a primitives collection, a semantic collection with modes, possibly a component one (ux-design-systems).
- Types: color, number (spacing, radii), string, boolean. You use variables instead of local styles
  where a mode is needed. A raw value in a component is a review error.

## Order and handoff
- Pages: Cover, Foundations, Components, Patterns, Screens (the "ready for development" status marked).
- Meaningful layer names; no hidden leftovers; annotations of focus, accessible names and live regions.
- Dev Mode and Code Connect link Figma components to code; keep the property-to-props mapping with the code team.
