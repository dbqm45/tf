# The evidence bank (`docs/project/02-domain/corpus.md`)

## Rules
- **Include by default.** The bank should be complete with respect to the substantive content of the sources; exclude only what carries no
  information: greetings, fillers, agreeing noises, comments about the meeting itself, the board legend.
- **Verbatim and in the source language** — no paraphrase, no translation; mark omissions with `[…]`.
- **Every quote has a location** by which the human will find it in the source.
- An already structured source (e.g. a board description `*.es.md`) goes into the bank in full, step by step.
- **The human's answers** from the conversation are a full-fledged source (`user-answers.md`, location = the question id).
- A quote that lost in a resolved contradiction **stays** with the note `[superseded by C3 → D-007]`.

## Locations
| Source | Format |
|---|---|
| text with line numbers | `L42-45` |
| a document with sections | `§ section name` |
| PDF | `p12 ¶3` |
| a board description | `lane: Customer / step 7` |
| JSON/YAML | the path `$.orders[2].status` |
| the human's answer | `Q4` / `C2` |

## Quote strength
- **Strong:** contains a rule, a number, a threshold, a decision, a process step, a problem ("what hurts us is…"), a deadline or a responsibility ("department X does that").
- **Mention:** a bare term without content. A mention confirms that the term exists, but does **not** count towards the area threshold.

## Format
```markdown
---
artifact: corpus
phase: domain
…
---
# Evidence bank
Sources: 3 · quotes: 87 · updated: 2026-09-27

## S1 — interview-with-the-ceo.md (transcript, en)
- **E1** > "The project manager picks the people himself, but often does not know who is free." — L12-13
- **E2** > "The penalty for a delay is 2% of the contract value per week." — L40 [strong: number]
```

## Verification (cheaply, without an LLM)
Every quote must be findable in the source — `python3 .claude/hooks/project_record.py evidence` checks this (also the area thresholds). Missing → remove the quote or mark it `[unverified]`
and do not count it towards the thresholds. With materials > ~150 KB build the bank **per source in separate subagents** and merge the files —
after context compression the model can "quote" lines it no longer sees.
