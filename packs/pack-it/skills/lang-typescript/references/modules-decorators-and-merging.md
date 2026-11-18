# Modules, decorators and declaration merging

> **Contents:** Modules · Decorators · Declaration merging

Based on the TypeScript Handbook ("Modules", "Decorators", "Declaration Merging") and release notes 5.0–7.0,
described in our own words. Examples checked in tsc 6.0.3 and 7.0.2 (`strict`, `module: nodenext`).

## Modules

### Exports, imports, aliases
```ts
// maths.ts
export const pi = 3.14;
export function absolute(n: number) { return n < 0 ? -n : n; }
export default function helloWorld() { console.log("Hello"); }

// import — in ESM under `nodenext` with the `.js` extension (or `.ts` + `rewriteRelativeImportExtensions`)
import helloWorld, { pi, absolute as abs } from "./maths.js";
import * as math from "./maths.js";
```

### Type-only imports
```ts
import { createCatName, type Cat, type Dog } from "./animal.js"; // inline (4.5+)
import type { Cat, Dog } from "./animal.js";                     // the whole import is type-only
```
With `verbatimModuleSyntax` (recommended; it replaces `importsNotUsedAsValues`/`preserveValueImports`) a type import without
`type` is an error — and rightly so: bundlers/Node compiling file by file do not know what is a type.

### Interop with CommonJS
| Situation | Form |
|---|---|
| an ESM file imports a CJS package | `import pkg from "pkg"` (`esModuleInterop` — always on since TS 6.0; `false` removed in 7.0) |
| a `.cts` file / a CJS project | `import fs = require("node:fs")`, `export =` — **not** in ESM files, and an error with `erasableSyntaxOnly` |
| Node ≥ 22.12 | `require()` of an ESM module works (without top-level await) — fewer reasons for a dual package |

`module.exports = …` in a `.ts` file is a sign that the file should be `.cts` or rewritten to `export`.

### Dynamic import, script files
```ts
const math = await import("./maths.js");  // lazy loading (top-level await only in ESM)
export {};                                 // forces the file to be treated as a module
```
`moduleDetection: "force"` treats every file as a module without this trick.

### JSON import and import attributes
```ts
import data from "./data.json" with { type: "json" };   // ✅ import attributes
import data from "./data.json" assert { type: "json" }; // ❌ an error since TS 6.0 — `assert` replaced by `with`
```

### Rules
- Prefer named exports; `default` for a file's single main export.
- `export *` hides what the public API is — in a module's `index.ts` list the exports explicitly.
- Path aliases: `paths` relative to the tsconfig (without `baseUrl`, removed in 7.0) or `imports` in `package.json`
  (`#shared/*` — `domain-modeling-patterns.md`); aliases work at runtime only if the bundler/Node knows them.

---

## Decorators

Two **incompatible** implementations:

| | Standard (TC39) — **the default since TS 5.0** | Legacy (`experimentalDecorators: true`) |
|---|---|---|
| signature | `(value, context)` — `context: ClassMethodDecoratorContext` etc. | `(target, key, descriptor)` |
| parameter decorators | **none** | yes (`@Inject()` in the constructor) |
| `emitDecoratorMetadata` / `reflect-metadata` | none | yes |
| `accessor` (auto-accessors) | yes | no |
| where you meet them | new code, ES libraries | older NestJS, TypeORM, class-validator, Angular (the decorators are processed by the Angular compiler — fw-angular) |

Do not switch the mode in an existing project "while you are at it" — metadata-based libraries will stop working.
Decorators are not erasable syntax: Node 22 running TS by type stripping will not handle them (V8 does not
implement them yet) — a compiler/bundler is needed.

