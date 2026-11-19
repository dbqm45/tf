# Team notes, wiki and freshness of knowledge

Contents: 1. Three write zones · 2. The note header · 3. A concept pinned to paths · 4. An instructions file or
a pipeline in code · 5. Freshness of generated knowledge

## 1. Three write zones
| Zone | Where in the factory | Who changes it |
|---|---|---|
| Sources | `.claude/knowledge/<id>/` (`kb.py ingest`), the `zrodla.json` registries | nobody edits; only fetching again |
| Pages maintained by the agent (summaries, maps, indexes) | `docs/knowledge/**`, with a `sources` field | the agent; an **update** of an existing page, not rewriting it from scratch |
| The team's notes and decisions | `docs/knowledge/**`, `docs/project/decisions.md` | only with the human's consent |

Every load of new sources you start with a plan: which pages will be created and which will change. The human sees it
before the write.

## 2. The note header
A note in `docs/knowledge/` has a short frontmatter, so other agents read it without guessing:
```yaml
type: decision        # decision | concept | partner | metric | runbook
owner: zespół-płatności
status: stable        # draft | stable | deprecated
sources: [docs/project/decisions.md#D-14, https://… (2026-10-20)]
code_refs:            # section 3
  - {path: src/payments/api/, level: constraint}
verified: 2026-10-30  # ONLY the human writes it; the agent sets generated: <date>
stale_after: 2027-04-30
```
- **Only the human writes the `verified` field.** The agent writes `generated` with a date. A page "verified by
  the agent" is not verified.
- You describe a concept **in the words people search with** (and synonyms: "deploy", "wdrożenie", "release").
  Word search (BM25, `kb.py search`) does not know synonyms.
- A decision records the chosen option, the rejected options with a reason and whether the code implements it. The agent cannot read that
  from the repo.
- The project's most common traps go at the start of the index (`docs/knowledge/index.md`, if you have one) or to
  `docs/project/lessons.md`.
- This layout is close to the fields proposed in the OKF format (`type`, `status`, `stale_after`, `verified`,
  `index.md`). Compatibility with the format itself was not checked [unverified]. Before declaring compatibility compare
  with the specification with a date.

## 3. A concept pinned to paths
A team agreement works only when the agent sees it **before** editing the file, not at PR review.
- The note points to the paths it concerns (`code_refs`), with a level:
  - `constraint` — an invariant to keep (e.g. a frozen API); the agent may change the file, but does not break
    the agreement;
  - `hold` — stop: before changing the file the agent asks the human.
- Before the first edit of a file in a task the agent looks for notes that cover its path: `kb.py search "<ścieżka>"`
  or `grep -rl "<katalog>" docs/knowledge`. It quotes a hit in the step plan.
- The same field on the gate side (the rule "the PR touches the area of an accepted decision") is a check after the change. One does not
  replace the other.

## 4. An instructions file or a pipeline in code
- **An instructions file with stages** (e.g. a section in `AGENTS.md` or `CLAUDE.md`) is enough for a small base (of the order of a few hundred
  documents) and at the start, while you are looking for the shape of the wiki.
- **A pipeline in code**, when the corpus is large, the result has to be repeatable or the wiki feeds further automation:
  - a page identifier as a hash of the content or a stable key (renaming a file breaks nothing);
  - type contracts between stages;
  - **a lint of the Markdown structure before writing:** one H1, a valid frontmatter, live links. Two H1s or a broken
    header silently break the next stages;
  - word search (BM25) instead of vectors for a small wiki (pack-it: ai-rag for larger corpora).
- Definitions that have to be exact and have an owner (metrics, schemas, rules) you read deterministically
  from curated files. You leave search for archives and bulk content.

## 5. Freshness of generated knowledge
A generated index, code graph or map drifts silently: the hook reports "success", and the map is weeks old
(a run skipped under load, a list of extensions out of sync with the source, a server with a cache from before regeneration).
- Every generated knowledge artifact has **a timestamp and the source commit** it was made from.
- A check in CI (or at session start) compares that commit with `git log -1` on the source paths and alarms after
  a threshold (e.g. more than N commits or a 24 h difference). The hook's exit code alone is not enough.
- For fetched sources: `kb.py status --max-age <dni>`. For notes: `stale_after` and a review by the owner.
- This also applies to the maps from pack-it: eng-codebase-mapping and every cache the agent reads.

Sources: R. Brasil Monteiro, "Building a Complete Personal Harness: LLM Wiki…" (2026-05-03); U. Estari,
"Production-Grade OKF + Graphify Setup" (2026-08-13); C. Core, "The Dev with Two Brains" (2026-10-07; the tool
`okf-agent-memory` unchecked, before use `skill_audit` and the human's consent); an article about LLM wikis "code or
an instructions file" (2026). Numbers and tool behaviour according to the authors [unverified].
