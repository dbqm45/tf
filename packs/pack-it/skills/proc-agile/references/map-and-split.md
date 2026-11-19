# Story map and splitting stories

## The story map
1. **The backbone** — user activities from left to right in the order in which the user performs them ("find a room" →
   "book" → "change or cancel" → "settle"), with steps under each (e.g. "filter by date", "check the
   equipment"). You tell the story of one user, you do not list the modules of the system.
2. **Stories under the steps** — the most important at the top, below them variants, exceptions and conveniences. You lay out
   the existing backlog under the steps; a story that cannot be attached to a step is a signal (a missing step or unnecessary work).
3. **Release lines** — horizontal cuts across the whole map. The first release: the thinnest slice through all the steps
   that gives the user an outcome from start to finish (a walking skeleton), even if every step is poor.
   Each release has a named outcome and a measure (proc-product-discovery), not a list of features.
4. **Gaps and risks** — steps with no stories, steps with only variants and no basic version, external
   dependencies; mark them on the map and add questions.
5. **Updating** — the map is alive: after each release you move the lines according to what you have learned.

## Patterns for splitting a story that is too big
Every piece after the split still gives the user something that works (vertically), not a layer.
| Pattern | When | Example (importing bank statements) |
|---|---|---|
| Flow steps | the story covers several steps of a process | upload a file → preview → approve → reconcile |
| Rule variants | the business rules have cases | first without automatic matching, then matching by amount, then by title |
| Data | different data formats or sources | first one bank and one format, further banks separately |
| Interfaces | several input channels | first a manual file upload, then an import through the bank's API |
| Paths | a main path and alternative ones | first a valid file, then errors and duplicates |
| Simple before complex | a "good enough" version exists | first manual assignment, then suggestions |
| Performance later | performance requirements are separate work | first 500 rows, then 50,000 |
| Spike | too many unknowns to estimate | a time-boxed investigation of the format, the result: a decision and new stories |

The order of the pieces: first the one that gives the most knowledge or value at the least risk.
A split into "backend" and "frontend" or "database, API, UI" gives tasks, not stories.

## Signals that a story mixes features
`requirements_lint.py` (proc-requirements-shaping) checks the same signals as the STORY-001…003 rules.
| Signal | Example | What to do |
|---|---|---|
| A conjunction or slash between verbs in the title or goal (STORY-001) | "I want to add, edit and delete a card", "Export/import of products" | one story per action; "number and date" (nouns) is not a signal |
| Several actors (STORY-001) | "As a customer or a seller I want…" | a separate story for each role, or one role and the rest later |
| Different main actions in the scenarios (STORY-001) | AC-1 "When they add an address", AC-2 "When they delete an address" | the "Flow steps" or "Paths" pattern; data variants of the same action (different filters) stay together |
| Too many scenarios or actions (STORY-002) | more than 6 scenarios or more than 3 actions | "Rule variants", "Data" or "Simple before complex" |
| A title that starts from a technical layer (STORY-003) | "BE: endpoint for saving a card", "Orders table migration" | that is a task — name the value for the user and attach the task to a story |

## Sources
- J. Patton, *User Story Mapping* (2014).
- R. Lawrence, "Patterns for Splitting User Stories" (2009); M. Cohn, SPIDR (Spikes, Paths, Interfaces, Data,
  Rules), mountaingoatsoftware.com (2017).
Described in our own words.
