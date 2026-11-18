# Bisection and tools — examples

Checked 2026-10-03 on git 2.43 and CPython 3.11: a repository with 20 commits, the bug introduced in c13, and c12 cannot
be imported (a syntax error).

## 1. `git bisect run`
The checking script returns an exit code that git understands:

| Code | Meaning |
|---|---|
| 0 | the commit is good |
| 1–127 (except 125) | the commit is bad |
| 125 | cannot be checked — skip (`skip`) |
| other (e.g. > 127) | abort the bisection |

```sh
#!/bin/sh
# check.sh — run by git bisect run in the repository directory
export PYTHONDONTWRITEBYTECODE=1                 # no bytecode cache between steps (see point 2)
python3 -c "import calc" 2>/dev/null || exit 125 # does not build → skip this commit
python3 -c "import calc, sys; sys.exit(0 if calc.add(2, 2) == 4 else 1)"
```

```sh
git bisect start <bad> <good>      # e.g. git bisect start HEAD v1.4.0
git bisect run ./check.sh
git bisect log > bisect.log         # record of the run for the report
git bisect reset                    # back to the branch
```

The result of the example: git checked c15, c12 (skipped, code 125), c13 and c11, and then gave two candidates: c12 and c13
("The first bad commit could be any of"). A skipped commit adjacent to the first bad one stays in the result — that is an honest
answer, not an error. You decide manually by reading the diff of both commits.

Tips:
- the script in a file outside the repository (e.g. in `/tmp`) or untracked — otherwise it will disappear when commits are switched;
- the test from the bisection becomes a regression test in the fix;
- a history with merges: `git bisect start --first-parent` checks only mainline commits;
- in a monorepo narrow down with a path: `git bisect start <bad> <good> -- packages/billing`.

## 2. The trap: stale artifacts
The first attempt without `PYTHONDONTWRITEBYTECODE` pointed to **the wrong commit**. The files with `return a + b` and `return a - b`
have the same size, and git set their modification time in the same second, so Python used the old bytecode
from `__pycache__`. The same threatens with any cache (an incremental build, `node_modules/.cache`, `dist/`). In the bisection
script: a clean build or a disabled cache, and between runs `git clean -fdx` (careful: it removes untracked files).

## 3. The debugger
Python:
```python
def total(lines):
    breakpoint()          # stop; PYTHONBREAKPOINT=0 disables all of them
    return sum(l.price * l.qty for l in lines)
```
`pdb` commands: `n` (next line), `s` (step into a function), `c` (continue), `p expression`, `pp`, `w` (stack),
`u`/`d` (frame up/down), `b file:line` (breakpoint), `q`. Running the whole program under the debugger:
`python -m pdb script.py`; in pytest: `pytest --pdb` (the debugger on failure).

Node.js: `node --inspect-brk app.js` and Chrome DevTools (`chrome://inspect`) or the IDE debugger; in code the
`debugger;` statement. Vitest/Jest: run a single test with `--inspect-brk` and one thread.

## 4. Narrowing down data (delta debugging)
1. Take the input that triggers the bug (a file, a request, a set of records).
2. Remove half. The bug is still there → work on that half. It disappeared → go back and remove the other half.
3. When no half alone triggers the bug, split into smaller pieces.
4. The end: the smallest input with the bug — it goes into a regression test (without personal data; arch-privacy-compliance).
