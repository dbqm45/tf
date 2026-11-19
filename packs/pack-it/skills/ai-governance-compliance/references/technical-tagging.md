# Marking AI-generated content (Art. 50(2))

Contents: 1. The obligation and the code of practice · 2. Marking layers · 3. A watermark in text · 4. Limitations ·
5. What to put in the compliance documentation

## 1. The obligation and the code of practice
- Art. 50(2) AI Act: the provider of a system generating audio, image, video or text ensures that the outputs are
  marked in a machine-readable format and detectable as artificially generated or manipulated.
  The technical solutions are to be effective, interoperable, robust and reliable as far as technically
  feasible, taking into account the specifics and limitations of the types of content, the costs of implementation and the generally acknowledged state
  of the art (as a standard may reflect it). Art. 50 applies from **2026-08-02**. (A summary of the obligation from
  the Commission's page on the code; check the literal wording in eur-lex before quoting.)
- **The Code of Practice on Transparency of AI-generated Content** (final version published 2026-06-10, prepared by independent experts with
  the participation of the AI Office). The state from the Commission's page (2026-11-01):
  - **voluntary**, but the Art. 50 obligations are legal ones; the code does not replace the AI Act or the Commission's guidelines on Art. 50;
  - it covers Art. 50(2), (4) and (5) in two sections: **1 — providers** (marking and detecting generated
    and manipulated content), **2 — deployers** (labelling deepfakes and texts published on matters of
    public interest, unless they have undergone editorial review by a human with editorial responsibility);
  - the Commission and the AI Board have assessed the code as **an adequate voluntary tool for demonstrating compliance**: a signatory
    can rely on its measures, and whoever meets the obligation in another way demonstrates the adequacy before the market
    surveillance authority themselves;
  - the EU provides icons for labelling AI content for deployers;
  - approx. 190 signatories by the end of July 2026.
- **The details of section 1 (according to commentaries, not from the text of the code)** [unverified]: at least two layers
  of machine-readable marking (secured metadata and a watermark, a fingerprint optionally) and a detection tool
  provided by the provider. Before implementation read the PDF of the code (the link on the Commission's page).
- **The Commission's guidelines on Art. 50** (the scope of the obligations): a draft published 2026-05-08 with a consultation; whether and when
  the final version was adopted, check on the Commission's page [unverified]. The deadline 2026-12-02 for systems
  placed on the market before 2026-08-02 is given only by commentaries [unverified].

## 2. Marking layers
| Layer | For what content | What survives | What removes it |
|---|---|---|---|
| **Signed metadata** (C2PA Content Credentials: a manifest with assertions, signed, bound to the file hash) | image, video, audio, documents | verifiable provenance and edit history | a screenshot, re-encoding, the platform stripping the metadata |
| **Watermark** (in the content itself) | image, audio, video; text statistically | compression, cropping (within the robustness of the algorithm) | heavy editing, paraphrasing of text |
| **Fingerprint** (comparison with the provider's database) | any | detection on the provider's side | content outside the database |

C2PA also binds metadata to the content through a "soft binding" (a watermark or a fingerprint that allows the manifest to be found after
it has been removed from the file); C2PA maintains the list of algorithms. One layer is not enough, because each one is lost in a different
way.

## 3. A watermark in text
The pattern from the paper by Kirchenbauer et al. ("A Watermark for Large Language Models", ICML 2023):
- before a token is generated, a seed from the previous token splits the vocabulary into a "green" and a "red" list,
  and the sampling slightly favours the green tokens;
- detection without access to the model and without an API key, if the rule is public (or behind an API, if it is private):
  a z-test on the number of green tokens (the expected value γT when there is no watermark);
- according to the authors the watermark is detectable from approx. **25 tokens**, and a false alarm on human text is
  statistically unlikely (at the threshold z = 4 the one-sided p ≈ 3 × 10⁻⁵);
- the watermark is strong only in text with **high entropy**. Low-entropy text (code, set phrases, text
  memorized and reproduced by the model) carries almost no watermark and can be undetectable; the authors point to this as
  the main cause of misses.

## 4. Limitations
Attacks catalogued by the authors (the section "Attacking the watermark"):
- **Inserting, deleting and substituting tokens**, including automatic **paraphrasing** with a weaker model (it weakens the watermark
  and the quality of the text) or manual paraphrasing. In long texts a few unchanged sentences are often enough for detection.
- **Minor changes** (spaces, typos) and **tokenization attacks**: the detector normalizes the text before computing
  the hash.
- **Homoglyphs and zero-width characters**: the detector canonicalizes Unicode, otherwise substituting characters removes the watermark.
- **Generative attacks** ("emoji attack": the model inserts characters after each token, which are then removed).
- **Discovering the rule from samples**: by observing pairs of tokens, an attacker can learn the lists; a small window h and a key
  kept private are recommended.

Outside this paper [unverified — secondary literature]: **watermark spoofing** (marking someone else's text as
"from the model") and **"piggyback"** (content changed by a human, also harmfully, is still detected as
generated).
- **Metadata** is lost with a screenshot and on platforms that strip it.

## 5. What to put in the compliance documentation
- Marking **supports mass detection** (platforms, moderation). It is not proof that a specific text was generated by
  a specific system, and it does not attribute authorship to an individual person.
- Describe the layers (C2PA metadata + a watermark, possibly a fingerprint), the scope of content, the detection tool and the known
  limitations. Record a robustness test against typical transformations (compression, cropping, paraphrasing) with the result.
- Whether the adopted solution meets Art. 50(2) is assessed by a lawyer on the basis of the current text of the code of practice
  and the guidelines. This file describes the technique, not an interpretation of the law.

Sources: European Commission, "Code of Practice on Transparency of AI-generated Content",
digital-strategy.ec.europa.eu/policies/code-practice-ai-generated-content (a printout of the page from 2026-11-01, provided
by a human); the details of section 1 according to commentaries by Jones Day, SCL, Freshfields (2026-06); Regulation (EU) 2024/1689,
Art. 50 (the text in eur-lex not checked in this session); J. Kirchenbauer et al., "A Watermark for Large Language Models",
arXiv 2301.10226v4 (ICML 2023; the PDF provided by a human, read: the introduction, the sections on entropy and attacks);
github.com/c2pa-org/specifications (documentation version 2.5, commit 2026-10-28; soft binding, `softbinding-alg-list`).
