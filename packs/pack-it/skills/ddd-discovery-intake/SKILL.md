---
name: ddd-discovery-intake
description: Use for raw materials (interviews, notes, ES boards) — business areas backed by evidence, contradictions.
metadata:
  review: "2027-10-09"
  catalog: "Use when business areas BASED ON EVIDENCE must be derived from raw materials (interviews, notes, photos of Event Storming boards, documents) — the \"is it worth it\" assessment, a quote bank, evidence thresholds, detecting contradictions, strategic questions, freezing the areas. Not for running a workshop (ddd-event-storming) or context boundaries (ddd-strategic-analysis)."
  keywords: "notatki z wywiadów, transkrypcje, zdjęcia tablic, czy warto modularyzować, czy dzielić na moduły, prototyp, obszary biznesowe, czy warto modularyzować, rozbijać na moduły i bounded contexty, pytania przed modularyzacją, pytania do wywiadów z użytkownikami, oceń pytania wywiadu, popraw pytania do wywiadów, interview notes, transcripts, board photos, is it worth modularizing, should we split into modules, prototype, business areas, split into modules and bounded contexts, questions before modularization, user interview questions, assess interview questions, improve interview questions"
---

# From materials to business areas (intake)

Goal: the source materials produce a **frozen list of business areas** in which every claim has a quote
from a source. This is the input to strategic analysis — an area is **not** yet a context or a module.
The overriding rule: **only the evidence bank may be quoted**; what is not in the bank, the agent does not claim.

## Flow (every step ends with a gate — the protocol in ddd-facilitation)
| # | Step | Result in `docs/project/` | Details |
|---|---|---|---|
| 0 | **Pre-flight assessment ("is it worth modularizing?")** — always three questions to the human | `01-discovery/pre-flight.md` | below |
| 1 | **Inventory and the size gate** — a list of sources with size and type; above ~150 KB of text ask: everything / selected / stop | a section in `corpus.md` | process source by source in subagents, only indexes return to the main thread |
| 2 | **Reading boards** (photos/exports) | `02-domain/boards/<name>.es.md` | `references/board-reading.md` |
| 3 | **The evidence bank** | `02-domain/corpus.md` | `references/corpus.md` |
| 4 | **Contradictions** — a separate critic agent, it only detects | `02-domain/contradictions.md` | `references/contradictions.md` |
| 5 | **Strategic questions** — BEFORE grouping, because the answers weigh the areas | `02-domain/strategic-gaps.md` | `references/strategic-questions.md` |
| 6 | **Conversation** — questions about gaps and contradictions; the human's answers go into the bank as a new source | `02-domain/user-answers.md` | ddd-facilitation → gates |
| 7 | **Areas** — grouping quotes, thresholds, approval and freezing | `02-domain/areas.md` | below |

## Step 0 — pre-flight assessment
Three questions asked always (the materials can only suggest the answer, the human decides):
1. **Lifecycle** — is it a prototype / a one-off solution?
2. **Scope** — is the scope a single module from the outset?
3. **Complexity** — are there rules, competition for resources, integrations, or only data storage?
The order of importance for a refusal: one-off > a single module from the outset > no complexity. A refusal is also a result:
propose tactical work in a single module or a simple CRUD (ddd-deep-modeling). Record the verdict with a justification and an
"if you disagree" section. Write nothing else before the verdict is approved.

## Step 7 — areas
- **The area threshold:** at least **3 strong quotes from at least 2 different sources** (the human's answers are one source).
  A strong quote carries a rule, a number, a threshold, a decision, a process step, a problem, a deadline or a responsibility; merely mentioning a name does not.
- Groups below the threshold → the section **"Candidates below the threshold"** (with the missing evidence); do not throw them away.
- **The area name** — in the business's words, in the source language; not a technical name.
- **The description length proportional to the number of distinct facts**: 3–4 quotes → one sentence; 5–9 → two or three; 10+ → a paragraph.
  Do not add content beyond the evidence.
- Every area: id, name, description, link to the strategic questions, the list of evidence (quote ids), the number of quotes/sources,
  a "named by the human" flag.
- Gate: for every area the human's decision — accept / rename / merge / split / reject; then a separate
  question about **freezing**. A frozen `areas.md` has the status `accepted` (set by the human) and changes only by a new version.
- What intake does NOT do: it does not classify Cynefin, does not delineate contexts, does not design. Those are the next steps (ddd-strategic-analysis,
  ddd-algorithm-recognition, ddd-deep-modeling).

## Research with users
When there is too little evidence from experts or the topic is end users: the research plan, recruitment, the interview
script (critiquing questions: keep / rewrite / remove), a survey, decision criteria and synthesis — `references/user-research.md`.

## Cost and stability
- Steps 0–1 and reading boards: a cheap model; the bank and grouping: std; the contradiction critic: a separate std agent (a fresh context = independence).
- The results are non-deterministic — hence: a cache keyed by the hash of the source content (a change of a source invalidates only its result),
  freezing artifacts by the human, verifying quotes and thresholds with a script: `python3 .claude/hooks/project_record.py evidence` (zero tokens).
- Materials from a simulation or from the agent's imagination never go into the bank as evidence.

## Checklist
- [ ] the pre-flight verdict approved by the human
- [ ] every quote verbatim, in the source language, with `source + location`; `project_record.py evidence` passes
- [ ] contradictions detected by a separate critic; each has a diagnostic question and a status
- [ ] every area meets the threshold or is in "below the threshold"
- [ ] `areas.md` frozen by the human's decision; handed over to ddd-strategic-analysis
