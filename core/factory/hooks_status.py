#!/usr/bin/env python3
"""
Czy hooki fabryki działały przy ostatnich commitach — porównanie śladów hooków w .claude/logs z historią git.

  python3 factory/hooks_status.py              # jedna linia: aktywne / nieaktywne / brak hooków
  python3 factory/hooks_status.py --json       # {"active": true|false|null, "last_log", "after_commits", "first_after"}
  --root <repozytorium>

Ślady hooków: wpisy `ts` w .claude/logs/skill-hints.jsonl (każde polecenie) i usage.jsonl (koniec sesji). Commit
później niż godzinę po ostatnim śladzie nie ma pokrycia w logach; od dwóch takich commitów hooki uznajemy za nieaktywne
(jeden to zwykle bieżąca sesja przed zapisem). Typowa przyczyna: sesja w chmurze z kilkoma repozytoriami albo sesja
uruchomiona z katalogu nadrzędnego — hooki z .claude/settings.json się nie wczytują, więc nie działają tdd_guard,
ochrona ścieżek ani logi kosztów. Wynik jest informacją (kod 0), nie błędem. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ("skill-hints.jsonl", "usage.jsonl")
GRACE = dt.timedelta(hours=1)
MIN_COMMITS = 2


def ts(text: str) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def has_hooks(root: Path) -> bool:
    try:
        return bool(json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8")).get("hooks"))
    except (OSError, ValueError, AttributeError):
        return False


def last_log(root: Path) -> dt.datetime | None:
    last = None
    for name in LOGS:
        f = root / ".claude" / "logs" / name
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                t = ts(json.loads(line).get("ts", ""))
            except (ValueError, AttributeError):
                continue
            if t and (last is None or t > last):
                last = t
    return last


def commit_times(root: Path) -> list[dt.datetime]:
    r = subprocess.run(["git", "-C", str(root), "log", "--format=%cI"], capture_output=True, text=True)
    return [t for t in (ts(x) for x in r.stdout.split()) if t] if r.returncode == 0 else []


def status(root: Path) -> dict:
    if os.environ.get("CI") or not has_hooks(root):   # w CI nie ma sesji Claude Code, więc nie ma czego sprawdzać
        return {"active": None, "last_log": None, "after_commits": 0, "first_after": None}
    last = last_log(root)
    after = sorted(t for t in commit_times(root) if last is None or t > last + GRACE)
    return {"active": len(after) < MIN_COMMITS, "last_log": last.isoformat() if last else None,
            "after_commits": len(after), "first_after": after[0].isoformat() if after else None}


def line(s: dict) -> str:
    if s["active"] is None:
        return "· hooki fabryki: brak hooków w .claude/settings.json albo CI — nic do sprawdzenia"
    if s["active"]:
        return "✓ hooki fabryki: aktywne (ślady w .claude/logs pokrywają ostatnie commity)"
    since = f"po ostatnim śladzie hooków ({s['last_log'][:16]})" if s["last_log"] else "bez żadnego śladu hooków w .claude/logs"
    return (f"⚠ hooki fabryki prawdopodobnie nieaktywne: {s['after_commits']} commitów {since} — tdd_guard, ochrona "
            "ścieżek i logi kosztów nie działają. Uruchamiaj testy i bramki ręcznie; następną sesję w chmurze zacznij "
            "z jednym repozytorium (README: Sesja w chmurze).")


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a == "--root":
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    s = status(Path(opts.get("--root") or ROOT).resolve())
    print(json.dumps(s, ensure_ascii=False) if opts.get("--json") else line(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
