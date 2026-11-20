---
name: lang-python
description: Use for Python 3.11–3.15 code — types and mypy, pyproject and uv, ruff, dataclass and Decimal, exceptions or result.
metadata:
  review: "2027-04-03"
  catalog: "Use when writing and reviewing Python code (3.11–3.15) — typing (3.12 generics syntax, X | None, Protocol, mypy/pyright), project structure (pyproject.toml, src layout, uv, lockfile, dependency groups), ruff, immutability (frozen dataclass), money in Decimal, error handling and rejections as a result, match, asyncio — and when expressing domain concepts with Python idioms. Not for pytest tests (tool-pytest), data analysis and statistics (data-analysis) or data pipelines (data-engineering)."
  keywords: "Python, pyproject, pyproject.toml, uv, ruff, mypy, pyright, typowanie w Pythonie, dataclass, Decimal, TypeVar, asyncio, venv, pip, requirements.txt, FastAPI, Django, .py, typing in Python"
---

# Python

**First check the project's version**: `requires-python` in `pyproject.toml` (the supported range) and `.python-version`
(the interpreter for work, uv/pyenv). Do not use syntax newer than the lower bound of `requires-python` — the
"Version-dependent" table.

## Language rules
1. **Types everywhere at module boundaries**, checked in CI (`mypy --strict` or pyright):
   - `X | None` instead of `Optional[X]`;
   - built-in generics (`list[int]`, `dict[str, Decimal]`);
   - from 3.12 the generics syntax without `TypeVar`: `class Result[T, E]: …`, `def first[T](xs: list[T]) -> T`,
     aliases `type Money = Decimal`;
   - `Protocol` instead of inheritance for ports, `@override` (3.12) when overriding;
   - `Any` only at the boundary with untyped code.
2. **Immutability by default:**
   - `@dataclass(frozen=True, slots=True)` for values, tuples and `frozenset` in fields;
   - modification through `dataclasses.replace`;
   - do not use mutable default values (`def f(xs=[])`, a `list` field without `field(default_factory=list)`).
3. **Money and quantities in `Decimal`** with a context or an explicit `quantize(Decimal('0.01'), ROUND_HALF_EVEN)`, never
   `float`. You create a `Decimal` from a `str` or `int`, not from a `float`.
4. **Errors:**
   - exceptions are for programming and infrastructure errors;
   - you return a **business rejection** (room taken, limit exceeded) as a result (a `Rejected` variant)
     or as your own domain exception with a name in the business language — never as a generic `ValueError` caught in the API;
   - do not catch a bare `except:` or `except Exception: pass`;
   - when re-raising, add context: `raise X from e`.
5. **Variants:** `match` on classes (`case Reserved(slot=s):`) and an exhaustive check with `assert_never` in the
   `case _` branch; enums through `enum.StrEnum` (3.11).
6. **Project structure:**
   - `pyproject.toml` with a `[project]` table (`requires-python`, `dependencies`) and `[build-system]`;
   - **src layout** (`src/<package>/`);
   - development dependencies in **`[dependency-groups]`** (PEP 735; `uv add --dev pytest`);
   - **uv** for the environment, the `uv.lock` lockfile in the repo, `uv sync --locked` in CI, `uv run` for commands;
   - export to the `pylock.toml` standard (PEP 751) through `uv export` when another tool requires it;
   - no installing packages globally and no `sudo pip`.
7. **Lint and format:** `ruff check` (with rules including `B`, `UP`, `SIM`, `S`) and `ruff format` instead of black/isort/flake8.
   The `UP` rule suggests syntax compatible with `requires-python`.
8. **Asynchrony:**
   - `asyncio.TaskGroup` (3.11) instead of loose `create_task`;
   - a timeout through `asyncio.timeout()`;
   - you do not call blocking functions in the event loop — `asyncio.to_thread` for synchronous calls.
9. **Security:**
   - SQL queries with parameters;
   - `subprocess` with a list of arguments, without `shell=True` with external data;
   - no `pickle` or `yaml.load` for external data (`yaml.safe_load`);
   - secrets from environment variables;
   - `secrets`, not `random`, for tokens.
10. **Text files:** always `encoding="utf-8"` in `open()` (the default from 3.15, but the code must work on the lower
    bound of `requires-python`).

Tested examples (Money, Result, a booking aggregate with a state machine and events, a repository port as a
`Protocol`, a 3.11 variant without the 3.12 generics syntax): `references/domain-building-blocks.md`.

