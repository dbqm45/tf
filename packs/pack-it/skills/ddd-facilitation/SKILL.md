---
name: ddd-facilitation
description: Use when leading a conversation or workshop with domain experts — facilitation, signal words, clean questions, the glossary, decision gates, a model as stand-in expert.
metadata:
  review: "2027-11-20"
  catalog: "Use when running a conversation or workshop with domain experts — the facilitator's stance, thinking modes, techniques for loops, dominance and disagreement (hot spots), clean questions, signal words (status, CRUD verbs, processed, always), building the ubiquitous language and glossary.md, confronting language with code, a language model as a stand-in expert (hypotheses to verify), decision gates for the agent's questions to the human, and the facilitator's self-check with 10 anti-patterns. Not for Event Storming formats, notation and colours (ddd-event-storming) or designing the model itself (ddd-deep-modeling)."
  keywords: "facylitacja, prowadzenie warsztatu, rozmowa z ekspertem domeny, wywiad z ekspertem, jak dopytywać eksperta, ekspert mówi zmieniono status, zaktualizowano rekord, język biznesu, wszechobecny język, ubiquitous language, słownik pojęć, glosariusz, czyste pytania, clean questions, słowa sygnałowe, eksperci się nie zgadzają, spór ekspertów, hot spot, kto ma rację, dyskusja kręci się w kółko, jedna osoba dominuje, ktoś milczy, model zamiast eksperta, przepytać model językowy, brak dostępu do eksperta, model zmyśla szczegóły, pytania do użytkownika, bramki decyzyjne, ile pytań zadać, samoocena facylitatora, ocena sesji warsztatowej, antywzorce facylitacji, sześć kapeluszy, parking lot, facilitation, facilitate a workshop, domain expert interview, probe the expert, status changed, record updated, business language, glossary, signal words, experts disagree, discussion going in circles, dominant participant, silent participants, simulated expert, interview the model instead of an expert, decision gates, clarifying questions batch, facilitator self-check, six thinking hats, parking lot"
---

# Facilitation — conversations and workshops with domain experts

The facilitator owns the **process**, not the content. Formats and notation of Event Storming: ddd-event-storming.
Turning the findings into a model: ddd-deep-modeling.

## 1. Stance
- Guard the goal and the time; when the group circles, name it and move on — the dispute becomes a hot spot.
- Write first, talk second: everyone writes silently, then reads out, so quiet experts are heard.
- Ground rules: everyone is partly right; disagreement is information, not a problem to suppress.
- Open with a check-in (what do you expect?) and close with a check-out (what do you take away?).

## 2. Thinking modes — say which one you are in
**Diverge** (generate, no judging) → **emerge** (group, find patterns, name them) → **converge** (decide).
Mixing modes either kills ideas (judging while generating) or burns the time (generating while deciding).

## 3. Difficult moments
| Situation | Move |
|---|---|
| The discussion loops | name the mode; Six Thinking Hats — everyone takes the same perspective at once (facts, risks, benefits, ideas, feelings, process) |
| Off-topic but important | the parking lot, each item with an owner |
| One person dominates | give them a task (retell the walkthrough, keep time) or vote round-robin; invite the silent ones by name |
| Experts disagree | **do not settle it.** Record both versions as a hot spot with names; the same word often means two things in two contexts |
| The group is new to the notation | introduce it in stages: events and hot spots → actors and systems → commands, policies, read models; each new element gets an example on the wall and a legend entry |

## 4. Clean questions
Neutral questions that reuse the speaker's own words and add none of yours:
- "What kind of *X* is that *X*?"
- "Is there anything else about *X*?"
- "Where does *X* come from?" / "What happens just before *X*?" / "And then what happens?"
- "What would you like to happen?"
They draw out the expert's model instead of confirming yours.

## 5. Signal words
| Word heard | Why it is suspicious | Ask |
|---|---|---|
| status, state | hides several lifecycles and events | "What happened in the business when it changed? Who decides? What is allowed in this state?" — each value is a candidate event or concept |
| create, update, delete, record updated | database language | "Why does someone change it? What do you call that?" |
| processed, synchronised, handled | hides decisions | "What is checked? What can go wrong?" |
| data, record, object, information, manager | no business meaning | "What kind? What for?" |
| always, never, automatically | hidden exceptions | "Was there ever a case when it did not?" |
| names of screens, tables, systems | the solution, not the problem | "If that system did not exist, what would you need?" |

## 6. Ubiquitous language and the glossary
- One word with two meanings (a *Customer* in CRM and in Billing) → probably a context boundary; do not unify it by force
  (ddd-context-mapping). Two words for one thing inside a context → choose one.
- Ask: "What do you call it?", "Are X and Y the same?", "Who uses this word?"
- File: `docs/project/02-domain/glossary.md` — one per context when there are several. Created at the first settled term,
  not in advance.
- Entry: the **term** in bold; one or two sentences saying what it *is* (not how it is stored); an "Avoid:" line with the
  rejected synonyms. Group under headings where it reads naturally. Be decisive — a glossary that lists three options
  helps nobody.
- Only domain terms of this context: no generic programming words, no implementation details; it is not a specification
  or a scratchpad. Prune drifted implementation detail from time to time.
