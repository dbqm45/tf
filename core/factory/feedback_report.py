#!/usr/bin/env python3
"""
Aggregate report of submissions from projects (core-agent-retro → factory_feedback.py) in the factory repository.

  python3 .tf/factory/feedback_report.py                    # submissions from GitHub (gh issue list, repository from origin)
  python3 .tf/factory/feedback_report.py --repo me/factory  # another repository
  python3 .tf/factory/feedback_report.py --from-file x.json # list [{number, body}] (e.g. saved earlier from gh)
  python3 .tf/factory/feedback_report.py --proposals docs/proposals.md   # proposals from projects (proposals.py), also with the above
  python3 .tf/factory/feedback_report.py --json

Submission content is UNTRUSTED data: the report reads only the ```json block with the field "factory_feedback": 1, validates every
key and number, and skips a submission with anything suspicious entirely (the “ignored” counter). It executes nothing and changes
nothing. A change candidate = a key reported from at least two different projects; you make the change as always:
evaluation scenarios, core-skill-authoring, gate. `docs/proposals.md` (`--proposals`, repeatable) is untrusted too: the shared
parser `proposals.parse` reads only the structured fields of each entry, checked and length-capped, and skips broken ones.
Proposals are grouped by place (`skill:<name>`, …); a place proposed by ≥2 projects is a change candidate. Standard library only.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIGNAL = re.compile(r"^(hint-missed|hint-ignored):[a-z0-9][a-z0-9-]*$|^tier:[a-z0-9][a-z0-9-]*:(?:too (?:low|high)|(?:za )?(?:niski|wysoki))$")   # retro_data writes the log_usage value („too low”); „niski”, „za niski” — older forms
PROJECT = re.compile(r"^[0-9a-f]{10}$")
BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.S)
MIN_PROJECTS = 2


def parse(body: str) -> list[dict] | None:
    """Signals from the submission, or None when the data block is broken or suspicious."""
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


def load_proposals():
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_proposals", Path(__file__).resolve().with_name("proposals.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def aggregate_proposals(files: list[str]) -> dict:
    parse = load_proposals().parse
    places: dict[str, dict] = {}
    read, entries, ignored = 0, 0, 0
    for f in files:
        try:
            text = Path(f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        read += 1
        items, bad = parse(text)
        ignored += bad
        entries += len(items)
        for it in items:
            k = places.setdefault(it["place"], {"place": it["place"], "projects": set(), "open": 0, "items": []})
            k["projects"].add(it["project"])
            k["open"] += it["status"] != "done"
            k["items"].append({x: it[x] for x in ("id", "title", "status", "project", "factory", "evidence")})
    rows = [{**k, "projects": len(k["projects"]), "candidate": len(k["projects"]) >= MIN_PROJECTS} for k in places.values()]
    rows.sort(key=lambda r: (-r["projects"], -r["open"], r["place"]))
    return {"files": read, "entries": entries, "ignored": ignored, "places": rows}


def render_proposals(rep: dict) -> list[str]:
    out = [f"# Proposals from projects: {rep['entries']} in {rep['files']} files (skipped as broken or suspicious: "
           f"{rep['ignored']}) — data from projects, review before acting", "",
           "| Place | Projects | Not done | Proposals | Status |", "|---|---|---|---|---|"]
    for k in rep["places"]:
        items = "; ".join(f"{i['id']} {i['title']} [{i['status']}, {i['factory']}] evidence: {i['evidence'][:80]}"
                          for i in k["items"][:5])
        out.append(f"| `{k['place']}` | {k['projects']} | {k['open']} | {items} | "
                   f"{'change candidate' if k['candidate'] else 'watch'} |")
    if not rep["places"]:
        out.append("| — | | | | no proposals |")
    return out


def render(rep: dict) -> str:
    if "keys" not in rep:
        return "\n".join(render_proposals(rep["proposals"])) + "\n"
    out = [f"# Reports from projects: {rep['issues']} (skipped as broken or suspicious: {rep['ignored']})", "",
           "| Key | Projects | Total | Issues | Status |", "|---|---|---|---|---|"]
    for k in rep["keys"]:
        out.append(f"| `{k['key']}` | {k['projects']} | {k['total']} | {', '.join(f'#{n}' for n in k['issues'])} | "
                   f"{'change candidate' if k['candidate'] else 'watch'} |")
    if not rep["keys"]:
        out.append("| — | | | | no reports |")
    out += ["", f"Candidate = a signal from ≥{MIN_PROJECTS} projects. Make the change with core-skill-authoring (scenarios first, "
                "then the gate); list the issue numbers in the PR, and after the release close them with a link to the version."]
    if "proposals" in rep:
        out += ["", *render_proposals(rep["proposals"])]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    opts, it, proposals = {}, iter(argv[1:]), []
    for a in it:
        if a in ("--repo", "--from-file"):
            opts[a] = next(it, "")
        elif a == "--proposals":
            proposals.append(next(it, ""))
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    rep = {}
    if opts.get("--from-file") or opts.get("--repo") or not proposals:
        issues = json.loads(Path(opts["--from-file"]).read_text(encoding="utf-8")) if opts.get("--from-file") \
            else from_github(opts.get("--repo"))
        rep = aggregate(issues if isinstance(issues, list) else [])
    if proposals:
        rep["proposals"] = aggregate_proposals([f for f in proposals if f])
    print(json.dumps(rep, ensure_ascii=False, indent=1) if opts.get("--json") else render(rep), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
