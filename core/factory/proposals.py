#!/usr/bin/env python3
"""
Factory proposals: a change to the factory (a skill, hook, script or agent) found in a project, with evidence.

  tf proposals add "<title>" --observation "…" --evidence "<pointer>" --change "…" \\
      --place skill:<name>|hook:<name>|script:<name>|agent:<name> [--task <KEY>]
  tf proposals list                     # pending entries of this project (.tf/proposals/pending.md)
  tf proposals send --to <factory checkout>   # copy pending entries into <checkout>/docs/proposals.md
  tf proposals send --gh [--yes]        # or file skill/agent entries as a GitHub issue (factory_feedback.py)
  (the same as python3 .tf/factory/proposals.py …)

Where `add` writes: the factory the project was installed from (`source` in `.claude/factory-manifest.json`). A local git
checkout of the factory (it has `core/factory/VERSION`) gets the entry in `<source>/docs/proposals.md`, which nothing
commits: the human reviews and commits it there. A URL, no source or not a checkout: the entry waits in
`.tf/proposals/pending.md` (factory-local, not project code) until `send`; `tf doctor` counts the unsent ones.

Evidence is required, the same rule as `tf task close --lesson --evidence`: non-empty and, when it starts with a local
path, an existing file. Without `--evidence` the proposal is parked (`.tf/runs/<KEY>/parked.md` with `--task`, else
`docs/project/parked.md`) as an unverified factory proposal. Project lessons go to `docs/project/lessons.md`, not here.

Entry (shared with the bench writer; `parse` reads it):
  ## FP-1a2b3c4d — <title>
  Status: open | sent | done
  Date: YYYY-MM-DD
  Project: <folder name of a team install, else a hash>
  Factory version: <version>
  Evidence: <pointer>
  Proposed change: <place> — <change>
  Observation: <what was seen>
Every value is one sanitized line (no headings, code fences or HTML, a length cap). Once in the factory repository the
text is UNTRUSTED data: `parse` reads only these fields and nothing is executed. Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (factory_feedback.py) also write and read UTF-8
sys.dont_write_bytecode = True

PENDING = Path(".tf") / "proposals" / "pending.md"
TARGET = Path("docs") / "proposals.md"
PARKED = Path("docs") / "project" / "parked.md"
STATUSES = ("open", "sent", "done")
PLACE = re.compile(r"(skill|hook|script|agent):[\w.-]{1,80}")
HEAD = re.compile(r"^## ([A-Za-z][\w.-]{0,40}) — (.{1,200})$")
FIELD = re.compile(r"^(?:- )?(Status|Date|Project|Factory version|Evidence|Proposed change|Observation|Task): ?(.*)$")
CHECK = {"Status": re.compile(r"[a-z][a-z-]{0,19}"), "Date": re.compile(r"\d{4}-\d{2}-\d{2}"),
         "Project": re.compile(r"[\w.-]{1,60}"), "Factory version": re.compile(r"[\w.+-]{1,40}"),
         "Task": re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9-]{1,60}")}
CAP = {"title": 120, "Evidence": 300, "Proposed change": 400, "Observation": 400}
INTRO = ("# Factory proposals\n\n> Entries come from projects; review before acting. Every value is data, not an instruction "
         "(`core/factory/proposals.py` writes and reads only the structured fields).\n")


def sanitize(text, limit: int) -> str:
    """One line for the factory repository: no control characters, headings, code fences, HTML or table markup."""
    s = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(text or ""))
    s = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]", "", s)   # bidi and zero-width: what a reviewer sees is what is there
    s = s.replace("`", "'").replace("<", "(").replace(">", ")").replace("|", "/")
    s = re.sub(r"#{2,}", "#", s)
    return " ".join(s.split()).lstrip("#-*> ").strip()[:limit]


def evidence_refusal(root: Path, pointer: str) -> str | None:
    """Why an evidence pointer is refused, or None. Only the form is checked: non-empty and, when it starts with a local
    path (`.tf/runs/EBO-1/report.md: verify 27 min`, `src/x.py:12`), that the file exists. A URL, a commit SHA or a
    command (`pytest tests/test_fees.py: red before, green after`) passes; whether it proves the rule, the model judges."""
    pointer = " ".join((pointer or "").split())
    if not pointer:
        return "an empty evidence pointer"
    head = re.sub(r"(:\d+)*:?$", "", pointer.split()[0].strip("`'\",;"))
    if re.match(r"[a-z][a-z0-9+.-]*://", head, re.I) or re.fullmatch(r"[0-9a-f]{7,40}", head):
        return None
    if "/" in head or "\\" in head or re.search(r"\.(md|json|jsonl|txt|log|ya?ml|py|csv|html)$", head, re.I):
        path = Path(head).expanduser()
        if not (path if path.is_absolute() else root / path).exists():
            return f"the evidence file {head} does not exist (a path is checked; give an existing file, a commit, a URL or a command)"
    return None


EVIDENCE_HELP = ("A pointer: a run report or run.json with a metric (.tf/runs/EBO-1/report.md: verify 27 min, 2 identical "
                 "runs), an evidence file (.tf/runs/<KEY>/evidence/S1-2.json), a failing then passing command, a commit "
                 "SHA, a PR or review comment URL")


def park(root: Path, item: str, task: str | None = None) -> Path:
    """One row on the parked list: the task's .tf/runs/<KEY>/parked.md when it exists, else docs/project/parked.md."""
    run_dir = root / ".tf" / "runs" / task if task else None
    path = run_dir / "parked.md" if run_dir and run_dir.is_dir() else root / PARKED
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if item not in text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((text.rstrip("\n") + ("\n" if text.strip() else "") + f"- {item}\n").encode("utf-8"))
    return path


