---
name: sec-detection-engineering
description: Use for designing and testing detection rules — Sigma as code, ATT&CK coverage, alert quality, purple team, threat hunting.
metadata:
  review: "2027-04-17"
  catalog: "Use when you must design, write, test and maintain attack detection — the rule lifecycle (hypothesis, data source, rule, simulation test, deployment, tuning, retirement), detection-as-code (Sigma, repo, CI), a MITRE ATT&CK coverage map and gap analysis, alert quality (precision, noise budget, context, runbook), purple team exercises (Atomic Red Team, Caldera), threat hunting basics, metrics (time to detect, coverage, false positives). Not for operating the SIEM, EDR, SOAR and incident response (ops-security-operations), general application alerts (ops-observability), a feature threat model (arch-threat-modeling) or malware sample analysis (sec-malware-analysis)."
  keywords: "reguła wykrywania, detection engineering, detection as code, Sigma, pokrycie ATT&CK, MITRE ATT&CK, Navigator, luki w wykrywaniu, fałszywe alarmy, zmęczenie alertami, strojenie reguł, purple team, red team, emulacja przeciwnika, Atomic Red Team, Caldera, threat hunting, polowanie na zagrożenia, hipoteza, czas do wykrycia, MTTD, hunting, testy reguł, SIEM reguła, detection rule, ATT&CK coverage, detection gaps, false positives, alert fatigue, rule tuning, adversary emulation, hypothesis, time to detect, rule tests, SIEM rule"
---

# Detection engineering (purple team)

Boundary: **ops-security-operations** operates the SIEM, EDR, SOAR and incidents (telemetry, triage, response). This skill
concerns **designing and testing detection**: how we know that a rule catches a technique and that it can be maintained.
General outage alerts: ops-observability. What can go wrong in the project: arch-threat-modeling. Rules from analysing
a sample: sec-malware-analysis. Details, the rule template and metrics: `references/rules-and-metrics.md`.

## Procedure (the rule lifecycle)
1. **Hypothesis.** How we know it matters: a threat report, our own incident, an ATT&CK technique relevant to our industry
   and stack. Record: "If an attacker does [technique], we will see [an observable trace] in [the source]".
2. **Data source.** Does the telemetry exist, is it complete and parsed (fields, latency, retention)? Without a source
   the rule is a decoration; the result of this step is sometimes a "turn on logging" task, not a rule.
3. **Rule.** The Sigma format (below), one rule per behaviour; the condition on the behaviour, not on the tool name.
   Record the known false positives (`falsepositives`) and the level (`level`).
4. **Test.** Positive: a simulation of the technique in a lab or on staging (Atomic Red Team) or recorded events —
   the alert must appear. Negative: events from normal work from the last few days — there should be few alerts.
5. **Deployment** through a PR and CI; first observation mode (without paging the on-call), then production.
6. **Tuning.** You add exceptions for known good behaviours narrowly (account, path, host), you do not weaken the condition.
7. **Retirement.** A rule with no hits and no test for a quarter, or constantly ignored → fix, merge or remove it (`status: deprecated`).

## Detection-as-code (Sigma)
- Sigma is an open, vendor-independent rule format in YAML. Required fields: `title`, `logsource`, `detection`
  with `condition`. Recommended: `id` (UUID), `status`, `description`, `references`, `author`, `date`, `tags`
  (e.g. `attack.t1059.001`), `falsepositives`, `level`. The values of `status` and `level` — `references/rules-and-metrics.md`.
- Repository: rules in directories by source, review in a PR, an owner, the change history as a decision log.
- CI: (1) syntax and schema validation, (2) conversion to the target SIEM query (pySigma, `sigma convert`;
  a field-mapping pipeline), (3) a test on positive and negative events, (4) a check of mandatory fields
  (`id`, `level`, `falsepositives`, an ATT&CK tag). A red test blocks the merge.
- Correlation rules (many events over time) are described by a separate Sigma specification; start with single rules.

