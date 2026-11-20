# Pull requests written by agents, and protected tests

## 1. Make agent work visible
- A label on every agent PR (e.g. `agent`, or the routine's name) — filterable in the PR list.
- A trailer in every agent commit: `Co-Authored-By: <agent> <address>` — searchable with `git log --grep`.
- The PR body says which task or routine produced it.

## 2. Protected paths
Paths where a mistake is expensive: `infra/`, auth, payments, `.github/workflows/`, `.claude/`, migrations.
- CODEOWNERS assigns their owners; branch protection with "Require review from Code Owners" makes that review mandatory.
- Auto-merge only for PRs that touch none of them — enforce with a required check that fails on those paths for agent PRs.
- A PR that edits the workflow which validates it cannot prove itself: green CI there is not evidence.
- `tf risk` marks these paths high-risk.
- Infrastructure written by AI gets extra gates: the `plan` output in the PR, drift detection after apply, optionally a
  signed provenance attestation (in-toto / SLSA, signed with Sigstore) naming the model, task and tools.

## 3. Scope
The PR does what the task asked. Unrelated edits are reverted or moved to their own item; the `scope-reviewer` agent
checks this. Permissions of agents in CI: core-agent-security.

## 4. Protected acceptance tests
A prompt saying "do not touch the scenarios" is not a control. What is:
1. CODEOWNERS on `features/` (or wherever scenarios live) **plus** branch protection "Require review from Code Owners" —
   CODEOWNERS alone only requests reviewers.
2. A required CI check that fails when one PR changes both scenarios and production code: scenario changes go in their own
   PR, reviewed by the owner.
3. A check that the number of protected scenarios does not drop. Weak signal: an assertion can be loosened without changing
   the count, so review still matters.
4. Step definitions, fixtures and adapters are guarded the same way — a scenario can be made green by editing its glue code.

## Example
A nightly routine opens dependency bumps and lint fixes. Changes: label `agent-nightly`, `Co-Authored-By` trailer,
CODEOWNERS entry `/infra/ @platform-team`, auto-merge rule limited to PRs whose files match `package*.json` or `src/**`
and whose CI passed; a PR touching `infra/terraform/` now waits for the platform team.

Sources: GitHub Docs — "About code owners", "About protected branches", "Automatically merging a pull request"
(docs.github.com); SLSA provenance (slsa.dev), in-toto attestation framework (in-toto.io), Sigstore (sigstore.dev).
