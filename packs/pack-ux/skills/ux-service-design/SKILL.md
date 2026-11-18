---
name: ux-service-design
description: Use when the problem is a service across many channels with a back office, not a screen — service blueprint, journey map, touchpoints, service prototype.
metadata:
  review: "2027-10-17"
  catalog: "Use when the customer's problem spans many channels, people and the back office (a shop, an office, a bank, a service centre, onboarding), not a single screen — service blueprint (customer actions, frontstage, backstage, support processes, evidence, lines of interaction and visibility), the current and target customer journey map, a stakeholder map, a touchpoint inventory, consistency across channels, a co-design workshop, a service prototype (role-play, concierge, Wizard of Oz), service metrics and the public service standard (GOV.UK Service Standard); the artifact service-blueprint.md. Not for modelling a domain process with events (ddd-event-storming), a value stream map and waste, choosing what to build and assumption tests (proc-product-discovery) or screen flows and states (ux-feature-design)."
  keywords: "usługa, service design, projektowanie usług, service blueprint, blueprint usługi, plan usługi, frontstage, backstage, zaplecze, mapa podróży klienta, customer journey, journey map, punkty styku, touchpoint, omnichannel, wielokanałowość, spójność kanałów, interesariusze, mapa interesariuszy, współprojektowanie, co-design, warsztat z klientami, prototyp usługi, Wizard of Oz, concierge, odgrywanie ról, bodystorming, standard usług, GOV.UK Service Standard, usługa publiczna, urząd, obsługa klienta, zwroty, reklamacje od strony klienta, nikt nie widzi całości, service, back office, customer journey map, touchpoints, multichannel, channel consistency, stakeholders, stakeholder map, customer workshop, service prototype, role-play, public service, government office, customer service, returns, complaints from the customer side, nobody sees the whole"
---

# Service design — from the whole experience to the back-office plan

A service is not a screen: the customer passes through channels (web, app, phone, counter, parcel), people and systems,
some of which they see and some they do not. A problem is a "service" one when the complaints concern the **seams** (a channel change, a handoff
between departments, waiting for the back office), not a single screen. The effect: a shared picture of the whole and a list of changes in
the back office, not only in the interface.

## When this skill
- Complaints, repeated data, the customer "bounced" between departments, different answers in different channels → yes.
- A question about one screen or a flow in the app → **ux-feature-design**.
- A model of the domain events and rules for a system → **ddd-event-storming**.
- Choosing which opportunities to pursue, and assumption tests → **proc-product-discovery**.

