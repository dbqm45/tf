# Reviewing a skill — how it works and how to make a similar one

To the question "how does this skill work?", "why does it behave like this and not otherwise?" or "how to make a similar one?"
you answer with a report in seven points. First you read all of it: SKILL.md, every file from `references/`, every script
(a foreign skill — first `python3 .tf/factory/skill_audit.py <katalog>`, core-agent-security §4a).

Depth: SKILL.md shorter than 150 lines → concisely, without the anatomy table; longer than 400 lines → a full anatomy
table with line numbers.

## The seven points of the report
1. **Problem and goal** — which gap of the model it closes (knowledge, steps, format, boundaries) and how to tell it works.
2. **Position in the chain** — the input (a file, a question, the repo state) → the output (a file, a report, a decision); which skill comes
   before it, which after it.
3. **Anatomy** — sections with a line range and the answer to "what breaks without this section":

   | Section | Lines | Role | What breaks without it |
   |---|---|---|---|

4. **3–5 driving mechanisms** with the high-leverage places marked: the description (a selection rule), `allowed-tools`,
   hard rules, the output schema, self-check gates, scripts.
5. **Design decisions** — each with a rejected alternative ("a refusal instead of a guess, because …").
6. **Easy / medium / hard changes** — hard ones are changes of file, section and status names that further
   skills, hooks or scripts depend on.
7. **The road from an instruction to a skill** — how to turn a one-off instruction into a skill: the gap measured without the skill,
   evaluation scenarios, minimal content (the procedure in the main SKILL.md).

## Example (short)
Input: "How does the PR review skill that leaves comments in CI work?"
Result: (1) it closes the gap "the model comments on style instead of risks"; (2) input: the PR diff + the step plan, output: a report
with the line `Werdykt: approve|request-changes`; (4) leverage: a fixed verdict marker checked by a script in CI and a ban on
questions to the human; (5) inline comments for every remark were rejected (noise) in favour of one report; (6) a hard
change: the name of the `Werdykt` field, because a gate step in the pipeline reads it.

The 10xDevs course, ed. 3 (2026), module 1, lesson 2 — training material (accessed 2026-10-09). Described in our own words.

## Slimming down
- **A "no-op" test sentence by sentence:** does the sentence change behaviour compared with the default model? If not, you remove
  the whole sentence (a measurement of 2026-10-30: two pack-it skills slimmed by 5–12% of words without losing results).
- **Positive instructions instead of bans:** a ban brings the forbidden thing into the context; write what to do.
- **Concepts by name,** when the model knows them (e.g. Fowler's code smells), instead of definitions.
- **A skill-router** called by hand, which only then loads a heavier skill.
- **The cost of the descriptions of all skills** visible in the session is a fixed overhead of every request: skills rarely called
  automatically get `disable-model-invocation` when the human calls them by name anyway (a decision
  with a measurement of hook hits and an evaluation, not from intuition).
- A specification in a skill without the project's file paths and code fragments — they age, and the agent reaches them anyway.
- Every cut goes through the scenarios and the gate; a paid measurement with the human's consent.
