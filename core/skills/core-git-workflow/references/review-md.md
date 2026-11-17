# The `REVIEW.md` template

`REVIEW.md` sits in the repository root and adjusts the PR review done by Claude (the Code Review service
in Claude Code). You write the rules directly into the file. Below a template to copy and adapt — the passes and weights
according to "The AI-Native SDLC Playbook" (Anthropic, 2026).

```markdown
# PR review rules

## Scope
Review changes in `src/` and `infra/`. Skip: generated code (`**/generated/**`, `*.lock`), changes of
formatting alone and everything CI checks (lint, types, coverage).

## Passes
1. **Bugs and logic** — edge cases, error handling, concurrency, agreement with the tests.
2. **Security** — authorisation in every action and endpoint, input validation, secrets, dependencies,
   personal data (minimisation, logs).
3. **Compliance** — with the requirements and the step plan (`docs/project/03-requirements/`, `docs/project/06-delivery/`),
   with the ADRs (`docs/project/04-architecture/adr/`) and the rules from `CLAUDE.md`.

## Weight of findings
- **Critical** — blocks the merge (a data error, a security gap, breaking an API contract).
- **Important** — to fix in this PR.
- **Minor** — at most 3 per PR; skip the rest.
For each finding: the file and line, what is wrong, why, a proposed fix.
For each finding also **the difficulty of the decision (impact)**: low (an obvious fix) / medium (a trade-off — give
the cost and what you did not check) / high (architectural consequences). At most 10 findings; merge similar ones into one.
You do not judge compliance with what the plan did not promise; what the plan excluded ("Out of scope") is not scope creep.

## What you do not do
You do not approve the PR and do not judge style the formatter takes care of. Questions about requirements you direct to the author.
```

A review in GitHub Actions with the verdict as a gate: `ai-review-in-ci.md`. Triage of findings with a weight × impact matrix:
the change review skill (pack-it: qa-change-review).

After a month: review the findings (accurate / inaccurate), improve the scope and examples in the file, and take the `REVIEW.md` change
through the same path as a code change — a PR.
