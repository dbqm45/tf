---
name: pm-product-strategy
description: Use for product strategy in the market — positioning, TAM/SAM/SOM market size, a competitive cheat sheet for sales, PESTEL, growth direction (Ansoff).
metadata:
  review: "2027-10-23"
  catalog: "Use when you must establish who the product is for and why it will win against the alternatives — positioning (competitive alternatives, unique attributes, value, best-fit customers, market category) and the message, TAM/SAM/SOM market size from the bottom up with assumptions, a competitive cheat sheet for salespeople (when we win and lose, objections, questions, dated evidence), the environment (PESTEL) and growth direction (the Ansoff matrix: penetration, new market, new product, diversification). Not for choosing features, the opportunity tree, the business model canvas, Porter's five forces and SWOT (proc-product-discovery), SaaS metrics, retiring a product (pm-product-lifecycle) or a project plan (proc-project-planning)."
  keywords: "pozycjonowanie, komunikat marketingowy, kolejny program, czym się wyróżniamy, wielkość rynku, TAM, SAM, SOM, inwestor pyta o rynek, ściągawka dla handlowców, battle card, przegrywamy z konkurentem, karta konkurencji, PESTEL, nowy kraj czy nowy produkt, macierz Ansoffa, ekspansja zagraniczna, wejść do innego kraju, wejście na nowy rynek, drugi produkt dla obecnych klientów, nowy produkt czy nowy rynek, strategia wzrostu, kategoria rynku, positioning, marketing message, yet another program, what makes us different, market size, an investor asks about the market, cheat sheet for salespeople, we lose to a competitor, competitor card, new country or new product, Ansoff matrix, international expansion, enter another country, entering a new market, a second product for current customers, new product or new market, growth strategy, market category"
---

# Product strategy in the market

Goal: to know who the product is the best choice for, what it really competes with and where to grow — with evidence or
a marked assumption on every sentence (core-grounding). A human makes the strategic decision; you provide
options, numbers with assumptions and a recommendation.

## Procedure
1. **The question and the decision.** Write down which decision the work is to support (a message for the website, an investor presentation,
   market entry, a cheat sheet for sales) and who decides. Which of the steps below you do depends on it.
2. **Positioning** — in this order, because each step follows from the previous one:
   1. **competitive alternatives** — what the customer would do without us (a spreadsheet, an accounting firm, "nothing", a competitor);
   2. **unique attributes** — what we have that the alternatives do not (a feature, a delivery model, knowledge, price);
   3. **value** — what those attributes give the customer, with evidence (a number, a customer quote, a case);
   4. **best-fit customers** — the traits of the customers for whom this value is greatest (not "everyone");
   5. **market category** — the frame in which the customer understands the value at once; the wrong category = "yet another X program".
   Result: a positioning statement and 3 messages with evidence — a template in `references/positioning.md`.
3. **Market size** from the bottom up: the number of target customers × annual revenue per customer, separating TAM / SAM /
   SOM and with a dated source for every number; a top-down estimate ("1% of a big market") only as a check —
   `references/market-and-environment.md`.
4. **Competition for sales** — a cheat sheet per competitor from win and loss data:
   `references/competitive-cheatsheet.md`. A comparison of customer jobs, SWOT and Porter's five forces:
   proc-product-discovery (`.claude/skills/proc-product-discovery/references/business-model-and-market.md`).
5. **Environment and growth direction** — PESTEL for the market you are entering and the Ansoff matrix for growth options
   (`references/market-and-environment.md`). Every option ends with the cheapest test of the key assumption
   (proc-product-discovery, step 8).
6. **Record**: the decision, the rejected options with the reason, the assumptions to verify and a review date →
   `docs/project/01-discovery/` (core-project-record).

## Rules
- A number without a source and date is an [assumption] — you mark it so, also in material for an investor.
- Positioning describes the product's state today; promises from the roadmap you mark as a plan.
- You describe a competitor with facts that can be verified; comparative advertising in the EU must compare objectively
  and verifiably (Directive 2006/114/EC, Art. 4) — for external materials: arch-eu-product-law.

## Example
A billing tool for accounting firms, customers: "yet another accounting program". Alternatives: Excel and the accounting
program the firm already uses. A unique attribute: automatic reconciliation of statements from 12 banks. Value: 6 h
less work per 100 of the firm's customers per month (measured at 4 pilot firms). Best fit: firms of 3–15
people with over 150 sole-proprietorship (JDG) customers. Category: not "an accounting program", but "an automatic payment-reconciliation tool for
accounting firms" — it works alongside the current program, so it does not compete with it. Market from the bottom up: firms of 3–15 people
[a number from GUS (Statistics Poland), year — to be verified] × 2,400 PLN a year = SAM; SOM for 3 years from the capacity of 2 salespeople.

## Sources
- A. Dunford, *Obviously Awesome* (2019) — the components of positioning and their order.
- G. Moore, *Crossing the Chasm* (1991) — the positioning statement, the target customer.
- H. I. Ansoff, "Strategies for Diversification", *Harvard Business Review* (1957) — the product × market matrix.
- F. Aguilar, *Scanning the Business Environment* (1967) — environmental scanning (the origin of PEST/PESTEL).
- Directive 2006/114/EC concerning misleading and comparative advertising, Art. 4.
Described in our own words.
