# Reguły Semgrep z testami — przykłady sprawdzone

Wszystkie trzy reguły i ich testy przechodzą `semgrep scan --test --metrics=off rules/` na Semgrepie 1.50.0, 1.100.0
i 1.182.1 (2026-10-24): `3/3: ✓ All tests passed`, `1/1: ✓ All fix tests passed`. Układ katalogu:

```
rules/
  shell-injection-from-request.yaml   # reguła
  shell-injection-from-request.py     # test: ta sama nazwa bazowa
  yaml-load-unsafe.yaml
  yaml-load-unsafe.py
  yaml-load-unsafe.fixed.py           # oczekiwany kod po autofix
  hardcoded-password.yaml
  hardcoded-password.py
```

## 1. Taint: wartość z żądania → polecenie powłoki
```yaml
rules:
  - id: shell-injection-from-request
    languages: [python]
    severity: ERROR
    message: >-
      Wartość z żądania trafia do polecenia powłoki (shell=True). Przekaż listę argumentów bez shell=True
      albo przepuść wartość przez shlex.quote.
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
`focus-metavariable` zawęża ujście do pierwszego argumentu — wartość z żądania w innym argumencie nie jest
trafieniem. Pełna nazwa `flask.request` dopasowuje też `from flask import request` (Semgrep rozwiązuje importy).

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
    name = cfg.lookup(request)  # wartość z żądania przez obiekt pomocniczy
    # todoruleid: shell-injection-from-request
    subprocess.run("ls " + name, shell=True)
```
Sprawdzenie, że test coś pilnuje: po usunięciu `pattern-sanitizers` test oblewa
(`missed lines: [], incorrect lines: [20]` — linia `good_quoted`).

## 2. Autofix z testem poprawki
```yaml
rules:
  - id: yaml-load-unsafe
    languages: [python]
    severity: WARNING
    message: yaml.load bez bezpiecznego Loadera może utworzyć dowolny obiekt Pythona. Użyj yaml.safe_load.
    patterns:
      - pattern: yaml.load($DATA)
    fix: yaml.safe_load($DATA)
```
`yaml.load($DATA)` z jednym argumentem nie dopasowuje `yaml.load(f, Loader=yaml.SafeLoader)` — przypadek `ok:`.

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
`yaml-load-unsafe.fixed.py` to ten sam plik z `return yaml.safe_load(f)` w funkcji `read`; `--test` stosuje
poprawkę do kopii testu i porównuje z nim („fix tests”). Podgląd na kodzie: `semgrep scan --config rules/ --autofix
--dryrun`.

## 3. Mniej fałszywych trafień: ograniczenia metazmiennych i ścieżek
```yaml
rules:
  - id: hardcoded-password
    languages: [python]
    severity: ERROR
    message: Hasło zapisane w kodzie ($NAME). Czytaj je ze zmiennej środowiskowej albo magazynu sekretów.
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
Każdy dawny fałszywy alarm jest przypadkiem `ok:` — zanim zmienisz regułę, test pokazuje go jako `incorrect
lines`, po zmianie przechodzi:

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
TEMPLATE_PASSWORD = "<wpisz-hasło>"

# ok: hardcoded-password
PASSWORD_FIELD_LABEL = "Hasło użytkownika"

# ok: hardcoded-password
db_password = os.environ["DB_PASSWORD"]
```
`paths.exclude` sprawdzone skanem katalogu: ten sam sekret w `tests/conftest.py` i w `app/settings.py` daje jedno
trafienie (`app/settings.py`).

## W CI (sprawdzone w repozytorium git)
```bash
semgrep scan --test --metrics=off .semgrep/                     # testy reguł — przed skanem
semgrep scan --metrics=off --config .semgrep/ --error \
  --baseline-commit "origin/$GITHUB_BASE_REF" .                 # PR: tylko nowe trafienia, kod 1 przy trafieniu
```
Z `--baseline-commit main` gałąź z nowym sekretem w `app/b.py` zgłosiła tylko `app/b.py`, a sekretu z `main`
w `app/a.py` nie (kod wyjścia 1 z `--error`). W GitHub Actions baza musi być pobrana (`actions/checkout`
z `fetch-depth: 0`). Nocą skan całego repozytorium bez `--baseline-commit`.

## Pułapki
- `--validate` pobiera reguły lintujące z semgrep.dev (`p/semgrep-rule-lints`); bez sieci kończy się błędem
  pobierania. Błędny schemat reguły (np. literówka `patern:`) i tak zatrzymuje skan i `--test`
  (`Invalid rule schema`), więc test reguł w CI wystarcza do wykrycia zepsutej reguły.
- `--metrics=off` w CI i lokalnie, jeśli polityka firmy nie pozwala wysyłać telemetrii.
- Reguła z `todoruleid:` przechodzi test, dopóki luka jest znana — to dług reguły; `--test-ignore-todo` pomija te
  adnotacje.
