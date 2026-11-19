---
name: sec-variant-analysis
description: Use after finding a vulnerability, to find its variants in the code — cause, source→sink pattern, grep/Semgrep/CodeQL, hit triage, a CI rule.
metadata:
  review: "2027-10-23"
  catalog: "Use when one vulnerability has been found (pentest, report, incident, review) and you must check whether the same bug occurs elsewhere — in this repository or in many of the company's repositories: cause and class (CWE), generalization to a source → sink pattern at several levels, search from the cheapest (grep, Semgrep, CodeQL, including many repositories at once), triage of every hit with reachability and exposure, a fix at the root through a shared safe API, a rule with tests in CI blocking new occurrences, a report with numbers. Not for the scanner program and fix deadlines (sec-appsec-devsecops), the threat model (arch-threat-modeling), incident handling (ops-security-operations) or analysis of a suspicious file (sec-malware-analysis)."
  keywords: "analiza wariantów, variant analysis, gdzie jeszcze jest ten błąd, ten sam błąd w innych miejscach, podobne podatności, znaleźliśmy podatność, pentester znalazł, po incydencie sprawdzić resztę kodu, wszystkie repozytoria, reguła semgrep na ten błąd, zapytanie codeql, źródło i ujście, taint, przepływ danych, sql injection w innych miejscach, deserializacja w innych usługach, where else is this bug, the same bug in other places, similar vulnerabilities, we found a vulnerability, a pentester found, check the rest of the code after an incident, all repositories, semgrep rule for this bug, codeql query, source and sink, data flow, sql injection in other places, deserialization in other services"
---

# Vulnerability variant analysis

Goal: one vulnerability found turns into **all** of its occurrences found and into a rule that will not
let the next ones in. Fixing only the reported place usually leaves the bug's siblings in the code. Only in code
that is yours or for which you have permission (core-agent-security).

## Procedure
1. **Understand the bug found**: where the untrusted data comes from (source), where it does harm (sink), which
   control is missing (validation, parameterization, authorization), what the exploitation condition is. Name the CWE class
   (e.g. CWE-89 SQL injection, CWE-502 deserialization of untrusted data).
2. **Generalize to a pattern** at three levels, from narrow to broad:
   - **the same code** — the same call, copied fragments, the same helper function;
   - **the same sink** — every place where input data reaches this sink by another path;
   - **the same class** — other sinks of the same category (e.g. every SQL concatenation, every `ORDER BY` from input,
     every deserialization of a format with types).
3. **Search from the cheapest**: grep/ripgrep for sink and function names → Semgrep (a syntactic pattern, taint mode
   with sources, sinks and sanitizers) → CodeQL (data flow between functions and files). Record every
   query and the number of hits — too many hits is a signal to narrow down, zero with a broad pattern — a reason to
   check whether the pattern works at all (run it on a known, fixed place in the git history).
4. **Scope**: other repositories (shared libraries, copied code, project templates), old release branches
   supported by the company. Many repositories: the same script and rules across all clones, or analysis of many
   repositories at once in CodeQL. The list of repositories and versions — from a human.
5. **Triage of every hit**: is the data reachable from untrusted input, is there a control on the way, what is
   the exposure of the service (internet, internal network, administrator only). Result: true / false /
   uncertain, with `file:line` and a justification. Uncertain ones are checked by a human or a test.
6. **Fix at the root**: one safe API or helper function (e.g. an allowlist of sort fields,
   a safe deserializer) instead of a patch in every place; the order of fixes and the deadlines according to
   sec-appsec-devsecops (`.claude/skills/sec-appsec-devsecops/references/triage-and-sla.md`).
7. **Prevention**: a rule (Semgrep or CodeQL) with tests — a vulnerable and a correct example — in CI on the PR diff,
   blocking new occurrences; template in `references/rule-with-tests.md`, rule craft (precision, autofix,
   CodeQL tests) — tool-semgrep. The lesson in `docs/project/lessons.md`.
8. **Report**: class and pattern, queries, numbers (hits / true / false / uncertain), a list with
   `file:line`, fixes and rules, what was not checked.

## Example
Pentest: SQL injection in `/reports` — the `sort` parameter went into an `ORDER BY` concatenated from a string (CWE-89).
Pattern: request data → a column name or direction in SQL (parameterization does not work here, an allowlist
of values is needed). Search: `rg -n "ORDER BY|order_by\(|\.extra\(|\.raw\("` → 41 hits; a Semgrep rule
in taint mode (source: request parameters, sink: `cursor.execute`, `raw`, `extra`) → 12; triage → 3 true
(`/reports`, `/invoices/export`, `/admin/users`), 8 false (constants), 1 uncertain (data from a queue). Fix:
the function `sort_clause(field, direction)` with an allowlist of fields, used in 4 places. The rule with tests in CI
blocks new cases; the same rules run in 2 other repositories — 1 hit, true.

## Sources
- MITRE CWE, cwe.mitre.org — weakness classes (accessed 2026-10-23).
- Semgrep, documentation: taint mode and rule testing (`semgrep --test`), semgrep.dev/docs (accessed 2026-10-23).
- GitHub, CodeQL documentation: data flow queries and variant analysis across many repositories,
  docs.github.com/code-security/codeql-for-vs-code (accessed 2026-10-23).
- Topic inspiration: Trail of Bits, skill `variant-analysis` (CC BY-SA 4.0 licence — no content was taken over).
Described in our own words.
