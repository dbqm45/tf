# Language analysis report format

## A single remark
```
[CATEGORY] | PRIORITY: HIGH / MEDIUM / LOW
Location: file:line or section / paragraph / a locating quotation
ORIGINAL: „<exact quotation>”
PROBLEM: <1–2 sentences, with a reference to the rule, e.g. RJP 12.1.1>
SUGGESTION: „<correct version>”
```
Categories: `SPELLING` · `PUNCTUATION` · `GRAMMAR` · `COLLOCATION` · `PLEONASM` · `CALQUE` · `STYLE` · `READABILITY` · `TYPOGRAPHY`.
Priority: **HIGH** — an error against the norm or one that changes the meaning; **MEDIUM** — noticeable to the reader (style,
register, repetitions); **LOW** — an editorial preference, typography.

## Summary (in the reply)
```
## Language analysis — <document>
Correctness score: X/10 · remarks: N (high A | medium B | low C)
| Category | Count | Example |
Most frequent patterns (to fix in the whole text): 1. … 2. … 3. …
Style and consistency score: X/10 — one sentence
```
The full report as a file: `docs/project/07-review/<data>-language-<dokument>.md` (core-project-record header, `artifact: review`)
or `.docx` on request (the docx skill; write the script with the Write tool in UTF-8 and check `file -i` — a report on Polish
without Polish characters is itself wrong).

## Corrected passages (on request)
ORIGINAL → CORRECTION, changes listed as bullets with an explanation; at the first occurrence of a pattern `[CHANGE: …]`.
Minimal intervention — no changes of substance, no “embellishing”, terms and code unchanged.
