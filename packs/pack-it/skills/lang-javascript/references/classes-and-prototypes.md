# Classes and prototypal inheritance

> **Contents:** Syntax basics · Private fields (`#`) · Inheritance — `extends` and `super` · Evaluation order (summary) · Classes vs prototype-based "under the hood" · Pitfalls · In TypeScript

Based on MDN Web Docs (developer.mozilla.org/docs/Web/JavaScript/Reference/Classes), described in our own words; examples checked in Node 22.

## Syntax basics

```js
class Rectangle {
  height = 0;          // a public field with a default value
  #width;               // a private field (accessible only inside the class)

  constructor(height, width) { this.height = height; this.#width = width; }

  get area() { return this.height * this.#width; }   // getter
  set width(w) { if (w <= 0) throw new Error("bad width"); this.#width = w; }

  calcPerimeter() { return 2 * (this.height + this.#width); } // method

  static defaultUnit = "cm";                    // a static field (on the class, not the instance)
  static create(h, w) { return new Rectangle(h, w); } // a static method

  static { console.log("class initialized"); }  // a static initialisation block
}
```

**Important properties of classes:**
- Classes are **not hoisted** like `function` — they are subject to the Temporal Dead Zone like `let`/`const`.
  A class cannot be used before its declaration in the code.
- The class body always runs **in strict mode**, even without `"use strict"`.
- Only **one** `constructor` — a second declaration is a `SyntaxError`.
- A call without `new` (`Rectangle(1,2)`) throws a `TypeError` — classes require `new`, unlike
  functions.

## Private fields (`#`)

```js
class Account {
  #balance = 0;
  deposit(amount) { this.#balance += amount; }
  get balance() { return this.#balance; }
}
const a = new Account();
a.#balance; // SyntaxError outside the class — it is not a convention, the language enforces it
```

Rules: private names must be unique in the class and declared in its body (anywhere —
they do not have to be at the top); you cannot add `this.#x = 1` without a `#x;` declaration. Checking "does the object
have a private field": `#balance in obj` (ES2022) — safer than `instanceof` across realms.

## Inheritance — `extends` and `super`

```js
class Animal {
  constructor(name) { this.name = name; }
  speak() { console.log(`${this.name} makes a noise.`); }
}
class Dog extends Animal {
  constructor(name) { super(name); } // MUST come first — before `this` is used
  speak() { super.speak(); console.log(`${this.name} barks.`); } // super.method() = a call to the parent
}
```

**An absolute rule:** a derived class (`extends`) must call `super()` in the constructor **before**
any use of `this` — otherwise a `ReferenceError`. If you do not define your own constructor,
JS inserts a default one that calls `super(...args)` itself.

## Evaluation order (summary)

1. `extends` is evaluated first.
2. The `constructor` is extracted (or a default one is inserted).
3. Property keys are evaluated in declaration order, methods are installed on the `prototype`
   (instance ones) or on the class itself (static ones).
4. Instance field values are computed **at the start of the constructor** (before its body, after `super()` in
   derived classes); static fields are computed with `this` = the class itself.
5. Static initialisation blocks run in declaration order.

## Classes vs prototype-based "under the hood"

Classes are **syntactic sugar** over the same prototype mechanism that has existed in JS since
the beginning:

```js
// The same behaviour, pre-ES6 style:
function Animal() {}
Animal.prototype.speak = function () { console.log("sound"); };
```

Differences worth remembering: classes are not hoisted (functions are), classes require `new`
(functions do not), the class body is always in strict mode, `super` is available only in classes.

## Pitfalls

**A method detached from the instance loses `this`** (see also `this-and-functions.md`):
```js
class Animal { speak() { return this; } }
const speak = new Animal().speak;
speak(); // undefined (strict mode) — this is lost
```
Solution: a class field as an arrow function (`speak = () => this;`) or `.bind(this)` in the
constructor.

**A forgotten `super()` in a derived constructor** → a `ReferenceError` on every `new`.

**Duplicate public field names are allowed, but confusing** — the last declaration wins, without
a warning:
```js
class C { x = 1; x = 2; } // syntactically OK
new C().x; // 2
```

**Private fields cannot be created dynamically** — `this.#foo = 1` in a method works only if
`#foo` was declared in the class body; an attempt to add a new private field "on the fly" is a
`SyntaxError`.

## In TypeScript

TS `private`/`protected` disappear at runtime — only `#` gives real privacy. Details of classes in TS
(modifiers, `override`, parameter properties): lang-typescript `.claude/skills/lang-typescript/references/functions-objects-classes.md`.
