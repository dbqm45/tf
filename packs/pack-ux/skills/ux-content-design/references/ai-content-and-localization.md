# Content of AI features and localization

Contents: 1. Texts of AI features · 2. Localization process · 3. String management

## 1. Texts of AI features
| Element | Rule | Example |
|---|---|---|
| Labelling | from the first contact it is visible that it is AI; the name and description do not pretend to be a human | "The bank's AI assistant" + "An AI system answers, not an employee" |
| Abilities and limits | 1–2 sentences: what it helps with, what it does not do | "I will help you find fees. I do not change limits." |
| Uncertainty | in words and with a source, without false precision | "Based on the terms of 12.03.2026. Check in the document." |
| Errors and refusals | what happened + what to do instead | "I cannot check this. Connect with an agent." |
| Data | what goes to the model, whether it is used for training | one sentence + a link to the policy |
| Feedback | an easy report of a wrong answer | "This answer is wrong" |
| Way out | always a route to a human in important matters | a "Talk to an agent" button |
Legal requirement: AI Act, Art. 50(1) (informing people that they interact with an AI system, unless it is obvious
from the context); applies from 2 August 2026. Marking generated content (Art. 50(2)) – the date for systems
already on the market according to secondary sources is 2 December 2026 [unverified]. Leave the decision on the scope of the obligation to a lawyer.
Do not promise "always correct" answers; do not insert a confidence percentage if the system does not compute it reliably.

## 2. Localization process
1. Internationalization first: keys instead of sentences in code, ICU for plural and gender (fe-web-platform).
2. A string has a **description for the translator**: where it is visible, character limit, the meaning of variables, register (informal/formal).
3. A glossary from the style guide (fixed terms, proper names, banned calques).
4. Pseudolocalization and a length test (+30–40%) before sending to translators.
5. Translation (a human or MT + editing) → a review **in the context of the screen** → proofreading (txt-polish-correctness for Polish).
6. A change in the source marks the string for retranslation; you must not change the meaning under the same key.
7. Dates, numbers, currencies, sorting — through `Intl`, not by hand.

## 3. String management
- One source of truth (a file or a translation management system), keys with namespaces (`billing.invoice.empty`).
- The same text in several places – one key, unless the context needs a different wording.
- Statuses: new, to translate, translated, approved; a missing approval does not block the release if there is a fallback version.
- Text changes in a PR with a content review; a test in CI that checks for missing keys.
