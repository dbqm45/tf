# The reconstruction report template (`docs/project/00-reconstruction/report.md`)

Sections in this order (`recon_check.py --final` checks them). Every bullet: `file:line` evidence or
the marker [assumption] / [unverified] / [question]. In "Questions" and "Not checked" evidence is not required.

`--final` also checks:
- **Stack** as a table with the rows Language, Framework, Data, Build, Tests, CI, Configuration. A row without evidence has
  a marker, e.g. "CI: [unverified] no pipeline files in the repo". A version mismatch (CI versus the build file,
  the image versus the SDK) you enter in the row and repeat in Risks.
- **CI**: when there are pipeline files in the repo (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` and similar), the CI row
  points to one of them as evidence. A bare "no CI [unverified]" will then not pass.
- **Modules**: every module from the cards `modules/*.json` has an entry and a current `modules/<module>.md` from `recon_cards.py`. The section
  is inserted by `recon_cards.py modules/ --into report.md`: the purpose, the evidence, key elements (entry points, terms, tables)
  and a link. A large module is split by batches (a card per package or project), so the level below is visible without adding anything.

```markdown
# <Project name> — reconstruction from code
Commit: <sha> · date: YYYY-MM-DD · scope: <everything | directories> · run cost: <USD, models>

## TL;DR
5–7 sentences: what the system is, for whom, the most important modules, the biggest risk, how many questions for people.

## Stack
| Area | Finding (with version) | Evidence |
|---|---|---|
| Language | <language and version; mismatches, e.g. CI ≠ build file> | `<build file>:<line>` |
| Framework | <framework and version, main libraries> | `<file>:<line>` |
| Data | <database, ORM, migrations, versions> | `<file>:<line>` |
| Build | <tool and version, wrapper> | `<file>:<line>` |
| Tests | <framework, test containers, coverage (e.g. JaCoCo)> | `<file>:<line>` |
| CI | <system, environment versions, steps> | `<file>:<line>` |
| Configuration | <profiles, settings with an effect (e.g. ddl-auto), environment variables> | `<file>:<line>` |
| Deployment | <image, manifests; optional> | `<file>:<line>` |

## Modules
- <module>: <responsibility in one sentence> — `<file>:<line>` · key: <entry points, terms, tables> (details: modules/<module>.md)
  - <package or project one level below>: <responsibility> — `<file>:<line>`

## Domains
- <subdomain> (core | supporting | generic): <what for> — `<file>:<line>`; glossary: domain.md

## Requirements
- <requirement in business language> — `<test or code>:<line>` (confidence: test | code | to confirm)

## Rules
- <business rule> — `<file>:<line>` "<quote from the line>" (confidence)

## Standards
- <area>: <rule> — <share>% (`standards/<area>.md`), exceptions: <how many>

## Risks
- <risk> — `<file>:<line>` (a hotspot, a cycle, no tests, a secret in the configuration…)

## Questions
- [question] <to whom> — <question>

## Not checked
- <area> — why (DI, reflection, queues, HTTP between services, external configuration, out of scope)
```
