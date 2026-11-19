# Type system basics and narrowing

> **Contents:** 1. Type annotations, inference, erasure · 2. `any` vs `unknown` · 3. Basic types · 4. `type` vs `interface` · 5. Assertions: `as`, `!`, `as const`, `satisfies` · 6. `enum` vs a literal union · Narrowing — narrowing techniques

Based on the TypeScript Handbook ("The Basics", "Everyday Types", "Narrowing"), described in our own words.
Examples checked in tsc 6.0.3 and 7.0.2 (`strict`, `noUncheckedIndexedAccess`).

## 1. Type annotations, inference, erasure

- **Annotate function parameters** — it is the only place where TypeScript has nothing to infer the type from:

  ```ts
  function greet(person, date) { /* ... */ }            // ❌ implicit any (an error in strict)
  function greet(person: string, date: Date) { /* ... */ } // ✅
  ```

- **Do not annotate what TypeScript infers anyway** (`let msg = "hello"` already has the type `string`).
  Exception: an explicit result type of public functions (a contract — rule 7 in SKILL.md).
- **Annotations are removed at compilation** — they cost nothing at runtime, but they also check nothing at runtime.
- **Typing existing code step by step:** start with function parameters — they immediately reveal mismatches
  at the call sites.

## 2. `any` vs `unknown`

| `any` | `unknown` |
|---|---|
| switches off type checking and "infects" further expressions | a safe alternative |
| you can call anything | you must narrow before use |
| the error escapes to runtime | the error is caught at compilation |

```ts
let a: any = { x: 0 };
a.foo(); // no compile error — it blows up at runtime

let u: unknown = { x: 0 };
u.foo(); // ❌ error — you must narrow
if (typeof u === "object" && u !== null && "foo" in u && typeof u.foo === "function") {
  u.foo(); // ✅ narrowed without `as` (since TS 4.9 `in` adds the property to the type)
}
```

New code: `unknown`, not `any`. `noImplicitAny` (part of `strict`) turns an implicit `any` into an error.

## 3. Basic types

```ts
let numbers: number[] = [1, 2, 3];
let strings: Array<string> = ["a", "b"];
let tuple: [number, string] = [42, "hi"];           // exact number and order

function printName(obj: { first: string; last?: string }) {
  console.log(obj.last?.toUpperCase());            // undefined must be handled
}

function printText(s: string, alignment: "left" | "right" | "center") {}
printText("Hi", "centre"); // ❌ literal type — only the listed values
```

With `noUncheckedIndexedAccess`, `numbers[0]` has the type `number | undefined` — handle a missing element (`?? default`, a guard).

## 4. `type` vs `interface`

| | `type` | `interface` |
|---|---|---|
| extending | `&` (intersection) | `extends` |
| declaration merging | no | yes |
| union, tuple, primitive, mapped/conditional types | yes | no |
| object shape | possible | usually preferred (clearer errors) |

```ts
type ID = number | string;
type Point = { x: number; y: number };
type Bear = Point & { honey: boolean };

interface Animal { name: string }
interface Bear2 extends Animal { honey: boolean }
```

**A conflict in `&`** on incompatible fields gives `never` on that field — with no error at the declaration:
```ts
interface A { name: string }
interface B { name: number }
declare const x: A & B;
x.name; // type: never
```
(`extends` reports an error immediately on such a conflict — another argument for `interface` for object shapes.)

## 5. Assertions: `as`, `!`, `as const`, `satisfies`

```ts
const canvas = document.getElementById("c") as HTMLCanvasElement; // only when the types "overlap"
const x = "hello" as unknown as number;                           // double assertion — DANGEROUS
```

`as` does not fix a type error — it is a declaration "I know better than the compiler" that you must be able to justify
(e.g. after validation). By default, narrow (a guard) instead of asserting.

