#!/usr/bin/env python3
"""Metryki skuteczności fabryki (B3): czy zmiany robione z fabryką są przyjmowane, cofane i ile kosztują.

  python3 .tf/factory/metrics.py                    # ostatnie 4 tygodnie wobec 4 tygodni wcześniej
  python3 .tf/factory/metrics.py --weeks 2 --revert-days 14
  python3 .tf/factory/metrics.py --no-gh            # bez historii PR (tylko git)
  tf metrics [opcje]

Liczy z gita (główna linia, `--first-parent`, bez `chore(release)` i commitów revert):
- zmiany i przyjęte zmiany — przyjęta = zmergowana i niecofnięta przez N dni (`--revert-days`, domyślnie 7);
  zmiany młodsze niż N dni są „w toku” i nie wchodzą do odsetka;
- odsetek revertów — główny wskaźnik jakości;
- przyczyny poprawek z trailera `Rework-Cause:` (luka-specyfikacji, blad-agenta, zmiana-wymagan, nieznana);
- koszt tokenów z `.tf/logs/usage.jsonl` (cennik `prices_usd_per_mtok`) i koszt przyjętej zmiany — bez pracy ludzi;
- z historii PR (`gh pr list`, gdy jest): mediana czasu od otwarcia PR do merge'a i liczba commitów na PR.
Liczba zmian sama w sobie nie jest celem — łatwo ją zawyżyć. Raport: `.tf/reports/metrics.md` i `metrics.json`.
"""
from __future__ import annotations

import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
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
CAUSES = ("luka-specyfikacji", "blad-agenta", "zmiana-wymagan", "nieznana")
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
    """Commity głównej linii (najnowsze pierwsze): sha, czas, temat, treść."""
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
    """Zmergowane PR z `gh` (number, createdAt, mergedAt, commits); bez `gh`, bez logowania albo poza repo — []."""
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
            v = v.lower() if v.lower() in CAUSES else "nieznana"
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


def compute(repo: Path, now: datetime | None = None, weeks: int = 4, revert_days: int = 7, prices: dict | None = None,
            prs: list[dict] | None = None) -> dict:
    """Okno bieżące (ostatnie `weeks` tygodni) i bazowe (`weeks` tygodni wcześniej)."""
    now = now or datetime.now(timezone.utc)
    log = git_log(repo)
    reverts: dict[str, datetime] = {}
    for c in log:
        if REVERT_SUBJECT.match(c["subject"]):
            for sha in REVERTS_SHA.findall(c["body"]):
                full = next((x["sha"] for x in log if x["sha"].startswith(sha)), sha)
                reverts[full] = min(reverts.get(full, c["ts"]), c["ts"])
    commits = [c for c in log if not RELEASE.match(c["subject"]) and not REVERT_SUBJECT.match(c["subject"])]
    if prices is None:
        try:
            prices = _cost_module()._tf_config(repo).get("prices_usd_per_mtok") or {}
        except Exception:   # brak konfiguracji projektu — koszt bez cennika to zero, raport mówi, skąd ceny
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
    rows = [("Zmiany (główna linia, bez wydań i revertów)", "changes", "n"),
            ("Przyjęte", "accepted", "n"), ("Cofnięte", "reverted", "n"), ("W toku (młodsze niż próg)", "pending", "n"),
            ("Odsetek revertów", "revert_rate", "pct"), ("Koszt tokenów (bez pracy ludzi)", "cost_usd", "usd"),
            ("Koszt przyjętej zmiany (bez pracy ludzi)", "cost_per_accepted", "usd"),
            ("PR zmergowane (historia PR)", "prs", "n"), ("Mediana czasu od otwarcia PR do merge'a", "cycle_median_h", "h"),
            ("Mediana commitów na PR", "commits_per_pr_median", "n")]
    lines = [f"# Metryki fabryki — {res['generated'][:10]}", "",
             f"Przyjęta zmiana = zmergowana i niecofnięta przez {res['revert_days']} dni (zmiana definicji = nowa seria). "
             f"Okno bieżące: ostatnie {res['weeks']} tyg.; bazowe: {res['weeks']} tyg. wcześniej. Koszt bez pracy "
             f"ludzi (czas człowieka nie jest mierzony). Liczba zmian sama w sobie nie jest celem.", "",
             "| Metryka | Bieżące | Bazowe |", "|---|---|---|"]
    for label, key, kind in rows:
        lines.append(f"| {label} | {_fmt(cur.get(key), kind)} | {_fmt(base.get(key), kind)} |")
    causes = sorted(set(cur["rework_causes"]) | set(base["rework_causes"]))
    lines += ["", "## Przyczyny poprawek (trailer `Rework-Cause:`)", ""]
    if causes:
        lines += ["| Przyczyna | Bieżące | Bazowe |", "|---|---|---|"]
        lines += [f"| {c} | {cur['rework_causes'].get(c, 0)} | {base['rework_causes'].get(c, 0)} |" for c in causes]
    else:
        lines.append("Brak commitów z `Rework-Cause:` — dopisuj trailer w commitach poprawek po przeglądzie "
                     "(luka-specyfikacji, blad-agenta, zmiana-wymagan, nieznana).")
    if not res["pr_history"]:
        lines += ["", "Bez historii PR (`gh` niedostępne albo bez logowania) — czas cyklu nieznany."]
    p = out / "metrics.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weeks", type=int, default=4, help="długość okna bieżącego i bazowego (tygodnie)")
    ap.add_argument("--revert-days", type=int, default=7, help="ile dni zmiana musi przetrwać bez revertu")
    ap.add_argument("--no-gh", action="store_true", help="bez historii PR z gh")
    args = ap.parse_args(argv)
    root = Path.cwd()
    if not (root / ".git").exists() and subprocess.run(["git", "-C", str(root), "rev-parse"], capture_output=True).returncode:
        print("✗ To nie jest repozytorium git.")
        return 2
    res = compute(root, weeks=args.weeks, revert_days=args.revert_days, prs=None if args.no_gh else pr_history(root))
    out = write_report(root, res)
    print(out.read_text(encoding="utf-8"))
    print(f"✓ Raport: {out.relative_to(root)} (+ metrics.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
