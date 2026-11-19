# PR review rules

A template from tf (mode-pdi, the PR loop N2; pattern: `core-git-workflow/references/review-md.md`). It is read by the AI review of the cuts'
PRs (`pr_loop.py review`) and by the human as a checklist. Adjust the scope to the product, and take a change to this file
through the same path as a code change — through a PR.

## Scope
Review the changes of code, tests and configuration in the PR diff. Skip: generated code, lockfiles, formatting-only
changes and everything CI checks (lint, types, coverage, the security scan from `change-check.yml`).

## Passes
1. **Bugs and logic** — edge conditions, error handling, consistency with the tests and the cut's criteria.
2. **Security** — authorization, input validation, secrets, personal data in logs.
3. **Conformance** — with the cut plan (`docs/project/changes/CHG-n/plan.md`), the requirements (`requirements.md`) and
   the change's decisions (`decisions.md`); what the plan excluded ("Out of scope") is not a gap.

## Finding severity
- **Critical** (`critical`) — blocks the merge (a data bug, a security hole, a broken contract).
- **Important** (`important`) — to fix in this PR.
- **Minor** (`minor`) — at most 3 per PR; they go to a list in the PR, without a fix.
For every finding: the file and line, what is wrong, why, a proposed fix. At most 10 findings.
A comment that would require changing a change's decision refers to it (e.g. `CHG-4/D2`) — the human decides.

## What you do not do
You do not approve the PR and you do not judge style the formatter enforces. Questions about requirements go to the human.
