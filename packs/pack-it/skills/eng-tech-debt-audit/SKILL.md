---
name: eng-tech-debt-audit
description: Use when auditing the technical debt of a repo or module — hotspots, nine dimensions, findings with file:line, priority by change frequency, repeat audits.
metadata:
  review: "2027-10-09"
  catalog: "Use when you audit the technical debt of a repository or module so the team can act on it — orientation by size × change frequency (hotspots, co-changes), nine debt dimensions, findings with file:line, weight, effort and a proposal, a computed priority, quick wins, a mandatory 'looks bad, but is fine' section, cheap versus dangerous coupling named by connascence, cycles without madge (code_graph.py), a repeat audit with ROZWIĄZANE/NOWE/ZMIENIONE statuses, and an ongoing architecture-hygiene routine (architecture tests, a ratchet, weekly small PRs, protected verifiers). The audit only proposes and rewrites nothing. Not for a single refactoring (eng-behavior-preserving-refactoring) or the review of one PR (eng-design-principles)"
  keywords: "audyt długu technicznego, dług techniczny, dług w module, ranking długu, uszeregować ustalenia, priorytet długu, 60 ustaleń, kod którego nikt nie dotyka, częstość zmian, hotspoty, gorące punkty, współzmiany, sprzężenie, groźne sprzężenie, tani dług, kod generowany, connascence, raport z audytu długu, porównanie audytów, ponowny audyt, szybkie wygrane, wygląda źle ale jest dobrze, cykle importów, łamanie warstw, rozpad architektury, bez madge, nie mogę nic instalować, pliki po 2000 linii, audyt raz na kwartał nic nie daje, testy architektury, zapadka, ratchet, rutyna porządkowania architektury, znaczniki debt:, tech debt audit, technical debt, rank debt findings, change frequency, hotspots, co-change, cheap vs dangerous coupling, generated code, debt report, repeat audit, quick wins, looks bad but is fine, import cycles, layer violations, architecture decay, architecture tests, ratchet, debt markers"
---

# Technical debt audit — findings the team can act on

An audit is useful when the team can pick the first three items on Monday and a later audit can say what changed.
So every finding has a location, a weight, an effort and a proposal; the order comes from a formula, not from taste;
and the report says what looks bad but is fine. **The audit only proposes — it rewrites nothing.** If you are asked to
fix the findings in the same run, finish the report and hand the choice to eng-refactor-planning.

## 1. Orientation (before any assessment)
1. Read README, manifests, ADRs and the module map.
2. History: `git log --oneline -200`, `git log --since=6.months --stat`.
3. **Hotspots = complexity × change frequency.** Run
   `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --cochange` (do not re-implement it).
   Each factor alone misleads: a dense file nobody touches is merely old; a trivial file changed weekly is usually
   config. Use one cheap complexity proxy uniformly (non-blank lines, indentation depth) — the product matters more
   than the proxy.
4. **Co-changes, read two ways:** a tight pair of files that always change together = a hidden contract (a candidate
   for connascence of meaning or algorithm); a hub that changes with many areas = wide reach. Co-changes mislead in both
   directions: bulk commits glue unrelated files, and missing co-change does not prove independence — e.g. an order
   DTO copied by hand into the API and the mobile client never changes in the same commit, and that silent copy is
   exactly the debt to inspect.
5. Write a 1–2 paragraph architecture model; a discrepancy with the README is itself a finding.
6. Show the audit plan (scope, modules, tools) to the human before starting. Run only tools the project already has
   or the human approves — no global installs.

## 2. Assessment — nine dimensions
| Dimension | What to look for | Tools (when present) |
|---|---|---|
| architecture decay | cycles, broken layers and module boundaries, files > 500 lines, logic duplicated in 3+ places, unused abstractions, dead code | `madge --circular`, dependency-cruiser, `nx graph` + module-boundary lint, `jdeps`, ArchUnit, `knip`; without them `code_graph.py` |
| inconsistency | several ways of doing the same thing: HTTP clients, state, errors, naming | grep, reading |
| types and contracts | `any`, casts, unvalidated boundaries, APIs without a schema | `tsc --noEmit` with strict |
| tests | often-changed files without tests, tests coupled to implementation, flaky tests | coverage, CI history (qa-regression) |
| dependencies and configuration | known CVEs, unused packages, env variable sprawl | `npm audit`, `depcheck`, OWASP dependency-check (ops-supply-chain-security) |
| performance | N+1 queries, blocking I/O, needless rendering | be-database, fe-architecture |
| errors and observability | swallowed exceptions, no logs or metrics on critical paths | ops-observability |
| security | secrets in code, missing per-resource authorization, dangerous patterns | be-auth-security |
| documentation | README and ADRs out of date with the code | docs-tech-writing |

A dimension with no findings says **"nothing significant"** — never invent debt to fill the table.

Cycles without madge or dependency-cruiser (e.g. Django + TypeScript, nothing installable):
`python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py <repo>`. It separates **runtime** cycles (module-level
imports) from cycles closed only by lazy edges — an import inside a function, under `TYPE_CHECKING`, or a type-only
import. Runtime cycles are the finding; lazy-only cycles are a weaker signal.

