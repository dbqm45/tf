#!/usr/bin/env python3
"""
Report to the factory repository from a saved retrospective (skill core-agent-retro) — standard library only.

  python3 .claude/skills/core-agent-retro/scripts/factory_feedback.py              # "new issue" link with the body
  ... --item "skill:core-semver: missing example of a 0.y.z version"                      # own note about a factory skill/agent
  ... --gh                                                                       # plan of sending through gh (sends nothing)
  ... --gh --yes                                                                 # send through `gh issue create`
  ... --mark-sent                                                                # after sending from the link: remember the keys
  --date YYYY-MM-DD (retrospective; default: newest) · --repo owner/repo · --force (also already reported)
  --json (title, body, link and data block) · --root <project directory>

What goes into the report: only signals about FACTORY skills and agents from the retrospective file
(`hint-missed:<skill>`, `hint-ignored:<skill>`, `tier:<agent>:<signal>`) with counts, the project's decision (without rejected),
the factory version and an anonymous project identifier. Pitfalls, journal, costs, paths and project names — never.
Own notes (`--item`) are checked: a path, address, e-mail or a target outside the factory → refusal (code 2).
Repository: `--repo`, otherwise `source` from the manifest (GitHub address). Sending through gh only with `--yes`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

RETRO_DIR = Path("docs") / "project" / "archive" / "retro"
SIGNAL = re.compile(r"^(hint-missed|hint-ignored):([a-z0-9][a-z0-9-]*)$|^tier:([a-z0-9][a-z0-9-]*):(?:za )?(?:niski|wysoki)$")   # retro_data writes the key with the log_usage value („niski”); „za niski” — the old form
GITHUB = re.compile(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:#.*)?$")
LEAK = [(re.compile(r"(?:^|\s)(?:~|[A-Za-z]:\\|\.{0,2}/)[\w.-]+[/\\]"), "a path"),
        (re.compile(r"https?://|www\.", re.I), "an address"), (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "an e-mail")]
URL_MAX = 7000


def factory_names(root: Path, manifest: dict) -> tuple[set, set]:
    files = manifest.get("files") or {}
    if files:
        skills = {m.group(1) for f in files if (m := re.match(r"\.claude/skills/([^/]+)/SKILL\.md$", f))}
        agents = {m.group(1) for f in files if (m := re.match(r"\.claude/agents/_generated/([^/]+)\.md$", f))}
        return skills, agents
    return ({p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md")},     # the factory repository
            {p.stem for p in (root / ".claude" / "agents" / "_generated").glob("*.md")})


def retro_file(root: Path, date: str | None) -> Path | None:
    if date:
        p = root / RETRO_DIR / f"{date.replace('-', '')}-retro.json"
        return p if p.is_file() else None
    files = sorted((root / RETRO_DIR).glob("*-retro.json"))
    return files[-1] if files else None


def signals(retro: dict, skills: set, agents: set, force: bool) -> list[dict]:
    dec, sent = retro.get("decisions") or {}, retro.get("reported") or {}
    out = []
    for e in retro.get("evidence", []):
        k = e.get("key", "")
        m = SIGNAL.match(k)
        if not m or dec.get(k) == "no" or (k in sent and not force):
            continue
        if (m.group(2) and m.group(2) not in skills) or (m.group(3) and m.group(3) not in agents):
            continue
        out.append({"key": k, "n": int(e.get("n") or 1), "decision": dec.get(k, "—")})
    return out


def check_item(raw: str, skills: set, agents: set) -> tuple[dict | None, str]:
    m = re.match(r"^(skill|agent):([a-z0-9][a-z0-9-]*):\s*(.+)$", raw.strip(), re.S)
    if not m:
        return None, "form: skill:<name>: <remark> or agent:<name>: <remark>"
    kind, name, text = m.groups()
    if name not in (skills if kind == "skill" else agents):
        return None, f"{kind} {name} does not come from the factory"
    if len(text) > 300:
        return None, "the remark is longer than 300 characters"
    for rx, what in LEAK:
        if rx.search(text):
            return None, f"the remark contains {what} — remove the project data"
    return {"target": f"{kind}:{name}", "text": text.strip()}, ""


HINT = {"hint-missed": "add words to metadata.keywords", "hint-ignored": "narrow the words or the description",
        "tier": "change the role tier or the task split"}


def compose(payload: dict) -> tuple[str, str]:
    sig, items = payload["signals"], payload["items"]
    title = f"Signals from a project retrospective (factory {payload['factory_version']}): " + \
            ", ".join(s["key"].split(":")[1] for s in sig[:3]) + (" …" if len(sig) > 3 else "") if sig else \
            f"Remarks from a project retrospective (factory {payload['factory_version']})"
    lines = ["A report from a retrospective of the agents' work (core-agent-retro). It contains only the names of the factory's "
             "skills and agents and numbers — no project data. It is a signal from one project: check it against other reports "
             "(`python3 .tf/factory/feedback_report.py`) and the evaluation scenarios before a change.", ""]
    if sig:
        lines += ["| Key | Count | Decision in the project | What it suggests |", "|---|---|---|---|"]
        lines += [f"| `{s['key']}` | {s['n']} | {s['decision']} | {HINT[s['key'].split(':')[0]]} |" for s in sig]
    if items:
        lines += ["", "Remarks:"] + [f"- `{i['target']}`: {i['text']}" for i in items]
    w = payload.get("window") or {}
    lines += ["", f"Factory version: {payload['factory_version']} · window: {w.get('since', '?')} – {w.get('until', '?')} · "
                  f"project (anonymous): {payload['project']}", "",
              "```json", json.dumps(payload, ensure_ascii=False), "```", "<!-- factory-feedback -->"]
    return title, "\n".join(lines) + "\n"


def link(repo: str, title: str, body: str) -> str:
    url = f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode({"title": title, "body": body})
    if len(url) > URL_MAX:   # browsers and GitHub truncate long URLs — only the data block remains
        short = body.split("```json", 1)[1]
        url = f"https://github.com/{repo}/issues/new?" + urllib.parse.urlencode({"title": title, "body": "```json" + short})
    return url


def main(argv: list[str]) -> int:
    opts, items_raw, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--root", "--date", "--repo"):
            opts[a] = next(it, "")
        elif a == "--item":
            items_raw.append(next(it, ""))
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    man_p = root / ".claude" / "factory-manifest.json"
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.is_file() else {}
    version = manifest.get("version") or ((root / ".tf" / "factory" / "VERSION").read_text(encoding="utf-8").strip()
                                          if (root / ".tf" / "factory" / "VERSION").is_file() else "?")
    repo = opts.get("--repo") or ""
    if not repo:
        m = GITHUB.search(str(manifest.get("source") or os.environ.get("CLAUDE_TEAM_FACTORY") or ""))
        repo = f"{m.group(1)}/{m.group(2)}" if m else ""
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        print("✗ The factory repository on GitHub is unknown (the source in the manifest is not a GitHub address). "
              "Give --repo owner/repo.")
        return 2
    skills, agents = factory_names(root, manifest)
    items = []
    for raw in items_raw:
        item, err = check_item(raw, skills, agents)
        if not item:
            print(f"✗ --item \"{raw[:60]}\": {err}")
            return 2
        items.append(item)
    rf = retro_file(root, opts.get("--date"))
    retro = json.loads(rf.read_text(encoding="utf-8")) if rf else {}
    if not rf and not items:
        print("✗ No saved retrospective — run retro_data.py --save first (or give --item).")
        return 2
    sig = signals(retro, skills, agents, bool(opts.get("--force")))
    if not sig and not items:
        print("✓ None: nothing new to report to the factory (signals already reported, rejected or not from the factory; --force reports them again).")
        return 0
    payload = {"factory_feedback": 1, "project": hashlib.sha256(str(root).encode()).hexdigest()[:10],
               "factory_version": version, "window": retro.get("window") or {}, "signals": sig, "items": items}
    title, body = compose(payload)
    url = link(repo, title, body)

    def remember(where: str) -> None:
        if rf:
            retro.setdefault("reported", {}).update({s["key"]: where for s in sig})
            rf.write_text(json.dumps(retro, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    if opts.get("--json"):
        print(json.dumps({"repo": repo, "title": title, "body": body, "url": url, "payload": payload}, ensure_ascii=False))
        return 0
    if opts.get("--mark-sent"):
        remember("link")
        print(f"✓ Recorded as reported: {', '.join(s['key'] for s in sig) or '—'}")
        return 0
    print(f"Title: {title}\n\n{body}")
    if opts.get("--gh"):
        gh = os.environ.get("CTF_GH") or shutil.which("gh") or ""
        cmd = [gh or "gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", "-"]
        if not opts.get("--yes"):
            print(f"Plan: gh issue create --repo {repo} --title \"{title}\" --body-file - (content above).\n"
                  "To send: add --yes. Or open the link and send it yourself:\n" + url)
            return 0
        if not gh or not os.access(gh, os.X_OK):
            print(f"✗ gh is missing — open the link and send the report yourself (then --mark-sent):\n{url}")
            return 1
        r = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"✗ gh returned an error: {r.stderr.strip()[:300]}\nOpen the link and send it yourself (then --mark-sent):\n{url}")
            return 1
        created = (r.stdout.strip().splitlines() or ["gh"])[-1]
        remember(created)
        print(f"✓ Issue created: {created}")
        return 0
    print(f"Open it, check the content and send it (then --mark-sent, so you do not report it twice):\n{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
