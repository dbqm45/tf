---
name: ux-accessibility
description: Use for a WCAG 2.2 AA accessibility audit, a findings report, a remediation plan, an accessibility statement and legal requirements (EAA, EN 301 549).
metadata:
  review: "2027-04-17"
  catalog: "Use when the accessibility of a digital product needs assessing or organizing — the WCAG 2.2 level AA audit process (scope and sample, automated tools, manual checks, keyboard, assistive technologies NVDA, JAWS, VoiceOver, TalkBack), a findings report with the success criterion, severity and fix, a remediation plan and priorities, accessibility annotations in the design (headings, landmarks, tab order, names), legal obligations (EN 301 549, the European Accessibility Act – directive (EU) 2019/882 and the Polish implementing act, the accessibility statement of public bodies), inclusive design and team training. Not for the accessibility code of components (fe-web-platform), manual tests in QA (qa-exploratory-manual) or general UX (ux-feature-design)."
  keywords: "audyt dostępności, dostępność cyfrowa, WCAG, WCAG 2.2, czytnik ekranu, NVDA, JAWS, VoiceOver, TalkBack, deklaracja dostępności, ustawa o dostępności, europejski akt o dostępności, EAA, EN 301 549, raport z audytu, niezgodność z WCAG, kontrast, dostępność strony, osoby niewidome, projekt włączający, adnotacje dostępności, plan napraw, zgodność z WCAG, BIP, accessibility audit, digital accessibility, screen reader, accessibility statement, accessibility act, European Accessibility Act, audit report, WCAG non-compliance, contrast, website accessibility, blind users, inclusive design, accessibility annotations, remediation plan, WCAG compliance, accessibility act, European Accessibility Act, EAA, does it apply to us, online store accessibility, which standard to follow, EN 301 549"
---

# Digital accessibility — audit, report, law, team

Goal: to know **who cannot use the product and why**, to fix it in the order of impact and to be able to prove it
(a report, a statement). Component code (ARIA, focus, keyboard) — **fe-web-platform** (`.claude/skills/fe-web-platform/references/accessibility/`);
manual tests in QA sessions — **qa-exploratory-manual**; general UX — **ux-feature-design**.

## Audit procedure (WCAG 2.2 AA)
1. **Goal and measure.** Level A+AA by WCAG 2.2 (a W3C recommendation of 5 October 2023). Establish whether the audit is legally
   required (the Law section) and which standard the contract or the regulation points to — in the EU the EN 301 549 standard.
2. **Scope and sample** by the W3C **WCAG-EM** methodology: define the scope (domain, application, language versions), get to know the site,
   choose a **representative sample** (the home page, key paths: login, purchase, contact form,
   search, a page with a table, a PDF document, complex components: modal, menu, calendar) plus random pages to
   check that the choice is not too optimistic. Record the version, the address, the browsers, the dates. The sample does not
   guarantee the conformance of the whole — the report says so.
3. **Automated tools** (axe, WAVE, Lighthouse, Pa11y) on the whole sample: a quick result, but they catch only part of the problems
   (in the order of 30–40% [unverified]); no errors does not mean conformance.
4. **Manual check** of every page in the sample: keyboard only (order, visible focus, no traps, shortcuts),
   200% zoom and reflow at 320 px, text contrast 4.5:1 and element contrast 3:1, text spacing, content on hover,
   text alternatives, headings and landmarks, forms (labels, errors, autocomplete), multimedia (captions,
   transcript), motion and animations, touch targets ≥ 24×24 px, new in 2.2: 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8.
5. **Assistive technologies** on the critical paths — at least two pairs: NVDA or JAWS with a browser on
   Windows and VoiceOver (Safari) on macOS/iOS; for a mobile app TalkBack on Android. Check names, roles,
   states, dynamic messages, reading order. Best with people who use them every day.
6. **Report** by `references/audit-and-report.md`: for every finding a number, the success criterion (e.g. 1.4.3), the level,
   the location (address, element, screenshot), a description and the impact on the user, the **severity** (critical / serious / moderate / low),
   a fix recommendation, the way of verification. First a summary: scope, method, number of findings by severity, conclusions.
