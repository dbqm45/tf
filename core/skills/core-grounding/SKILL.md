---
name: core-grounding
description: Use when asking whether a version, flag, option, date or number is real, when a claim needs evidence, or when the assistant may be making things up.
metadata:
  review: "2027-11-20"
  catalog: "Use when facts must be checked before they are stated or handed over: versions, CLI flags, config options, API and package names, file paths, numbers, dates, quotes and counts in code; when a colleague's or an earlier answer may be invented; when a long document must be summarised only from its text; when a long session starts producing wrong file names or patches around the same failure; and before handing over a report (reference and number checks with the factory scripts). Not for researching what changed recently in the outside world (core-source-research) or testing application code (the testing skills of a pack)."
  keywords: "halucynacje, zmyśla, zmyślił, wymyśla, wymyślił, czy to prawda, czy ta flaga istnieje, czy ta opcja istnieje, nie istnieje, fałszywa opcja, kolega twierdzi, nieistniejąca funkcja, nieistniejące wersje, wersja biblioteki, flagi CLI, sprawdź fakty, weryfikacja faktów, źródło, dowód, nie wiem, przyznać że nie wie, pewnym tonem, strzela, niezweryfikowane, założenie, liczby w raporcie, konkretne liczby od asystenta, data wydania, zweryfikować liczby przed wpisaniem, release date, procenty się nie zgadzają, 45/56, claims_check, grounding_check, odwołania plik:linia, ścieżki w dokumentacji, wynik skryptu, liczba z narzędzia, cykl importów, dokładnie w 4 miejscach, ile wywołań, ast-grep, LSP, znajdź odwołania, podsumowanie umowy, umowa SLA, specyfikacja na wiele stron, tylko z dokumentu, cytaty, dopisał od siebie, długa rozmowa, myli nazwy plików, łatki wokół testu, czerwony test, zużyty kontekst, /compact, /rewind, /clear, nowa sesja, punkt kontrolny, pamięć, MEMORY.md, hallucination, made up, is the flag real, does the option exist, verify claim, evidence, I don't know, unverified, assumption, numbers in report, file:line, structural claims, quote first, sources only"
---

# Grounding - every claim has evidence, or is marked

Invented facts come from three places: answering from memory instead of checking, pressure to always have an answer, and
a long context cluttered with failed attempts. The defences below are procedures, plus two mechanical ones: the
`context_guard` hook and the checking scripts.

## 1. What kind of statement is it, and what proves it
- **About this repository** (a file exists, a function does X, tests pass) -> a file you read in this session (`path:line`) or
  a command you ran here and its output.
- **A current external fact** (version, compatibility, CLI flag, config option, package name, price, limit, legal deadline,
  CVE) -> a primary source with its date: `<tool> --help`, `npm view <pkg> version`, the docs for the project's version, the
  vendor's page, the official journal. Researching what changed recently is core-source-research.
- **Stable knowledge** (how a B-tree works) -> memory is acceptable, but no unchecked specific names or numbers.
- **A conclusion or estimate** -> say so: `[assessment]` or `[assumption]`, with how to confirm it.
A claim without evidence is checked, marked, or left out. It is never stated as fact.

Markers (English, read by scripts): `[checked: <how>]`, `[assumption]` + how to confirm, `[unverified]` + the risk, and the
plain words "I don't know" + who or what can answer.

## 2. "I don't know" is a valid answer
- Prefer it to a plausible invention. Say what is unknown and how to find out.
- Never guess names of methods, endpoints, flags, config keys, packages, files or environment variables. An invented package
  name is also a supply-chain risk: someone may register it (pack-it ops-supply-chain-security).
- A question with a false premise ("how do I enable option X?") gets "X was not found", where you looked (docs for that
  version, `--help`, the settings listing such as `SHOW ALL` / `pg_settings` for PostgreSQL), and what real feature might be
  meant. Do not bend the answer to fit the premise.
- Warning signs of fabrication: a very specific name you have not seen in any file or source; numbers without a calculation
  or source; an answer that fits a doubtful question too neatly; repeated fixes for the same problem in one session.

## 3. Always check these
Versions and compatibility; API, method and option names; CLI flags; package names; repository paths and file names;
numbers (ports, limits, prices and discounts, error codes, CVE and RFC ids, article numbers); dates and deadlines; quotes and who said them;
output of commands you did not run; behaviour of code you did not read; arithmetic in estimates (show the calculation and
compute it with a command). How to check each: `references/checking.md`.

**Counts and exclusivity in code** ("called in exactly 4 places", "only from module billing", "the interface has 54
methods"): models count poorly and readers trust confident numbers. Verify each with a structural tool (ast-grep
`ast-grep -p '<pattern>' -l <lang> --json`, LSP find-references, the compiler) and give the verdict - confirmed, corrected
or refuted - with `file:line`. Confirm every zero result with a plain text search `rg -n '<text>'`: zero may mean a wrong
pattern. Fix numbers in place with a trace ("150 (report: 145)").

**A tool's output is a claim too.** Before copying a number from a script or analyser, open the largest item (biggest cycle,
biggest hub) and one random item, and read the producing `file:line`. Factory measurement 2026-10-18: a draft script
reported a 242-file runtime import cycle that was really closed by type-only imports; every agent that used it repeated the
error, the agent without the script counted correctly.

