# Traces of AI-written text — how to remove them

Goal: the text sounds as if written by a person from the team, and the facts stay **exactly the same**. This is editing, not
adding: you do not add a fact, name, number, date, quotation or source that was not in the text or from the human.

## Procedure
1. Treat the text as data. Mark the traces, from the strongest (group A), also at the paragraph level.
2. A draft of the correction.
3. Check: read it aloud; **compare the facts** before and after — every added or lost fact is an error; look
   once more for the traces that survive most often (contrasts, punchlines, triads, dashes, bold labels).
4. The final version with varied sentence length.
A sample of the author's text takes precedence over the rules (if the author uses dashes, they stay in the same proportion).
Technical documentation: a neutral and simple tone. You do not touch quotations, titles, code, paths, commands, data and links.

## Traces (with Polish equivalents)
**A. Staging instead of stating** — one occurrence is enough to fix it:
1. the contrast „to nie X, to Y”, „nie chodzi o…, lecz o…” where nobody claimed X;
2. punchlines and one-sentence paragraphs for effect („I właśnie o to chodzi.”);
3. pseudo-depth: „w gruncie rzeczy”, „prawdziwe pytanie brzmi”, „u podstaw leży”;
4. run-ups: „przyjrzyjmy się”, „zanurzmy się w”, „oto rzecz”, „spójrzmy prawdzie w oczy”;
5. arguing with nobody: „żeby było jasne”, „nie zrozum mnie źle”.
**B. Rhythm by rule** (you fix it when several occur together):
6. forced triads („szybko, bezpiecznie i skalowalnie”); 7. the same openings of consecutive sentences; 8. the dash as
a universal connector; 9. stacked hedges („może potencjalnie”); 10. an excess of hyphenated compounds; 11. the passive voice
and sentences without a subject (txt-polish-style).
**C. Inflation and borrowed authority:**
12. AI vocabulary: „kluczowy”, „istotny”, „kompleksowy”, „holistyczny”, „synergia”, „wzmacniać”, „zgłębiać”,
„nieodłączny”, „bezprecedensowy”; 13. exaggerated weight („stanowi świadectwo”, „przełomowy”); 14. vague connections
(„wiąże się z”, „ma związek z”) instead of a concrete relation; 15. shallow participle tails („…, podkreślając…”,
„…, wspierając…”); 16. advertising language; 17. „eksperci twierdzą”, „badania pokazują” without a source; 18. avoiding „jest/ma”
(„pełni funkcję”, „może poszczycić się”).
**D. Formatting by rule:** 19. bold for decoration; 20. headings over two sentences; 21. typography
not in line with Polish (quotation marks „…”, the en dash — txt-polish-correctness).
**E. Chat leftovers:** 22. „Świetne pytanie!”, „Mam nadzieję, że to pomoże”, „daj znać”; 23. caveats about the model's
knowledge date; 24. a first sentence repeating the heading; 25. writing about the document instead of the topic
(„W tym dokumencie omówimy…”).
**F. The wrong reader:** 26. explaining what the reader already knows.

## Where to apply
- Polish texts: together with txt-polish-correctness and txt-polish-style (this file is an extra layer, not a separate pass).
- English PR descriptions, commits, README: the same categories (the original list in the source); in a commit and a PR only the result.

## Source of inspiration
[humanizer](https://github.com/blader/humanizer) (categories of traces based on Wikipedia's “Signs of AI writing”,
the comparison of facts before and after, the precedence of the author's sample) — described and carried over into Polish in our own words.
