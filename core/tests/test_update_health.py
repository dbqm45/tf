#!/usr/bin/env python3
"""A warning after a factory update (step H29, decision D13): `metrics.py --after-update` compares the window after
the last update with a window of the same length before it (git reverts, blocks and hook errors) and on
degradation gives the rollback command; the factory does not roll back by itself. Hook blocks go to the log without content.
python3 .claude/tests/test_update_health.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
METRICS = ROOT / ".tf" / "factory" / "metrics.py"
HOOKS = ROOT / ".claude" / "hooks"
NOW = datetime.now(timezone.utc).replace(microsecond=0)
UPDATE = NOW - timedelta(days=10)


def git(repo: Path, *args: str, when: datetime | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "T",
           "GIT_COMMITTER_EMAIL": "t@example.com"}
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when.isoformat()
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args], capture_output=True, text=True,
                          env=env, timeout=60)


def commit(repo: Path, msg: str, when: datetime) -> str:
    f = repo / "log.txt"
    f.write_text(f.read_text(encoding="utf-8") + msg + "\n" if f.exists() else msg + "\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg, when=when)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def project(base: Path, name: str, before_reverts: int, after_reverts: int, with_backup: bool = True) -> Path:
    """10 changes in each window (10 days before and 10 days after the update); some reverted after 2 days."""
    p = base / name
    p.mkdir()
    git(p, "init", "-q", "-b", "main")
    commit(p, "chore: init", UPDATE - timedelta(days=40))
    for window, start, n_rev in (("before", UPDATE - timedelta(days=10), before_reverts), ("after", UPDATE, after_reverts)):
        for i in range(10):
            when = start + timedelta(hours=6 + i * 6)   # within the window and older than the revert threshold (7 days)
            sha = commit(p, f"feat: change {window} {i}", when)
            if i < n_rev:
                commit(p, f'Revert "feat: change {window} {i}"\n\nThis reverts commit {sha}.', when + timedelta(days=2))
    if with_backup:
        stamp = UPDATE.astimezone().strftime("%Y%m%d-%H%M%S")
        b = p / ".tf" / "backup" / f"{stamp}-v10.11.0"
        b.mkdir(parents=True)
        (b / "backup.json").write_text(json.dumps({"version": "10.11.0", "files": []}), encoding="utf-8")
    man = p / ".claude" / "factory-manifest.json"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(json.dumps({"version": "10.17.0", "files": {}}), encoding="utf-8")
    return p


def log_entries(p: Path, name: str, times: list[datetime], **fields) -> None:
    f = p / ".tf" / "logs" / name
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as h:
        for t in times:
            h.write(json.dumps({"ts": t.timestamp(), **fields}) + "\n")


def health(p: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(METRICS), "--after-update", *args], cwd=p, capture_output=True,
                          text=True, timeout=120, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        # more reverts after the update → a warning with the rollback command
        p = project(base, "worse", before_reverts=1, after_reverts=5)
        r = health(p, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(r.returncode == 0 and data.get("from") == "10.11.0" and data.get("to") == "10.17.0"
              and (data.get("before") or {}).get("revert_rate") == 0.1 and (data.get("after") or {}).get("revert_rate") == 0.5,
              f"UH-1: the windows before and after the update with the revert rate and versions: {r.returncode} {r.stdout[:600]} {r.stderr[-300:]}")
        check(any("revert" in w for w in data.get("warnings") or []),
              f"UH-2: a rise in reverts of ≥ 15 points → warning: {data.get('warnings')}")
        r = health(p)
        check(r.returncode == 0 and "update.py --rollback" in r.stdout and "10.11.0" in r.stdout and "10.17.0" in r.stdout
              and "by itself" in r.stdout,
              f"UH-3: the warning gives the rollback command and says the factory does not roll back by itself: {r.stdout}")

        # no degradation → no warning
        p = project(base, "same", before_reverts=2, after_reverts=2)
        data = json.loads(health(p, "--json").stdout or "{}")
        check(data.get("warnings") == [], f"UH-4: the same revert rate → no warning: {data}")

        # hook blocks: a twofold rise and at least 5 after the update
        log_entries(p, "hook-blocks.jsonl", [UPDATE - timedelta(days=d) for d in (1, 3)], hook="tdd_guard", decision="deny")
        log_entries(p, "hook-blocks.jsonl", [UPDATE + timedelta(hours=h) for h in range(2, 14, 2)], hook="guard_paths",
                    decision="deny")
        data = json.loads(health(p, "--json").stdout or "{}")
        check((data.get("after") or {}).get("blocks") == 6 and (data.get("before") or {}).get("blocks") == 2
              and any("hook blocks" in w for w in data.get("warnings") or []),
              f"UH-5: hook blocks 2 → 6 → warning: {data}")
        log_entries(p, "hook-errors.jsonl", [UPDATE + timedelta(hours=h) for h in (1, 2, 3, 4)], hook="tdd_guard",
                    type="KeyError", where="tdd_guard.py:10", msg="x")
        data = json.loads(health(p, "--json").stdout or "{}")
        check(any("hook errors" in w for w in data.get("warnings") or []), f"UH-6: hook errors 0 → 4 → warning: {data}")

        # too little data: it does not warn on the basis of two changes
        p = base / "few"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        sha = commit(p, "feat: jedna", UPDATE + timedelta(days=1))
        commit(p, f'Revert "feat: jedna"\n\nThis reverts commit {sha}.', UPDATE + timedelta(days=2))
        b = p / ".tf" / "backup" / f"{UPDATE.astimezone().strftime('%Y%m%d-%H%M%S')}-v10.11.0"
        b.mkdir(parents=True)
        (b / "backup.json").write_text(json.dumps({"version": "10.11.0"}), encoding="utf-8")
        data = json.loads(health(p, "--json").stdout or "{}")
        check(data.get("warnings") == [] and "too few" in json.dumps(data, ensure_ascii=False),
              f"UH-7: with few changes the revert rate gives no warning, and the result says \'too little data\': {data}")

        # without a copy from the update → nothing to compare, code 0
        p = project(base, "noupdate", before_reverts=1, after_reverts=5, with_backup=False)
        r = health(p)
        check(r.returncode == 0 and "update" in r.stdout and "rollback" not in r.stdout,
              f"UH-8: without a pre-update copy there is nothing to compare — a message, not an error: {r.returncode} {r.stdout}")

        # tf doctor shows the warning (information)
        p = project(base, "doctor", before_reverts=1, after_reverts=5)
        shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__"))
        r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "tf.py"), "doctor"], cwd=p, capture_output=True,
                           text=True, timeout=300, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        check("update.py --rollback" in r.stdout and "Traceback" not in r.stderr,
              f"UH-9: tf doctor shows the post-update warning: {r.stdout[-800:]} {r.stderr[-300:]}")

        # the block log: an entry without the command content or path
        p = base / "hooklog"
        p.mkdir()
        r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import hook_errors; "
                            "hook_errors.record_block('guard_bash', 'deny')", str(HOOKS)], cwd=p, capture_output=True,
                           text=True, timeout=30, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        f = p / ".tf" / "logs" / "hook-blocks.jsonl"
        e = json.loads(f.read_text(encoding="utf-8").splitlines()[-1]) if f.is_file() else {}
        check(r.returncode == 0 and set(e) == {"ts", "hook", "decision"} and e.get("hook") == "guard_bash"
              and e.get("decision") == "deny" and abs(e.get("ts", 0) - time.time()) < 60,
              f"UH-10: record_block records the time, hook and decision — nothing more: {r.stderr[-300:]} {e}")

    # every hook that blocks records the block
    for name in ("tdd_guard.py", "guard_paths.py", "guard_bash.py", "cleanroom_guard.py", "scan_secrets.py"):
        text = (HOOKS / name).read_text(encoding="utf-8") if (HOOKS / name).is_file() else ""
        check("record_block(" in text, f"UH-11: {name} records the block in the log (record_block)")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} post-update warning tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
