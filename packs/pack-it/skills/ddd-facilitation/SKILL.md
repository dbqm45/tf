---
name: ddd-facilitation
description: Use for a conversation or workshop with domain experts — facilitation techniques, ubiquitous language, signal words.
metadata:
  review: "2027-10-09"
  catalog: "Use when leading a conversation or workshop with domain experts — facilitation techniques, building the ubiquitous language, catching signal words (status, CRUD), group dynamics. Also the agent's decision gates and the facilitator's self-check. Not for the course and notation of Event Storming (ddd-event-storming) or designing the model (ddd-deep-modeling)."
---

# Facilitation and a shared language

## The facilitator's role
- You own the **process**, not the content. You do not settle substantive disputes — you record them as a hot spot.
- You keep the session's goal and time; you decide to move to the next step when the group goes round in circles.
- First we write, then we talk — this way the quiet experts are heard too, not only the loudest ones.
- Set the rules at the start (in the spirit of Deep Democracy): everyone is partly right, nobody is wholly right; a difference of opinion is information, not a problem.
- Open with a **check-in** (short, human) and close with a **check-out** ("what are you taking away from the session?").

## Modes of thinking — do not mix them
1. **Divergence** — we generate (chaotic exploration): no judging.
2. **Emergence** — we group, look for patterns, name things (ordering the timeline, swimlanes).
3. **Convergence** — we decide (voting, choosing boundaries).
Announce aloud which mode you are in. Judging in the divergence phase kills ideas; generating in the decision phase kills time.

## Techniques for difficult moments
- **Six hats** — when the discussion goes round in circles: everyone looks from one perspective at once (facts → risks → benefits → ideas → emotions → process), instead of trading arguments.
- **Clean Questions** — questions that do not suggest an answer and use the speaker's words:
  "And what kind of X is that?", "Is there anything else about X?", "Where does X come from?", "What happens just before X?", "And then what happens?",
  "What would you like to happen?". Ideal for drawing out concepts without imposing your own vocabulary.
- **Parking lot** — a thread that is important, but not now → a sticky note in the parking lot with an owner.
- **A dominant participant** — give them a task (e.g. telling the walkthrough at the end), collect votes in a round.
- **The experts disagree** — do not settle it. Record both versions as a hot spot; often these are two different contexts with the same word.

## Introducing the notation gradually
You show only what the group needs in a given step: first events and hot spots, then actors and systems,
finally commands, policies and read models. A new element = a short example on the wall + a note in the legend.

## Complementary techniques — when to reach for them
| Technique | When | How to combine it with Event Storming |
|---|---|---|
| Customer Journey | when the customer experience matters | the journey stages as lanes above the event timeline |
| User Story Mapping | when the scope has to be cut into releases | the steps from the timeline = the backbone of the map, the stories underneath |
| Impact Mapping | when it is not clear why we are building something | goal → actors → impact → products; it checks the sense of the processes on the timeline |
| Service Blueprint | when the "back office" of the service matters | frontstage/backstage as lanes, support systems underneath |
| C4 | when you move on to architecture | the contexts from the session → containers/components |

## Ubiquitous language
If the expert does not understand the model, the project goes in the wrong direction from the start. The language is shared by the business, the analysis and the code.
- Keep the glossary `docs/project/02-domain/glossary.md`: the term, its meaning **in the given context**, examples, synonyms, conflicts.
- The same word, different meanings (e.g. "Customer" in CRM and in Billing) → a likely **context boundary**. Do not unify by force.
- Different words, the same meaning → agree on one within the context.
- Ask: "What do you call it on your side?", "Are X and Y the same thing?", "Who uses this word?".

### The glossary during design (not only at a workshop)
- **An entry**: the term in bold, 1–2 sentences on what something **is** (not what it does), a `_Avoid_: …` line with the rejected
  synonyms. Be firm: choose one word out of several. Group entries under headings when natural groups appear.
- **Only the terms of this context** — no general programming terms (timeout, error type) and no implementation
  details. The glossary is not a specification or a scratchpad. Several contexts → a separate glossary per context + a map of
  relationships (ddd-context-mapping).
- **Record it right away** when a term is settled — not in bulk at the end of the session. The glossary shrinks as often as it grows;
  periodically remove implementation details from it.
- A word that contradicts the glossary → name the conflict right away ("the glossary says Cancellation is X, but you are talking about Y — which one?").
  A vague word → propose a precise one ("account — Customer or User?").
