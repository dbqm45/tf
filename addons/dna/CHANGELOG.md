# Changelog

## 0.3.0 — 2026-11-20
- UI catalog (`lib/code.py`), counted in the code with `path:line` evidence: design-system components (stack
  design-system packages, workspace UI packages, `design_system.packages` in dna.yaml) ordered by importing files,
  with the import form the code uses; own shared components imported by ≥ 2 files, `@deprecated` ones marked;
  tokens (CSS custom properties with use counts, SCSS variables in variables/tokens files, DTCG); theme files; the
  styling method as shares of styled files (CSS Modules, styled/emotion, `sx`, Tailwind, inline, plain CSS).
- `out/rules/ui.md` (rule with `paths` for UI files, ≤ 40 lines; the factory copies it to `.claude/rules/`) and
  `out/catalog/ui.md` (full lists); a line about it in `INDEX.md`; `provides.rules` in addon.yaml.
- Type imports (`import type`, inline `type X`, `…Props`) are not counted as components.

## 0.2.1 — 2026-11-20
- Typings of the locked version: `@types/<pkg>` from the lockfile next to the library (installed or from the npm
  registry); only its declarations are indexed.
- `.d.ts` chunks per declaration, also inside namespaces, with the JSDoc above it; the declaration line is the title.

## 0.2.0 — 2026-11-20
- Official documentation for the exact versions in the project (`lib/docs.py`): the installed package (no network),
  the npm tarball and the PyPI release description of that version, and sources listed per technology in
  `registry/docs-sources.yaml` (`raw` at the version's tag, `page`, `llms` marked latest-only). Only https, only
  registry and listed hosts, no private addresses; local BM25 index in `cache/docs/`.
- `dna.py docs query <tech> "<topic>"` (exit 3 when the version asked for is not the project's), `out/docs-index.md`
  (≤ 8 KB, in the permanent context through `context_extra`), a line about it in `INDEX.md`.
- `learn --offline` / `DNA_OFFLINE=1`; sources not read are listed in `coverage.md`.
- Python: dependencies in PEP 621 inline lists are detected.

## 0.1.0 — 2026-11-19
- Skeleton of the add-on: `addon.yaml` (contract 1), `dna.py learn | verify | status`, `knowledge.json` schema,
  Markdown generated from JSON, output replaced only after a passing check.
- Stack detection with exact versions from lockfiles: JavaScript/TypeScript (npm, pnpm, yarn; workspaces),
  Python (uv, poetry, pins), Go, Rust, Maven, Gradle version catalog and Spring Boot plugin, .NET.
- Runtime versions, commands (test, lint, build, typecheck, format) and formatting/lint tooling.
