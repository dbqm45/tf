# Production ready — the definition and the readiness review

In phase 7 the review is done by DevOps/SRE with the security-reviewer and the test designer (pack-it: Piotr and Kasia;
a domain pack: its operations and test personas). The result is recorded in `docs/project/07-review/<data>-readiness.md`
(the `review` artifact) and presented to the human at gate B4. Every point has one of three states: **met** (with
evidence: a link to a test, a report, a file, a command output), **not met** or **risk accepted** (who accepted it and by
when to fix it). Points marked *(minimum)* apply also on the shortened path.

Evidence is the result of a check, not a declaration. "The tests pass" without a link to the CI run is an assumption,
not evidence.

In brackets at the points: the area of knowledge and an example skill from a pack (named). When that pack is not
installed, you find the equivalent in `.claude/catalog.md` or ask a consultant from another pack.

## 1. Features and quality
- [ ] *(minimum)* All requirements with the "must" priority delivered. Acceptance criteria covered by tests, with a
  requirement → test map (test design; pack-it: qa-test-design).
- [ ] *(minimum)* Unit, integration and end-to-end tests of the critical paths pass in CI on the release branch.
- [ ] Regression tests and exploratory sessions for the risk areas (pack-it: qa-regression, qa-exploratory-manual);
  known defects classified, none critical open.
- [ ] Accessibility of the key paths checked (pack-it: fe-web-platform; pack-ux: ux-accessibility) and UX decisions
  confirmed by a usability test or explicitly postponed (pack-ux: ux-feature-design).

## 2. Security
- [ ] *(minimum)* A security review (security-reviewer) without open high and critical findings; the threat model
  current (pack-it: arch-threat-modeling).
- [ ] *(minimum)* Secrets only in a secrets manager or environment variables, nothing in the repository or the images
  (pack-it: ops-secrets-identities); a secrets scan in CI.
- [ ] Authentication and authorization tested, including access to other users' resources (OWASP API1; pack-it: be-auth-security).
- [ ] A scan of dependencies and images, an SBOM, signed artifacts, pinned versions (pack-it: ops-supply-chain-security).
- [ ] Security headers, TLS, request and size limits, input validation (pack-it: be-api-design; be-auth-security,
  `api-security-checklist.md` in pack-it).

## 3. Performance and capacity
- [ ] Targets from the quality requirements (e.g. p95, throughput) confirmed by a load test in an environment close to
  production (pack-it: qa-performance-testing), with a report.
- [ ] A capacity estimate for the start and for growth; autoscaling limits and connection pools chosen (pack-it: arch-system-design).

## 4. Observability and on-call
- [ ] *(minimum)* Structured logs without sensitive data, RED/USE metrics, health checks (pack-it: ops-observability).
- [ ] *(minimum)* SLOs for the critical paths and alerts on the error budget; an alert leads to a runbook (pack-it: ops-sre-incidents).
- [ ] Distributed traces for paths through several services; a release dashboard (version, errors, latency).
- [ ] It is known who receives alerts and how they escalate (a human, not an agent).

## 5. Release and rollback
- [ ] *(minimum)* A repeatable deployment from the pipeline, an artifact built once and promoted between environments
  (pack-it: ops-ci-cd, eng-continuous-delivery).
- [ ] *(minimum)* The rollback described and **rehearsed** in the test environment, with its duration (pack-it: ops-release-engineering).
- [ ] A gradual strategy (canary, blue-green, flags) with SLO-based gates; database migrations backward compatible
  (expand → migrate → contract; pack-it: be-database).
- [ ] Infrastructure as code, without manual changes; drift detection.

## 6. Data
- [ ] *(minimum)* Automatic backups and **a tested restore**, with an RPO and an RTO matching the requirements
  (pack-it: ops-sre-incidents).
- [ ] Retention and deletion of personal data per the human's decision (GDPR); test data without production data.

## 7. Documentation and handover
- [ ] *(minimum)* A README with running locally, configuration and environment variables (pack-docs: docs-tech-writing).
- [ ] *(minimum)* A runbook: deployment, rollback, typical failures, contacts.
- [ ] The architecture document and ADRs current with the code; the project record with a report (`project_record.py report`).
- [ ] Texts for users and documentation after language correction (pack-editorial-pl: txt-polish-correctness).

## 8. Cost and compliance
- [ ] A monthly cost estimate, budgets and cost alerts, resource tags (pack-it: ops-finops).
- [ ] Legal and contractual requirements confirmed by the human (GDPR, industry regulations, the AI Act, dependency
  licences). The agent collects the facts and a list of questions, the human decides (pack-it: ops-security-operations,
  `compliance.md`).

## Verdict
At the end of the artifact: **ready / ready with accepted risks / not ready**, the list of unmet points with an owner
and a deadline, and a recommendation of the release strategy. The human makes the "we release" decision at B4.

## Sources
- Google SRE Book and SRE Workbook — Production Readiness Review, launch checklist
- Lists from pack-it: the backend and frontend performance checklist, the API security checklist, ops-release-engineering
Described in our own words.
