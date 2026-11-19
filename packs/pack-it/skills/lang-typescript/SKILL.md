---
name: lang-typescript
description: Use for TypeScript 5.x–7.x code — types, narrowing, generics, tsconfig, validation at boundaries, domain concepts.
metadata:
  review: "2027-04-17"
  catalog: "Use when writing, refactoring and reviewing TypeScript 5.x–7.x code — types, narrowing, generics, decorators, modules, tsconfig, validation at boundaries, TS/npm security pitfalls and domain concepts (value object, variants, aggregate, result) in TS idioms. Not for JS runtime mechanics (lang-javascript), a framework (fw-*), general auth principles (be-auth-security) or modelling (ddd-*)."
  keywords: "TypeScript types, mixing up IDs, customer ID and order ID, branded type, amounts as number, model money in TypeScript"
---

# TypeScript

## Language rules
1. `strict: true` (preferably also `noUncheckedIndexedAccess`) is non-negotiable. You do not switch rules off to make the code compile.
2. No `any`. An unknown type → `unknown` + narrowing (a type guard, a schema validator at the boundary).
3. No `as` to "silence" the compiler; `as const`, `satisfies` and a cast after validation are allowed.
4. `// @ts-ignore` is forbidden; `// @ts-expect-error` only with a comment saying why.
5. Types of external contracts in one place (or generated from OpenAPI/JSON Schema) — no duplicates.
6. Discriminated unions instead of many optional flags; an exhaustive `switch` with `assertNever` in `default`.
7. Public functions have an explicitly typed result; data is `readonly` by default.
8. Data from the network, storage, URLs, forms and env is `unknown` until you validate it — the type from the validator
   (`z.infer<typeof Schema>` or an equivalent) is the only source of truth. Types are not a defence → `references/security.md`.

## Pitfalls and decisions (summary)
| Situation | Rule |
|---|---|
| `interface` / `type` | object shape → `interface`; union, tuple, mapped/conditional type → `type`; a conflict in `&` gives `never` |
| `enum`, `namespace`, parameter properties | new code: a literal union + a companion; these constructs break `erasableSyntaxOnly` |
| changing a public API | a new field is `?` first; widening a parameter / narrowing a result is safe, the reverse — check the call sites |
| generics, overloads | a type parameter used once is redundant; only the overload signatures are visible from outside; when a union is enough — a union |
| classes | `#field` instead of `private` (disappears at runtime); `override`; a method passed as a reference loses `this`; the base does not see the subclass's fields |
| decorators | standard TC39 (5.0+) ≠ legacy `experimentalDecorators` (parameters, `reflect-metadata`) — do not switch the mode in an existing project |
| library types | module augmentation / `declare global`, not `as any` at the call sites |

## Configuration (tsconfig) — a style compatible with TS 6/7
- Explicitly: `"strict": true`, `"rootDir"`, `"types": [...]` (since 6.0 the default is `[]` — put e.g. `["node", "vitest/globals"]`),
  `"moduleResolution": "bundler"` (applications with a bundler) or `"nodenext"` (Node/libraries), `"verbatimModuleSyntax": true`.
- No `baseUrl` (aliases in `paths` relative to the tsconfig directory), no `moduleResolution: node/node10/classic`,
  no `module: amd/umd/system/none`, no `target: es5`, no `outFile`; `esModuleInterop` always on.
- Running TS by type stripping in Node → `erasableSyntaxOnly`; decorators and `using` on Node 22 need compilation anyway.
- The framework decides the TS version: check its constraints (e.g. Angular 22 → TS 6.0.x) — **do not raise TS above the framework's range**.

## Domain concepts in TypeScript
| Concept (glossary) | TypeScript idiom |
|---|---|
| **value object** | a class with a `private constructor` + a `static of()` factory, `readonly` fields, operations return new instances; amounts as `bigint` in the smallest unit (never `number` in calculations) |
| **identifier / entity** | a branded type `string & { __brand: 'PartyId' }` — you cannot mix up IDs of different entities |
| **variants** | a discriminated union with a `kind`/`type` field + an exhaustive `switch` and `assertNever` |
| **operation result** | `type Result<E, T> = { ok: true; value: T } \| { ok: false; error: E }` — a rejection with a reason instead of an exception |
| **aggregate** | a class with private state, changes only through business methods returning `Result`, events collected and handed over by `pullEvents()` |
| **state machine** | a union of states (`{ state: 'free' } \| { state: 'blocked'; by }`) — invalid states are unrepresentable |
| **event** | an immutable object in a union of events, named in the past tense (`type: 'ResourceBlocked'`) |
| **policy** | a function type (`(ctx: Ctx) => Money`) or a strategy interface; the policy is chosen in a factory |
| **specification** | predicates `(x: T) => boolean` composed with `and/or/not` functions |
| **repository / port** | an `interface` in the domain (async), the implementation (HTTP, database, memory) outside the domain |
| **read model** | a flat `readonly` type matched to the view/query, without business methods |
| **module** | a directory with an `index.ts` exporting only the public interface; import rules (e.g. eslint `no-restricted-imports`) guard the boundaries |

