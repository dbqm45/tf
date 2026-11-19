# Advanced types: keyof, typeof, indexed access, conditional, mapped, template literal

> **Contents:** `keyof` · `typeof` in a type context (not runtime) · Indexed access types (`Type["prop"]`) · Conditional types · Mapped types · Template literal types · The cost of complex types

Based on the TypeScript Handbook ("Type Manipulation": keyof, typeof, indexed access, conditional, mapped,
template literal types), described in our own words. Examples checked in tsc 6.0.3 and 7.0.2 (`strict`).

## `keyof`

```ts
type Point = { x: number; y: number };
type P = keyof Point; // "x" | "y"

type Mapish = { [k: string]: boolean };
type M = keyof Mapish; // string | number (JS always converts keys to string)

type Arrayish = { [n: number]: unknown };
type A = keyof Arrayish; // number
```

The most common practical use — safe access to a property by name:
```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
```

## `typeof` in a type context (not runtime)

```ts
let s = "hello";
type S = typeof s; // string — extracts the type FROM A VARIABLE, does not check at runtime

class C { x = 0; }
type CType = typeof C; // the constructor type, not the instance type — see InstanceType in generics-and-utility-types.md
```

## Indexed access types (`Type["prop"]`)

```ts
type Person = { age: number; name: string; alive: boolean };
type Age = Person["age"];              // number
type NameOrAge = Person["name" | "age"]; // string | number
type AnyValue = Person[keyof Person];    // string | number | boolean

// An array element via number:
const arr = [{ name: "A", age: 1 }];
type Elem = (typeof arr)[number];        // { name: string; age: number }

// typeof is needed when you index with a variable, not a type alias:
const key = "age";
type AgeViaVar = Person[typeof key];    // OK
type Bad = Person[key];                  // ❌ 'key' is a value, not a type
```

## Conditional types

### Basic syntax
```ts
type Example = Dog extends Animal ? number : string;
```

### With generics — this is where they become useful
```ts
type NameOrId<T extends number | string> = T extends number ? IdLabel : NameLabel;
function createLabel<T extends number | string>(x: T): NameOrId<T> { throw new Error("unimplemented"); }
```

### The constraint must be in the condition, not in the field access itself
```ts
// ❌ T has no guarantee of a "message" field
type MessageOf<T> = T["message"];

// ✅
type MessageOf<T> = T extends { message: unknown } ? T["message"] : never;
```

### `infer` — extracting a type inside the condition
```ts
type Flatten<T> = T extends Array<infer Item> ? Item : T;
type Str = Flatten<string[]>; // string

type GetReturn<T> = T extends (...args: never[]) => infer R ? R : never;
type R1 = GetReturn<() => number>; // number
```

### Distributive vs non-distributive
```ts
// Distributive — a conditional type on a union "distributes" over each member
type ToArray<T> = T extends unknown ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]

// Non-distributive — [] around extends switches this distribution off
type ToArrayNonDist<T> = [T] extends [unknown] ? T[] : never;
type Result2 = ToArrayNonDist<string | number>; // (string | number)[]
```
**Rule:** if the result of a conditional type on a union looks "split per element" where
you expect one type for the whole union (or the reverse) — check whether `T` in the condition is bare
(distributive) or wrapped in `[T]` (non-distributive). This is a common cause of "why doesn't my type
match" in complicated generics.

## Mapped types

### The basis: `[K in Keys]`
```ts
type OptionsFlags<T> = { [P in keyof T]: boolean };
```

### `+`/`-` modifiers on `readonly` and `?`
```ts
type CreateMutable<T> = { -readonly [P in keyof T]: T[P] };   // removes readonly
type Concrete<T> = { [P in keyof T]-?: T[P] };                 // removes optionality
```

### Key remapping with `as` — usually with template literal types
```ts
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};
interface Person { name: string; age: number; }
type LazyPerson = Getters<Person>; // { getName: () => string; getAge: () => number }

// Filtering keys with Exclude:
type RemoveKindField<T> = { [P in keyof T as Exclude<P, "kind">]: T[P] };

// Mapping a discriminated union by its discriminant field:
type EventConfig<E extends { kind: string }> = { [K in E as K["kind"]]: (e: K) => void };
```

### Combination with conditional types
```ts
type ExtractPII<T> = { [P in keyof T]: T[P] extends { pii: true } ? true : false };
```

**Refactoring rule:** when you see several hand-written, almost identical types that differ
only by a modifier (`readonly`, `?`) or a field name prefix (`getX`, `setX`) — it is a candidate for
one mapped type instead of N separate declarations that must be kept in sync by hand.

## Template literal types

```ts
type World = "world";
type Greeting = `hello ${World}`; // "hello world"

// Unions in interpolation → the cross-product of all combinations
type Lang = "en" | "pl";
type Id = "welcome" | "footer";
type Keys = `${Lang}_${Id}`; // "en_welcome" | "en_footer" | "pl_welcome" | "pl_footer"
```

A practical pattern — type-safe event names derived from an object's keys:
```ts
type PropEventSource<T> = {
  on<K extends string & keyof T>(
    eventName: `${K}Changed`,
    cb: (newValue: T[K]) => void
  ): void;
};
declare function watch<T>(obj: T): T & PropEventSource<T>;

const person = watch({ firstName: "John", age: 30 });
person.on("firstNameChanged", (v) => v.toUpperCase()); // v: string, inferred
person.on("ageChnaged", () => {}); // ❌ the literal type catches the typo at compile time
```

Intrinsic string manipulation types used in template literals: `Uppercase<S>`, `Lowercase<S>`,
`Capitalize<S>`, `Uncapitalize<S>` (table in `generics-and-utility-types.md`).

**When to reach for this in a refactor:** wherever you have a string-based API (event names, configuration
keys, paths) built by concatenation and so far typed as a bare `string` — template
literal types can usually turn it into one fully checked by the compiler, without changing runtime
behaviour.
## The cost of complex types

Deeply recursive conditional/mapped types slow down compilation and the editor (also in native TS 7) and give
unreadable errors. Name the intermediate steps with aliases, limit recursion, and when a type needs a comment longer
than the code itself — consider a simpler contract. Diagnostics: `tsc --extendedDiagnostics`, `--generateTrace`.
