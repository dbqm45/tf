# `REVIEW.md` — review rules for AI and human reviewers

`REVIEW.md` sits in the repository root. CLAUDE.md tells an agent how to *work* in the repo; `REVIEW.md` tells a reviewer
what to *look for* in a change. Both the CI workflow (`references/ai-review-in-ci.md`) and a human can follow it. Keep it
under one screen; project specifics beat general advice.

## Template
```markdown
# Review rules

## Scope
- Review only the PR's diff against its base. Plan: the step report in docs/project/ changed by the PR, or the `Plan:` line.
- Skip: lockfiles, generated code (`src/gen/**`), snapshots, files already checked by CI (formatting, types).

## Passes (in this order)
1. Bugs and logic — wrong conditions, missing error paths, races, off-by-one, broken contracts with callers.
2. Security — input validation at boundaries, authz checks, secrets in code or logs, injection, unsafe deserialization.
3. Compliance with project rules — <3–5 rules specific to this repo, e.g. "money is integer cents", "no SQL outside repositories/">.

## Weights
- critical — blocks the merge (bug, vulnerability, data loss, broken contract).
- important — should be fixed in this PR.
- minor — optional; at most 3 per review.
Impact for each finding: low / medium / high.

## Output
- At most 10 findings after merging duplicates, most severe first; each with file:line, what is wrong, a concrete fix.
- A secret is reported by location and type, never by value.

## What you do not do
- You do not approve or request changes — a human decides.
- No remarks a formatter or linter would make; no style preferences.
- Whatever the plan lists under "Out of scope" is not scope creep.
```

## Filling it in
- Take the project rules from real review history: the last 20 merged PRs' comments and the bugs that escaped.
- After code reconstruction a draft may exist; the human reads and approves it, then
  `python3 .claude/skills/core-git-workflow/scripts/ai_review.py review-md` copies it to `REVIEW.md` (`--from FILE` for
  another draft, `--force` to overwrite).
- Revisit monthly with the numbers: findings accepted vs dismissed. Rules that only produce dismissed findings go.

Sources: Claude Code docs, "Code Review" and GitHub Actions pages (code.claude.com) — `REVIEW.md` as the place for
review-specific guidance [unverified: exact file lookup rules of the managed service].
