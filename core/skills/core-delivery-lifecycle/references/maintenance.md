# Phase 9 — retiring features and the end of life of the system

A supplement to the "Phase 9 — maintenance" section in SKILL.md. The human makes both decisions; the agent prepares
the data and the plan.

## Retiring features
- The human's decision based on usage data (the maintenance review, gate B6).
- An announcement with a date and a transition period for users and integrations.
- A version per SemVer (core-semver): marking as deprecated in a MINOR, removal in a MAJOR.
- Removing the code and the data per the retention policy (privacy; pack-it: arch-privacy-compliance).

## The end of life of the system
A shutdown plan as a separate mini-project with gates B1 and B5:
- **data:** export, archive or deletion;
- **users:** a message and a deadline;
- **infrastructure:** decommissioning the resources and the costs (cloud costs; pack-it: ops-finops).
