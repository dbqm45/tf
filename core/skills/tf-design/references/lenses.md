# Lenses — several perspectives, one pass

Apply them yourself on stages that decide structure (options, the chosen option in detail, edge cases). Report only
the lenses that found something, one line each, labelled [risk] or [recommendation]. A deep finding (security boundary,
data model) → hand that one question to the `architect` or `security-reviewer` subagent, not all lenses.
A real debate between roles that must answer each other → propose `/team-session` (mode-team) and its cost; never by default.

| Lens | Asks |
|---|---|
| Architect | Is the boundary in the right place? What is costly to reverse? Which option keeps the most doors open for its cost? |
| Senior Developer | Is there a simpler shape? What will be hard to read or change in six months? Does it fit the existing code style and modules? |
| QA | How do we know it works — which acceptance criterion can a test check? Edge cases with real probability: empty, duplicate, concurrent, large? |
| Security | Who can do what, and what if they are not who they claim? Input from outside? Secrets, personal data, audit trail? |
| Product Owner | Which user problem does it solve, and what is the smallest version that does? What can wait? |
| DevOps | How is it deployed, migrated and rolled back? What do we monitor? What does it cost to run? |

Proportion: an unlikely edge case gets "fail with a clear error", not a design. A finding outside the subject →
`parked.md` or one sentence to the developer.
