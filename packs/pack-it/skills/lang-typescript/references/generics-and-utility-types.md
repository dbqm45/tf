# Generics and built-in utility types

Based on the TypeScript Handbook ("Generics", "Utility Types"), described in our own words.
Examples checked in tsc 6.0.3 and 7.0.2 (`strict`, `noUncheckedIndexedAccess`).

## Generics

### Constraints (`extends`) and dependent parameters (`keyof`)
```ts
function loggingIdentity<T>(arg: T): T { console.log(arg.length); return arg; }   // ❌ no .length

interface Lengthwise { length: number }
function loggingIdentity2<T extends Lengthwise>(arg: T): T { console.log(arg.length); return arg; }

function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] { return obj[key]; }
getProperty({ a: 1, b: 2 }, "m"); // ❌ "m" is not a key
```

### Default type parameters
```ts
declare function create<T extends HTMLElement = HTMLDivElement, U extends HTMLElement[] = T[]>(
  element?: T, children?: U,
): { element: T; children: U };
const div = create(); // element: HTMLDivElement
```
Default parameters come after the required ones and must satisfy their own constraint.

### `const` type parameters (since TS 5.0) and `NoInfer` (since TS 5.4)
```ts
function identity<const T>(x: T): T { return x; }
const pair = identity(["a", "b"]);                 // readonly ["a", "b"] without `as const` at the caller

function withDefault<T extends string>(values: readonly T[], fallback: NoInfer<T>): T {
  return values[0] ?? fallback;
}
withDefault(["a", "b"], "c");                      // ❌ "c" does not widen T — it must be one of the values
```

### Rules for writing generics
1. Let it infer — `identity("x")`, not `identity<string>("x")`.
2. Constrain with `extends` when the body depends on properties of the type.
3. A generic constraint instead of a fixed union when the input → output relationship must be kept
   (`merge<T extends object, U extends object>(a: T, b: U): T & U`).
4. Do not multiply type parameters; a parameter used once in the signature is redundant.
5. A factory with a constructor type: `function make<T>(c: new () => T): T { return new c(); }`.
6. Generic interfaces for repeated shapes — e.g. a repository port (asynchronous, as in the domain):
   ```ts
   interface Repository<T, Id> {
     getById(id: Id): Promise<T | undefined>;
     save(item: T): Promise<void>;
   }
   ```

Checklist when refactoring generics:
- [ ] a generic instead of `any`?
- [ ] is `extends` needed? a dependency between parameters → `K extends keyof T`?
- [ ] a default type parameter instead of overloads?
- [ ] a type unreadable at first glance → split it into named pieces

---

## Built-in utility types

| Utility type | What it does | Example |
|---|---|---|
| `Partial<T>` / `Required<T>` | all fields optional / required | `Partial<Todo>` — a partial update |
| `Readonly<T>` | all fields `readonly` (shallow) | `Readonly<Todo>` |
| `Record<K, V>` | an object with keys `K` and values `V` | `Record<CatName, CatInfo>` — enforces the full set of keys |
| `Pick<T, K>` / `Omit<T, K>` | picks / removes fields | `Pick<Todo, "title" \| "done">` |
| `Exclude<U, M>` / `Extract<U, M>` | removes / keeps union members | `Exclude<"a"\|"b"\|"c", "a">` → `"b"\|"c"` |
| `NonNullable<T>` | removes `null`/`undefined` | `NonNullable<string \| undefined>` → `string` |
| `Parameters<F>` / `ReturnType<F>` | parameters (tuple) / result of a function | `ReturnType<typeof fn>` |
| `ConstructorParameters<C>` / `InstanceType<C>` | parameters / instance of a constructor | `InstanceType<typeof MyClass>` |
| `Awaited<T>` | recursively unwraps `Promise` | `Awaited<Promise<Promise<number>>>` → `number` |
| `NoInfer<T>` (5.4+) | blocks inference from this position | default values in generics |
| `ThisParameterType<F>` / `OmitThisParameter<F>` | the `this` type / removing `this` from the signature | rare, libraries |
| `ThisType<T>` | a marker of contextual `this` (`noImplicitThis`) | object builders |
| `Uppercase` / `Lowercase` / `Capitalize` / `Uncapitalize` | string literal transformations | `advanced-types.md` |

```ts
interface Todo { title: string; description: string; completed: boolean }
function updateTodo(todo: Todo, fields: Partial<Todo>): Todo { return { ...todo, ...fields }; }
type TodoPreview = Pick<Todo, "title" | "completed">;
type TodoInfo = Omit<Todo, "completed">;
type FnReturn = ReturnType<typeof updateTodo>;
```

Before you write out a variant of an existing type by hand — compose it from utility types. A hand-made copy is two places to
keep in sync. Exception: external contracts (API DTOs) deliberately independent of the domain model.
