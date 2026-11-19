# Variable scope and closures

> **Contents:** `var` vs `let`/`const` · What a closure is · Use: the module pattern / private state · The classic pitfall: `var` in a loop · Closures and ES modules — live bindings · Performance/memory — when closures are a problem

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Closures), described in our own words; examples checked in Node 22.

## `var` vs `let`/`const`

| | `var` | `let`/`const` |
|---|---|---|
| Scope | function (function scope) | block (`{}`, block scope) |
| Hoisting | hoisted, initialised to `undefined` | hoisted, but in the **Temporal Dead Zone** until the declaration |
| Redeclaration in the same scope | allowed | `SyntaxError` |

```js
if (Math.random() > 0.5) { var x = 1; } else { var x = 2; }
console.log(x); // 1 or 2 — a block does NOT create a scope for var

if (Math.random() > 0.5) { const y = 1; } else { const y = 2; }
console.log(y); // ReferenceError: y is not defined — it does not exist outside the block
```

**Rule:** `const` by default, `let` when the value changes, `var` practically never in new
code — `let`/`const` give a more predictable scope and more predictable closures (see the pitfall
below).

## What a closure is

Closure = a function + a reference to its **lexical environment** (the scope in which it was
defined). Created automatically for every function in JS — it is not an opt-in feature.

```js
function makeAdder(x) {
  return function (y) {
    return x + y; // a closure over `x` from the outer scope
  };
}
const add5 = makeAdder(5);
add5(2); // 7 — `x=5` lives on, even though makeAdder() has already returned
```

Every call to `makeAdder` creates a **new, independent** lexical environment — `add5` and `add10` have
their own, separate copies of `x`.

## Use: the module pattern / private state

```js
const counter = (function () {
  let privateCounter = 0; // not accessible from outside
  function changeBy(val) { privateCounter += val; }
  return {
    increment() { changeBy(1); },
    decrement() { changeBy(-1); },
    value() { return privateCounter; },
  };
})();

counter.increment(); counter.increment();
counter.value(); // 2 — privateCounter is not accessible other than through these 3 methods
```

Calling the same factory (`makeCounter()`) twice would give two **independent** counters — each
call creates its own lexical environment.

## The classic pitfall: `var` in a loop

```js
// ❌ BUG — all callbacks see the same, last value of item
for (var i = 0; i < items.length; i++) {
  var item = items[i];
  el[i].onfocus = function () { showHelp(item.help); }; // always the last item.help
}
```

**Cause:** `var` has function scope — there is **one** `item` variable shared by all
closures created in the loop; after the loop ends it points to the last element.

**Fixes (from the oldest to the recommended one):**
```js
// 1) Function factory — a new lexical environment per call
function makeCallback(help) { return function () { showHelp(help); }; }
for (var i = 0; i < items.length; i++) { el[i].onfocus = makeCallback(items[i].help); }

// 2) IIFE — a new block scope through a function call
for (var i = 0; i < items.length; i++) {
  (function () { const item = items[i]; el[i].onfocus = () => showHelp(item.help); })();
}

// 3) let/const — RECOMMENDED: every iteration has its own block binding
for (let i = 0; i < items.length; i++) {
  const item = items[i];
  el[i].onfocus = () => showHelp(item.help);
}
```

## Closures and ES modules — live bindings

```js
// counter.js
export let count = 0;
export function increment() { count++; }
```
An import in another module sees a **live** binding — after `increment()` reading `count` at the import site
changes too (it is not a copy taken at import time). See `modules.md`.

## Performance/memory — when closures are a problem

```js
// ❌ suboptimal — every instance gets ITS OWN copy of the method (a closure per instance)
function MyObject(name) {
  this.name = name;
  this.getName = function () { return this.name; }; // a new function on every `new`
}

// ✅ methods shared through the prototype — one function for all instances
function MyObject(name) { this.name = name; }
MyObject.prototype.getName = function () { return this.name; };
```

**Rule:** if a method does not need to close over something instance-specific (apart from `this`,
which it gets from the call anyway), define it on the `prototype`/in the class body, not as a field
assigned in the constructor — otherwise you pay a new function allocation for every instance.
