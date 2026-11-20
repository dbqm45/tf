# How to check each kind of claim

## 1. Checking table
| Claim | How to check | What to cite |
|---|---|---|
| A file or symbol exists | `ls`, `git ls-files`, `rg -n '<name>'` | `file:line` |
| A function behaves in a way | Read the function and its tests, not only its name | `file:line` of the code and test |
| Tests or build pass | Run the project's own command | The command and the end of its output |
| Dependency version used by the project | `python3 .claude/hooks/detect_stack.py`, the manifest or lockfile entry (core-stack-sync) | Manifest `file:line` |
| Latest version of a package / whether it exists | `npm view <pkg> version` (and `time.modified`), `pip index versions <pkg>`, Maven Central search | Command output with today's date |
| A CLI flag or config option | `<tool> --help`, the docs for the installed version, the config schema; for databases the settings view (`SHOW ALL`, `pg_settings`) | Help output or versioned doc URL + date |
| A library API | The package's own type definitions - grep one specific `.d.ts` file, not all of `node_modules` - or versioned docs | `file:line` or URL + version |
| Browser or platform behaviour | MDN or the specification, with the support table | URL + date |
| CVE, RFC, standard, law article | The primary source: NVD, IETF, the official journal (e.g. EUR-Lex) | URL + date read |
| Price, rate limit, legal deadline | The vendor's page or the legal act; it may change | URL + date read |
| An estimate | Show the calculation; compute it with a command | The command |
| Counts and exclusivity in code | A structural tool, then a text search for zeros (section 2) | Verdict table |
| A quote from a document | The literal excerpt with its location; mark paraphrase as paraphrase | Page / section / `file:line` |
| What the community reports | core-source-research, with dated sources | URLs + dates |

## 2. Verifying counts in code
Applies to reports, codebase maps and refactoring plans containing statements such as "called in exactly 4 places",
"only module X uses it", "always goes through Y", "the interface has 54 methods".
1. List every such statement in the document.
2. Check each with a structural tool: `ast-grep -p '<pattern>' -l <lang> --json` (the binary is `ast-grep`; on Linux `sg` is
   often the system's group command), LSP find-references, or the compiler (e.g. remove the symbol and count the errors).
3. Confirm every zero result with `rg -n '<text>'` - a zero can mean the pattern was wrong (generics, decorators,
   dynamic calls).
4. Record the result in a table and fix numbers in the text with a trace ("6 (report: 4)"):

| Claim | Verdict | Evidence | Method |
|---|---|---|---|
| `calculateFee` called in exactly 4 places | corrected: 6 | src/billing/fee.ts:41, src/checkout/total.ts:88, ... | ast-grep call pattern + rg |
| Only module billing calls it | refuted | src/checkout/total.ts:88 | ast-grep |
| `PaymentGateway` has 54 methods | confirmed | src/payments/gateway.ts:12-140 | compiler / LSP symbol list |

5. Do not rewrite the document's conclusions or ranking yourself: flag the discrepancies as "to decide" for the author.

## 3. Checking a tool's output
A script's or analyser's number is a claim from that tool. Before it goes into a report:
- open the largest item (the biggest cycle, the most connected module) and one random item;
- read the `file:line` that produced each and check that the tool's classification is right (e.g. a type-only import counted
  as a runtime dependency);
- where possible, compare a total with an independent count (a second tool, a hand count on a small module).

## 4. Quote verification
For a summary others will rely on:
1. Split the summary into individual claims.
2. For each claim find the supporting literal quote and its location.
3. Claims with no quote are removed and replaced by `[]`, so the reader sees that something was cut.
4. Add a list of gaps: questions the document does not answer.
Second pass, optional: give the summary and the document to an independent reviewer who checks claim by claim.

## Sources
- Anthropic, "Reduce hallucinations", platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations - accessed 2026-11-20 (quote extraction, verification with citations).
- `ast-grep run --help` (ast-grep 0.50.0) - accessed 2026-10-10.
