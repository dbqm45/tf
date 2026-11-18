# Diagrams, explanation pages and presentations

## 1. When a picture, when text
- A table with 4+ rows or 3+ columns, or a comparison of several options → a table (in Markdown) or an HTML page, and in the chat
  a short summary, not ASCII art.
- Flow, sequence, states, data model, system context → a diagram. A long description in prose → cards/sections.
- With 15+ elements: a small overview diagram + details in cards or separate diagrams.

| What you show | Form |
|---|---|
| flow, decisions | Mermaid `flowchart` (by default `TD`; `LR` only for 3–4 nodes) |
| exchange of messages over time | `sequenceDiagram` |
| states of an object (e.g. an aggregate) | `stateDiagram-v2` |
| data model | `erDiagram` / `classDiagram` |
| the system and its surroundings, containers | C4 (PlantUML C4; in Mermaid C4 is experimental) |
| timeline, roadmap | a table or `timeline` |

## 2. Diagram content
- Draw the **mechanism**, not boxes with names: what flows, who calls, what is written.
- **Every arrow has a label** (≤ 3 words). One diagram = one claim, and the caption states it.
- When comparing options, draw the difference between them, not two full systems.
- Do not invent responsibilities, protocols or numbers — if a fact is missing, ask or mark it "to be determined".

## 3. Notation conventions
| Element | Meaning |
|---|---|
| solid, thick line | main flow |
| solid line | control / call |
| dashed | data write, asynchronous communication (events, queue) — in the legend, which variant |
| cylinder | persistent data store |
| hexagon | API / gateway |
| diamond | decision |
| dashed border | external or temporary system |
UML: hollow triangle = inheritance (dashed — interface implementation), filled diamond = composition, hollow diamond =
aggregation; multiplicities at the ends; on state transitions `event [condition] / action`.
Two or more kinds of arrows → a legend.

## 4. Readable layout
- 0 line crossings as the goal; at most 2 bends per edge — more means the nodes need moving.
- Elements of one layer in one row; between the layers a free corridor for the connections.
- Too tight → widen or split the diagram, **do not shrink the text**.
- **Look at the result** before you consider the work done (Mermaid preview, PNG): cut-off labels, overlaps, contrast.
  If you cannot see it, say so.

## 5. Mermaid — pitfalls
- A line break in a label: `<br/>`, not `\n`.
- Do not override the `.node` class in the page CSS — Mermaid uses it.
- Complex diagrams: the ELK layout, if the renderer supports it (Mermaid 11+: `layout: elk` with the package `@mermaid-js/layout-elk`); the `base` theme with your own variables instead of the default, if the repo has color tokens.

## 6. An HTML page with an explanation (review of a plan, a diff, an architecture)
- Order of style: what the human wants → the project's tokens (colors, typography from the repo) → the skill's defaults.
- A diagram in `<figure>` with `<figcaption>`; `role="img"` and `aria-label` on the wrapper, not on the SVG (a re-render replaces it).
- CSS tokens (`--bg`, `--surface`, `--text`, `--text-dim`, 3–5 accents); dark mode = other token values,
  not inverted colors. State colors separate from the accent and backed by shape (a label, a bar), not by color alone.
- Text: a base of 16–18 px, lines of about 65 characters, numbers in tables `tabular-nums`; grid items with `min-width: 0`,
  wide tables and code in scrolling containers — no horizontal page scrolling.
- Pin libraries from a CDN to a version (or copy them locally) — that is a supply chain too.

## 7. Presentations (sprint demo, architecture review)
- First the mode: a presentation **with a speaker** (1–3 points per slide) or **for reading** (4–8 points).
- Too much content → a new slide, not a smaller font. The source content goes onto the slides in full — add slides
  instead of skipping.
- A fixed stage (e.g. 1920×1080 scaled as a whole) instead of reflowing the layout on every slide; check at 1280×720.
- No working labels stay on the slides ("Option A", file paths, template names).
- When the style is open, show 2–3 previews to choose from instead of asking for adjectives.
- Publishing on the internet (hosting, a public link) only with a human's consent.

## Sources of inspiration
[visual-explainer](https://github.com/nicobailon/visual-explainer) (choice of form, Mermaid rules, figure accessibility,
tokens and dark mode), [fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) (layout budget,
meaning of arrows and shapes, UML notation, looking at the result before handing it in) and
[frontend-slides](https://github.com/zarazhangrui/frontend-slides) (density modes, fixed stage, splitting instead of
shrinking, previews to choose from) — described in our own words, without their scripts.
