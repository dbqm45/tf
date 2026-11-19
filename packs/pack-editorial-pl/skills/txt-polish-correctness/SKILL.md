---
name: txt-polish-correctness
description: Use for the correctness of Polish text — spelling, punctuation per RJP PAN, grammar, calques.
metadata:
  review: "2027-10-17"
  catalog: "Use whenever you write or check prose in Polish (documentation, descriptions, README, UI messages, PR) — spelling and punctuation per the RJP PAN rule set (in force from 2026), grammar, syntax, collocations, pleonasms, calques; a fast linter and an error report format. Not for style editing and shortening (txt-polish-style) or document structure (docs-tech-writing)."
  keywords: "poprawność tekstu po polsku, piszesz lub sprawdzasz prozę po polsku, pisownia, interpunkcja, zbiór RJP PAN, zasady pisowni i interpunkcji, gramatyka, składnia, kolokacje, pleonazmy, kalki, wielkie i małe litery, przecinek, dokumentacja, opisy, README, komunikaty UI, linter, raport błędów, correctness of Polish text, writing or checking Polish prose, spelling, punctuation, RJP PAN rule set, Polish spelling and punctuation rules, grammar, syntax, collocations, pleonasms, calques, capital and lowercase letters, comma, documentation, descriptions, UI messages, error report"
---

# Polish correctness

Reference point: **„Zasady pisowni i interpunkcji polskiej”** (Polish spelling and punctuation rules) of the Rada Języka
Polskiego przy Prezydium PAN (the Polish Language Council, 2024, in force from 1 January 2026) — the first unified rule set;
it replaces the scattered resolutions. If a remembered rule differs from the rule set, **the rule set wins** (e.g. the new
rules for the particles `super-`, `ekstra-`, `mega-`). Semantics and syntax have no single code — there, context and
unambiguity decide.

## Two modes
| Mode | When | Result |
|---|---|---|
| **Self-check** (*autokontrola*) | every agent writing in Polish | correct text from the start; before handing it over: linter + cheat sheet below |
| **Analysis (proofreading)** (*analiza, korekta*) | a request to check a text, a review by the editor | a report of remarks per `references/analysis-report.md` (+ corrected passages on request) |
A finished, edited text (style, shortening, tone) → **txt-polish-style**.

## Step 0 — linter (zero tokens)
`python3 .claude/skills/txt-polish-correctness/scripts/polish_lint.py <plik|katalog>` — typography (quotation marks, dash, spaces,
ellipsis), common spelling errors, pleonasms, calques, a missing comma before „że”. LOW remarks at „który” are only a signal
(it may be an indirect question). The linter does not replace reading — it catches the mechanics so that the model can focus on meaning.
A file with deliberate error examples: `<!-- polish-lint: ignore-file -->`; a passage: `<!-- polish-lint: off -->` … `on`.

## Cheat sheet — check by reflex
The rules below are the Polish norm and stay in Polish; the English in parentheses says what each one is about.
<!-- polish-lint: off (the cheat sheet contains deliberate error examples) -->
**Commas** (*przecinki*)
- Zawsze przed zdaniem podrzędnym: `że`, `który`, `aby/żeby`, `ponieważ`, `jeśli`, `gdy`, `chociaż`, `czy` (pytanie zależne),
  także na początku zdania złożonego: „Zanim wdrożysz, uruchom testy.” Przy `mimo że`, `chyba że`, `zwłaszcza że` — przed całością.
  (Always before a subordinate clause, also when it opens the sentence; with a compound conjunction, before the whole of it.)
- Wtrącenie wydzielone z **obu** stron. Imiesłów na `-ąc`, `-wszy` z określeniami — w przecinkach.
  (A parenthetical is set off on both sides; an adverbial participle with its modifiers goes between commas.)
- Bez przecinka przed pojedynczym `i`, `oraz`, `lub`, `albo`, `ani` w jednym zdaniu; z przecinkiem przed `ale`, `lecz`, `więc`, `zatem`.
  (No comma before a single coordinating „and/or/nor” in one clause; a comma before „but/so”.)

