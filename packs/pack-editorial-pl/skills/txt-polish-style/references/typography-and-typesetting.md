# Typography and document typesetting

Applies to typeset documents (DOCX, PDF, print, e-book). In Markdown only the character rules (section 1) apply — the rest is up to
the renderer; do not simulate layout with spaces or blank lines.

## 1. Characters (Markdown too)
| Character | Use | Spaces |
|---|---|---|
| hyphen (*łącznik*) `-` | compound words (biało-czerwony, e-mail) | none |
| en dash (*półpauza*) `–` | ranges (1990–2000, s. 23–45) | none |
| dash (*myślnik*) `–` / `—` | a parenthetical, a pause | on both sides; one form in the document |
| quotation marks (*cudzysłów*) `„…”`, nested `»…«` | quotations, titles | close up to the text |
| ellipsis (*wielokropek*) `…` (U+2026) | a break-off, an omission `[…]` | no space before |
No space before `, . ; : ! ?`; a space after. A non-breaking space (U+00A0) between a number and a unit and after one-letter conjunctions
at the end of a line (i, a, w, z, o, u) in typesetting for print.

## 2. Paragraphs and spacing
Set spacing and indents with the paragraph style, not with blank lines or spaces. Body text: 6–12 pt spacing after a paragraph
or a first-line indent of 1–1.25 cm (one of the two). A heading closer to the text it opens than to the previous one.

## 3. Widows and orphans (*wdowy i bękarty*)
A lone last line of a paragraph on a new page (a widow) and a lone first line at the bottom of a page (an orphan) — a typesetting error.
Turn on widow and orphan control in the style; if needed, shorten/lengthen the neighbouring paragraph.

## 4. Typefaces, sizes, line spacing
One body typeface + at most one for headings. Body text 10.5–12 pt, line spacing about 1.15–1.5; footnotes and captions 9–10 pt;
the heading hierarchy visible by size and weight. Left alignment is safe; justification only with hyphenation
(otherwise “rivers” of spacing).

## 5. Margins (print)
2–2.5 cm; more on the binding side (about 3–3.5 cm). E-book (EPUB): the reader sets the margins — do not force them.

## 6. Editorial report
Remarks in the format from txt-polish-correctness (`.claude/skills/txt-polish-correctness/references/analysis-report.md`), category `TYPOGRAPHY`, stating the rule and the change
in the document style (not “by hand in every paragraph”).

## Typesetting checklist
- [ ] characters: hyphen / en dash / dash, Polish quotation marks, ellipsis, no space before punctuation
- [ ] spacing and indents from styles; no blank lines for layout
- [ ] no widows and orphans; consistent typefaces and heading hierarchy
