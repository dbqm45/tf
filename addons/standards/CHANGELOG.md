# Changelog

## 0.1.0 — 2026-11-20
- Split from dna 0.8.0: decisions from standards skills (in the project, by path, from a git repository by URL),
  ADRs, ESLint restricted imports, project docs and other agents' instruction files; merge, strength, acceptance.
- Confluence through the session's MCP tool: pending reads in `cache/pending.json` (`provides.pending`), page copies
  with a `Source:` / `Fetched:` header, stale copies listed for a re-read. No REST client and no credentials.
- Output: `out/INDEX.md`, `out/rules/standards*.md`, `out/decisions.md`, `out/decisions.json` (`provides.decisions`).
