# Public API and the kind of bump — detailed cases

The general rule: a change is **backward-incompatible** (MAJOR) if an existing, correct way of using it stops working
or starts working differently without a change on the user's side.

## Library (TypeScript, JavaScript, Java)
| Change | Bump | Notes |
|---|---|---|
| a new exported function or class | MINOR | |
| a new optional parameter at the end | MINOR | in Java an overload instead of changing the signature |
| a new required parameter or a changed order | MAJOR | |
| narrowing the input type (`string \| number` → `string`) | MAJOR | the user's code stops compiling |
| widening the result type (`string` → `string \| null`) | MAJOR | the user must handle a new case |
| widening the input type, narrowing the result type | MINOR | compatible |
| a new field in the result object | MINOR | unless the type is "exact" or checked by structural equality |
| a new variant in a union or enum returned to the user | MAJOR | a `switch` without `default` stops being exhaustive |
| a change of the thrown exception class | MAJOR | |
| raising the minimal version of Node, Java, a browser | MAJOR | |
| removing an export, even an undocumented one someone uses | MAJOR if it was in the public API; otherwise check whether it was importable | hence explicit `exports` in package.json |
| marking `@deprecated` | MINOR | with a description of the replacement |

## HTTP API
| Change | Bump |
|---|---|
| a new endpoint, a new optional query parameter, a new field in the response | MINOR |
| a new required request field, removing or renaming a field, a type change | MAJOR |
| a change of the status code or error format the client reacts to | MAJOR |
| stricter validation (e.g. a shorter length limit) | MAJOR |
| a new enum value in the response | MAJOR, unless the contract announces unknown values |
| a change of rate limits without a contract change | PATCH (with an announcement) |

## CLI
- A new command or flag → MINOR.
- Removing or changing a flag, a change of exit codes → MAJOR.
- A change of the output format read by scripts (JSON, columns) → MAJOR. A change of text for humans → PATCH.

## Application, service, configuration
- A new optional environment variable with a safe default → MINOR.
- Renaming a variable or a new required one → MAJOR. A transition period with the old name as an alias allows a
  MINOR with deprecation.
- A database migration that needs operator action → MAJOR. An automatic, backward-compatible migration → MINOR or
  PATCH.
- Events and messages: a new optional field → MINOR; removal or a change of meaning → MAJOR
  (pack-it: be-messaging-outbox, contract tests).

## IaC module and container image
- Module: a new variable with a default → MINOR; a change that destroys and recreates a resource → MAJOR.
- Image: a tag with the full version is immutable. Moving tags (`1`, `1.4`, `latest`) you move only forward, within
  compatibility.

## The factory (claude-team-factory)
The factory's public API is described in `.tf/factory/PUBLIC_API.md`. The release procedure and the CHANGELOG checks
are there too.
