# Techniques for untangling a model

Four recurring smells of a tangled model, each with its fix: the same fact kept in several places, a many-to-many
link whose two sides drift apart, a "status" field that absorbs every new need, and types hard-coded where the
business wants to define them itself. Treat them as diagnostic lenses, not as a fixed procedure.

## 1. A single source of truth for every fact
- **Smell:** a customer's billing address lives in `Customer`, `Order`, `Invoice` and `Shipment`; after a change, half
  of them still show the old one. Other signs: a copy kept "for convenience" that nothing refreshes, two tables with
  their own `valid_until` for the same thing, teams arguing whose number is right.
- **Test question:** "when the business changes this fact, how many places do we have to touch?" One is healthy;
  more than one means the fact has no owner.
- **Fix:** give each fact exactly one owner, an aggregate in one bounded context (ddd-tactical-design). Everyone else
  keeps only its identifier, or a read-only copy (read model) refreshed by an event the owner publishes
  (ddd-context-mapping). A copy may be displayed or used to filter, never to decide a change of the fact itself.
- **Not every copy is a smell:** an invoice must keep the address valid on the day of issue. That is a deliberate,
  frozen snapshot with a legal meaning, so name it as such (`billedTo`) and do not refresh it.
- **How to get there:** list the facts that drift; for each one ask who in the business decides about it; replace
  the other copies with references or read models; make the owner announce changes as events.

## 2. A hidden concept in a many-to-many relationship
- **Smell:** a student holds a list of course ids, a course holds a list of student ids, and a flag such as
  `isPassed` sits on the student, although it is true only for one course in one term.
- **Diagnosis:** a many-to-many link almost always hides a third concept with its own data (dates from-to,
  conditions, a role), its own life cycle and its own rules. Here it is an **Enrolment** (term, grade, pass status);
  a doctor working in several clinics hides an **Employment** (hours, specialization, schedule).
- **Fix:** name the concept in the expert's language and make it the owner of the facts about the relationship.
  The id lists on both sides disappear, and so does the drift between them (one source of truth again).
- **What to ask the expert:** what starts and ends the relationship; whether it has dates, conditions or a document
  behind it; whether the same pair can be linked again later, e.g. a student retaking a course. A "yes" to any of
  these means a concept of its own.
- **In the archetypes:** a link between people or organisations is a party relationship
  (`ddd-archetypes/references/parties-and-relationships.md`); an agreement with items and obligations is a
  commitment (`ddd-archetypes/references/commitments.md`). In code, the textbook form is an association class.

## 3. Status is not an extension mechanism
- **Smell:** each new requirement becomes one more status value. A quote is an `Order` with `status = QUOTE`, a stock
  item gets `status = RESERVED` although a reservation has a customer, an expiry and rules of its own. Soon there are
  `if (status == ...)` checks in many services and rules that apply only to some values.
- **When a status is fine:** it describes the life cycle of ONE concept, the data stays the same and only the allowed
  operations change, with explicit transitions. An order going draft, paid, shipped, delivered is a plain state
  machine; do not invent new concepts for it.
- **When it is not:** a "state" that brings its own data, rules or owner is a different concept. Pick the fix by
  what differs:
  - different data, rules or life cycle: a **separate concept**; a quote *becomes* a contract or an order (Becoming),
    it is not one of its states; a reservation is its own concept holding stock for someone until a deadline;
  - the same thing acting in a new context: a **role** (Role Object);
  - an extra capability only some objects have: an **extension** (Extension Object);
  - a different way of calculating: a **policy** chosen at run time (ddd-tactical-design).
- **Start with 5 why** on every transition (see the Behaving section of SKILL.md) before deciding which case it is.

## 4. Two levels of the model: knowledge and operations
- **Knowledge level:** types, rules and configuration that the business defines and changes, e.g. a kind
  of insurance with fields and rules, a product type, a procedure, a chart of accounts, role permissions.
- **Operations level:** concrete events and instances created every day, e.g. a policy,
  a product instance, a performed activity, a posting. Each of them points to its type on the knowledge level.
- **When:** the business wants to add kinds without a programmer, the rules depend on the kind, and the number of kinds grows.
- **Rules:**
  - Operations refer to knowledge, never the other way round.
  - A change of knowledge is a new version. New operations use the new version, existing ones stay with theirs (commitments,
    price calculation in ddd-archetypes).
  - The knowledge level has its own validity rules, e.g. you will not delete a type that has operations.
- **Cost:** the model becomes abstract and harder to read. When there are a few kinds and new ones rarely appear,
  ordinary classes are enough.
- **In the archetypes:** product type and product instance (`product-definitions.md`), procedure and its execution (`work-execution.md`),
  asset type and asset instance (`assets-and-services.md`).

## Sources
- M. Fowler, *Analysis Patterns: Reusable Object Models*, Addison-Wesley, 1996 [unverified: the year according to
  catalogues is 1996, some editions give 1997]. Knowledge and operations level: chapter 2 "Accountability", section
  "Accountability Knowledge Level" (table of contents at the publisher, InformIT, accessed 2026-10-21).
- E. Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, chapter 16
  "Large-Scale Structure", the "Knowledge Level" pattern [unverified: according to a table of contents from secondary sources].
- J. Arlow, I. Neustadt, *Enterprise Patterns and MDA: Building Better Software with Archetype Patterns and UML*,
  Addison-Wesley, ISBN 9780321112309, year: sources give 2003 or 2004 (chapters Party, Product, Inventory, Rule according to the table of contents).
