# Part III. Semantics, vocabulary and syntax — linguistic correctness

> **Spis treści:** 21. The linguistic norm and register · 22. A typology of linguistic errors — a map to the rest of… · 23. Lexical-semantic, word-formation and phraseological… · 24. Syntax — syntactic relations, word order, reference · 25. Semantic relations and terminology consistency

<!-- polish-lint: ignore-file (the file contains deliberate error examples) -->

Sources: the definitions and typology of linguistic correctness per the ZPE material „Co każdy powinien wiedzieć o
poprawności językowej”, the definition and subtypes of linguistic semantics (polszczyzna.pl), the semantic categories and
relations of the Słownik semantyczny języka polskiego (SSJP, Katedra Lingwistyki Komputerowej UJ / Grupa
Lingwistyki Komputerowej AGH), and the basic concepts of Polish sentence syntax (aniakubica.com/skladnia).

**A status different from Parts I–II.** Spelling and punctuation (`spelling.md`, `punctuation.md`) encode one
unified, binding RJP PAN rule set (2024) — there the ruling is always unambiguous. Semantics,
phraseology, syntax and stylistics have no comparable single, codified rule set of that
level of detail — the sources used in this part are mostly definitional/survey material, not lists of
ready-made rules. This part therefore combines what those sources actually give (the typology of errors, definitions of the norm,
the SSJP semantic categories and relations, the parts and syntactic relations of a sentence) with generally accepted, settled
knowledge of Polish language culture, needed to turn those definitions into concrete, checkable cases.
When in doubt between “nicer” and “unambiguous” — as in this whole skill — choose unambiguity.

## 21. The linguistic norm and register

Four types of norm (after ZPE):
- **Codified** (*skodyfikowana*) — rules formulated by specialists (dictionaries, the RJP rule sets).
- **Model** (*wzorcowa*) — binding in official situations, in line with tradition; this is the default register for
  technical documentation, feature descriptions, commit/PR texts, formal communication.
- **Functional** (*użytkowa*) — acceptable in casual contacts (internal chat, a working comment), less strict.
- **Customary** (*zwyczajowa*) — what the community accepts as correct in practice, regardless of codification.

When proofreading documentation/code/formal texts, rule by the **model** norm, not the customary one —
even if some colloquial form is widely used today, in technical documentation use the form that is
correct by the model norm, as long as this does not reduce unambiguity for the reader.

**A linguistic error** is an unjustified and *unconscious* violation of the norm — distinguish it from a **justified
innovation**: naming a new phenomenon/concept, a conscious breach of the norm for a rhetorical purpose, terminology
adopted in a given community (technical jargon, proper names, calques agreed in the team as a standard). Do not
“correct back” to the model form a term that in the given repo/documentation is already settled, consistently used
jargon (e.g. anglicisms like `deploy`, `merge`, `commit` in technical documentation
are not an error — they are the accepted register of the field).

## 22. A typology of linguistic errors — a map to the rest of the skill

The full typology of errors (after ZPE), with a pointer to the part of this skill that covers each:

| Error type | Example | Where to look |
|---|---|---|
| orthographic | *wziąś* instead of *wziąć* | `spelling.md` |
| punctuation | a missing comma before *który* | `punctuation.md` |
| inflectional (declension/conjugation) | *poszłem* instead of *poszedłem* | §23 below (cases, gender) |
| word-formation | a word built on a non-existent pattern (e.g. *„skopowanie”* instead of *ograniczenie zakresu*) | §23 below |
| syntactic (sentence structure, relations) | *nie mam czas* instead of *nie mam czasu* | §24 below |
| lexical-semantic (meaning of a word) | *efektowny* used in the meaning of *efektywny* | §23 below |
| phraseological (fixed expressions) | *pełnić rolę* (a contamination of *pełnić funkcję* + *odgrywać rolę*) | §23 below |
| stylistic | a template, a language fad, a register mismatch | §23 below |

