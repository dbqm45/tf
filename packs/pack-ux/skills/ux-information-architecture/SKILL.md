---
name: ux-information-architecture
description: Use for the information architecture of a site or app — content inventory, card sorting, tree test, taxonomy, labels, navigation, site search.
metadata:
  review: "2027-10-17"
  catalog: "Use when the information structure of a site, intranet, shop or large app needs ordering — content inventory and audit, open, closed and hybrid card sorting, tree test (success rate, directness), taxonomy and labels, navigation patterns, metadata, site map, site search design, findability test and information architecture documentation (ia-documentation.md). Not for the basic information structure within one feature's flow, wireframes and heuristics (ux-feature-design), planning a study, recruitment and participant consent (ux-research-methods), the look of the interface (ux-visual-design), deciding what to build (proc-product-discovery) or the domain model in code (ddd-strategic-analysis)."
  keywords: "architektura informacji, IA, struktura serwisu, mapa serwisu, sitemap, nawigacja, menu, kategorie, taksonomia, etykiety, nazewnictwo, sortowanie kart, card sorting, test drzewa, tree testing, inwentarz treści, audyt treści, metadane, wyszukiwarka w serwisie, nie mogą znaleźć, odnajdywalność, findability, głębokość menu, intranet, sklep z produktami, information architecture, site structure, site map, navigation, categories, taxonomy, labels, naming, content inventory, content audit, metadata, site search, can't find, menu depth, product catalog"
---

# Information architecture — a structure people can find their way in

Goal: the user **finds** what they look for and **understands** where they are. IA is not the look of the menu, but groups, names,
hierarchy, relations and search. The basics of IA within one feature's flow (domain glossary, navigation, hierarchy)
are in **ux-feature-design** — this skill comes in when the structure is large or disputed and needs to be **measured**. Study planning,
recruitment and participant consent: **ux-research-methods**; the same rules apply to card sorting and the tree test.

## Procedure
1. **Goal and scope.** Who looks for what (the 5–10 most important user tasks, from research or search
   and path analytics), which content is in scope, which indicator will improve (e.g. the share of tasks completed in the tree test).
2. **Content inventory and audit** (`references/inventory-and-metadata.md`): a list of all pages with address, title,
   type, owner, update date, traffic. The inventory is **counting**, the audit is **assessing** (current,
   accurate, needed, understandable). A decision for each: keep / fix / merge / remove / add. A script or an export
   from the CMS, not manual copying.
3. **Card sorting** — choice of variant:
   - **open** — participants group and **name the groups themselves**; when there is no structure yet or it is doubtful;
   - **closed** — they assign cards to **ready** categories; when you want to check or extend existing ones;
   - **hybrid** — ready categories plus the option to add their own.
   Cards: 30–60 items, names in the users' language, without words from the target labels (do not suggest). The number of participants
   and the analysis (similarity matrix, dendrogram, name standardization): `references/card-sorting-and-tree-testing.md`.
4. **Structure design.** From the results: the hierarchy (wide and shallow is usually better than narrow and deep — check with a test,
   not a rule), category names from the participants' language, **one** grouping principle per level (topic, task,
   audience, time — do not mix), handling content in two places (a cross-link, not a copy). Navigation patterns
   and labels: `references/navigation-and-labels.md`. Write down the site map (Mermaid or an indented list).
5. **Tree test** on the hierarchy alone (text, no visuals): 8–10 tasks with real goals, each with one (or
   several) correct paths. Measures: **success rate** (reached the correct node), **directness**
   (reached it without going back), time, the **first-click node** and the places where people get confused. Read them together:
   high success with low directness = the labels mislead, but people get there by trial and error;
   low success with high directness = a confident choice of the wrong node (competing labels). Fixes → a repeat test.
6. **Site search** (`references/navigation-and-labels.md` § Search): analysis of queries without results, synonyms,
   suggestions, filters from metadata, a results page with a message when there is nothing.
7. **Findability test** on a prototype or a live site: "find…" tasks in a moderated or unmoderated
   test; comparison with the baseline indicator. Report the result to the team by ux-research-methods.
8. **Documentation** `docs/project/03-requirements/ia-documentation.md`: goal and scope, users and tasks, site
   map, taxonomy and label glossary (name, definition, synonyms, ban), metadata schema, rules for adding
   content and owners, test results with dates, open decisions.

## Example
Input: "The 'Biuro24' intranet has 1 200 pages, people cannot find the leave request form. Propose an IA plan."
Result (a fragment of `ia-documentation.md`):

```markdown
## Tasks and indicator
T1 "Submit a leave request", T2 "Check the remote work rules"… Indicator: ≥80% success, ≥60% direct.
## Plan
1. CMS inventory: 1 200 → after the audit about 700 to keep (decisions in a spreadsheet, content owners).
2. Open sort: 40 cards, 20 employees from 4 departments. 3. Hierarchy v1: 7 sections, max. 3 levels.
4. Tree test v1: 10 tasks, 30 people; T1 came out 72% success, 38% direct → the label "Absences" misleads,
   change to "Leave and time off"; test v2 → 88% / 71%.
```

## Checklist
- [ ] user tasks and the indicator before designing the structure
- [ ] an inventory with owners and a decision for every page; an audit based on criteria
- [ ] the card sorting variant matched to the situation; cards without suggestive words
- [ ] a tree test with success and directness; fixes checked again
- [ ] a label glossary (definition, synonyms); one grouping principle per level
- [ ] site search and metadata planned; queries without results monitored
- [ ] ia-documentation.md with test results and dates

## Additional materials
- `references/inventory-and-metadata.md` — inventory, audit, metadata, taxonomy; read when ordering content.
- `references/card-sorting-and-tree-testing.md` — participants, analysis, thresholds and pitfalls of both methods.
- `references/navigation-and-labels.md` — navigation patterns, labels, search, site map.

## Sources
- Tullis and Wood (2004), the sample in card sorting — 20–30 people according to secondary summaries; correlation with the "true" result
  about 0.90 with 15 and 0.95 with 30 people, attributed to NN/g (search 2026-10-17, the originals were not opened
  [unverified]).
- Definitions of success and directness in the tree test, interpretation thresholds (different across tool vendors:
  search 2026-10-17; the Optimal Workshop documentation was not opened [unverified]).
- The other rules (depth, one grouping principle, cross-links) are industry practice without a single source [unverified].
Described in our own words.
