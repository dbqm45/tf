---
name: lang-javascript
description: Use for plain JavaScript ES2022+ — coercion, closures, this, async and the event loop, arrays, ESM vs CommonJS.
metadata:
  review: "2027-04-17"
  catalog: "Use when writing and reviewing plain JavaScript code (ES2022+, browser or Node) — coercion and comparisons, scope and closures, this, classes, Promise/async and the event loop, array methods (mutating vs not), ESM vs CommonJS, errors — and domain concepts without TypeScript (JSDoc, Object.freeze, bigint). Not for browser APIs (fe-web-platform), TS typing (lang-typescript) or modelling (ddd-*)."
---

# JavaScript

Runtime behaviour — it also applies to TypeScript code (lang-typescript describes the types laid over the same thing).

## Language rules
- ES modules (`import`/`export`), `const` by default, no global variables and no `var`.
- `async/await`; every promise has error handling; parallel independent operations through `Promise.all`/`allSettled`.
- Do not swallow errors (`catch {}`) — handle, log or pass them on. Throw `Error` (or subclasses, with `cause`), not strings.
- No `eval`, `new Function`, `with`; `===` comparisons (exception: `x == null` catches `null` and `undefined`).
- Turn on `// @ts-check` and describe types in JSDoc — the editor checks the code without a migration to TypeScript.
- Before you add code, check the file's module system (ESM / CommonJS / a classic `<script>`) — do not mix syntaxes.

## Pitfalls — first suspects on a bug or in review
| Symptom | Likely cause → fix |
|---|---|
| a strange condition result | `==` with coercion (`"1" == 1`), `"0"` is truthy, `typeof null === "object"`, `NaN !== NaN` → `===`, `Number.isNaN`, `== null` |
| an array changed "by itself" | a mutating method (`sort`, `reverse`, `splice`, `fill`) → `toSorted`/`toReversed`/`toSpliced`/`with`; spread/`slice` copies are shallow → `structuredClone` |
| `undefined` in a Promise chain | a missing `return` in `.then()`; independent `await`s one after another → `Promise.all` |
| `catch` does not catch the error | an error in a callback (`setTimeout`, an event) outside the `try` → wrap it in a Promise and `await` |
| `finally` "eats" the result | `return`/`throw` in `finally` overrides the result → only cleanup in `finally` |
| `require is not defined` / `Cannot use import` | mixed ESM and CommonJS → check `"type"`, the `.mjs`/`.cjs` extension |
| `ReferenceError` in a subclass | `this` before `super()` |

## Domain concepts in JavaScript
| Concept (vocabulary) | JavaScript idiom |
|---|---|
| **value object** | a factory returning `Object.freeze({...})` with validation; amounts as `bigint` in the smallest unit |
| **entity** | an object with an `id` field and behaviour; identifiers wrapped in a factory so types are not mixed |
| **variants** | objects with a `kind` field + a `switch` with a `default: throw new Error('unhandled variant')` branch; in JSDoc `@typedef {A \| B}` |
| **operation result** | `{ ok: true, value }` / `{ ok: false, error }` — a business rejection without an exception |
| **aggregate** | a class with private `#state` fields, business methods returning a result, events handed out through `pullEvents()` |
| **state machine** | the state as an object `{ state: 'free' }` / `{ state: 'blocked', by }`, transitions in one method |
| **event** | a frozen object `{ type: 'ResourceBlocked', ... }` in the past tense |
| **policy** | a function passed to a factory/object |
| **repository** | an object/class with `async load/save`, the domain depends only on the shape (JSDoc `@typedef`) |
| **read model** | a plain frozen data object for a view |
| **module** | a file or directory with an `index.js` that exports only the public API |

The implementations from `lang-typescript/references/domain-building-blocks.md` carry over 1:1 after removing the types:
`#private` instead of `private`, `Object.freeze` instead of `readonly`, JSDoc instead of annotations.

## `references/` index (read only the file you need)
| File | Read when… |
|---|---|
| `types-and-comparisons.md` | `==` vs `===`, the coercion algorithm, `typeof`/`instanceof`, truthy/falsy |
| `scope-and-closures.md` | `var`/`let`/`const`, TDZ, closures, `var` in a loop, the cost of closures |
| `this-and-functions.md` | the `this` rules in every context, `call`/`apply`/`bind`, arrows |
| `classes-and-prototypes.md` | `#` fields, static blocks, `extends`/`super`, evaluation order, prototypes |
| `asynchrony.md` | Promise states, `all`/`allSettled`/`race`/`any`, micro- vs macrotasks |
| `iteration-and-arrays.md` | choosing a loop, mutating vs non-mutating methods, 10 pitfalls, newer array/Set APIs |
| `modules.md` | ESM vs CommonJS, live bindings, cycles, `require(esm)`, `import.meta` in Node |
| `errors-and-exceptions.md` | `try/catch/finally`, `Error.cause`, custom error classes, error types |

## ECMAScript / Node versions (check `target` and the environment)
| From | What you may use |
|---|---|
| ES2022 | `at()`, `Object.hasOwn`, `Error.cause`, `#` fields, `#x in obj`, static blocks, top-level `await` (ESM) |
| ES2023 | `toSorted`/`toReversed`/`toSpliced`/`with`, `findLast` |
| ES2024 | `Object.groupBy`/`Map.groupBy`, `Promise.withResolvers`, `Array.fromAsync` |
| ES2025 | `Set` methods (`union`…), iterator helpers, import attributes (`with { type: "json" }`), `Promise.try`, `RegExp.escape` |
| Node 22 | has ES2024 + `Set` methods and iterator helpers; **no** `Promise.try`, `RegExp.escape`, `using`, decorators; `require(esm)` from 22.12, ESM detection in `.js` from 22.7 |

## Checklist
- [ ] `// @ts-check` + JSDoc in domain files
- [ ] no money arithmetic on `number`
- [ ] every `switch` on `kind` has a `default` with an error
- [ ] no `==` (except `== null`), `for...in` on arrays, `var`
- [ ] no mutating methods on shared data; deep copies through `structuredClone`
- [ ] every promise handled; independent operations in parallel
- [ ] the file's module system matches `"type"`/the extension

Sources: MDN Web Docs (JavaScript Guide and Reference, CC-BY-SA content) — described in our own words.
