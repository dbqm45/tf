# Changelog

## 0.1.0 — 2026-11-19
- Skeleton of the add-on: `addon.yaml` (contract 1), `dna.py learn | verify | status`, `knowledge.json` schema,
  Markdown generated from JSON, output replaced only after a passing check.
- Stack detection with exact versions from lockfiles: JavaScript/TypeScript (npm, pnpm, yarn; workspaces),
  Python (uv, poetry, pins), Go, Rust, Maven, Gradle version catalog and Spring Boot plugin, .NET.
- Runtime versions, commands (test, lint, build, typecheck, format) and formatting/lint tooling.
