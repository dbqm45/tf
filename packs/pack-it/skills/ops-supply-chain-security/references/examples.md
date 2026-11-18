# Examples: the supply chain

> **Contents:** 1. "Did axios hit us?" · 2. A cooldown and a script allowlist in pnpm · 3. Publishing your own package through OIDC

The names of repositories, internal packages and the numbers are illustrative; the axios data comes from `cases.md`.

## 1. "Did axios hit us?"
**Situation:** "I heard about the taken-over axios. We have 12 repositories with the frontend and backend in Node. Are we affected?"

**How:**
1. The facts from the advisory (`dependency-incident.md`, step 1): the malicious axios versions 1.14.1 and 0.30.4, the additional package
   `plain-crypto-js`, an attack window of about 3 hours.
2. You search with `grep` in the lockfiles of all repositories and release branches — you do not read whole files.
3. You check `node_modules` on the runners and laptops: the `plain-crypto-js` directory alone means that `postinstall` was executed.
4. For hits: the list of machines that installed during the attack window → rebuild and secret rotation (steps 3–5 of the procedure).
5. You pin a safe version through `overrides` and check which safeguard would have stopped the attack.

**Result:** the commands and the expected results.

```bash
#!/usr/bin/env bash
# Run in the directory with the repository clones (e.g. ~/src/acme).
set -euo pipefail

# 1. The additional package from the attack and the malicious axios versions in the lockfiles
LOCKS=(--include=package-lock.json --include=pnpm-lock.yaml --include=yarn.lock)
grep -rn "${LOCKS[@]}" 'plain-crypto-js' . || echo "lockfile: no plain-crypto-js"
grep -rn -A3 "${LOCKS[@]}" 'axios' . | grep -E '1\.14\.1|0\.30\.4' || echo "lockfile: no malicious axios versions"

# 2. A trace of an executed postinstall
find . -type d -name plain-crypto-js -path '*node_modules*' -print | grep . || echo "node_modules: no hits"

# 3. Release branches without a checkout
for repo in */; do
  for ref in $(git -C "$repo" for-each-ref --format='%(refname:short)' 'refs/remotes/origin/release/*' 2>/dev/null); do
    git -C "$repo" grep -n 'plain-crypto-js' "$ref" -- '*lock*' || true
  done
done
```

| Result | Meaning | Next |
|---|---|---|
| only "no …" messages in all 12 repositories | not affected | an entry in the project log, conclusions (step 7) |
| `./web-shop/package-lock.json:4182: "node_modules/plain-crypto-js": {` | the version was in the tree | the machines that installed during the attack window = compromised |
| `./web-shop/node_modules/plain-crypto-js` on the runner `ci-runner-07` | the script was executed | destroy the runner and the image, rotate the secrets from the runner |

## 2. A cooldown and a script allowlist in pnpm
**Situation:** "We want to protect ourselves against the next axios. The project is on pnpm 10, Renovate opens PRs every day".
A day later a critical vulnerability in `react-dom` was announced, and the application is internet-facing.

**How:**
1. A 3-day cooldown in the package manager (section 2) — and separately in Renovate.
2. Install scripts only from an allowlist (`onlyBuiltDependencies`), in CI additionally `--ignore-scripts` where
   the build does not need them (section 3).
3. Installation in CI only from a frozen lockfile (section 1).
4. The patch within 24 hours: a single exception with a review of the package diff, not disabling the cooldown (section 2).
5. You remove the exception when the patch is older than 3 days.

**Result:** the configuration.

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "libs/*"
minimumReleaseAge: 4320          # minutes = 3 days
minimumReleaseAgeExclude:
  - react-dom                    # critical patch, PR #812, diff review: @jkowalska; remove after 3 days
onlyBuiltDependencies:
  - esbuild
```

```bash
# CI
pnpm install --frozen-lockfile
```
In the PR with the patch: "An exception only for `react-dom`; the package diff reviewed, no new transitive dependencies".

## 3. Publishing your own package through OIDC
**Situation:** "We publish `@acme/ui-kit` from the lead's laptop with a classic token. Let's move it to CI".

**How:**
1. A trusted publisher in npm pinned to one workflow file and a protected environment with approval (section 4).
2. Publishing only from a tag in the main repository, never from commits from forks.
3. `--provenance` when publishing; consumers check `npm audit signatures`.
4. Classic tokens revoked — in axios a working old token bypassed the configured OIDC.
5. Actions pinned to a SHA, install scripts disabled.

**Result:** `.github/workflows/publish.yml`.

```yaml
name: publish
on:
  push:
    tags: ["v*.*.*"]
permissions:
  contents: read
jobs:
  publish:
    if: github.repository == 'acme/ui-kit'
    runs-on: ubuntu-latest
    environment: npm-publish      # a human's approval required
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@<SHA>
      - uses: actions/setup-node@<SHA>
        with:
          registry-url: https://registry.npmjs.org
      - run: npm ci --ignore-scripts
      - run: npm test
      - run: npm publish --provenance --access public
```
After the first publication: the lead's classic tokens revoked, the account with a hardware key, an entry in the decision log.
