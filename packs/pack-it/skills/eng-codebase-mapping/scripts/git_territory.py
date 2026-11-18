#!/usr/bin/env python3
"""
Code territory from git history — what changes, what changes together, who changed it, where the hotspots are.

  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py                    # 12 months, top 10
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --all --depth 3     # all sections
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --cochange --max-files 30 --json
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --authors src/billing
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --top 20
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --bus-factor --since 24.months

Sections:
- always: a ranking of directories (at --depth) and files by commit count; files no longer in `git ls-files`
  are marked as removed (history speaks of the past);
- --by-quarter: a ranking of directories per quarter (a steady core vs a campaign of changes);
- --cochange: pairs of directories and files changed in the same commits (commits > --max-files files are skipped,
  because a mass refactor glues unrelated files together) and hubs — files changed together with many areas;
- --authors <path>: contributors of an area without bots and without commits authored by an AI agent
  (a human commit with an agent's Co-Authored-By trailer stays); prints only the author name, no e-mails;
- --hotspots: changes × non-blank lines (a complexity proxy) for current files, plus max. indentation depth;
- --bus-factor: "single person" risk per directory (at --depth, areas with ≥ --min-commits human commits):
  bus factor = the fewest people who together hold over 50% of the area's commits; active = people with a commit in the
  area in the last --active-days days before the HEAD date. Risk: critical (nobody active), high (bus factor 1),
  moderate (2), low (≥ 3). Without bots and AI agents, author names only; not part of --all.
Noise filtered by default: lockfiles, snapshots, dist/build, generated and minified files, translations,
.env*. Custom patterns: --exclude <regex> (repeatable). Bot commits (dependabot, renovate, github-actions, "[bot]")
enter no section; AI agent commits enter the territory but not the contributor list.

Exit code: 0 — result printed; 2 — the directory is not a git repository, a git error or bad arguments.
History is read only (`git log`, `git ls-files`, `git rev-parse`); standard library, no network.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

NOISE = re.compile(
    r"(^|/)(package-lock\.json|npm-shrinkwrap\.json|yarn\.lock|pnpm-lock\.yaml|bun\.lockb?|poetry\.lock|uv\.lock|"
    r"Pipfile\.lock|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock|pubspec\.lock|gradle\.lockfile|packages\.lock\.json)$"
    r"|\.lock$|(^|/)__snapshots__/|\.snap$|(^|/)(dist|build|out|coverage|\.next)/|\.generated\.|\.g\.(dart|cs)$"
    r"|\.min\.(js|css)$|(^|/)(locales?|i18n|translations)/|(^|/)\.env")
BOT = re.compile(r"\[bot\]|^(dependabot|renovate|github-actions|greenkeeper|snyk-bot|mergify|pre-commit-ci|"
                 r"semantic-release-bot|imgbot|allcontributors)\b", re.I)
AGENT = re.compile(r"^(claude|copilot|devin|codex|cursor\s*agent|sweep|aider)\b|noreply@anthropic\.com|"
                   r"copilot-swe-agent", re.I)
REC, FLD, END = "\x1e", "\x1f", "\x1d"


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.quotepath=off", "-C", str(repo), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: exit code {r.returncode}")
    return r.stdout


def load_commits(repo: Path, since: str, extra_noise: list[re.Pattern]) -> tuple[list[dict], int]:
    out = git(repo, "log", f"--since={since}", "--no-merges", "--name-only",
              f"--format={REC}%H{FLD}%an{FLD}%ae{FLD}%aI{FLD}%B{END}")
    commits, bots = [], 0
    for chunk in out.split(REC)[1:]:
        head, _, names = chunk.partition(END)
        sha, name, email, date, _body = (head.split(FLD) + [""] * 5)[:5]
        if BOT.search(name) or BOT.search(email.split("@")[0]):
            bots += 1
            continue
        files = [f.strip() for f in names.splitlines() if f.strip()]
        files = [f for f in files if not NOISE.search(f) and not any(p.search(f) for p in extra_noise)]
        if not files:
            continue
        commits.append({"sha": sha, "name": name, "email": email, "date": date, "files": files,
                        "agent": bool(AGENT.search(name) or AGENT.search(email))})
    return commits, bots


def dir_of(path: str, depth: int) -> str:
    parts = path.split("/")[:-1]
    return "/".join(parts[:depth]) if parts else "."


def quarter(iso: str) -> str:
    y, m = int(iso[:4]), int(iso[5:7])
    return f"{y}-Q{(m - 1) // 3 + 1}"


def rank_dirs(commits: list[dict], depth: int) -> Counter:
    c = Counter()
    for cm in commits:
        for d in {dir_of(f, depth) for f in cm["files"]}:
            c[d] += 1
    return c


def complexity(path: Path) -> tuple[int, int] | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    lines = [ln for ln in raw.decode("utf-8", "replace").splitlines() if ln.strip()]
    depth = 0
    for ln in lines:
        stripped = ln.expandtabs(4)
        depth = max(depth, (len(stripped) - len(stripped.lstrip(" "))) // 4)
    return len(lines), depth


RISK_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


def bus_factor(commits: list[dict], depth: int, min_commits: int, active_days: int, head_date: str) -> list[dict]:
    since_active = datetime.fromisoformat(head_date) - timedelta(days=active_days)
    areas = defaultdict(lambda: defaultdict(lambda: {"commits": 0, "last": None}))
    for cm in commits:
        if cm["agent"]:
            continue
        when = datetime.fromisoformat(cm["date"])
        for d in {dir_of(f, depth) for f in cm["files"]}:
            p = areas[d][cm["name"]]
            p["commits"] += 1
            p["last"] = max(p["last"] or when, when)
    out = []
    for d, people in areas.items():
        total = sum(p["commits"] for p in people.values())
        if total < min_commits:
            continue
        ranked = sorted(people.items(), key=lambda kv: (-kv[1]["commits"], kv[0]))
        covered, bf = 0, 0
        for _, p in ranked:
            covered += p["commits"]
            bf += 1
            if covered * 2 > total:
                break
        active = sum(p["last"] >= since_active for p in people.values())
        risk = "critical" if not active else "high" if bf == 1 else "moderate" if bf == 2 else "low"
        out.append({"path": d, "commits": total, "people": len(people), "bus_factor": bf, "top_author": ranked[0][0],
                    "top_share": round(ranked[0][1]["commits"] / total, 2), "active": active, "risk": risk})
    return sorted(out, key=lambda x: (RISK_ORDER[x["risk"]], -x["commits"], x["path"]))


def analyse(a) -> dict:
    repo = Path(a.repo).resolve()
    extra = [re.compile(x) for x in a.exclude]
    head = git(repo, "rev-parse", "--short", "HEAD").strip()
    head_date = git(repo, "log", "-1", "--format=%cI").strip()
    commits, bots = load_commits(repo, a.since, extra)
    alive = set(git(repo, "ls-files").splitlines())
    file_c = Counter(f for cm in commits for f in set(cm["files"]))
    dirs = rank_dirs(commits, a.depth)
    res = {
        "repo": str(repo), "head": head, "head_date": head_date, "since": a.since, "depth": a.depth,
        "commits": len(commits), "skipped_bot_commits": bots,
        "dirs": [{"path": d, "commits": n} for d, n in dirs.most_common(a.top)],
        "files": [{"path": f, "commits": n, "alive": f in alive} for f, n in file_c.most_common(a.top)],
    }
    if a.by_quarter or a.all:
        byq = defaultdict(list)
        for cm in commits:
            byq[quarter(cm["date"])].append(cm)
        res["quarters"] = {q: [{"path": d, "commits": n} for d, n in rank_dirs(cs, a.depth).most_common(a.top)]
                           for q, cs in sorted(byq.items())}
    if a.cochange or a.all:
        dpairs, fpairs, partners, skipped = Counter(), Counter(), defaultdict(set), 0
        for cm in commits:
            files = sorted(set(cm["files"]))
            if len(files) > a.max_files:
                skipped += 1
                continue
            ds = sorted({dir_of(f, a.depth) for f in files})
            dpairs.update(combinations(ds, 2))
            fpairs.update(combinations(files, 2))
            for f in files:
                partners[f].update(d for d in ds if d != dir_of(f, a.depth))
        res["cochange"] = {
            "max_files": a.max_files, "skipped_large_commits": skipped,
            "dir_pairs": [{"a": x, "b": y, "commits": n} for (x, y), n in dpairs.most_common(a.top)],
            "file_pairs": [{"a": x, "b": y, "commits": n,
                            "share": round(n / min(file_c[x], file_c[y]), 2)}   # n / rzadziej zmieniany plik pary
                           for (x, y), n in fpairs.most_common() if n >= 2][:a.top],
            "hubs": [{"path": f, "areas": len(p), "alive": f in alive}
                     for f, p in sorted(partners.items(), key=lambda kv: (-len(kv[1]), kv[0])) if len(p) >= 1][:a.top],
        }
    if a.authors:
        prefix = a.authors.rstrip("/") + "/"
        people = defaultdict(lambda: {"commits": 0, "last": ""})
        for cm in commits:
            if cm["agent"] or not any(f == a.authors or f.startswith(prefix) for f in cm["files"]):
                continue
            p = people[cm["name"]]
            p["commits"] += 1
            p["last"] = max(p["last"], cm["date"][:10])
        res["authors_path"] = a.authors
        res["authors"] = [{"name": n, **v} for n, v in sorted(people.items(), key=lambda kv: (-kv[1]["commits"], kv[0]))]
    if a.bus_factor:
        res["bus_factor"] = {"min_commits": a.min_commits, "active_days": a.active_days,
                             "areas": bus_factor(commits, a.depth, a.min_commits, a.active_days, head_date)[:a.top]}
    if a.hotspots or a.all:
        hot = []
        for f, n in file_c.items():
            if f not in alive:
                continue
            cx = complexity(repo / f)
            if cx and cx[0]:
                hot.append({"path": f, "commits": n, "nloc": cx[0], "max_indent": cx[1], "score": n * cx[0]})
        res["hotspots"] = sorted(hot, key=lambda h: (-h["score"], h["path"]))[:a.top]
    return res


def table(head: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows] or ["| " + " | ".join("—" for _ in head) + " |"]
    return out


def to_text(r: dict) -> str:
    out = [f"# Territory: {r['repo']}", "",
           f"HEAD {r['head']} ({r['head_date'][:10]}) · window: since {r['since']} · commits: {r['commits']} "
           f"(skipped bots: {r['skipped_bot_commits']}) · directory depth: {r['depth']}", "", "## Directories"]
    out += table(["directory", "commits"], [[f"`{d['path']}`", d["commits"]] for d in r["dirs"]])
    out += ["", "## Files"]
    out += table(["file", "commits", "exists"], [[f"`{f['path']}`", f["commits"], "yes" if f["alive"] else "DELETED"]
                                                    for f in r["files"]])
    if "quarters" in r:
        out += ["", "## Quarters"]
        for q, rows in r["quarters"].items():
            out.append(f"- {q}: " + ", ".join(f"`{x['path']}` ({x['commits']})" for x in rows[:5]))
    if "cochange" in r:
        co = r["cochange"]
        out += ["", f"## Co-changes (skipped commits > {co['max_files']} files: {co['skipped_large_commits']})",
                "", "Directory pairs:"]
        out += table(["A", "B", "commits"], [[f"`{p['a']}`", f"`{p['b']}`", p["commits"]] for p in co["dir_pairs"]])
        out += ["", "File pairs (share = shared / changes of the less changed file; ≥ 0.8 → tight pair, hidden contract):"]
        out += table(["A", "B", "commits", "share"], [[f"`{p['a']}`", f"`{p['b']}`", p["commits"], p["share"]]
                                                        for p in co["file_pairs"]])
        out += ["", "Hubs (changed together with many areas):"]
        out += table(["file", "areas"], [[f"`{h['path']}`", h["areas"]] for h in co["hubs"]])
    if "authors" in r:
        out += ["", f"## Contributors `{r['authors_path']}` (no bots or agents; who to ask, not owners)"]
        out += table(["author", "commits", "last"], [[x["name"], x["commits"], x["last"]] for x in r["authors"]])
    if "bus_factor" in r:
        bf = r["bus_factor"]
        out += ["", f"## Bus factor (areas with ≥ {bf['min_commits']} human commits; active: a commit in the last "
                    f"{bf['active_days']} days before HEAD; bus factor = fewest people with > 50% of commits)"]
        out += table(["area", "commits", "people", "bus factor", "top author", "share", "active", "risk"],
                     [[f"`{x['path']}`", x["commits"], x["people"], x["bus_factor"], x["top_author"], x["top_share"],
                       x["active"], x["risk"]] for x in bf["areas"]])
    if "hotspots" in r:
        out += ["", "## Hotspots (changes × non-blank lines)"]
        out += table(["file", "commits", "lines", "max indent", "score"],
                     [[f"`{h['path']}`", h["commits"], h["nloc"], h["max_indent"], h["score"]] for h in r["hotspots"]])
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Code territory from git history (read only). Exit code: 0 result, "
                                             "2 no git repository / git error / bad arguments.")
    ap.add_argument("--repo", default=".", help="repository directory (default: current)")
    ap.add_argument("--since", default="12.months", help="history window for git log --since (default 12.months)")
    ap.add_argument("--top", type=int, default=10, help="number of items in rankings (default 10)")
    ap.add_argument("--depth", type=int, default=2, help="directory depth in the ranking (default 2)")
    ap.add_argument("--exclude", action="append", default=[], help="extra noise regex (repeatable)")
    ap.add_argument("--by-quarter", action="store_true", help="directory ranking per quarter")
    ap.add_argument("--cochange", action="store_true", help="co-change pairs and hubs")
    ap.add_argument("--max-files", type=int, default=30, help="skip commits with more files than this in co-changes")
    ap.add_argument("--authors", metavar="PATH", help="contributors of an area (no bots or AI agents)")
    ap.add_argument("--hotspots", action="store_true", help="hotspots: changes × non-blank lines")
    ap.add_argument("--bus-factor", action="store_true", help="single-person risk per directory (no bots or AI agents)")
    ap.add_argument("--min-commits", type=int, default=5, help="with --bus-factor: minimum human commits in an area (default 5)")
    ap.add_argument("--active-days", type=int, default=90, help="with --bus-factor: activity window before the HEAD date (default 90)")
    ap.add_argument("--all", action="store_true", help="all sections except --authors and --bus-factor")
    ap.add_argument("--json", action="store_true", help="output as JSON")
    a = ap.parse_args(argv)
    try:
        res = analyse(a)
    except (RuntimeError, OSError, re.error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else to_text(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
