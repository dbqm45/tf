# Changelog

## 0.3.0 — 2026-11-20
- Sources from the factory's configuration: `addons.standards.sources.<name>` in the company pack
  (`org_defaults.config`), the team pack (`team_defaults.config`) or the project's config, passed by the factory in
  TF_ADDON_SETTINGS; keyed by name so the layers add up, `enabled: false` turns one off; then the project's
  standards.yaml. `source list` shows where each source comes from.

## 0.2.0 — 2026-11-20
- The cheap model for what the patterns cannot read: a section of a standards skill or a Confluence page copy whose
  prose or tables use normative words, but with no rule in lists, becomes a pending item `tool: model` (tier fast)
  with the section text and the fixed prompt `prompts/extract.md`. The agent's subagent on the cheapest model
  answers with rules and verbatim quotes; only rules whose quote is found in the section are used (evidence: the
  quote's line), the rest is reported in coverage.md. The answer is reused while the section is unchanged.
- decisions.md shows the quote of rules read by the model; their acceptance says "cheap model, quote checked".

## 0.1.0 — 2026-11-20
- Split from dna 0.8.0: decisions from standards skills (in the project, by path, from a git repository by URL),
  ADRs, ESLint restricted imports, project docs and other agents' instruction files; merge, strength, acceptance.
- Confluence through the session's MCP tool: pending reads in `cache/pending.json` (`provides.pending`), page copies
  with a `Source:` / `Fetched:` header, stale copies listed for a re-read. No REST client and no credentials.
- Output: `out/INDEX.md`, `out/rules/standards*.md`, `out/decisions.md`, `out/decisions.json` (`provides.decisions`).