```ts
function f(x?: number | null) {
  console.log(x!.toFixed());               // ! = "definitely not null/undefined" — risky
  if (x != null) console.log(x.toFixed()); // ✅ narrowing
}
```

**`as const`** — the narrowest, immutable literal type (`"GET"` instead of `string`):
```ts
const req = { url: "/x", method: "GET" } as const; // req.method: "GET"
```

**`satisfies`** (since TS 4.9) — checks compatibility with a type **without widening** the inferred type:
```ts
const cfg = { port: 8080, host: "localhost" } satisfies Record<string, string | number>;
cfg.port; // number (not string | number)
```

## 6. `enum` vs a literal union

```ts
enum Direction { Up = 1, Down, Left, Right }                  // generates JS code; an error with erasableSyntaxOnly
type Direction2 = "Up" | "Down" | "Left" | "Right";           // purely type-level
const DIRECTIONS = ["Up", "Down", "Left", "Right"] as const;  // + an array of values for iteration
type Direction3 = (typeof DIRECTIONS)[number];
```

- New code: a literal union / `as const` (the "type + companion" pattern with `is()` and `values` →
  `domain-modeling-patterns.md`). `enum` and `const enum` do not work with `--erasableSyntaxOnly` or with running
  TS by type stripping alone (Node).
- Do not replace existing `enum`s "while you are at it" — the values are often serialised (API, database); that is a separate migration.

---

## Narrowing — narrowing techniques

### `typeof`
```ts
function padLeft(padding: number | string, input: string) {
  if (typeof padding === "number") return " ".repeat(padding) + input;
  return padding + input;
}
```
Values: `"string" | "number" | "bigint" | "boolean" | "symbol" | "undefined" | "object" | "function"`.
Pitfall: `typeof null === "object"`.

### Truthiness
```ts
function printAll(strs: string | string[] | null) {
  if (strs && typeof strs === "object") for (const s of strs) console.log(s);
}
```
Falsy: `0`, `-0`, `NaN`, `""`, `0n`, `null`, `undefined`, `false` — watch out for `0` and `""` as valid values.

### Equality
```ts
function example(x: string | number, y: string | boolean) {
  if (x === y) x.toUpperCase(); // x: string — the only common type
}
if (value != null) value.trim(); // `!= null` removes both null and undefined at once
```

### `in`, `instanceof`
```ts
type Fish = { swim: () => void };
type Bird = { fly: () => void };
function move(a: Fish | Bird) { return "swim" in a ? a.swim() : a.fly(); }

function logValue(x: Date | string) {
  if (x instanceof Date) console.log(x.toUTCString()); else console.log(x.toUpperCase());
}
```

### Control flow analysis
TypeScript tracks the *observed* type of a variable after every assignment and every branch:
```ts
let x: string | number | boolean;
x = Math.random() < 0.5;             // boolean
if (cond) { x = "a"; } else { x = 1; }
// here: string | number
```

### Type predicates (`pet is Fish`)
```ts
function isFish(pet: Fish | Bird): pet is Fish { return "swim" in pet; }
const fishes: Fish[] = animals.filter(isFish);

// since TS 5.5 the predicate is inferred from simple lambdas:
const nums = [1, undefined, 2].filter((x) => x !== undefined); // number[]
```
A predicate is a promise the compiler does not check — a wrong implementation gives false narrowing.

### Discriminated unions + an exhaustive `switch`
```ts
interface Circle { kind: "circle"; radius: number }
interface Square { kind: "square"; sideLength: number }
type Shape = Circle | Square;

export function assertNever(x: never): never { throw new Error(`unhandled: ${JSON.stringify(x)}`); }

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2; // shape: Circle
    case "square": return shape.sideLength ** 2;       // shape: Square
    default: return assertNever(shape);                // a compile error after adding a variant
  }
}
```
Every branch on the discriminant field has a `default` with `assertNever` — only then does the compiler report
an unhandled new variant (and at runtime an unknown value from the network throws an error instead of passing silently).
