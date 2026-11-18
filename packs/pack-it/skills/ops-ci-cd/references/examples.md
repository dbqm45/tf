# CI/CD examples

> **Contents:** 1. A new CI workflow for PRs · 2. Fixing an injection through the PR title · 3. One image from staging to production · 4. An AI PR review with a verdict gate

The examples apply the rules from SKILL.md. `<full-SHA>` is the place for the 40-character SHA of the action's commit — look it up
in the action's repository and leave the tag in a comment, so that updates stay readable.

## 1. A new CI workflow for PRs
**Situation:** "Add CI to our Node repo: lint, types, tests and a build on every PR. Right now there is nothing."

**How:**
1. Fail-fast order: lint and typecheck (seconds) before the tests and the build.
2. `permissions: contents: read` at the workflow level; no job needs more.
3. Actions pinned to a SHA; the npm cache through `setup-node`.
4. `npm ci --ignore-scripts` — the job has no secrets, but install scripts have no business here anyway.
5. `concurrency` with `cancel-in-progress: true`, so that a new push cancels the old run.

**Result:** `.github/workflows/ci.yml`
```yaml
name: ci
on:
  pull_request:
    paths: ["src/**", "package.json", "package-lock.json", ".github/workflows/ci.yml"]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-SHA> # v4
      - uses: actions/setup-node@<full-SHA> # v4
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci --ignore-scripts
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
      - run: npm run build
```
Verification: `actionlint` (if available) and YAML parsing; in the PR description: "workflow run on this PR, the run is green,
cancellation checked with a second push".

## 2. Fixing an injection through the PR title
**Situation:** A security review pointed to a workflow that labels PRs. It runs on `pull_request_target`
and pastes the PR title straight into `run:`.

**How:**
1. Find the interpolation `${{ github.event.* }}` in `run:` — a title `"; curl … #` will execute in the runner's shell.
2. Move the value to `env:` and use it as a quoted shell variable.
3. Keep `pull_request_target` only because the job does not fetch code from the fork; narrow the permissions to `pull-requests: write`.
4. Pin the actions to a SHA.

**Result:** before (vulnerable):
```yaml
on: pull_request_target
jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Title: ${{ github.event.pull_request.title }}" >> "$GITHUB_STEP_SUMMARY"
```
after:
```yaml
on: pull_request_target

permissions:
  contents: read

jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      # no actions/checkout: code from the fork does not reach a runner with write permission
      - name: Summary
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          printf 'Title: %s\n' "$PR_TITLE" >> "$GITHUB_STEP_SUMMARY"
```

## 3. One image from staging to production
**Situation:** "The pipeline builds the image separately for staging and production, and the cloud keys sit in the repo secrets.
We want it safer and without rebuilding."

**How:**
1. Build once; the image digest as the job output goes through all environments.
2. Deployments through OIDC (`id-token: write` only in the deployment jobs), with no keys in secrets.
3. Staging → smoke tests → production in the `production` environment with required approval.
4. Every deployment records the SHA and the digest in the run summary — who, what, when.

**Result:** `.github/workflows/deploy.yml`
```yaml
name: deploy
on:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: deploy
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@<full-SHA> # v4
      - id: push # the script writes "digest=sha256:…" to $GITHUB_OUTPUT
        run: ./scripts/build-and-push.sh "ghcr.io/acme/orders-api" "$GITHUB_SHA"

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<full-SHA> # v4
      - uses: aws-actions/configure-aws-credentials@<full-SHA> # <tag>
        with:
          role-to-assume: arn:aws:iam::111111111111:role/deploy-staging
          aws-region: eu-central-1
      - env:
          DIGEST: ${{ needs.build.outputs.digest }}
        run: ./scripts/deploy.sh staging "ghcr.io/acme/orders-api@$DIGEST"
      - run: ./scripts/smoke-test.sh https://staging.acme.example

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<full-SHA> # v4
      - uses: aws-actions/configure-aws-credentials@<full-SHA> # <tag>
        with:
          role-to-assume: arn:aws:iam::222222222222:role/deploy-production
          aws-region: eu-central-1
      - env:
          DIGEST: ${{ needs.build.outputs.digest }}
        run: |
          ./scripts/deploy.sh production "ghcr.io/acme/orders-api@$DIGEST"
          printf 'Deployed %s (%s) by %s\n' "$DIGEST" "$GITHUB_SHA" "$GITHUB_ACTOR" >> "$GITHUB_STEP_SUMMARY"
```
The production role trusts only OIDC tokens from the `production` environment of this repository. The rollout and rollback strategy
in `deploy.sh` — ops-release-engineering.

