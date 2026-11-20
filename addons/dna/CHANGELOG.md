# Changelog

## 0.9.0 — 2026-11-20
- Breaking: decisions from sources (standards skills, Confluence, ADR, lint, docs, other agents' rule files) moved to
  the separate `standards` add-on, with `rules/standards*.md`, `decisions.md` and `dna.py standards`. dna keeps what
  the code is: stack, docs of the versions, UI catalog, styling, exemplars, `check`.
- `consumes: [decisions]`: decisions of other add-ons (TF_ADDON_DECISIONS) — an agreed rule that forbids an import
  is a hard finding of `check` and keeps files that use it out of the exemplars.

## 0.8.0 — 2026-11-20
- Standards skills from a git repository by URL: `dna.py standards add <git URL> [--ref <tag>] [--dir <skills
  dir>] [--scope fe|be|mutual]` (also `list`, `remove`; through the factory: `tf addon run dna standards add …`)
  writes `standards` in dna.yaml; `learn` clones the repository (shallow, `cache/standards/`), reads every skill
  under `--dir` with its references/ and rules/ and the Confluence pages it links to. Evidence: the repository URL,
  ref, path and line. Offline: the cached clone. `refresh` notices a new commit on the ref (`git ls-remote`).
- `DNA_CONFIG` points to another dna.yaml.

## 0.7.0 — 2026-11-20
- `dna.py refresh` (`provides.refresh`): learns again only when its inputs changed — a fingerprint of HEAD, the
  changed and untracked files, the standards skills, dna.yaml and the add-on version, stored in `knowledge.json`;
  the factory's blocks in CLAUDE.md / CLAUDE.local.md and the files the factory writes do not count.
- Documentation already indexed for a technology and version is reused from `cache/` (no fetch on re-learn).

## 0.6.0 — 2026-11-20
- Exemplar files per kind of change (`lib/exemplars.py`): page, component, form, hook, store, API endpoint,
  service, test, migration; chosen by script (recent by git, typical size, not legacy/generated, no deprecated
  component), with their test, local imports and users. `out/exemplars.md` and a line in `INDEX.md`; the factory's
  scout reads them from `knowledge.json`.
- Path aliases from `tsconfig.json` / `jsconfig.json` (`compilerOptions.paths`, comments allowed) in the UI catalog
  and exemplars: own components imported as `@/components/...` are found.

## 0.5.0 — 2026-11-20
- Decisions from sources (`lib/sources.py`): standards skills (`standards` in dna.yaml or skills named *standards*;
  SKILL.md, references/, rules/; scope fe/be/mutual from the config or the name), the Confluence pages they link to
  (REST API; credentials from the environment, sent only to the Atlassian site), ADRs, ESLint restricted imports,
  README/CONTRIBUTING/docs, instruction files of other agents (CLAUDE.md and AGENTS.md without the factory's blocks,
  Cursor rules with globs, Copilot instructions with applyTo). A decision is a list item or a rule-ID line with
  normative words (English and Polish); the quote is the source's own line.
- `lib/decide.py`: duplicates merged with all evidence; strength hard/soft; auto-accepted when a standards skill,
  an accepted ADR or a lint rule states it, or two independent sources do; otherwise a candidate (listed, not
  applied); rank by the hierarchy.
- Output: `out/rules/standards*.md` (rules with `paths` per scope, ≤ 40 lines, overflow pointer),
  `out/decisions.md` (applied and candidates with sources), a line in `INDEX.md`, hard rules for the whole repo in it.
- HTML list items stay list items when converted to text.

## 0.4.0 — 2026-11-20
- `dna.py check [--base <ref>] [--json]` (`lib/check.py`, `provides.check`): added lines of the change (untracked
  files included) against the guidelines, by the balance rule — hard findings (a deprecated component) block
  everywhere, soft ones (raw element where the design system has a component, value that has a token, duplicate of a
  catalog component, import form different from the code, styling method rare or absent in the code) block in new
  files and warn in existing ones. Exit 1 when a finding blocks; the factory's `/tf` gate runs it after green tests.

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
