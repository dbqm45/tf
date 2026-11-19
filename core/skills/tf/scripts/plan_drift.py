#!/usr/bin/env python3
"""
Conformance of changes to the run plan: files changed on the story branch vs the slice files in plan.md.

  python3 .claude/skills/tf/scripts/plan_drift.py <run directory> [--base main] [--json]

A slice in plan.md: `- [x] S<n> — <value> · … · files: <comma-separated paths> · …` (a path may be a directory
or a glob pattern). The plan lives in the run directory or — when `run.json` has `task_dir` — in the task directory
`docs/project/changes/<KEY>/`. Result: per slice the touched and untouched files, changes outside the plan (without the factory's
work output in `.tf/` and task files in `docs/project/changes/`), the plan's coverage of the diff in % and the number of
changed test files. The script only reports (code 0); 2 — bad call.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys

SLICE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(S\d+)\b(.*)$")
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                  r"(Test|Tests)\.(java|cs)$")


def parse_plan(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        files = []
        for part in m.group(3).split("·"):
            k, _, v = part.strip().partition(":")
            if k.strip().lower() == "files":
                files = [f.strip().strip("`") for f in v.split(",") if f.strip()]
        out.append({"id": m.group(2), "done": m.group(1).lower() == "x", "files": files})
    return out


def matches(path: str, spec: str) -> bool:
    if spec.endswith("/"):
        return path.startswith(spec)
    return path == spec or fnmatch.fnmatch(path, spec) or path.startswith(spec.rstrip("/") + "/")


RUN_PREFIXES = (".tf/", "docs/project/changes/")   # the factory's work output and task files (written by `tf task`)


def plan_file(run_dir: str) -> str:
    """The run's plan.md: in the task directory pointed to by `task_dir` in run.json (from the project directory, three
    levels above .tf/runs/<KEY>/), and in the old layout in the run directory itself."""
    try:
        with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as fh:
            rel = json.load(fh).get("task_dir")
    except (OSError, ValueError, AttributeError):
        rel = None
    if rel:
        return os.path.normpath(os.path.join(os.path.abspath(run_dir), "..", "..", "..", rel, "plan.md"))
    return os.path.join(run_dir, "plan.md")


def changed_files(base: str) -> list[str]:
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(["git", "diff", "--name-only", base], capture_output=True, text=True)
    return sorted(f for f in r.stdout.splitlines() if f and not f.startswith(RUN_PREFIXES))


def drift(plan: list[dict], changed: list[str]) -> dict:
    slices, covered = [], set()
    for s in plan:
        touched = sorted(f for f in changed if any(matches(f, spec) for spec in s["files"]))
        missing = [spec for spec in s["files"] if not any(matches(f, spec) for f in changed)]
        covered |= set(touched)
        slices.append({**s, "touched": touched, "missing": missing})
    unplanned = [f for f in changed if f not in covered]
    return {"slices": slices, "changed": changed, "unplanned": unplanned,
            "coverage": round(100 * len(covered) / len(changed)) if changed else 100,
            "tests_changed": sum(1 for f in changed if TEST.search(f))}


def render(r: dict) -> str:
    done = sum(s["done"] for s in r["slices"])
    L = [f"Agreement with the plan: slices {done}/{len(r['slices'])}, the plan's coverage of the diff {r['coverage']}%, "
         f"changed files {len(r['changed'])}, of which tests {r['tests_changed']}"]
    for s in r["slices"]:
        L.append(f"  - {s['id']} [{'x' if s['done'] else ' '}]: touched {len(s['touched'])}"
                 + (f"; untouched from the plan: {', '.join(s['missing'])}" if s["missing"] else ""))
    if r["unplanned"]:
        L.append("Changes outside the plan (check the scope or add them to the plan): " + ", ".join(r["unplanned"]))
    return "\n".join(L)


def main(argv: list[str]) -> int:
    base, as_json, args = "main", False, []
    it = iter(argv)
    for a in it:
        if a == "--base":
            base = next(it, "main")
        elif a == "--json":
            as_json = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            args.append(a)
    plan_md = plan_file(args[0]) if args else ""
    if len(args) != 1 or not os.path.isfile(plan_md):
        print(f"✗ give the run directory with plan.md (got: {args})", file=sys.stderr)
        return 2
    with open(plan_md, encoding="utf-8") as fh:
        r = drift(parse_plan(fh.read()), changed_files(base))
    print(json.dumps(r, ensure_ascii=False, indent=2) if as_json else render(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
