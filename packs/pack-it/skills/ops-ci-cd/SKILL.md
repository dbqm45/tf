---
name: ops-ci-cd
description: Use for CI/CD pipelines (GitHub Actions and others) — creating, fixing, build caching, deployments, security.
metadata:
  review: "2027-04-10"
  catalog: "Use when creating and fixing CI/CD pipelines (GitHub Actions and similar), for deployment strategies, build caching, pipeline security, composite actions and reusable workflows, the PR diff in CI and the AI review verdict gate. Not for writing a Dockerfile (ops-docker) or commits (core-git-workflow)."
---

# CI/CD

## Pipeline structure
`lint → typecheck → test → build → (security scan) → deploy staging → smoke tests → deploy production (with approval)`
- Fast steps first (fail fast). Independent jobs in parallel.
- The same artifact (an image with a digest) goes through all environments — you do not rebuild it for production.

## GitHub Actions — security
1. Set `permissions:` at the workflow level to the minimum (`contents: read`), widen per job.
2. Pin external actions to the full commit SHA, not to a tag.
3. The cloud through OIDC (`id-token: write`) instead of long-lived keys in secrets.
4. `pull_request_target` and `workflow_run` with code from a fork = a risk — do not run untrusted code in them.
5. Do not interpolate `${{ github.event.* }}` (PR titles, branches) directly in `run:` — pass it through `env:`.
6. Secrets only in the jobs that need them; the `production` environment with required approval.
7. Install dependencies with `npm ci --ignore-scripts` (or an allowlist of scripts) in a job **without** publishing
   and deployment secrets. A package publishing token does not exist in CI — publishing through trusted publishing (OIDC) with `--provenance`.
8. Outbound traffic from runners limited to the registries and services the pipeline needs (e.g. harden-runner on
   GitHub Actions, network rules on self-hosted runners). A malicious install script then cannot send out the secrets.
9. Scanners and linters are also external code: pin them to the SHA and the image digest (in 2026 Trivy was swapped through its actions).
10. An AI agent in CI does not run with write permission or with secrets on untrusted input (a PR from a fork, the content of an issue) —
    core-agent-security. Dependencies and incidents with packages — ops-supply-chain-security.

## Performance
- Dependency cache (`actions/setup-node` with `cache: npm`, Docker layer cache).
- `concurrency:` with `cancel-in-progress: true` for PRs.
- Run only what changed (`paths:` filters) in a monorepo.

## Reuse and the diff in a PR
- A repeated step (an AI agent, a scan) in many repos → **a composite action** (`action.yml` with `runs.using: composite`);
  a whole process → a reusable workflow. Start locally in `.github/actions/<name>/`, move it to a separate repo only
  with the second consumer; the consumer pins `uses: org/action@<full-SHA>`.
- In a composite action every `run` step has an explicit `shell:`; you call the action's scripts through `${{ github.action_path }}`;
  you treat `inputs` from the consumer as untrusted (into `env:`, never directly in `run:`).
- A PR diff requires `actions/checkout` with `fetch-depth: 0` (or fetching the base) — a shallow clone gives an empty diff.
- Do not write a multi-line value (a diff, a report) to `$GITHUB_OUTPUT` as `key=$(…)` — it breaks on a new
  line. Use a delimiter (`key<<EOF` … `EOF`) for content in which the delimiter will not occur; write arbitrary content (a diff,
  model output) to a file and pass the path — that is what the GitHub documentation recommends.
- A workflow that commits to the PR branch: `[skip ci]` in the subject and a guard step that skips the bot's commits. An AI PR review
  with a verdict gate: example 4 in `references/examples.md` and `.claude/skills/core-git-workflow/references/ai-review-in-ci.md`.

## Deployments
- A strategy with a fast rollback: blue/green, canary or rolling with healthchecks; the choice, canary gates, GitOps
  and expand–contract migrations — ops-release-engineering.
- Build and deployment on separate identities; secret scanning as the last safeguard after the local hooks —
  ops-secrets-identities. Kubernetes manifests validated in CI — ops-kubernetes.
- Every production deployment: who, what (SHA), when — visible in the history.

## Verification
`actionlint` (if available); check the YAML syntax; in the PR describe how the pipeline was tested.

## Example
**Situation:** "Add CI on every PR in a Node repo." **Result** (`.github/workflows/ci.yml`, abridged; plus
`concurrency` with `cancel-in-progress: true`):
```yaml
on: pull_request
permissions: { contents: read }
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-SHA> # v4
      - run: npm ci --ignore-scripts && npm run lint && npm run typecheck && npm test && npm run build
```
More examples: `references/examples.md`.

## Sources
- GitHub Docs: "Creating a composite action", "Workflow commands — multiline strings" (`GITHUB_OUTPUT` with a delimiter),
  "Metadata syntax" (`runs.steps[*].shell` required with `run`) — the github/docs repository, accessed 2026-10-10;
  `anthropics/claude-code-action`, `action.yml` (`claude_args`, `structured_output`; accessed 2026-10-10).
- The 10xDevs course, ed. 3 (2026), module 5, lesson 3 (composite action, AI review in CI) — training material (accessed 2026-10-09).
