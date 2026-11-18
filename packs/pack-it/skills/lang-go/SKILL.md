---
name: lang-go
description: Use for Go 1.22–1.27 code — conventions, errors (errors.Is/As), concurrency, value object, aggregate.
metadata:
  review: "2027-01-23"
  catalog: "Use when writing and reviewing Go code (1.22–1.27) — language conventions, error handling (sentinel errors, error types, %w wrapping, errors.Is and errors.As), interfaces on the consumer side, concurrency with context and limits, table-driven tests, differences between versions (iterators, WaitGroup.Go, new with an expression, generic methods) and expressing domain concepts with Go idioms (value object, variants, aggregate, operation result, events, repository port). Not for HTTP API design (be-api-design), containerisation (ops-docker) or domain modelling (ddd-*)."
  keywords: "Go, golang, go.mod, błędy w Go, errors.Is, errors.As, wrap %w, sentinel error, wynik operacji w Go, interfejs w Go, gorutyny, context, WaitGroup, kanały, iteratory, range po funkcji, metody generyczne, testy tabelaryczne, kwota w Go, float64, int64 w groszach, goły string w Go, typ nazwany, identyfikator klienta w Go, obiekt wartości w Go, agregat w Go, Go 1.27, errors in Go, operation result in Go, interface in Go, goroutines, channels, iterators, range over function, generic methods, table-driven tests, amount in Go, int64 in minor units, bare string in Go, named type, customer identifier in Go, value object in Go, aggregate in Go"
---

# Go

## Language rules
1. The module's language version is the `go` directive in `go.mod` — you use a new feature only after raising that
   directive (`go mod edit -go=1.27`); `toolchain` only says what to build with. The same versions in CI and locally.
2. Errors are values: you return `error` as the last result. Business rejections — sentinel errors
   (`var ErrSlotTaken = errors.New(...)`) or error types with details; you wrap with `fmt.Errorf("...: %w", err)`,
   check with `errors.Is` / `errors.As`, never by comparing text. `panic` only for programmer errors.
3. Interfaces small and defined where they are **used** (a port in the domain package), not next to the implementation;
   functions accept interfaces and return concrete types.
4. Money: `int64` in minor units (grosze) with the currency in the type, or a decimal library — never
   `float64`.
5. Named types instead of bare `string`/`int` for identifiers and units; a `NewX(...) (X, error)` constructor
   guards validity, fields unexported.
6. Concurrency: every goroutine has an owner and a way to finish (`context.Context` as the first parameter,
   a timeout); `errgroup` or `sync.WaitGroup` instead of "fire and forget"; shared data behind a mutex
   or passed through a channel. Tests with `-race` in CI.
7. Packages by responsibility (domain, adapter), not by technical layer; `internal/` for what must not
   be imported from outside the module. No import cycles (the compiler forbids them).
8. Code is formatted by `gofmt` and checked by `go vet`; table-driven tests with `t.Run`.

## Domain concepts in Go
| Concept (vocabulary) | Go idiom |
|---|---|
| **value object** | a struct with unexported fields, a constructor with validation, value-receiver methods returning a new value; comparable with `==` |
| **entity** | a struct with an identifier of a named type (`type CustomerID string`) and behaviour; equality by identifier |
| **aggregate** | a pointer to a struct with private state, business methods instead of setters, `version` for optimistic locking, `PullEvents()` |
| **variants** | an interface with an unexported method (a set closed within the package) + `switch v := x.(type)`; `default` with `panic` for an unhandled variant |
| **operation result** | `(T, error)`; rejections as sentinel errors or error types with `Unwrap`, told apart with `errors.Is` / `errors.As` |
| **event** | a struct in the past tense (`ResourceBlocked`) implementing the module's event interface |
| **policy** | an interface with one method or a function type (`type DiscountPolicy func(Order) Money`) injected through the constructor |
| **repository** | an interface (port) in the domain package operating on aggregates; the SQL adapter in the infrastructure package |
| **read model** | a separate struct and SQL query bypassing the aggregate |
| **state machine** | the state as variants (`Free`, `Blocked`, `Disabled`), transitions in a type `switch` in an aggregate method |
| **module** | a package with a small exported API, the rest unexported; `internal/` for boundaries |

Tested implementations (amount, identifier, rejection errors, state variants, aggregate with events, repository
port, table-driven tests): `references/domain-building-blocks.md`.

## Version-dependent
Every threshold checked with a compiler (2026-10-23): the code does not compile in the earlier version, and compiles in the given one.
| Version | Changes relevant to this skill |
|---|---|
| 1.22 | the `for` loop variable is new in each iteration; `for i := range n`; patterns in `http.ServeMux` (method, `{id}`, `r.PathValue`) |
| 1.23 | iterators: `range` over a function, the `iter` package (`iter.Seq`, `iter.Seq2`) |
| 1.24 | `os.Root` (file access limited to a directory), `testing.B.Loop` in benchmarks |
| 1.25 | `sync.WaitGroup.Go`; the `testing/synctest` package (tests of code with time and goroutines) |
| 1.26 | `new` with an expression: `p := new(42)` |
| 1.27 | generic methods — a method can have its own type parameters: `func (b Box[T]) Map[U any](f func(T) U) Box[U]` |
A project with a directive older than 1.22 → `detect_stack.py` reports `PROJECT_OLDER`: use only what works in that
version. Newer than 1.27 → `SKILL_OUTDATED`, update per core-stack-sync.

## Example
Question: "Reserve should return success or a rejection (slot taken, resource disabled)". Result:
`func (r *ResourceAvailability) Block(by string, at time.Time) error` — `nil` is success; `ErrDisabled`
(a sentinel error); `*ConflictError{BlockedBy: "jan"}` with `Unwrap() error { return ErrSlotTaken }`. The caller:
`errors.Is(err, ErrSlotTaken)` → 409, `errors.As(err, &ce)` → a message with `ce.BlockedBy`, another error → 500.
The full code with a test: `references/domain-building-blocks.md`.

## Checklist
- [ ] `gofmt -l` empty, `go vet ./...` with no findings, `go test -race ./...` in CI
- [ ] no `float64` for amounts, identifiers as named types
- [ ] rejections as errors told apart with `errors.Is`/`errors.As`, no comparing of error text
- [ ] every goroutine with a `context` and a way to finish
- [ ] the `go` directive in `go.mod` allows the language features used

## Sources
- The language specification and release notes: go.dev/ref/spec, go.dev/doc/go1.22 … go1.27 (go.dev unreachable from the session
  2026-10-23; versions and thresholds checked with the compilers go1.21.0–go1.27.3 from proxy.golang.org).
- "Effective Go", "Go Code Review Comments" (go.dev/wiki), the `errors` package (`Is`, `As`, `%w`).
Described in our own words.