- Check relationships with **invented edge-case scenarios** until the boundaries of the terms are sharp.
- **Confront it with the code**: when someone says how something works, check it in the code and quote the discrepancy ("the code cancels the whole
  Order, but you are talking about a partial cancellation — which is true?"). A discrepancy between the code and the language blocks further decisions.
- **A glossary written by the agent is a proposal**, not an authority: entries without a human review sound confident, but can be
  false. You show new and changed entries in the session summary for acceptance (core-project-record: statuses).
- **No files in advance** — the glossary and an ADR are created when there is the first term or the first decision to record.
- **An existing repo without a glossary:** do not wait for the glossary to grow along the way (too slow). Do a short interrogation:
  the agent lists candidate terms from the code (the names of aggregates, tables, endpoints) and asks about meaning and synonyms, in batches.
  Full distillation of documents and code (a glossary with "BRAK w kodzie" — missing in the code, a table of model ↔ code divergences): ddd-legacy-modernization.
- The agent confronts the language with the code and the recorded artifacts — it does not see the issue tracker; if there are language
  agreements there, point to them in the project's `CLAUDE.md`.
Modelled on the `domain-modeling` skill from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT; description: [aihero.dev](https://www.aihero.dev/skills-domain-modeling)), described in our own words.

### A simulated domain expert (a language model)
- Without access to an expert you can question a model about the domain: the key processes that deliver value, the terms that
  a programmer names differently from the industry (e.g. "review" rather than "quiz"), industry algorithms with their trade-offs.
- The result is a **hypothesis generator**, not a source of truth. The model is strong at widely described generalities, and makes things up in
  precise-sounding details: formulas and constants, thresholds, the field names of someone else's API, recent changes, regulated domains
  (taxes, law, standards).
- A claim on which you base a schema, a class name or a rule is checked before you record it: (1) the source documentation
  or a specification, (2) the same question to a model from another provider — the discrepancies are a list for manual
  checking, (3) a confrontation with the PRD and the code (`file:line`).
- Entries with the source "model" go into `glossary.md` with the status `proposed` for a human's acceptance; a real
  expert takes precedence as soon as one is available.

### Signal words — stop and ask more
| Signal | Why it is suspicious | What to ask |
|---|---|---|
| **status** ("the status was changed to…") | a status field often hides several different life cycles and several business events | "What happened in the business that the status changed? Who decides about it? What is allowed in this state, and what is not?" — every status value is a potential event or a separate concept |
| **CRUD**: added, updated, deleted, saved, edited | the language of the database, not of the business | "Why does someone change it? What do you call it?" — "the order was updated" is e.g. "The customer changed the delivery address" or "The order was paid" |
| processed, synchronized, handled | it hides a decision or a rule | "What exactly is checked? What can go wrong?" |
| data, record, object, information, manager | a term without a business meaning | "What kind of information is it? What is it for?" |
| always / never / automatically | hidden exceptions | "Was there a case when it did not…?" |
| names of screens, tables, systems | a solution instead of a problem | "What would happen if this system did not exist?" |

## The agent's work with the user
- Ask **one to three questions at a time**, specific, preferably with an example.
- Paraphrase in the speaker's language and ask for corrections ("Do I understand correctly that…?").
- Never fill gaps by making things up — a gap is a hot spot with a question and an addressee.
- After each round record: new terms, hot spots, decisions.

## Decision gates (agent ↔ human)
A gate = a point where the agent stops for a human's decision. The loop: **investigate → propose with a justification → stop**.
- Per turn **3–7 questions**, each based on evidence (a quote/a file), with options, a **default value** and a "blocking / not blocking" mark.
- The human can answer in shorthand: `q1: b`, `C2: defer`; control words: `skip` (accept the defaults), `stop`, `repeat`.
- After each answer one sentence: "OK — based on X I am doing Y". Record the decisions in an artifact (core-project-record), so that
  interrupted work can be resumed without asking again.
- A limit of 10 turns; after 3 turns without progress accept the default values and record that as an assumption.
- **Always ask:** a contradiction in the sources, a value decision (priority, risk, cost), weak evidence, a contract change.
  **Do not ask:** about mechanical or stylistic things, or about what the materials already answer.
- A subagent has no conversation with the human — instead of asking, it returns the questions (hot spots) to the persona that leads the conversation.

## Metaprograms — a lens on the participants
| Axis | You recognize it by | How to lead |
|---|---|---|
| sameness ↔ difference | "as always" / "this is completely different" | show continuity to the sameness people, let the difference people look for exceptions (hot spots) |
| general ↔ specific | mental shortcuts / long stories with numbers | ask the general ones for an example, the specific ones — for the name of the stage |
| "away from" ↔ "towards" | talks about problems / about goals | give those focused on problems the job of marking risks and hot spots |
| internal ↔ external frame | "I know that…" / "customers say…" | do not convince a self-assured person with authority — invite them to check the thesis on an example themselves |

## The facilitator's self-check (after the session or every few rounds)
| # | Anti-pattern | Signal |
|---|---|---|
| 1 | premature design | talking about tables/APIs at Big Picture |
| 2 | one person dominated | the same person speaks long, many times |
| 3 | someone is silent | no contribution for several rounds — invite them directly |
| 4 | no hot spots | fewer than one per two rounds = disputes are swept under the rug |
| 5 | no pivotal events | a timeline without structure |
| 6 | no chronology | sticky notes without time order |
| 7 | mixing levels | commands/policies at Big Picture |
| 8 | the facilitator writes for the group | sticky notes come from their words |
| 9 | regulations/compliance skipped | nobody asked about the law and contracts |
| 10 | unchecked language | signal words without asking more |
Summary: the 3 strongest moments and 3 to improve each, in the form "I noticed… this leads to… next time try…".
Record: `docs/project/07-review/<date>-facilitation.md`.

## Sources
- The 10xDevs course, ed. 3 (2026), module 4, lesson 5 (interviewing an expert, "when the expert makes things up") — training material
  (accessed 2026-10-09); described in our own words.
