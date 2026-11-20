---
name: ops-ci-cd
description: Use when building, fixing or hardening a CI/CD pipeline (GitHub Actions) — stage order, permissions, SHA pins, injection, cache, composite actions, deploy.
metadata:
  review: "2027-05-20"
  catalog: "Use when building or repairing a CI/CD pipeline, mainly GitHub Actions — the order of stages, workflow hardening (permissions, SHA pinning, OIDC, script injection, pull_request_target, runner egress), caching and concurrency, composite actions and reusable workflows, PR diffs and multiline outputs, bot commits, promoting one artifact to production, an AI PR review with a verdict gate. Not for Dockerfile layers (ops-docker), release strategies such as canary or blue/green (ops-release-engineering) or a compromised dependency (ops-supply-chain-security)."
---

# CI/CD pipelines

A pipeline is code that runs with your secrets on every push. Treat each workflow change like a change to production access:
least privilege first, speed second, convenience last.

## 1. Stage order — fail fast
1. lint and format → typecheck → unit tests (cheap, run in parallel jobs);
2. build **once** → the artifact gets an immutable identifier (image digest, package checksum);
3. scans of the artifact (dependencies, image, secrets) → deploy to staging → smoke tests;
4. production from **the same digest**, behind an environment with required reviewers. Never rebuild for production.

Jobs that do not depend on each other run in parallel; `needs:` only where an output is really consumed.

## 2. Workflow security (each line is a check in review)
1. `permissions: {}` (or `contents: read`) at the top of the workflow; widen per job only what that job needs
   (`pull-requests: write`, `id-token: write`, `statuses: write`).
2. Third-party actions pinned to the full 40-character commit SHA, the tag in a comment: `uses: owner/action@<full-SHA> # v4.2.0`.
   A tag can be moved by whoever controls the action's repository; a SHA cannot. Let Dependabot/Renovate bump the pins.
3. **No interpolation of event data into `run:`.** `${{ github.event.pull_request.title }}`, branch names, issue bodies and
   commit messages are attacker-controlled; inside `run:` they become shell code (script injection). Pass them through `env:`
   and use the variable in quotes:
   ```yaml
   - env:
       PR_TITLE: ${{ github.event.pull_request.title }}
     run: printf '%s\n' "$PR_TITLE"
   ```
4. `pull_request_target` and `workflow_run` run with the base repository's secrets and a write token. They must **never check out
   and run fork code** (build, test, `npm install`, a script from the PR). Untrusted code goes to a `pull_request` job without secrets;
   a privileged follow-up job only reads its artifacts as data.
5. Cloud and registry access through OIDC (`id-token: write` + a trust policy bound to repository, branch and environment),
   not long-lived keys in secrets. Secrets only in the jobs that use them; production secrets only in a protected environment.
6. Dependency installation in a job without secrets: `npm ci --ignore-scripts` (then an explicit `npm rebuild <pkg>` for an allowlisted
   package that needs a build step). A malicious `postinstall` that runs next to a publish token is the classic supply-chain path.
7. Publishing packages through trusted publishing (OIDC) with provenance (`npm publish --provenance`), no stored publish token.
   Provenance proves where a package was built, not that the release was intended — bind the trusted publisher to one workflow file
   and a protected environment. Version cooldowns, install-script allowlists and the incident procedure: ops-supply-chain-security.
8. Runner egress limited to the hosts the job needs (for example `step-security/harden-runner` with `egress-policy: block` and an
   allowlist, or a self-hosted runner behind a proxy). Exfiltration needs an outbound connection.
9. Scanners, linters and setup actions are third-party code with access to your workspace: pin them by SHA or image digest like any other
   action. Retagged actions and hijacked scanner releases have happened; a pin plus a review of the bump is what stops them.
10. An AI agent running in CI on untrusted input (a PR, an issue comment) gets read-only permissions and no secrets beyond its own API key;
    it comments, it does not push or merge (core-agent-security).
11. Fork PRs never receive secrets. When someone asks "just make secrets available to forks", explain that this hands the secret to
    anyone who opens a PR, and offer the safe split: an unprivileged `pull_request` job + a label-gated or post-merge privileged job.

## 3. Speed
- Dependency cache through the setup action (`actions/setup-node` with `cache: npm`, `setup-python` with `cache: pip`) keyed on the lockfile.
- `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` for PR workflows (not for deploys to production).
- `paths:` / `paths-ignore:` filters in a monorepo; a matrix only for dimensions that really differ.

## 4. Reusable pieces
- A repeated group of steps → a **composite action**; a whole repeated process (build-test-deploy) → a **reusable workflow** (`workflow_call`).
- Start locally in `.github/actions/<name>/action.yml`; extract to a shared repository when a second consumer appears.
  Consumers reference it by full SHA, like any third-party action.
- In a composite action every `run:` step needs an explicit `shell: bash`; the action's own scripts are referenced through
  `${{ github.action_path }}`, not a path relative to the caller's workspace.
