# Navigation, labels, search, site map

## Navigation patterns
| Pattern | When | Note |
|---|---|---|
| global navigation (main menu) | main sections, always visible | 5–9 items [a heuristic, not a rule], a fixed position |
| local / side navigation | a split within a section, many levels | show the position (the current item) |
| breadcrumbs | a deeper hierarchy | a complement, not a replacement for the menu |
| mega menu | many items on 2 levels | clear groups, keyboard, does not open only on hover |
| related content, cross-links | content fits several places | instead of a copy |
| faceted navigation | a shop, a catalog with traits | filters from metadata, the number of results |
| footer | legal, help, contact | not for main tasks |
| in-app navigation (bottom bar, tabs) | 3–5 main areas | text labels next to icons |
Accessibility: focus order, `nav` landmarks, accessible names, no reliance on hover — fe-web-platform.

## Labels
- From the users' language (open sorting, search queries), not from the company's org chart.
- Disjoint and predictable ("Leave and time off", not "Miscellaneous"); an end to "Other", "Remaining", "Services" without a qualifier.
- One name for one concept across the whole site; the first word carries the information (information scent).
- Descriptive links ("Remote work rules"), not "Click here".

## Search
- Log analysis: the most frequent queries, queries without results, results without clicks → synonyms, new content, label corrections.
- A visible, wide field; suggestions; typo tolerance; filters from metadata; a result with context (type, date).
- No results: a message, suggestions, contact; not an empty page.
- Best results: the task page at the top (promoted results for frequent queries).

## Site map
A hierarchy with indents or a Mermaid `flowchart TD` diagram: level 1 (sections), level 2, key pages; mark
content in several places (cross-links), pages only from search and planned removals. The map is versioned
together with `ia-documentation.md`.
