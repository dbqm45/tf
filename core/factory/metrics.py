#!/usr/bin/env python3
"""Factory effectiveness metrics (B3): whether changes made with the factory are accepted, reverted, and what they cost.

  python3 .tf/factory/metrics.py                    # the last 4 weeks against the 4 weeks before
  python3 .tf/factory/metrics.py --weeks 2 --revert-days 14
  python3 .tf/factory/metrics.py --no-gh            # without PR history (git only)
  tf metrics [options]
  python3 .tf/factory/metrics.py --after-update [--json]   # whether anything got worse after the last factory update

Counts from git (main line, `--first-parent`, without `chore(release)` and revert commits):
- changes and accepted changes — accepted = merged and not reverted within N days (`--revert-days`, default 7);
  changes younger than N days are "in progress" and do not enter the percentage;
- revert rate — the main quality indicator;
- rework causes from the `Rework-Cause:` trailer (spec-gap, agent-error, requirement-change, unknown; any other value,
  including the pre-19.0.0 Polish ones in old commits, counts as unknown);
- token cost from `.tf/logs/usage.jsonl` (price list `prices_usd_per_mtok`) and the cost of an accepted change — without human labor;
- from PR history (`gh pr list`, when available): median time from PR opening to merge and the number of commits per PR.
The number of changes by itself is not a goal — it is easy to inflate. Report: `.tf/reports/metrics.md` and `metrics.json`.

`--after-update` (step H29, decision D13): the latest copy in `.tf/backup/` marks the moment of the factory update
and the version before it. The window after the update (up to 14 days) is compared with a window of the same length before it:
revert rate (a warning on a rise of ≥ 15 points when both windows have ≥ 5 settled changes),
hook blocks from `.tf/logs/hook-blocks.jsonl` (≥ 5 after and at least a twofold rise) and hook errors from
`.tf/logs/hook-errors.jsonl` (≥ 3 after and more than a twofold rise). The warning gives the rollback command
(`update.py --rollback`); the factory does not roll back by itself — with few changes this indicator is noisy.
"""
from __future__ import annotations

import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
import argparse
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAUSES = ("spec-gap", "agent-error", "requirement-change", "unknown")
RELEASE = re.compile(r"^chore\(release\)")
REVERT_SUBJECT = re.compile(r'^(Revert "|revert(\([^)]*\))?!?:)')
REVERTS_SHA = re.compile(r"This reverts commit ([0-9a-f]{7,40})")
CAUSE_RE = re.compile(r"^Rework-Cause:\s*(\S+)", re.M | re.I)