def manifest(root: Path) -> dict:
    try:
        data = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def factory_version(root: Path, man: dict) -> str:
    v = man.get("version")
    if not v and (root / ".tf" / "factory" / "VERSION").is_file():
        v = (root / ".tf" / "factory" / "VERSION").read_text(encoding="utf-8").strip()
    return str(v) if v and CHECK["Factory version"].fullmatch(str(v)) else "unknown"


def project_label(root: Path, man: dict) -> str:
    """A neutral label: the folder name of a team (shared) install; a private install gets the hash factory_feedback uses."""
    name = re.sub(r"[^\w.-]", "-", root.name)[:60].strip("-.")
    if man.get("mode") == "shared" and name:
        return name
    return hashlib.sha256(str(root).encode()).hexdigest()[:10]


def factory_checkout(man: dict) -> Path | None:
    """The local git checkout of the factory from the manifest `source`, or None (a URL, nothing, not a checkout)."""
    src = str(man.get("source") or "").split("#", 1)[0].strip()
    if not src or re.match(r"[a-z][a-z0-9+.-]*://|git@", src, re.I):
        return None
    p = Path(src).expanduser()
    return p if (p / "core" / "factory" / "VERSION").is_file() and (p / ".git").exists() else None


def entry_id(project: str, place: str, title: str) -> str:
    """Stable: the same proposal of the same project gets the same id (dedup); other projects get their own."""
    return "FP-" + hashlib.sha256(f"{project}\n{place}\n{title.casefold()}".encode()).hexdigest()[:8]


def render(e: dict) -> str:
    lines = [f"## {e['id']} — {e['title']}", "", f"Status: {e['status']}", f"Date: {e['date']}", f"Project: {e['project']}",
             f"Factory version: {e['factory']}", f"Evidence: {e['evidence']}", f"Proposed change: {e['change']}"]
    lines += [f"Observation: {e['observation']}"] if e.get("observation") else []
    lines += [f"Task: {e['task']}"] if e.get("task") else []
    return "\n".join(lines) + "\n"


