#!/usr/bin/env python3
"""
The record of a design session (skill tf-design): the script writes it, so it does not depend on the model remembering to.
No model and no network; standard library only.

  python3 .claude/skills/tf-design/scripts/design_session.py start "<subject>" [--slug S] [--stages "A;B;C"] [--by WHO]
  python3 .claude/skills/tf-design/scripts/design_session.py status <slug>
  python3 .claude/skills/tf-design/scripts/design_session.py stage <slug> <n> accept --decision "<text>" [--why "<reason>"]
  python3 .claude/skills/tf-design/scripts/design_session.py stage <slug> <n> back --reason "<why>"
  python3 .claude/skills/tf-design/scripts/design_session.py stage <slug> <n> skip --assumption "<text>"
  python3 .claude/skills/tf-design/scripts/design_session.py handoff <slug>

- `start`: `docs/project/04-architecture/design-<slug>.md` (header as in core-project-record, `status: proposed`) with a
  stage map, and a checkpoint `.tf/wip/design-<slug>.md` (`.claude/hooks/project_record.py wip start`, when present).
- `accept`: the stage becomes `accepted` and a row `D-NNN … | accepted | user |` goes to `docs/project/decisions.md` —
  run it only after the human chose "Accept". An accepted decision binds: only `back` reopens it, explicitly.
- `back`: the current file goes to `docs/project/archive/design-<slug>-v<k>.md` (`status: superseded`), the version rises,
  the stage and every later accepted stage become `reopened`, and their decisions are marked `reopened` in the register.
- `skip`: the stage becomes `skipped`; the assumption is written under the stage map.
- `handoff`: refuses (exit 1, the list of what is missing) while a stage is open or reopened, or the `## Handoff` section
  lacks an `AC-` criterion or still holds a `<…>` placeholder; otherwise prints the `/tf-task` command.
Exit codes: 0 done, 1 refused (state), 2 bad invocation.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DIR = Path("docs") / "project" / "04-architecture"
ARCHIVE = Path("docs") / "project" / "archive"
DECISIONS = Path("docs") / "project" / "decisions.md"
HOOK = Path(".claude") / "hooks" / "project_record.py"
DEC_TEMPLATE = Path(".claude") / "skills" / "core-project-record" / "templates" / "decisions.md"
DEFAULT_STAGES = ("Problem and scope", "Current state", "Options", "Chosen option in detail", "Edge cases and risks", "Plan")
ROW = re.compile(r"^\| (\d+) \| (.+?) \| (open|accepted|reopened|skipped) \| (.*?) \|$", re.M)
MAP_HEAD = "| # | Stage | Status | Decision |\n|---|---|---|---|\n"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48].strip("-") or "session"


def artifact(root: Path, slug: str) -> Path:
    return root / DIR / f"design-{slug}.md"


def today() -> str:
    return date.today().isoformat()


def header(text: str, key: str, value: str) -> str:
    return re.sub(rf"^{key}: .*$", f"{key}: {value}", text, count=1, flags=re.M)


def stages(text: str) -> list[dict]:
    return [{"n": int(m[1]), "name": m[2], "status": m[3], "decision": m[4]} for m in ROW.finditer(text)]


def set_row(text: str, n: int, status: str, decision: str | None = None) -> str:
    def repl(m: re.Match) -> str:
        if int(m[1]) != n:
            return m[0]
        return f"| {m[1]} | {m[2]} | {status} | {m[4] if decision is None else decision} |"
    return ROW.sub(repl, text)


def new_artifact(subject: str, names: list[str], by: str) -> str:
    rows = "".join(f"| {i} | {name} | open | — |\n" for i, name in enumerate(names, 1))
    return (f"---\nartifact: design-session\nphase: architecture\nstatus: proposed\nversion: 1\nauthor: {by}\n"
            f"created: {today()}\nupdated: {today()}\ninputs: []\n---\n# Design: {subject}\n\n"
            f"## TL;DR\nState: Explore — {subject}. Stages accepted: 0 of {len(names)}.\n\n"
            f"## Problem and scope\nTo be written in stage 1.\n\n## Stage map\n{MAP_HEAD}{rows}\n"
            f"## Open questions\n- none yet\n\n## Handoff\nTo be written before the handoff to /tf-task.\n")


def refresh_tldr(text: str) -> str:
    st = stages(text)
    done = sum(s["status"] in ("accepted", "skipped") for s in st)
    nxt = next((s for s in st if s["status"] in ("open", "reopened")), None)
    state = f"Design: stage {nxt['n']} of {len(st)}" if nxt else "Ready for the handoff"
    line = f"State: {state}. Stages accepted or skipped: {done} of {len(st)}."
    return re.sub(r"(## TL;DR\n)State: .*", lambda m: m[1] + line, text, count=1)


def decisions_file(root: Path) -> Path:
    path = root / DECISIONS
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        tpl = root / DEC_TEMPLATE
        text = tpl.read_text(encoding="utf-8") if tpl.is_file() else (
            "---\nartifact: decisions\nphase: meta\nstatus: accepted\nversion: 1\nauthor: system\n"
            "created: <YYYY-MM-DD>\nupdated: <YYYY-MM-DD>\ninputs: []\n---\n# Decision register\n\n"
            "| ID | Date | Decision | Rationale (1 sentence) | Status | Author | Details |\n|---|---|---|---|---|---|---|\n")
        path.write_text(text.replace("<YYYY-MM-DD>", today()), encoding="utf-8")
    return path


def add_decision(root: Path, decision: str, why: str, detail: str) -> str:
    path = decisions_file(root)
    text = path.read_text(encoding="utf-8")
    ids = [int(x) for x in re.findall(r"^\|\s*D-(\d+)\s*\|", text, re.M)]
    did = f"D-{(max(ids) + 1) if ids else 1:03d}"
    cell = lambda s: s.replace("|", "/").replace("\n", " ").strip()
    row = f"| {did} | {today()} | {cell(decision)} | {cell(why) or '—'} | accepted | user | {cell(detail)} |\n"
    path.write_text(text.rstrip("\n") + "\n" + row, encoding="utf-8")
    return did


def reopen_decisions(root: Path, ids: list[str]) -> None:
    path = root / DECISIONS
    if not ids or not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for did in ids:
        text = re.sub(rf"^(\| {re.escape(did)} \|(?:[^|\n]*\|){{3}}) accepted (\|)", r"\1 reopened \2", text, flags=re.M)
    path.write_text(text, encoding="utf-8")


def hook(root: Path, *args: str) -> str:
    script = root / HOOK
    if not script.is_file():
        return "⚠ no .claude/hooks/project_record.py — checkpoint not written"
    r = subprocess.run([sys.executable, str(script), *args], cwd=root, capture_output=True, text=True)
    return (r.stdout or r.stderr).strip()


def opt(args: list[str], name: str) -> str | None:
    if name in args:
        i = args.index(name)
        return args[i + 1] if i + 1 < len(args) else ""
    return None


def cmd_start(root: Path, args: list[str]) -> int:
    skip = {i for i, a in enumerate(args) if a in ("--slug", "--stages", "--by")}
    skip |= {i + 1 for i in skip}
    subject = " ".join(a for i, a in enumerate(args) if i not in skip).strip()
    if not subject:
        print('✗ give the subject: start "<subject>"')
        return 2
    slug = slugify(opt(args, "--slug") or subject)
    names = [s.strip() for s in (opt(args, "--stages") or "").split(";") if s.strip()] or list(DEFAULT_STAGES)
    path = artifact(root, slug)
    if path.exists():
        print(f"✗ {path.relative_to(root).as_posix()} already exists — resume it: design_session.py status {slug}")
        return 1
    by = opt(args, "--by") or "agent"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_artifact(subject, names, by), encoding="utf-8")
    print(f"✓ {path.relative_to(root).as_posix()} — {len(names)} stages, status proposed")
    print(hook(root, "wip", "start", f"design: {subject}", "--slug", f"design-{slug}", "--by", by))
    return 0


def load(root: Path, slug: str) -> tuple[Path, str] | None:
    path = artifact(root, slug)
    if not path.is_file():
        print(f"✗ no design session {slug} — start it: design_session.py start \"<subject>\" --slug {slug}")
        return None
    return path, path.read_text(encoding="utf-8")


def cmd_status(root: Path, slug: str) -> int:
    got = load(root, slug)
    if not got:
        return 1
    path, text = got
    ver = re.search(r"^version: (\d+)", text, re.M)
    print(f"Session: {path.relative_to(root).as_posix()} (version {ver[1] if ver else '?'})")
    for s in stages(text):
        print(f"  {s['n']}. {s['name']} — {s['status']}" + (f" ({s['decision']})" if s["decision"] not in ("—", "") else ""))
    nxt = next((s for s in stages(text) if s["status"] in ("open", "reopened")), None)
    print(f"Next: stage {nxt['n']} — {nxt['name']}" if nxt else f"Next: handoff (design_session.py handoff {slug})")
    return 0


def cmd_stage(root: Path, args: list[str]) -> int:
    if len(args) < 3 or not args[1].isdigit() or args[2] not in ("accept", "back", "skip"):
        print("✗ stage <slug> <n> accept|back|skip …")
        return 2
    slug, n, action = args[0], int(args[1]), args[2]
    got = load(root, slug)
    if not got:
        return 1
    path, text = got
    st = stages(text)
    if not any(s["n"] == n for s in st):
        print(f"✗ stage {n} is not in the stage map (1–{len(st)})")
        return 2
    rel = path.relative_to(root).as_posix()
    if action == "accept":
        decision = opt(args, "--decision")
        if not decision:
            print("✗ accept needs --decision \"<what the human accepted>\" (after the human chose Accept)")
            return 2
        name = next(s["name"] for s in st if s["n"] == n)
        did = add_decision(root, decision, opt(args, "--why") or "", f"{rel} stage {n} ({name})")
        text = set_row(text, n, "accepted", did)
        print(f"✓ stage {n} accepted — {did} in {DECISIONS.as_posix()} (binding; only `back` reopens it)")
    elif action == "skip":
        assumption = opt(args, "--assumption")
        if not assumption:
            print("✗ skip needs --assumption \"<what we assume instead>\"")
            return 2
        text = set_row(text, n, "skipped", "—")
        text = text.replace("\n## Open questions", f"Assumption (stage {n} skipped): {assumption}\n\n## Open questions", 1)
        print(f"✓ stage {n} skipped — the assumption is in the artifact")
    else:
        reason = opt(args, "--reason")
        if not reason:
            print("✗ back needs --reason \"<why the stage is reopened>\"")
            return 2
        ver = int((re.search(r"^version: (\d+)", text, re.M) or ["", "1"])[1])
        old = root / ARCHIVE / f"design-{slug}-v{ver}.md"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text(header(header(text, "status", "superseded"), "updated", today()), encoding="utf-8")
        again = [s for s in st if s["n"] == n or (s["n"] > n and s["status"] == "accepted")]
        reopen_decisions(root, [s["decision"] for s in again if s["decision"].startswith("D-")])
        for s in again:
            text = set_row(text, s["n"], "reopened")
        text = header(text, "version", str(ver + 1))
        text = text.replace("\n## Open questions", f"Reopened from stage {n} (version {ver + 1}): {reason}\n\n## Open questions", 1)
        names = ", ".join(str(s["n"]) for s in again)
        print(f"✓ version {ver} archived in {old.relative_to(root).as_posix()}; reopened stages: {names}")
    text = refresh_tldr(header(text, "updated", today()))
    path.write_text(text, encoding="utf-8")
    print(hook(root, "wip", "snapshot"))
    return 0


def cmd_handoff(root: Path, slug: str) -> int:
    got = load(root, slug)
    if not got:
        return 1
    path, text = got
    missing = [f"stage {s['n']} ({s['name']}) is {s['status']}" for s in stages(text) if s["status"] in ("open", "reopened")]
    hand = text.split("## Handoff", 1)[1] if "## Handoff" in text else ""
    if not re.search(r"\bAC-\d+", hand):
        missing.append("the Handoff section has no acceptance criterion (AC-1 …)")
    if re.search(r"<[^>\n]+>", hand):
        missing.append("the Handoff section still holds a <…> placeholder")
    if missing:
        print("✗ not ready for the handoff:\n" + "\n".join(f"  - {m}" for m in missing))
        return 1
    rel = path.relative_to(root).as_posix()
    print(f"✓ ready: /tf-task {rel}  (or with --plan / --auto, as the human chose)")
    return 0


def main(argv: list[str]) -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    cmd, rest = args[0], args[1:]
    if cmd == "start":
        return cmd_start(root, rest)
    if cmd == "stage":
        return cmd_stage(root, rest)
    if cmd in ("status", "handoff"):
        if not rest:
            print(f"✗ {cmd} <slug>")
            return 2
        return cmd_status(root, rest[0]) if cmd == "status" else cmd_handoff(root, rest[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
