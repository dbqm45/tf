#!/usr/bin/env python3
"""One human confirmation pushes the task branch: `run_state.py push <dir> --by human:<id>` runs `git push -u <remote>
<task branch>` itself (no shell), so after the human's "Yes, push" in the loop's question no second permission window
appears (the `run_state.py *` allow rule covers it). It pushes only the task branch recorded in run.json, never forces,
sets the upstream and applies the autonomy policy (`autonomy.operations.git_push`) the way guard_bash does: `deny`
refuses; in Auto (no human answer) `confirm` refuses with the STOP `permissions` hint; only a `human:` value is accepted.
python3 .claude/tests/test_task_push.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")
CHANGES = Path("docs") / "project" / "changes"
KEY = "IMP-7"


def env(project: Path) -> dict:
    return {**{k: v for k, v in os.environ.items() if k != "TF_CONTAINER"}, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
            "TF_DASHBOARD_OPEN": "0", "TF_DASHBOARD_LIVE": "0", "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull}


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True,
                          env=env(project), timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "commit.gpgsign=false", *args], capture_output=True,
                          text=True, env=env(project), timeout=60)


def head(p: Path, ref: str = "HEAD") -> str:
    return git(p, "rev-parse", ref).stdout.strip()


def task(base: Path, name: str, before=None, title: str = "Płatność kartą") -> tuple[Path, str, str]:
    """A repository on main, a task started (`before` runs first), a story branch with one slice commit and the task
    files committed. Returns the project, the run directory and the base commit."""
    p = base / name
    p.mkdir(parents=True)
    git(p, "init", "-q", "-b", "main")
    (p / ".gitignore").write_text(".tf/\n", encoding="utf-8")
    (p / "README.md").write_text("x\n", encoding="utf-8")
    git(p, "add", "-A")
    git(p, "commit", "-q", "-m", "chore: init")
    if before:
        before(p)
    sha = head(p)
    r = call(p, REPORT, "start", title, "--key", KEY, "--story", "Jako kierowca chcę widzieć postój.")
    assert r.returncode == 0, r.stdout + r.stderr
    d = str(p / ".tf" / "runs" / KEY)
    git(p, "switch", "-q", "-c", "story/platnosc-karta")
    call(p, SCRIPT, "stage", d, "intake")
    (p / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
    git(p, "add", "pay.py", str(CHANGES / KEY))
    git(p, "commit", "-q", "-m", "feat(pay): card payment")
    return p, d, sha


def remote_for(base: Path, p: Path, name: str) -> Path:
    r = base / f"{name}.git"
    subprocess.run(["git", "init", "-q", "--bare", str(r)], check=True)
    git(p, "remote", "add", "origin", str(r))
    return r


def remote_head(r: Path, branch: str) -> str:
    return subprocess.run(["git", "-C", str(r), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
                          capture_output=True, text=True).stdout.strip()


def meta(d: str) -> dict:
    return json.loads((Path(d) / "run.json").read_text(encoding="utf-8"))


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    br = "story/platnosc-karta"
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # PU-1: refused without --by human:<id> (also a non-human value); nothing pushed
        p, d, _ = task(base, "plain")
        r_ = remote_for(base, p, "plain")
        for extra in ([], ["--by", "model"], ["--by", "agent:x"]):
            r = call(p, SCRIPT, "push", d, *extra)
            check(r.returncode != 0 and "--by human:" in r.stdout + r.stderr and not remote_head(r_, br),
                  f"PU-1: push without --by human:<id> is refused ({extra}): {r.stdout}{r.stderr}")

        # PU-2: with the human's answer: the task branch reaches the remote, with the upstream set
        r = call(p, SCRIPT, "push", d, "--by", "human:ada")
        up = git(p, "rev-parse", "--abbrev-ref", f"{br}@{{upstream}}").stdout.strip()
        check(r.returncode == 0 and remote_head(r_, br) == head(p, br),
              f"PU-2: push sends the task branch to the remote: {r.returncode} {r.stdout}{r.stderr}")
        check(up == f"origin/{br}", f"PU-3: push sets the upstream: {up!r}")
        check((meta(d).get("pushed") or {}).get("by") == "human:ada",
              f"PU-4: run.json records who approved the push: {meta(d).get('pushed')}")

        # PU-5: never forces: a remote that moved on is not overwritten
        other = base / "other"
        subprocess.run(["git", "clone", "-q", "-b", br, str(r_), str(other)], check=False, capture_output=True)
        if other.is_dir():
            (other / "x.txt").write_text("theirs\n", encoding="utf-8")
            git(other, "add", "x.txt")
            git(other, "commit", "-q", "-m", "chore: theirs")
            git(other, "push", "-q", "origin", br)
        theirs = remote_head(r_, br)
        git(p, "commit", "-q", "--allow-empty", "-m", "feat(pay): mine")
        r = call(p, SCRIPT, "push", d, "--by", "human:ada")
        check(other.is_dir() and r.returncode != 0 and remote_head(r_, br) == theirs,
              f"PU-5: a non-fast-forward push is rejected, the remote keeps its commits: {r.returncode} {r.stdout}{r.stderr}")
        src = SCRIPT.read_text(encoding="utf-8")
        start = src.find("def cmd_push")
        body = src[start:src.find("\ndef ", start + 1)] if start >= 0 else ""
        check(body and "--force" not in body and '"-f"' not in body and "shell=True" not in body,
              "PU-6: cmd_push never passes --force and runs git without a shell")

        # PU-7: another branch is refused: the human is on a different branch, or run.json names the base branch
        p, d, _ = task(base, "other-branch")
        r_ = remote_for(base, p, "other-branch")
        git(p, "switch", "-q", "-c", "feature/mine")
        r = call(p, SCRIPT, "push", d, "--by", "human:ada")
        check(r.returncode != 0 and not remote_head(r_, "feature/mine") and not remote_head(r_, br),
              f"PU-7: push refuses when the current branch is not the task branch: {r.stdout}{r.stderr}")
        git(p, "switch", "-q", "main")
        m = meta(d)
        m["branch"] = "main"
        (Path(d) / "run.json").write_text(json.dumps(m), encoding="utf-8")
        r = call(p, SCRIPT, "push", d, "--by", "human:ada")
        check(r.returncode != 0 and not remote_head(r_, "main"),
              f"PU-8: push refuses the base branch as a task branch: {r.stdout}{r.stderr}")

        # PU-9: git_push: deny in the project policy → refused, even with the human's answer
        p, d, _ = task(base, "deny")
        r_ = remote_for(base, p, "deny")
        (p / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (p / ".tf" / "config" / "config.yaml").write_text("autonomy:\n  operations:\n    git_push: deny\n", encoding="utf-8")
        r = call(p, SCRIPT, "push", d, "--by", "human:ada")
        check(r.returncode != 0 and "deny" in r.stdout + r.stderr and not remote_head(r_, br),
              f"PU-9: git_push: deny refuses the push: {r.stdout}{r.stderr}")

        # PU-10: Auto mode, policy confirm → refused with the STOP permissions hint (nobody answered)
        p, d, _ = task(base, "auto", title="Lista postojów")  # a normal weight: Auto applies
        r_ = remote_for(base, p, "auto")
        m = call(p, SCRIPT, "mode", d, "auto")
        check("mode Auto" in m.stdout, f"PU-10a: the task is in Auto: {m.stdout}")
        r = call(p, SCRIPT, "push", d)
        out = r.stdout + r.stderr
        check(r.returncode != 0 and "--code permissions" in out and not remote_head(r_, br),
              f"PU-10: in Auto the confirm policy refuses with the STOP permissions hint: {out}")

        # PU-11: the container has no git keys (guard_bash D1): refused there
        p, d, _ = task(base, "container")
        r_ = remote_for(base, p, "container")
        r = subprocess.run([sys.executable, str(SCRIPT), "push", d, "--by", "human:ada"], cwd=p, capture_output=True,
                           text=True, env={**env(p), "TF_CONTAINER": "1"}, timeout=120)
        check(r.returncode != 0 and not remote_head(r_, br), f"PU-11: no push from the factory container: {r.stdout}{r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task push tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
