---
name: tool-semgrep
description: Use for custom Semgrep and CodeQL rules — patterns, taint, autofix, rule tests, false positives, CI.
metadata:
  review: "2027-01-24"
  catalog: "Use when writing, testing or fixing a custom Semgrep rule or a CodeQL query — rule syntax (pattern, patterns, pattern-either, pattern-inside, pattern-not, metavariables, metavariable-regex, focus-metavariable), taint mode (sources, sanitizers, sinks), autofix (fix:) with a fix test (.fixed), rule tests (ruleid:, ok:, todoruleid:, todook:, semgrep scan --test), reducing false positives (metavariable constraints, paths.exclude, ok: cases from real alarms), rules in CI (rule tests, --baseline-commit, --error), licenses of registry rules, CodeQL query tests (.qlref, .expected, codeql test run). Not for hunting variants of a found vulnerability (sec-variant-analysis), choosing scanners and thresholds in an AppSec program (sec-appsec-devsecops) or detection rules in a SIEM (sec-detection-engineering)."
  keywords: "semgrep, własna reguła semgrep, napisać regułę semgrep, reguła semgrep fałszywe trafienia, false positives semgrep, mode: taint, pattern-sources, pattern-sinks, pattern-sanitizers, pattern-not, pattern-inside, metavariable-regex, focus-metavariable, ruleid, todoruleid, semgrep --test, test reguły, autofix semgrep, fix:, .fixed, baseline-commit, .semgrepignore, opengrep, codeql test run, qlref, zapytanie codeql test, custom semgrep rule, write a semgrep rule, semgrep rule false positives, rule test, codeql query test"
---

# Semgrep — custom rules with tests

When to write a rule after a vulnerability is found: sec-variant-analysis. The scanner program and thresholds: sec-appsec-devsecops.
This skill is the craft of the rule: syntax, tests, precision, CI.

## Procedure
1. **The test first, then the rule.** A test file with the same base name as the rule (rule x.yaml, test x.py):
   vulnerable code with `# ruleid: <id>` above the matching line, correct code with `# ok: <id>`. The best examples are real
   code from before the fix and real false alarms. A known gap in the rule → `todoruleid:`, a known false alarm →
   `todook:` (the test passes, the debt is visible).
2. **The narrowest syntax that suffices**:
   - one call → `pattern`; several forms → `pattern-either`; joint conditions → `patterns`;
   - context → `pattern-inside` / `pattern-not-inside`; exceptions → `pattern-not`;
   - a condition on the content → `metavariable-regex` / `metavariable-pattern`; the reporting location → `focus-metavariable`;
   - data flows through variables and functions → `mode: taint` with sources, sinks and **sanitizers** (without them
     every correct path is an alarm).
   Full module names (`flask.request`, `subprocess.run`) — Semgrep resolves imports and aliases.
3. **The message says how to fix**, not only what is wrong; `metadata` with CWE and `confidence`. `severity: ERROR`
   only for rules that are meant to block a merge.
4. **Autofix** (`fix:` with metavariables) only for an unambiguous replacement; the fix test in the x.fixed.py file.
   On code, first `--autofix --dryrun`, changes go through review like any commit.
5. **Precision before rollout**: run the rule on the whole repository, review a sample of the matches and count
   the share of true ones. Every false alarm → an `ok:` case in the test → narrowing the rule (metavariable
   constraints, `pattern-not`, context). Test code and examples → `paths.exclude` in the rule or
   `.semgrepignore`. A blocking rule with many false alarms will be switched off — then `WARNING` or
   report-only until precision improves.
6. **CI**: rules in the repository (e.g. `.semgrep/`); first `semgrep scan --test` for the rules, then a PR scan
   with `--baseline-commit` (only new matches) and `--error` (exit code 1 on a match); the whole repository at night.
   `--metrics=off` when policy forbids telemetry.
7. **Licenses**: the Semgrep CE engine and the Opengrep fork — LGPL-2.1; registry rules (`semgrep/semgrep-rules`) have
   a separate license, "Semgrep Rules License v1.0" — before using it in a product or service, read its terms
   [unverified: the content of the terms, semgrep.dev not reachable from the session]. Your own rules are yours.

## CodeQL — query tests
When a variant requires full flow analysis across files, the rule is a CodeQL query (sec-variant-analysis,
step 3). Tests per the GitHub documentation: a separate test pack with a qlpack.yml file (`extractor: <language>`, a dependency on the
pack with the queries, `codeql pack install`), sample code in the test directory, a `.qlref` file with the query path
and `.expected` with the same base name. `codeql test run <directory>` builds a database from the examples, writes `.actual`
and shows the difference from `.expected`; a deliberately accepted result — `codeql test accept`. Not verified locally
(the CLI download was blocked in the session).

## Example
The rule `shell-injection-from-request` (taint: `request.args.get` → the first argument of `subprocess.run(...,
shell=True)`, sanitizer `shlex.quote`) with a test: two `ruleid`, two `ok`, one `todoruleid` (a value passed through a
helper object). `semgrep scan --test` passes; after removing the sanitizer the test fails on the line with
`shlex.quote` — proof that the test guards the rule. The code of this rule, of the `yaml.load` → `yaml.safe_load` autofix with the
.fixed.py file and of the password rule with `paths.exclude`: `references/rules-and-tests.md`.

## Version-dependent
The examples from `references/rules-and-tests.md` pass on 1.50.0, 1.100.0 and 1.182.1 (2026-10-24); the subcommand thresholds
were checked with `semgrep --help` of successive PyPI releases (1.99.0 without `test`, 1.149.0 without `mcp`). Releases weekly.
| Version | Changes relevant to this skill |
|---|---|
| 1.50 | `scan --test` with `ruleid`/`ok`/`todoruleid`/`todook` and `.fixed` fix tests, taint mode, `--baseline-commit` |
| 1.100 | the `semgrep test` subcommand (experimental, alongside `semgrep validate`); `scan --test` still works |
| 1.150 | the `semgrep mcp` subcommand (Semgrep's MCP server — evaluate before connecting: core-agent-security) |
A project with a version older than 1.50 → `PROJECT_OLDER`: check the examples with a test before using them.

## Checklist
- [ ] a rule test with `ruleid` and `ok` (including real false alarms), the test fails after the rule is broken
- [ ] taint has sanitizers; `focus-metavariable` points to the right place
- [ ] a message with the fix, CWE in `metadata`, `severity` consistent with whether the rule blocks
- [ ] precision measured on the repository before enabling blocking
- [ ] CI: rule tests, then a PR scan with `--baseline-commit` and `--error`

## Sources
- Semgrep 1.50.0, 1.100.0, 1.182.1 (PyPI) — examples, `--baseline-commit`, `--validate`, `todook` verified
  in operation 2026-10-24; `semgrep scan --help`.
- Licenses: `LICENSE` in `semgrep/semgrep`, `semgrep/semgrep-rules`, `opengrep/opengrep` (GitHub, read 2026-10-24).
- GitHub Docs, "Testing custom queries", "Query reference files", `codeql test accept` (github/docs, commit
  02c25d1, 2026-10-23).
- Inspiration for the topic: Trail of Bits `semgrep-rule-creator` — the content was not taken over.
Described in our own words.
