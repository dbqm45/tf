# Accessibility in the team — DoD, roles, training

Contents: 1. Definition of done · 2. Roles · 3. Training plan · 4. Metrics

## 1. Definition of done (DoD) of a component and a task
- Component: works with the keyboard alone, has an accessible name and role, contrasts from tokens, focus/error/disabled states, a test
  with a screen reader on one pair, annotations in the component documentation.
- Task: the acceptance criteria include the keyboard behaviour and the messages; automated checks in CI without new errors.
- Release: a checklist of the key paths; new findings go to the register with a severity.

## 2. Roles
| Role | Responsible for |
|---|---|
| Designer | contrast, hierarchy, annotations (headings, landmarks, focus order), touch targets |
| Content author | headings, links, alternatives, plain language (ux-content-design) |
| Developer | HTML semantics, keyboard, ARIA only when needed (fe-web-platform) |
| QA | paths with the keyboard and a screen reader (qa-exploratory-manual) |
| Accessibility specialist | audit, report, plan, training, contact with the lawyer |
| Product owner | fix priorities, the statement, the budget |

## 3. Training plan (3 sessions of 90 minutes)
1. **Experience**: an hour without a mouse; navigating the site with a screen reader (NVDA or VoiceOver) with a recording of a person
   who uses it every day; the goal — to understand, not to pass.
2. **Role**: exercises for the roles from section 2 on your own product (fixing 3 real findings).
3. **Process**: DoD, reporting findings, where to look for help; appointing a "champion" in every team.
Repeat for new people; part of the materials in onboarding.

## 4. Metrics
The number of open findings by severity and the trend; the share of key paths tested with a screen reader in this release; the time from
report to fix of critical ones; the number of reports from users. Do not measure by the automated result alone.