## 4. An AI PR review with a verdict gate
**Situation:** "Claude is to review PRs labelled `ai-review`, and a "rejected" verdict is to block the merge."

A ready workflow, pinned to a SHA, with these rules is installed by
`python3 .claude/skills/core-git-workflow/scripts/ai_review.py install` (core-git-workflow); below is an abridged version for
your own changes.

**How:**
1. `permissions: {}` at the top, in the job only what it needs (comments, the commit status).
2. The fork block and the label condition in the job's `if:`; `concurrency` per PR number.
3. `fetch-depth: 0` — without the base history the three-dot diff is empty.
4. The agent returns JSON according to a schema (`--json-schema` in `claude_args` → the `structured_output` output); limits and tools
   also in `claude_args`.
5. The gate in a separate `if: always()` step: no valid verdict = a red status, not a silent pass.
   An override only with a label added by a human. Branch protection requires the `ai-review/verdict` status.

**Result:** `.github/workflows/ai-review.yml` (abridged; the review rules in `.github/review-criteria.md`)
```yaml
name: ai-review
on:
  pull_request:
    types: [opened, synchronize, reopened, labeled]

permissions: {}

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    if: >-
      github.event.pull_request.head.repo.full_name == github.repository &&
      contains(github.event.pull_request.labels.*.name, 'ai-review')
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: read
      pull-requests: write
      statuses: write
    steps:
      - uses: actions/checkout@<full-SHA> # v4
        with:
          fetch-depth: 0
      - id: review
        uses: anthropics/claude-code-action@<full-SHA> # v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review the changes of this PR (git diff origin/${{ github.base_ref }}...HEAD) according to .github/review-criteria.md.
            Inline comments only on the lines added in the diff. Do not approve the PR. Return the verdict in the verdict field.
          claude_args: >-
            --model <model> --max-turns 30
            --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*)"
            --json-schema '{"type":"object","properties":{"verdict":{"enum":["APPROVED","NEEDS_ATTENTION","REJECTED"]}},"required":["verdict"]}'
      - name: Verdict as a commit status
        if: always()
        env:
          GH_TOKEN: ${{ github.token }}
          OUT: ${{ steps.review.outputs.structured_output }}
          OVERRIDE: ${{ contains(github.event.pull_request.labels.*.name, 'ai-review-override') }}
          SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          verdict=$(printf '%s' "$OUT" | jq -r '.verdict // "NONE"' 2>/dev/null || echo NONE)
          case "$verdict" in APPROVED|NEEDS_ATTENTION) state=success ;; *) state=failure ;; esac
          desc="AI: $verdict"
          if [ "$OVERRIDE" = "true" ]; then state=success; desc="AI: $verdict, overridden by label"; fi
          gh api "repos/$GITHUB_REPOSITORY/statuses/$SHA" \
            -f state="$state" -f context=ai-review/verdict -f description="$desc"
```
To add when needed: a light job on `labeled/unlabeled` with the override label (only the verdict step, without a new
review), a commit of the report by the bot with `[skip ci]` and a guard, de-duplication of comments —
`.claude/skills/core-git-workflow/references/ai-review-in-ci.md`. Verification: `actionlint`; a test PR with a planted bug (a red status)
and a clean PR (a green status).
