#!/usr/bin/env python3
"""Tests of the commit-msg hook (skill core-conventional-commits, scripts/commit_msg.py): the Conventional Commits header,
the `Change:` footers (a change or cut key, D3 of the pdi contract) and `Flag:`, a required `Change:` on a branch with a key,
installing the hook in a git repository. python3 .claude/tests/test_commit_msg.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-conventional-commits" / "scripts" / "commit_msg.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.com", "PYTHONDONTWRITEBYTECODE": "1"}


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=ENV, timeout=60)


def new_repo(tmp: str, branch: str = "main") -> Path:
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", branch)
    return repo


def check_msg(repo: Path, message: str) -> subprocess.CompletedProcess:
    f = repo / "MSG"
    f.write_text(message, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "check", str(f)], cwd=repo, capture_output=True, text=True,
                          env=ENV, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    ok = {
        "plain commit": "feat(cart): apply discount codes\n",
        "Change with TSK": "feat(payments): retry failed payment\n\nWhy it matters.\n\nChange: TSK-57\n",
        "Change with CHG and scope F4": "docs(CHG-12): faza requirements (pdi)\n\nChange: CHG-12\n",
        "several keys": "fix(payments): avoid double charge\n\nChange: TSK-57, TSK-58\n",
        "Flag": "feat(payments): retry behind a flag\n\nChange: TSK-57\nFlag: payment-retry\n",
        "Merge": "Merge branch 'main' into story/x\n",
        "fixup": "fixup! feat(cart): apply discount codes\n",
        "git comments": "feat(cart): apply codes\n\n# Please enter the commit message\n# On branch main\n",
        "breaking": "feat(api)!: remove v1 endpoints\n\nBREAKING CHANGE: clients must call /v2\n",
    }
    bad = {
        "no type": ("apply discount codes\n", "type"),
        "period": ("feat(cart): apply discount codes.\n", "period"),
        "description too long": ("feat(cart): " + "a" * 73 + "\n", "72"),
        "no blank line": ("feat(cart): apply codes\nbody here\n", "blank line"),
        "bad key in Change": ("feat(cart): apply codes\n\nChange: tsk-57\n", "tsk-57"),
        "empty Change": ("feat(cart): apply codes\n\nChange:\n", "Change"),
        "Flag with a space": ("feat(cart): apply codes\n\nChange: TSK-1\nFlag: payment retry\n", "Flag"),
        "empty message": ("# only a comment\n", "empty"),
        "breaking in lowercase": ("feat(api): drop v1\n\nbreaking change: gone\n", "BREAKING CHANGE"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        for label, message in ok.items():
            r = check_msg(repo, message)
            check(r.returncode == 0, f"CM-1 passes: {label}: {r.stdout}{r.stderr}")
        for label, (message, needle) in bad.items():
            r = check_msg(repo, message)
            check(r.returncode == 1 and needle in r.stdout + r.stderr, f"CM-2 rejects: {label}: {r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp, "story/tsk-57-ponowienie-platnosci")
        r = check_msg(repo, "feat(payments): retry failed payment\n")
        check(r.returncode == 1 and "Change: TSK-57" in r.stdout + r.stderr,
              f"CM-3: a branch with a key without a footer -> an error with a ready line to add: {r.stdout}{r.stderr}")
        r = check_msg(repo, "feat(payments): retry failed payment\n\nChange: TSK-57\n")
        check(r.returncode == 0, f"CM-4: a branch with a key and a footer -> OK: {r.stdout}{r.stderr}")
        r = check_msg(repo, "feat(payments): retry failed payment\n\nChange: TSK-58\n")
        check(r.returncode == 1 and "TSK-57" in r.stdout + r.stderr, f"CM-5: a footer with a different key than the branch: {r.stdout}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        local = repo / ".claude" / "skills" / "core-conventional-commits" / "scripts" / "commit_msg.py"
        local.parent.mkdir(parents=True)
        local.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")   # as in a project with the factory
        git(repo, "add", ".claude")
        r = subprocess.run([sys.executable, str(local), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        hook = repo / ".git" / "hooks" / "commit-msg"
        check(r.returncode == 0 and hook.is_file() and os.access(hook, os.X_OK),
              f"CM-6: install writes an executable commit-msg hook: {r.stdout}{r.stderr}")
        (repo / "a.txt").write_text("a", encoding="utf-8")
        git(repo, "add", "a.txt")
        r = git(repo, "commit", "-q", "-m", "add a file")
        check(r.returncode != 0 and "commit-msg" in r.stdout + r.stderr and git(repo, "rev-parse", "HEAD").returncode != 0,
              f"CM-7: the installed hook rejects a commit outside the format: {r.stdout}{r.stderr}")
        r = git(repo, "commit", "-q", "-m", "feat(core): add file", "-m", "Change: TSK-1")
        check(r.returncode == 0, f"CM-8: the installed hook lets a valid commit through: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(SCRIPT), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        check(r.returncode == 0, f"CM-9: a repeated install (our hook) without an error: {r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        hook = repo / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\nexec npx commitlint --edit \"$1\"\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        check(r.returncode == 1 and "commitlint" in hook.read_text(encoding="utf-8") and "commit_msg.py" in r.stdout,
              f"CM-10: a foreign hook is not overwritten; the output says how to attach the check: {r.stdout}{r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} commit-msg hook tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
