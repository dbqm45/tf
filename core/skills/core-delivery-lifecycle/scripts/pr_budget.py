#!/usr/bin/env python3
"""
Artifact budget in a PR: whether plans, reports and run evidence drown out the code change in review.

  python3 .claude/skills/core-delivery-lifecycle/scripts/pr_budget.py --base main [--json]

Counts the lines the branch adds relative to the merge base with --base (commits, without uncommitted changes) and splits them into
code and artifacts. Artifacts: docs/project/**, docs/test/**, docs/work/**, .tf/**, **/evidence/** and patterns
from `.claude/pr-budget.json` ({"artifacts": [...], "max_share": 0.5, "max_artifact": 600, "max_plan": 300}).
Exceeded when:
- artifacts > max_share (default 50%) of the added lines, when the PR also changes code (a docs-only PR is exempt);
- a single artifact > max_artifact lines (default 600), a plan (`plan.md`, `*-plan.md`) > max_plan (300).
First line: `Werdykt: OK | OVER` (verdict); exit code 1 when exceeded. What to do: keep in the PR what
the review needs (plan, slicing report), move the rest (raw logs, evidence, screenshots) outside the repository or
shorten it; for a justified exception describe it in the PR. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ARTIFACTS = ["docs/project/**", "docs/test/**", "docs/work/**", ".tf/**", "**/evidence/**"]
PLAN = re.compile(r"(^|/)([\w.-]*-)?plan\.md$")


def glob_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(f"^{out}$")


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, errors="replace", timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} ended with exit code {r.returncode}")
    return r.stdout


def budget(root: Path, base: str) -> dict:
    cfg_path = root / ".claude" / "pr-budget.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    patterns = [glob_re(p) for p in DEFAULT_ARTIFACTS + list(cfg.get("artifacts") or [])]
    max_share = float(cfg.get("max_share", 0.5))
    max_artifact = int(cfg.get("max_artifact", 600))
    max_plan = int(cfg.get("max_plan", 300))
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    code = art = 0
    artifacts, problems, sizes = [], [], {}
    for line in git(root, "diff", "--numstat", f"{merge_base}..HEAD").splitlines():
        added, _deleted, path = line.split("\t", 2)
        if added == "-":          # binary file
            continue
        n = int(added)
        if any(p.match(path) for p in patterns):
            art += n
            artifacts.append(path)
            sizes[path] = n
            size = len(git(root, "show", f"HEAD:{path}").splitlines()) if n else 0
            limit = max_plan if PLAN.search(path) else max_artifact
            if size > limit:
                kind = "plan" if limit == max_plan else "artifact"
                problems.append(f"{path}: {size} lines — {kind} over the limit of {limit}")
        else:
            code += n
    total = code + art
    share = art / total if total else 0.0
    if code and share > max_share:
        top = ", ".join(f"{p} (+{n})" for p, n in sorted(sizes.items(), key=lambda kv: -kv[1])[:3])
        problems.append(f"artifacts are {share:.0%} of the added lines ({art} of {total}) — the limit is {max_share:.0%}; "
                        f"largest: {top}")
    return {"verdict": "OVER" if problems else "OK", "base": base, "code_lines": code,
            "artifact_lines": art, "share": round(share, 3), "artifacts": artifacts, "problems": problems}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="main")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = budget(Path.cwd(), a.base)
    except (RuntimeError, OSError, ValueError) as e:
        print(f"✗ {e}")
        return 2
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"Verdict: {res['verdict']} — code: {res['code_lines']} lines, artifacts: {res['artifact_lines']} lines "
              f"({res['share']:.0%}), base: {a.base}")
        for p in res["problems"]:
            print(f"✗ {p}")
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
