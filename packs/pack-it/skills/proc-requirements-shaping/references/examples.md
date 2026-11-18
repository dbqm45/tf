# Examples and brownfield mode

## Brownfield mode — what changes in the phases
| Phase | Greenfield | Brownfield (requirements as a delta) |
|---|---|---|
| Problem | the pain, a person, the moment, the cost today | what exists, who uses it, what hurts, **what must not break** |
| Access | the login and roles model | the current model; whether the change touches it |
| MVP | the first flow and an estimate | the smallest change proving an improvement + the blast radius (modules, data, integrations) |
| Requirements | `FR-NNN … Priority` | as above + `Change: new / changed / kept` |
| Business rule | one sentence, the empty CRUD test | one sentence about the change of the rule or "no change to the domain rule" |
| Recording | brief + requirements | additionally "Obecny system" (Current system) and "Preserved behavior" |

In the "Obecny system" section you may name technologies (you are describing what exists). `requirements_lint.py` does not check it.

## A brownfield example — a waiting list in a booking system
**Input:** "We have a working room booking system. We want a waiting list for when a room is taken."
**Grey areas of phase 1 (options with a recommendation):**
- who joins the list: a) an employee, b) reception on someone's behalf as well → recommendation: a (a smaller blast radius);
- what happens when the room is freed: a) a notification and 30 min to confirm, b) an automatic booking →
  recommendation: a (b changes the allocation rule — a bigger risk);
- I don't know → to "Otwarte pytania" (→ the office manager).
**Result (a fragment):**
```
- FR-014: An employee can join the waiting list for a taken room slot. Priority: must. Change: new
- FR-003: An employee can cancel a booking. Priority: must. Change: changed (cancellation frees the slot for the list)
## Preserved behavior
- a booking without a waiting list works as today; booking limits per person unchanged
## Reguła biznesowa
A freed slot goes to the first person on the list who confirms it within 30 minutes of the notification.
```

## An example of a challenge round (phase 5)
`FR-002: A learner can accept, edit or reject each suggestion.`
Counterarguments to choose from:
1. with 15 suggestions, accepting one by one is tiring — consider "accept all" with a preview;
2. editing the content breaks the link to the source text — record whether the flashcard keeps a reference to the source;
3. rejected suggestions may return on the next generation — do we remember rejections?
4. no counterargument.
The result is recorded under the FR as "Challenge: …"; a new need from the conversation goes to "Otwarte pytania", not to the FR.

## An example of an empty CRUD
**Input:** "The user adds, browses, edits and deletes recipes."
**The agent's answer:** "This is an empty CRUD — the application decides nothing on its own. Which shape of a rule fits?
a recommendation (what to cook from what I have in the fridge) · classification (diet, allergens) · calculation (portions,
calories, a weekly shopping list) · validation (a recipe without steps will not be published) · or we consciously
stay with CRUD and I record it as an open question."

## An example of the script output
```
$ python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py requirements.md --brief brief.md
Readiness: 3/4
  · missing: a story with Given/When/Then criteria for the main flow
requirements.md:41 — execution location: "server-side" → describe behaviour visible from outside or move it to "For the stack decision"
MVP: estimate 25 days > budget 15 days — cost NOT acknowledged — propose cuts
✗ there are blocking problems
```
