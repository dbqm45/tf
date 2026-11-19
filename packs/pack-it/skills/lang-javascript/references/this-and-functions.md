# `this` and functions

> **Contents:** The overriding principle · Table — `this` in every context · Plain functions — strict vs non-strict · Arrow functions — lexical `this` · `call`, `apply`, `bind` · Classes — `this` in the constructor and methods · Pitfalls

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Reference/Operators/this), described in our own words; examples checked in Node 22.

## The overriding principle

**`this` depends on HOW the function is CALLED, not on where it is DEFINED** (exception: arrow
functions — see below). The same function assigned to two objects gives a different `this`:

```js
function getThis() { return this; }
const obj1 = { name: "obj1" }, obj2 = { name: "obj2" };
obj1.getThis = getThis; obj2.getThis = getThis;
obj1.getThis(); // this === obj1
obj2.getThis(); // this === obj2 — the same function, a different result
```

## Table — `this` in every context

| Context | `this` |
|---|---|
| Global scope | script: `globalThis`; ESM module: `undefined`; a CommonJS file in Node: `module.exports` |
| `new MyClass()` | the newly created object |
| `fn.call(obj)` / `fn.apply(obj)` / `fn.bind(obj)()` | the explicitly given `obj` |
| Arrow function | `this` from the **enclosing scope at definition time** (lexical), impossible to change |
| `obj.method()` | `obj` (the object it was called on, even if the method lives in the prototype) |
| Plain function, strict mode | `undefined` |
| Plain function, non-strict mode | `globalThis` (the so-called "this substitution") |
| Event handler (`addEventListener`) | the element the handler was attached to (`currentTarget`) |
| Getter/setter | the object on which the property was accessed |
| Callback (`forEach`, `map`...) | usually `undefined`/`globalThis`, unless `thisArg` was given as the 2nd argument |

## Plain functions — strict vs non-strict

```js
function f() { "use strict"; return this; }
typeof f(); // "undefined" — strict: no substitution

function g() { return this; }
g() === globalThis; // true — non-strict: null/undefined this → globalThis
```

## Arrow functions — lexical `this`

An arrow function **has no `this` of its own** — it inherits it from the surroundings in which it was **defined**,
and this cannot be changed with `call`/`apply`/`bind`:

```js
const obj = {
  getThisGetter() {
    const inner = () => this; // closes over `this` from getThisGetter → this obj
    return inner;
  },
};
obj.getThisGetter()() === obj; // true

// BUT if we detach the outer method (not the arrow function itself):
const detached = obj.getThisGetter;
detached()() === globalThis; // true — because `this` in getThisGetter (a plain method) is already lost
```

**Practical rule:** an arrow function as a class field (`this.method = () => {...}` or
`method = () => {...}` as a class field) is the standard way to "pin" `this` permanently to the
instance — useful for callbacks/event handlers.

## `call`, `apply`, `bind`

```js
function add(c, d) { return this.a + this.b + c + d; }
const o = { a: 1, b: 3 };

add.call(o, 5, 7);   // 16 — this=o, arguments one by one
add.apply(o, [5, 7]); // 16 — this=o, arguments as an array

const bound = add.bind(o);
bound(5, 7); // 16 — this permanently set to o

bound.bind({ a: 100 })(5, 7); // still 16! — bind works only ONCE, a later bind does not override it
```

## Classes — `this` in the constructor and methods

```js
class C {
  constructor() { this.a = 37; }
}
new C().a; // 37

class Derived extends Base {
  constructor() { super(); /* only AFTER super() can this be used */ }
}
class Bad extends Base {
  constructor() {} // ReferenceError on new Bad(): must call super() before accessing/returning
}
```

Instance fields as arrow functions bind `this` permanently:
```js
class Car {
  constructor() { this.sayBye = this.sayBye.bind(this); } // alternative: field = arrow function
  sayHi() { console.log(`Hi from ${this.name}`); }
  sayBye() { console.log(`Bye from ${this.name}`); }
  get name() { return "Ferrari"; }
}
const car = new Car();
const bird = { name: "Tweety" };
bird.sayHi = car.sayHi;  bird.sayHi();  // "Hi from Tweety" — this = bird (an unbound method)
bird.sayBye = car.sayBye; bird.sayBye(); // "Bye from Ferrari" — this = car (bound in the constructor)
```

## Pitfalls

**A detached method:**
```js
const carSayHi = car.sayHi; // detached from the object
carSayHi(); // TypeError (strict mode) — this is undefined, not car
```
Solution: `.bind(this)` in the constructor, or a class field as an arrow function.

**A callback without `this`:**
```js
class Widget {
  constructor() { this.value = 1; }
  handle() { console.log(this.value); } // a plain method
}
const w = new Widget();
button.addEventListener("click", w.handle); // ❌ this in handle = the button, not w
button.addEventListener("click", () => w.handle()); // ✅ the arrow keeps this = w
button.addEventListener("click", w.handle.bind(w)); // ✅ an alternative
```

**`this` and `forEach`/`map`/other array callbacks:** the function passed in does **not** inherit
`this` from the enclosing method if it is a plain function declared separately — use an inline arrow function
or the second argument `thisArg`.
