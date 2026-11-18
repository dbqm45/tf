# Functions, object types and classes

> **Contents:** Functions · Object types · Classes

Based on the TypeScript Handbook ("More on Functions", "Object Types", "Classes"), described in our own words.
Examples checked in tsc 6.0.3 and 7.0.2 (`strict`, `noUncheckedIndexedAccess`).

## Functions

### Function types, call and construct signatures
```ts
type GreetFunction = (a: string) => void;            // the parameter name is required by the syntax

type DescribableFunction = {
  description: string;
  (someArg: number): boolean;                         // call signature — a function with extra fields
};

type SomeConstructor = new (s: string) => SomeObject; // construct signature
```
Avoid the global `Function` type (a call returns `any`) — type a concrete signature.

### Generic functions — rules
```ts
function firstElement<T>(arr: readonly T[]): T | undefined { return arr[0]; }
function longest<T extends { length: number }>(a: T, b: T): T { return a.length >= b.length ? a : b; }
```
- Constrain the element (`T extends { length: number }`), not the whole (`T extends any[]`), unless you have to.
- A type parameter should appear **at least twice** in the signature; otherwise replace it with a concrete type.
- Do not pass the type argument explicitly (`identity<string>("x")`) when inference is enough.
- More: `generics-and-utility-types.md`.

### Optional parameters in callbacks and variance
```ts
function f(x?: number) {}   // x: number | undefined
function g(x = 10) {}       // x: number

// ❌ `index?` in the callback type suggests the caller may not pass it — and that is what happens:
function myForEach<T>(arr: readonly T[], cb: (arg: T, index?: number) => void) {
  for (const item of arr) cb(item); // index never passed
}
```
Declare a callback with **required** parameters — a function that takes fewer arguments still fits.
With `strictFunctionTypes` (part of `strict`), parameters of function types are checked contravariantly, but
**method** parameters (`method(x: T): void` in an interface) stay bivariant — for strict checking
in interfaces use the property syntax: `handle: (x: T) => void`.

### `this` in functions (not in an arrow function)
```ts
interface DB { filterUsers(filter: (this: User) => boolean): User[] }
db.filterUsers(function (this: User) { return this.admin; }); // ✅ `this` typed
db.filterUsers(() => this.admin);                              // ❌ an arrow takes `this` from the surrounding scope
```

### Overloads
```ts
function makeDate(timestamp: number): Date;
function makeDate(m: number, d: number, y: number): Date;
function makeDate(mOrTs: number, d?: number, y?: number): Date {
  if (d !== undefined && y !== undefined) return new Date(y, mOrTs, d);
  return new Date(mOrTs);
}
makeDate(1, 2); // ❌ the implementation signature is NOT visible from outside
```
- The overload signatures stand above the implementation; from outside **only the overloads** are visible, and the implementation must
  be compatible with each of them.
- When a union is enough — use a union instead of overloads:
  ```ts
  function len(x: string | readonly unknown[]): number { return x.length; }
  ```

### `void`, `unknown`, `never` as a result
```ts
type VoidFunc = () => void;
const f1: VoidFunc = () => true;                 // OK — the result is ignored (contextual void)
function f2(): void { return true; }             // ❌ in an explicit declaration it is an error
function fail(msg: string): never { throw new Error(msg); }
```

---

## Object types

### `?`, `readonly`, index signatures
```ts
interface Options { shape: Shape; xPos?: number }
interface Locked { readonly id: string }
interface Dict {
  [key: string]: number | string; // ordinary fields must be compatible with the index signature
  length: number;
}
```
`exactOptionalPropertyTypes` (outside `strict`) distinguishes "no field" from `xPos: undefined` — worth switching on in new code.

### Excess property checks
```ts
interface SquareConfig { color?: string; width?: number }
createSquare({ colour: "red", width: 100 }); // ❌ 'colour' does not exist
```
It works only for a literal passed directly; use the workarounds (an assertion, an index signature, an intermediate variable)
deliberately — the error usually points to a typo.

