---
name: txt-polish-style
description: Use for editing Polish text into a finished version — shortening, active voice, concreteness, typography.
metadata:
  review: "2027-10-17"
  catalog: "Use when editing a Polish text and the result is to be a finished, corrected version — shortening and strengthening sentences, active voice, concreteness, one tone and perspective, readability of instructions and messages, consistency between chapters, document typography. Not for an error report (txt-polish-correctness) or changes of substance."
  keywords: "zredaguj, przeredaguj, redakcja tekstu, gotowa wersja tekstu, popraw styl, uprość zdanie, urzędowy styl, czytelniej, komunikat w interfejsie, ton, komunikaty UI, teksty przycisków, komunikat błędu, link kliknij tutaj, mikrotekst, edit the text, rewrite, text editing, finished version of the text, improve the style, simplify a sentence, officialese, more readable, interface message, tone, UI messages, button labels, error message, click here link, microcopy"
argument-hint: "[standard|extended|premium] [file or passage]"
---

# Editing Polish text

Result: **a finished text**, not a list of remarks. Correctness (spelling, punctuation, syntax) is a precondition —
first txt-polish-correctness (linter + cheat sheet), then style.

## The principle of minimal intervention
Change only what needs correcting. Keep the author's voice, the terminology (the project glossary), the structure and the **meaning** of every sentence.
Do not add content, do not “embellish”, do not change code, commands, source quotations or numbers. A sentence with an unclear intent →
two versions and a question to the author instead of guessing.

## Modes
| Mode | Scope | When |
|---|---|---|
| **standard** (*standardowy*, default) | proofreading + simplification + style + tone + readability | documentation, README, descriptions, `docs/project/` artifacts |
| **extended** (*rozszerzony*) | + consistency between chapters/files (terms, level of detail, transitions) | longer documents, a set of files |
| **premium** | + imagery, contrast, rhythm — **only on explicit request** | articles, e-books, marketing texts |
No mode given → standard (*standardowy*; say so).

## Target style by kind of text
| Kind | Perspective and tone | Priorities |
|---|---|---|
| technical documentation, runbook | impersonal or „ty” (consistently), matter-of-fact | steps, operational verbs, zero information fog |
| project artifacts (brief, ADR, report) | neutral | TL;DR at the start, specifics and numbers, decision + rationale |
| UI messages, errors, buttons | „ty”, short | what happened + what to do; microcopy in detail: the interface content skill from the UX overlay, if installed |
| article, e-book, guide | „ty” or „my”, semi-formal | narrative + practice, sentence rhythm |

## Procedure (for each section)
1. **Proofreading** — errors against the norm (txt-polish-correctness).
2. **Simplification** — empty words out, one sentence = one thought, verbal nouns → verbs.
3. **Style** — active voice, the concrete instead of the abstract, no officialese.
4. **Tone** — one perspective and one level of formality in the whole text.
5. **Readability** — the reader knows where they are, what to do and what will happen next.
6. *(extended)* **Consistency** — terms, level of detail, transitions.
7. *(premium)* **Imagery** — sparingly, only when it strengthens.
Details, replacement tables and examples: `references/editing.md`. A text that sounds generated
(punchlines, triads, „kluczowy”, chat leftovers): `references/ai-writing-traces.md` — with a comparison of facts before and after. A document for print/PDF/DOCX: `references/typography-and-typesetting.md`.

## Result
- Make changes in the file pointwise (Edit), do not rewrite whole files; a long text — section by section.
- At the end a note (≤ 8 lines): mode, scope, 3–5 main changes with the reason, **the author's decisions kept**, questions to the author.
- A `docs/project/` artifact: after editing `project_record.py check` must pass (TL;DR and Handoff stay).

## Checklist
- [ ] the text has been proofread (linter without HIGH and MEDIUM remarks)
- [ ] meaning, numbers, terms, code and quotations unchanged
- [ ] one perspective and tone; short sentences where it is an instruction
- [ ] an editorial note with the author's decisions kept
