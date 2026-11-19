---
name: ai-nlp
description: Use for NLP tasks on text, including Polish — choice of approach, classification, NER, span-level evaluation, annotation, PII and anonymization.
metadata:
  review: "2027-04-17"
  catalog: "Use when you need to solve a task on text and choose a method — rules and regex, classic ML, a small encoder model, an LLM zero/few-shot or a fine-tuned model (cost, latency, data, accuracy), text classification, NER and information extraction, span-level evaluation (precision, recall, F1 micro and macro), normalization and tokenization, embeddings and semantic similarity, topic and intent detection, the limitations of summary evaluation, annotation design (guidelines, inter-annotator agreement, active learning), imbalanced classes, Polish (inflection, lemmatization, Morfeusz, spaCy, HerBERT, KLEJ, diacritics) and detecting personal data and anonymization in text (PESEL, first names, addresses). Not for RAG and chunking (ai-rag), writing prompts (ai-prompt-engineering), fine-tuning a model (ai-fine-tuning), the general LLM evaluation method (ai-evals), the spelling of Polish text for people (txt-polish-correctness), statistics and a data report (data-analysis) or the legal bases of the GDPR (arch-privacy-compliance)."
  keywords: "nlp, przetwarzanie języka naturalnego, klasyfikacja tekstu, klasyfikacja maili, ner, rozpoznawanie encji, ekstrakcja informacji, f1, precision, recall, micro, macro, tokenizacja, lematyzacja, fleksja, polski model językowy, herbert, klej, morfeusz, spacy, diakrytyki, embeddingi, podobieństwo zdań, intencja, temat, streszczenia, adnotacja, wytyczne adnotacji, kappa, active learning, niezbalansowane klasy, anonimizacja, pii, pesel, dane osobowe w tekście, presidio, regex czy llm, natural language processing, text classification, email classification, entity recognition, information extraction, tokenization, lemmatization, inflection, polish language model, diacritics, embeddings, sentence similarity, intent, topic, summaries, annotation, annotation guidelines, imbalanced classes, anonymization, personal data in text, regex or llm"
---

# NLP — choosing a method and evaluating on text

NLP rarely starts with a model. It starts with the task, the data and the measure of success. You write a prompt for an LLM per
**ai-prompt-engineering**, you design retrieval for an LLM per **ai-rag**, you run fine-tuning per **ai-fine-tuning**,
and the method of evaluating LLM features is described by **ai-evals**. This skill chooses the approach and measures it on text.

## Procedure
1. **Task and measure.** Name the type: classification (single label, multi-label), NER/extraction (spans), similarity
   or search, generation (summary). Record: daily volume, acceptable latency, the cost of an error
   (what hurts more: a miss or a false alarm), the language and domain, the number of labels. Without this you will not choose a method.
2. **The cheapest approach that passes the threshold** (a ladder; move up after a failure, not up front):
   - rules, dictionaries, regex — when the pattern is closed (codes, numbers, dates, formats); zero data, full
     predictability;
   - classic ML (TF-IDF + logistic regression or SVM) — **always as a reference point**; often enough with
     hundreds of labels;
   - a small fine-tuned encoder model (BERT-like, for Polish e.g. HerBERT) — when latency and cost
     at a large volume count and there are ≥ about 1,000 labels [assumption — check the learning curve];
   - an LLM zero/few-shot — when there are few labels, the categories change, the task requires understanding; you pay for every
     call and for latency; measure it on the same set as the rest;
   - a fine-tuned model (ai-fine-tuning) — when an LLM is too expensive or too slow, and the data exists.
   A cascade often works: rules → a small model → an LLM only for uncertain cases.
3. **Data and split.** The test set is frozen before the work, from the production distribution, not from hand-picked
   examples. For texts from the same source (customer, thread, document) split **by source**, not randomly, because
   otherwise duplicates leak and the result is inflated.
4. **Text before the model.** Decide the normalization once and apply it the same way in training and in production: Unicode NFC,
   whitespace, letter case only if the model does not carry it, replacing URLs/numbers with tokens — only when they carry no
   signal. Do not remove stop words for contextual models. The tokenizer must match the model; do not count "words"
   by spaces with inflection. Specifics of Polish: `references/polish-pii-and-annotation.md`.
