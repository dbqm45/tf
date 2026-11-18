# Modules: ES Modules (ESM) vs CommonJS

> **Contents:** Two module systems — do not mix them thoughtlessly · ES Modules — syntax · CommonJS — syntax · When which — a practical rule · Pitfalls · Node — the state as of 22.x

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Guide/Modules), described in our own words; examples checked in Node 22.

## Two module systems — do not mix them thoughtlessly

| Aspect | ES Modules (ESM) | CommonJS |
|---|---|---|
| Syntax | `import`/`export` | `require()`/`module.exports` |
| Analysis | static (imports known before execution) | dynamic (`require` is an ordinary function call) |
| Top-level `await` | yes | no |
| Strict mode | always, automatically | optional |
| Live bindings (see below) | yes | no (a copy of the value at the moment of `require`) |
| Loading/evaluation | the import graph is loaded and linked before execution; modules run once, in dependency order | synchronously, at the moment `require` is called |
| Environment | browser (`<script type="module">`), Node with `"type":"module"`/`.mjs` | Node by default (`.js` without `"type":"module"`), `.cjs` |

**Rule:** check which system the file/project lives in **before** you add code — `import` in a
CommonJS file (or `require` in an ESM file) is a syntax/runtime error, not a stylistic preference.

## ES Modules — syntax

```js
// square.js
export const name = "square";
export function draw() { /* ... */ }
export default function mainExport() { /* ... */ } // one default per module

// main.js
import mainExport, { name, draw } from "./square.js"; // default + named at once
import { draw as drawSquare } from "./square.js";      // alias
import * as Square from "./square.js";                  // everything as a namespace object
```

**Dynamic import** — returns a Promise, also works in non-module files:
```js
const module = await import("./square.js"); // top-level await or in an async function
```

**Live bindings** — the imported value tracks changes in the source module (it is not a copy from
import time):
```js
// counter.js
export let count = 0;
export function increment() { count++; }
// main.js
import { count, increment } from "./counter.js";
console.log(count); // 0
increment();
console.log(count); // 1 — it changed, because it is a live binding
count = 5;           // ❌ TypeError: count is read-only — an import cannot be assigned
```

**Modules are always in strict mode and have their own scope** (not the global one) — a variable declared at
module top level does not leak into `window`/`globalThis`.

## CommonJS — syntax

```js
// maths.js
function absolute(n) { return n < 0 ? -n : n; }
module.exports = { pi: 3.14, absolute };

// main.js
const { pi, absolute } = require("./maths.js");
const maths = require("./maths.js"); // the whole module.exports object
```

`require()` is **synchronous and eager** — the module code runs exactly at the moment of
`require()`, not earlier/later; the result is cached (a second `require()` of the same path does not
run the module again, it returns the same object from the cache).

## When which — a practical rule

- **Node.js, a script/server without a framework that dictates otherwise** → check `package.json`
  (`"type": "module"`?) and the file extension (`.mjs`/`.cjs` win regardless of `package.json`).
  No `"type"` = CommonJS, but from Node 22.7 a `.js` file with ESM syntax is detected and loaded as ESM
  (extra parsing; a warning when there is a `package.json` without `"type"` next to it) — set `"type"` explicitly.
- **Browser** → ESM requires `<script type="module">` and an HTTP server (it does not work from `file://` —
  a CORS error); without `type="module"` it is a "classic script" with CommonJS not available natively (it needs
  a bundler).
- **The same project can have both** (e.g. build tooling in CommonJS, application code in ESM) — do not
  assume one system for the whole repo without checking per file/folder.

## Pitfalls

**Circular imports** — module A imports B, which imports A back: in ESM it works partially
(live bindings let you read the value *later*, but not at import time if it has not yet
been exported); in CommonJS `require()` of a cycle returns a **partially filled** `module.exports`
object (whatever managed to run before the cycle) — a common cause of
`undefined is not a function` with a wrong import order.

**Mixing syntaxes in one file** — `import` in a file without `type="module"`/`.mjs` gives
`SyntaxError: Cannot use import statement outside a module`; `require` in a real ESM module gives
`ReferenceError: require is not defined`.

**Testing modules through `file://`** — ESM in the browser requires an HTTP server; opening an
`.html` file with modules directly from disk (`file://`) throws a CORS error on import.

**An import is not a variable to assign** — `import { x } from "./m.js"; x = 5;` is always an error in
ESM (a read-only binding); in CommonJS `const { x } = require(...)` is an ordinary assignment, so
that local variable is normally mutable (although changing `x` locally does not affect the source module
— it is a copy of the value, not a reference to it).

## Node — the state as of 22.x

- `require()` of an ESM module works from Node 22.12 (without a flag), as long as the module does not use top-level `await` — CJS can
  consume ESM packages; the other way round, ESM imports CJS through `import pkg from "pkg"` (default = `module.exports`).
- In ESM there is no `__dirname`/`__filename`/`require` — use `import.meta.dirname`, `import.meta.filename`
  (Node 20.11+), `import.meta.url`, or possibly `createRequire(import.meta.url)`.
- JSON import: `import data from "./data.json" with { type: "json" }` (import attributes; the old `assert` was withdrawn).
- Built-in modules with the `node:` prefix (`import { readFile } from "node:fs/promises"`).
- Internal aliases: the `imports` field in `package.json` (`"#shared/*": "./src/shared/*"`) instead of relative `../../..`.
