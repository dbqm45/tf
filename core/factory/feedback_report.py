#!/usr/bin/env python3
"""
Zbiorczy raport zgłoszeń z projektów (core-agent-retro → factory_feedback.py) w repozytorium fabryki.

  python3 .tf/factory/feedback_report.py                    # zgłoszenia z GitHuba (gh issue list, repozytorium z origin)
  python3 .tf/factory/feedback_report.py --repo ja/fabryka  # inne repozytorium
  python3 .tf/factory/feedback_report.py --from-file x.json # lista [{number, body}] (np. zapisana wcześniej z gh)
  python3 .tf/factory/feedback_report.py --json

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

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
        sys.exit("✗ gh is missing — save the issues to a file and use --from-file.")
    if not repo:
        r = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True)
        m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$", r.stdout.strip())
        if not m:
            sys.exit("✗ Unknown repository — pass --repo owner/repo.")
        repo = f"{m.group(1)}/{m.group(2)}"
    r = subprocess.run([gh, "issue", "list", "--repo", repo, "--state", "all", "--limit", "500", "--search",
                        "factory-feedback in:body", "--json", "number,body"], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"✗ gh: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout or "[]")


def render(rep: dict) -> str:
    out = [f"# Reports from projects: {rep['issues']} (skipped as broken or suspicious: {rep['ignored']})", "",
           "| Key | Projects | Total | Issues | Status |", "|---|---|---|---|---|"]
    for k in rep["keys"]:
        out.append(f"| `{k['key']}` | {k['projects']} | {k['total']} | {', '.join(f'#{n}' for n in k['issues'])} | "
                   f"{'change candidate' if k['candidate'] else 'watch'} |")
    if not rep["keys"]:
        out.append("| — | | | | no reports |")
    out += ["", f"Candidate = a signal from ≥{MIN_PROJECTS} projects. Make the change with core-skill-authoring (scenarios first, "
                "then the gate); list the issue numbers in the PR, and after the release close them with a link to the version."]
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
