# Interface copy, inclusive and ethical design

## Interface copy (UX writing)
- The words of the user and of the domain glossary (ddd-facilitation), not of the system: "Order shipped", not "Status: SHIPPED".
  The same thing always under the same name.
- **Buttons** say what will happen, with a verb: "Send invoice", "Delete 3 files" — not "OK", "Submit", "Yes".
- **Error message**: what happened + why (if it helps) + what to do, next to the field, without blame or codes:
  "This tax ID has 9 digits — enter 10 digits without dashes", not "Invalid data (E1043)". An error code only as
  an identifier for support.
- **Empty state**: why it is empty and the first step ("You have no customers yet. Add the first one or import
  from a CSV file").
- **Confirmations** of irreversible actions name the consequence ("Delete the project "Home"? You will also delete 12 tasks"), and the button
  repeats the verb. Where possible — undo instead of confirmation.
- Short, with the most important first; copy must also fit in longer languages (Polish is several tens of
  percent longer than English) and with plural forms of numerals (fe-web-platform, `i18n.md`).
- Polish copy: proofreading and style by txt-polish-correctness and txt-polish-style.

## Voice and tone
- **Voice** (constant): the product's character, e.g. "matter-of-fact, kind, no jargon". **Tone** (variable): depends on the user's
  situation — at a payment error calm and concrete, at a success short, without euphoria.
- The form of address: one across the whole product (e.g. informal "ty" in a consumer app, impersonal or formal "Państwo" in B2B
  and official products in Polish) — a decision recorded in the main document of the design system.
- A list of preferred and forbidden words in the repo (e.g. `docs/content-guide.md`), a review of copy in PRs like code.

## Inclusive design
- Disability as a spectrum: permanent (a blind person), temporary (a broken arm), situational (a parent with a child
  in their arms, sun on the screen). A solution for one group often helps everyone (captions, large touch targets).
- Recruit people with disabilities, older people, people with lower digital proficiency for research; test with a screen reader,
  a keyboard, 200% zoom, a weak connection.
- Forms without cultural assumptions: first name and surname in one field or flexibly, gender optional with sensible
  options, addresses of different countries, diacritics everywhere.
- Legal requirements: WCAG 2.2 AA, the European Accessibility Act (fe-web-platform).

## Ethical design — deceptive patterns you do not use
| Pattern | Example | Instead |
|---|---|---|
| hard exit | cancelling a subscription only by phone | cancelling as easy as buying |
| confirmshaming | "No, I prefer to overpay" | a neutral "No, thanks" |
| hidden costs | a fee added at the last step | the full price from the start |
| pre-ticked consents and extras | a ticked newsletter, insurance in the cart | the choice off by default |
| false urgency or scarcity | a countdown that resets; "2 left" without substance | only true information |
| unequal consent options | "Accept all" highlighted, "Reject" hidden in settings | equal buttons on the first level |
| disguised ads, forced registration | an account required to browse the offer | access without an account where possible |
- EU law: the Digital Services Act (DSA, Art. 25) forbids online platforms from designing
  an interface that deceives or manipulates; the Unfair Commercial Practices Directive and the GDPR (consent
  voluntary, informed, easy to withdraw) cover more broadly. The EU is preparing further rules (the Digital Fairness Act) —
  before designing purchase, subscription and consent flows check the current state with the legal department.
- Design responsibly: who can be harmed by this feature (abuse, harassment, addiction, exclusion)?
  Add the question to the design review and the threat model (arch-threat-modeling).

## Sources
- NN/g, [UX Writing: Study Guide](https://www.nngroup.com/articles/ux-writing-study-guide/),
  [Inclusive Design](https://www.nngroup.com/articles/inclusive-design/); Microsoft Inclusive Design Toolkit
- [DSA art. 25](https://dsa-library.com/article/25/); H. Brignull, *Deceptive Patterns* (2023)
- [roadmap.sh — Product Design](https://roadmap.sh/product-design) (UX writing, microcopy, voice & tone, inclusive,
  ethical design, designing responsibly)
Described in our own words.
