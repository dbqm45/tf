---
name: ux-feature-design
description: Use for the UX of a feature before code — tasks, flows with states, information architecture, wireframes, heuristics, UI copy.
metadata:
  review: "2027-10-17"
  catalog: "Use when designing and evaluating the UX of a feature before code — task analysis, flows with states and edge cases, information architecture, wireframes, prototypes, heuristics, usability tests, visual hierarchy, motion, interface copy, inclusive and ethical design, the specification for developers, Figma frames linked to requirements and states through Figma MCP (the frame table in design.md). Not for deciding what to build (proc-product-discovery) or CSS (fe-css)."
  keywords: "Figma MCP, ramki Figmy, powiązać ekrany z wymaganiami, design.md, tabela ramek, node-id, ramka dla stanu, powiadomienia, nawyk, onboarding, makieta, przepływ użytkownika, stany ekranu, użyteczność, etyka projektowania, dark patterns, Figma frames, link screens to requirements, frame table, frame for a state, notifications, habit, wireframe, user flow, screen states, usability, design ethics"
---

# UX and interface design

You design behaviour, not a picture. First it works (flow, states, content), then it looks; iteration instead of
perfection — every version goes in front of a user or the team. Consistency with the repo's design system (fe-css:
tokens, the main document) takes precedence over a new idea.

## Procedure
1. **Input**: the opportunity, the problem and the success metric (proc-product-discovery); users and context (ddd-discovery-intake:
   research). If missing — ask instead of assuming.
2. **Task analysis**: the user's goal → steps → decisions → information needed at each step → where today they
   make mistakes or wait. Do it on a real case from research, not an ideal one.
3. **Flow** (Mermaid `flowchart`): the main path, branches, returns, exits. For every screen or step
   a **state table**: empty (first use and no results), loading, partial data, success, validation error,
   system error, no permissions, offline, very long and very short content, many items (1, 2, 1000).
   Write domain edge cases explicitly (cancelling midway, concurrent editing, session expiry).
4. **Information architecture**: how users name and group things (the domain glossary — ddd-facilitation),
   navigation and hierarchy; for a large structure card sorting (how they group) and a tree test (whether they find).
5. **Low-fidelity wireframe** (text, ASCII, plain HTML without styling): layout, order, real content, not
   "lorem ipsum". Two–three versions differing in approach, not color.
6. **Prototype** with fidelity matched to the question: a clickable flow for a task test, high fidelity only
   for questions about look and motion. A prototype in code: an HTML page or components in the repo behind a flag.
7. **Evaluation**: heuristics and an expert review, then a test with 5 users per segment
   (`references/heuristics-and-tests.md`). Results → fixes → the next iteration.
8. **Specification for developers** (section below) and a review with engineering **before** the end of the design — API,
   data, performance and platform constraints come out cheaper then.

## Visual interface and motion
Visual hierarchy, typography, color, grid, component states, microinteractions and motion rules:
`references/visual-ui-and-motion.md`. Accessibility thresholds and the pre-handoff list: fe-css (`ui-review.md`) and fe-web-platform.

## Content, inclusion, ethics
Interface copy (error messages, buttons, empty states, tone), inclusive design and the deceptive patterns you do
not use: `references/content-and-ethics.md`.

## Behaviour change
When a feature is meant to make people start, continue or stop doing something: an ethics gate, the goal (actor,
action, outcome), a diagnosis with the Fogg model and the CREATE funnel, strategies (do it for the user → habit → conscious
action), techniques with abuse limits, measurement — `references/behavior-design.md`.

## Specification for developers (handoff)
Figma frames linked to requirements and states (the table `Requirement | Journey | State | Frame | Notes`, Figma MCP,
by default matching the designer's frames, a draft by the agent only on request): `references/figma-mcp.md`.
A contract, not a picture. It contains: the goal and scope (what is out of scope), the flow, a **state table** for every screen
and component, behaviour (validation — when and how, scrolling, focus after an action), final copy with i18n keys,
responsiveness (behaviour at 375 px, 768 px, a wide screen), tokens instead of values, accessibility annotations
(focus order, accessible names, `aria-live` regions), analytics events (proc-product-discovery), open
questions. Split large specifications into parts shipped separately. Changes after handoff — in one place with a date.

## Design review (critique)
It starts from the goal and the author's question ("is the return flow clear?"). Comments refer to the goal, the users
and the heuristics, not to taste: "the customer will not see the return cost before confirming — it violates visibility of system status",
not "I don't like it". The author collects the comments and decides; agreements with the owner.

## Checklist
- [ ] a flow with branches and a state table for every screen
- [ ] real content and names from the domain glossary
- [ ] a heuristic evaluation and a test with users (or an explicit "not tested" with the risk)
- [ ] accessibility and responsiveness described in the specification
- [ ] no deceptive patterns; consents voluntary and equal

## Sources
- NN/g: [Usability Testing 101](https://www.nngroup.com/articles/usability-testing-101/),
  [UX Expert Reviews](https://www.nngroup.com/articles/ux-expert-reviews/),
  [Task Analysis](https://www.nngroup.com/articles/task-analysis/),
  [Creating Design Specs for Development](https://www.nngroup.com/articles/creating-design-specs-for-development/),
  [Design Critiques](https://www.nngroup.com/articles/design-critiques/)
- [roadmap.sh — Product Design](https://roadmap.sh/product-design)
Described in our own words.
