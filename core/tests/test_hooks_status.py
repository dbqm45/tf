#!/usr/bin/env python3
"""Testy factory/hooks_status.py: czy hooki fabryki działały w ostatnich commitach (log vs historia git)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory").is_dir())
SCRIPT = ROOT / "factory" / "hooks_status.py"
CHECK = ROOT / "factory" / "check.py"


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


NO_CI = {k: v for k, v in os.environ.items() if k != "CI"}   # testy działają też w GitHub Actions (CI=true)


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
        (repo / ".claude" / "logs").mkdir(parents=True)
        (repo / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"SessionEnd": []}}), encoding="utf-8")
        log = repo / ".claude" / "logs" / "skill-hints.jsonl"
        log.write_text(json.dumps({"ts": "2026-10-18T10:00:00+00:00"}) + "\n", encoding="utf-8")
        commit(repo, "a", "2026-10-18T10:30:00+00:00")           # w ciągu godziny od logu — w porządku

        r = run("--root", str(repo), "--json")
        s = json.loads(r.stdout)
        check(r.returncode == 0 and s["active"] is True and s["after_commits"] == 0, f"H1 aktywne: {s}")

        commit(repo, "b", "2026-10-18T13:00:00+00:00")
        commit(repo, "c", "2026-10-18T14:00:00+00:00")
        r = run("--root", str(repo), "--json")
        s = json.loads(r.stdout)
        check(s["active"] is False and s["after_commits"] == 2, f"H2 luka: {s}")
        check(s["last_log"].startswith("2026-10-18T10:00"), f"H2 ostatni log: {s}")
        r = run("--root", str(repo))
        check(r.returncode == 0 and "nieaktywne" in r.stdout and "2 commit" in r.stdout and "jednym repozytorium"
              in r.stdout, f"H2 tekst: {r.stdout}")

        # jeden commit po luce to jeszcze nie sygnał (bieżąca sesja mogła nie zapisać SessionEnd)
        log.write_text(json.dumps({"ts": "2026-10-18T12:30:00+00:00"}) + "\n", encoding="utf-8")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is True and s["after_commits"] == 1, f"H3 jeden commit: {s}")

        # jev.jsonl (pisany też przez testy) nie liczy się jako ślad hooków
        log.unlink()
        (repo / ".claude" / "logs" / "jev.jsonl").write_text(json.dumps({"ts": "2026-10-18T15:00:00"}) + "\n")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is False and s["last_log"] is None and s["after_commits"] == 3, f"H4 bez logów hooków: {s}")

        # w CI nie ma sesji Claude Code ani logów — bez ostrzeżenia
        env = {**os.environ, "CI": "true"}
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo), "--json"], capture_output=True, text=True,
                           timeout=60, env=env, stdin=subprocess.DEVNULL)
        check(json.loads(r.stdout)["active"] is None, f"H7 CI: {r.stdout}")

        # repozytorium bez hooków w settings.json: nic do sprawdzania
        (repo / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        s = json.loads(run("--root", str(repo), "--json").stdout)
        check(s["active"] is None, f"H5 bez hooków: {s}")

    r = subprocess.run([sys.executable, str(CHECK), "-k", "nic_takiego"], capture_output=True, text=True, timeout=900,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, cwd=ROOT, env=NO_CI)
    check("hooki fabryki" in r.stdout, f"H6 krok w check.py: {r.stdout[-500:]}")

    for f in fails:
        print("✗", f)
    print(f"{total - len(fails)}/{total} testów hooks_status zielonych")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
