# RAG failures and choosing a vector database

## Contents
- Symptom → cause → fix
- Vector database: criteria and candidates
- Diagnosis order

## Symptom → cause → fix
| Symptom | Most common cause | Fix |
|---|---|---|
| the right fragment is not in the top-k | a chunk without context; a weak model; no BM25 | contextual retrieval, hybrid, testing models on the golden set |
| the fragment is in the top-50, but not in the top-5 | no reranking | a reranker on 50–150 candidates |
| the answer ignores a good fragment | too much noise in the context; the fragment in the middle | fewer fragments, a better order, enforced citations |
| an untrue answer, no source | the prompt allows general knowledge | "only from the fragments", "I don't know", quote verification |
| stale data in the answer | no reindexing, no version | a content hash, the date in the metadata, a freshness filter |
| a broken table, numbers without headers | the parser flattens tables | a structural parser, the row with the header in the chunk |
| the same fragment 5 times | duplicate versions, overlap | deduplication by hash, one version in the index |
| codes and numbers not found | vectors only | BM25 in a hybrid |
| a selective filter returns few results (pgvector) | the filter after the index scan | iterative scan, partitions, or a database with the filter in the index |
| a user sees someone else's fragment | the permission filter after retrieval or in the prompt | the filter in the query to the index, a test with an account without permissions |
| the answer executes an instruction from a document | the fragment treated as an instruction | data, not instructions; no tools driven by the content |

## Vector database: criteria and candidates
Criteria in order of importance: (1) scale and p95 latency with filters, (2) metadata filtering in the same
query, (3) hybrid (BM25 plus vectors) without gluing two systems together, (4) operations and maintenance, (5) cost,
(6) integration with the stack you have. Record the result of the comparison as a criteria matrix (arch-tech-selection).

| Candidate | When | Note |
|---|---|---|
| pgvector | PostgreSQL is already there, a corpus of up to a few million vectors, transactions with the data | an HNSW or IVFFlat index; the filter after the approximate scan; indexes and plan: be-database |
| Qdrant | filtering by metadata, medium and large scale | a separate service to maintain [unverified — check the current hybrid features] |
| Milvus | very large scale, many index types | the most elements to maintain [unverified] |
| OpenSearch | BM25 and vectors in one engine, already used for logs or search | a good lexical hybrid, Polish analyzers [unverified] |

Do not choose by rankings from the internet: load your own 100 thousand fragments, run the golden set and measure
recall@k, latency and cost.

## Diagnosis order
1. Does the right fragment exist in the index at all (the parser, ingestion)?
2. Is it in the top-50 (the embedding, BM25, the chunk)? 3. Is it in the top-5 (reranking)? 4. Does the answer use it (the prompt,
the context)? You fix the first stage that fails.
