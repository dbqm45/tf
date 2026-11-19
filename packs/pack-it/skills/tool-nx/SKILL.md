---
name: tool-nx
description: Use for an Nx monorepo — projects and libraries, tags and module boundaries, generators, cache, affected, release, migrate.
disable-model-invocation: true
metadata:
  status: "inactive"  # measurement 2026-11-16: docs/inactive-skills.md
  review: "2027-01-17"
  catalog: "Use in an Nx monorepo — project and library structure, tags and module boundaries, generators, tasks and cache, affected, nx release, migrations (nx migrate). Also when mapping DDD bounded contexts onto Nx libraries. Not for framework conventions (fw-*) or language conventions (lang-*)."
---

# Nx (monorepo)

## Rules
1. **Applications are thin, logic lives in libraries.** An application composes routes and configuration; feature, domain and UI code lives in `libs/`.
2. **Tags and module boundaries are mandatory.** Every project has tags in at least two axes:
   `scope:<area>` (context/domain) and `type:<kind>` (feature, ui, data-access, domain, util). The
   `@nx/enforce-module-boundaries` rule (ESLint) guards the allowed dependencies — do not disable it with a comment.
3. **Run only what changed:** `nx affected -t lint test build` locally and in CI; `nx run-many` only deliberately.
4. **The cache is a contract:** deterministic tasks, correct `inputs`/`outputs` in `targetDefaults` or in plugins;
   a task that reads undeclared files = a wrong cache.
5. **Tasks inferred by plugins** (`nx.json → plugins`) instead of copying targets by hand into every `project.json`.
6. **Generators instead of copying:** `nx g @nx/angular:library …` (or the repo's own generator) — consistent tags and structure.
7. **Migrations through `nx migrate`:** `npx nx migrate latest` → review `migrations.json` → `npx nx migrate --run-migrations`;
   it upgrades Nx and the related frameworks together (e.g. Angular). Do not mix manual version bumps with migrations.
8. **Releases:** `nx release` (versioning, a changelog from Conventional Commits — core-conventional-commits, publishing).
9. **The project graph** (`nx graph`) is the first source of truth about dependencies when analysing the architecture.

## Domain concepts in Nx
| Concept | Mapping in Nx |
|---|---|
| **module / bounded context** | a group of libraries with the tag `scope:<context>`; dependencies between contexts only through public libraries (e.g. `type:api`) |
| **module edge (small interface)** | a `type:api`/`feature` library with a narrow `index.ts`; the rest of the context is unavailable to other `scope:`s |
| **domain layer** | a `type:domain` library — no dependency on the framework or on `data-access` |
| **repository / port** | an interface in `type:domain`, the implementation in `type:data-access` |
| **read model / UI** | `type:data-access` (state, queries) + `type:ui` (presentational components) |
| **Shared Kernel** | a `scope:shared` library — minimal, with an owner, changes consulted |
| **ACL** | a `type:data-access` library in the consumer's context that translates the contract of a foreign context |

`depConstraints` (`onlyDependOnLibsWithTags`) in `eslint.config.mjs` maps the table: `type:domain` depends only on
`domain`/`util`, and `scope:<context>` only on itself and `scope:shared`.

## Version-dependent
| Version | What changed |
|---|---|
| 21 | baseline: tasks inferred by plugins, `nx release`, Terminal UI |
| 22 | database cache mandatory (`NX_DISABLE_DB` removed); `createNodes` v1 deprecated in favour of `createNodesV2`; old `nx release` versioning removed; npm without forcing `--legacy-peer-deps`; experimental Maven support, the `@nx/dotnet` plugin |
| 23 | minimum Node 22 LTS; the `...` operator in targets extends the inherited `targetDefaults` instead of replacing them; "agentic" migrations (generator, prompt or hybrid); task sandboxing (verifying reads/writes against inputs/outputs); Vitest split out into `@nx/vitest`; removed, among others, the Angular NgRx generators and `move`; `@nx/dotnet` stable |
| 23.1 | support for Angular 22 (Angular 19 no longer supported), TypeScript 6 (TS 7 alongside TS 6, because TS 7 has no programmatic API); `targetDefaults` as an ordered array with filters; ESLint 9 required; performance reports after every run |

## Checklist
- [ ] every project has `scope:` and `type:` tags; the boundaries lint passes
- [ ] CI uses `nx affected` and a remote cache
- [ ] upgrades through `nx migrate`, not manual bumps
