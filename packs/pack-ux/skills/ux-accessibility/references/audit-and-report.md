# Accessibility audit — report, severity, checks

Contents: 1. Report template · 2. Severity scale · 3. Manual checks · 4. Screen reader–browser pairs · 5. Remediation plan

## 1. Report template
1. **Summary** (half a page): scope, standard and level (WCAG 2.2 A+AA), date, product version, number of findings by severity,
   the 3 most important barriers, an overall assessment in words ("partially conformant: 5 barriers blocking a purchase").
2. **Scope and method**: the addresses in the sample and the reason for the choice (WCAG-EM), tools with versions, browsers, assistive technologies,
   limitations (what was not checked: content behind login, PDFs, the mobile app).
3. **Findings** — a table or cards: `ID | Success criterion (number, level) | Severity | Location (URL, element, screenshot) | Description and impact on the user | Recommendation | How to verify after the fix`.
4. **Conformance with the criteria**: a table of the A+AA criteria with a status: met / not met / not applicable / not checked.
5. **Strengths** (what to keep) and the **remediation plan** (section 5).
One finding = one problem in one pattern; the same thing in 30 places is one finding with a list of places.
Write the impact about a person: "a blind person will not learn which field is wrong", not "missing aria-describedby".

## 2. Severity scale (our own; adjust to the contract)
| Severity | Criterion | Example |
|---|---|---|
| Critical | prevents completing a task on a key path | the payment form not reachable with the keyboard |
| Serious | makes it very hard or requires a workaround | missing field labels, button contrast 2:1 |
| Moderate | makes it harder, there is a workaround | an unclear heading order |
| Low | a minor inconvenience, a risk on change | redundant alternative text |
Severity takes into account the reach (a key path or a corner of the site) and the affected groups. Do not confuse severity with the A/AA level
of the criterion.

## 3. Manual checks (a set per page in the sample)
- Keyboard: Tab/Shift+Tab reaches everything, the order matches the layout, focus always visible and not obscured (2.4.7, 2.4.11),
  no trap, Escape closes overlays, single-character shortcuts can be turned off (2.1.4).
- 200% zoom and reflow at a width of 320 px without scrolling in two directions (1.4.4, 1.4.10); text spacing (1.4.12).
- Contrast: text 4.5:1 (large 3:1), interface elements and focus 3:1 (1.4.3, 1.4.11).
- Content: headings, landmarks, page title, language (`lang`), text alternatives, links understandable out of context (2.4.4).
- Forms: labels, required fields, errors in text with a suggestion, autocomplete (1.3.5), no re-entering (3.3.7),
  authentication without a cognitive test (3.3.8).
- Multimedia: captions, transcript, audio description where the image carries content; no autoplay with sound.
- Motion: the ability to pause, no flashes (> 3 per second), an alternative to dragging (2.5.7), targets ≥ 24×24 px (2.5.8).
- Dynamics: status messages announced without taking focus (4.1.3).

## 4. Screen reader–browser pairs (a typical test set)
NVDA + Firefox or Chrome (Windows), JAWS + Chrome (Windows), VoiceOver + Safari (macOS, iOS), TalkBack + Chrome (Android).
Choose the pair by what the audience uses (the WebAIM screen reader survey – check the current edition [unverified]).
Record the screen reader and browser versions in the report; differences between pairs often come from screen reader bugs.

## 5. Remediation plan
Table: `Finding IDs | Fix | Owner | Effort | Deadline | Verification`. Order: (1) barriers blocking a task,
(2) fixes in components and templates, (3) the rest on key paths, (4) everything else. Findings that cannot
be fixed before the legal deadline go into the statement as non-conformities with a plan and a date.
