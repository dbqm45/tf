# Vulnerability triage and SLA

## Signals
- **CVSS v4.0** (FIRST, November 2023): technical severity; it is not backward compatible with v3.1, so do not compare
  scores from different versions. The names of the metric groups (Base, Threat, Environmental, Supplemental) [unverified
  in this session, from memory]. CVSS-B (the base alone) overstates risk; add knowledge of the threat and the environment.
- **EPSS** (FIRST): the probability of exploitation within 30 days, refreshed daily. A statistical estimate,
  not proof.
- **CISA KEV**: a catalog of vulnerabilities confirmed as exploited; this is the strongest urgency signal.
- **Reachability**: whether the vulnerable code is called, whether the service is exposed, whether a compensating control works (VEX/
  "not affected" with a justification).

## Priority rule
1. In KEV or with a working exploit and the service reachable from the internet → P0.
2. High EPSS (e.g. > 0.1 [example threshold]) or CVSS ≥ 9 and reachable → P1.
3. CVSS 7–8.9 reachable or critical unreachable → P2.
4. The rest → P3 in the cycle, unreachable ones can be closed with VEX.

## SLA table [example, agree with the risk owner]
| Priority | Deadline for a fix or a compensating control |
|---|---|
| P0 | 48 hours (mitigation), full fix 7 days |
| P1 | 14 days |
| P2 | 30–60 days |
| P3 | 90 days or the release cycle |
Missing the deadline = escalation to the product owner; an exception requires human approval, a justification, a compensating
control and an expiry date. Applying the patch in production: `ops-security-operations`.

## A finding in a ticket (fields)
ID, source (tool, rule), component and version, base severity, KEV (yes/no), EPSS, reachability with evidence,
owner, deadline, status (new / confirmed / false / exception / fixed), closure date.
Mark false positives in the tool with a reason, so they do not come back.
