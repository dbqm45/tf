---
name: ddd-discovery-intake
description: Use when turning interview transcripts, notes or Event Storming board photos into business areas backed by verbatim quotes, or critiquing interview questions.
metadata:
  review: "2027-11-20"
  catalog: "Use when raw discovery material (interview transcripts, notes, documents, photos or exports of Event Storming boards) must become a frozen, evidence-backed list of business areas — a pre-flight check whether modelling is worth it (three questions), a size gate, reading boards as numbered flows, an evidence bank of verbatim quotes with locations, contradictions found by a separate critic, strategic questions, areas with a threshold of 3 strong quotes from 2 sources and a human freeze; plus user research support (plan, interview script and question critique, survey, decision criteria, synthesis). Not for running a workshop (ddd-event-storming) or drawing context boundaries (ddd-strategic-analysis)."
  keywords: "transkrypcje wywiadów, notatki z wywiadów, zdjęcia tablic, zdjęcie tablicy Event Storming, wyciągnąć obszary biznesowe, obszary biznesowe z wywiadów, model nie może zmyślać, bez zmyślania, cytaty ze źródła, dosłowne cytaty, bank dowodów, sprzeczności w wywiadach, wywiady mówią co innego niż tablica, pytania strategiczne, czy warto modularyzować, czy warto robić DDD, rozbić skrypt na moduły, szef chce bounded contexty, ocena wstępna, dużo materiału, pytania do wywiadów, oceń pytania do wywiadu, popraw pytania do wywiadów, czy używałbyś, ile byś zapłacił, wywiady z użytkownikami, plan badania, ankieta, synteza wywiadów, rekrutacja respondentów, screener, interview transcripts, interview notes, board photos, extract business areas, must not invent, verbatim quotes, evidence bank, contradictions between sources, strategic questions, is it worth modularising, pre-flight, critique interview questions, would you use, user interviews, research plan, survey design, interview synthesis, screener"
---

# Discovery intake — from raw material to frozen business areas

Raw material (interview transcripts, notes, documents, board photos or exports) becomes a list of business areas in which
every claim points to a verbatim quote. The agent finds and organises; the human answers, resolves and freezes.
No files supplied → ask for them; never invent a quote.

## Flow — each step ends with a human gate (ddd-facilitation)
| # | Step | Output (under `docs/project/`) | Detail |
|---|---|---|---|
| 0 | Pre-flight: is modelling worth it? | `01-discovery/pre-flight.md` | below |
| 1 | Inventory of sources and size gate | list of sources with sizes | below |
| 2 | Read boards | `02-domain/boards/<name>.es.md` | `references/board-reading.md` |
| 3 | Evidence bank | `02-domain/corpus.md` | `references/corpus.md` |
| 4 | Contradictions (separate critic) | `02-domain/contradictions.md` | `references/contradictions.md` |
| 5 | Strategic questions | `02-domain/strategic-gaps.md` | `references/strategic-questions.md` |
| 6 | Conversation with the human | `02-domain/user-answers.md` (a new source in the bank) | — |
| 7 | Areas | `02-domain/areas.md` | below |

Strategic questions come **before** grouping: the answers change how much each area weighs.

## 0. Pre-flight — three questions, always
1. **Lifecycle:** is it a prototype or a one-off (a migration script, a report run once)?
2. **Scope:** will it stay a single module from the start?
3. **Complexity:** are there business rules, competition for resources or integrations — or is it storing and showing data?
If the answers say "not worth it", the priority of reasons is: one-off > single module > no complexity. Record the verdict
with its justification and an "If you disagree" section; write nothing else until the human approves. A refusal proposes
the cheaper path: tactical design inside one module or plain CRUD (ddd-deep-modeling).

## 1. Inventory and size gate
List every source with its type and size. Above roughly **150 KB of text** ask: process everything / selected sources /
stop. Large inputs are processed **per source in separate subagents** that return only their part of the bank (ids and
locations), then merged — after context compression a model may "quote" lines it no longer sees.

## 2–3. Boards and the evidence bank
- Boards are read as a numbered flow per lane, not as a pile of notes by colour; anything uncertain is marked and is not
  evidence until the human confirms it (`references/board-reading.md`).
- The bank holds **verbatim quotes in the source language** with a location, by default everything with substance
  (exclude greetings, fillers, meeting chatter, the board legend). No paraphrase, no translation; omissions marked `[…]`.
- Strong quote = a rule, number, threshold, decision, process step, problem, deadline or responsibility. A bare term is
  a `[mention]` and does not count towards the threshold.
- Verify cheaply, without a model: `python3 .claude/hooks/project_record.py evidence` checks that each quote appears in its
  source at its location; a quote not found is an error unless tagged `[unverified]`.
- Simulated or imagined material (ddd-es-simulation) never enters the bank.

## 4. Contradictions
A **separate critic** — the `sources-critic` agent, a fresh context of standard tier — reads the bank and returns only the
contradictions table (an empty table is a valid result). Detection is not resolution: the human resolves, the resolution
goes to `decisions.md`, the losing quote stays in the bank marked `[superseded …]`. Kinds, the same-subject test and the
format: `references/contradictions.md`.

## 5. Strategic questions
Default set: money (earn, lose, save), risks and opportunities, integrations and outside parties, regulation and audits,
the success measure and what wins in a conflict of goals. For each question write the gap checklist first, then match
quotes by meaning: `references/strategic-questions.md`. Gaps are phrased so the human can answer in a paragraph; the
answers become a new source (location = question id).

## 7. Areas
- **Threshold:** at least **3 strong quotes from at least 2 sources** (the human's answers count as one source).
- A group below the threshold goes to the section `## Candidates below the threshold` with the evidence it lacks — it is
  not dropped.
- Each area: heading `### A<n> <name>` in business words and the source language; a description whose length follows the
  number of distinct facts (3–4 quotes → one sentence; 5–9 → 2–3; 10+ → a paragraph), nothing beyond the
  evidence; the strategic questions it touches; a line `Evidence:` with E-ids; counts; `Named by the human: yes/no`.
- Gate per area: accept / rename / merge / split / reject; then a separate question to freeze. The human sets status
  `accepted`; later changes only as a new version.
- Intake does not classify domains, draw context boundaries (ddd-strategic-analysis) or design.

## Cost and repeatability
A cheap model for steps 0–1 and board reading; a standard one for the bank and grouping; the critic separate and standard.
Results vary between runs, so cache each source's result by the hash of its content (a change invalidates only that
source), freeze through the human, and check quotes with the script (zero tokens).

## User research
When the material does not exist yet, or the questions for it need work: planning a study, critiquing an interview
script, a survey, decision criteria set before the research, synthesis — `references/user-research.md`.
Recordings and transcripts are personal data (arch-privacy-compliance).

## Example
**Situation:** "12 logistics interview transcripts and photos of 2 Event Storming boards; extract business areas
without inventing anything."
**Result:**
- Pre-flight: a long-lived system, several modules, competition for loading docks → worth modelling; verdict recorded.
- Size: 310 KB → the human picks "everything"; 14 subagents (one per source) build bank parts S1–S14.
- Bank: 412 entries, e.g. `- **E87** > "a truck waits no more than 40 minutes for a dock" — L118-119`.
- Critic: 3 contradictions, e.g. E87 vs E203 (40 vs 60 minutes for the same dock type) with the question "Which limit
  applies to refrigerated trucks?"
- Areas: A1 Dock scheduling (11 quotes, 5 sources) accepted; A4 Driver ratings (2 quotes, 1 source) → below the threshold.
