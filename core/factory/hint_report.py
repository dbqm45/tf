#!/usr/bin/env python3
"""
Effectiveness report of skill hints (the skill_hint hook) on real work in a project.

  python3 .tf/factory/hint_report.py               # all sessions from the logs
  python3 .tf/factory/hint_report.py --days 7      # the last 7 days

Combines two logs from .tf/logs/:
- skill-hints.jsonl (the skill_hint hook): what was suggested at each command,
- usage.jsonl (the log_usage hook): which skills the session actually loaded (main thread and executors).

Result per skill:
- hit: suggested and used in the same session,
- ignored: suggested but unused in the session (noise, or the model judged it unnecessary),
- missed: used but never suggested in the session (a candidate for `metadata.keywords` in SKILL.md).
The comparison is at the session level, not of a single command — it is an approximation. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / ".tf" / "logs"


def read_jsonl(path: Path, since: datetime | None) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since and r.get("ts"):
            try:
                if datetime.fromisoformat(r["ts"]) < since:
                    continue
            except ValueError:
                pass
        out.append(r)
    return out


def analyse(hints: list[dict], usage: list[dict]) -> dict:
    hinted: dict[str, set] = defaultdict(set)
    prompts: Counter = Counter()
    with_hint: Counter = Counter()
    for h in hints:
        s = h.get("session") or "?"
        prompts[s] += 1
        if h.get("hinted"):
            with_hint[s] += 1
        hinted[s].update(h.get("hinted") or [])
    used: dict[str, set] = defaultdict(set)
    for u in usage:
        used[u.get("session") or "?"].update(u.get("skills") or [])
    sessions = set(prompts) & set(used) if used else set(prompts)
    hit, ignored, missed = Counter(), Counter(), Counter()
    for s in sessions:
        for sk in hinted[s] & used[s]:
            hit[sk] += 1
        for sk in hinted[s] - used[s]:
            ignored[sk] += 1
        for sk in used[s] - hinted[s]:
            missed[sk] += 1
    return {"sessions": len(sessions), "prompts": sum(prompts[s] for s in sessions),
            "prompts_with_hint": sum(with_hint[s] for s in sessions), "hit": hit, "ignored": ignored, "missed": missed}


def render(r: dict) -> str:
    lines = [f"Sessions: {r['sessions']} · prompts: {r['prompts']} · with a hint: {r['prompts_with_hint']}"]
    if not r["sessions"]:
        lines.append("No data: logs .tf/logs/skill-hints.jsonl and usage.jsonl from the same sessions are needed.")
        return "\n".join(lines)
    total_hit, total_ign, total_miss = sum(r["hit"].values()), sum(r["ignored"].values()), sum(r["missed"].values())
    lines.append(f"Hints hit: {total_hit} · ignored: {total_ign} · skills used without a hint: {total_miss}")
    names = sorted(set(r["hit"]) | set(r["ignored"]) | set(r["missed"]),
                   key=lambda n: -(r["missed"][n] + r["ignored"][n]))
    lines += ["", f"{'skill':<36} {'hit':>8} {'ignored':>8} {'missed':>8}"]
    lines += [f"{n:<36} {r['hit'][n]:>8} {r['ignored'][n]:>8} {r['missed'][n]:>8}" for n in names]
    tips = []
    for n in names:
        if r["missed"][n] >= 2:
            tips.append(f"- {n}: used without a hint in {r['missed'][n]} sessions — add the users' words to "
                        f"metadata.keywords (with CLAUDE_SKILL_HINT_LOG_PROMPT=1 you see the wording of prompts)")
        if r["ignored"][n] >= 3 and r["hit"][n] == 0:
            tips.append(f"- {n}: hinted {r['ignored'][n]}× and never used — check that the description does not catch "
                        f"other skills' words (python3 .claude/hooks/skill_hint.py --explain \"<prompt>\")")
    if tips:
        lines += ["", "What to fix:"] + tips
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--logs", default=str(LOGS))
    a = ap.parse_args(argv[1:])
    since = datetime.now(timezone.utc) - timedelta(days=a.days) if a.days else None
    logs = Path(a.logs)
    r = analyse(read_jsonl(logs / "skill-hints.jsonl", since), read_jsonl(logs / "usage.jsonl", since))
    print(render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
