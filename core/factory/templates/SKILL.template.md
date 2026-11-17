---
name: {{name}}
description: {{short}}
metadata:
  catalog: "{{description}}"
---

# {{name}}

<!--
Rules for a good skill:
- description (above) is a SELECTION RULE: "Use when/for <situation> — <key concepts>." (≤ 170 characters, no ": ", because it breaks YAML) — this is
  all Claude sees at the start (Claude Code ignores the metadata field), and the list
  of all descriptions fits in ~1% of the context window. The full description with boundaries ("Not for …") → metadata.catalog
  (the dispatcher reads it from .claude/catalog.md). A skill run only by hand: disable-model-invocation: true.
- Evaluations: tests/skill_evals/<name>.json — 2 questions where the skill must trigger (with a check of specific
  knowledge), 1 question of a neighboring skill (the format is in tests/skill_evals/README.md).
- Do not use the paths field: a skill with paths is unknown to the model ("Unknown skill") until a matching file
  appears in the session — also on an explicit call and in personas (measured 2026-10-02). The skill_hint hook triggers it.
- This file: max. ~150–300 lines (Anthropic: < 500); the rules part fits "on a phone screen"; details,
  edge cases and long examples → references/ (one level from SKILL.md, a table of contents at > 100 lines).
- Examples > rules: at least one concrete example (input → result) in the "Example" section, more
  in references/examples.md.
- Code where it fits: sorting, parsing, counting, validation → a script in scripts/ (deterministic, cheaper).
  Say whether to RUN the script or READ it. A script that connects to the network is declared with a "Network: …" line.
- One skill, one task: if the description lists several independent tasks, split the skill.
- Do not repeat other skills' content — refer to them by name ("apply the rules of <skill-name>").
- A good skill packs a PROCEDURE the agent would otherwise improvise: steps, order, decision points, result format.
  Knowledge alone ("what X is") without steps rarely changes the agent's behaviour.
- If the skill uses external tools: a preview mode before writing, diagnostics ("does the tool work"),
  a fallback when the tool fails, and risk warnings (accounts, limits, credentials).
-->

## When to use
- …

## Procedure
1. …

## Rules
- …

## Example
<!-- Input (a command or situation) → result (a code fragment, a decision, an artifact). Concrete numbers and names. -->

## Checklist before handing in the work
- [ ] …

## Additional materials
- `references/…` — read only when you need details about …
