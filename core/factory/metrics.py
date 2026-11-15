#!/usr/bin/env python3
"""Metryki skuteczności fabryki (B3): czy zmiany robione z fabryką są przyjmowane, cofane i ile kosztują.

  python3 .tf/factory/metrics.py                    # ostatnie 4 tygodnie wobec 4 tygodni wcześniej
  python3 .tf/factory/metrics.py --weeks 2 --revert-days 14
  python3 .tf/factory/metrics.py --no-gh            # bez historii PR (tylko git)
  tf metrics [opcje]
  python3 .tf/factory/metrics.py --after-update [--json]   # czy po ostatniej aktualizacji fabryki coś się pogorszyło

Liczy z gita (główna linia, `--first-parent`, bez `chore(release)` i commitów revert):
- zmiany i przyjęte zmiany — przyjęta = zmergowana i niecofnięta przez N dni (`--revert-days`, domyślnie 7);
  zmiany młodsze niż N dni są „w toku” i nie wchodzą do odsetka;
- odsetek revertów — główny wskaźnik jakości;
- przyczyny poprawek z trailera `Rework-Cause:` (luka-specyfikacji, blad-agenta, zmiana-wymagan, nieznana);
- koszt tokenów z `.tf/logs/usage.jsonl` (cennik `prices_usd_per_mtok`) i koszt przyjętej zmiany — bez pracy ludzi;
- z historii PR (`gh pr list`, gdy jest): mediana czasu od otwarcia PR do merge'a i liczba commitów na PR.
Liczba zmian sama w sobie nie jest celem — łatwo ją zawyżyć. Raport: `.tf/reports/metrics.md` i `metrics.json`.

`--after-update` (krok H29, decyzja D13): ostatnia kopia w `.tf/backup/` wyznacza chwilę aktualizacji fabryki
i wersję sprzed niej. Okno po aktualizacji (do 14 dni) jest porównane z oknem tej samej długości przed nią:
odsetek cofnięć (ostrzeżenie przy wzroście o ≥ 15 punktów, gdy w obu oknach jest ≥ 5 rozstrzygniętych zmian),
blokady hooków z `.tf/logs/hook-blocks.jsonl` (≥ 5 po i co najmniej dwukrotny wzrost) i błędy hooków z
`.tf/logs/hook-errors.jsonl` (≥ 3 po i ponad dwukrotny wzrost). Ostrzeżenie podaje polecenie powrotu
(`update.py --rollback`); fabryka sama się nie cofa — przy małej liczbie zmian ten wskaźnik jest zaszumiony.
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


def _reverts(log: list[dict]) -> dict[str, datetime]:
    """sha zmiany → czas pierwszego commita, który ją cofa."""
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
    """Chwila ostatniej aktualizacji i wersja sprzed niej — z nazwy i znacznika najnowszej kopii w `.tf/backup/`."""
    best = None
    for d in (repo / BACKUP).glob("*/backup.json") if (repo / BACKUP).is_dir() else []:
        m = re.match(r"(\d{8}-\d{6})-v", d.parent.name)
        if not m:
            continue
        try:
            at = datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").astimezone()   # nazwa kopii w czasie lokalnym
            version = str(json.loads(d.read_text(encoding="utf-8")).get("version") or "?")
        except (ValueError, OSError, AttributeError):
            continue
        if best is None or at > best[0]:
            best = (at.astimezone(timezone.utc), version)
    return best


def _events(path: Path, start: datetime, end: datetime) -> int:
    """Wpisy dziennika (pole `ts` w sekundach) w oknie (start, end]."""
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
    """Porównanie okna po ostatniej aktualizacji fabryki z oknem tej samej długości przed nią (D13: tylko ostrzega)."""
    now = now or datetime.now(timezone.utc)
    up = last_update(repo)
    if up is None:
        return {"update": None, "warnings": [], "notes": ["brak kopii sprzed aktualizacji w .tf/backup/ — nie ma z czym "
                                                          "porównać (kopię robi każda aktualizacja fabryki)"]}
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
            warnings.append(f"odsetek cofniętych zmian wzrósł z {before['revert_rate']:.0%} do {after['revert_rate']:.0%}")
    else:
        notes.append(f"za mało rozstrzygniętych zmian do porównania cofnięć ({before['decided']} przed, "
                     f"{after['decided']} po; potrzeba co najmniej {MIN_DECIDED} w każdym oknie)")
    if after["blocks"] >= MIN_BLOCKS and after["blocks"] >= 2 * before["blocks"]:
        warnings.append(f"blokad hooków było {before['blocks']} przed i {after['blocks']} po")
    if after["errors"] >= MIN_ERRORS and after["errors"] > 2 * before["errors"]:
        warnings.append(f"błędów hooków było {before['errors']} przed i {after['errors']} po")
    return {"update": at.isoformat(), "from": old, "to": new, "window_days": round(span.total_seconds() / 86400, 1),
            "before": before, "after": after, "warnings": warnings, "notes": notes,
            "rollback": ROLLBACK if warnings else None}


def health_text(res: dict) -> str:
    if not res.get("update"):
        return "• po aktualizacji fabryki: " + "; ".join(res.get("notes") or [])
    head = f"po aktualizacji fabryki {res['from']} → {res['to']} ({res['update'][:10]}, okna po {res['window_days']} dni)"
    if res["warnings"]:
        return (f"⚠ {head}: {'; '.join(res['warnings'])}. Jeśli to skutek aktualizacji, wróć do poprzedniej wersji: "
                f"{ROLLBACK} (kopia sprzed aktualizacji). Fabryka sama się nie cofa — decyzja należy do Ciebie.")
    return f"✓ {head}: bez pogorszenia" + (f" ({'; '.join(res['notes'])})" if res.get("notes") else "")


def compute(repo: Path, now: datetime | None = None, weeks: int = 4, revert_days: int = 7, prices: dict | None = None,
            prs: list[dict] | None = None) -> dict:
    """Okno bieżące (ostatnie `weeks` tygodni) i bazowe (`weeks` tygodni wcześniej)."""
    now = now or datetime.now(timezone.utc)
    log = git_log(repo)
    reverts = _reverts(log)
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
    if res.get("after_update"):
        lines += ["", "## Po ostatniej aktualizacji fabryki", "", health_text(res["after_update"])]
    p = out / "metrics.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weeks", type=int, default=4, help="długość okna bieżącego i bazowego (tygodnie)")
    ap.add_argument("--revert-days", type=int, default=7, help="ile dni zmiana musi przetrwać bez revertu")
    ap.add_argument("--no-gh", action="store_true", help="bez historii PR z gh")
    ap.add_argument("--after-update", action="store_true", help="porównanie przed i po ostatniej aktualizacji fabryki")
    ap.add_argument("--json", action="store_true", help="z --after-update: wynik jako JSON")
    args = ap.parse_args(argv)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    if args.after_update:
        res = update_health(root, revert_days=args.revert_days)
        print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else health_text(res))
        return 0
    if not (root / ".git").exists() and subprocess.run(["git", "-C", str(root), "rev-parse"], capture_output=True).returncode:
        print("✗ To nie jest repozytorium git.")
        return 2
    res = compute(root, weeks=args.weeks, revert_days=args.revert_days, prs=None if args.no_gh else pr_history(root))
    res["after_update"] = update_health(root, revert_days=args.revert_days)
    out = write_report(root, res)
    print(out.read_text(encoding="utf-8"))
    print(f"✓ Raport: {out.relative_to(root)} (+ metrics.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
