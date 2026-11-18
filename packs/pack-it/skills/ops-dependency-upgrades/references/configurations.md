# Renovate and Dependabot configurations — examples

> **Contents:** Renovate (`renovate.json`) · Dependabot (`.github/dependabot.yml`) · End-of-support schedules (as of 2026-10-03)

Checked 2026-10-03:
- `renovate.json` passed `renovate-config-validator --strict --no-global` from the Renovate 44.132.4 package;
  the same validator rejects a typo in an option name;
- `dependabot.yml` parsed as YAML, and every key appears in the official description of the Dependabot options
  (github/docs, `dependabot-options-reference.md`).

Choose **one** tool per repository — two at once create duplicate PRs.

## Renovate (`renovate.json`)
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", ":semanticCommits"],
  "timezone": "Europe/Warsaw",
  "schedule": ["before 6am on monday"],
  "prConcurrentLimit": 5,
  "minimumReleaseAge": "3 days",
  "lockFileMaintenance": { "enabled": true, "schedule": ["before 6am on the first day of the month"] },
  "packageRules": [
    {
      "description": "Minor updates together; automatic merging with a green CI",
      "matchUpdateTypes": ["minor", "patch"],
      "matchCurrentVersion": "!/^0/",
      "groupName": "minor updates",
      "automerge": true,
      "automergeType": "pr"
    },
    {
      "description": "Major versions: a separate PR per dependency, no automatic merging",
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "addLabels": ["major-upgrade"]
    }
  ],
  "vulnerabilityAlerts": { "minimumReleaseAge": null, "schedule": ["at any time"] }
}
```
What it does:
- `config:recommended` — the recommended set (among others, a dependency dashboard in an issue, monorepo grouping);
- `schedule` + `timezone` — PRs only on Monday morning; `prConcurrentLimit` — at most 5 open at once;
- `minimumReleaseAge` — a 3-day cooldown for new versions (ops-supply-chain-security);
- the first rule: patch and minor (except `0.x` versions, where a minor may break compatibility) in one PR with automatic
  merging when CI is green;
- the second rule: major separately, without automatic merging;
- `vulnerabilityAlerts` — security patches: Renovate skips the schedule and PR limits for them by default
  (it requires Dependabot alerts enabled in the repository), and here explicitly also without a cooldown;
- `lockFileMaintenance` — a refresh of transitive dependencies once a month.

A local check before the commit: `npx --package renovate renovate-config-validator --strict --no-global renovate.json`.

## Dependabot (`.github/dependabot.yml`)
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "05:00"
      timezone: "Europe/Warsaw"
    open-pull-requests-limit: 5
    cooldown:
      default-days: 3
      semver-major-days: 14
    groups:
      minor-and-patch:
        update-types: ["minor", "patch"]
    labels: ["dependencies"]
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      minor-and-patch:
        update-types: ["minor", "patch"]
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
```
What it does:
- a weekly schedule for npm and uv, a monthly one for GitHub actions;
- `groups` — patch and minor in one PR per ecosystem; major separately (by default);
- `cooldown` — 3 days for everything, 14 days for major versions; on github.com Dependabot applies
  3 days for version updates by default anyway, and security patches have no cooldown;
- `open-pull-requests-limit` — at most 5 open PRs per ecosystem (5 by default for version updates).

Dependabot has no automatic merging option in `dependabot.yml`. If a human wants to merge minor updates
automatically, a separate workflow with required tests and branch protection does it — the agent does not enable it on its own.

## End-of-support schedules (as of 2026-10-03)
| Runtime | Status | Source |
|---|---|---|
| Node.js 20 | end of support 2026-04-30 | github.com/nodejs/Release (`schedule.json`) |
| Node.js 22 | maintenance (maintenance LTS) until 2027-04-30 | as above |
| Node.js 24 | active LTS, maintenance from 2026-10-20, end 2028-04-30 | as above |
| Node.js 26 | current release, LTS from 2026-10-28, end 2029-04-30 | as above |
| Python 3.10 | end of support 2026-10 | devguide.python.org/versions |
| Angular 20 | end of LTS 2026-11-28; 22 active, 21 LTS | angular.dev/reference/releases |
| Next.js | 16.x active LTS, 15.x maintenance; 14 and older unsupported | nextjs.org/support-policy |

Check the dates in the source with every plan — the table ages.
