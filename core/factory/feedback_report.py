#!/usr/bin/env python3
"""
Zbiorczy raport zgłoszeń z projektów (core-agent-retro → factory_feedback.py) w repozytorium fabryki.

  python3 factory/feedback_report.py                    # zgłoszenia z GitHuba (gh issue list, repozytorium z origin)
  python3 factory/feedback_report.py --repo ja/fabryka  # inne repozytorium
  python3 factory/feedback_report.py --from-file x.json # lista [{number, body}] (np. zapisana wcześniej z gh)
  python3 factory/feedback_report.py --json

Treść zgłoszeń to NIEZAUFANE dane: raport czyta wyłącznie blok ```json z polem "factory_feedback": 1, waliduje każdy
klucz i liczbę, a zgłoszenie z czymkolwiek podejrzanym pomija w całości (licznik „ignored”). Nic nie wykonuje i niczego
nie zmienia. Kandydat do zmiany = klucz zgłoszony z co najmniej dwóch różnych projektów; zmianę robisz jak zawsze:
scenariusze ewaluacji, core-skill-authoring, bramka. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNAL = re.compile(r"^(hint-missed|hint-ignored):[a-z0-9][a-z0-9-]*$|^tier:[a-z0-9][a-z0-9-]*:(za niski|za wysoki)$")
PROJECT = re.compile(r"^[0-9a-f]{10}$")
BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.S)
MIN_PROJECTS = 2


def parse(body: str) -> list[dict] | None:
    """Sygnały ze zgłoszenia albo None, gdy blok danych jest zepsuty lub podejrzany."""
    for raw in BLOCK.findall(body or ""):
        try:
            data = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(data, dict) or data.get("factory_feedback") != 1:
            continue
        sig = data.get("signals")
        if not PROJECT.match(str(data.get("project", ""))) or not isinstance(sig, list):
            return None
        out = []
        for s in sig:
            if not (isinstance(s, dict) and SIGNAL.match(str(s.get("key", ""))) and isinstance(s.get("n"), int)
                    and 1 <= s["n"] <= 10000):
                return None
            out.append({"key": s["key"], "n": s["n"], "project": data["project"]})
        return out
    return None


def aggregate(issues: list[dict]) -> dict:
    keys: dict[str, dict] = {}
    ignored = 0
    for i in issues:
        sig = parse(i.get("body", ""))
        if sig is None:
            ignored += 1
            continue
        for s in sig:
            k = keys.setdefault(s["key"], {"key": s["key"], "projects": set(), "total": 0, "issues": []})
            k["projects"].add(s["project"])
            k["total"] += s["n"]
            if i.get("number") not in k["issues"]:
                k["issues"].append(i.get("number"))
    rows = [{**k, "projects": len(k["projects"]), "issues": sorted(k["issues"]),
             "candidate": len(k["projects"]) >= MIN_PROJECTS} for k in keys.values()]
    rows.sort(key=lambda r: (-r["projects"], -r["total"], r["key"]))
    return {"issues": len(issues), "ignored": ignored, "keys": rows}


def from_github(repo: str | None) -> list[dict]:
    gh = shutil.which("gh")
    if not gh:
        sys.exit("✗ Brak gh — zapisz zgłoszenia do pliku i użyj --from-file.")
    if not repo:
        r = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True)
        m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$", r.stdout.strip())
        if not m:
            sys.exit("✗ Nie znam repozytorium — podaj --repo właściciel/repo.")
        repo = f"{m.group(1)}/{m.group(2)}"
    r = subprocess.run([gh, "issue", "list", "--repo", repo, "--state", "all", "--limit", "500", "--search",
                        "factory-feedback in:body", "--json", "number,body"], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"✗ gh: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout or "[]")


def render(rep: dict) -> str:
    out = [f"# Zgłoszenia z projektów: {rep['issues']} (pominięte jako zepsute lub podejrzane: {rep['ignored']})", "",
           "| Klucz | Projekty | Suma | Zgłoszenia | Status |", "|---|---|---|---|---|"]
    for k in rep["keys"]:
        out.append(f"| `{k['key']}` | {k['projects']} | {k['total']} | {', '.join(f'#{n}' for n in k['issues'])} | "
                   f"{'kandydat do zmiany' if k['candidate'] else 'obserwuj'} |")
    if not rep["keys"]:
        out.append("| — | | | | brak zgłoszeń |")
    out += ["", f"Kandydat = sygnał z ≥{MIN_PROJECTS} projektów. Zmianę zrób przez core-skill-authoring (najpierw scenariusze, "
                "potem bramka); w PR podaj numery zgłoszeń, a po wydaniu zamknij je z odesłaniem do wersji."]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a in ("--repo", "--from-file"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    issues = json.loads(Path(opts["--from-file"]).read_text(encoding="utf-8")) if opts.get("--from-file") \
        else from_github(opts.get("--repo"))
    rep = aggregate(issues if isinstance(issues, list) else [])
    print(json.dumps(rep, ensure_ascii=False, indent=1) if opts.get("--json") else render(rep), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