## Index of `references/` (read only the file you need)
| File | Read when… |
|---|---|
| `domain-building-blocks.md` | you implement Money, Quantity, Party, TimeSlot, Result, an aggregate with events |
| `domain-modeling-patterns.md` | type + companion, internal vs published events, decider, `#imports`, date pitfalls |
| `basics-and-narrowing.md` | `any`/`unknown`, `type`/`interface`, assertions, `satisfies`, `enum`, narrowing |
| `functions-objects-classes.md` | signatures, overloads, variance, excess property checks, classes, `this` |
| `generics-and-utility-types.md` | constraints, `const T`, `NoInfer`, utility types |
| `advanced-types.md` | `keyof`, conditional types (`infer`), mapped, template literal |
| `modules-decorators-and-merging.md` | type imports, CJS interop, standard/legacy decorators, `accessor`, merging |
| `security.md` | external input, SQL/NoSQL, object merge, JWT, secrets, URLs, npm dependencies |

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 5.0 | standard decorators (TC39; legacy only with `experimentalDecorators` — the only mode with parameter decorators and `emitDecoratorMetadata`), `const` in type parameters, `moduleResolution: bundler`, `verbatimModuleSyntax` |
| 5.2 | `using` / `await using` (at runtime: Node 24+ or transpilation — Node 22 does not know them), decorator metadata (`context.metadata`) |
| 5.4 | `NoInfer<T>` |
| 5.5 | inferred type predicates (`filter(x => x !== undefined)` narrows the type), RegExp syntax checking |
| 5.7 | `rewriteRelativeImportExtensions` (imports `./x.ts` rewritten to `.js`) |
| 5.8 | `--erasableSyntaxOnly` (code runnable by type stripping, e.g. Node): an error for `enum`, `namespace` with values, parameter properties, `import x = require` |
| 5.9 | the last 5.x line; a minimal, modern `tsc --init` |
| 6.0 | **changed defaults**: `strict: true`, `module: esnext`, `target: es2025`, `types: []`, `rootDir: .` (error TS5011 when you do not set it), `noUncheckedSideEffectImports: true`; **deprecated** (error TS5101/5107, temporarily `"ignoreDeprecations": "6.0"`; removed in 7.0): `target: es5`, `downlevelIteration`, `moduleResolution: node/node10/classic`, `baseUrl`, `module: amd/umd/system/none`, `outFile`, `esModuleInterop: false`, the `module` keyword for a namespace; `assert` in imports → an error (use `with`); `tsc file.ts` with an existing tsconfig ends with an error (`--ignoreConfig`); `--stableTypeOrdering` to prepare for 7.0; new: `es2025`, Temporal types, `#/` imports |
| 7.0 | **native compiler (Go), ~10× faster**; the options deprecated in 6.0 are **removed** (TS5102/5108); no programmatic API until 7.1 — tools that use the API (Angular, typescript-eslint, loaders) still need TS 6 → install `@typescript/typescript6` (`tsc6`) alongside; new flags `--checkers`, `--builders`, `--singleThreaded`; legacy decorators still supported |

Migrating 5.x → 6.0 in practice: set `rootDir` and `types`, replace `baseUrl` with `paths`, `moduleResolution` with `bundler`/`nodenext`;
test with `--stableTypeOrdering` before moving to 7.0. The `domain-*.md` code is checked in 5.9/6.0/7.0, the other
references in 6.0.3/7.0.2 (legacy/`enum` examples are marked).

## Checklist
- [ ] `tsc --noEmit` with no errors in the project's TS version (and within the range the framework requires)
- [ ] no new `any`, `as`, `@ts-ignore`; no `as`/`!` on external data
- [ ] variants handled exhaustively
- [ ] domain code without framework imports
- [ ] new code without `enum`/`namespace`/parameter properties when the project uses `erasableSyntaxOnly` or type stripping

Sources: the TypeScript Handbook and release notes 5.0–7.0 (typescriptlang.org, devblogs.microsoft.com) — described in our own words.
