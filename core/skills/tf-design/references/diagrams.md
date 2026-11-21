# Choosing a diagram

A diagram earns its place when it answers a question faster than text. One question per diagram; name it in the
caption ("Who calls whom when an order is paid?"). Mermaid inside the artifact — GitHub, GitLab and most IDEs render it,
and a text diff shows what changed between versions.

| Question | Form (Mermaid) | Notes |
|---|---|---|
| what happens, in which order, with which branches | `flowchart` | a process, a decision path, a state of the current code |
| who talks to whom over time | `sequenceDiagram` | API calls, events, retries, timeouts |
| which states an entity goes through | `stateDiagram-v2` | orders, approvals, lifecycles; mark the terminal states |
| what the parts are and how they depend | `flowchart` with subgraphs, or `C4Context` / `C4Container` | modules, services, boundaries |
| which types and relations | `classDiagram` | domain model, roles and inheritance |
| which tables and keys | `erDiagram` | data model; the database skill (be-database, pack-it) for details |
| what the screen holds and where the user goes | a wireframe is not Mermaid — a text layout or `flowchart` of screens; ux-feature-design (pack-ux) when installed | |

Rules:
- Current state and proposal: two diagrams side by side, never one with "new" boxes mixed in.
- At most ~15 nodes; more → split by question or zoom level.
- Labels in the domain's words, the same names as in the code (or the proposed names, marked).
- A diagram changed after the stage was accepted is a new version of the artifact (core-project-record), so the old one
  stays in `archive/` for comparison.
- No diagram is better than a decorative one.