Inflectional and word-formation errors have no separate rule section in this skill (this is a closed list of forms in
the grammar, not a set of rules to enumerate) — treat them as “does this form exist in this meaning” and when
in doubt check the dictionary, as with `ó`/`u`, `rz`/`ż`, `h`/`ch` in `spelling.md`, instead of guessing.

## 23. Lexical-semantic, word-formation and phraseological errors

**Pleonasm** (*pleonazm*) — using two words, one of which already contains the meaning of the other: *cofnąć się do tyłu*
(*cofnąć się* already means „do tyłu”), *kontynuować dalej*, *identyczny taki sam*, *kompletnie pusty* (*pusty*
already is complete/total). In technical documentation especially: *wewnętrzny mechanizm wewnątrz systemu*,
*opcjonalny do wyboru*.

**Tautology** (*tautologia*) — repeating the same content in other words within one utterance (broader than a
pleonasm — it can cover whole phrases, not only single words): *„ten sam identyczny plik”*, *„zbiór
wszystkich elementów, które w nim są”*.

**Phraseological contamination** (*kontaminacja frazeologiczna*) — crossing two fixed expressions into a phrase that exists
in neither of them, by distortion, swapping an element or changing the inflected form. The classic example:
*pełnić rolę* (a cross of *pełnić funkcję* + *odgrywać/grać rolę*) — correct is *pełnić funkcję* or
*odgrywać rolę*, not the mixture. With such expressions check whether the verb and the noun come from the same,
single fixed expression, not from two different ones.

**Wrong use of near-synonyms/paronyms** — words similar in form or meaning, but not
interchangeable. Frequent in technical/formal texts:
- *efektywny* (producing an effect, effective) vs *efektowny* (impressive, spectacular) — „efektowne
  rozwiązanie” ≠ „efektywne rozwiązanie”, they are not synonyms.
- *ilość* (uncountable things, mass/volume: *ilość wody*) vs *liczba* (countable things: *liczba
  wpisów*, *liczba użytkowników*) — in the model register „ilość rekordów”/„ilość plików” is a
  lexical-semantic error, correct is *liczba rekordów*, *liczba plików*.
- *permanentny* (constant, uninterrupted) vs *stały* — near-synonyms, but *permanentny* has the extra shade
  “lasting without a break”, not every *stałe* can be replaced with it.
- *incydentalny* (exceptional, one-off) vs *przypadkowy* (without a cause/random) — confused, but they are different
  meanings: something can be *incydentalne* (rare) without being *przypadkowe* (unplanned).

**Calques / syntactic anglicisms** (*kalki językowe*) — a literal translation of an English construction that in Polish
breaks the verb's valency or sounds unnatural, even though every word on its own is correct. An example
found and fixed in this repo: *„X pojawia swoje issue pod wszystkimi z nich”* (a calque of *„X surfaces its
issues”*) — *pojawiać (się)* is intransitive/reflexive in Polish and takes no direct object;
correct is *„X ma swoje issue widoczne pod wszystkimi z nich”*. When translating from English source
documentation, check not only the word but whether the Polish verb takes at all the kind of object the
English original has (see also §24, government).

**Language fads / overused words** — words used without need, flattening the text through overuse:
*dokładnie, globalny, kultowy, ekstremalny*; corporate templates: *nowa formuła, odbyć rozmowę, owocna
współpraca, szereg osiągnięć*. In technical documentation the equivalent is overused, say-nothing
filler words (*„robust”, „seamless”, „leveraging”* and their calques: *„bezproblemowo”, „wykorzystując
możliwości”*) — in line with the KISS principle from the docs-tech-writing skill, replace them with a concrete, checkable
description of what actually happens.

## 24. Syntax — syntactic relations, word order, reference

Three syntactic relations govern how words combine in a sentence:

