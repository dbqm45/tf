---
name: core-grounding
description: Use when you ask whether a version, flag, date or number is real, or the assistant may be making things up — a source, "I don't know".
metadata:
  review: "2027-10-10"
  catalog: "Use for every answer, report and artifact that contains facts about code, versions, APIs, commands, numbers or sources — classes of claims and how to check them, the places where models make things up most often, context hygiene, self-check and a script that checks references. Not for the procedure of researching external sources (core-source-research) or code tests (the testing skills, pack-it)."
  keywords: "wynik skryptu, liczba z narzędzia, przepisać liczbę z wyniku, halucynacje, zmyślanie, nie zgaduj, czy to prawda, kolega twierdzi, podobno istnieje, czy taka opcja istnieje, sprawdź fakty, źródło, pewność, wymyślona flaga, nieistniejące API, za długi kontekst, model się myli, weryfikacja odpowiedzi, liczby w raporcie, dokładnie N wywołań, tylko w jednym miejscu, ile razy wywoływana, zużyty kontekst, pamięć automatyczna, podsumowanie długiego dokumentu, streszczenie umowy lub regulaminu, notatka z dokumentu, najpierw cytaty, niczego spoza dokumentu, z podanych materiałów, agent powtarza ustalenia, łata wokół czerwonego testu, długa sesja, skąd wiem że to prawda, czy to nie wymysł, asystent zmyśla, przyznać że nie wie, mówi pewnym tonem a zgaduje, dopisał coś od siebie, streszczenie długiego dokumentu, czy ta flaga istnieje, sprawdzić liczby przed wpisaniem do dokumentacji, sprawdzić liczby w raporcie, czy procenty się zgadzają, raport z pomiaru przed oddaniem, liczby bez źródła, data w przyszłości, zweryfikować liczby z odpowiedzi, data wydania, liczby przed wpisaniem do dokumentacji, hallucinations, making things up, is this true, does this flag exist, check the facts, made-up API, numbers in a report, I don't know, quotes first, long context, used-up context, nie zmyślał, nieistniejące wersje i flagi, ścieżki plików, których nie ma, łamie przyjęte ograniczenie, sygnały zużytego kontekstu, długa sesja, potwierdzić twierdzenie, fałszywe założenie w pytaniu, pamięć to twierdzenie z dnia zapisu, wcześniejsze ustalenie z notatek, liczba z pamięci, versions and flags that do not exist, paths that do not exist, signals of a used-up context, false assumption in the question, memory is a claim from the day it was written"
---

# Grounding answers — how not to make things up

A model makes things up most often when:
- it answers from memory instead of from a check;
- it feels pressure to always answer;
- it works in a long context full of failed attempts.

This skill removes those three causes. Two parts work mechanically and do not depend on the model:
- the `context_guard` hook warns about a context that is too long;
- the `scripts/grounding_check.py` script checks whether the references in documents exist.

## 1. Every claim has a class and evidence
| Class | Example | Evidence before writing |
|---|---|---|
| **about this repository** | "function X validates Y", "file Z exists", "the test passes" | a file you read (`plik:linia`), the output of a command in this session |
| **a current external fact** | a version, version compatibility, a CLI flag, a configuration option, a package name, a price, a legal deadline, a CVE | a primary source with a date (core-source-research), `--help`, `npm view <pakiet> version`, the documentation for the project's version |
| **stable knowledge** | how a B-tree works, what idempotency is | knowledge is enough — but without specific numbers and names you did not check |
| **a conclusion or assessment** | "it's probably the cache", "option B will be cheaper" | mark it: **[assumption]** or **[assessment]**, with how to check it |

A claim without evidence you do not give as a fact. The choices:
- check it;
- mark it as an assumption;
- leave it out.

## 2. "I don't know" is a correct answer
- When it cannot be checked (no access, no source, no time), you say so plainly: what you do not know and how to
  find out. A made-up but plausible-sounding answer is worse than "I don't know".
- You do not guess names: of methods, endpoints, flags, configuration keys, packages, files, environment variables.
  A non-existent package name is also a security risk (impersonating packages — the supply chain skill, pack-it: ops-supply-chain-security).