- Record a term as soon as it is settled, not in a batch at the end.
- Stress a term with invented edge cases ("is a cancelled-then-restored booking the same booking?") until its boundary is sharp.
- Name a conflict with an existing entry at once; for a vague word propose two or three precise ones.
- **Confront with code:** when someone describes behaviour, check the code and quote the difference (file:line). A gap
  between the language and the code blocks further decisions until it is resolved.
- Entries the agent writes have status `proposed` until the human accepts them (core-project-record); list new and
  changed entries in the session summary.
- An existing repository without a glossary: a short interview with candidate terms mined from the code (aggregates,
  tables, endpoints), in batches; full distillation: ddd-legacy-modernization.

## 7. Conduct with the human
- 1–3 questions at a time, concrete, with an example; paraphrase in the speaker's language.
- Never fill a gap by guessing: a gap is a hot spot with a question and the person who can answer it.
- After each round record new terms, hot spots and decisions.

## 8. A language model as a stand-in expert
When no expert is available, a model can be interviewed — but its answers are **hypotheses**, never facts.
- Good use: walking through value-delivering processes, finding the industry's name for something programmers named
  differently, outlining common algorithms and trade-offs in the field.
- Weak spot: models are fluent about widely described generalities and **invent precise details** — formulas, constants,
  thresholds, field names of other systems' APIs, recent changes, and anything in regulated areas (tax, law, standards).
- Before a claim shapes a schema, a class or a rule: check the source documentation or specification; ask a model from
  another provider and review where they differ; confront it with the PRD and the code (file:line).
- Glossary entries from such a session carry status `proposed`; open points become hot spots. A real expert overrides the model.

## 9. Decision gates
The agent's loop: **investigate → propose with a justification → stop and ask.**
- Always ask on: a contradiction between sources, a value decision (priority, risk, cost), weak evidence, a change of a contract.
- Never ask about mechanical or stylistic matters, or anything the materials already answer.
- One turn holds **3–7 questions**. Each cites its evidence (a quote or a file), offers options, names a default and is marked
  **blocking** or **not blocking**.
- The human may answer in shorthand: `q1: b`, `C2: defer`. Control words: `skip` (accept all defaults), `stop`, `repeat`.
- Acknowledge each answer in one sentence: "OK — based on X I am doing Y." Record the decisions in an artefact.
- At most **10 turns**; after 3 turns without progress accept the defaults and record them as assumptions.
- Subagents do not ask the human: they return their questions to the leading persona.

Example turn:
```
Q1 [blocking] E14 says "the dock is booked per truck", E52 says "per delivery". Which unit is the booking?
   a) truck  b) delivery (default)  c) both, as two concepts
Q2 [not blocking] No quote on cancellation fees. a) none for now (default)  b) ask Finance
```

## 10. The facilitator's self-check
Run it after a session or every few rounds. Rate each anti-pattern **green / yellow / red** with evidence (round, quote):
1. **Premature design** — talk of tables, classes or endpoints before the flow is understood.
2. **One person dominated** — most notes or speaking time came from one participant.
3. **Someone was silent** — a participant contributed nothing for several rounds.
4. **No hot spots** — fewer than one per two rounds: disagreement is being hidden.
5. **No pivotal events** — the timeline has no events that split it into phases.
6. **No chronology** — notes in clusters rather than along time.
7. **Mixing levels** — commands and policies appearing at Big Picture.
8. **The facilitator writes for the group** — the notes are the facilitator's words, not the experts'.
9. **Regulations skipped** — compliance, contracts and audits never came up.
10. **Unchecked language** — signal words (section 5) passed without a question.

Summary: the 3 strongest moments and 3 to improve, each written as "I noticed… this leads to… next time try…". Save it as
`docs/project/07-review/<date>-facilitation.md`.

## 11. Reading people (optional lens)
Some people look for sameness (show continuity), others for differences (let them hunt exceptions as hot spots); some
speak in generalities (ask for an example), others in specifics (ask for the stage name); some move away from problems
(give them the risk and hot-spot job), others move to goals; some judge by their own frame (let them test their thesis on
an example rather than arguing). Treat it as a hint for how to lead, not as a diagnosis.

## Combining with Event Storming
| Technique | How it fits the timeline |
|---|---|
| Customer Journey | journey stages as lanes above the timeline |
| User Story Mapping | timeline steps become the backbone; stories hang below |
| Impact Mapping | goal → actors → impacts → deliverables; checks that processes serve a goal |
| Service Blueprint | frontstage and backstage lanes, supporting systems below |
| C4 | contexts from the session become containers and components |

## Example
**Situation:** "The expert keeps saying 'the status changed' and 'the record was updated'."
**Result:** treat both as signal words. Ask "What happened in the business when the status changed?" → "the dispatcher
confirmed the route" → event *Route confirmed*. Then "What kind of confirmation is that?" → "a provisional one, before the
driver accepts" → two events, *Route proposed* and *Route accepted*. Glossary entry (status `proposed`):
**Route** — the ordered list of stops one driver serves in one shift. *Avoid:* trip, tour.

## Sources
- E. de Bono, *Six Thinking Hats*, 1985.
- D. Grove, Clean Language — clean questions as described in P. Tompkins, J. Lawley, *Metaphors in Mind*, 2000.
- Deep Democracy (Lewis method) — treating disagreement as information [unverified: edition].
- NLP metaprograms (section 11) — weakly evidenced; used only as a facilitation hint.
- Glossary-entry practice in the spirit of the `domain-modeling` skill from mattpocock/skills (MIT).
