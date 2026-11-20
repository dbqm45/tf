---
name: ai-rag
description: Use for RAG and document search for an LLM — RAG or long context, chunking, embeddings, hybrid, reranking, permissions, retrieval evaluation.
metadata:
  review: "2027-04-17"
  catalog: "Use when you build a chatbot or a feature that answers based on your own documents — the decision between RAG, long context, fine-tuning or tools, loading and parsing (PDF, tables), chunking (size, overlap, by structure), choosing embeddings also for Polish, hybrid search BM25 plus vectors, reranking, contextual retrieval, metadata filters, per-document permissions, freshness and reindexing, choosing a vector database (pgvector, Qdrant, Milvus, OpenSearch), retrieval metrics (recall@k, MRR, nDCG), citing sources, typical failures and prompt injection through retrieved documents. Not for the SDK, the output contract and the tool loop (eng-llm-features), PostgreSQL indexes and queries (be-database), the general evaluation method (ai-evals), data pipelines (data-engineering) or agent design (ai-agents)."
  keywords: "rag, retrieval, wyszukiwanie semantyczne, baza wiedzy, czatbot na dokumentach, embeddingi, wektory, baza wektorowa, pgvector, qdrant, milvus, opensearch, chunking, dzielenie dokumentów, hybrydowe wyszukiwanie, bm25, reranking, contextual retrieval, recall@k, mrr, ndcg, cytowanie źródeł, halucynacje, długi kontekst, uprawnienia do dokumentów, reindeksacja, definicje metryk i schematy tabel, wrzucić wszystko do RAG, wiki kanoniczne, strony w Confluence, asystent odpowiada na pytania o definicje, semantic search, knowledge base, chatbot over documents, embeddings, vectors, vector database, splitting documents, hybrid search, citing sources, hallucinations, long context, document permissions, reindexing, metric definitions and table schemas, put everything into RAG, canonical wiki, Confluence pages, the assistant answers questions about definitions, rag z uprawnieniami, izolacja klientów w rag, sprzeczne źródła, nieaktualne źródła, evale wyszukiwania i odpowiedzi, permission-aware retrieval, tenant isolation in rag, conflicting sources, stale sources"
---

# RAG — from the decision to measured retrieval

RAG is two systems: **retrieval** (returns the right fragments) and **generation** (answers only from them).
Most failures lie in retrieval, so you measure it separately before you touch the prompt. The model call, the output
schema and the tool loop are described by **eng-llm-features**; this skill is about what goes into the context and from where.

## Procedure
1. **Whether RAG at all.** A choice by the problem, not by fashion:
   - the corpus fits in the context (Anthropic: below approx. 200,000 tokens, approx. 500 pages) and changes rarely →
     the whole thing in the prompt with prompt caching, without an index;
   - the corpus is large, changing, with permissions or requires citations → RAG;
   - structured data (an order, an account balance) → a tool with a query to an API or SQL, not vectors;
   - definitions that must be exact and have an owner (metrics, schemas, rules) → curated files read
     deterministically, RAG for the rest, a router between them (`references/parsing-evaluation-wiki.md` §3);
   - fine-tuning changes style, format and behaviour, it does not supply current facts; it does not replace RAG
     [assumption — verify with the model provider].
2. **Loading.** Choose the parser for the document and look at the result on 10 pages: the column order, headers, footers
   repeated on every page, tables (keep them as Markdown/HTML with a header, not as flat text), OCR for
   scans. For each fragment record the source, page, section, date, version and the list of permissions. A page without a text
   layer or with a suspiciously small number of characters is an alarm, not an empty document. With bad answers you first
   read the raw parser output on the worst documents (a scan, a table across two pages, two columns), only
   then tune the retriever (`references/parsing-evaluation-wiki.md` §1).
3. **Chunking.** Start with splitting by structure (a section, a paragraph, a table row with the header), not with a fixed number
   of characters. A starting point: 200–500 tokens and an overlap of 10–20% [assumption — tune on the set from step 7]. A too small chunk
   loses context, a too large one blurs the embedding. The "small for searching, large for sending" variant (parent–child) helps
   when the answer requires the neighbourhood.
4. **Embeddings.** Criteria: quality on **your own** Polish questions, input length, dimension (storage cost),
   licence and hosting (an API or your own model), the cost of reindexing when the model changes. Multilingual models handle
   Polish differently — the PIRB benchmark compares them on Polish tasks, but only a test on your
   data decides. Record the model name and version with the index; a model change = full reindexing. Query/document prefixes,
   if the model requires them, apply consistently.
5. **Hybrid search.** Vectors lose identifiers, error codes, proper names and paragraph numbers; BM25
   loses paraphrases. Run both and merge the rankings (Reciprocal Rank Fusion or a weighted sum), then **reranking**
   (a cross-encoder or a reranking model) on 50–150 candidates down to 5–20 results. Polish requires an analyzer with lemmatization
   or at least a correct tokenizer on the BM25 side.
