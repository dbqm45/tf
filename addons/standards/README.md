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

A rule is a list item or a rule-ID line (`FE-UI-001: …`) with normative words (must, never, should, prefer, avoid…,
also Polish). A section of a standards skill or Confluence page that states rules in prose or tables goes to the
cheapest model in the session (pending item `tool: model`, prompt `prompts/extract.md`); a rule it returns counts
only when its quote is found verbatim in the section. Duplicates are merged; `hard` / `soft` by the wording; a rule is
applied when a settling source (standards skill, accepted ADR, lint) or two independent sources state it, otherwise
it is a listed candidate.

## Use

```bash
python3 standards.py source add https://github.com/acme/standards.git --ref v1.4.0 --dir skills [--scope fe]
python3 standards.py learn            # or, through the factory: tf learn
python3 standards.py pending          # Confluence pages waiting for the agent (MCP)
python3 standards.py refresh          # again only when the inputs changed (the factory: at session start)
```

## Confluence through MCP

The script never contacts Confluence. For each page linked from a standards skill without a fresh copy it writes a
pending read to `cache/pending.json` (`provides.pending`). The factory announces it at session start and the agent
reads the page with the Confluence tool connected in the session (read-only), saves its text to the given file with
the header lines `Source:`, `Fetched:` (and `Version:`), and runs `tf addon refresh`. A copy older than
`confluence.stale_after_days` (standards.yaml, default 14) is still used and listed for a re-read. Page copies live
in `cache/`, outside git.

## Output (contract 1)

| File | Content |
|---|---|
| `out/INDEX.md` | ≤ 15 lines for the permanent context |
| `out/rules/standards*.md` | rules with `paths` per scope (fe, be, whole repo), ≤ 40 lines each |
| `out/decisions.md` | all decisions with quotes and sources; candidates listed, not applied |
| `out/decisions.json` | applied decisions for other add-ons (`provides.decisions`) |
| `out/coverage.md` | sources read and not read (with the reason) |

## Rules for changes

Nothing here imports from the factory or from other add-ons. Tests: `python3 tests/test_sources.py`,
`tests/test_sources_git.py` (CI job `addons`). SemVer in `addon.yaml`, changes in `CHANGELOG.md`.
