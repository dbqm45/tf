# Asynchrony: Promise, async/await, event loop

> **Contents:** Promise states · `.then()` always returns a NEW Promise · ⚠️ Rule #1: always `return` in `.then()`, otherwise a… · Error handling — `.catch()` · `Promise.all` / `allSettled` / `race` / `any` · Sequential vs parallel `await` — a common performance… · `async`/`await` — sugar over Promise, not a different… · ⚠️ Pitfall: `try/catch` does NOT catch an error from an… · Microtask queue vs macrotask (event loop)

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Guide/Using_promises), described in our own words; examples checked in Node 22.

## Promise states

A Promise has one of three states, irreversibly: **pending** → **fulfilled** or **rejected**.

```js
const p = new Promise((resolve, reject) => { /* async operation */ });
Promise.resolve(value);  // fulfilled at once
Promise.reject(error);   // rejected at once
```

## `.then()` always returns a NEW Promise

```js
const p2 = p.then(onFulfilled, onRejected); // p2 !== p
```

## ⚠️ Rule #1: always `return` in `.then()`, otherwise a floating promise

```js
// ❌ BUG — no return, the next .then() does NOT wait for fetch()
doSomething().then((url) => { fetch(url); })
             .then((result) => console.log(result)); // undefined — fetch has not finished yet

// ✅ CORRECT
doSomething().then((url) => { return fetch(url); })
             .then((result) => console.log(result)); // the proper response
```

This is one of the most common real bugs in Promise code — a missing `return` creates a **race
condition**: code further down the chain runs before the inner operation actually finishes.

## Error handling — `.catch()`

`.catch()` catches an error from **any** earlier step in the chain (the equivalent of `try/catch` for
synchronous code):

```js
doSomething()
  .then((r) => doSomethingElse(r))
  .then((r2) => doThirdThing(r2))
  .catch(failureCallback); // catches an error from doSomething, doSomethingElse OR doThirdThing
```

Code after `.catch()` in the chain **continues to run normally**, even after the error was caught:
```js
doSomething()
  .then(() => { throw new Error("x"); })
  .catch(() => console.error("handled"))   // runs
  .then(() => console.log("runs anyway")); // RUNS — .catch() "repaired" the chain
```

**Unhandled rejection** — a Promise rejected without `.catch()`/without a `try/catch` around `await`:
```js
window.addEventListener("unhandledrejection", (e) => console.error(e.reason)); // browser
process.on("unhandledRejection", (reason) => console.error(reason));           // Node.js
```

## `Promise.all` / `allSettled` / `race` / `any`

| Method | Waits for | Result on an error |
|---|---|---|
| `Promise.all([...])` | all | rejects the whole on the **first** rejected |
| `Promise.allSettled([...])` | all, always | never rejects — returns `{status, value/reason}` per Promise |
| `Promise.race([...])` | the first settled (fulfilled **or** rejected) | the result/error of that first one |
| `Promise.any([...])` | the first **fulfilled** | `AggregateError` if all are rejected |

```js
const [r1, r2] = await Promise.all([func1(), func2()]); // both in parallel
const results = await Promise.allSettled([func1(), func2()]); // none "breaks" the rest
```

## Sequential vs parallel `await` — a common performance problem

```js
// ❌ needlessly sequential — func2 waits for func1 even though they are independent
const r1 = await func1();
const r2 = await func2();

// ✅ parallel — both start immediately
const [r1, r2] = await Promise.all([func1(), func2()]);
```

Sequential `await` is right **only** when the second operation really depends on the result of
the first — otherwise it is an unnecessary delay that is easy to fix.

## `async`/`await` — sugar over Promise, not a different mechanism

```js
// Identical behaviour:
doSomething().then((url) => fetch(url)).then((r) => r.json()).then((d) => console.log(d));

async function run() {
  const url = await doSomething();
  const r = await fetch(url);
  const d = await r.json();
  console.log(d);
}
```

Error handling with `async/await` — a plain `try/catch` (see `errors-and-exceptions.md`):
```js
async function main() {
  try {
    const result = await doSomething();
    return await doSomethingElse(result);
  } catch (error) {
    failureCallback(error);
  }
}
```

## ⚠️ Pitfall: `try/catch` does NOT catch an error from an asynchronous callback

```js
// ❌ the catch never runs — the setTimeout callback runs outside this try
try {
  setTimeout(() => { throw new Error("boom"); }, 1000);
} catch (e) { console.error(e); } // useless

// ✅ wrapping in a Promise + await brings the error back to where try/catch works
async function safe() {
  try {
    await new Promise((_, reject) => setTimeout(() => reject(new Error("boom")), 1000));
  } catch (e) { console.error(e); } // now it works
}
```

## Microtask queue vs macrotask (event loop)

Promise callbacks (`.then`, `await`) go to the **microtask queue**, which is drained
**before** the next macrotask (e.g. `setTimeout`, even with a `0` delay):

```js
Promise.resolve().then(() => console.log("promise"));
setTimeout(() => console.log("timeout"), 0);
console.log("sync");
// order: "sync", "promise", "timeout" — ALWAYS, even though it looks symmetrical
```

**Practical rule:** `async`/Promise-based code is always asynchronous, even if the Promise
is already `resolved` when it is created — the callback still goes to the microtask queue, it does not
run synchronously in place.