- The question contains a false assumption (e.g. it asks about a flag that does not exist)? You say you did not find it. You show where you looked, and you do not fit the answer to the question.

## 3. Where models make things up most often — always check
Versions and version compatibility · names of APIs, methods and options · CLI flags · package names · paths and file names
in the repository · numbers (ports, limits, error codes, CVEs, RFCs, articles of law) · dates and deadlines · quotes
and attribution of sources · the output of a command you did not run · the behaviour of code you did not read ·
numbers in estimates (show the calculation). Details and checking commands: `references/checking.md`.

### Structural claims about code
"Exactly 4 calls", "only in module X", "always through Y", "the interface has 54 methods" — models count these worst,
and the reader of the report takes them on trust. The more certain a number looks, the more you check it:
1. list all such claims in the report (maps, analyses, a refactoring plan);
2. check each with a structural tool (`ast-grep -p '<wzorzec>' -l <język> --json`, "find references" in an LSP,
   the compiler) — verdict: confirmed / refined / refuted, with `plik:linia`;
3. confirm every **zero** from a structural tool with a plain `rg -n '<tekst>'` — a zero can mean a wrong pattern;
4. a fix in place with a trace ("150 (report: 145)") and a "Claim verification" table: claim → verdict →
   evidence → method. You do not rewrite the conclusions and the ranking on this occasion — you describe a discrepancy as "to decide".
5. **The output of a script or tool is also a claim.** Before you copy a number into a report, check in the code
   the largest item (the largest cycle, a hub) and one random one — read the `plik:linia` that produces it. In a factory
   measurement (2026-10-18) an error of a draft script ("a runtime cycle of 242 files", in reality closed by type imports)
   was repeated by all the agents that used it; the agent without the script counted correctly.

## 4. Long documents: quotes first, conclusions after
When analysing long material (a specification, logs, a transcript, terms and conditions):
1. List the literal quotes with their place (file:line, section) that answer the question.
2. Only on their basis draw conclusions.
3. Withdraw a conclusion without a quote or mark it as an assumption.

**Verification with quotes after writing** (text for others: a report, a legal note, a change description): after the draft go
claim by claim and find a quote from the material for each. Remove a claim without a quote, and in its place leave
`[]` — the reader sees that something was cut and can ask.

**Only from the given materials** — when the task requires it (regulations, a contract, customer requirements, interview analysis):
general knowledge serves to understand the question, not as a source of claims; what the materials do not cover you name as a gap.
The factory turns this mode on for consultants and roles with `grounding: sources-only` (`.tf/config/config.yaml`, `sources_only_note`).

The same pattern is used by ddd-discovery-intake from pack-it (a bank of quotes with an `evidence` check).

## 5. Context hygiene
The quality of answers drops when the context fills up, and when there are many failed attempts in it.
- **One task — one context.** A new, unrelated task you start from a clean session (`/clear`). You come back
  from a checkpoint (core-project-record), not from a long history.
- **Two failed fixes of the same thing** → stop. Write down in the checkpoint what does not work and why.
  Then start again with a better instruction.
- **Exploration in a subagent** (`scout`, `Explore`): reading many files stays in its context, you get back
  the result.
- **Load only the skills and sections you need** — TL;DR and Handoff instead of whole artifacts.
- **Compaction:** decisions and findings must be in files before the context is summarised (CLAUDE.md
  says what to keep).
- **Signals of a used-up context** (behaviour, not a number of tokens): you repeat findings as new discoveries; you give
  paths or commands that do not exist; you break an agreed constraint; you patch around a red test instead of going back
  to the cause; summaries grow, decisions shrink. **Two signals at once → a decision, not another attempt:** `/compact`
  (the direction is good), undoing the last step (`/rewind`), `/clear` (the task is over), a new session from the checkpoint.
- **The compaction command:** `/compact Keep: decisions, file paths, commands run and their results, test status,
  constraints, open risks. Drop: failed attempts, repeated logs, abandoned hypotheses. Next step: <jedno>.`
