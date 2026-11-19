# Content style guide and microcopy patterns

Contents: 1. Guide template · 2. Voice and tone · 3. Microcopy patterns · 4. Anti-patterns

## 1. Style guide template (`docs/content-guide.md`)
A short document, not a manual. Sections:
1. **Goal and readers** — who we write for, in what situations (2–3 personas or situations).
2. **Voice** — 3–4 traits, each in the form "we are X, not Y" with a "yes" and a "no" example sentence.
3. **Tone by situation** — a table: situation (success, error, warning, payment, first use) → tone → example.
4. **Form of address** — one decision (informal / formal / impersonal) and the exceptions.
5. **Glossary** — the preferred concept, banned synonyms, a one-sentence definition (consistent with the domain glossary
   from ddd-facilitation; the same list feeds the translation glossary).
6. **Writing rules** — sentence length, active voice, numbers and dates (format), capital letters, abbreviations, emoji.
7. **Patterns** — ready skeletons from point 3; each with a good and a bad example.
8. **Process** — who approves, how to change (PR), how to report exceptions.
Review texts in a PR like code; Polish — txt-polish-correctness and txt-polish-style.

## 2. Voice and tone
- A constant voice: e.g. "matter-of-fact, not cold"; "kind, not overfamiliar"; "concrete, not jargony".
- A changing tone: the more stress the user has (losing money, data), the fewer jokes, the more concreteness and a way out.
- Humour only in situations without risk and without a cost for the person reading it for the tenth time.
- Test: could you say the sentence aloud to a person at a counter? If not, rewrite it.

## 3. Microcopy patterns
| Element | Skeleton | Example |
|---|---|---|
| Field error | what to fix + the requirement | "Enter the tax ID — 10 digits, no dashes" |
| System error | what happened + whether data is safe + what next | "We could not save the invoice. Your changes are still in the form. Try again in a moment or write to us." |
| Empty state | why it is empty + the first step + a button | "You have no customers yet. Add the first one or import a CSV file." |
| Empty search result | what was found (nothing) + a hint | "No results for "invc". Check the spelling or search by number." |
| Confirmation | the effect + a verb | "Delete the project "Home"? You will also delete 12 tasks." → [Delete project] [Cancel] |
| Button | a verb + an object | "Send invoice", not "OK" |
| Success | what happened + what next (optional) | "Invoice 03/2026 sent to Jan Kowalski." |
| Onboarding | one thing per screen, the benefit before the feature | "Issue your first invoice in 2 minutes" |
| Notification | who/what + what it concerns + an action | "The customer paid invoice 03/2026. See the payment" |
| Consent | what, why, how to withdraw; equal options | "Send reminders about due dates? You can turn this off in Settings." |

## 4. Anti-patterns
- "An unexpected error occurred" without a next step; "Invalid data"; a code instead of a sentence.
- Blaming: "You entered a wrong number" → "The number has 9 digits, 10 are needed".
- "We apologize for the inconvenience" instead of help; exclamation marks and "Oops!" when data is lost.
- "Yes" / "No" buttons on a negated question; an unclear "Cancel" (cancel the action or close the window?).
- The same thing under three names (order, purchase, transaction).
- Text as an image or text glued from fragments in code (it breaks translation and screen readers).