### Standard decorators (TS 5.0+)
```ts
// method decorator — returns a replacement function
function logged<This, Args extends unknown[], R>(
  target: (this: This, ...args: Args) => R,
  context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => R>,
) {
  return function (this: This, ...args: Args): R {
    console.log(`→ ${String(context.name)}`, args);
    return target.call(this, ...args);
  };
}

// decorator factory (parameterised)
function repeat(times: number) {
  return function <This, Args extends unknown[]>(
    target: (this: This, ...args: Args) => void,
    _context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => void>,
  ) {
    return function (this: This, ...args: Args): void {
      for (let i = 0; i < times; i++) target.call(this, ...args);
    };
  };
}

// auto-accessor decorator (`accessor` — TS 4.9+ syntax, decorating in 5.0+)
function nonNegative<This>(
  target: ClassAccessorDecoratorTarget<This, number>,
  _context: ClassAccessorDecoratorContext<This, number>,
): ClassAccessorDecoratorResult<This, number> {
  return { set(this: This, v: number) { if (v < 0) throw new RangeError("negative"); target.set.call(this, v); } };
}

// class decorator
function sealed<T extends abstract new (...args: never[]) => unknown>(value: T, _ctx: ClassDecoratorContext<T>) {
  Object.seal(value);
  Object.seal(value.prototype);
}

@sealed
class Calculator {
  @nonNegative accessor total = 0;
  @logged add(a: number, b: number) { return a + b; }
  @repeat(2) ping(msg: string) { console.log(msg); }
}
```
`context.addInitializer(fn)` runs code when an instance is created (e.g. registration, binding `this`);
`context.metadata` (TS 5.2, `Symbol.metadata`) replaces `reflect-metadata` in new code.

### Legacy (`experimentalDecorators`) — only for maintaining existing code
```ts
function logMethod(_target: object, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value as (...a: unknown[]) => unknown;
  descriptor.value = function (this: unknown, ...args: unknown[]) {
    console.log(key, args);
    return original.apply(this, args);
  };
}
function requiredParam(_target: object, _key: string | symbol | undefined, _index: number) { /* metadata */ }
class Report {
  @logMethod add(a: number, b: number) { return a + b; }
  print(@requiredParam verbose: boolean) { return verbose; } // parameters — legacy only
}
```
Order (both modes): decorator/factory expressions are evaluated top to bottom, the decorators themselves are applied
bottom to top; member decorators before the class decorator (the class last).

### Angular
The `@Component`, `@Injectable`/`@Service` decorators stay, but `@Input`/`@Output` and constructor DI
are replaced by the `input()`, `output()`, `inject()` functions — do not introduce new code on the old patterns (fw-angular).

---

## Declaration merging

### Interfaces
```ts
interface Box { height: number; width: number }
interface Box { scale: number }  // Box has height, width, scale
```
Methods with the same name become overloads; the later declaration takes precedence, signatures with literal
types go to the front.

### Namespace + function/class/enum
```ts
function buildLabel(name: string): string { return buildLabel.prefix + name; }
namespace buildLabel { export let prefix = "Hello, "; }   // a namespace with a value — an error with erasableSyntaxOnly
```
New code: assigning a property to the function (`buildLabel.prefix = "Hello, "` — TS understands it since 3.1) or
a companion object; `namespace` only in declaration files (`declare namespace`). The `module` keyword instead of `namespace`
(`module Foo {}`) is deprecated since TS 6.0.

### Module augmentation — extending library types
```ts
declare module "./observable.js" {
  interface Observable<T> { map<U>(f: (x: T) => U): Observable<U> }
}
declare module "node:http" {
  interface IncomingMessage { userId?: string }
}
declare global {
  interface Window { appVersion?: string }
}
```
A file with `declare module`/`declare global` must be a module (have an `import`/`export`). This is the right way instead of
`as any` scattered across the call sites.

### What can merge

| Declaration | creates a namespace | creates a type | creates a value | merges with `namespace` |
|---|---|---|---|---|
| namespace | yes | — | yes (if it has values) | yes |
| class | — | yes | yes | yes |
| enum | — | yes | yes | yes |
| interface | — | yes | — | yes (the "type + companion" pattern) |
| type alias | — | yes | — | yes |
| function | — | — | yes | yes |
| variable (`const`/`let`) | — | — | yes | no |

These do not merge: two classes, a class and a variable, a variable and a namespace with values, two `type`s with the same name.
A type + a `const` with the same name (the type and the value in separate spaces) is the simplest "companion" without a namespace.
