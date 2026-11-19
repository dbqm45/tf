#!/usr/bin/env python3
"""B3: factory effectiveness metrics (`tf metrics`, .tf/factory/metrics.py) on an artificial git repository.

python3 tests/test_metrics.py

The revert rate, accepted changes (merged and not reverted for N days), changes in progress, causes of rework
(the `Rework-Cause:` trailer), the cost of an accepted change from `.tf/logs/usage.jsonl`, the cycle time from the PR history (`gh`, a stub)
and the baseline window. No network and no model.
"""
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory").is_dir())
ENGINE = ROOT / ".tf" / "factory"
NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)

FAKE_GH = """#!/usr/bin/env python3
import json, sys
if sys.argv[1:3] == ["pr", "list"]:
    print(json.dumps([
        {"number": 1, "createdAt": "2026-10-28T10:00:00Z", "mergedAt": "2026-10-28T14:00:00Z", "commits": [{}, {}]},
        {"number": 2, "createdAt": "2026-10-29T08:00:00Z", "mergedAt": "2026-10-30T08:00:00Z", "commits": [{}]},
        {"number": 9, "createdAt": "2026-09-30T08:00:00Z", "mergedAt": "2026-10-01T10:00:00Z", "commits": [{}]}]))
    raise SystemExit(0)
raise SystemExit(1)
"""


def load():
    spec = importlib.util.spec_from_file_location("tf_metrics", ENGINE / "metrics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(repo: Path, *args, when: datetime | None = None) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com"}
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when.isoformat()
    return subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


def commit(repo: Path, msg: str, when: datetime) -> str:
    f = repo / "f.txt"
    f.write_text(f.read_text() + msg + "\n" if f.exists() else msg + "\n")
    git(repo, "add", "f.txt")
    git(repo, "commit", "-q", "-m", msg, when=when)
    return git(repo, "rev-parse", "HEAD")


def build(repo: Path) -> None:
    git(repo, "init", "-q", "-b", "main")
    d = lambda days: NOW - timedelta(days=days)
    # the baseline window (28–56 days ago): 2 changes, none reverted
    commit(repo, "feat: baseline one (#9)", d(40))
    commit(repo, "fix: baseline two", d(35))
    commit(repo, "chore(release): 1.0.0", d(34))                       # a release — not a change
    # the current window (0–28 days): 4 changes; one reverted within 7 days; one younger than 7 days (in progress)
    commit(repo, "feat: add export (#1)", d(13))
    bad = commit(repo, "feat: add import (#2)", d(11))
    commit(repo, f'Revert "feat: add import (#2)"\n\nThis reverts commit {bad}.', d(10))
    commit(repo, "fix: correct totals\n\nRework-Cause: spec-gap", d(9))
    commit(repo, "fix: rounding\n\nRework-Cause: luka-specyfikacji", d(8))   # a pre-19.0.0 value: not mapped
    commit(repo, "feat: fresh change", d(2))


def main() -> int:
    fails = []
    m = load()
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t) / "p"
        repo.mkdir()
        build(repo)
        logs = repo / ".tf" / "logs"
        logs.mkdir(parents=True)
        usage = [{"ts": (NOW - timedelta(days=12)).isoformat(), "models": {"claude-sonnet-5-5": 1},
                  "input": 1_000_000, "output": 0, "cache_read": 0, "cache_write": 0},
                 {"ts": (NOW - timedelta(days=40)).isoformat(), "models": {"claude-sonnet-5-5": 1},
                  "input": 500_000, "output": 0, "cache_read": 0, "cache_write": 0}]
        (logs / "usage.jsonl").write_text("\n".join(json.dumps(u) for u in usage) + "\n", encoding="utf-8")
        prices = {"sonnet": {"input": 2, "output": 10, "cache_read": 0.2, "cache_write": 2.5}}

        res = m.compute(repo, now=NOW, weeks=4, revert_days=7, prices=prices, prs=None)
        cur, base = res["current"], res["baseline"]
        # M-1: changes without releases and reverts; 5 changes in the current window (export, import, totals, rounding, fresh)
        if cur["changes"] != 5 or base["changes"] != 2:
            fails.append(f"M-1: changes on the main line without chore(release) and revert commits: {cur['changes']}/"
                         f"{base['changes']}")
        # M-2: reverts — import reverted within 7 days; fresh (2 days) in progress, outside the denominator
        if (cur["reverted"], cur["pending"], cur["accepted"]) != (1, 1, 3) or abs(cur["revert_rate"] - 0.25) > 1e-9:
            fails.append(f"M-2: reverted 1, in progress 1, accepted 3, revert rate 1/4: {cur}")
        # M-3: rework causes from the trailer; an unknown value (also a former Polish one) → unknown
        if cur["rework_causes"] != {"spec-gap": 1, "unknown": 1}:
            fails.append(f"M-3: Rework-Cause: {cur['rework_causes']}")
        # M-4: cost from usage.jsonl in the window; cost of an accepted change = cost / accepted; a mark for no human work
        if abs((cur["cost_usd"] or 0) - 2.0) > 1e-9 or abs((cur["cost_per_accepted"] or 0) - 2.0 / 3) > 1e-9 \
                or abs((base["cost_usd"] or 0) - 1.0) > 1e-9 or cur.get("human_time") is not False:
            fails.append(f"M-4: cost $2, per accepted change $0.667, baseline $1, without human time: {cur} {base}")
        # M-5: without PR data the cycle time is unknown (not zero)
        if cur["cycle_median_h"] is not None:
            fails.append(f"M-5: without the PR history the median cycle time = no data: {cur['cycle_median_h']}")

        # M-6: the PR history from gh (a stub in PATH): the median from opening to merge in the window, the number of commits per PR
        bin_dir = Path(t) / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH, encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        old = os.environ["PATH"]
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old}"
        try:
            prs = m.pr_history(repo)
        finally:
            os.environ["PATH"] = old
        res2 = m.compute(repo, now=NOW, weeks=4, revert_days=7, prices=prices, prs=prs)
        c2, b2 = res2["current"], res2["baseline"]
        if c2["cycle_median_h"] != 14.0 or c2["prs"] != 2 or c2["commits_per_pr_median"] != 1.5 \
                or b2["cycle_median_h"] != 26.0:
            fails.append(f"M-6: the cycle time from PRs (4 h and 24 h → median 14 h), baseline 26 h, commits per PR 1.5: "
                         f"{c2} {b2}")
        if m.pr_history(Path(t) / "missing") != []:
            fails.append("M-6: without gh or outside a repository the PR history is empty, no exception")

        # M-7: the .md and .json report in .tf/reports/, the acceptance definition in the header, current and baseline columns
        out = m.write_report(repo, res2)
        md = (repo / ".tf" / "reports" / "metrics.md").read_text(encoding="utf-8")
        js = json.loads((repo / ".tf" / "reports" / "metrics.json").read_text(encoding="utf-8"))
        if out != repo / ".tf" / "reports" / "metrics.md" or "not reverted for 7 days" not in md \
                or "Revert rate" not in md or "without human work" not in md or js["current"]["changes"] != 5:
            fails.append(f"M-7: the metrics.md and metrics.json report: {md[:400]}")

    # M-8: `tf metrics` in the launcher starts the engine (help without an error)
    tf = (ENGINE / "tf.py").read_text(encoding="utf-8")
    if "metrics" not in tf.split('"""')[1] or '"metrics"' not in tf:
        fails.append("M-8: tf metrics in the launcher's help and dispatch")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} factory metrics: {8 - len(fails)}/8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
