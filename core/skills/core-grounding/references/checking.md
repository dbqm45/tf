# How to check a claim before you write it

First the cheapest and most reliable check: a file in the repository, a command, the documentation of the version used
in the project. The model's memory comes last and only for stable knowledge.

| Claim | Check (examples) |
|---|---|
| a file, directory, symbol exists | `ls`, `git ls-files <ścieżka>`, Grep by name; give `plik:linia` |
| a function does X | read it (Read) and its tests; do not infer from the name |
| a test / build passes | run the command from CLAUDE.md and show the output; "it should pass" is not evidence |
| the version of a dependency in the project | `python3 .claude/hooks/detect_stack.py`, `package.json`, `pom.xml` (core-stack-sync) |
| the latest version of a package, whether a package exists | `npm view <pakiet> version`, `npm view <pakiet> time.modified`; Maven Central; core-source-research |
| a CLI flag, a configuration option | `<narzędzie> --help`, the documentation for the project's version; the configuration schema |
| a library API (method, parameter) | the types in the package (`grep` in a specific `.d.ts` file of the package, without reading the whole `node_modules`), the version's documentation |
| the behaviour of a browser or platform | documentation (MDN, a specification) with a date; a support table |
| a CVE, RFC, standard number, article of law | the primary source (NVD, IETF, the official journal / EUR-Lex) with the date it was read |
| a price, a service limit, a legal deadline | the vendor's page or the legal act with a date; note that it may change |
| a number in an estimate | show the calculation (input data × conversion factor); compute it with a command when possible |
| the number or exclusivity of occurrences in code ("exactly 4", "only here") | `ast-grep -p '<wzorzec>' -l <język> --json` or "find references" in an LSP; confirm every zero with `rg -n '<tekst>'`. The binary is `ast-grep` — on Linux `sg` is often the system command to change group (the `login` package) |
| a quote from a document, conversation, issue | a literal excerpt with its place; a paraphrase marked as a paraphrase |
| "someone reported / the community thinks" | core-source-research: specific sources with a date, not a general "everyone knows that" |

## Confidence markers (when it cannot be checked)
- **[checked: <how>]** — the output of a command, file:line, a source with a date.
- **[assumption]** — a conclusion from the available data; add how to confirm it.
- **[unverified]** — a fact from memory that cannot be checked now (e.g. no network); add the risk.
- **I don't know** — when there is no basis even for an assumption; propose who or what will give the answer.
The scripts also accept the older Polish markers ([założenie], [niezweryfikowane], [pytanie]) in existing documents.

## Signals that an answer may be made up
- A very specific name (flag, option, method) that did not appear in any file or source you read.
- A number without a calculation or a source ("usually 30%", "the limit is 1000").
- An answer that fits a question with a false assumption perfectly.
- Repeated fixes of the same thing in one session: the context is cluttered, and the model starts patching symptoms.

Described in our own words.