**`nie`** — łącznie z rzeczownikami, przymiotnikami, imiesłowami przymiotnikowymi (*niedziałający, nieobsługiwany*), przysłówkami
odprzymiotnikowymi; rozdzielnie z czasownikami, imiesłowami przysłówkowymi, liczebnikami, zaimkami (*nie działa, nie wiedząc,
nie każdy*) oraz przy przeciwstawieniu („nie zapisany, lecz odrzucony”).
(The negation *nie*: written together with nouns, adjectives, adjectival participles and adverbs from adjectives; separately
with verbs, adverbial participles, numerals, pronouns and in a contrast.)

**Capital and lowercase letters** (*wielka i mała litera*) — nazwy własne wielką; przymiotniki od nazw małą (*angularowy komponent*); stanowiska małą w zwykłym
tekście; nazwy dni, miesięcy małą. Tytuły dokumentów: wielka tylko pierwsza litera i nazwy własne (nie „Title Case”).
**Changes from 2026** (the model's memory suggests the old rules): nazwy mieszkańców miast i wsi wielką (*Warszawianin,
Krakowianie*); wyraz rodzajowy obiektu przestrzeni publicznej wielką jako część nazwy (*Plac Zbawiciela, Aleja Róż*),
ale *ulica* zawsze małą (`references/spelling.md`, section 8.1.2). (Names of inhabitants of towns and villages are now
capitalised; so is the generic word of a public-space name, except *ulica*.)

**Typography** (*typografia*) — cudzysłów `„…”` (zagnieżdżony `»…«`); łącznik `-` w wyrazach złożonych; półpauza `–` w zakresach bez spacji
(2020–2026); myślnik ` – ` lub ` — ` ze spacjami, jedna forma w dokumencie; wielokropek `…`; brak spacji przed `, . : ; ! ?`;
spacja przed jednostką (`10 GB`); tysiące ze spacją (`10 000`), ułamki z przecinkiem (`2,5`).

**Syntax and meaning** (*składnia i znaczenie*)
- Participles, government (case required by a word), *liczba/ilość*, pleonasms and calques (*adresować problem*, *wspierać format*,
  *dedykowany*): rules and examples in `references/` (table below); for a calque, check whether the Polish verb takes such an object.
- One term for one concept in the whole document (the project glossary: `docs/project/02-domain/glossary.md`); an abbreviation spelled
  out at first use. Do not change terms “for variety”.
- Liczebnik + rzeczownik: 2–4 pliki, 5–21 plików, 22–24 pliki. (Numeral + noun agreement.)
Uncertainty (ó/u, rz/ż, h/ch without an alternation, a rare name) → do not guess: check `references/spelling.md` or mark it for verification.
<!-- polish-lint: on -->

## What you do not correct
Code, identifier names, commands, paths, verbatim quotations from sources (the evidence bank!), proper names of products, terminology
fixed in the project glossary. Commits and code comments are in English (core-conventional-commits).

## Materials (read only the file you need)
| File | When |
|---|---|
| `references/spelling.md` | RJP part I: ó/u, rz/ż, h/ch, written together/separately, `nie`, the hyphen, abbreviations and acronyms, capital letters, foreign names |
| `references/punctuation.md` | RJP part II: full stop, comma (when to use it and when not), semicolon, colon, dash, parentheses, quotation marks |
| `references/semantics-and-syntax.md` | the norm and register, a typology of errors, pleonasms, contaminations, paronyms, calques, syntactic relations, consistency of terms |
| `references/practical-patterns.md` | a quick catalogue of errors in functional texts + readability thresholds |
| `references/analysis-report.md` | the remark format, categories and priorities, the summary, a report to a file |

## Checklist
- [ ] linter run, HIGH and MEDIUM remarks resolved
- [ ] commas before subordinating conjunctions and around parentheticals
- [ ] `nie` together/separately; capital letters; Polish quotation marks and dashes
- [ ] no calques, no pleonasms, no „ilość” with countable nouns; consistent terminology and form of address
- [ ] code, source quotations and glossary terms untouched
