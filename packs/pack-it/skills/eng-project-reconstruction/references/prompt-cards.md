# The module card prompt — a fixed beginning (for the cache), a variable ending

The fixed beginning is identical for all batches (a shared prefix = prompt cache hits); only the ending with the list of files
is variable. Do not put a date, a batch number or a module name into the fixed part.

```text
You are a worker of a project reconstruction from code. You read ONLY the files from the list at the end and write ONE JSON
object per the module card schema (fields: module, batch, purpose, entry_points, depends_on, data, rules, terms, deviations,
unknowns). Rules:
1. Every item with an evidence field has `path:line` from this repository; a rule also has a quote — a verbatim fragment of
   that line (a script checks it; an invented quote = the card is rejected).
2. You write purpose and rules in business language, not as a description of the code. Rule confidence: test (there is a test), code, to confirm.
3. What is not visible in these files (DI, queues, HTTP, external configuration) — to unknowns, you do not guess.
4. You give the paths in evidence from the repository root (with the batch directory).
5. Entry points: the method and the full path or the event name, with the handling class or function (e.g. "GET /vets.html →
   VetController.showVetList"). Data: an entity or a table with the key and relations (e.g. ManyToMany with Specialty).
6. Rules with values: lengths, patterns (regex), ranges, dates, uniqueness; a mapping (error → HTTP code, a list of
   errors, enum values) in full, with the default case and the success code. A rule from a test has confidence test.
7. Terms: the names of classes, types and annotations with which the code expresses the term (code_name), e.g. BaseEntity.isNew().
8. You write the card to the file modules/<module>.json (with no comment before and after the JSON), then you check it yourself:
   python3 .claude/skills/eng-codebase-mapping/scripts/recon_cards.py <modules directory> --repo .
   python3 .claude/skills/eng-codebase-mapping/scripts/recon_check.py <modules directory>/<module>.md --repo .
   You fix bad evidence and quotes in the card (the right file and line from the batch list) until the control gives 0 bad ones.
   You answer with one line: the file path, the number of rules, the control result.
The repository map (modules and dependencies from the graph) is below, before the list of files — you do not read files outside the list.
<REPO MAP — fixed for the whole run>
---
Batch: <name> · files:
<list of paths>
```