5. **Measures.**
   - Classification: precision, recall, F1 **per class** and macro-F1 (classes weighted equally) and micro-F1 (examples weighted equally);
     with imbalance, macro and the recall of the rare class, not accuracy alone. Read the confusion matrix by hand.
   - NER/extraction: **span-level evaluation** (an entity is hit when the type and the boundaries match), e.g. `seqeval`;
     accuracy on tokens is useless, because the `O` label dominates. Give the strict and the lenient (overlap) mode.
     Micro-F1 over all entities and macro over types; a report per type.
   - Similarity and search: recall@k, MRR, nDCG (as in **ai-rag**); choose the similarity threshold on the dataset,
     not from an example in the documentation.
   - Summaries and generation: ROUGE and similar measures measure word overlap, not faithfulness or coherence; use
     human evaluation or an LLM judge calibrated to humans (ai-evals) and check the facts separately (hallucinations).
6. **Imbalanced classes.** First class weights or choosing the decision threshold from the precision–recall curve,
   then collecting labels of the rare class (active learning), oversampling last. Leave the test set in the production
   distribution; after changing the threshold, recompute the measures.
7. **Annotation, when labels are missing.** Guidelines with a definition of each class, borderline examples and rules
   for resolving; a pilot of 100–200 examples for ≥ 2 annotators; agreement: Cohen's kappa (2 people) or Krippendorff's
   alpha (more), for spans also F1 between annotators. Low agreement = unclear guidelines, not the model's fault;
   inter-annotator agreement is also the upper limit of a meaningful result. Active learning (uncertainty sampling) directs
   labelling to the examples the model is uncertain about; do not feed the test set with it.
8. **Personal data in text.** Rules with validation (e.g. the PESEL checksum) + an NER model for first names, surnames,
   addresses; measure **recall** on your own labelled set, because a miss is a leak. Anonymization (irreversible)
   versus pseudonymization (a stable token per person); the inflection of Polish surnames makes counting harder — details in the reference
   file. Legal bases and minimization: **arch-privacy-compliance**.
9. **Result: an NLP solution design** in a fixed layout: the task and the measure of success; the chosen approach with a justification
   from the ladder; data (source, number of labels, split); an evaluation plan (set, measures, acceptance threshold); risks
   (imbalance, drift, PII); the next step if the threshold is not passed.

Polish, tools, benchmarks, PII and annotation in detail: `references/polish-pii-and-annotation.md`.

## Example
**Input:** "40,000 emails a day in Polish, 6 departments, 800 labelled, the rare department "Debt collection" (*Windykacja*) is 3% of emails."
**Result:**
- measure: macro-F1 and the recall of "Debt collection" ≥ 0.85 [assumption — agree the threshold with the business], because a miss costs the most;
- reference point: TF-IDF + logistic regression with class weights (an hour of work, zero call cost);
- if macro-F1 is below the threshold: a fine-tuned HerBERT; measure the learning curve (400/800 labels) to know whether
  adding labels will help; an LLM few-shot on the same test as a cost comparison (40,000 × the price of a call);
- split by sender, not random; a test of 300 emails in the production distribution;
- active learning: 200 emails with the lowest model confidence for labelling, kappa on a pilot of 100 emails ≥ 0.7 [assumption];
- cascade: rules (headers, keywords) → model → LLM for emails with confidence below the threshold.

## Checklist
- [ ] task, volume, latency and cost of an error recorded; measure of success chosen before the model
- [ ] a classic reference point (rules or TF-IDF); a higher rung of the ladder justified by the result
- [ ] test set frozen, from the production distribution, split by source
- [ ] classification: measures per class and macro and micro; NER: span measures, not accuracy on tokens
- [ ] imbalance handled (weights, threshold), test set untouched
- [ ] annotation: guidelines, inter-annotator agreement, a pilot before full labelling
- [ ] Polish: NFC normalization, lemmatization or tokenization matched to inflection, the model checked on your own data
- [ ] PII: recall measured on your own set; anonymization or pseudonymization decided
- [ ] facts about models and tools (versions, licences) checked in a source with a date

## Sources
- Rybak et al., "KLEJ: Comprehensive Benchmark for Polish Language Understanding" (ACL 2020, arXiv 2005.00630,
  accessed 2026-10-17): the KLEJ benchmark with a leaderboard; HerBERT introduced in this paper.
- Augustyniak et al., "This is the way: designing and compiling LEPISZCZE" (NeurIPS 2022 Datasets and Benchmarks,
  accessed 2026-10-17): 13 task–dataset pairs for Polish, including five from KLEJ.
- seqeval (pypi.org/project/seqeval, accessed 2026-10-17): NER span evaluation modelled on `conlleval`; scikit-learn
  `f1_score`, the `average` parameter (micro, macro, weighted), accessed 2026-10-17.
- [unverified] numerical thresholds (≥ 1,000 labels, kappa ≥ 0.7, recall ≥ 0.85) — practical rules, not results
  from the literature; adjust them to your own cost of an error.

Described in our own words.
