# Patterns outside GoF: Role Object and Extension Object

Two structural patterns from the later PLoP catalogs, useful in domain models when the same entity plays many
roles or gets additional capabilities. Both replace flag fields and a growing "status" field (ddd-deep-modeling,
`.claude/skills/ddd-deep-modeling/references/untangling.md`).

## Role Object
- **Problem:** the same person or company is at the same time a customer, a supplier and an employee. Each role has its own
  data, rules and life cycle, and roles appear and disappear over time. One class with the fields `isCustomer`,
  `isSupplier` and their data grows without end. Subclasses (`CustomerSupplier`) explode combinatorially and do not allow
  changing a role during the object's lifetime.
- **Solution and participants:**
  - **the core**: the identity and the shared data, e.g. a person with a name and an address;
  - **role objects:** separate objects with the role's data and behaviour (`Customer` with a credit limit, `Supplier`
    with delivery terms), which point to the core;
  - the core allows asking for a role, adding it and removing it (`hasRole`, `getRole`, `addRole`, `removeRole`).
- **When to use:** the roles are independent, are added and disappear over time, or each has its own rules and owner.
- **Costs:** the identity is split into several objects; you must make sure a role does not exist without the core, and settle
  where the shared data lives.
- **In a domain model:** a role is often a separate aggregate in another context, pointing to the party by an identifier.
  The Party and PartyRole archetype (`.claude/skills/ddd-archetypes/references/party.md`) is this pattern at the level
  of the business model.
- **When NOT:** the role has no data or rules of its own and only changes permissions; then an attribute or
  an authorization mechanism is enough.

## Extension Object
- **Problem:** you need to add to an existing class interfaces that only some clients need, e.g.
  a document with a "signable" or "printable" extension. Adding methods to the base class bloats it and forces
  all subclasses to implement them.
- **Solution and participants:**
  - **the subject** with one method for accessing an extension by name or type, e.g. `getExtension("signature")`;
  - **extensions:** separate objects with an additional interface, attached to the subject;
  - the client asks for the extension and handles its absence.
- **When to use:** the set of additional interfaces is open, and which objects have them is decided
  at runtime, e.g. in plugins or in extensions added by other modules.
- **Costs:** the client must check whether the extension exists; the subject's interface stops saying what the object can do.
- **Difference:** Role Object concerns roles in the business model with a life cycle, while Extension Object concerns additional
  technical interfaces. Decorator keeps the interface and adds behaviour around the calls, while Extension Object
  adds a new interface alongside.
- **When NOT:** there are a few extensions and they are known up front; then an ordinary interface or a union type is enough.
  In TS a map of extensions keyed by type is often enough.

## Sources
- D. Bäumer, D. Riehle, W. Siberski, M. Wulf, "Role Object", PLoP '97; reprinted in *Pattern Languages of Program
  Design 4* (eds. N. Harrison, B. Foote, H. Rohnert), Addison-Wesley, 2000, pp. 15–32 [unverified: bibliographic
  data from catalogs and secondary sources, without reading the text in this session].
- E. Gamma, "Extension Object", in: *Pattern Languages of Program Design 3* (eds. R. Martin, D. Riehle, F. Buschmann),
  Addison-Wesley, 1998, ISBN 0201310112 [unverified: as above].
- Described in our own words; the scope based on the programme of the training "DDD — zaawansowane techniki modelowania
  i archetypy" ("DDD — advanced modelling techniques and archetypes"; Bottega IT Minds, material from a human, 2026-10-21).
