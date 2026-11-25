# standards — the project's agreed rules for the factory

`standards` does not write standards. It reads the ones you have and writes them as rules the factory loads for the
matching files:

| Source | How |
|---|---|
| standards skills | in the project (`.claude/skills/*standards*`), by path, or from a git repository by URL (`source add`) |
| Confluence pages the skills link to | read by the agent through the session's MCP tool (see below) |
| ADR | `docs/adr`, `docs/decisions`, `adr`, `doc/adr` (an accepted ADR settles a rule) |
| lint | ESLint `no-restricted-imports` with a message (also as `forbidden_import` for other add-ons) |
| docs | README, CONTRIBUTING, `docs/**/*.md` |
| other agents' rule files | CLAUDE.md, AGENTS.md (without the factory's blocks), Cursor rules (globs), Copilot instructions (applyTo) |
| PR review comments | recurring requests in the last 30 merged pull requests, read by the agent (MCP or `gh api`, see below); candidates only |
| code conventions | high-confidence conventions of another add-on (`provides.conventions`, e.g. dna); candidates only |

A rule is a list item or a rule-ID line (`FE-UI-001: …`) with normative words (must, never, should, prefer, avoid…,
also Polish). A section of a standards skill or Confluence page that states rules in prose or tables goes to the
cheapest model in the session (pending item `tool: model`, prompt `prompts/extract.md`); a rule it returns counts
only when its quote is found verbatim in the section. Duplicates are merged; `hard` / `soft` by the wording; a rule is
applied when a settling source (standards skill, accepted ADR, lint) or two independent sources state it, otherwise
it is a listed candidate. Review rules and code conventions are inferred, not written: alone (even from two pull
requests or two files) they stay candidates; with a written source they count as the second one.

A candidate is confirmed by writing it in a source (a standards skill, CONTRIBUTING, CLAUDE.md…) or by listing its id
(`D-…` in `decisions.md`) under `accept` in the configuration (`addons.standards.accept` or standards.yaml): status
`accepted`.

## Where the sources are set

| Where | For | How |
|---|---|---|
| company pack `pack.yaml` → `org_defaults.config.addons.standards` | every project of the company | `sources.<name>: {git, ref, dir, scope}`, `install: true` |
| team pack → `team_defaults.config.addons.standards` | the team's projects | its own `sources.<name>` (added to the company's) |
| project `.tf/config/config.yaml` → `addons.standards` | this project | add a source, or `sources.<name>.enabled: false` |
| project `standards.yaml` here (`source add`) | this project | local sources, listed after the configured ones |
| any of the layers → `addons.standards.pr_reviews` | PR reviews | `{enabled: false}` turns it off; `max_prs` (30), `stale_after_days` (7) |

The factory merges the configuration layers and passes `addons.standards` in TF_ADDON_SETTINGS; with
`install: true`, `tf learn` installs this add-on where it is missing. `source list` shows every source and where it
comes from.

## Use

```bash
python3 standards.py source add https://github.com/acme/standards.git --ref v1.4.0 --dir skills [--scope fe]   # project only
python3 standards.py learn            # or, through the factory: tf learn
python3 standards.py pending          # what waits for the agent: Confluence pages, PR reviews (MCP), the cheap model
python3 standards.py refresh          # again only when the inputs changed (the factory: at session start)
```

## Confluence through MCP

The script never contacts Confluence. For each page linked from a standards skill without a fresh copy it writes a
pending read to `cache/pending.json` (`provides.pending`). The factory announces it at session start and the agent
reads the page with the Confluence tool connected in the session (read-only), saves its text to the given file with
the header lines `Source:`, `Fetched:` (and `Version:`), and runs `tf addon refresh`. A copy older than
`confluence.stale_after_days` (standards.yaml, default 14) is still used and listed for a re-read. Page copies live
in `cache/`, outside git.

## PR reviews through MCP or gh

Reviewers repeat the team's unwritten rules ("don't use X, we have helper Y"). With an `origin` remote, `learn`
writes a pending item `tool: code-review`: the agent reads, read-only, the review bodies and inline review comments
(not descriptions, not the conversation) of the last `max_prs` merged pull requests through the session's GitHub,
GitLab or Bitbucket MCP tool, or with the `gh` commands of the item when `gh` is installed and authenticated, and
saves them as JSON to `cache/reviews/batch-<date>.json`. Pull requests already cached are in `skip`; a new read is
due after `stale_after_days`. The comments of the window then go to the cheapest model (`prompts/reviews.md`); its
answer is reused while the window is unchanged. A rule counts only with 2+ verbatim quotes, found in the comments,
from different pull requests or reviewers; evidence is the pull request URL with the fetch date.

The comments are untrusted (anyone who can comment writes them): invisible and control characters, HTML comments
and tags are removed, every field is capped, bots are skipped, the model sees every line as a quote, rules with
links are dropped, and a review rule never becomes a rule file on its own.

## Output (contract 1)

| File | Content |
|---|---|
| `out/INDEX.md` | ≤ 15 lines for the permanent context |
| `out/rules/standards*.md` | rules with `paths` per scope (fe, be, whole repo), ≤ 40 lines each |
| `out/decisions.md` | all decisions with quotes and sources; candidates listed, not applied |
| `out/decisions.json` | applied decisions for other add-ons (`provides.decisions`) |
| `out/coverage.md` | sources read and not read (with the reason) |

## Rules for changes

Nothing here imports from the factory or from other add-ons (another add-on's conventions are read as a file it
declares). Tests: `python3 tests/test_sources.py`, `tests/test_sources_git.py`, `tests/test_reviews.py` (CI job
`addons`). SemVer in `addon.yaml`, changes in `CHANGELOG.md`.