7. **Remediation plan.** Priority = severity × reach (critical path, number of pages) ÷ cost; first the barriers that block
   a task (no keyboard access, no labels in the payment form), then solutions in components
   (one fix in the design system closes many findings), at the end individual pages. For every fix a regression
   test and a "done" criterion (the component's DoD).
8. **Repeat** after the fixes on the same pages and paths; update the report and, if applicable, the statement.

## Accessibility annotations in the design (before code)
Add to the screen specification (ux-feature-design, handoff): the heading structure (one `h1`, no skips), landmarks
(`header`, `nav`, `main`, `footer`, `aside` with a name when there are several), the **focus order** (numbered on the wireframe),
the accessible names of buttons and fields (consistent with the visible text), messages (the `status` or `alert` role), where focus
returns after a dialog closes, text alternatives, contrasts from tokens, behaviour under zoom. Tasks at the design stage
are cheaper than fixes after release. Accessible content — ux-content-design.

## Law (state checked 2026-10-17, details: `references/law-and-declaration.md`)
- **European Accessibility Act** — directive (EU) 2019/882, applied from **28 June 2025**; in Poland the act of
  26 April 2024 on ensuring that certain products and services of economic operators meet accessibility requirements
  (Dz.U. 2024 item 731). It covers among others e-commerce, retail banking, telecommunications
  services, e-books, passenger transport; the services of microenterprises are excluded (not the products).
- **Public bodies** — the act of 4 April 2019 on the digital accessibility of websites and mobile applications
  of public bodies (Dz.U. 2019 item 848; consolidated text Dz.U. 2023 item 82 — check the current one):
  WCAG 2.1 AA requirements, an **accessibility statement** on the website, an annual review.
- **EN 301 549** — the European standard for ICT; version V3.2.1 points to WCAG 2.1 AA, V4.1.1 (WCAG 2.2) published on
  2 September 2026, and for a presumption of conformity it must be cited in the OJ EU [unverified — secondary sources].
  So the legal requirement is currently WCAG 2.1 AA; use 2.2 AA as a forward-looking target.

## Inclusive design and the team
- Design for a spectrum: permanent, temporary and situational disability (ux-feature-design, inclusive design). Research
  with people with disabilities, payment for taking part, accessible research tools.
- Accessibility as the **definition of done** of a component and a task, not a phase at the end. Roles: designer (contrast,
  annotations), content author (links, headings, alternatives), developer (semantics, keyboard), QA (paths with a screen reader).
- Training: a workshop with the keyboard and a screen reader (30 minutes of your own experience convinces more than slides),
  a role checklist, a designated person (champion), measured findings per sprint. Plan: `references/team-and-training.md`.

## Example
Input: "A shoe shop (45 people, Poland), the order form: fields without labels, an error only in red."

Result (a fragment of the report):

| ID | SC | Severity | Finding | Fix |
|---|---|---|---|---|
| A-007 | 3.3.2 / 1.3.1 (A) | critical | The "Postal code" field has only a placeholder; NVDA reads "edit". Affects 4 of 4 order steps | a `label` associated with the field, the placeholder as a hint |
| A-008 | 1.4.1 (A), 3.3.1 (A) | serious | The error is marked with color; no error text | The text "Enter the code in the format 00-000" + `aria-describedby` |

Plan: A-007 and A-008 as one fix in the field component (design system) — closes 11 of 23 findings; rollout before
the next release. Obligation: the shop (50 people) is subject to the act of 26.04.2024 from 28.06.2025.

## Checklist
- [ ] goal and standard set (WCAG 2.2 AA; in the EU EN 301 549), scope and sample by WCAG-EM recorded
- [ ] automated tools + manual check + keyboard + at least two assistive technologies
- [ ] every finding: success criterion, severity, location, impact, fix, verification
- [ ] a remediation plan by severity and reach; fixes in components before individual pages
- [ ] accessibility annotations in the design specification
- [ ] the legal obligation identified; the accessibility statement (public bodies) up to date
- [ ] DoD with accessibility, training, a repeat after the fixes

## Additional materials
- `references/audit-and-report.md` — the report template, the severity scale, the set of manual checks and screen reader–browser pairs; read during an audit.
- `references/law-and-declaration.md` — EAA, the Polish acts, EN 301 549, the content of the accessibility statement; read for questions about obligations.
- `references/team-and-training.md` — DoD, roles, a training plan, metrics; read when bringing accessibility into the team.

## Sources
- W3C, WCAG 2.2 (a recommendation of 5 October 2023; 4.1.1 Parsing removed) and WCAG-EM (the evaluation methodology) — confirmed
  by a secondary search, the W3C pages were unavailable in the session of 2026-10-17 [unverified at the source].
- Directive (EU) 2019/882 (EAA), applied from 28 June 2025 — EUR-Lex unavailable in the session; confirmed by
  secondary sources (accessed 2026-10-17) [unverified at the source].
- The act of 26 April 2024 (Dz.U. 2024 item 731, entry into force of Art. 88 – 28 June 2025; supervision: the president of PFRON
  and sector authorities) — eli.gov.pl and search results, accessed 2026-10-17.
- The act of 4 April 2019 (Dz.U. 2019 item 848, consolidated text Dz.U. 2023 item 82), gov.pl/web/dostepnosc-cyfrowa — search
  results, accessed 2026-10-17; the annual review date "by 31 March" only from secondary sources [unverified].
- ETSI EN 301 549 V3.2.1 (2021) and V4.1.1 (published 2 September 2026) — secondary sources (Deque, NDA), accessed 2026-10-17.
Described in our own words.
