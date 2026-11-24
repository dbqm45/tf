#!/usr/bin/env python3
"""Tests of .tf/factory/hooks_status.py: whether the factory hooks ran in the latest commits (the log vs the git history)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory").is_dir())
SCRIPT = ROOT / ".tf" / "factory" / "hooks_status.py"
CHECK = ROOT / ".tf" / "factory" / "check.py"


def git(repo: Path, *args, date="2026-10-18T12:00:00+00:00"):
    env = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_AUTHOR_DATE": date,
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_COMMITTER_DATE": date,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env, check=True, capture_output=True,
                   stdin=subprocess.DEVNULL)


def commit(repo: Path, name: str, date: str):
    (repo / name).write_text(name, encoding="utf-8")
    git(repo, "add", "-A", date=date)
    git(repo, "commit", "-q", "-m", f"feat: {name}", date=date)


NO_CI = {k: v for k, v in os.environ.items() if k != "CI"}   # the tests also run in GitHub Actions (CI=true)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=NO_CI)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    r = run("--help")
    check(r.returncode == 0 and "--json" in r.stdout and "hook" in r.stdout.lower(), f"H0 --help: {r.stdout[:200]}")

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        (repo / ".tf" / "logs").mkdir(parents=True)
        (repo / ".claude").mkdir()
        (repo / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"SessionEnd": []}}), encoding="utf-8")
        log = repo / ".tf" / "logs" / "skill-hints.jsonl"
        log.write_text(json.dumps({"ts": "2026-10-18T10:00:00+00:00"}) + "\n", encoding="utf-8")
        commit(repo, "a", "2026-10-18T10:30:00+00:00")           # within an hour of the log — fine

        r = run("--root", str(repo), "--json")
        s = json.loads(r.stdout)
        check(r.returncode == 0 and s["active"] is True and s["after_commits"] == 0, f"H1 aktywne: {s}")

        commit(repo, "b", "2026-10-18T13:00:00+00:00")
        commit(repo, "c", "2026-10-18T14:00:00+00:00")
        r = run("--root", str(repo), "--json")
        s = json.loads(r.stdout)
        check(s["active"] is False and s["after_commits"] == 2, f"H2 luka: {s}")
        check(s["last_log"].startswith("2026-10-18T10:00"), f"H2 the last log: {s}")
        r = run("--root", str(repo))
        check(r.returncode == 0 and "not active" in r.stdout and "2 commit" in r.stdout and "one repository"
              in r.stdout, f"H2 tekst: {r.stdout}")

        # a single commit after a gap is not yet a signal (the current session may not have written SessionEnd)
        log.write_text(json.dumps({"ts": "2026-10-18T12:30:00+00:00"}) + "\n", encoding="utf-8")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is True and s["after_commits"] == 1, f"H3 one commit: {s}")

        # jev.jsonl (also written by tests) does not count as a trace of the hooks
        log.unlink()
        (repo / ".tf" / "logs" / "jev.jsonl").write_text(json.dumps({"ts": "2026-10-18T15:00:00"}) + "\n")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is False and s["last_log"] is None and s["after_commits"] == 3, f"H4 without hook logs: {s}")

        # check.py runs hooks_status.py as its "factory hooks" step: check.py --root on this repository, where the only
        # script is a copy of hooks_status.py — the other steps are skipped, so this does not run the whole factory check
        (repo / ".tf" / "factory").mkdir()
        (repo / ".tf" / "factory" / "hooks_status.py").write_bytes(SCRIPT.read_bytes())
        expected = run("--root", str(repo)).stdout.strip().splitlines()[-1]
        r = subprocess.run([sys.executable, str(CHECK), "--root", str(repo)], capture_output=True, text=True, timeout=120,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, cwd=repo, env=NO_CI)
        step = next((ln for ln in r.stdout.splitlines() if "factory hooks" in ln), "")
        check(step.startswith("ℹ factory hooks:") and step.endswith(expected) and "not active" in step,
              f"H6 a step in check.py runs hooks_status.py (info, its verdict line): {r.stdout[-500:]}")

        # in CI there are no Claude Code sessions or logs — no warning
        env = {**os.environ, "CI": "true"}
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo), "--json"], capture_output=True, text=True,
                           timeout=60, env=env, stdin=subprocess.DEVNULL)
        check(json.loads(r.stdout)["active"] is None, f"H7 CI: {r.stdout}")

        # a repository without hooks in settings.json: nothing to check
        (repo / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is None, f"H5 without hooks: {s}")

    for f in fails:
        print("✗", f)
    print(f"{total - len(fails)}/{total} hooks_status tests green")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
