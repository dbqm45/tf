# Errors and exceptions: try/catch/finally

> **Contents:** Syntax — three forms · Optional catch binding and destructuring · Conditional handling by error type, and re-throw · Custom error classes and `Error.cause` · ⚠️ `finally` with `return`/`throw` OVERRIDES the result… · `finally` always runs, even with an unhandled error · Nested try/catch — an error is caught only by the nearest… · Async — `try/catch` does not catch an error from a… · Catalogue of built-in error types (MDN Reference)

Based on MDN Web Docs (Reference/Statements/try...catch, built-in error types), described in our own words;
examples checked in Node 22.

## Syntax — three forms

```js
try { risky(); } catch (e) { handle(e); }                    // try...catch
try { risky(); } finally { cleanup(); }                       // try...finally
try { risky(); } catch (e) { handle(e); } finally { cleanup(); } // the full form
```

`try`/`catch`/`finally` **must** be `{}` blocks — `try foo(); catch (e) bar();` is a `SyntaxError`.

## Optional catch binding and destructuring

```js
try { JSON.parse(text); return true; }
catch { return false; } // the error parameter is omitted, it is not needed

try { throw new TypeError("oops"); }
catch ({ name, message }) { console.log(name, message); } // "TypeError" "oops"
```

## Conditional handling by error type, and re-throw

```js
try { myRoutine(); }
catch (e) {
  if (e instanceof TypeError) { /* handle */ }
  else if (e instanceof RangeError) { /* handle */ }
  else { throw e; } // an unknown error — pass it on, do not "swallow" it silently
}
```

**Rule:** do not catch an error you cannot handle meaningfully — re-throw is better than
a silent `catch (e) {}`, which hides real problems.

## Custom error classes and `Error.cause`

```js
class ValidationError extends Error {
  constructor(message) { super(message); this.name = "ValidationError"; }
}

try { throw new ValidationError("Field required"); }
catch (e) { if (e instanceof ValidationError) console.log(e.message); }

// Error.cause — a causal chain of errors (useful when wrapping a lower-level error)
try {
  try { throw new Error("Database error"); }
  catch (dbError) { throw new Error("Cannot load the user", { cause: dbError }); }
} catch (e) {
  console.error(e.message);        // "Cannot load the user"
  console.error(e.cause.message);  // "Database error"
}
```

## ⚠️ `finally` with `return`/`throw` OVERRIDES the result from `try`/`catch`

```js
function doIt() {
  try { return "from try"; }
  finally { return "from finally"; } // this wins — the function returns "from finally"!
}

function doIt2() {
  try { throw "from try"; }
  catch { throw "from catch"; }
  finally { return "from finally"; } // return in finally STOPS the throw from propagating!
}
```

**Rule:** avoid `return`/`throw`/`break`/`continue` in `finally` — their effect is surprising
(it overrides the result from `try`/`catch`) and hard to predict in review. `finally` should be used
only for **cleaning up resources** (closing a connection, removing a listener), not for returning
values.

## `finally` always runs, even with an unhandled error

```js
try { throw new Error("oops"); }
finally { console.log("I always run"); }
// the log is printed, AND THEN the error still propagates further (no catch = an unhandled exception)
```

## Nested try/catch — an error is caught only by the nearest `catch`

```js
try {
  try { throw new Error("oops"); }
  catch (e) { console.log("inner", e.message); } // caught here, propagation ends
  finally { console.log("finally"); }
} catch (e) {
  console.log("outer", e.message); // does NOT run — the error is already handled inside
}
```
For the error to reach the outer `catch`, the inner one must **re-throw** it (`throw e;`).

## Async — `try/catch` does not catch an error from a callback, but catches `await`

See `asynchrony.md`, the section on `setTimeout`/callbacks — it is one of the most common mistakes
when combining `try/catch` with asynchronous code.

## Catalogue of built-in error types (MDN Reference)

| Type | When |
|---|---|
| `Error` | the base class, a general error |
| `TypeError` | an operation on a value of the wrong type (`null.foo`, calling a non-function) |
| `RangeError` | a value outside the allowed range (e.g. `new Array(-1)`) |
| `ReferenceError` | a reference to a non-existent variable |
| `SyntaxError` | invalid syntax (often with `eval`/`JSON.parse`) |
| `URIError` | incorrect use of a URI function (`decodeURIComponent`) |
| `EvalError` | historical, practically unused today |
| `AggregateError` | many errors at once (e.g. from `Promise.any`, when all are rejected) |

**A practical rule when throwing your own errors:** throw `Error` instances (or subclasses), not
bare strings/objects — `throw "something"` means `e.message`/`e.stack` do not exist in `catch`, which
makes diagnosing harder later.