## 4. Long documents: quotes first, sources only
- First list the literal quotes, with their location (page, section, `file:line`), that answer the question. Then draw
  conclusions only from those quotes. A conclusion without a quote is withdrawn or marked `[assumption]`.
- Text for others (a summary for a client or board): for each claim find the supporting quote; remove claims without one and
  leave a visible gap marker `[]` so the reader sees what was cut. End with the gaps: what the document does not say.
- **Sources-only mode** (regulations, contracts, requirements, interview notes): general knowledge serves only to understand
  the question, never as the source of a claim. The factory switches it on for roles with `grounding: sources-only` in
  `.tf/config/config.yaml` (`sources_only_note`); pack-it ddd-discovery-intake applies the same pattern to interviews.
- No document attached -> say so and ask for it; do not summarise from the title.

## 5. Context hygiene
- One task per context; `/clear` for an unrelated task; resume from a checkpoint (core-project-record) rather than a long
  history; exploration goes to a subagent (`scout`, `Explore`) that returns a short report; load only the skill sections you need.
- Two failed fixes of the same thing -> stop. Record in the checkpoint what does not work and why, and restart with a better
  instruction instead of a third patch.
- Signs that a context is worn out: findings repeated as if new, paths or commands that do not exist, an agreed constraint
  broken, patches around the same failing test, summaries growing while decisions shrink. When you see them: save the checkpoint
  first, then choose - `/compact` (direction is right, history is heavy), `/rewind` (undo the last wrong step), `/clear` (the
  task is done), or a new session started from the checkpoint. Fix the cause, not the symptom.
- Decisions and findings are on disk before any compaction. Compaction instruction: keep decisions, file paths, commands run
  with results, test status, constraints, open risks, one next step; drop failed attempts, repeated logs, abandoned hypotheses.
- Memory (`~/.claude/projects/<project>/memory/`, `MEMORY.md` - the first 200 lines or 25 KB load) and earlier artifacts are
  claims dated when written: verify in code before relying on them and correct stale notes openly. Rules binding the team live
  in the repository (core-agent-instructions), not in memory.
- The `context_guard` hook warns at 100k and 150k tokens (`CLAUDE_CONTEXT_WARN_K`, 0 disables). Response: write the
  checkpoint, propose a new session or `/compact` with the instruction above.

## 6. Self-check before hand-over
1. List the factual claims in what you hand over; give each the evidence its kind needs (check / mark / remove). State claims
   come with command and output, `file:line`, or a dated source.
2. References in documents:
   `python3 .claude/skills/core-grounding/scripts/grounding_check.py <file.md|dir> [--warn] [--jev]` - checks paths in code
   spans, `file:line` and `file:line-line` (reports "the file has N lines" when the line does not exist) and local links; skips
   code blocks, URLs, patterns and paths marked "(planned)", "(new)", "(to be created)", "[plan]". Exit 1 on problems; `--warn`
   only reports. `--jev` (needs `TYPESAFE_API_KEY`) also asks whether the cited lines confirm the sentence; below 0.8 confidence
   the item goes to human review. Fix contradicting or non-confirming references.
3. Numbers and dates:
   `python3 .claude/skills/core-grounding/scripts/claims_check.py <file.md|dir> [--strict]` - first line
   `Verdict: OK | WARNINGS | ERRORS` with counts. Errors: a percentage that does not match its `X/Y (Z%)` fraction (45/56 is
   80%, not 85%), an impossible date, an as-of / accessed / measured date in the future. Warnings: a number with a unit on a
   prose line without a trace of origin (a command or path in backticks, a link, `file:line`, "source", "according to",
   `[assumption]`, `[unverified]`, a footnote); one data declaration such as "Data: `path`" covers the whole document. Exit 1 on
   errors (with `--strict` also on warnings).
4. In AI-written diffs look for: code that is valid but semantically wrong (a lost transaction, retry or edge case), tests
   that pin the implementation instead of behaviour, and an earlier decision from the conversation silently overridden.
5. Important decisions get an independent check (`security-reviewer`, `/code-review`, a second executor); authors do not grade
   their own work. For an irreversible decision without a checkable source, ask the same question 2-3 times independently:
   disagreement signals invention; keep only claims that repeat and have evidence. Cheaper: have the answer checked claim by claim.

## Example
Question: "Does PostgreSQL 17 have `auto_index_advisor = on`, and how do I enable it?"

```
I don't know of such a setting, and I could not confirm it: it is not in the PostgreSQL 17 configuration
reference [checked: docs for version 17, "Server Configuration"]. Check on your server:
  SHOW ALL;  or  SELECT name FROM pg_settings WHERE name LIKE '%index%';
If it is absent, it is not a built-in option. What may be meant: the hypopg extension or an external
index-advisor tool [unverified] - confirm in its own docs before planning anything.
```

## Sources
- Anthropic, "Reduce hallucinations", platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations - accessed 2026-11-20 (allow "I don't know", quotes first, verify with citations, restrict to provided material, repeated runs).
- Claude Code docs, "Best practices for Claude Code", code.claude.com/docs/en/best-practices - accessed 2026-11-20 (a full context lowers quality, `/clear`, subagents, verify rather than declare).
- Claude Code docs, "How Claude remembers your project", code.claude.com/docs/en/memory - accessed 2026-11-20 (memory files, 200 lines / 25 KB).
- `ast-grep run --help` (ast-grep 0.50.0) - accessed 2026-10-10.
- Factory measurement 2026-10-18 (import-cycle script).