### Extending, generic shapes, `readonly` arrays, tuples
```ts
interface ColorfulCircle extends Colorful, Circle {}
type ColorfulCircle2 = Colorful & Circle;

interface Box<T> { contents: T }

function f(v: readonly string[]) { v.push("x"); } // ❌ readonly
let ro: readonly string[] = []; let m: string[] = [];
ro = m; // ✅   m = ro; // ❌

type Pair = [string, number];
type Optional3rd = [number, number, number?];
type RestTuple = [string, ...boolean[]];
const point = [3, 4] as const; // readonly [3, 4]
```
A function that only reads data: a `readonly T[]` / `Readonly<T>` parameter — it documents the intent and blocks mutation.

---

## Classes

### Fields, `readonly`, `strictPropertyInitialization`
```ts
class Point {
  x = 0;
  y = 0;
  readonly id: string;               // initialise in the constructor or immediately
  constructor(id: string) { this.id = id; }
}
```
`name!: string` (definite assignment) only when a framework/initialiser sets the field outside the constructor.

### `public` / `protected` / `private` vs `#`
```ts
class Example {
  public x = 0;
  protected y = 0;
  private z = 0;       // type checking only — accessible at runtime (`obj["z"]`)
  #realPrivate = 0;    // truly private (JS), also at runtime
}
```
- In new code, `#field` by default for internal state (aggregates — `domain-building-blocks.md`).
- `protected` does not give access to the members of a sibling subclass of the same base.
- `implements Interface` does not carry parameter types over to the methods: a parameter without an annotation is an implicit `any`
  (an error in `strict`). Annotate method parameters explicitly.
- Overriding: `override` + `noImplicitOverride` — the compiler detects a method rename in the base.

### Static members, generic classes
```ts
class MyClass { static x = 0; static printX() { console.log(MyClass.x); } }

class Box<T> {
  readonly contents: T;
  constructor(contents: T) { this.contents = contents; }
  // static defaultValue: T; // ❌ static fields do not see the class's type parameters
}
```

### Polymorphic `this`, `this`-based guards
```ts
class Box2 { contents = ""; set(v: string) { this.contents = v; return this; } }
class Clearable extends Box2 { clear() { this.contents = ""; } }
new Clearable().set("hi").clear(); // set returns Clearable, not Box2

class FSObject { isFile(): this is FileRep { return this instanceof FileRep; } }
```

### Parameter properties — only with non-erasable syntax
```ts
class Service {
  constructor(private readonly http: HttpClient) {} // creates a field + an assignment
}
```
- It is code-generating syntax: **an error with `erasableSyntaxOnly`**, and it does not work when TS is run by type
  stripping (Node). In new code declare the field explicitly (`readonly #http: HttpClient;` + an assignment in the constructor).
- Angular: modern DI is `inject()` in a field (`private readonly http = inject(HttpClient)`) — details in fw-angular.
  Changing constructor parameters in classes with DI is a change of the contract with the framework.

### Abstract classes, `implements` vs `extends`
```ts
abstract class BaseService {
  abstract getData(): unknown;
  processData() { return this.getData(); }
}
class UserService extends BaseService { getData() { return { id: 1 }; } }
```
- `implements X` — the class fulfils the `X` contract, it inherits nothing.
- `extends X` — inherits the implementation; prefer composition when there is no real "is a" relationship.

### Runtime pitfalls

**`super()` before `this`** in a subclass constructor.

**Initialisation order:** base fields → base constructor → subclass fields → subclass constructor.
```ts
class Base { name = "base"; constructor() { console.log(this.name); } }
class Derived extends Base { override name = "derived"; }
new Derived(); // logs "base"
```
If the base needs a value from the subclass — pass it as a constructor argument.

**Losing `this` when passing a method as a reference** (handlers, `setTimeout`, `.subscribe(this.m)`):
```ts
class C {
  name = "C";
  getName() { return this.name; }       // `this` depends on how it is called
  getNameBound = () => this.name;        // arrow field: always the instance
}
setTimeout(c.getName);                   // ❌
setTimeout(c.getNameBound);              // ✅  (or: () => c.getName(), c.getName.bind(c))
```
Runtime mechanics of `this`: lang-javascript `.claude/skills/lang-javascript/references/this-and-functions.md`.