## ATT&CK coverage and gap analysis
1. Collect the `attack.tNNNN` tags from the rules and generate an ATT&CK Navigator layer.
2. Separate three states of a technique: **no telemetry**, **telemetry without a rule**, **a tested rule**.
   The mere presence of a rule with a tag is not coverage; an untested rule counts as "unconfirmed".
3. Gap priority: techniques used by groups attacking our industry (threat intelligence), our stack and assets,
   the cost of detection; do not aim for a 100% map (pointless and not cost-effective).
4. State the ATT&CK version in the layer and in the report; the matrix changes twice a year, and identifiers are sometimes replaced.

## Alert quality
An alert has: severity, context (host, account, command, parent process), triage steps and **a link to the runbook**, an owner.
- **Precision** = true alarms / all alarms; measure per rule. **Noise budget**: set how many alerts per analyst
  per shift are bearable [example: 20], and a new rule must fit within it or replace another one.
- A rule with precision below the threshold agreed with the SOC goes to tuning or turns into a hunt (without an alert).

## Purple team
A joint exercise of offence and defence: we execute a technique, check whether the alert appeared, and fix it.
- **Only with the written consent of the systems' owner, within an agreed scope** (targets, a time window, an emergency contact,
  a ban on damage); preferably a lab or staging. The SOC team knows about the exercise or has rules for recognizing the simulation.
- The emulation plan: a list of ATT&CK techniques for the chosen adversary, for each: the expected trace, the expected alert,
  the cleanup method. Tools: Atomic Red Team (small tests per technique, with a cleanup step), MITRE Caldera (an emulation
  platform; use version ≥ 5.1.0 after the CVE-2025-27364 patch, do not expose it to the internet).
- The result per technique: detected / logged without an alert / no trace → tasks: telemetry, rule, tuning.
  Repeat the test after the fix (regression).

## Threat hunting (basics)
Hunting is driven by a hypothesis, not by an alert: a question, a query, analysis of the results (the long tail, rare values,
anomalies against a baseline). The result: a finding (→ an incident, ops-security-operations), a new rule from step 3
of the procedure or a telemetry gap. Record the hypothesis, the query, the time range and the result, including a negative one.

## Metrics
Time to detect (from executing the technique in a test to the alert), coverage tested techniques / priority techniques,
the false positive rate, the share of rules with a test and a runbook, the age of rules without review. Metrics are a direction, not a goal
in themselves (do not reward the number of rules).

## Example
**Input:** "A report on a group attacking our industry describes launching PowerShell with an encoded command (T1059.001)."
**Result** (a fragment of the rule card): hypothesis: `powershell.exe` with `-enc` launched by an Office process; source: process
creation events with the command line (checked: present on workstations, missing on servers → a telemetry task); positive
test: atomic T1059.001 on a lab machine, alert after [example: 40 s]; negative test: 7 days of events,
[example: 3 hits, all from the inventory tool → an exception by path]; `level: high`, `falsepositives`
filled in, runbook linked, tag `attack.t1059.001`.

## Checklist
- [ ] a hypothesis with an ATT&CK technique and a checked data source
- [ ] a Sigma rule with `id`, `level`, `falsepositives`, a tag; in the repo, through a PR
- [ ] a positive test (simulation) and a negative one (normal traffic) in CI
- [ ] an alert with context and a runbook; precision measured
- [ ] coverage distinguishing "a rule exists" from "tested"; the ATT&CK version stated
- [ ] purple team only with consent, within scope, with cleanup

## Sources
- [Sigma Rules Specification 2.1.0](https://github.com/SigmaHQ/sigma-specification) (read 2026-10-17); [pySigma and sigma-cli](https://github.com/SigmaHQ/pySigma)
- [MITRE ATT&CK, STIX data releases](https://github.com/mitre-attack/attack-stix-data/releases): v20.0 (read 2026-10-17, release year [unverified])
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) (MIT); [MITRE Caldera](https://github.com/mitre/caldera) (Apache-2.0; ≥ 5.1.0 after CVE-2025-27364), read 2026-10-17
Described in our own words.