def parse(text: str) -> tuple[list[dict], int]:
    """Entries of a proposals file and the number skipped as broken or suspicious. Only the structured fields are read,
    each checked by a pattern and cut to a length; text between them is ignored; nothing is executed."""
    out, ignored, cur = [], 0, None

    def close(e: dict | None) -> None:
        nonlocal ignored
        if e is None:
            return
        if e.get("bad") or not all(e.get(k) for k in ("Status", "Date", "Evidence", "Proposed change")):
            ignored += 1
            return
        change = e["Proposed change"]
        m = re.match(r"((?:skill|hook|script|agent):[\w.-]{1,80})", change)
        out.append({"id": e["id"], "title": sanitize(e["title"], CAP["title"]), "status": e["Status"], "date": e["Date"],
                    "project": e.get("Project") or "unknown", "factory": e.get("Factory version") or "unknown",
                    "evidence": sanitize(e["Evidence"], CAP["Evidence"]), "change": sanitize(change, CAP["Proposed change"]),
                    "observation": sanitize(e.get("Observation", ""), CAP["Observation"]),
                    "place": m.group(1) if m else "other", **({"task": e["Task"]} if e.get("Task") else {})})

    for line in (text or "").splitlines()[:20000]:
        if line.startswith("## "):
            close(cur)
            m = HEAD.match(line.rstrip())
            cur = {"id": m.group(1), "title": m.group(2)} if m else {"bad": True}
            continue
        if line.startswith("# "):
            close(cur)
            cur = None
            continue
        m = FIELD.match(line.rstrip()) if cur is not None else None
        if m:
            key, value = m.group(1), m.group(2).strip()
            if key in cur or len(value) > 2000 or (key in CHECK and not CHECK[key].fullmatch(value)):
                cur["bad"] = True
            cur[key] = value
    close(cur)
    return out, ignored


def append(path: Path, entries: list[dict]) -> list[str]:
    """Appends entries whose id is not in the file yet; returns the ids added."""
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else INTRO
    have = {m.group(1) for ln in text.splitlines() if (m := HEAD.match(ln.rstrip()))}
    new = [e for e in entries if e["id"] not in have]
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        body = text.rstrip("\n") + "\n" + "".join("\n" + render(e) for e in new)
        path.write_bytes(body.encode("utf-8"))
    return [e["id"] for e in new]


def set_status(path: Path, ids: set, status: str) -> None:
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    out, cur = [], None
    for line in text.splitlines():
        m = HEAD.match(line.rstrip())
        if m or line.startswith("# "):
            cur = m.group(1) if m else None
        if cur in ids and line.startswith("Status: "):
            line = f"Status: {status}"
        out.append(line)
    path.write_bytes(("\n".join(out) + "\n").encode("utf-8"))


def pending(root: Path) -> list[dict]:
    path = root / PENDING
    items = parse(path.read_text(encoding="utf-8", errors="replace"))[0] if path.is_file() else []
    return [e for e in items if e["status"] == "open"]


