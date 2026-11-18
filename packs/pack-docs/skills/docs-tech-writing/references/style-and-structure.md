# Style and structure of technical documentation

> **Contents:** Traits of good documentation · Who you write for — choosing the style · What technical documentation of an application/system must… · Examples of good tables of contents (navigation patterns) · Describing components, methods, commands · Procedures in the spirit of ASD-STE100 · Consistency — more important than elegance · Formatting — one set of styles · Tools (documentation generators) · Why it pays off

An expansion of the docs-tech-writing hub. The "heavy" elements (copyright, list of figures, index, page numbering) apply to
larger documents (a manual, system documentation), not to a README.

## Traits of good documentation

- it is **accurate and error-free**,
- it is **complete** (it leaves no holes the reader has to fill with guesses),
- it is **consistent** — terminology, style, formatting,
- it is written **clearly and unambiguously**,
- the user can **easily find** the information they need (navigation, table of contents, index),
- it has a **neat, predictable look** (uniform formatting).

## Who you write for — choosing the style

Three typical situations in which someone opens documentation:
1. they are curious how something works and what it offers,
2. they want to start using it,
3. they got stuck while using it and are looking for help.

The real reader is more often a **developer who deploys/integrates the system** than a purely decision-making person —
by default write in a technical, concrete style: short, meaty sentences without ornaments, readable at
first glance, logically ordered.

If there are several groups of readers with substantially different needs (e.g. a sales department using the UI vs.
an IT department developing the source code) — consider **two separate documentations**. It is more work, but more convenient
for the readers than one documentation trying to serve both groups. If you still decide on one
document, **clearly mark** which sections are for which group.

**Descriptive vs. task-based approach**: the descriptive one follows the structure of the system (e.g. the order of the menu); the task-based one
follows the order in which the reader actually performs their tasks. Example: when documenting an interface
for a person issuing invoices, the task-based approach describes the options in the order of use when issuing an
invoice, not in the order they are laid out in the menu.

## What technical documentation of an application/system must contain

- **an introduction** — a concrete description of what this application/system does (in one sentence or one paragraph — both forms
  are acceptable, depending on complexity),
- **installation and dependencies**,
- **the algorithms used / the logic of operation**,
- **the layout and the operation of the individual components**.

### At the start of the document

- copyright (if applicable — preferably wording from the legal department, not improvised),
- table of contents,
- optionally: a list of figures/diagrams (useful in larger documents),
- an introduction that says: what product the documentation describes, who it is for, what it generally contains,
  what notation conventions are used (e.g. a font/format for code fragments, NOTE/WARNING markers).

### At the end of the document

- appendices — supporting information, useful but not critical for understanding the main text (e.g.
  definitions of database fields). Appendices **are not** the place for everything that has no obvious
  home — that is a signal that the structure needs rethinking, not that another appendix needs adding.
- a glossary of system-specific terms and abbreviations the reader may not know. **A glossary
  at the end is better than explaining on first use in the text** — documentation is not a
  novel read linearly from A to Z; the reader lands in a specific chapter from a link/search.
- an index — it strongly affects how useful the documentation is in practice; do not treat it as an optional
  extra in larger documents.

## Examples of good tables of contents (navigation patterns)

- **Heroku Dev Center** — the main categories visible at once (architecture, databases, security,
  CLI, add-ons, languages), and below them — without hiding in drop-down menus — the full list of items of each
  category in several columns. Advantage: nothing needs an extra click to see the scope.
- **Laravel** — the main categories in a sidebar, expanded with a plus; the current submenu highlighted in color.
  Advantage: a clear sense of "where am I" in deeper navigation.

There is no one right layout — both above are considered very good, even though they are completely different. The choice
depends on the size of the documentation: a flat list visible at once (Heroku) for small/medium sets;
an expandable sidebar (Laravel) for very extensive documentation.

## Describing components, methods, commands

- **Back every** described method/command/endpoint **with a code fragment**. Reasons: (1) an example explains
  the principle faster than a verbal description; (2) it is a ready copy-paste element for a reader who does not
  have to work out the syntax on their own.
