# Semgrep rules with tests — verified examples

> **Contents:** 1. Taint: a value from the request → a shell command · 2. Autofix with a fix test · 3. Fewer false positives: metavariable and path constraints · In CI (verified in a git repository) · Pitfalls

All three rules and their tests pass `semgrep scan --test --metrics=off rules/` on Semgrep 1.50.0, 1.100.0
and 1.182.1 (2026-10-24): `3/3: ✓ All tests passed`, `1/1: ✓ All fix tests passed`. The directory layout:

```
rules/
  shell-injection-from-request.yaml   # the rule
  shell-injection-from-request.py     # the test: the same base name
  yaml-load-unsafe.yaml
  yaml-load-unsafe.py
  yaml-load-unsafe.fixed.py           # the expected code after autofix
  hardcoded-password.yaml
  hardcoded-password.py
```

## 1. Taint: a value from the request → a shell command
```yaml
rules:
  - id: shell-injection-from-request
    languages: [python]
    severity: ERROR
    message: >-
      A value from the request reaches a shell command (shell=True). Pass an argument list without shell=True
      or run the value through shlex.quote.
    metadata:
      cwe: "CWE-78: OS Command Injection"
      confidence: HIGH
    mode: taint
    pattern-sources:
      - pattern: flask.request.args.get(...)
      - pattern: flask.request.form[...]
    pattern-sanitizers:
      - pattern: shlex.quote(...)
    pattern-sinks:
      - patterns:
          - pattern: subprocess.run($CMD, ..., shell=True, ...)
          - focus-metavariable: $CMD
```
`focus-metavariable` narrows the sink to the first argument — a value from the request in another argument is not
a match. The full name `flask.request` also matches `from flask import request` (Semgrep resolves imports).

```python
import shlex
import subprocess
from flask import request


def bad():
    name = request.args.get("name")
    # ruleid: shell-injection-from-request
    subprocess.run("ls " + name, shell=True)


def bad_fstring():
    # ruleid: shell-injection-from-request
    subprocess.run(f"grep {request.form['q']} log.txt", shell=True)


def good_quoted():
    name = shlex.quote(request.args.get("name"))
    # ok: shell-injection-from-request
    subprocess.run("ls " + name, shell=True)


def good_list():
    # ok: shell-injection-from-request
    subprocess.run(["ls", request.args.get("name")])


def known_gap(cfg):
    name = cfg.lookup(request)  # a value from the request through a helper object
    # todoruleid: shell-injection-from-request
    subprocess.run("ls " + name, shell=True)
```
Checking that the test guards something: after removing `pattern-sanitizers` the test fails
(`missed lines: [], incorrect lines: [20]` — the `good_quoted` line).

## 2. Autofix with a fix test
```yaml
rules:
  - id: yaml-load-unsafe
    languages: [python]
    severity: WARNING
    message: yaml.load without a safe Loader can create an arbitrary Python object. Use yaml.safe_load.
    patterns:
      - pattern: yaml.load($DATA)
    fix: yaml.safe_load($DATA)
```
`yaml.load($DATA)` with one argument does not match `yaml.load(f, Loader=yaml.SafeLoader)` — an `ok:` case.

```python
import yaml


def read(path):
    with open(path) as f:
        # ruleid: yaml-load-unsafe
        return yaml.load(f)


def read_safe(path):
    with open(path) as f:
        # ok: yaml-load-unsafe
        return yaml.load(f, Loader=yaml.SafeLoader)
```
`yaml-load-unsafe.fixed.py` is the same file with `return yaml.safe_load(f)` in the `read` function; `--test` applies
the fix to a copy of the test and compares it with that file ("fix tests"). A preview on code: `semgrep scan --config rules/ --autofix
--dryrun`.

## 3. Fewer false positives: metavariable and path constraints
```yaml
rules:
  - id: hardcoded-password
    languages: [python]
    severity: ERROR
    message: A password written in code ($NAME). Read it from an environment variable or a secret store.
    paths:
      exclude:
        - "tests/"
        - "*_test.py"
        - "examples/"
    patterns:
      - pattern-either:
          - pattern: $NAME = "$VALUE"
          - pattern: $FUNC(..., $NAME="$VALUE", ...)
      - metavariable-regex:
          metavariable: $NAME
          regex: (?i)^.*(password|passwd|pwd|secret)$
      - metavariable-regex:
          metavariable: $VALUE
          regex: ^(?!(changeme|example|xxx+|\*+|<.*>)$).{8,}$
```
Every former false alarm is an `ok:` case — before you change the rule, the test shows it as `incorrect
lines`, after the change it passes:

```python
import os
import psycopg


# ruleid: hardcoded-password
DB_PASSWORD = "S3cr3t-Prod-2026"

# ruleid: hardcoded-password
conn = psycopg.connect(host="db", password="S3cr3t-Prod-2026")

# ok: hardcoded-password
EMPTY_PASSWORD = ""

# ok: hardcoded-password
DEFAULT_PASSWORD = "changeme"

# ok: hardcoded-password
TEMPLATE_PASSWORD = "<enter-password>"

# ok: hardcoded-password
PASSWORD_FIELD_LABEL = "User password"

# ok: hardcoded-password
db_password = os.environ["DB_PASSWORD"]
```
`paths.exclude` verified with a directory scan: the same secret in `tests/conftest.py` and in `app/settings.py` gives one
match (`app/settings.py`).

## In CI (verified in a git repository)
```bash
semgrep scan --test --metrics=off .semgrep/                     # rule tests — before the scan
semgrep scan --metrics=off --config .semgrep/ --error \
  --baseline-commit "origin/$GITHUB_BASE_REF" .                 # PR: only new matches, exit code 1 on a match
```
With `--baseline-commit main`, a branch with a new secret in `app/b.py` reported only `app/b.py`, and not the secret from `main`
in `app/a.py` (exit code 1 from `--error`). In GitHub Actions the base must be fetched (`actions/checkout`
with `fetch-depth: 0`). At night, a scan of the whole repository without `--baseline-commit`.

## Pitfalls
- `--validate` downloads lint rules from semgrep.dev (`p/semgrep-rule-lints`); without a network it ends with a download
  error. An invalid rule schema (e.g. the typo `patern:`) stops the scan and `--test` anyway
  (`Invalid rule schema`), so the rule test in CI is enough to detect a broken rule.
- `--metrics=off` in CI and locally if the company policy does not allow sending telemetry.
- A rule with `todoruleid:` passes the test while the gap is known — it is the rule's debt; `--test-ignore-todo` skips these
  annotations.