- **Agreement** (*związek zgody*) — two words agree in gender/number/case (subject–predicate, attribute–
  noun). A trap: a collective subject like *większość/część/wiele + rzeczownik w dopełniaczu* in the model
  register takes a predicate in the **singular**: *„Większość komponentów **ma** już tę flagę”*
  (not *„mają”*), although in colloquial speech the plural form is tolerated.
- **Government** (*związek rządu*) — a verb/adjective/preposition requires a specific case from the dependent word
  (**valency**). The most important trap to catch when proofreading: **a negated transitive verb
  usually requires the genitive, not the accusative that the same verb would require in the non-negated form**:
  *„mam czas”* (accusative) → negated *„nie mam **czasu**”* (genitive), never *„nie mam czas”*. This is
  exactly the mechanism of the error found and fixed in `FEATURES.pl.md` of this repo: *„(...) ma prawie
  żadnej konfiguracji”* — the noun already stood in the genitive („żadnej konfiguracji”), but the verb was not
  negated, which is inconsistent; the lost „nie” shows itself precisely through this case mismatch.
  **A practical heuristic:** a noun/pronoun in the genitive after a verb that looks non-negated
  (`mieć`, `widzieć`, `znać`, `czytać`…) — check whether a `nie` before the verb was lost by accident,
  instead of automatically correcting the case itself to the accusative (the direction of the correction depends on what the author
  actually wanted to say).
  Other verbs with a “sensitive” valency, easy to confuse because of near-synonymy: *słuchać kogoś/czegoś*
  (genitive) vs *słyszeć kogoś/coś* (accusative); the preposition *dzięki* requires the dative (*dzięki niemu*, not
  *dzięki niego*).
- **Adjunction** (*związek przynależności*) — an adverbial/object belongs to one specific predicate in the
  sentence; in multiple compound sentences check that the adverbial really modifies the predicate
  it is visually/logically closest to, not another, distant one.

**Word order** (*szyk wyrazów*) — in Polish word order is free (it does not decide grammaticality), but it decides the
logical stress and unambiguity. In technical documentation: an attribute/object placed too far from
the word it refers to may suggest a reference to another, nearer noun — if
reordering removes the ambiguity without changing the content, reorder, even when the original order is not per se
an error.

**Pronoun reference in compound sentences** — a relative pronoun (`który/która/które`, `co`, `jaki`) should
have an unambiguous antecedent. When a sentence has two candidate nouns (especially of different gender, which by itself
does not settle it for a more distant attribute) and the context does not make clear which one the pronoun refers to,
rephrase instead of leaving the reader to guess — this is the same overriding priority “unambiguity over
a rigid rule” as in the docs-tech-writing skill.

## 25. Semantic relations and terminology consistency

SSJP (Słownik semantyczny języka polskiego, UJ/AGH) describes word meanings through relations: **synonymy**,
**near-synonymy**, **hyponymy/hypernymy** (specific/general word), **meronymy/holonymy**
(part/whole). Practical use when editing technical documentation:

- **Synonymy/near-synonymy as a consistency trap** — two near-synonyms (not identical, but
  interchangeable in a given context) used inconsistently for one technical concept confuse
  the reader, even if each use on its own is linguistically correct. This is the same principle as “terminology
  consistency matters more than elegance” from the docs-tech-writing skill — here named from the perspective of
  semantics: if you once called something „workflowem”, do not swap it for „przepływ pracy” or „proces” for
  variety in the same document.
- **Hypernym vs hyponym** — make sure a general term (a hypernym, e.g. „błąd”) does not replace a precise
  specific term (a hyponym, e.g. „wyjątek”/„ostrzeżenie”/„awaria”) when the documentation elsewhere
  distinguishes these levels — using the hypernym where the context has already set up the distinction into hyponyms is
  a loss of precision, not stylistic variety.
- **Meronymy/holonymy** (the part–whole relation) — when describing architecture/components check whether
  the expressions „komponent X” and „część systemu Y” keep one consistent direction of this relation across
  the whole document (X is part of Y, not the other way round), especially in documents with many levels of
  nesting (system → module → component → function).
