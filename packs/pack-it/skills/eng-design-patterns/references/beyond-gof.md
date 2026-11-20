# Patterns outside GoF: Role Object and Extension Object

Two structural patterns from the later PLoP catalogs. Both are alternatives to boolean flag fields and to a base
class that keeps growing for the sake of a few clients. See also the modelling side of the same problem in
`.claude/skills/ddd-deep-modeling/references/untangling.md`.

## Role Object
- **Problem:** one entity plays several roles at once or over time, e.g. a company is our customer, later also our
  supplier; a person is a student and becomes a teaching assistant. Each role has its own data, rules and life cycle.
  Putting `isCustomer`, `isSupplier`, `creditLimit`, `paymentTerms` into one class makes it grow without limit.
  Subclassing does not help either: combinations explode (`CustomerSupplier`, `StudentAssistant`) and an object
  cannot change its class when a role starts or ends.
- **Structure:**
  - a **core object** with the identity and the data shared by all roles (name, tax id, contact);
  - **role objects**, one per role, holding only role-specific data and behaviour and a link to the core;
  - the core exposes `hasRole(type)`, `getRole(type)`, `addRole(role)`, `removeRole(type)`; clients ask for the
    role they need instead of checking flags.
  ```ts
  const supplier = company.getRole(SupplierRole);
  if (supplier) supplier.schedulePickup(order);
  ```
- **Use when:** roles are independent of each other, are added and removed at run time, and have their own rules or
  their own owner in the organisation.
- **Costs:** identity is split across several objects (equality and caching must go through the core); a role must
  never outlive its core; decide explicitly which data is shared and lives in the core.
- **In a domain model:** a role frequently grows into its own aggregate, often in another bounded context, that
  refers to the party only by id (a `Supplier` in purchasing, a `Customer` in sales). The business-level counterpart
  is the party and party-relationship archetype (`.claude/skills/ddd-archetypes/references/parties-and-relationships.md`).
- **Do not use when:** the "role" carries no data or rules of its own and only changes what the user may do, e.g. an
  admin flag. That is an attribute or an authorization concern, not a role object.

## Extension Object
- **Problem:** some clients need an extra interface on an object (export, signing, watermarking, an accounting view),
  others never use it, and the set of such interfaces is not known when the base class is written. Adding every one
  to the base class bloats it and forces all subclasses to implement things they do not care about.
- **Structure:**
  - a **subject** with one generic accessor, e.g. `getExtension(key)` or `getExtension(Type)`;
  - **extension objects** implementing the additional interface and attached to the subject, typically by the
    module that provides the capability;
  - the **client** asks for the extension it needs and must handle the case that it is missing.
  ```ts
  const signing = doc.getExtension(Signable);
  if (!signing) return reject("document cannot be signed");
  await signing.sign(user);
  ```
- **Use when:** the set of extensions is open and decided at run time, e.g. capabilities contributed by plugins or by
  modules the core does not depend on.
- **Costs:** every client has to check for presence; the subject's own interface no longer tells you what it can do,
  so documentation and tests of the registered extensions matter more.
- **Compared with neighbours:**
  - Role Object models business roles with a life cycle; Extension Object adds (often technical) interfaces.
  - Decorator keeps the same interface and wraps calls (logging, caching); Extension Object offers a *new* interface
    next to the subject without wrapping it.
- **Do not use when:** there are two or three capabilities known up front. A plain interface, a union type, or in
  TypeScript a typed map of optional capabilities is simpler and checked by the compiler.

## Sources
- D. Bäumer, D. Riehle, W. Siberski, M. Wulf, "Role Object", PLoP '97; reprinted in *Pattern Languages of Program
  Design 4* (eds. N. Harrison, B. Foote, H. Rohnert), Addison-Wesley, 2000, pp. 15–32 [unverified: bibliographic
  data from catalogs and secondary sources, without reading the text in this session].
- E. Gamma, "Extension Object", in: *Pattern Languages of Program Design 3* (eds. R. Martin, D. Riehle, F. Buschmann),
  Addison-Wesley, 1998, ISBN 0201310112 [unverified: as above].
