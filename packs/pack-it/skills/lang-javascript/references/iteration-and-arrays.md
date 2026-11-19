# Iteration, loops and array methods

> **Contents:** Which loop type, when · ⚠️ `for...in` on an array is a pitfall — never do it · `forEach` does not support `break`/`continue` · Array methods — mutating vs non-mutating · 10 concrete pitfalls · `break`/`continue` with a label (rare, but sometimes needed… · Newer APIs (check `target`/the environment)

Based on MDN Web Docs (Guide/Loops_and_iteration, Reference/Global_Objects/Array), described in our own words;
examples checked in Node 22.

## Which loop type, when

| Loop | When | Values or keys | break/continue |
|---|---|---|---|
| `for` | a known number of iterations, index control needed | index | yes |
| `for...in` | iterating over **object properties** | property names (strings!) | yes |
| `for...of` | iterating over **values** of iterables (Array, Map, Set, String) | values | yes |
| `forEach` | an array, functional style, you do not need to break | value + index | **no** (see the pitfall) |
| `while` | a dynamic condition, a number of iterations not known in advance | — | yes |
| `do...while` | the body must run **at least once** | — | yes |

## ⚠️ `for...in` on an array is a pitfall — never do it

```js
const arr = [3, 5, 7];
arr.foo = "hello"; // an extra property on the array (rare, but possible)

for (const i in arr) console.log(i);   // "0" "1" "2" "foo"  ❌ — strings + own properties
for (const v of arr) console.log(v);   // 3 5 7               ✅ — only the array values
```
`for...in` iterates over **properties** (including ones inherited from the prototype and ones added
by hand), returns their names as strings, and does not guarantee order. For arrays always `for...of` or
`for`.

## `forEach` does not support `break`/`continue`

```js
arr.forEach((n) => { if (n === 3) break; }); // ❌ SyntaxError — break does not work in a callback
arr.forEach((n) => { if (n === 3) return; }); // ✅ return = "continue" (skips the rest of the callback BODY, not the loop)
```
If you need to stop the iteration early — use `for...of` with `break`, or `some()`/
`every()` (which **can** stop early, unlike `forEach`).

## Array methods — mutating vs non-mutating

**Mutating** (they change the array in place and often return something other than a new array):
`push`, `pop`, `shift`, `unshift`, `splice`, `sort` ⚠️, `reverse`, `fill`, `copyWithin`.

**Non-mutating** (they return a new array/value, the original is unchanged):
`map`, `filter`, `slice`, `concat`, `flat`, `flatMap`, `find`, `findIndex`, `includes`, `indexOf`,
`every`, `some`, `reduce`, `join`, `at`, and the **ES2023 equivalents** of the mutating ones:
`toSorted`, `toReversed`, `toSpliced`, `with`.

| Mutating | Non-mutating equivalent (ES2023+) |
|---|---|
| `sort()` | `toSorted()` |
| `reverse()` | `toReversed()` |
| `splice()` | `toSpliced()` |
| `arr[i] = v` (a single element) | `arr.with(i, v)` |

## 10 concrete pitfalls

**1. `sort()` sorts lexicographically (as strings), not numerically:**
```js
[10, 5, 40, 25, 1000].sort();           // [10, 1000, 25, 40, 5] ❌ (as strings)
[10, 5, 40, 25, 1000].sort((a, b) => a - b); // [5, 10, 25, 40, 1000] ✅
```

**2. `sort()`/`reverse()`/`splice()` mutate the original:**
```js
const arr = [3, 1, 2];
const sorted = arr.sort();
sorted === arr; // true — it is THE SAME array, not a copy
```
If you do not want to mutate: `arr.toSorted()` (ES2023) or `arr.slice().sort(...)` (older engines).

**3. `reduce()` without `initialValue` on a short/empty array:**
```js
[].reduce((a, b) => a + b);        // TypeError: Reduce of empty array with no initial value
[5].reduce((a, b) => a - b);       // 5 — the first element used as the start, no reduction happened
[1,2,3,4].reduce((s, n) => s + n, 0); // 10 — ALWAYS give initialValue, unambiguous behaviour
```

**4. Mutating an array while iterating over it:**
```js
arr.forEach((el, i, a) => { if (i === 1) a.splice(2, 1); }); // unpredictable skips
// safer: iterate over a copy — arr.slice().forEach(...)
```

**5. Copies (`slice()`, spread `[...arr]`) are SHALLOW:**
```js
const original = [{ id: 1 }];
const copy = original.slice();
copy[0].id = 999;
original[0].id; // 999 — the objects inside are still the same references!
```
A deep copy: `structuredClone(original)` (modern) or `JSON.parse(JSON.stringify(original))`
(older, loses functions/`undefined`/`Date` etc.).

**6. `find()` vs `filter()` — a different result type:**
```js
arr.find(x => x > 2);   // a single value or undefined
arr.filter(x => x > 2); // ALWAYS an array (may be empty)
```

**7. `indexOf(NaN)` does not find `NaN`, but `includes(NaN)` does:**
```js
[NaN].indexOf(NaN);   // -1  (uses === internally, NaN !== NaN)
[NaN].includes(NaN);  // true (uses SameValueZero — treats NaN as equal to itself)
```

**8. Empty slots (sparse arrays) — older methods skip them:**
```js
const arr = [1, , 3]; // arr[1] is a "hole", not undefined
arr.map(x => x * 2);  // [2, <empty>, 6] — the hole stays a hole, the callback was not called for it
Array.from(arr);      // [1, undefined, 3] — Array.from fills holes as undefined
```

**9. `for...in` on an array** — see the separate section above, it is one of the most common mistakes.

**10. `Map`/`Set` iterated with `for...of`, not `for...in`:**
```js
const m = new Map([["a", 1]]);
for (const [k, v] of m) { /* ... */ }        // ✅ for...of + destructuring
for (const [k, v] of Object.entries(obj)) {} // for a plain object — Object.entries + for...of
```

## `break`/`continue` with a label (rare, but sometimes needed for nested loops)

```js
outer: for (const a of listA) {
  for (const b of listB) {
    if (shouldStopAll(a, b)) break outer;    // leaves BOTH loops
    if (shouldSkipA(a, b)) continue outer;   // moves to the next `a`, skipping the rest of `b`
  }
}
```

## Newer APIs (check `target`/the environment)

| API | From | Instead of |
|---|---|---|
| `at(-1)` | ES2022 | `arr[arr.length - 1]` |
| `findLast`, `findLastIndex` | ES2023 | `slice().reverse().find()` |
| `toSorted`, `toReversed`, `toSpliced`, `with` | ES2023 | a copy + a mutating method |
| `Object.groupBy`, `Map.groupBy` | ES2024 | `reduce` into a dictionary (the `groupBy` result has a `null` prototype) |
| `Array.fromAsync` | ES2024 | a `for await` loop with `push` |
| `Set` methods (`union`, `intersection`, `difference`…) | ES2025 | manual filtering |
| iterator helpers (`iter.map/filter/take/toArray`) | ES2025 | `Array.from(iter).map(...)` (lazily, without a copy) |
