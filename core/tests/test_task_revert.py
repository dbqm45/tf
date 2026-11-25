#!/usr/bin/env python3
"""Reverting a task (`run_state.py revert <dir> --by human:<id>`): after the human says No to the push and then chooses
"Revert everything", the factory goes back to the state before /tf-task started. `run_report.py start` records the base
(branch, commit, a clean tree and the files already dirty); revert checks out the base branch at its current state,
deletes the task branch only when it was never pushed, moves the task files to `.tf/backup/revert-<KEY>-<date>/` and
prints how to undo. It never touches the human's own changes or stash, never runs `git reset --hard` or `git clean`,
and refuses without `--by human:<id>`, for a run without a recorded base and with foreign uncommitted changes.
python3 .claude/tests/test_task_revert.py"""
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
    return {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
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


def task(base: Path, name: str, before=None) -> tuple[Path, str, str]:
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
    r = call(p, REPORT, "start", "Płatność kartą", "--key", KEY, "--story", "Jako kierowca chcę zapłacić kartą.")
    assert r.returncode == 0, r.stdout + r.stderr
    d = str(p / ".tf" / "runs" / KEY)
    git(p, "switch", "-q", "-c", "story/platnosc-karta")
    call(p, SCRIPT, "stage", d, "intake")
    (p / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
    git(p, "add", "pay.py", str(CHANGES / KEY))
    git(p, "commit", "-q", "-m", "feat(pay): card payment")
    return p, d, sha


def stashed(p: Path) -> None:
    """The human's own work in a stash before the task."""
    (p / "README.md").write_text("stashed\n", encoding="utf-8")
    git(p, "stash", "push", "-q")


def meta(d: str) -> dict:
    return json.loads((Path(d) / "run.json").read_text(encoding="utf-8"))


def backups(p: Path) -> list[Path]:
    return sorted((p / ".tf" / "backup").glob(f"revert-{KEY}-*")) if (p / ".tf" / "backup").is_dir() else []


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # RV-1: start records the base: branch, commit, a clean tree
        p, d, sha = task(base, "plain", before=stashed)
        b = meta(d).get("base") or {}
        check(b.get("branch") == "main" and b.get("sha") == sha and b.get("clean") is True and b.get("dirty") == [],
              f"RV-1: start records the base branch, commit and a clean tree: {b}")
        check(meta(d).get("branch") == "story/platnosc-karta",
              f"RV-1b: the loop records the task branch once it is on it: {meta(d).get('branch')}")
        stash = git(p, "stash", "list").stdout

        # RV-2: without --by human:<id> → refused, nothing changes
        for extra in ([], ["--by", "model"]):
            r = call(p, SCRIPT, "revert", d, *extra)
            check(r.returncode != 0 and "--by human:" in r.stdout + r.stderr
                  and git(p, "branch", "--show-current").stdout.strip() == "story/platnosc-karta" and Path(d).is_dir(),
                  f"RV-2: revert without --by human:<id> is refused and changes nothing ({extra}): {r.stdout}{r.stderr}")

        # RV-3: revert → back on main at its commit, the unpushed branch deleted, the task files archived, undo printed
        tip = head(p)
        r = call(p, SCRIPT, "revert", d, "--by", "human:ada")
        out = r.stdout + r.stderr
        arch = backups(p)
        check(r.returncode == 0 and git(p, "branch", "--show-current").stdout.strip() == "main" and head(p) == sha,
              f"RV-3: revert returns to the base branch at its commit: {r.returncode} {out}")
        check(not git(p, "branch", "--list", "story/platnosc-karta").stdout.strip() and tip[:7] in out
              and "git branch story/platnosc-karta" in out,
              f"RV-4: the unpushed task branch is deleted and the undo command names its tip: {out}")
        check(len(arch) == 1 and (arch[0] / "changes" / KEY / "plan.md").is_file()
              and (arch[0] / "runs" / KEY / "run.json").is_file()
              and not (p / CHANGES / KEY).exists() and not Path(d).exists() and arch[0].name in out,
              f"RV-5: the task files move to .tf/backup/revert-{KEY}-<date>/: {arch} {out}")
        rec = json.loads((arch[0] / "revert.json").read_text(encoding="utf-8")) if arch else {}
        check(rec.get("by") == "human:ada" and rec.get("branch") == "story/platnosc-karta" and rec.get("tip") == tip,
              f"RV-6: the archive records who reverted, the branch and its tip: {rec}")
        check(git(p, "stash", "list").stdout == stash and stash.strip(),
              f"RV-7: the human's stash is untouched: {stash!r} → {git(p, 'stash', 'list').stdout!r}")

        # RV-8: a pushed branch is kept (deleting it is the human's call); the rest of the revert happens
        p, d, sha = task(base, "pushed")
        remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(p, "remote", "add", "origin", str(remote))
        git(p, "push", "-q", "-u", "origin", "story/platnosc-karta")
        r = call(p, SCRIPT, "revert", d, "--by", "human:ada")
        out = r.stdout + r.stderr
        check(r.returncode == 0 and git(p, "branch", "--list", "story/platnosc-karta").stdout.strip()
              and git(p, "branch", "--show-current").stdout.strip() == "main" and "pushed" in out and backups(p),
              f"RV-8: a pushed task branch is kept and the revert says so: {r.returncode} {out}")

        # RV-9: foreign uncommitted changes block the revert and are listed; nothing changes
        p, d, sha = task(base, "foreign")
        (p / "README.md").write_text("my own edit\n", encoding="utf-8")
        (p / "mine.txt").write_text("mine\n", encoding="utf-8")
        r = call(p, SCRIPT, "revert", d, "--by", "human:ada")
        out = r.stdout + r.stderr
        check(r.returncode != 0 and "README.md" in out and "mine.txt" in out and Path(d).is_dir() and not backups(p)
              and git(p, "branch", "--show-current").stdout.strip() == "story/platnosc-karta"
              and (p / "README.md").read_text(encoding="utf-8") == "my own edit\n",
              f"RV-9: foreign uncommitted changes block the revert and are listed: {r.returncode} {out}")

        # RV-10: a file already dirty before the task stays as it was
        p, d, sha = task(base, "dirty-before", before=lambda q: (q / "notes.txt").write_text("before\n", encoding="utf-8"))
        b = meta(d).get("base") or {}
        r = call(p, SCRIPT, "revert", d, "--by", "human:ada")
        check(b.get("clean") is False and b.get("dirty") == ["notes.txt"] and r.returncode == 0
              and (p / "notes.txt").read_text(encoding="utf-8") == "before\n",
              f"RV-10: a change from before the task is recorded and left alone: {b} {r.stdout}{r.stderr}")

        # RV-11: an old run without a recorded base → refused with a clear message
        p, d, sha = task(base, "old")
        m = meta(d)
        m.pop("base", None)
        (Path(d) / "run.json").write_text(json.dumps(m), encoding="utf-8")
        r = call(p, SCRIPT, "revert", d, "--by", "human:ada")
        check(r.returncode != 0 and "base" in r.stdout + r.stderr and Path(d).is_dir()
              and git(p, "branch", "--show-current").stdout.strip() == "story/platnosc-karta",
              f"RV-11: a run without a recorded base is refused: {r.stdout}{r.stderr}")

    # RV-12: the script never runs git reset --hard or git clean
    source = SCRIPT.read_text(encoding="utf-8")
    check('"reset", "--hard"' not in source and '"clean"' not in source,
          "RV-12: run_state.py does not call git reset --hard or git clean")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task revert tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
