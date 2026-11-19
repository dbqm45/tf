# A rule with tests — template (Semgrep)

A rule without tests breaks silently: it stops catching the bug or starts catching everything. A test is a file with
vulnerable and correct code, marked with comments.
More examples (autofix with a `.fixed` test, reducing false hits, `--baseline-commit`):
`.claude/skills/tool-semgrep/references/rules-and-tests.md`.

## Rule (taint mode, Python)
```yaml
rules:
  - id: sql-sort-from-request
    languages: [python]
    severity: ERROR
    message: A sort field from the request reaches SQL — use an allowlist of fields (sort_clause)
    mode: taint
    pattern-sources:
      - pattern: request.GET.get(...)
      - pattern: request.args.get(...)
    pattern-sanitizers:
      - pattern: sort_clause(...)
    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: $CUR.execute($Q, ...)
              - pattern: $MODEL.objects.raw($Q, ...)
          - focus-metavariable: $Q
```

## Test (a file with the same name as the rule, e.g. `sql-sort-from-request.py`)
```python
def bad(request, cur):
    sort = request.GET.get("sort")
    # ruleid: sql-sort-from-request
    cur.execute("SELECT * FROM reports ORDER BY " + sort)

def good(request, cur):
    sort = sort_clause(request.GET.get("sort"), "asc")
    # ok: sql-sort-from-request
    cur.execute("SELECT * FROM reports ORDER BY " + sort)
```
Running: `semgrep --test <directory with rules and tests>`. A test from a real case (the place before
the fix) is the best vulnerable example.

## In CI
- Rules in the repository (e.g. `.semgrep/`), rule tests in CI together with the rest of the tests.
- A diff scan in the PR blocks new hits of this rule; the whole repository at night (sec-appsec-devsecops, steps 4 and 6).
- An exception only with a reason and an expiry date, not with a disabling comment that leaves no trace.
- CodeQL: the same in the form of a data flow query with a test (a test directory with code and the expected result).
