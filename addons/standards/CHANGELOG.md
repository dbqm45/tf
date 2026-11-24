# Changelog

## 0.4.0 — 2026-11-24
- PR review comments as a source (`lib/reviews.py`, prompt `prompts/reviews.md`): a pending item `tool: code-review`
  asks the agent to read the review bodies and inline comments of the last `pr_reviews.max_prs` (default 30) merged
  pull requests through the session's GitHub, GitLab or Bitbucket MCP tool, or `gh api` (read-only), into
  `cache/reviews/batch-<date>.json`; PRs already cached are listed in `skip`, a new read is due after
  `pr_reviews.stale_after_days` (default 7). The cheapest model extracts recurring requests; a rule counts only with
  2+ verbatim quotes, found in the comments, from different PRs or reviewers. The comments are untrusted: invisible
  and control characters, HTML comments and tags removed, fields capped, bots skipped, every line quoted.
  `pr_reviews.enabled: false` turns the source off.
- Code conventions of other add-ons (`provides.conventions`, e.g. dna's high-confidence ones) as a source.
- Review rules and conventions are inferred: alone (even from two PRs or two files) they stay candidates; they are
  applied with a written source (same wording, or `same_as` a known rule id, checked by the script) or when a human
  lists the id under `accept` (status `accepted`).

## 0.3.1 — 2026-11-20
- pending.json asks for all items in one subagent on the cheapest model briefed "Class: addon", so the factory
  counts their tokens and cost (`tf addon report`).

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