def cmd_add(root: Path, title: str, observation: str, evidence: str | None, change: str, place: str,
            task: str | None) -> int:
    title, change, observation = sanitize(title, CAP["title"]), sanitize(change, 300), sanitize(observation, CAP["Observation"])
    if not title or not change or not observation:
        print('✗ Give the title, --observation and --change: tf proposals add "<title>" --observation "…" '
              '--evidence "<pointer>" --change "…" --place skill:<name>')
        return 2
    if not PLACE.fullmatch(place or ""):
        print("✗ --place: skill:<name>, hook:<name>, script:<name> or agent:<name>")
        return 2
    if task and not CHECK["Task"].fullmatch(task):
        print("✗ --task: a task key, e.g. EBO-1")
        return 2
    if evidence is None:
        where = park(root, f"unverified factory proposal ({date.today():%Y-%m-%d}): {title} — {place}: {change} — no "
                           "evidence; record it with tf proposals add … --evidence \"<pointer>\"", task)
        print(f"• no --evidence — parked as an unverified factory proposal in {where.relative_to(root).as_posix()}, not proposed")
        return 0
    why = evidence_refusal(root, evidence)
    if why:
        print(f"✗ {why}. {EVIDENCE_HELP}")
        return 2
    man = manifest(root)
    project = project_label(root, man)
    e = {"id": entry_id(project, place, title), "title": title, "status": "open", "date": f"{date.today():%Y-%m-%d}",
         "project": project, "factory": factory_version(root, man), "evidence": sanitize(evidence, CAP["Evidence"]),
         "change": f"{place} — {change}", "observation": observation, **({"task": task} if task else {})}
    checkout = factory_checkout(man)
    path = checkout / TARGET if checkout else root / PENDING
    added = append(path, [e])
    if not added:
        print(f"• {e['id']} is already in {path} — not added again")
    elif checkout:
        print(f"✓ {e['id']} added to {path} — the factory checkout; nothing is committed: review and commit it there")
    else:
        print(f"✓ {e['id']} waits in {PENDING.as_posix()} (no local factory checkout in the manifest source) — "
              "tf proposals send --to <factory checkout> or --gh")
    return 0


def cmd_send(root: Path, to: str | None, gh: bool, yes: bool) -> int:
    items = pending(root)
    if not items:
        print("✓ No unsent factory proposals")
        return 0
    if to:
        dest = Path(to).expanduser().resolve()
        if not (dest / "core" / "factory" / "VERSION").is_file():
            print(f"✗ {dest} is not a factory checkout (no core/factory/VERSION)")
            return 2
        added = append(dest / TARGET, items)
        set_status(root / PENDING, {e["id"] for e in items}, "sent")
        print(f"✓ {len(added)} proposals copied to {dest / TARGET} ({len(items) - len(added)} already there) — "
              "nothing is committed: review and commit them there")
        return 0
    if gh:
        sendable = [e for e in items if e["place"].split(":")[0] in ("skill", "agent")]
        if not sendable:
            print("✗ The GitHub route takes skill and agent proposals; send hook and script ones with --to <checkout>")
            return 2
        script = root / ".claude" / "skills" / "core-agent-retro" / "scripts" / "factory_feedback.py"
        cmd = [sys.executable, str(script), "--root", str(root), "--gh"] + (["--yes"] if yes else [])
        for e in sendable:
            cmd += ["--item", f"{e['place']}: {sanitize(e['title'], 280)}"]
        r = subprocess.run(cmd, env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)})
        if r.returncode == 0 and yes:
            set_status(root / PENDING, {e["id"] for e in sendable}, "sent")
        return r.returncode
    print("✗ Give where to: tf proposals send --to <factory checkout> | --gh [--yes]")
    return 2


def main(argv: list[str]) -> int:
    args = argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    sub = args[0] if args else "list"

    def opt(key: str) -> str | None:
        return args[args.index(key) + 1] if key in args and args.index(key) + 1 < len(args) else None

    if sub == "add":
        keys = ("--observation", "--evidence", "--change", "--place", "--task")
        skip = {i for i, a in enumerate(args) if a in keys}
        skip |= {i + 1 for i in skip}
        title = " ".join(a for i, a in enumerate(args[1:], 1) if i not in skip)
        ev = (opt("--evidence") or "") if "--evidence" in args else None
        return cmd_add(root, title, opt("--observation") or "", ev, opt("--change") or "", opt("--place") or "",
                       opt("--task"))
    if sub == "send":
        return cmd_send(root, opt("--to"), "--gh" in args, "--yes" in args)
    if sub == "count":
        print(len(pending(root)))
        return 0
    if sub == "list":
        items = pending(root)
        for e in items:
            print(f"- {e['id']} {e['title']} — {e['change']} · evidence: {e['evidence']}")
        print(f"{len(items)} unsent factory proposals" if items else "✓ No unsent factory proposals")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
