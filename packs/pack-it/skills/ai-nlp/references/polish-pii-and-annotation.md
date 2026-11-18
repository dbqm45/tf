# Polish, PII and annotation — details

Contents: Polish in NLP · tools and models · benchmarks · PII and anonymization · annotation

## Polish in NLP
- **Inflection.** One word has many forms ("umowa, umowy, umowie, umową" — forms of "contract"). Models based on word counts (TF-IDF, BM25,
  dictionaries) need lemmatization or character n-grams; subword models cope better, but rare forms
  break into many tokens, which shortens the effective context.
- **Lemmatization of proper names fails.** An analyser may reduce the surname "Kowalskiego" to "Kowalski", but
  unknown surnames and company names ("Żabki") are often lemmatized wrongly. Base counting per person on an identifier
  or a key from identity resolution, not on the form from the text alone.
- **Diacritics.** Users write without Polish characters ("zazolc gesla jazn"). Normalizing to ASCII loses
  distinctions (e.g. "łąka" and "laka"), so do not convert the text to ASCII in training. Instead, add to the test
  set a share of entries without diacritics, if there is such traffic, and measure the drop. Always apply Unicode normalization (NFC),
  because the same character can have two representations.
- **Free word order and dropped subjects.** Rules based on word position break more often than in English.
- **Letter case.** A capital letter in the middle of a sentence indicates a proper name; do not lowercase before NER.

## Tools and models (as of 2026-10-17)
- **Morfeusz 2** — a dictionary-based morphological analyser and generator for Polish, the SGJP and Polimorf dictionaries; licence
  BSD 2-clause (Woliński, LREC 2014; CLARIN-PL repository). There is a wrapper for Python; the wrapper's licence may differ,
  check it before redistribution. The current version and project maintenance: [unverified].
- **spaCy, the `pl_core_news_*` pipelines** — tokenization, morphology, lemmatizer, parser, NER. The model card of
  `pl_core_news_lg` (Hugging Face, accessed 2026-10-17): version 3.7.0 for spaCy ≥ 3.7.0 and < 3.8.0, lemma accuracy
  about 94.2%, NER F-score about 84.1%, data: UD Polish PDB, NKJP. The model licence on the card: GPL-3.0 — check
  compatibility with your own product. The results concern general text; on specialist texts (e.g. medical ones)
  they can be much worse, so measure on your own data.
- **HerBERT** — a BERT-type model for Polish, trained on Polish corpora, introduced together with KLEJ (Allegro
  ML Research, ACL 2020). Availability of current variants and licences: [unverified], check on Hugging Face.
- **Polish generative models (e.g. Bielik, PLLuM)** — status, licences and results [unverified]; choose
  through your own test, not through a leaderboard.
- Embeddings and search for Polish: the PIRB benchmark and the criteria in **ai-rag**; apply the same principles here
  (your own questions, the model name recorded).

## Benchmarks
- **KLEJ** (2020): nine language understanding tasks, including NER-like, inference, sentiment (Allegro Reviews).
- **LEPISZCZE** (NeurIPS 2022): 13 task–dataset pairs, five from KLEJ, eight new; designed to be extensible.
- A public leaderboard says which model is good **on average**; the choice is decided by a test set from your domain.
  I do not quote specific results here [unverified].

## PII and anonymization in text
1. **Inventory of types:** first name and surname, PESEL (national ID number), NIP (tax ID), REGON (business register number), ID card number, phone, e-mail, address, IBAN, licence
   plate, data in free text ("my neighbour from Lipowa 5").
2. **Layers:** regex with validation where there is structure; NER for first names, surnames, addresses; dictionaries for
   context. The PESEL checksum: weights 1-3-7-9-1-3-7-9-1-3 for ten digits, check digit = (10 − sum mod 10)
   mod 10; validation rejects random 11-digit numbers and raises precision. NIP has its own checksum [assumption —
   check in the regulations].
3. **Presidio** (Microsoft, open source): an English configuration by default; Polish requires swapping the NLP engine
   (spaCy or Stanza) and the recognizers, and a list of context words per language; your own recognizers are the class
   `PatternsRecognizer` or a subclass of the base class (Presidio documentation, accessed 2026-10-17). Whether there is a ready PESEL
   recognizer in the current version: [unverified] — check in the code.
4. **Measure:** a gold set with labelled PII (≥ 200 documents in the domain); report **recall per type** (a miss
   is a leak) and precision (an excess spoils the usefulness of the text). Errors in the boundary characters also count as
   a partial leak.
5. **Anonymization vs pseudonymization:** replacing with `[PERSON]` is irreversible; a stable token (`PERSON_17`) keeps
   consistency within a document and allows counting, but requires resolving coreference and inflection ("Kowalskiemu" =
   "Kowalski"); keep the token ↔ person mapping separately and protect it. Pseudonymization is still processing of personal
   data — the legal assessment: **arch-privacy-compliance**.
6. **Before sending to an external LLM**, perform the anonymization locally and check on a sample that nothing leaks.

## Annotation
- **Guidelines:** a definition of the class, 3–5 typical and borderline examples, resolution rules ("when two classes
  fit, choose…"), span boundaries (does "Pan" (Mr) belong to the surname?). Version the guidelines; a change = a note on its impact
  on the data already labelled.
- **Pilot:** 100–200 examples, ≥ 2 annotators independently. Measures: Cohen's kappa (2 people), Krippendorff's alpha
  (more people, missing values), for spans the F1 of one annotator against the other. Discuss the disagreements and add them to the guidelines.
- **Gold set:** part is labelled by two annotators with adjudication; the rest by one person with a sample check.
- **Active learning:** uncertainty sampling (the lowest confidence) or diversity; after each round recompute the measures on
  a fixed test set that takes no part in selecting the examples.
- **An LLM as the annotator's aid:** a label suggestion speeds up the work, but risks anchoring; check a sample
  labelled without suggestions.