## 3. Weight, effort, priority
- **Weight** by effect: critical 4 (data loss, security, outage), high 3, medium 2, low 1 (slows the team a little).
- **Effort:** S = hours (1), M = days (2), L = weeks (4).
- **Priority = weight × change frequency ÷ effort**, where change frequency = commits touching the file in the last
  6 months (minimum 1). Examples: a high finding (3) in a file changed 25 times, effort M (2) → 3×25/2 = **37.5**;
  a critical finding (4) in a file changed 6 times, effort S (1) → 4×6/1 = **24**. Debt in code nobody touches can wait.
- **Quick wins** = effort S with weight ≥ medium.
- **Cheap vs dangerous coupling.** Mechanical coupling caught by a tool — generated code refreshed by regeneration,
  drift the compiler or CI catches — has weight at most low. Dangerous is dynamic coupling without a tool barrier:
  order of calls, meaning of values shared at a distance, a copied algorithm. Name the kind of connascence (name, type,
  meaning, position, algorithm, order, timing) instead of saying "tightly coupled".
- An auxiliary label: the debt quadrant (deliberate/inadvertent × prudent/reckless, after Fowler). Pay the highest-interest
  debt first.

## 4. The report
Path `docs/project/07-review/<date>-tech-debt.md` (e.g. `2026-10-04-tech-debt.md`). Parts:
1. Summary (≤ 10 points) and the architecture model.
2. Findings table: ID, dimension, file:line, weight, effort, priority, description, proposal — sorted by priority.
3. Top 5 with a sketch of the change.
4. Quick wins.
5. **"Looks bad, but is fine"** (mandatory): deliberate choices with evidence — an ADR, `git log -L :<function>:<file>`,
   `git blame`, a PR description, the number of fixes to the mechanism (e.g. 0 in 6 years). The risk of a deliberate
   limitation is closed with a cheap guard (a test, a linter rule), not a rebuild. Mark it "do not touch".
6. Questions for the team where context is missing.

Markers in code: `debt: <limitation>, <when to come back>`. The audit collects them into the table; a marker without a
return condition is a separate finding. Worked report: `references/examples.md`.

## 5. Scale and repeat audits
- More than ~50k lines or more than 5 modules → one executor per module with the same procedure (core-async-delegation),
  then merge into one table with a shared ranking.
- **A repeat audit** compares with the previous report and marks every finding **ROZWIĄZANE** (resolved), **NOWE** (new)
  or **ZMIENIONE** (changed — weight, scope or location moved). Unchanged findings keep their IDs.

## 6. Architecture hygiene routine
A quarterly audit alone does not stop decay when agents add code every day. Turn it into a loop:
1. **Architecture tests** for layers, cycles and file size (import-linter, dependency-cruiser, ArchUnit, Tach) in the
   fast local gates and CI; the agent runs them before saying "done".
2. **A ratchet:** each threshold starts at today's maximum (e.g. the largest file, the current cycle count) and only
   goes down; exceptions are listed by name, with an owner and a deadline, and the list only shrinks.
3. **A weekly cadence:** one violation → one small refactoring PR reviewed by a human (eng-refactor-planning for the
   bigger ones).
4. **Protected verifiers:** thresholds, exception lists and architecture tests live in paths guarded by CODEOWNERS and
   branch protection — an agent optimising for green CI will otherwise move the verifier instead of fixing the code.

## Example
Request: "60 findings in a monolith, how do I rank them without fixing code nobody touches?" Answer: compute change
frequency per file from `git log --since=6.months` (git_territory.py), weight 1–4 and effort S/M/L for each finding, then
priority = weight × frequency ÷ effort; a medium (2) finding in an untouched file with effort L scores 2×1/4 = 0.5
and waits, while a high (3) finding in a file changed 25 times with effort M scores 37.5 and leads. Pull quick wins
(S, weight ≥ medium) into their own list; record deliberate oddities under "looks bad, but is fine".

## Checklist
- [ ] orientation done and the plan shown before assessment; only approved tools
- [ ] every finding: file:line, weight, effort, priority from the formula, proposal
- [ ] empty dimensions say "nothing significant"; coupling named by connascence kind
- [ ] "looks bad, but is fine" present, with evidence
- [ ] repeat audit: ROZWIĄZANE / NOWE / ZMIENIONE; `debt:` markers collected
- [ ] nothing rewritten; refactoring choice handed to eng-refactor-planning

## Sources
- `git log -L` and `git blame` (git-scm.com/docs, accessed 2026-10-09).
- madge, dependency-cruiser, knip, import-linter, Tach, ArchUnit — project documentation (accessed 2026-10-09).
- M. Fowler, "TechnicalDebtQuadrant" (martinfowler.com, 2009).
- Connascence vocabulary: M. Page-Jones; connascence.io (accessed 2026-10-09).
- Sources of inspiration: GitHub `ksimback/tech-debt-skill` (orientation, dimensions, the deliberate-things section,
  per-module split, repeat audit) and `DietrichGebert/ponytail` (`debt:` markers), accessed 2026-10-09.
