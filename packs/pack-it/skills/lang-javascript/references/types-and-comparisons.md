# Types, coercion and comparisons

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Reference/Operators/Equality), described in our own words; examples checked in Node 22.

## `==` (loose equality) vs `===` (strict equality)

- **`===`** — never converts types; operands of different types are always different.
- **`==`** — tries to convert operands of different types before comparing (coercion).

### The coercion algorithm for `==` (summary)

1. **The same type** → a comparison like `===` (Object: the same reference; String: the same characters;
   Number: the same value, `NaN` is never equal to anything, `+0 == -0`; Boolean/BigInt/Symbol:
   literal equality).
2. **`null`/`undefined`** — if one operand is `null` or `undefined`, the other must also be
   `null`/`undefined`, otherwise `false`. This is a **special rule**: `null == undefined` → `true`,
   but `null === undefined` → `false`.
3. **Object + primitive** — the object is converted to a primitive (`valueOf`/`toString`).
4. **Primitive + primitive of different types** — Boolean→Number (`true`→`1`), Number+String→the String
   is converted to a Number, Symbol+anything → `false` (no conversion).

### Table of examples

```js
"1" == 1;                  // true  (string → number)
0 == false;                 // true  (false → 0)
0 == null;                  // false (null only == null/undefined)
0 == undefined;              // false
null == undefined;           // true  (special rule)
NaN == NaN;                  // false (NaN is never equal to anything, not even itself)
+0 == -0;                    // true

const o1 = { k: "v" }, o2 = { k: "v" };
o1 == o2;                    // false (different objects, the same content)
o1 == o1;                    // true  (the same reference)

[1, 2, 3] == "1,2,3";        // true  (array → string through toString())
```

## When to use which

**By default: `===`.** It is predictable, does not require understanding the coercion algorithm, and prevents
subtle bugs (`"1" == 1` is often unintended).

```js
if (value === 0) { /* ... */ }
if (status === "active") { /* ... */ }
```

**`==` deliberately, in one idiomatic case:** checking "is it `null` or `undefined`",
both at once, with one comparison:

```js
if (value == null) {
  // true for value === null OR value === undefined
}
// instead of the longer:
if (value === null || value === undefined) { /* ... */ }
```

Outside this one case, a use of `==` in code review is a signal to ask "is this
intended", not the default practice.

## `typeof` and `instanceof`

- `typeof` returns a string: `"string"`, `"number"`, `"bigint"`, `"boolean"`, `"symbol"`,
  `"undefined"`, `"object"`, `"function"`.
- **A historical pitfall:** `typeof null === "object"` — a bug rooted in JS from the start, it cannot
  be fixed without breaking backward compatibility. To check for `null` use `=== null`, not `typeof`.
- `instanceof` checks the prototype chain (`obj instanceof MyClass`) — it works for objects created
  with `new`/classes, not for primitives or objects from another context (e.g. an `iframe`, another
  realm — there `instanceof Array` can fail even though it really is an array).

## Truthy / Falsy

Falsy (exactly these values, everything else is truthy): `false`, `0`, `-0`, `0n` (BigInt zero),
`""`, `null`, `undefined`, `NaN`.

**A pitfall:** `"0"` (a string) is **truthy** (a non-empty string), `0` (a number) is falsy — easy
to confuse with data from a form/URL, where values are often strings.