- **Memory is a claim from the day it was written.** An automatic memory entry (`~/.claude/projects/<projekt>/memory/`) or
  an earlier artifact (a map, research) is a starting point, not the truth: before using it check it in the code, and correct an outdated
  claim openly in the report. Rules binding the team you keep in the repo (core-agent-instructions), not in memory.
- The `context_guard` hook warns when the context crosses a threshold (by default 100 thousand and 150 thousand tokens). You answer
  the warning by saving a checkpoint and proposing a new session or `/compact` with an instruction.

## 6. Self-check before handing over
Before an answer with facts, a step report or an artifact:
1. List the factual claims in your head. Each must have evidence from section 1. Without evidence: check, mark
   or remove.
2. Give claims about state ("tests pass", "the file exists", "version X supports Y") with evidence: a command
   and its output, `plik:linia`, a source with a date.
3. For documents: `python3 .claude/skills/core-grounding/scripts/grounding_check.py <plik.md>`. The script
   checks whether paths, `plik:linia` references and local links exist. With `--jev` (optional, the key
   TYPESAFE_API_KEY) it also checks whether the indicated lines **confirm** the sentence the reference stands in.
   - Fix conflicting and non-confirming references.
   - Review the uncertain ones yourself.
   Numbers and dates: `python3 .claude/skills/core-grounding/scripts/claims_check.py <plik.md|katalog>` — the first line
   is `Verdict: OK | WARNINGS | ERRORS`.
   - An error: a percentage that does not match the fraction in the `X/Y (Z%)` notation, a date that does not exist, a state date in the future — fix it.
   - A warning: a number with a unit (%, USD, ms…) without a trace of its origin on that line — add a command, a path,
     a link or [assumption]; a report based on one data file declares it once (a "Files:" line with the data file's path in backticks).
4. In the diff you look for three typical classes of model errors: code that is syntactically correct but semantically wrong (a lost
   transaction, a retry, an edge case); a test that pins the implementation instead of the behaviour; a decision from the middle
   of a long conversation skipped in favour of newer context.
5. For important decisions (architecture, security, law) let someone without your context assess the result:
   security-reviewer, `/code-review` or a second executor. The author does not assess their own work.
6. **A decision that is hard to reverse, an answer with no source to check:** ask the same question 2–3 times
   independently (separate executors, the same brief — best-of-N). Diverging answers are a signal of making things up: only
   what repeats and has evidence stays; the rest goes back as a question. It costs N runs — only for such
   decisions. A cheaper variant: hand the answer over to be checked claim by claim (iterative refinement).

## Checklist
- [ ] facts about the repo backed by a file you read or a command from this session
- [ ] versions, flags, APIs, packages, numbers and dates checked at the source or marked as unverified
- [ ] conclusions marked **[assumption]** / **[assessment]**; "I don't know" where it cannot be checked
- [ ] long material: quotes before conclusions; text for others verified with quotes (cut claims as `[]`)
- [ ] context: the task in a clean session, exploration in a subagent, the `context_guard` warning handled
- [ ] numbers and exclusivity claims about code ("exactly N", "only here") checked with a structural tool, zeros confirmed with `rg`
- [ ] `grounding_check.py` without errors for the documents handed over

## Sources
- Anthropic — "Reduce hallucinations" (the right to "I don't know", quotes as the basis, verification through quotes,
  multi-run verification, restriction to the given materials), platform.claude.com, checked 2026-10-20
- Anthropic — "Best practices for Claude Code" (a full context lowers quality, `/clear` between tasks,
  subagents for exploration, verification instead of declaration)
- Claude Code — "How Claude remembers your project" (code.claude.com/docs/en/memory, accessed 2026-10-10): automatic
  memory in `~/.claude/projects/<projekt>/memory/`, `MEMORY.md` loaded up to 200 lines or 25 KB.
- ast-grep 0.50.0 — `ast-grep run --help` (the flags `-p`, `-l`, `--json`), checked 2026-10-10.
- The 10xDevs course, ed. 3 (2026), lessons 3.1 and 3.3 (classes of errors, signals of a used-up context), module 4, lessons 3–4
  (verifying structural claims) — training material (accessed 2026-10-09).
Described in our own words.