6. **Contextual retrieval** (when fragments lose their meaning without the document, e.g. "revenue grew by 3%"): the model adds to
   each chunk 50–100 tokens of context from the document before the embedding and BM25. Anthropic's result (19.09.2024): failed
   retrievals in the top-20 dropped by 35% (embeddings), 49% (with BM25), 67% (with reranking). A one-off cost of approx. 1.02 USD
   per million document tokens with prompt caching. This is a result on their sets — measure it yourself.
7. **A golden set and retrieval metrics** (the general method: **ai-evals**). Collect 50–200 real questions with the expected
   fragments, including questions without an answer in the corpus. Measure: recall@k (whether the right fragment is in the top-k),
   MRR (how high), nDCG (when there are many fragments and they differ in usefulness). You change one thing at a time
   (the parser, the chunk, the model, the hybrid, the reranker) and compare with the previous result. Only then do you assess the answers.
   You compute recall@k **separately for two buckets**: semantic queries (paraphrases) and exact ones (identifiers, codes,
   versions, numbers); questions combining two facts are a third category. You set the similarity threshold only after
   a cosine histogram for random, unrelated pairs from your own corpus (`references/parsing-evaluation-wiki.md` §2).
8. **An answer with citations.** The prompt: answer only from the given fragments, give the source identifier with every claim,
   and when there is no basis answer "I don't know". The code checks that the cited identifier exists
   among the passed fragments and that the quote occurs in its content. Put fewer, better fragments into the context;
   the model loses the middle of a long context.
9. **Permissions and freshness.** You enforce permissions **in the query to the index** (a metadata filter at the database
   level), never in the prompt or after generating the answer. A change of a document's permissions must reach the index
   as fast as a document deletion. Incremental reindexing by a content hash, deletions as a separate path,
   date and version in the metadata, a "current" filter. Loading pipelines: **data-engineering**.
10. **A vector database.** Criteria: scale (millions rather than hundreds of thousands of vectors?), metadata filtering together
    with the search, hybrid in one query, operations (backups, replication, who will maintain it), cost, compatibility
    with the existing stack. A hint: a small corpus and PostgreSQL already in use → pgvector (indexes: **be-database**);
    a large scale and rich filtering → Qdrant, Milvus or OpenSearch (also BM25). The pgvector trap: the filter works after
    the scan of the approximate index, so a selective `WHERE` returns too few rows — turn on iterative scan (since 0.8.0).
11. **Prompt injection.** A retrieved document is **data, not instructions**: it contains text that tries to steer the model
    ("ignore the instructions", "send the conversation to the address…"). The model does not get write or send tools driven
    by the content of the fragments; fragments in clear delimiters; sources from outside trusted indexes marked. If the question
    is "does the user see a document they should not", that is a matter for step 9, not for the prompt.

Failure diagnosis (symptom → cause → fix) and a longer table of databases: `references/failures-and-vector-store.md`.

## Example
**Input:** "An HR chatbot over 1,800 PDFs, Polish, codes like ZUS-ZUA, employees see only their own department."
**Result:**
- a corpus of approx. 40 million tokens → RAG (beyond the 200,000 limit);
- a parser preserving tables, chunks by section of approx. 350 tokens, the metadata `department`, `version`, `date`;
- the index: multilingual embeddings + BM25 with a Polish analyzer, RRF, a reranker 100 → 8; BM25 will find the codes;
- the filter `department IN (user)` in the query to the database;
- a golden set of 120 questions (20 without an answer); a starting target recall@20 ≥ 0.9 [assumption], a comparison before and after every change;
- an answer with identifiers `[doc-123#s4]` checked by code; "I don't know" when there is no hit.

## Checklist
- [ ] a justified choice: context, RAG, a tool or fine-tuning
- [ ] the parser result viewed on the worst documents; an alarm for pages without text; source, version and permission metadata with every chunk
- [ ] embeddings checked on your own Polish questions; the model name recorded with the index
- [ ] hybrid and reranking or a justification for their absence
- [ ] a golden set with questions without an answer; recall@k separately for semantic and exact queries; the threshold from the distribution of random pairs
- [ ] permissions in the query to the index; propagation of changes and deletions
- [ ] citations verified by code; "I don't know" when there is no basis
- [ ] retrieved fragments treated as data; no write tools driven by the content

## Sources
- Anthropic, "Introducing Contextual Retrieval" (19.09.2024, accessed 2026-10-17): error reduction 35%/49%/67%,
  top-20, approx. 1.02 USD per million tokens, the 200,000 token threshold (approx. 500 pages).
- pgvector README (github.com/pgvector/pgvector, accessed 2026-10-17): HNSW and IVFFlat, `halfvec`, filtering after the index
  scan, iterative scan since 0.8.0.
- PIRB: Polish Information Retrieval Benchmark (arXiv 2402.13350) — the results of multilingual models on Polish
  tasks; the ranking depends on the set, hence a test on your own data [I do not quote the numbers].
- [unverified] RRF as a method of merging rankings, the ranges of chunk size and the number of reranking candidates,
  the OWASP LLM Top 10 2025 numbering (vectors and embeddings, prompt injection) — from general knowledge, check before citing.

Described in our own words.