## Domain concepts in Python
| Concept (glossary) | Python idiom |
|---|---|
| **value object** | `@dataclass(frozen=True, slots=True)` with validation in `__post_init__`; operations return a new object |
| **identifier / entity** | `NewType('RoomId', str)` or a frozen dataclass instead of a bare `str`; an entity = a class with identity and behaviour, equality by ID |
| **variants** | a union of frozen dataclasses (`type Outcome = Reserved \| Rejected`) and `match` with `assert_never` |
| **operation result** | `type Result[T] = Ok[T] \| Rejected` (variants as above) or success/rejection events returned from the method |
| **aggregate** | a class with private state (`_slots`), business methods instead of setters, `version` for optimistic locking, a list of events handed over by `pull_events()` |
| **state machine** | the state as a union of dataclasses or a `StrEnum`; transitions in `match` with `if` conditions in `case` |
| **event** | a frozen dataclass with a past-tense name (`RoomReserved`) and an `occurred_at: datetime` field (UTC zone) |
| **policy** | a `Protocol` with one method or a `Callable[[...], ...]` function injected into the aggregate or service |
| **specification** | a predicate function with a name from the business language; compositions through `all()`/`any()` |
| **repository / port** | a `Protocol` in the domain package operating on aggregates; the adapter (SQLAlchemy, psycopg) in infrastructure |
| **read model** | a separate frozen dataclass or `TypedDict` + an SQL query that bypasses the aggregate |
| **module** | a package with a public `__init__.py` (`__all__`); internal names with `_`; boundaries guarded by an import test (e.g. import-linter) |

## Version-dependent
| Version | Status (2026-10-03) | Changes relevant to this skill |
|---|---|---|
| 3.10 | end of support 2026-10 | `match`, `X \| Y` in types |
| 3.11 | security fixes only | `TaskGroup`, `asyncio.timeout`, `ExceptionGroup`/`except*`, `StrEnum`, `Self`, `tomllib`; a faster interpreter |
| 3.12 | security fixes only | **generics syntax** `def f[T]`, `class C[T]`, the `type` statement; `@override`; f-strings without quote restrictions; `distutils` removed; `datetime.utcnow()` deprecated — use `datetime.now(UTC)` |
| 3.13 | security fixes only | a new REPL; `warnings.deprecated`; type parameter defaults, `TypeIs`, `ReadOnly`; an experimental build without the GIL and a JIT; old modules removed (PEP 594: `cgi`, `crypt`, `telnetlib` and others) |
| 3.14 | bug fixes (currently 3.14.8) | **lazy annotations** (PEP 649/749, the `annotationlib` module) — references to types defined further down work without quotes; **t-strings** (`t"…"`, PEP 750) for safely composing SQL/HTML; `except A, B:` without parentheses; `compression.zstd`; `concurrent.interpreters`; the build without the GIL officially supported; `uuid.uuid7()` |
| 3.15 | release candidate; release planned for 2026-10-09 (PEP 790) | **UTF-8 by default** (PEP 686); `lazy import` (PEP 810); built-in `frozendict` and `sentinel`; unpacking in comprehensions; the `profiling` module (a sampling profiler) |

A project on a version newer than in the table → `detect_stack.py` reports `SKILL_OUTDATED`; update the skill per
core-stack-sync. You do not upgrade the interpreter or dependencies without a human's request.

## Checklist
- [ ] the version from `requires-python` checked; no syntax newer than the lower bound
- [ ] `ruff check`, `ruff format --check` and `mypy --strict` (or pyright) without errors
- [ ] no `float` for amounts, no mutable default values
- [ ] business rejections as a result or a domain exception, not `ValueError`
- [ ] `uv.lock` current; development dependencies in `[dependency-groups]`
- [ ] domain tests in pytest without a database and framework (tool-pytest)

## Sources
- docs.python.org/3/whatsnew/ (3.11–3.14) and docs.python.org/3.15/whatsnew/3.15.html — accessed 2026-10-03
- devguide.python.org/versions/ (branch status), PEP 745 (3.14), PEP 790 (3.15)
- packaging.python.org: Writing your pyproject.toml, Dependency groups (PEP 735), pylock.toml (PEP 751)
- PyPI (2026-10-03): uv 0.12.22, ruff 0.16.10, mypy 2.4.0
