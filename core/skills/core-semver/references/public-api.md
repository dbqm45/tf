# Public API per product type and bump cases

Contents: 1. What is public API · 2. Library · 3. HTTP API · 4. CLI · 5. Application or service configuration and events ·
6. IaC module and container image · 7. Where to write it down

The rule for every row: **incompatible** = an existing, correct use stops working or silently changes behaviour with
no change on the user's side → major. New compatible capability → minor. Compatible correction → patch.

## 1. What is public API
| Product | Public (versioned) | Not public |
|---|---|---|
| Library | exported functions, classes, types, thrown exception classes, minimum runtime/language version | internal modules, file layout, private helpers |
| HTTP API | paths, methods, request and response fields, status codes, error body format, authentication | handler code, database schema behind it |
| CLI | commands, flags, exit codes, output that scripts parse (`--json`, CSV) | wording meant for humans, colours |
| Application / service | configuration keys and environment variables, published events, data others read | internal logs, UI layout (unless contracted) |
| IaC module / image | input variables, outputs, exposed ports, mounts, environment variables, entrypoint | internal resource names that nothing references |

## 2. Library
| Change | Bump |
|---|---|
| new exported function or type | minor |
| new optional trailing parameter with a safe default | minor |
| new required parameter, reordered parameters | major |
| accepts a wider input type (e.g. `string` → `string \| URL`) | minor |
| accepts a narrower input type | major |
| returns a narrower type | minor |
| returns a wider type (e.g. may now return `null`, a new union member, a new enum value) | major |
| throws a different exception class for the same situation | major — callers' `catch` blocks stop matching |
| raised minimum runtime (Node 18 → 20, Python 3.9 → 3.11) | major |
| `@deprecated` with the replacement documented | minor |
| internal refactor, faster implementation, same results | patch (or no release) |

## 3. HTTP API
| Change | Bump |
|---|---|
| new endpoint, new optional query parameter, new response field | minor |
| new required request field, stricter validation of existing input | major |
| removed, renamed or retyped field | major |
| changed status code or error body format | major |
| new value in a response enum | major, unless the contract says clients must tolerate unknown values (then minor) |
| changed rate limit with no contract change | patch, announced in advance |

The `/v1` → `/v2` path segment is a separate choice (be-api-design (pack-it)); a new path version normally accompanies a major.

## 4. CLI
| Change | Bump |
|---|---|
| new command or new flag | minor |
| removed or renamed flag, changed meaning of a flag, changed exit code | major |
| changed format of machine-read output | major |
| reworded human-oriented messages | patch |

## 5. Application or service configuration and events
| Change | Bump |
|---|---|
| new optional environment variable with a safe default | minor |
| renamed or newly required variable | major — or minor if the old name stays as a deprecated alias |
| data migration needing operator action | major |
| automatic, compatible migration | minor or patch |
| new optional field in a published event | minor |
| removed event field or changed meaning of a field | major |

## 6. IaC module and container image
| Change | Bump |
|---|---|
| new input variable with a default, new output | minor |
| change that destroys and recreates an existing resource on apply | major |
| removed input or output | major |
| image: new optional environment variable | minor |
| image: changed port, mount path or entrypoint | major |

Image tags: the full version tag (`1.4.2`) never changes once pushed. Convenience tags (`1`, `1.4`, `latest`) move only
forward, and only to versions compatible with what they pointed to.

## 7. Where to write it down
- In a project: a "Public API" section in README or a `PUBLIC_API.md` file next to it — one list, kept with the code.
- The factory itself: `.tf/factory/PUBLIC_API.md` (kept in the factory repository's core/factory directory).
- Anything not on the list may change in a patch; anything on it follows the tables above.
