#!/usr/bin/env python3
"""Tests of the AI PR review in CI (core-git-workflow, scripts/ai_review.py, templates/ai-review.yml): installing the
workflow, the YAML security properties, the verdict step (status and summary comment) with a `gh` stub, the bypass
by label, REVIEW.md from the reconstruction draft. python3 .claude/tests/test_ai_review.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-git-workflow" / "scripts" / "ai_review.py"
try:
    import yaml
except ImportError:   # the bundled PyYAML copy (.tf/factory/_vendor)
    sys.path.insert(0, str(ROOT / ".tf" / "factory" / "_vendor"))
    import yaml

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(sys.argv[1:]) + "\n")
if "--method" not in sys.argv and any("/comments" in a for a in sys.argv):
    print(os.environ.get("FAKE_COMMENTS", "[]"))
'''


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def new_repo(tmp: str) -> Path:
    repo = Path(tmp) / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def step_script(wf: dict, job: str, name: str) -> tuple[str, dict]:
    step = next(s for s in wf["jobs"][job]["steps"] if s.get("name") == name)
    return step["run"], step.get("env", {})


def run_step(script: str, tmp: Path, env: dict, comments: str = "[]") -> list:
    bindir = tmp / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    gh.write_text(FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    log = tmp / "gh.log"
    log.write_text("", encoding="utf-8")
    full = {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}", "GH_LOG": str(log), "FAKE_COMMENTS": comments,
            "GITHUB_REPOSITORY": "acme/shop", **env}
    r = subprocess.run(["bash", "-e", "-c", script], capture_output=True, text=True, env=full, timeout=60)
    calls = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [r, calls]


def status_of(calls: list) -> dict:
    for c in calls:
        if any("/statuses/" in a for a in c):
            return {k: v for a in c if "=" in a for k, v in [a.split("=", 1)]}
    return {}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        r = run(["install"], repo)
        path = repo / ".github" / "workflows" / "ai-review.yml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        check(r.returncode == 0 and text and "REVIEW.md" in r.stdout and "review-md" in r.stdout,
              f"AR-1: install writes the workflow and says how to create a missing REVIEW.md: {r.stdout}{r.stderr}")
        wf = yaml.safe_load(text) if text else {}
        on = wf.get(True) or wf.get("on") or {}
        jobs = wf.get("jobs", {})
        check(wf.get("permissions") == {} and set(jobs) == {"review", "override"},
              f"AR-2: permissions: {{}} at the top, the review and override jobs: {wf.get('permissions')} {list(jobs)}")
        rv = jobs.get("review", {})
        check(rv.get("permissions") == {"contents": "read", "pull-requests": "write", "statuses": "write"}
              and jobs.get("override", {}).get("permissions") == {"statuses": "write"},
              f"AR-3: minimal permissions of the jobs: {rv.get('permissions')} {jobs.get('override', {}).get('permissions')}")
        check("head.repo.full_name == github.repository" in rv.get("if", "")
              and "head.repo.full_name == github.repository" in jobs.get("override", {}).get("if", "")
              and "'ai-review'" in rv.get("if", ""),
              f"AR-4: the fork block and the ai-review label condition: {rv.get('if')}")
        uses = re.findall(r"^\s*(?:-\s*)?uses:\s*(\S+)", text, re.M)
        check(uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses),
              f"AR-5: actions pinned to full SHAs: {uses}")
        runs = [s.get("run", "") for j in jobs.values() for s in j.get("steps", [])]
        check(runs and all("${{" not in r_ for r_ in runs), "AR-6: no ${{ ... }} in run: (PR data only through env)")
        co = next((s for s in rv.get("steps", []) if "actions/checkout" in str(s.get("uses"))), {})
        check(co.get("with", {}).get("fetch-depth") == 0 and "github.event.pull_request.number" in str(wf.get("concurrency"))
              and rv.get("timeout-minutes"), f"AR-7: fetch-depth 0, concurrency per PR, a time limit: {co} {wf.get('concurrency')}")
        ai = next((s for s in rv.get("steps", []) if "claude-code-action" in str(s.get("uses"))), {})
        args = str(ai.get("with", {}).get("claude_args", ""))
        check("--json-schema" in args and "--max-turns" in args and "verdict" in args and "REVIEW.md" in str(ai.get("with", {}).get("prompt"))
              and "ANTHROPIC_API_KEY" in str(ai.get("with", {}).get("anthropic_api_key")),
              f"AR-8: the agent returns JSON per a schema, with a turn limit, per REVIEW.md: {ai}")
        check(set(on.get("pull_request", {}).get("types", [])) >= {"opened", "synchronize", "labeled", "unlabeled"},
              f"AR-9: PR events with labels: {on}")

        script, env = step_script(wf, "review", "Verdict, status and comment")
        check(set(env) >= {"OUT", "OVERRIDE", "SHA", "PR", "GH_TOKEN"}, f"AR-10: the verdict step gets data through env: {env}")
        base = {"SHA": "a" * 40, "PR": "7", "OVERRIDE": "false", "GH_TOKEN": "x"}
        cases = {
            "REJECTED": ("failure", json.dumps({"verdict": "REJECTED", "summary": "luka", "findings": [
                {"severity": "critical", "file": "src/a.py", "line": 3, "description": "SQL z konkatenacji"}]})),
            "APPROVED": ("success", json.dumps({"verdict": "APPROVED", "summary": "ok", "findings": []})),
            "NEEDS_ATTENTION": ("success", json.dumps({"verdict": "NEEDS_ATTENTION", "summary": "minor", "findings": []})),
            "no JSON": ("failure", ""),
            "bad verdict": ("failure", json.dumps({"verdict": "OK"})),
        }
        for label, (want, out) in cases.items():
            res, calls = run_step(script, Path(tmp), {**base, "OUT": out})
            st = status_of(calls)
            check(res.returncode == 0 and st.get("state") == want and st.get("context") == "ai-review/verdict",
                  f"AR-11 verdict {label} -> {want}: {st} {res.stderr[-300:]}")
        res, calls = run_step(script, Path(tmp), {**base, "OUT": cases["REJECTED"][1]})
        posted = [c for c in calls if any(a.endswith("/issues/7/comments") for a in c) and "--method" in c and "POST" in c]
        body = " ".join(" ".join(c) for c in posted)
        check(posted and "<!-- AI-REVIEW-REPORT -->" in body and "REJECTED" in body and "src/a.py:3" in body,
              f"AR-12: a summary comment with the marker, the verdict and a file:line finding: {calls}")
        old = json.dumps([{"id": 55, "body": "<!-- AI-REVIEW-REPORT -->\nstary"}])
        res, calls = run_step(script, Path(tmp), {**base, "OUT": cases["APPROVED"][1]}, comments=old)
        check(any("PATCH" in c and any(a.endswith("/issues/comments/55") for a in c) for c in calls)
              and not any("POST" in c and any(a.endswith("/comments") for a in c) for c in calls),
              f"AR-13: an existing bot comment is updated, not duplicated: {calls}")
        res, calls = run_step(script, Path(tmp), {**base, "OUT": cases["REJECTED"][1], "OVERRIDE": "true"})
        st = status_of(calls)
        check(st.get("state") == "success" and "label override" in st.get("description", ""),
              f"AR-14: a bypass by label -> a green status with a description: {st}")
        oscript, oenv = step_script(wf, "override", "Label override")
        res, calls = run_step(oscript, Path(tmp), {"SHA": "b" * 40, "ACTION": "labeled", "GH_TOKEN": "x"})
        st = status_of(calls)
        check(res.returncode == 0 and st.get("state") == "success" and st.get("context") == "ai-review/verdict"
              and set(oenv) >= {"SHA", "ACTION"}, f"AR-15: the bypass job sets a green status without a review: {st}")
        res, calls = run_step(oscript, Path(tmp), {"SHA": "b" * 40, "ACTION": "unlabeled", "GH_TOKEN": "x"})
        check(status_of(calls).get("state") == "pending", f"AR-16: removing the bypass -> pending: {status_of(calls)}")

        r = run(["install"], repo)
        check(r.returncode == 1 and "already exists" in r.stdout + r.stderr, f"AR-17: without --force it does not overwrite: {r.stdout}")
        r = run(["install", "--force", "--all-prs"], repo)
        wf2 = yaml.safe_load(path.read_text(encoding="utf-8"))
        check(r.returncode == 0 and "'ai-review'" not in wf2["jobs"]["review"]["if"]
              and "head.repo.full_name == github.repository" in wf2["jobs"]["review"]["if"],
              f"AR-18: --all-prs without the label condition, the fork block stays: {wf2['jobs']['review']['if']}")

        draft = repo / "docs" / "project" / "00-reconstruction" / "REVIEW.draft.md"
        r = run(["review-md"], repo)
        check(r.returncode == 1 and "REVIEW.draft.md" in r.stdout + r.stderr, f"AR-19: no draft -> 1: {r.stdout}")
        draft.parent.mkdir(parents=True)
        draft.write_text("# Zasady przeglądu PR\n## Ważne\n- reguła\n", encoding="utf-8")
        r = run(["review-md"], repo)
        check(r.returncode == 0 and (repo / "REVIEW.md").read_text(encoding="utf-8") == draft.read_text(encoding="utf-8"),
              f"AR-20: review-md copies the approved draft to REVIEW.md: {r.stdout}{r.stderr}")
        r = run(["review-md"], repo)
        check(r.returncode == 1 and "already exists" in r.stdout + r.stderr, f"AR-21: REVIEW.md is not overwritten: {r.stdout}")
        r = run(["install", "--force"], repo)
        check(r.returncode == 0 and "review-md" not in r.stdout, f"AR-22: with REVIEW.md install does not suggest review-md: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} AI PR review in CI tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