def _cost_module():
    spec = importlib.util.spec_from_file_location("tf_cost_report", Path(__file__).resolve().parent / "cost_report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git_log(repo: Path) -> list[dict]:
    """Main-line commits (newest first): sha, time, subject, body."""
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "--first-parent", "--format=%H%x1f%ct%x1f%B%x1e", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    rows = []
    for rec in out.stdout.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, ts, body = rec.split("\x1f", 2)
        rows.append({"sha": sha, "ts": datetime.fromtimestamp(int(ts), timezone.utc),
                     "subject": body.split("\n", 1)[0].strip(), "body": body})
    return rows


def pr_history(repo: Path) -> list[dict]:
    """Merged PRs from `gh` (number, createdAt, mergedAt, commits); without `gh`, without login or outside a repo — []."""
    if not shutil.which("gh") or not repo.is_dir():
        return []
    try:
        r = subprocess.run(["gh", "pr", "list", "--state", "merged", "--limit", "500", "--json",
                            "number,createdAt,mergedAt,commits"], cwd=repo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        data = json.loads(r.stdout) if r.returncode == 0 else []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _parse(ts: str) -> datetime | None:
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _usage(repo: Path) -> list[dict] | None:
    log = repo / ".tf" / "logs" / "usage.jsonl"
    if not log.exists():
        return None
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _window(commits: list[dict], start: datetime, end: datetime, reverts: dict, now: datetime, revert_days: int,
            usage: list[dict] | None, prices: dict, prs: list[dict] | None) -> dict:
    changes = [c for c in commits if start < c["ts"] <= end]
    limit = timedelta(days=revert_days)
    reverted = [c for c in changes if c["sha"] in reverts and reverts[c["sha"]] - c["ts"] <= limit]
    pending = [c for c in changes if c not in reverted and now - c["ts"] < limit]
    decided = len(changes) - len(pending)
    accepted = decided - len(reverted)
    causes: dict[str, int] = {}
    for c in changes:
        for v in CAUSE_RE.findall(c["body"]):
            v = v.lower() if v.lower() in CAUSES else "unknown"
            causes[v] = causes.get(v, 0) + 1
    cost = None
    if usage is not None:
        rc = _cost_module().record_cost
        cost = 0.0
        for u in usage:
            ts = _parse(u.get("ts") or "")
            if ts and start < ts <= end:
                cost += rc(u, prices) or 0.0
    w = {"from": start.isoformat(), "to": end.isoformat(), "changes": len(changes), "reverted": len(reverted),
         "pending": len(pending), "accepted": accepted,
         "revert_rate": (len(reverted) / decided) if decided else None,
         "rework_causes": causes, "cost_usd": cost,
         "cost_per_accepted": (cost / accepted) if cost is not None and accepted else None, "human_time": False,
         "prs": 0, "cycle_median_h": None, "commits_per_pr_median": None}
    if prs:
        mine = []
        for p in prs:
            created, merged = _parse(p.get("createdAt") or ""), _parse(p.get("mergedAt") or "")
            if created and merged and start < merged <= end:
                mine.append(((merged - created).total_seconds() / 3600, len(p.get("commits") or [])))
        if mine:
            w["prs"] = len(mine)
            w["cycle_median_h"] = round(statistics.median(h for h, _ in mine), 2)
            w["commits_per_pr_median"] = statistics.median(n for _, n in mine)
    return w


def _reverts(log: list[dict]) -> dict[str, datetime]:
    """change sha → time of the first commit that reverts it."""
    reverts: dict[str, datetime] = {}
    for c in log:
        if REVERT_SUBJECT.match(c["subject"]):
            for sha in REVERTS_SHA.findall(c["body"]):
                full = next((x["sha"] for x in log if x["sha"].startswith(sha)), sha)
                reverts[full] = min(reverts.get(full, c["ts"]), c["ts"])
    return reverts


BACKUP = Path(".tf") / "backup"
BLOCKS = Path(".tf") / "logs" / "hook-blocks.jsonl"
ERRORS = Path(".tf") / "logs" / "hook-errors.jsonl"
ROLLBACK = "python3 .tf/factory/update.py --rollback"
MIN_DECIDED, REVERT_RISE, MIN_BLOCKS, MIN_ERRORS = 5, 0.15, 5, 3


def last_update(repo: Path) -> tuple[datetime, str] | None:
    """Time of the last update and the version before it — from the name and marker of the newest copy in `.tf/backup/`."""
    best = None
    for d in (repo / BACKUP).glob("*/backup.json") if (repo / BACKUP).is_dir() else []:
        m = re.match(r"(\d{8}-\d{6})-v", d.parent.name)
        if not m:
            continue
        try:
            at = datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").astimezone()   # the copy name is in local time
            version = str(json.loads(d.read_text(encoding="utf-8")).get("version") or "?")
        except (ValueError, OSError, AttributeError):
            continue
        if best is None or at > best[0]:
            best = (at.astimezone(timezone.utc), version)
    return best


def _events(path: Path, start: datetime, end: datetime) -> int:
    """Log entries (field `ts` in seconds) in the window (start, end]."""
    n = 0
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0
    for line in lines:
        try:
            ts = datetime.fromtimestamp(float(json.loads(line).get("ts")), timezone.utc)
        except (ValueError, TypeError, AttributeError, OverflowError, OSError):
            continue
        n += start < ts <= end
    return n


def update_health(repo: Path, now: datetime | None = None, days: int = 14, revert_days: int = 7) -> dict:
    """Comparison of the window after the last factory update with a window of the same length before it (D13: warns only)."""
    now = now or datetime.now(timezone.utc)
    up = last_update(repo)
    if up is None:
        return {"update": None, "warnings": [], "notes": ["no pre-update backup in .tf/backup/ — nothing to compare with "
                                                          "(every factory update makes a backup)"]}
    at, old = up
    try:
        new = json.loads((repo / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("version") or "?"
    except (OSError, ValueError, AttributeError):
        new = "?"
    span = min(timedelta(days=days), max(now - at, timedelta(0)))
    log = git_log(repo)
    reverts = _reverts(log)
    commits = [c for c in log if not RELEASE.match(c["subject"]) and not REVERT_SUBJECT.match(c["subject"])]
    side = {}
    for name, (a, b) in (("before", (at - span, at)), ("after", (at, at + span))):
        w = _window(commits, a, b, reverts, now, revert_days, None, {}, None)
        side[name] = {"decided": w["changes"] - w["pending"], "reverted": w["reverted"], "revert_rate": w["revert_rate"],
                      "blocks": _events(repo / BLOCKS, a, b), "errors": _events(repo / ERRORS, a, b)}
    before, after = side["before"], side["after"]
    warnings, notes = [], []
    if before["decided"] >= MIN_DECIDED and after["decided"] >= MIN_DECIDED:
        if after["revert_rate"] - before["revert_rate"] >= REVERT_RISE - 1e-9:
            warnings.append(f"revert rate rose from {before['revert_rate']:.0%} to {after['revert_rate']:.0%}")
    else:
        notes.append(f"too few decided changes to compare reverts ({before['decided']} before, "
                     f"{after['decided']} after; need at least {MIN_DECIDED} in each window)")
    if after["blocks"] >= MIN_BLOCKS and after["blocks"] >= 2 * before["blocks"]:
        warnings.append(f"hook blocks: {before['blocks']} before, {after['blocks']} after")
    if after["errors"] >= MIN_ERRORS and after["errors"] > 2 * before["errors"]:
        warnings.append(f"hook errors: {before['errors']} before, {after['errors']} after")
    return {"update": at.isoformat(), "from": old, "to": new, "window_days": round(span.total_seconds() / 86400, 1),
            "before": before, "after": after, "warnings": warnings, "notes": notes,
            "rollback": ROLLBACK if warnings else None}


def health_text(res: dict) -> str:
    if not res.get("update"):
        return "• after the factory update: " + "; ".join(res.get("notes") or [])
    head = f"after the factory update {res['from']} → {res['to']} ({res['update'][:10]}, windows of {res['window_days']} days)"
    if res["warnings"]:
        return (f"⚠ {head}: {'; '.join(res['warnings'])}. If the update caused this, go back to the previous version: "
                f"{ROLLBACK} (pre-update backup). The factory does not roll back by itself — the decision is yours.")
    return f"✓ {head}: no regression" + (f" ({'; '.join(res['notes'])})" if res.get("notes") else "")


def compute(repo: Path, now: datetime | None = None, weeks: int = 4, revert_days: int = 7, prices: dict | None = None,
            prs: list[dict] | None = None) -> dict:
    """The current window (the last `weeks` weeks) and the base window (`weeks` weeks earlier)."""
    now = now or datetime.now(timezone.utc)
    log = git_log(repo)
    reverts = _reverts(log)
    commits = [c for c in log if not RELEASE.match(c["subject"]) and not REVERT_SUBJECT.match(c["subject"])]
    if prices is None:
        try:
            prices = _cost_module()._tf_config(repo).get("prices_usd_per_mtok") or {}
        except Exception:   # no project configuration — cost without a price list is zero, the report says where prices come from
            prices = {}
    usage = _usage(repo)
    span = timedelta(weeks=weeks)
    args = (reverts, now, revert_days, usage, prices, prs)
    return {"generated": now.isoformat(), "weeks": weeks, "revert_days": revert_days, "pr_history": bool(prs),
            "current": _window(commits, now - span, now, *args),
            "baseline": _window(commits, now - 2 * span, now - span, *args)}


def _fmt(v, kind: str) -> str:
    if v is None:
        return "—"
    if kind == "pct":
        return f"{v:.0%}"
    if kind == "usd":
        return f"${v:.2f}"
    if kind == "h":
        return f"{v:.1f} h"
    return str(v)


def write_report(repo: Path, res: dict) -> Path:
    out = repo / ".tf" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cur, base = res["current"], res["baseline"]
    rows = [("Changes (main line, without releases and reverts)", "changes", "n"),
            ("Accepted", "accepted", "n"), ("Reverted", "reverted", "n"), ("Pending (younger than the threshold)", "pending", "n"),
            ("Revert rate", "revert_rate", "pct"), ("Token cost (without human work)", "cost_usd", "usd"),
            ("Cost per accepted change (without human work)", "cost_per_accepted", "usd"),
            ("Merged PRs (PR history)", "prs", "n"), ("Median time from PR open to merge", "cycle_median_h", "h"),
            ("Median commits per PR", "commits_per_pr_median", "n")]
    lines = [f"# Factory metrics — {res['generated'][:10]}", "",
             f"Accepted change = merged and not reverted for {res['revert_days']} days (a new definition = a new series). "
             f"Current window: last {res['weeks']} weeks; baseline: {res['weeks']} weeks before that. Cost without human "
             f"work (human time is not measured). The number of changes is not a goal by itself.", "",
             "| Metric | Current | Baseline |", "|---|---|---|"]
    for label, key, kind in rows:
        lines.append(f"| {label} | {_fmt(cur.get(key), kind)} | {_fmt(base.get(key), kind)} |")
    causes = sorted(set(cur["rework_causes"]) | set(base["rework_causes"]))
    lines += ["", "## Rework causes (trailer `Rework-Cause:`)", ""]
    if causes:
        lines += ["| Cause | Current | Baseline |", "|---|---|---|"]
        lines += [f"| {c} | {cur['rework_causes'].get(c, 0)} | {base['rework_causes'].get(c, 0)} |" for c in causes]
    else:
        lines.append("No commits with `Rework-Cause:` — add the trailer to rework commits after review "
                     "(spec-gap, agent-error, requirement-change, unknown).")
    if not res["pr_history"]:
        lines += ["", "No PR history (`gh` not available or not logged in) — cycle time unknown."]
    if res.get("after_update"):
        lines += ["", "## After the last factory update", "", health_text(res["after_update"])]
    p = out / "metrics.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weeks", type=int, default=4, help="length of the current and the baseline window (weeks)")
    ap.add_argument("--revert-days", type=int, default=7, help="how many days a change must last without a revert")
    ap.add_argument("--no-gh", action="store_true", help="without PR history from gh")
    ap.add_argument("--after-update", action="store_true", help="compare before and after the last factory update")
    ap.add_argument("--json", action="store_true", help="with --after-update: result as JSON")
    args = ap.parse_args(argv)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    if args.after_update:
        res = update_health(root, revert_days=args.revert_days)
        print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else health_text(res))
        return 0
    if not (root / ".git").exists() and subprocess.run(["git", "-C", str(root), "rev-parse"], capture_output=True).returncode:
        print("✗ This is not a git repository.")
        return 2
    res = compute(root, weeks=args.weeks, revert_days=args.revert_days, prs=None if args.no_gh else pr_history(root))
    res["after_update"] = update_health(root, revert_days=args.revert_days)
    out = write_report(root, res)
    print(out.read_text(encoding="utf-8"))
    print(f"✓ Report: {out.relative_to(root)} (+ metrics.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
