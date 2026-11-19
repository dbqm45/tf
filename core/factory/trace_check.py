#!/usr/bin/env python3
"""
Trace criterion → test → commit → proof (step D of the run axis).

  tf trace <KEY> [--base <branch>] [--md | --json]

Criteria `AC-n` come from `docs/project/changes/<KEY>/spec.md`. A test is found by the identifier `AC-n` in the name or a
comment, only in test files changed on the branch relative to the base (committed and working) — identifiers
of other tasks do not mix in, and an `AC-n` in production code is not a test. The commit is the first commit of the branch that
introduced the identifier into the file. The proof is a task slice (`tf task verify`) whose files include the test file,
with the state computed now. "Red before code" tells whether the TDD hook saw this test as failing
(recorded in the slice's proof or in `.tf/logs/tdd-red.jsonl`); "no record" only means the hook did not see it —
e.g. the test was run outside a Claude Code session.

Rules:
  TRACE-001 a criterion without a test (error) · TRACE-002 a test points to an `AC-n` that is not in the specification (error) ·
  TRACE-003 a test does not belong to the files of any slice — no proof that it passed (warning).
With a trace error `tf task stage <KEY> review` (and later stages) is refused.

Base: `--base`, otherwise the first existing of `main`, `origin/main`, `master`, `origin/master`.
Test files: directories tests/, test/, __tests__/, e2e/, spec/ and names test_*.py, *_test.py, *_test.go, *.test.*,
*.spec.*, *Test.java, *Tests.cs.

Exit code: 0 — every criterion has a test (or the task has no specification); 1 — trace errors; 2 — no git
repository, unknown base or invocation error. Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")

CHANGES = Path("docs") / "project" / "changes"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
AC = re.compile(r"\bAC[-_ ]?(\d+)\b", re.I)
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                  r"(Test|Tests)\.(java|cs)$")
BASES = ("main", "origin/main", "master", "origin/master")


def sibling(name: str):
    """An engine script next to this file as a module (task_state, spec_check)."""
    spec = importlib.util.spec_from_file_location(f"tf_{name}", Path(__file__).resolve().with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return r.returncode, r.stdout


def find_base(root: Path, base: str | None) -> str | None:
    """Comparison base; None when the directory is not a git repository or there is no base."""
    if git(root, "rev-parse", "--is-inside-work-tree")[0] != 0:
        return None
    for ref in ([base] if base else BASES):
        if git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")[0] == 0:
            return ref
    return None


def changed_tests(root: Path, base: str) -> list[str]:
    """Test files changed on the branch relative to the base: committed, changed in the working tree and new untracked."""
    files: set[str] = set()
    for args in (("diff", "--name-only", f"{base}...HEAD"), ("diff", "--name-only", "HEAD"),
                 ("ls-files", "--others", "--exclude-standard")):
        files.update(ln.strip() for ln in git(root, *args)[1].splitlines() if ln.strip())
    return sorted(f for f in files if TEST.search(f) and (root / f).is_file())


def first_commit(root: Path, base: str, rel: str, ident: str) -> str | None:
    """The first commit of the branch that introduced the identifier into the file; None when the change is not committed."""
    out = git(root, "log", "--reverse", "--format=%h", f"-S{ident}", f"{base}..HEAD", "--", rel)[1].split()
    return out[0] if out else None


def trace(root: Path, key: str, base: str | None = None) -> dict | None:
    """Task trace. None when it cannot be computed (no git repository or base). `spec: False` when the task
    has no specification."""
    spec = sibling("spec_check").check_task(root, key)
    if spec is None:
        return {"ok": True, "spec": False, "rows": [], "errors": [], "warnings": [], "base": None}
    ref = find_base(root, base)
    if ref is None:
        return None
    ts = sibling("task_state")
    task = ts.load(root, key) or {}
    states = ts.slice_states(root, task)
    owner: dict[str, str] = {}           # file → slice whose proof covers it (the last wins)
    for sid, sl in (task.get("slices") or {}).items():
        for rel in ((ts.evidence_of(root, key, sl) or {}).get("files") or {}):
            owner[rel] = sid
    red: set[str] = set(ts.red_tests(root, changed := changed_tests(root, ref)))
    for sl in (task.get("slices") or {}).values():
        red.update((ts.evidence_of(root, key, sl) or {}).get("red_tests") or {})
    found: dict[str, list[tuple[str, int]]] = {}
    for rel in changed:
        try:
            lines = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for m in AC.finditer(line):
                hits = found.setdefault(f"AC-{int(m.group(1))}", [])
                if not any(f == rel for f, _ in hits):       # one entry per file: the first occurrence
                    hits.append((rel, n))
    errors, warnings, rows = [], [], []
    for ac in spec["criteria"]:
        hits = found.get(ac, [])
        if not hits:
            errors.append({"rule": "TRACE-001", "criterion": ac,
                           "message": f"{ac} has no test — add a test with \"{ac}\" in its name or a comment"})
            rows.append({"criterion": ac, "tests": [], "commit": None, "slice": None, "evidence": "no-test", "red": False})
            continue
        rel = hits[0][0]
        sid = next((owner[f] for f, _ in hits if f in owner), None)
        evidence = states[sid][0] if sid in states else "no-evidence"
        if sid is None:
            warnings.append({"rule": "TRACE-003", "criterion": ac,
                             "message": f"{ac}: {rel} is not in the files of any slice — add it to `--files` when you "
                                        "verify the slice"})
        rows.append({"criterion": ac, "tests": [f"{f}:{n}" for f, n in hits],
                     "commit": first_commit(root, ref, rel, ac), "slice": sid, "evidence": evidence,
                     "red": any(f in red for f, _ in hits)})
    for ac in sorted(set(found) - set(spec["criteria"]), key=lambda a: int(a[3:])):
        rel, n = found[ac][0]
        errors.append({"rule": "TRACE-002", "criterion": ac,
                       "message": f"{rel}:{n} points to {ac}, which is not in the specification — fix the ID or "
                                  "add the criterion (a change of requirements)"})
    return {"ok": not errors, "spec": True, "rows": rows, "errors": errors, "warnings": warnings, "base": ref}


def render_md(rows: list[dict]) -> str:
    out = ["| Criterion | Test | Red before the code | Commit | Evidence |", "|---|---|---|---|---|"]
    for r in rows:
        tests = ", ".join(f"`{t}`" for t in r["tests"]) or "—"
        proof = f"{r['slice']}: {r['evidence']}" if r["slice"] else r["evidence"]
        out.append(f"| {r['criterion']} | {tests} | {'yes' if r.get('red') else 'not recorded'} | {r['commit'] or '—'} | {proof} |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf trace", description="Trace criterion → test → commit → evidence.")
    ap.add_argument("key")
    ap.add_argument("--base", default=None)
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        print(f"✗ the key \"{a.key}\" does not match the pattern (e.g. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    result = trace(root, a.key, a.base)
    if result is None:
        print("✗ cannot compute the trace: the directory is not a git repository or there is no comparison base "
              f"({a.base or ', '.join(BASES)}) — give --base <branch>")
        return 2
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result["ok"] else 1
    if not result["spec"]:
        print(f"Task {a.key} has no {CHANGES / a.key / 'spec.md'} — there is nothing to compute the criteria trace from.")
        return 0
    rows = result["rows"]
    if a.md:
        print(render_md(rows))
    else:
        covered = sum(1 for r in rows if r["tests"])
        print(f"{'✓' if result['ok'] else '✗'} {a.key}: criteria with a test {covered}/{len(rows)} (base: {result['base']})")
        for r in rows:
            proof = f"{r['slice']}: {r['evidence']}" if r["slice"] else r["evidence"]
            print(f"  {r['criterion']} → {', '.join(r['tests']) or '—'} → red before the code: "
                  f"{'yes' if r.get('red') else 'not recorded'} → {r['commit'] or 'not committed'} → {proof}")
    for e in result["errors"]:
        print(f"✗ {e['rule']}  {e['message']}", file=sys.stderr if a.md else sys.stdout)
    for w in result["warnings"]:
        print(f"⚠ {w['rule']}  {w['message']}", file=sys.stderr if a.md else sys.stdout)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
