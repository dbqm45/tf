#!/usr/bin/env python3
"""Tests of the factory tool `tools/flow_compare.py` (comparing flows — the /tf loop, mode-pdi, the plan mode alone — on the same
tickets: anonymized diffs for blind grading and a report with measures). python3 tests/test_flow_compare.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPT = ROOT / "tools" / "flow_compare.py"


def git(repo, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=repo, check=True,
                   capture_output=True)


def lines(n, w="l"):
    return "".join(f"{w}{i}\n" for i in range(n))


def branch(repo, name, files, commits=1):
    git(repo, "checkout", "-q", "main")
    git(repo, "checkout", "-qb", name)
    items = list(files.items())
    for i in range(commits):
        for rel, text in items[i::commits]:
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        git(repo, "add", ".")
        git(repo, "commit", "-qm", f"{name} {i}")


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=120)


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    if not SCRIPT.is_file():
        print(f"✗ missing {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        repo = t / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# r\n")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "init")
        branch(repo, "plan/T-1", {"src/a.py": lines(40)})
        branch(repo, "story/T-1", {"src/a.py": lines(50), "tests/test_a.py": lines(30),
                                   "docs/project/changes/CHG-1/runs/TSK-1.md": lines(20)}, commits=3)
        branch(repo, "pdi/T-1", {"src/a.py": lines(60), "tests/test_a.py": lines(40),
                                 "docs/project/changes/CHG-1/plan.md": lines(120),
                                 "docs/project/changes/CHG-1/requirements.md": lines(150)}, commits=2)
        manifest = {"repo": str(repo), "base": "main", "baseline": "plan", "tickets": [
            {"id": "T-1", "runs": [
                {"flow": "plan", "branch": "plan/T-1", "cost_usd": 6.0, "minutes": 20},
                {"flow": "tf", "branch": "story/T-1", "cost_usd": 14.0, "minutes": 45},
                {"flow": "pdi", "branch": "pdi/T-1", "cost_usd": 72.0, "minutes": 210}]}]}
        mf = t / "flows.json"
        mf.write_text(json.dumps(manifest))
        out = t / "blind"
        r = run("prepare", str(mf), "--out", str(out), "--seed", "7", cwd=t)
        diffs = sorted(p.name for p in (out / "T-1").glob("*.diff")) if (out / "T-1").is_dir() else []
        key = json.loads((out / "key.json").read_text()) if (out / "key.json").is_file() else {}
        check(r.returncode == 0 and diffs == ["A.diff", "B.diff", "C.diff"] and set(key.get("T-1", {}).values()) ==
              {"plan", "tf", "pdi"}, f"F-1: prepare gives A/B/C diffs and a separate key: {r.stdout}{r.stderr} {diffs} {key}")
        body = "".join((out / "T-1" / d).read_text() for d in diffs)
        check("story/T-1" not in body and "pdi/T-1" not in body and "tf" not in body,
              "F-2: the diffs do not reveal the flow (branch names, flow names)")
        check((out / "T-1" / "ocena.json").is_file() and "kryteria" in (out / "T-1" / "ocena.json").read_text(),
              "F-3: a grading template with criteria for the grader next to the diffs")
        check(not (out / "T-1" / "key.json").exists(), "F-4: the key is not in the grader's directory")

        inv = {v: k for k, v in key.get("T-1", {}).items()}
        verdicts = {"T-1": {inv["plan"]: {"score": 7, "mergeable": True},
                            inv["tf"]: {"score": 8, "mergeable": True},
                            inv["pdi"]: {"score": 8, "mergeable": False}}}
        (out / "oceny.json").write_text(json.dumps(verdicts))
        rep = t / "report.md"
        r = run("report", str(mf), "--key", str(out / "key.json"), "--verdicts", str(out / "oceny.json"),
                "--out", str(rep), cwd=t)
        text = rep.read_text() if rep.is_file() else ""
        check(r.returncode == 0 and "| tf |" in text and "| pdi |" in text and "| plan |" in text,
              f"F-5: a report with a row per flow: {r.stdout}{r.stderr} {text[:400]}")
        row = next((l for l in text.splitlines() if l.startswith("| pdi |")), "")
        check("270" in row and "100" in row and "12,0×" in row and "2" in row,
              f"F-6: pdi: artifacts 270, code 100 (src + tests), cost 12,0× the baseline, 2 commits: {row}")
        row = next((l for l in text.splitlines() if l.startswith("| tf |")), "")
        check("1,75" in row and "8" in row and "| yes |" in row,
              f"F-7: tf: cost per point 14/8 = 1,75 USD, grade 8, ready to merge: {row}")
        check("Verdict" in text and "tf" in text.split("Verdict", 1)[1][:200],
              f"F-8: verdict: the best grade among the merge-ready ones, the cheaper on a tie: {text[-400:]}")
        check("Files:" in text and "flows.json" in text, "F-9: the report declares the data source (claims_check)")
        r = run("report", str(mf), "--key", str(out / "key.json"), "--out", str(t / "bez.md"), cwd=t)
        check(r.returncode == 0 and "no score" in (t / "bez.md").read_text(),
              f"F-10: a report without grades shows the measures and “no score”: {r.stdout}{r.stderr}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} flow comparison tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