## Procedure
1. **Scope and input.** Choose one service from the opening event to the closing one ("the customer wants to return
   an item" → "the money came back"). Collect evidence from research (interviews, support tickets, data); if it is missing, plan
   research (ux-research-methods). Do not draw from the team's head.
2. **Stakeholder map.** Customers (segments), frontstage and backstage staff, partners (courier, payments),
   the regulator. For each: what they need, what they influence, who listens to them. Record it as a table; a diagram only with
   >10 parties.
3. **Journey map — current.** Stages, customer actions, channels, thoughts and emotions, moments of truth and pain points, each
   with evidence (a quote, a number). A separate map per segment if the paths differ. The map shows **the customer's
   perspective**; the blueprint adds the back office.
4. **Touchpoint inventory.** A table: touchpoint, channel, owner, system, purpose, consistency with other channels
   (the same data, the same language, the same promise). Consistency gaps are candidates for changes (`references/templates.md`).
5. **Service blueprint** (current state, then target). Horizontal lanes from the top:
   physical and digital evidence → **customer actions** → *line of interaction* → **frontstage** (visible actions of
   staff and interfaces) → *line of visibility* → **backstage** (invisible staff actions) →
   *line of internal interaction* → **support processes** (systems, other units, partners).
   Each step: time, who, with what tool, what data. Mark failure points, waiting and handoffs.
   Mermaid and the table template: `references/templates.md`.
6. **Diagnosis.** On the blueprint mark: handoffs without data, places where the customer does the back office's work,
   discrepancies between channels, steps without an owner. Rank them by the impact on the customer and the cost of service.
   First solve the **whole problem** (not a fragment) and the consistency across channels.
7. **Co-design.** A workshop with customers and staff from both sides of the line of visibility: 6–10 people, 2–3 hours,
   the blueprint on the wall, participants add missing steps and propose changes. Back-office staff know
   workarounds that are not in any document. Facilitation: ddd-facilitation.
8. **Service prototype** with the cheapest method that will answer the question: role-play and bodystorming (the layout
   of a counter, a conversation), **concierge** (a human does by hand what a system will do later), **Wizard of Oz**
   (the customer thinks the system works, while a human does it), a mock-up of a room or a paper form.
   Write down the hypothesis, the success criterion and what you will measure; code only after confirmation.
9. **Target blueprint and target map.** Changes arranged in waves; for each: the impact on the customer, the back-office work,
   changes in systems, the organizational change (who loses, who gains tasks). Turn them into opportunities for
   proc-product-discovery, and the back-office changes into a backlog.
10. **Metrics and standard.** Service metrics with the customer at the centre: the completion rate of the whole task (in every channel),
    the time from the request to the result, repeat contacts on the same matter, the cost of handling one case, satisfaction. For
    public services relate the assessment to the GOV.UK Service Standard (14 points, among them "Solve a whole problem for users",
    "Provide a joined up experience across channels", "Define what success looks like and publish performance
    data") — the full list and notes: `references/service-standard.md`.

Result: `docs/project/01-discovery/service-blueprint.md` (+ maps in the same directory); TL;DR and Handoff by
core-project-record. The first line of the file: `Service blueprint: <service> — current|target state`.

## Example
Input: "Returns in an online shop: 31% of customers contact support after sending the return form."
Result (a fragment of `service-blueprint.md`, current state):

```markdown
Service blueprint: item return — current state
| Layer | Step 1 | Step 2 | Step 3 |
|---|---|---|---|
| Evidence | web form, "received" e-mail | PDF label | courier SMS |
| Customer actions | fills in the form (6 fields) | prints the label, packs | waits for the refund |
| — line of interaction — | | | |
| Frontstage | — | hotline: "courier in 3 days" | chat: "I will check" |
| — line of visibility — | | | |
| Backstage | manual re-entry into the ERP (~4 h) | the warehouse scans the parcel | accounting waits for approval |
| — line of internal interaction — | | | |
| Support processes | ERP, e-mail | courier system | bank (transfer once a day) |
Failure points: P1 re-entry (a 4 h delay, 9% errors); P2 no status for the customer →
31% of contacts. Consistency: the hotline and the chat give a different refund time (3 vs 7 days).
```

Target change: the form saves straight into the ERP, the customer sees the status in an e-mail; a first test through concierge
(an employee sends statuses by hand to 50 customers), we measure the drop in contacts from 31% in the same period.

## Checklist
- [ ] one service, an opening and a closing event; evidence from research, not from the team's head
- [ ] stakeholders, the journey map (current), a touchpoint inventory with an assessment of channel consistency
- [ ] a blueprint with all lanes, three lines and failure points; the current state separate from the target
- [ ] a workshop with frontstage and backstage staff; a service prototype with a hypothesis and a criterion
- [ ] service metrics cover the whole task in all channels; (a public service) a reference to the Service Standard
- [ ] [unverified] and assumptions marked; the result in `docs/project/01-discovery/`

## Additional materials
- `references/templates.md` — templates of the blueprint (table and Mermaid), the journey map, stakeholders and the inventory; read when writing the artifact.
- `references/service-standard.md` — the GOV.UK Service Standard, service prototyping methods and how to use them.

## Sources
- NN/g, *Service Blueprints: Definition* (nngroup.com/articles/service-blueprints-definition/) — the elements of the blueprint;
  confirmed in this session only by search (accessed 2026-10-17), the wording of the lines from secondary sources [unverified].
- GOV.UK Service Manual, *Service Standard* (gov.uk/service-manual/service-standard), points 2, 3, 4 and 10 confirmed
  in the search results (accessed 2026-10-17); the full list of 14 points in the references.
- Shostack, *How to Design Services* (1984) and Bitner, Ostrom, Morgan, *Service Blueprinting* (2008) — the source
  of the blueprint method [unverified in this session].
Described in our own words.
