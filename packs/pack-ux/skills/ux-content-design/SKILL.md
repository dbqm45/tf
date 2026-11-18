---
name: ux-content-design
description: Use for in-product content as design — voice and tone, style guide, plain language, microcopy, content models, localization, content tests.
metadata:
  review: "2027-10-17"
  catalog: "Use when product content needs to be designed, not just written — voice and tone, a content style guide, plain language (including the Polish „prosty język”), microcopy patterns (errors, empty states, confirmations, buttons, onboarding, notifications), content models and patterns, content-first design (real content before the layout), the localization process and string management, content tests (cloze, highlighter, comprehension tasks), accessible content, texts of AI features (AI labelling, uncertainty, limitations). Not for basic UI texts in a screen specification (ux-feature-design), Polish proofreading and editing (txt-polish-correctness, txt-polish-style), technical documentation (docs-tech-writing) or the i18n mechanics in code alone (eng-i18n, fe-web-platform)."
  keywords: "UX writing, content design, mikrotekst, microcopy, komunikat błędu, pusty stan, tekst przycisku, głos marki, ton komunikacji, przewodnik stylu, content style guide, prosty język, zrozumiały tekst, czy użytkownicy rozumieją, test cloze, lokalizacja, tłumaczenie aplikacji, klucze tłumaczeń, treść przed makietą, lorem ipsum, model treści, asystent AI teksty, teksty asystenta LLM, asystent w aplikacji, użytkownik wie, że rozmawia z AI, nie ufać ślepo odpowiedziom AI, oznaczenie AI, czy klienci rozumieją tekst, zrozumiałość treści, test zrozumienia tekstu, regulamin prostym językiem, nowa treść, error message, empty state, button text, brand voice, tone of voice, style guide, plain language, understandable text, do users understand, localization, app translation, translation keys, content before the wireframe, content model, AI assistant texts, user knows they talk to AI, AI labelling, text comprehension test, terms in plain language"
---

# Product content design

Content is part of the interface, not decoration. You start from the user's task and the real words that help do it,
not from an empty wireframe. The basic rules of UI texts (a verb on the button, an error: what happened and what to do, an empty
state) are in **ux-feature-design** (`.claude/skills/ux-feature-design/references/content-and-ethics.md`) — here you develop them into a system and test them on people.

## Procedure
1. **Task and reader.** Who, in what situation (hurry, stress, a phone on the move), what they want to do, what they already know.
   No research → ask or mark it [assumption]. Research methods — ux-research-methods.
2. **Content before the layout.** Write real texts for the longest, the shortest and the typical case, and only
   then lay out the screen. Instead of "lorem ipsum" — production data (anonymized). For sites with many page
   types build a **content model**: types (e.g. a help article), fields (title ≤ 60 characters, lead, steps, warning),
   rules (required/optional), relations. One type = one pattern, so authors do not invent the layout every time.
3. **Voice and tone.** The voice is constant (3–4 traits, each with an "is / is not" pair: "matter-of-fact, not stiff"), the tone changes
   with the user's situation (a payment error ≠ a success). Choose one form of address (informal / formal / impersonal)
   and keep it across the product. The full procedure and a template: `references/style-guide-and-microcopy.md`.
4. **Plain language.** Sentences on average up to about 15–20 words, active voice, one concept = one name, the important things first,
   concrete numbers and terms, no nominalizations ("perform a verification" → "check"). For official
   and legal content add a plain-language version next to the original. This is not simplifying the content, but removing
   obstacles. Polish editing — txt-polish-style, correctness — txt-polish-correctness.
5. **Microcopy by pattern.** For every state from the state table (ux-feature-design): error (what happened → why → what to do,
   at the field), empty state (why it is empty → the first step), confirmation (the effect → a verb on the button), onboarding
   (one thing per screen, value before the feature), notification (why now → what we expect → how to turn it off).
   Patterns with examples and anti-patterns: `references/style-guide-and-microcopy.md`.
6. **Accessible content.** Link text makes sense without context ("Download invoice 03/2026", not "Click here"), headings
   describe the section, a message does not rely on color or an icon alone, text alternatives say the function, abbreviations
   expanded on first use, the language of the page and of foreign fragments marked. Accessibility audit — ux-accessibility.
