#!/usr/bin/env python3
"""
Terytorium kodu z historii gita — co się zmienia, co zmienia się razem, kto zmieniał, gdzie są hotspoty.

  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py                    # 12 mies., top 10
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --all --depth 3     # wszystkie sekcje
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --cochange --max-files 30 --json
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --authors src/billing
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --top 20
  python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --bus-factor --since 24.months

Sekcje:
- zawsze: ranking katalogów (na głębokości --depth) i plików wg liczby commitów; pliki, których już nie ma
  w `git ls-files`, oznaczone jako usunięte (historia mówi o przeszłości);
- --by-quarter: ranking katalogów per kwartał (stałe centrum vs kampania zmian);
- --cochange: pary katalogów i plików zmieniane w tych samych commitach (commity > --max-files plików pominięte,
  bo masowy refaktor skleja niezwiązane pliki) oraz huby — pliki zmieniane razem z wieloma obszarami;
- --authors <ścieżka>: kontrybutorzy obszaru bez botów i bez commitów, których autorem jest agent AI
  (commit człowieka z trailerem Co-Authored-By agenta zostaje); wypisuje tylko nazwę autora, bez e-maili;
- --hotspots: zmiany × linie niepuste (proxy złożoności) dla bieżących plików, plus maks. głębokość wcięć;
- --bus-factor: ryzyko „jednej osoby” per katalog (głębokość --depth, obszary z ≥ --min-commits commitami ludzi):
  bus factor = najmniej osób, które razem mają ponad 50% commitów obszaru; aktywni = osoby z commitem w obszarze
  w ostatnich --active-days dniach przed datą HEAD. Ryzyko: krytyczne (nikt aktywny), wysokie (bus factor 1),
  umiarkowane (2), niskie (≥ 3). Bez botów i agentów AI, tylko nazwy autorów; nie wchodzi do --all.
Szum odfiltrowany domyślnie: lockfile'e, snapshoty, dist/build, pliki generowane i zminifikowane, tłumaczenia,
.env*. Własne wzorce: --exclude <regex> (wiele razy). Commity botów (dependabot, renovate, github-actions, „[bot]”)
nie wchodzą do żadnej sekcji; commity agentów AI wchodzą do terytorium, ale nie do listy kontrybutorów.

Kod wyjścia: 0 — wynik wypisany; 2 — katalog nie jest repozytorium git, błąd gita lub złe argumenty.
Tylko odczyt historii (`git log`, `git ls-files`, `git rev-parse`); biblioteka standardowa, bez sieci.
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
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: kod {r.returncode}")
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


RISK_ORDER = {"krytyczne": 0, "wysokie": 1, "umiarkowane": 2, "niskie": 3}


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
        risk = "krytyczne" if not active else "wysokie" if bf == 1 else "umiarkowane" if bf == 2 else "niskie"
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
    out = [f"# Terytorium: {r['repo']}", "",
           f"HEAD {r['head']} ({r['head_date'][:10]}) · okno: od {r['since']} · commity: {r['commits']} "
           f"(pominięte boty: {r['skipped_bot_commits']}) · głębokość katalogów: {r['depth']}", "", "## Katalogi"]
    out += table(["katalog", "commity"], [[f"`{d['path']}`", d["commits"]] for d in r["dirs"]])
    out += ["", "## Pliki"]
    out += table(["plik", "commity", "istnieje"], [[f"`{f['path']}`", f["commits"], "tak" if f["alive"] else "USUNIĘTY"]
                                                    for f in r["files"]])
    if "quarters" in r:
        out += ["", "## Kwartały"]
        for q, rows in r["quarters"].items():
            out.append(f"- {q}: " + ", ".join(f"`{x['path']}` ({x['commits']})" for x in rows[:5]))
    if "cochange" in r:
        co = r["cochange"]
        out += ["", f"## Współzmiany (pominięte commity > {co['max_files']} plików: {co['skipped_large_commits']})",
                "", "Pary katalogów:"]
        out += table(["A", "B", "commity"], [[f"`{p['a']}`", f"`{p['b']}`", p["commits"]] for p in co["dir_pairs"]])
        out += ["", "Pary plików (udział = wspólne / zmiany rzadszego pliku; ≥ 0,8 → ciasna para, ukryta umowa):"]
        out += table(["A", "B", "commity", "udział"], [[f"`{p['a']}`", f"`{p['b']}`", p["commits"], p["share"]]
                                                        for p in co["file_pairs"]])
        out += ["", "Huby (zmieniane razem z wieloma obszarami):"]
        out += table(["plik", "obszary"], [[f"`{h['path']}`", h["areas"]] for h in co["hubs"]])
    if "authors" in r:
        out += ["", f"## Kontrybutorzy `{r['authors_path']}` (bez botów i agentów; kogo zapytać, nie właściciele)"]
        out += table(["autor", "commity", "ostatnio"], [[x["name"], x["commits"], x["last"]] for x in r["authors"]])
    if "bus_factor" in r:
        bf = r["bus_factor"]
        out += ["", f"## Bus factor (obszary z ≥ {bf['min_commits']} commitami ludzi; aktywni: commit w ostatnich "
                    f"{bf['active_days']} dniach przed HEAD; bus factor = najmniej osób z > 50% commitów)"]
        out += table(["obszar", "commity", "osoby", "bus factor", "główny autor", "udział", "aktywni", "ryzyko"],
                     [[f"`{x['path']}`", x["commits"], x["people"], x["bus_factor"], x["top_author"], x["top_share"],
                       x["active"], x["risk"]] for x in bf["areas"]])
    if "hotspots" in r:
        out += ["", "## Hotspoty (zmiany × linie niepuste)"]
        out += table(["plik", "commity", "linie", "maks. wcięcie", "wynik"],
                     [[f"`{h['path']}`", h["commits"], h["nloc"], h["max_indent"], h["score"]] for h in r["hotspots"]])
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Terytorium kodu z historii gita (tylko odczyt). Kod wyjścia: 0 wynik, "
                                             "2 brak repozytorium git / błąd gita / złe argumenty.")
    ap.add_argument("--repo", default=".", help="katalog repozytorium (domyślnie bieżący)")
    ap.add_argument("--since", default="12.months", help="okno historii dla git log --since (domyślnie 12.months)")
    ap.add_argument("--top", type=int, default=10, help="liczba pozycji w rankingach (domyślnie 10)")
    ap.add_argument("--depth", type=int, default=2, help="głębokość katalogów w rankingu (domyślnie 2)")
    ap.add_argument("--exclude", action="append", default=[], help="dodatkowy regex szumu (wiele razy)")
    ap.add_argument("--by-quarter", action="store_true", help="ranking katalogów per kwartał")
    ap.add_argument("--cochange", action="store_true", help="pary współzmian i huby")
    ap.add_argument("--max-files", type=int, default=30, help="pomijaj commity z większą liczbą plików przy współzmianach")
    ap.add_argument("--authors", metavar="ŚCIEŻKA", help="kontrybutorzy obszaru (bez botów i agentów AI)")
    ap.add_argument("--hotspots", action="store_true", help="hotspoty: zmiany × linie niepuste")
    ap.add_argument("--bus-factor", action="store_true", help="ryzyko jednej osoby per katalog (bez botów i agentów AI)")
    ap.add_argument("--min-commits", type=int, default=5, help="z --bus-factor: minimum commitów ludzi w obszarze (domyślnie 5)")
    ap.add_argument("--active-days", type=int, default=90, help="z --bus-factor: okno aktywności przed datą HEAD (domyślnie 90)")
    ap.add_argument("--all", action="store_true", help="wszystkie sekcje poza --authors i --bus-factor")
    ap.add_argument("--json", action="store_true", help="wynik w JSON")
    a = ap.parse_args(argv)
    try:
        res = analyse(a)
    except (RuntimeError, OSError, re.error) as e:
        print(f"błąd: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else to_text(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