- `inputs` are untrusted text: pass them to scripts through `env:`, never splice them into `run:`.
- A diff of a PR needs history: `actions/checkout` with `fetch-depth: 0` (the default shallow clone of one commit gives an empty or failing
  `git diff origin/main...HEAD`).
- Multiline values in `$GITHUB_OUTPUT` need the delimiter form, with a random delimiter, or a file path as the output instead:
  ```bash
  delim="EOF_$(openssl rand -hex 8)"
  { echo "diff<<$delim"; git diff origin/main...HEAD; echo "$delim"; } >> "$GITHUB_OUTPUT"
  ```
  For large diffs write `diff.patch` and output only its path.
- A bot that commits to the PR branch: put `[skip ci]` in the message **and** add a guard step (`if: github.actor != 'github-actions[bot]'`)
  so the pipeline cannot loop. Commits made with the default `GITHUB_TOKEN` do not trigger new workflow runs anyway; a PAT or App token does.

## 5. Deployment
- The method (rolling, blue/green, canary, flags, rollback): ops-release-engineering. The pipeline's job is to feed it one immutable artifact
  and stop on a failed healthcheck.
- Build identity ≠ deploy identity: the job that builds cannot deploy to production, the deploy job does not build.
- Log each deploy: who approved, which commit SHA and digest, when, to which environment.
- Secret scanning (push protection, gitleaks) is the last line, not the plan: secrets come from OIDC or a secret store (ops-secrets-identities).
- Kubernetes manifests: ops-kubernetes; images: ops-docker.

## 6. AI PR review with a verdict gate (factory feature)
The factory ships a ready workflow: `python3 .claude/skills/core-git-workflow/scripts/ai_review.py install` writes
`.github/workflows/ai-review.yml`. It reviews PRs with the `ai-review` label against `.github/review-criteria.md`, sets the commit status
`ai-review/verdict` (APPROVED / NEEDS_ATTENTION / REJECTED), and a human bypasses it only with the `ai-review-override` label.
Details: `core-git-workflow/references/ai-review-in-ci.md`; the annotated workflow: example 4 in `references/examples.md`.
When writing such a gate by hand: `permissions: {}` at the top, fork PRs blocked, actions pinned by SHA, PR data via `env:`,
the verdict validated against a JSON schema, and a final `if: always()` step that **fails closed** when the verdict is missing or malformed.

## 7. Verify before you hand over
- `actionlint` on every changed workflow (it also runs shellcheck on `run:` blocks); at least a YAML parse when actionlint is missing.
- Grep the diff for `${{ github.event` inside `run:`, for `uses: …@v` without a SHA, and for `pull_request_target` with `actions/checkout`.
- In the PR description: how the workflow was tested (a run on a branch, `act`, a dry run) and which permissions it adds.

## Example
Request: "New Node repo, no CI yet — add something sensible."

Result (abridged; the full annotated version is example 1 in `references/examples.md`):
```yaml
name: ci
on:
  pull_request:
  push: { branches: [main] }
permissions: {}
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }
jobs:
  check:
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@<full-SHA> # v4
        with: { persist-credentials: false }
      - uses: actions/setup-node@<full-SHA> # v4
        with: { node-version: 22, cache: npm }
      - run: npm ci --ignore-scripts
      - run: npm run lint && npm run typecheck && npm test
      - run: npm run build
```
Plus in the reply: "ran actionlint — 0 findings; the workflow has no secrets, so it is safe for fork PRs; deploy comes later as a
separate job behind a `production` environment."

More: `references/examples.md` — 1. a new PR workflow · 2. fixing an injection through the PR title · 3. one image from staging to
production via OIDC with an approval and a digest output · 4. the AI review with a verdict gate.

## Related skills
ops-release-engineering (release methods, rollback) · ops-supply-chain-security (dependencies, publishing, incidents) ·
ops-secrets-identities (secrets, OIDC trust) · ops-docker · ops-kubernetes · core-agent-security · core-git-workflow.

## Sources
- GitHub Docs: "Security hardening for GitHub Actions" / "Secure use reference" (script injection, pinning to SHA,
  `pull_request_target`, OIDC), "Workflow syntax for GitHub Actions" (`permissions`, `concurrency`), "Metadata syntax for GitHub Actions"
  (composite `shell`, `github.action_path`), "Workflow commands" (multiline values in `GITHUB_OUTPUT` with a delimiter),
  "Triggering a workflow from a workflow" (`GITHUB_TOKEN` does not start new runs) — docs.github.com, as of 2026-11.
- npm Docs: "Trusted publishing for npm packages" and "Generating provenance statements" — docs.npmjs.com, as of 2026-11.
- actionlint (github.com/rhysd/actionlint) and step-security/harden-runner READMEs — tool documentation, as of 2026-11.
- anthropics/claude-code-action, action.yml — the action used by the factory's AI review template.
