# A wide repo scan — tools, legend, couplings

## 1. Search: which family for which question
| Question | Family | Tool | Pitfall |
|---|---|---|---|
| where a word or pattern occurs | text | `rg` | needs the project's vocabulary; catches comments and strings |
| where a symbol's definition, signature, call is | structural / symbolic | ast-grep, ctags, LSP ("find references"), SCIP | a wrong pattern = an empty hit without an error → you confirm a zero with `rg` |
| who imports a module | dependency graph | madge, dependency-cruiser, jdeps, `nx graph` | does not see runtime dependencies |
| "something like…", I do not know the name | semantic (embeddings) | a RAG index | a stale index, a probabilistic result |
| how a flow goes through the layers | agentic (iterative) | a subagent | keep it short in a wide scan — it is a deepening task |
A tool advertised as "semantic search" is sometimes structural (AST), not vector-based — do not assign it
approximate confidence until you check how it works.

The ast-grep binary is `ast-grep` (packages: npm `@ast-grep/cli`, pip `ast-grep-cli`, cargo `ast-grep`). The package
also installs the alias `sg`, but on Linux `/usr/bin/sg` (the `login` package) runs a command with a different group —
use the full name in scripts and instructions.

## 2. dependency-cruiser, when the graph is a tangle (checked on 18.5.0)
| Lever | Flag | When |
|---|---|---|
| nodes = folders | `--collapse "^src/[^/]+"` or `--collapse 2` | the first view of a large repo |
| down from a module | `--focus "^src/billing" --focus-depth 1` | the neighbours of one module |
| who leads to X | `--reaches "^src/db/"` | the reach of a change in a base module |
| stability metrics | `--metrics` (Ca, Ce, instability) | candidates for load-bearing modules |
| architecture view | `-T archi` (or `-T mermaid`, `-T dot`) | a diagram for the map |
| changed since a revision | `--affected <revision>` | diff impact |
**Pitfall:** `--do-not-follow node_modules` (or `doNotFollow` in the configuration) leaves packages as leaves of the graph.
To make them disappear from the picture, exclude them: `--exclude "node_modules|\.test\.|\.spec\.|\.stories\.|__snapshots__|\.d\.ts$"`.
First a text result with a table (area · finding · evidence · why it matters · what next); an SVG render only for
one subgraph that answers one question. It needs the project's toolchain installed (TS: `tsconfig`).

## 3. The graph outside JS/TS and blind spots
| Ecosystem | Tool (check the syntax in the documentation of the version) | Blind spot |
|---|---|---|
| Java | `jdeps`, ArchUnit, `mvn dependency:tree`, the Gradle module graph | reflection, `Class.forName`, DI from configuration |
| Python | Tach, pydeps, import-linter | dynamic imports (`importlib`), plugins through entry points |
| Go | `go mod graph`, goda | interfaces satisfied implicitly |
| .NET | the project reference graph (`dotnet list reference`) | DI in `Program.cs`, reflection |
| Swift | `swift package show-dependencies` | — |
| TS | madge, dependency-cruiser, skott | path aliases without `tsconfig` lose imports |
You write the blind spots into the map's "Limitations" section.

## 4. Territory from history — how to read the output of `git_territory.py`
- **Ranking of directories and files:** where the work happens. When a too general directory is at the top, increase `--depth`.
- **Quarters:** a directory at the top in every quarter = a stable centre (the core); one quarter = a campaign (a migration,
  a rewrite) — check whether it is finished.
- **Co-change pairs:** a share ≥ 0.8 (almost always together) = a hidden agreement between files — a candidate for connascence
  of meaning or algorithm (ddd-connascence-analysis). A pair resulting from regeneration (generated code + schema) is
  cheaper than manual editing — mark it.
- **Hubs:** a file changed together with many areas (configuration, translations, the route registry) = a wide reach of change;
  the hub ranking ≠ the pair ranking.
- **Co-changes lie both ways:** mass commits glue unrelated files together (hence `--max-files`); the absence of
  co-changes does not prove the absence of an agreement (a backend model and its hand-made copy on the front end that do NOT change together
  are silent debt → an `unknown` to check in the code).
- **Deleted files** in the ranking: the past. Do not put them on the reading route.

## 5. Module legend
| Axis | Values | Evidence |
|---|---|---|
| role | core / supporting / peripheral | an entry point, a public contract, the product's main flow — not the folder name |
| depth | deep / shallow | internal branching and rules vs a router, adapter, wrapper (eng-module-depth) |
| change profile | stable / volatile / seasonal | the quarterly ranking |
| reach | load-bearing / contained | high Ca, contracts, auth, data, cache, migrations, runtime configuration |
| sensitivity | high / medium / low | the sum of the above + cycles + integrations |
A module entry: role · evidence (a list) · inference · caution (what to check before a change) · unknowns. A label without
evidence is a guess → `to verify`.

## 6. Kinds of coupling on the map
| Kind | How you know | Notes |
|---|---|---|
| incoming / outgoing | the import graph | Ca / Ce |
| contractual | shared types, DTOs, schemas | a contract change = a change of all sides |
| runtime | DI, flags, queues, webhooks, reflection, dynamic import, codegen | the graph does not see them → always in `unknowns`, unless checked in the code |
| co-change | git history | pair vs hub; regeneration cheaper than manual editing |
For every coupling give the source: the import graph / history / "the tool did not cover it".