- **Grade the difficulty** — start with the 3–5 easiest cases (a simple request, authentication),
  then move on to more complex ones. The reader gains confidence from early successes before meeting
  harder challenges — it is then easier for them to absorb new information.
- Screenshots with forms/data — fill them with **realistic but made-up** data (name, address,
  phone), do not leave empty fields. **Never** use real people's data (e.g. copied from
  a phone book) — that is a real legal risk, not only a stylistic slip.

## Procedures in the spirit of ASD-STE100

ASD-STE100 (Simplified Technical English) is a language standard for technical maintenance documentation from aviation:
a limited vocabulary, one meaning per word, short sentences [unverified: the current edition and the detailed rules
— check in the ASD specification before citing it]. The standard is about English; for documentation in
English you can adopt it directly, for other languages you carry over the rules:
- one action in one step, numbered steps, a verb in the imperative mood at the start ("Run…");
- a sentence in a procedure up to about 20 words; the condition before the action ("If the test fails, stop the deployment.");
- one term for one concept and one meaning of a term across the whole document (the project glossary);
- a warning before the step it concerns, not after it;
- active voice, no parenthetical clauses and no shortcuts ("this", "that" without a noun).
You apply them in runbooks, installation instructions, repair steps and specifications — wherever the reader
performs actions under time pressure. Explanatory text (concepts, ADR) can be looser.

## Consistency — more important than elegance

- If the word "system" repeats ten times in one paragraph — that is not a mistake. Replacing it with synonyms
  ("program", "application") for variety **misleads**, because the reader starts to wonder whether
  it is still the same thing or something else. A term once adopted for a given phenomenon/element — used consistently to the
  end of the document.
- The same goes for actions: if in the first chapter you write about "clicking", do not switch in another
  chapter to a different synonym of the same action.
- Clarity beats strict adherence to stylistic/grammatical rules when these two values
  collide. Example: the sentence "systems: A, B, C and D" is ambiguous (4 systems, or 3, the
  last of which is called "C and D"?) — adding a comma after "C" removes the ambiguity, even if the resulting
  punctuation is unusual.
- Documentation is for a human, not for a computer: if a diagram (e.g. a state transition diagram)
  turns out more confusing than helpful — better drop it and describe the states/transition conditions
  in words than insist on the visualization "because that was the plan".

## Formatting — one set of styles

Define and consistently apply a style for (key especially when more than one person works on the document
— otherwise chapters by different authors will be visually inconsistent):
- the heading of a main chapter, a subchapter, a sub-subchapter (and so on),
- "plain" text,
- a numbered / bulleted list,
- the continuation text of a list item (indented, from a new line),
- a source code fragment,
- a caption under a figure/screenshot.

Expose key information (especially sequences of actions to perform) as a **list**, not as
a comma-separated enumeration in one sentence hidden among others. A reader performing actions takes their eyes off
the screen/document and comes back to it many times — a list lets them find the right step faster than a compound
sentence.

**Many small chapters are better than a few large ones** — it is easier to land directly on the fragment you need.

**The KISS rule** (*Keep It Short and Simple*): a few short, simple sentences/paragraphs are easier to absorb than
one long compound sentence / one long paragraph.

## Tools (documentation generators)

When documentation can be generated from the sources (code comments, annotations, contracts) — generate it: faster than a manual
document and less prone to drifting from the code. Examples: TypeDoc / JSDoc (TS/JS), OpenAPI + Redoc/Scalar/Swagger UI
(HTTP API), Javadoc (Java), Doxygen (C/C++ and others). Narrative pages (manuals, tutorials) — static site
generators from Markdown (e.g. Docusaurus, MkDocs, VitePress; Slate for single-page API documentation).
Generators handle reference documentation well, narrative documentation less so — that you write yourself.

## Why it pays off

Good technical documentation really reduces the number of support tickets (solving a problem usually takes
longer than writing the paragraph that would have prevented it), changes the tone of communication with customers from
frustration to neutrality/satisfaction, and becomes the foundation for scaling further products/features without
having to rebuild the context from zero.
