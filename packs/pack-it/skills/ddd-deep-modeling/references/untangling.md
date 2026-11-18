# Techniques for untangling a model

Four techniques for a model in which the same knowledge sits in many places, relationships drift apart, and every new
need ends with another value of the "status" field.

## 1. A single source of truth
- **Principle:** every business fact has one owner (an aggregate in one context). The others point to it by an
  identifier or keep a read-only copy refreshed by an event (a read model). The copy is never the
  basis of a decision that changes this fact.
- **Test:** "where will I change this fact when it changes in the business?". More than one place means the fact is
  untangled badly.
- **Signals:**
  - the same list of identifiers on both sides of a relationship;
  - fields "copied for convenience" without an event that refreshes them;
  - two tables with the same validity date;
  - disputes between teams about "who holds the truth".
- **Procedure:**
  1. List the facts that drift apart.
  2. For each, establish the owner: who decides about it in the business.
  3. Replace the other copies with references or read models.
  4. Announce a change of the fact with an event (ddd-tactical-design, ddd-context-mapping).

## 2. A hidden concept in a many-to-many relationship
- **Principle:** a many-to-many relationship between two concepts almost always hides a third concept. It has its own
  data (from–to dates, conditions, role), its own life cycle and its own rules. Name it in the business language. It becomes
  the single source of truth about the relationship.
- **Example:** doctor ↔ clinic is an **Employment** (*Zatrudnienie*: from–to, working hours, the specialization in this clinic,
  the schedule). In turn, student ↔ course is an **Enrolment** (*Zapis*: term, pass status, grade). The lists of identifiers on both
  sides disappear, and the question "where does the doctor work on day X" has one place for the answer.
- **Questions for the expert:**
  - "What happens when this relationship begins and ends?"
  - "Does the relationship have dates, conditions or a document?"
  - "Can the same pair be related twice in different periods?"

  Every "yes" confirms that the relationship is a separate concept.
- **Archetype:** relationships between parties are PartyRelationship
  (`.claude/skills/ddd-archetypes/references/party.md`), and a contract with items is Agreement
  (`.claude/skills/ddd-archetypes/references/agreement.md`).

## 3. Status is not an extension mechanism
- **Problem:** every new need gets a new status value, e.g. an offer as "an order with the status offer",
  "VIP", "wholesale order". This ends with conditions `if (status == …)` spread everywhere and rules that apply
  only to some of the values.
- **A status is fine** when it describes the life cycle of one concept with explicit transitions (a state machine):
  the same data, different allowed operations.
- **Instead of a new status value:**
  - different data, rules and life cycle mean a **separate concept** (Becoming: an offer turns into a contract or
    an order, but it is not one);
  - the same entity in a new context is a **role** (Role Object);
  - an additional capability for some of the objects is an **extension** (Extension Object);
  - a different way of calculating is a **policy** (ddd-tactical-design).

## 4. Two levels of the model: knowledge and operations
- **Knowledge level:** types, rules and configuration that the business defines and changes, e.g. a kind
  of insurance with fields and rules, a product type, a procedure, a chart of accounts, role permissions.
- **Operations level:** concrete events and instances created every day, e.g. a policy,
  a product instance, a performed activity, a posting. Each of them points to its type on the knowledge level.
- **When:** the business wants to add kinds without a programmer, the rules depend on the kind, and the number of kinds grows.
- **Rules:**
  - Operations refer to knowledge, never the other way round.
  - A change of knowledge is a new version. New operations use the new version, existing ones stay with theirs (agreement,
    pricing in ddd-archetypes).
  - The knowledge level has its own validity rules, e.g. you will not delete a type that has operations.
- **Cost:** the model becomes abstract and harder to read. When there are a few kinds and new ones rarely appear,
  ordinary classes are enough.
- **In the archetypes:** ProductType and ProductInstance (`product.md`), procedure and activity (`activity-process.md`),
  resource type and instance (`resource-service.md`).

## Sources
- M. Fowler, *Analysis Patterns: Reusable Object Models*, Addison-Wesley, 1996 [unverified: the year according to
  catalogues is 1996, some editions give 1997]. Knowledge and operations level: chapter 2 "Accountability", section
  "Accountability Knowledge Level" (table of contents at the publisher, InformIT, accessed 2026-10-21).
- E. Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, chapter 16
  "Large-Scale Structure", the "Knowledge Level" pattern [unverified: according to a table of contents from secondary sources].
- J. Arlow, I. Neustadt, *Enterprise Patterns and MDA: Building Better Software with Archetype Patterns and UML*,
  Addison-Wesley, ISBN 9780321112309, year: sources give 2003 or 2004 (chapters Party, Product, Inventory, Rule according to the table of contents).
- Techniques 1–3 are described in our own words on the basis of the sources above and the training programme "DDD — zaawansowane
  techniki modelowania i archetypy" (Advanced modeling techniques and archetypes; Bottega IT Minds, material from a human, 2026-10-21).