7. **AI features.** Say plainly that AI is answering (from 2 August 2026 a requirement of AI Act Art. 50(1), when the user
   could take the system for a human), what it can and cannot do, where it gets its answers, that it can be wrong and what to check
   (confidence expressed in words and a source, not false precision "97%"). Give a way out: correcting, contact with a human,
   reporting a wrong answer. Details: `references/ai-content-and-localization.md`.
8. **Localization.** Keep texts in keys with a description for the translator (where it is visible, character limit, variables), without gluing
   sentences from fragments; plural and gender through ICU MessageFormat (the mechanics — fe-web-platform, `i18n.md`). A reserve for
   length (German, Polish longer than English), a glossary, a review in the context of the screen. Process:
   `references/ai-content-and-localization.md`.
9. **Content test** before release, matched to the question:
   - **cloze** — cut out every 5th–6th word, the participant fills in the gaps; a result of about 60% or more means an understandable text for this group;
   - **highlighter** — participants mark in green what is clear and builds trust, and in red what is unclear or
     worrying; you count which fragments got red from many people;
   - **comprehension task** — "What will happen after the click?", "How much will you pay?", an answer in their own words.
   5–8 people per group are enough to find the main problems. Readability indexes (e.g. Flesch) are at most a signal.
   Details: `references/content-testing.md`.
10. **Result.** A style guide (or an update), texts with keys and descriptions, a list of word decisions, test results
    with fixes. Further iterations: a text change is a code change, it goes through review like a PR.

## Example
Input: "Invoicing app: the message »Error 422. Invalid data.« after saving an invoice with an empty tax ID."

Result:
- Tax ID field: "Enter the buyer's tax ID — 10 digits, no dashes." (what to do, at the field, no code)
- Summary above the form: "The invoice was not saved. Fix 2 fields: Tax ID, Sale date." — links to the fields.
- Code 422 only in the details for support ("Code: INV-422").
- Test: a highlighter with 6 people; 4 marked "buyer" in red → replaced with "customer", in line with the product
  glossary. The name "customer" recorded in the style guide and in the translation glossary.

## Checklist
- [ ] task and reader named; texts written on real data, also the extreme cases
- [ ] voice (3–4 traits), tone by situation, one form of address, a glossary of concepts
- [ ] microcopy by pattern for every state; error codes only as an identifier for support
- [ ] plain language; legal and official content with a plain-language version
- [ ] accessible content (links, headings, alternatives, not only color)
- [ ] AI features: labelling, limitations, uncertainty, a way out to a human
- [ ] keys and descriptions for translators, ICU, a length reserve; a review in context
- [ ] a content test (cloze, highlighter or task) or an explicit "not tested"

## Additional materials
- `references/style-guide-and-microcopy.md` — a style guide template, voice and tone, microcopy patterns; read when writing texts.
- `references/content-testing.md` — how cloze, highlighter and comprehension tasks run, interpretation; read before a test.
- `references/ai-content-and-localization.md` — texts of AI features, the localization process and string management; read for these topics.

## Sources
- GOV.UK, Content design guidance — "Writing for GOV.UK" and "Content design: planning, writing and managing content"
  (design/content guidance; principles: user needs, plain English). Only secondary sources, the primary pages
  were unavailable in the session of 2026-10-17 [unverified].
- NN/g — content tests (cloze, highlighter) described in secondary sources as methods from the book by Nielsen, Budiu,
  *Mobile Usability*; a threshold of about 60% for cloze [unverified] (accessed 2026-10-17).
- KPRM, *Komunikacja pisemna. Rekomendacje* (2nd ed. 2017, gov.pl) and the "Prosto i kropka" materials — Polish plain language
  (accessed 2026-10-17, through search).
- Regulation (EU) 2024/1689 (AI Act), Art. 50 — transparency obligations; applying from 2 August 2026, with
  the content marking obligation of Art. 50(2) for systems already on the market moved to 2 December 2026 by the
  Digital Omnibus package (regulation 2026/1744) — secondary legal sources (accessed 2026-10-17) [unverified in the OJ EU].
Described in our own words.
