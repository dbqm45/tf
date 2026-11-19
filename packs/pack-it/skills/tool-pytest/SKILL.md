---
name: tool-pytest
description: Use for tests in pytest 8–9 — fixtures, parametrize, tmp_path, monkeypatch, TOML configuration, asyncio, Hypothesis.
metadata:
  review: "2027-01-03"
  catalog: "Use for tests in pytest (8–9.1) — test structure and conftest.py, fixtures (scopes, yield, factories), parametrize with pytest.param and ids, tmp_path, monkeypatch, caplog, pytest.raises(match=), subtests, [tool.pytest] configuration and strict = true, the importlib import mode, asyncio tests (pytest-asyncio, asyncio_mode), property-based tests (Hypothesis), coverage (pytest-cov) and mutation tests (mutmut), migration 8→9. Not for a tool-independent test strategy (eng-testing), test case design (qa-test-design) or tests in JS/TS (tool-vitest, tool-jest)."
  keywords: "pytest, conftest, fixture, parametrize, tmp_path, monkeypatch, pytest.raises, pytest-asyncio, asyncio_mode, Hypothesis, pytest-cov, mutmut, test_*.py, tests/"
---

# pytest

**Check the version first** (`uv.lock`, `[dependency-groups]` in `pyproject.toml` or `pip show pytest`) and the configuration
section. TDD rules and choosing the kind of test: eng-testing; you write production code after a red test
(the `tdd_guard` hook).

## Configuration
- **pytest 9:** native TOML in `pyproject.toml` in the **`[tool.pytest]`** section (lists and numbers as TOML types) or
  in a `pytest.toml` file. The old `[tool.pytest.ini_options]` section (values as INI strings) still works;
  when moving to 9, move it to `[tool.pytest]` and turn the strings into lists (`addopts = ["-ra"]`).
- **`strict = true`** (9.0) enables `strict_config`, `strict_markers`, `strict_parametrization_ids` and `strict_xfail`:
  a typo in a marker or option is an error, and an `xfail` that passes fails the test. Strict mode adds
  new options in future versions, so enable it when the pytest version is locked (lockfile).
- A new project: `addopts = ["--import-mode=importlib"]`, `testpaths = ["tests"]`, the `src/` layout (pytest tests the
  installed package, not the working directory by accident).
- Installing as a development dependency: `uv add --dev pytest` (goes to `[dependency-groups]`), running with
  `uv run pytest`.

```toml
[tool.pytest]
minversion = "9.0"
strict = true
testpaths = ["tests"]
addopts = ["-ra", "--import-mode=importlib"]
markers = ["slow: slow tests, outside the fast suite"]
```

## Rules
1. **Names:** files `test_*.py`, functions `test_<behavior>_<condition>`; one expected change of behavior per test.
   A plain `assert` (pytest shows the differences), no `self.assertEqual`.
2. **Fixtures instead of setUp:**
   - you declare a dependency as a parameter;
   - you do cleanup after `yield`;
   - the scope is `function` by default, a wider one (`module`, `session`) only for costly, unmodified resources;
   - you keep shared fixtures in `conftest.py` at the lowest common directory level;
   - a factory (a fixture returning a function) is used to create many objects with variants.
3. **Built-in fixtures:**
   - `tmp_path` (instead of `tempfile`), `monkeypatch` (environment variables, attributes), `caplog`, `capsys`;
   - you create files only in `tmp_path`, never in the repo.
4. **Case tables:** `@pytest.mark.parametrize("amount, discount", [...])` instead of copies of a test; readable names
   through `pytest.param(..., id="threshold-200")` or `ids=`; the edges of equivalence classes from qa-test-design.
5. **Exceptions:** `with pytest.raises(RoomTaken, match="taken"):` — always a specific type, not `Exception`.
   Rejections returned as a result you check with a plain `assert result == Rejected(...)`.
6. **Test doubles:**
   - a **fake** first (e.g. an in-memory repository implementing a `Protocol`), then a stub;
   - `unittest.mock` only at the system boundary (HTTP, clock, queue);
   - with `mock.patch` you use `autospec=True`;
   - you do not mock types that you own.
7. **Time and randomness:** the clock is injected into the code (`Callable[[], datetime]`) instead of patching `datetime`; an explicit
   random seed.
8. **asyncio:** `pytest-asyncio` 1.x:
   - the default `asyncio_mode = "strict"` requires `@pytest.mark.asyncio`;
   - `asyncio_mode = "auto"` is recommended in asyncio-only projects;
   - set `asyncio_default_fixture_loop_scope = "function"` explicitly;
   - you do not put tests to sleep with `sleep` — you wait for an event with a limit (`asyncio.timeout`).
9. **Many assertions in one test:** subtests (built in since 9.0, the `subtests` fixture, `with subtests.test(i=i):`),
   when you want to see all the failures of a loop and parametrize does not fit.
10. **Property-based tests:** Hypothesis (`@given(st.decimals(...))`) for invariants (e.g. the sum of discounts ≤ the price);
    you preserve the examples found with `@example`.
11. **Suite quality:**
    - `pytest-cov` (`--cov=src --cov-branch`) shows uncovered branches, but does not say whether the tests check anything;
    - **mutmut** measures that, on a domain module (qa-spec-first-testing);
    - you fix unstable tests or move them to quarantine with a deadline (qa-regression);
    - you do not add `@pytest.mark.flaky`.

Examples (a factory fixture, parametrize with `pytest.param`, `tmp_path`, `monkeypatch`, a fake repository, an
asyncio test, Hypothesis, subtests) run on pytest 9.1.1: `references/examples.md`.

## Version-dependent
| Version | Changes relevant to this skill |
|---|---|
| 8.x | `tmp_path`, `pytest.param`, `--import-mode=importlib`; configuration only in `[tool.pytest.ini_options]` (INI strings); 8.4 (2025-06) ends support for Python 3.8 |
| 9.0 (2025-11) | **native TOML `[tool.pytest]`** and the `pytest.toml` file; **`strict = true`**; **built-in subtests**; `PytestRemovedIn9Warning` warnings become errors; end of support for Python 3.9 |
| 9.1 (2026-06) | support for Python 3.15; `pytest.register_fixture()`; `--max-warnings`; currently 9.1.1 |

Plugins (PyPI, 2026-10-03): pytest-asyncio 1.4.0, pytest-cov 7.1.0, hypothesis 6.168.3, mutmut 3.8.0 — all
require Python ≥3.10. You do not raise versions in the project without a human's request (core-stack-sync).

## Checklist
- [ ] the test written before the code and seen red (the failure message checks the right thing)
- [ ] configuration in `[tool.pytest]` or `[tool.pytest.ini_options]`, markers declared, `strict` when the version is locked
- [ ] no copies of tests differing in data — `parametrize` with readable `id`s
- [ ] no files outside `tmp_path`, no `sleep` in tests
- [ ] test doubles only at boundaries; a fake for domain ports

## Sources
- docs.pytest.org (documentation and changelog from the pytest 9.1.1 source package: doc/en/reference/customize.rst,
  doc/en/reference/reference.rst — `strict`, how-to/subtests.rst, explanation/goodpractices.rst) — accessed 2026-10-03
- pytest-asyncio 1.4.0: docs/reference/configuration.rst, docs/concepts.rst
- PyPI (2026-10-03): pytest 9.1.1 (2026-06-19), pytest-asyncio, pytest-cov, hypothesis, mutmut
