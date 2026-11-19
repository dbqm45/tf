# Parsing, evaluation in buckets and canonical knowledge

Contents: 1. Checking parsing before indexing · 2. Evaluation in two buckets and the similarity threshold ·
3. A canonical wiki or RAG · 4. The freshness of generated knowledge artifacts

## 1. Checking parsing before indexing
Wrong text from the parser spoils every further step, and tuning the retriever on bad text is a waste of time. The order:
1. **Per-page alarms:** a page without a text layer or with a suspiciously small number of characters compared with the neighbouring ones
   is an alarm (a scan without OCR, text as an image), not an empty document. You compute this automatically for the whole corpus.
2. **A review of the raw output on the worst documents:** a scan, a table across two pages, a two-column layout,
   footnotes, headers repeated on pages. You read the parser result before anyone changes the embedding model.
3. **Measures in the evaluation set:** table structure (e.g. TEDS — the similarity of the table tree to the reference) and the reading
   order (whether paragraphs from two columns are not interleaved) on a dozen or so manually annotated pages.
4. **A layout-aware parser** (open source or a service) you choose by criteria: tables and merged cells, reading
   order, OCR and languages (Polish characters), formulas and footnotes, cost per page, local processing or at the provider
   (sensitive data), stability of the result between versions. A test on your worst documents decides, not a ranking.

## 2. Evaluation in two buckets and the similarity threshold
- Every question in the set has a **query type**: *semantic* (paraphrases, intents) or *exact*
  (identifiers, codes, contract numbers, versions, numbers, negations). You compute recall@k separately for each bucket.
  An average of 0.82 can hide 0.95 for paraphrases and 0.4 for numbers. The exact bucket is rescued by BM25 and the hybrid (SKILL.md step 5).
- **Questions combining two facts** (from two documents or fragments) are a third category: a single query
  vector has a theoretical limit on how many different combinations of documents it can point to (Weller et al., "On the
  Theoretical Limitations of Embedding-Based Retrieval", 2025 [unverified]). Decomposing the question or
  several queries helps.
- **You set the similarity threshold from the distribution, not "by eye".** First a cosine histogram for a few hundred random,
  unrelated pairs from your own corpus: the embedding space is sometimes anisotropic and random pairs lie at 0.8–0.9.
  A threshold below that distribution cuts nothing off. It is better to cut off after the rerank or at a fixed top-k and measure "I don't know".

## 3. A canonical wiki or RAG
| Content | Where | Why |
|---|---|---|
| definitions that must be exact and have an owner (metrics, table schemas, business rules) | curated files (Markdown with frontmatter: `type`, owner, verification date, links to related ones) read deterministically, starting from the index | one definition, versioned, with a review; RAG will return three contradictory versions from different pages |
| archives, mass content, documents without an owner | RAG | too much to curate |
| data from systems (order status, numbers) | a tool with a query | vectors do not compute |

The router chooses the path before the search: a question about a definition → the canonical file, the rest → RAG. An example open
format: Open Knowledge Format (github.com/GoogleCloudPlatform/knowledge-catalog, the SPEC file in the okf directory, version 0.2,
read 2026-10-29): only the `type` field is required; an index file as a table of contents for progressive disclosure; plain Markdown links.

If an agent maintains the wiki, three zones with different write rights:
- sources — read only;
- pages maintained by the agent, with a `sources` field and updating instead of rewriting;
- the team's notes and decisions — changed only with a human's approval.

Loading new sources first shows a plan (new and changed pages), and only then writes. The
"verified" field is filled in by a human, the agent only "generated".

## 4. The freshness of generated knowledge artifacts
A generated index, code graph or map drifts silently: the hook reports success, and the map is weeks old. Every such
artifact has a timestamp and the source commit; a check in CI compares it with `git log -1` and alarms after a threshold (e.g. 24 h).
The `stale_after` and `verified` fields (OKF) or your own equivalents carry this information to the agent that reads the artifact.

Sources: P. Perrone, "Why Your RAG Pipeline Dies on Real Documents" (2026-10-01, a sponsored article — without
a provider recommendation); J. Wąsowski, "The Limits of Vector Search in RAG" (2026-09-14, numbers [unverified]);
Dev Evolution, "Beyond RAG: … Open Knowledge Format" (2026-09-09); R. Brasil Monteiro, "Building a Complete Personal
Harness: LLM Wiki…" (2026-05-03); U. Estari, "Production-Grade OKF + Graphify Setup" (2026-08-13).
