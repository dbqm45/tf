#!/usr/bin/env python3
"""
Project record (docs/project/): structure, index, validation, event log, report.

  python3 .claude/hooks/project_record.py init                 # create the docs/project/ structure
  python3 .claude/hooks/project_record.py status               # phase state, items awaiting acceptance, last handoff
  python3 .claude/hooks/project_record.py check                # artifact validation (exit 1 on errors)
  python3 .claude/hooks/project_record.py index                # rebuild docs/project/README.md
  python3 .claude/hooks/project_record.py log --by ewa --phase domain "Created the context map (proposed)"
  python3 .claude/hooks/project_record.py report [--out file]  # a report to read/hand over
  python3 .claude/hooks/project_record.py evidence             # quotes from corpus.md exist in the sources; area thresholds
  python3 .claude/hooks/project_record.py wip start "Task goal" [--slug name] [--by who]   # checkpoint of work in progress
  python3 .claude/hooks/project_record.py wip list | show [name] | done <name> | pause <name> | snapshot
  --hook-session / --hook-index                                 # hook modes (SessionStart / PostToolUse)
  --hook-snapshot <event> / --hook-stop                         # state snapshot (PreCompact, SessionEnd) / reminder (Stop)

Standard library only. Project directory: $CLAUDE_PROJECT_DIR or the current one.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

TEMPLATES = Path(__file__).resolve().parent.parent / "skills" / "core-project-record" / "templates"
PHASES = [
    ("discovery", "01-discovery", "Discovery"),
    ("domain", "02-domain", "Domain"),
    ("requirements", "03-requirements", "Requirements"),
    ("architecture", "04-architecture", "Architecture and stack"),
    ("plan", "05-plan", "Plan"),
    ("delivery", "06-delivery", "Delivery"),
    ("review", "07-review", "Reviews"),
    ("operations", "08-operations", "Operations"),
]
PHASE_DIR = {p: d for p, d, _ in PHASES}
PHASE_LABEL = {p: label for p, _, label in PHASES}
STATUSES = ["draft", "proposed", "accepted", "superseded", "rejected"]
REQUIRED_KEYS = ["artifact", "phase", "status", "version", "author", "created", "updated", "inputs"]
NO_SECTIONS = {"adr", "journal", "decisions"}
# main phase artifacts — they must have a header (other files are supporting material)
MAIN_PATTERNS = [
    r"01-discovery/brief\.md", r"02-domain/strategic\.md", r"03-requirements/requirements\.md",
    r"04-architecture/[^/]+\.md", r"04-architecture/adr/[^/]+\.md", r"05-plan/[^/]+\.md",
    r"06-delivery/[^/]+\.md", r"07-review/[^/]+\.md", r"08-operations/[^/]+\.md",
]


def root_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()


def record_dir(root: Path) -> Path:
    return root / "docs" / "project"


# ───────────── parsowanie ─────────────

def parse(path: Path) -> tuple[dict | None, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, text
    meta: dict = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = re.sub(r"\s+#.*$", "", value).strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value.strip("'\"")
    return meta, m.group(2)


# Section names: English (since 14.x) and the former Polish — both recognized, templates use the English one.
SECTION_NAMES = {"Przekazanie": ("Handoff", "Przekazanie"), "Otwarte pytania": ("Open questions", "Otwarte pytania"),
                 "Następna czynność": ("Next step", "Następna czynność"), "Kroki": ("Steps", "Kroki")}


def section(body: str, name: str) -> str | None:
    names = "|".join(re.escape(n) for n in SECTION_NAMES.get(name, (name,)))
    m = re.search(rf"^##\s+(?:{names})\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else None


def title(body: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return m.group(1).strip() if m else fallback


def artifacts(rec: Path) -> list[dict]:
    items = []
    for p in sorted(rec.rglob("*.md")):
        rel = p.relative_to(rec).as_posix()
        if rel == "README.md" or rel.startswith(("exports/", "archive/", "wip/")):
            continue
        meta, body = parse(p)
        if meta is None and rel.startswith("changes/"):   # a task file (ticket, plan, report) — index: changes/INDEX.md
            continue
        items.append({"path": p, "rel": rel, "meta": meta, "body": body,
                      "main": any(re.fullmatch(pat, rel) for pat in MAIN_PATTERNS)})
    return items


def phase_index(phase: str) -> int:
    return next((i for i, (p, _, _) in enumerate(PHASES) if p == phase), -1)


# ───────────── walidacja ─────────────

def language_warnings(rec: Path) -> list[str]:
    """Language remarks (HIGH and MEDIUM) from the Polish-language linter (pack-editorial-pl) — zero tokens; warnings only,
    they do not block. Without the overlay — no remarks."""
    lint_path = Path(__file__).resolve().parent.parent / "skills" / "txt-polish-correctness" / "scripts" / "polish_lint.py"  # pack-editorial-pl
    if not lint_path.exists():
        return []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("polish_lint", lint_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        out = []
        for f in sorted(rec.rglob("*.md")):
            rel = f.relative_to(rec).as_posix()
            if rel == "README.md" or rel.startswith(("exports/", "archive/")) or rel.endswith("corpus.md"):
                continue   # the evidence bank holds verbatim quotes — we do not correct them
            issues = [i for i in mod.lint_file(f) if i["priority"] in ("HIGH", "MEDIUM")]
            if issues:
                first = issues[0]
                out.append(f"{rel}: {len(issues)} language remarks (e.g. l.{first['line']}: {first['fragment']} → "
                           f"{first['suggestion']}) — polish_lint.py or polish-editor")
        return out
    except Exception:
        return []


def check(root: Path) -> tuple[list[str], list[str]]:
    rec = record_dir(root)
    errors, warnings = [], []
    if not rec.exists():
        return [f"no {rec.relative_to(root)} — run: project_record.py init"], []
    items = artifacts(rec)
    by_rel = {f"docs/project/{i['rel']}": i for i in items}
    for it in items:
        meta, rel = it["meta"], it["rel"]
        if meta is None:
            if it["main"]:
                errors.append(f"{rel}: no header (frontmatter) — the main artifact of a phase")
            continue
        for k in REQUIRED_KEYS:
            if k not in meta or meta[k] in ("", None):
                errors.append(f"{rel}: no '{k}' field in the header")
        raw = "\n".join(f"{k}: {v}" for k, v in meta.items())
        if "<" in raw and ">" in raw:
            errors.append(f"{rel}: template markers <…> are left in the header")
        status, phase, kind = meta.get("status"), meta.get("phase"), meta.get("artifact")
        if status and status not in STATUSES:
            errors.append(f"{rel}: unknown status '{status}' (allowed: {', '.join(STATUSES)})")
        if phase and phase != "meta":
            if phase not in PHASE_DIR:
                errors.append(f"{rel}: unknown phase '{phase}'")
            elif not rel.startswith(PHASE_DIR[phase] + "/"):
                errors.append(f"{rel}: phase '{phase}', but the file is not in {PHASE_DIR[phase]}/")
        if kind not in NO_SECTIONS:
            tldr = section(it["body"], "TL;DR")
            if tldr is None:
                errors.append(f"{rel}: no \"## TL;DR\" section")
            elif not tldr or tldr.startswith("<"):
                errors.append(f"{rel}: empty TL;DR section")
            elif len([l for l in tldr.splitlines() if l.strip()]) > 12:
                warnings.append(f"{rel}: TL;DR longer than ~10 lines — shorten it (every next agent reads it)")
            handoff = section(it["body"], "Przekazanie")
            if handoff is None and status != "superseded":
                errors.append(f"{rel}: no \"## Handoff\" section (formerly \"## Przekazanie\")")
            elif handoff is not None and status in ("proposed", "accepted") and (
                    re.search(r"<[^>]+>", handoff) or re.search(r":\*?\*?\s*…\s*$", handoff, re.M)):
                errors.append(f"{rel}: Handoff has unfilled template fields (<…> or …)")
        if kind not in ("journal", "decisions") and status in ("proposed", "accepted"):
            leftovers = re.findall(r"^[^|`\n]*<[A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż][^>\n]{3,}>", it["body"], re.M)
            if leftovers:
                warnings.append(f"{rel}: template leftovers in the content, e.g. {leftovers[0].strip()[:60]!r}")
        if status == "superseded" and not meta.get("superseded_by"):
            errors.append(f"{rel}: status superseded without the superseded_by field")
        for inp in meta.get("inputs") or []:
            target = by_rel.get(inp)
            if not (root / inp).exists():
                errors.append(f"{rel}: the input '{inp}' does not exist")
            elif status == "accepted" and target and target["meta"] and target["meta"].get("status") != "accepted":
                warnings.append(f"{rel}: accepted, but the input {inp} has the status '{target['meta'].get('status')}'")
    dec = rec / "decisions.md"
    if dec.exists():
        ids = re.findall(r"^\|\s*(D-\d+)\s*\|", dec.read_text(encoding="utf-8"), re.M)
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            errors.append(f"decisions.md: duplicated decision IDs {dup}")
    warnings += language_warnings(rec)
    for phase, d, _ in PHASES:
        folder = rec / d
        mains = {"discovery": ["brief.md", "pre-flight.md"], "domain": ["strategic.md", "areas.md"], "requirements": ["requirements.md"],
                 "plan": ["plan.md", "test-plan.md"]}.get(phase)
        if mains and folder.exists() and any(folder.rglob("*.md")) and not any((folder / m).exists() for m in mains):
            warnings.append(f"{d}/: there are files, but no main artifact {' nor '.join(mains)}")
    return errors, warnings


# ───────────── indeks / status / raport ─────────────

def first_line(text: str | None) -> str:
    for line in (text or "").splitlines():
        line = line.strip().lstrip("-* ").strip()
        if line and not line.startswith("<!--"):
            return (line[:140] + "…") if len(line) > 140 else line
    return ""


def journal_rows(rec: Path, n: int) -> list[str]:
    j = rec / "journal.md"
    if not j.exists():
        return []
    rows = [l for l in j.read_text(encoding="utf-8").splitlines() if l.startswith("| 20")]
    return rows[-n:]


def summary(root: Path) -> dict:
    rec = record_dir(root)
    items = [i for i in artifacts(rec) if i["meta"] and i["meta"].get("phase") in PHASE_DIR]
    live = [i for i in items if i["meta"].get("status") not in ("superseded", "rejected")]
    current = max(live, key=lambda i: phase_index(i["meta"]["phase"]), default=None)
    with_handoff = [i for i in live if section(i["body"], "Przekazanie")]
    latest = max(with_handoff, key=lambda i: (i["meta"].get("updated", ""), phase_index(i["meta"]["phase"]),
                                             i["path"].stat().st_mtime), default=None)
    return {
        "items": items,
        "current_phase": current["meta"]["phase"] if current else None,
        "to_accept": [i for i in live if i["meta"].get("status") == "proposed"],
        "latest": latest,
    }


def build_index(root: Path) -> str:
    rec = record_dir(root)
    s = summary(root)
    lines = [
        "<!-- GENERATED by .claude/hooks/project_record.py — do not edit by hand -->",
        "# Project record", "",
        f"**Current phase:** {PHASE_LABEL.get(s['current_phase'], '—')}  ·  "
        f"**To accept:** {len(s['to_accept'])}  ·  [Event journal](journal.md)  ·  [Decision register](decisions.md)", "",
        "| Phase | Artifact | Status | Version | Author | Updated | TL;DR |", "|---|---|---|---|---|---|---|",
    ]
    for it in sorted(s["items"], key=lambda i: (phase_index(i["meta"]["phase"]), i["rel"])):
        m = it["meta"]
        lines.append(f"| {PHASE_LABEL[m['phase']]} | [{title(it['body'], it['rel'])}]({it['rel']}) | {m.get('status')} | "
                     f"{m.get('version', '')} | {m.get('author', '')} | {m.get('updated', '')} | {first_line(section(it['body'], 'TL;DR'))} |")
    wips = wip_items(root)
    if wips:
        lines += ["", "## Work in progress", "", "| Task | Status | Updated | Next step |", "|---|---|---|---|"]
        lines += [f"| [{title(w['body'], w['slug'])}](wip/{w['slug']}.md) | {w['meta'].get('status', 'active')} | "
                  f"{w['meta'].get('updated', '')} | {first_line(section(w['body'], 'Następna czynność'))} |" for w in wips]
    if s["latest"]:
        handoff = section(s["latest"]["body"], "Przekazanie")
        if handoff:
            lines += ["", f"## Latest handoff — from [{s['latest']['rel']}]({s['latest']['rel']})", "", handoff]
    rows = journal_rows(rec, 5)
    if rows:
        lines += ["", "## Recent events", "", "| When | Who | Phase | Event |", "|---|---|---|---|", *rows]
    return "\n".join(lines) + "\n"


def write_index(root: Path) -> None:
    rec = record_dir(root)
    if rec.exists():
        (rec / "README.md").write_text(build_index(root), encoding="utf-8")


def status_text(root: Path, compact: bool = False) -> str:
    rec = record_dir(root)
    if not rec.exists():
        return ""
    s = summary(root)
    out = wip_lines(root, compact)
    out.append(f"Project record: docs/project/README.md · current phase: {PHASE_LABEL.get(s['current_phase'], 'no artifacts')}")
    if s["to_accept"]:
        out.append("For a human to accept: " + ", ".join(i["rel"] for i in s["to_accept"]))
    if s["latest"]:
        handoff = section(s["latest"]["body"], "Przekazanie") or ""
        h = [l for l in handoff.splitlines() if l.strip()][: 4 if compact else 20]
        if h:
            out.append(f"Latest handoff ({s['latest']['rel']}):")
            out += ["  " + l for l in h]
    recent = journal_rows(rec, 3)
    if recent:
        out.append("Recent events (journal.md) — take the user's decisions and answers into account:")
        out += ["  " + " · ".join(c.strip() for c in r.strip("|").split("|")) for r in recent]
    if not compact:
        out.append("")
        for it in sorted(s["items"], key=lambda i: (phase_index(i["meta"]["phase"]), i["rel"])):
            m = it["meta"]
            out.append(f"  [{m.get('status'):<10}] {it['rel']:<45} {first_line(section(it['body'], 'TL;DR'))[:80]}")
    return "\n".join(out)


def report(root: Path, out: Path | None) -> Path:
    rec = record_dir(root)
    s = summary(root)
    brief = rec / "01-discovery" / "brief.md"
    name = title(parse(brief)[1], root.name) if brief.exists() else root.name
    lines = [f"# Project report: {name}", "", f"Generated: {datetime.now():%Y-%m-%d %H:%M} · current phase: "
             f"{PHASE_LABEL.get(s['current_phase'], '—')}", "", "## Artifact status", "",
             "| Phase | Artifact | Status | Author | Updated |", "|---|---|---|---|---|"]
    ordered = sorted(s["items"], key=lambda i: (phase_index(i["meta"]["phase"]), i["rel"]))
    for it in ordered:
        m = it["meta"]
        lines.append(f"| {PHASE_LABEL[m['phase']]} | {it['rel']} | {m.get('status')} | {m.get('author')} | {m.get('updated')} |")
    lines += ["", "## Phase summaries"]
    for it in ordered:
        if it["meta"].get("status") in ("superseded", "rejected"):
            continue
        tl = section(it["body"], "TL;DR")
        if tl:
            lines += ["", f"### {title(it['body'], it['rel'])}  ·  _{it['meta'].get('status')}_", "", tl]
    dec = rec / "decisions.md"
    if dec.exists():
        rows = [l for l in dec.read_text(encoding="utf-8").splitlines() if re.match(r"^\|\s*D-\d+", l)]
        if rows:
            lines += ["", "## Decisions", "", "| ID | Date | Decision | Rationale | Status | Author | Details |",
                      "|---|---|---|---|---|---|---|", *rows]
    questions = []
    for it in ordered:
        q = section(it["body"], "Otwarte pytania") if it["meta"].get("status") not in ("superseded", "rejected") else None
        for l in (q or "").splitlines():
            l = l.strip()
            if l.startswith(("- [ ]", "- ", "* ")) and not l.startswith("- [x]") and "…" not in l:
                questions.append(f"{l}  _({it['rel']})_")
    if questions:
        lines += ["", "## Open questions", "", *questions]
    rows = journal_rows(rec, 15)
    if rows:
        lines += ["", "## Recent events", "", "| When | Who | Phase | Event |", "|---|---|---|---|", *rows]
    target = out or rec / "exports" / f"report-{date.today():%Y-%m-%d}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


# ───────────── writing ─────────────

def from_template(name: str) -> str:
    today = f"{date.today():%Y-%m-%d}"
    return (TEMPLATES / name).read_text(encoding="utf-8").replace("<YYYY-MM-DD>", today)


def init(root: Path) -> Path:
    rec = record_dir(root)
    for _, d, _ in PHASES:
        (rec / d).mkdir(parents=True, exist_ok=True)
    (rec / "04-architecture" / "adr").mkdir(exist_ok=True)
    for extra in ("archive", "exports"):
        (rec / extra).mkdir(exist_ok=True)
    for name in ("journal.md", "decisions.md"):
        if not (rec / name).exists():
            (rec / name).write_text(from_template(name), encoding="utf-8")
    log(root, "system", "meta", "Created the project record (docs/project/)")
    write_index(root)
    return rec


def log(root: Path, by: str, phase: str, text: str) -> None:
    rec = record_dir(root)
    j = rec / "journal.md"
    if not j.exists():
        rec.mkdir(parents=True, exist_ok=True)
        j.write_text(from_template("journal.md"), encoding="utf-8")
    clean = " ".join(text.split()).replace("|", "\\|")
    with j.open("a", encoding="utf-8") as f:
        f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | {by} | {phase} | {clean} |\n")
    content = j.read_text(encoding="utf-8")
    j.write_text(re.sub(r"^updated: .*$", f"updated: {date.today():%Y-%m-%d}", content, count=1, flags=re.M), encoding="utf-8")


# ───────────── work in progress (wip/) — session interruption and return ─────────────

WIP_ACTIVE = ("active", "paused", "blocked")
AUTO_BEGIN, AUTO_END = "<!-- stan-automatyczny:begin -->", "<!-- stan-automatyczny:end -->"
STALE_MINUTES = 10          # Stop reminds when file changes are this much newer than the checkpoint
PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.translate(PL).lower()).strip("-")
    return s[:40].rstrip("-") or "task"


def git(root: Path, *args: str) -> str | None:
    """A fast, non-blocking git call: without fsmonitor (on Windows its daemon held the pipe and the hook hung),
    without optional index locks, output in UTF-8 regardless of the system code page."""
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args], cwd=root,
                           stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", errors="replace",
                           timeout=4)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def hook_deadline() -> None:
    """Hook mode ends on its own (exit 0, no output) before the Claude Code limit (10 s in settings.json). A process killed by
    Claude Code produced „Stop hook error … No stderr output” on Windows."""
    import threading
    try:
        seconds = float(os.environ.get("CLAUDE_HOOK_DEADLINE", "7"))
    except ValueError:
        seconds = 7.0
    timer = threading.Timer(seconds, lambda: os._exit(0))
    timer.daemon = True
    timer.start()


def changed_files(root: Path) -> list[str] | None:
    """Uncommitted changes (excluding the checkpoints themselves); None when this is not a git repository."""
    out = git(root, "status", "--porcelain", "-uall")
    if out is None:
        return None
    files = []
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path and not path.startswith((".tf/wip/", ".tf/")) and \
                path not in ("docs/project/README.md", "docs/project/journal.md"):
            files.append(path)
    return files


def wip_dir(root: Path) -> Path:
    """Checkpoints of work in progress: `.tf/wip/` (the factory's work output), archive in `.tf/wip/archive/`."""
    return root / ".tf" / "wip"


def wip_items(root: Path, statuses: tuple = WIP_ACTIVE) -> list[dict]:
    folder = wip_dir(root)
    items = []
    for p in sorted(folder.glob("*.md")) if folder.exists() else []:
        meta, body = parse(p)
        meta = meta or {}
        if meta.get("status", "active") in statuses:
            items.append({"path": p, "slug": p.stem, "meta": meta, "body": body})
    return items


def unchecked(body: str) -> list[str]:
    steps = section(body, "Kroki") or ""
    return [l.strip()[6:].strip() for l in steps.splitlines() if l.strip().startswith("- [ ]")]


def wip_start(root: Path, goal: str, slug: str | None, by: str) -> Path:
    folder = wip_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    slug = slugify(slug or goal)
    path = folder / f"{slug}.md"
    if path.exists():
        raise FileExistsError(f".tf/wip/{slug}.md already exists — resume it or give another --slug")
    now = f"{datetime.now():%Y-%m-%d %H:%M}"
    branch = git(root, "branch", "--show-current") or "—"
    text = from_template("wip.md").replace("<slug>", slug)
    for placeholder, value in (("<who>", by), ("<goal>", goal), ("<YYYY-MM-DD HH:MM>", now), ("<branch>", branch)):
        text = text.replace(placeholder, value)
    path.write_text(text, encoding="utf-8")
    log(root, by, "meta", f"Work in progress started: {goal} (.tf/wip/{slug}.md)")
    write_index(root)
    return path


def wip_set_status(root: Path, slug: str, status: str, by: str) -> Path:
    path = wip_dir(root) / f"{slug}.md"
    if not path.exists():
        raise FileNotFoundError(f"no .tf/wip/{slug}.md")
    text = path.read_text(encoding="utf-8")
    now = f"{datetime.now():%Y-%m-%d %H:%M}"
    text = re.sub(r"^status: .*$", f"status: {status}", text, count=1, flags=re.M)
    text = re.sub(r"^updated: .*$", f"updated: {now}", text, count=1, flags=re.M)
    if status == "done":
        target = wip_dir(root) / "archive" / f"{datetime.now():%Y%m%d}-{slug}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        path.unlink()
        path = target
    else:
        path.write_text(text, encoding="utf-8")
    log(root, by, "meta", f"Work in progress {slug}: {status}")
    write_index(root)
    return path


# Event names from core/settings.json (Polish hook arguments from before 14.x) → English entry in the snapshot.
EVENT_NAMES = {"koniec sesji": "session end", "kompaktowanie kontekstu": "context compaction"}


def snapshot(root: Path, event: str) -> int:
    """Mechanical state record (branch, commit, changed files) in active checkpoints; does not change mtime."""
    items = wip_items(root)
    if not items:
        return 0
    files = changed_files(root)
    branch = git(root, "branch", "--show-current") or "—"
    head = git(root, "log", "-1", "--format=%h %s") or "—"
    shown = ", ".join(f"`{f}`" for f in (files or [])[:25]) + (" …" if files and len(files) > 25 else "")
    block = "\n".join([
        AUTO_BEGIN,
        "## Automatic state (written by the hook — do not edit)",
        f"- Saved: {datetime.now():%Y-%m-%d %H:%M} · event: {event}",
        f"- Branch: {branch} · last commit: {head}",
        f"- Uncommitted changes ({len(files) if files is not None else 'no git'}): {shown or '—'}",
        AUTO_END,
    ])
    for it in items:
        p = it["path"]
        st = p.stat()
        text = p.read_text(encoding="utf-8")
        if AUTO_BEGIN in text and AUTO_END in text:
            text = text[:text.index(AUTO_BEGIN)] + block + text[text.index(AUTO_END) + len(AUTO_END):]
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
        p.write_text(text, encoding="utf-8")
        os.utime(p, (st.st_atime, st.st_mtime))      # the snapshot does not pose as an update by the agent
    return len(items)


def stop_reminder(root: Path, data: dict) -> str | None:
    """A reason to continue when the checkpoint is clearly older than the file changes."""
    if data.get("stop_hook_active"):
        return None
    items = [i for i in wip_items(root, ("active",))]
    files = changed_files(root) if items else None
    if not items or not files:
        return None
    newest = max(((root / f).stat().st_mtime for f in files if (root / f).exists()), default=0)
    checkpoint = max(i["path"].stat().st_mtime for i in items)
    if newest - checkpoint < STALE_MINUTES * 60:
        return None
    names = ", ".join(f".tf/wip/{i['slug']}.md" for i in items)
    return (f"The checkpoint ({names}) is older than the file changes by more than {STALE_MINUTES} min. Before you finish, "
            "update it briefly: tick the finished steps with evidence, write the \"Next step\" and new agreements "
            "from the conversation. If the task is finished: `project_record.py wip done <name>`; if paused: `wip pause <name>`.")


def repo_drift(root: Path, body: str) -> str | None:
    """Drift of the current repo from the state recorded by the snapshot (branch, commit); None when consistent or no data."""
    m = re.search(r"^- (?:Branch|Gałąź): (.+?) · (?:last commit|ostatni commit): (\S+)", body, re.M)
    if not m or m.group(2) == "—":
        return None
    saved_branch, saved_commit = m.group(1).strip(), m.group(2)
    issues = []
    branch = git(root, "branch", "--show-current")
    if branch and saved_branch != "—" and branch != saved_branch:
        issues.append(f"branch {branch} instead of {saved_branch}")
    saved = git(root, "rev-parse", "--verify", "--quiet", f"{saved_commit}^{{commit}}")
    head = git(root, "rev-parse", "HEAD")
    if saved is None:
        issues.append(f"the checkpoint's commit {saved_commit} does not exist in the repository")
    elif head and saved != head:
        if git(root, "merge-base", "--is-ancestor", saved, "HEAD") is None:
            issues.append(f"commit {saved_commit} is not in the current branch's history")
        else:
            n = int(git(root, "rev-list", "--count", f"{saved}..HEAD") or 0)
            word = "commit" if n == 1 else "commits"
            issues.append(f"{n} {word} since the save")
    return "; ".join(issues) or None


def wip_lines(root: Path, compact: bool) -> list[str]:
    out = []
    for it in wip_items(root):
        m, body = it["meta"], it["body"]
        nxt = first_line(section(body, "Następna czynność"))
        todo = unchecked(body)
        out.append(f"Work in progress [{m.get('status', 'active')}]: .tf/wip/{it['slug']}.md — "
                   f"{title(body, it['slug'])} (updated {m.get('updated', '?')}, steps to do: {len(todo)})")
        if nxt:
            out.append(f"  Next step: {nxt}")
        drift = repo_drift(root, it["path"].read_text(encoding="utf-8"))
        if drift:
            out.append(f"  Note: the repo state differs from the checkpoint ({drift}) — before continuing run the tests "
                       "and check whether the steps ticked with evidence are still true.")
        out += [f"  - [ ] {t[:120]}" for t in todo[: 3 if compact else 20]]
    if out:
        out.append("  When resuming: read the whole checkpoint file and `git status` — changes after the last save may "
                   "be unfinished; check them before you start the next step.")
    return out


# ───────────── CLI ─────────────

# ───────────── evidence (the evidence-bank format from the ddd-discovery-intake skill, pack-it) ─────────────

SRC_RE = re.compile(r"^##\s+(S\d+)\s+[—-]\s+(.+?)\s*$", re.M)
ENTRY_RE = re.compile(r"^-\s+\*\*(E\d+)\*\*\s*>\s*[„\"“](.+?)[”\"“]\s*[—-]\s*([^\[\n]*?)\s*((?:\[[^\]]*\]\s*)*)$", re.M)
WEAK_TAGS = ("mention", "superseded", "unverified")


def _norm(text: str) -> str:
    text = text.replace("„", '"').replace("”", '"').replace("“", '"').replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def corpus_entries(corpus: Path) -> tuple[dict, list[str]]:
    text = corpus.read_text(encoding="utf-8")
    entries, errors = {}, []
    heads = [(m.start(), m.group(1), m.group(2).strip()) for m in SRC_RE.finditer(text)]
    for m in ENTRY_RE.finditer(text):
        src = next(((sid, path) for pos, sid, path in reversed(heads) if pos < m.start()), (None, None))
        eid = m.group(1)
        if eid in entries:
            errors.append(f"corpus.md: zduplikowane id {eid}")
        tags = [t.strip().lower() for t in re.findall(r"\[([^\]]*)\]", m.group(4) or "")]
        entries[eid] = {"quote": m.group(2), "loc": m.group(3).strip(), "source": src[0], "path": src[1], "tags": tags}
    return entries, errors


def evidence(root: Path) -> tuple[list[str], list[str], dict]:
    rec = record_dir(root)
    corpus = rec / "02-domain" / "corpus.md"
    if not corpus.exists():
        return ["no docs/project/02-domain/corpus.md"], [], {}
    entries, errors = corpus_entries(corpus)
    warnings: list[str] = []
    cache: dict[str, str | None] = {}
    for eid, e in entries.items():
        if not e["path"]:
            errors.append(f"{eid}: a quote outside a source section (## S1 — path)"); continue
        if e["path"] not in cache:
            f = (root / e["path"])
            cache[e["path"]] = f.read_text(encoding="utf-8", errors="ignore") if f.is_file() else None
        src = cache[e["path"]]
        if src is None:
            errors.append(f"{eid}: the source '{e['path']}' does not exist (the path is relative to the project directory)"); continue
        frags = [f for f in re.split(r"\[(?:…|\.\.\.)\]|…", e["quote"]) if len(f.strip()) >= 3]
        nsrc = _norm(src)
        missing = [f for f in frags if _norm(f) not in nsrc]
        if missing and "unverified" not in e["tags"]:
            errors.append(f"{eid}: the quote does not appear verbatim in {e['path']}: \"{missing[0].strip()[:60]}\"")
            continue
        m = re.fullmatch(r"L(\d+)(?:\s*-\s*L?(\d+))?", e["loc"])
        if m and not missing:
            a = int(m.group(1)); b = int(m.group(2) or a)
            window = _norm("\n".join(src.splitlines()[max(0, a - 3): b + 2]))
            if not all(_norm(f) in window for f in frags):
                warnings.append(f"{eid}: the quote is in the source, but not at {e['loc']}")
    areas = rec / "02-domain" / "areas.md"
    if areas.exists():
        _, body = parse(areas)
        main_part = re.split(r"^##\s+(?:Candidates below the threshold|Kandydaci poniżej progu)", body, flags=re.M)[0]
        for m in re.finditer(r"^###\s+(A\d+)\b(.*?)(?=^###\s|^##\s|\Z)", main_part, re.M | re.S):
            aid, block = m.group(1), m.group(2)
            ids = re.findall(r"E\d+", (re.search(r"(?:Evidence|Dowody):\*?\*?(.*)", block) or [None, ""])[1])
            unknown = [i for i in ids if i not in entries]
            if unknown:
                errors.append(f"areas.md {aid}: unknown evidence {unknown}")
            strong = [i for i in ids if i in entries and not any(t.startswith(WEAK_TAGS) for t in entries[i]["tags"])]
            sources = {entries[i]["source"] for i in strong}
            user = re.search(r"(?:Named by the human|Wskazany przez człowieka):\*?\*?\s*(?:yes|tak)", block, re.I)
            if len(strong) < 3 or len(sources) < 2:
                msg = f"areas.md {aid}: {len(strong)} strong quotes from {len(sources)} sources (threshold: 3 from 2)"
                (warnings if user else errors).append(msg + (" — named by the human" if user else " — move it to \"Candidates below the threshold\""))
    contra = rec / "02-domain" / "contradictions.md"
    if contra.exists():
        for i in sorted(set(re.findall(r"\bE\d+\b", contra.read_text(encoding="utf-8")))):
            if i not in entries:
                warnings.append(f"contradictions.md: a reference to a non-existent quote {i}")
    return errors, warnings, {"quotes": len(entries), "sources": len({e["path"] for e in entries.values()})}


def main(argv: list[str]) -> int:
    args = argv[1:]
    if any(a.startswith("--hook-") for a in args):
        hook_deadline()
    root = root_dir()
    if "--hook-session" in args:
        try:
            print(status_text(root, compact=True))
        except Exception as e:  # the hook does not interrupt the session; the error goes to the log
            record_error("project_record", e)
        return 0
    if "--hook-snapshot" in args:
        try:
            i = args.index("--hook-snapshot")
            event = args[i + 1] if len(args) > i + 1 else "hook"
            snapshot(root, EVENT_NAMES.get(event, event))
        except Exception as e:  # the hook does not interrupt the session; the error goes to the log
            record_error("project_record", e)
        return 0
    if "--hook-stop" in args:
        try:
            reason = stop_reminder(root, json.load(sys.stdin))
            if reason:
                print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        except Exception as e:  # the hook does not interrupt the session; the error goes to the log
            record_error("project_record", e)
        return 0
    if "--hook-index" in args:
        try:
            data = json.load(sys.stdin)
            path = Path((data.get("tool_input") or {}).get("file_path", "")).resolve()
            rec = record_dir(root)
            task_file = (rec / "changes") in path.parents and (not path.is_file() or path.suffix != ".md"
                                                               or parse(path)[0] is None)
            if rec in path.parents and path.name != "README.md" and "exports" not in path.parts and not task_file:
                write_index(root)
        except Exception as e:  # the hook does not interrupt the session; the error goes to the log
            record_error("project_record", e)
        return 0
    cmd = args[0] if args else "status"
    if cmd == "init":
        print(f"✓ Created {init(root).relative_to(root)}")
        return 0
    if cmd == "index":
        write_index(root)
        print("✓ Updated docs/project/README.md")
        return 0
    if cmd == "status":
        print(status_text(root) or "No docs/project/ — run: project_record.py init")
        return 0
    if cmd == "check":
        errors, warnings = check(root)
        for w in warnings:
            print(f"⚠ {w}")
        for e in errors:
            print(f"✗ {e}")
        write_index(root)
        print("✓ Project record valid" if not errors else f"✗ {len(errors)} errors")
        return 1 if errors else 0
    if cmd == "log":
        by = args[args.index("--by") + 1] if "--by" in args else "unknown"
        phase = args[args.index("--phase") + 1] if "--phase" in args else "meta"
        skip = {i for i, a in enumerate(args) if a in ("--by", "--phase")}
        skip |= {i + 1 for i in skip}
        text = " ".join(a for i, a in enumerate(args[1:], 1) if i not in skip)
        if not text:
            print("Give the entry text"); return 2
        log(root, by, phase, text)
        write_index(root)
        print("✓ Appended to journal.md")
        return 0
    if cmd == "wip":
        sub = args[1] if len(args) > 1 else "list"
        by = args[args.index("--by") + 1] if "--by" in args else "unknown"
        try:
            if sub == "start":
                slug = args[args.index("--slug") + 1] if "--slug" in args else None
                skip = {i for i, a in enumerate(args) if a in ("--by", "--slug")}
                skip |= {i + 1 for i in skip}
                goal = " ".join(a for i, a in enumerate(args[2:], 2) if i not in skip).strip()
                if not goal:
                    print("Give the task goal, e.g. wip start \"Sign-in with Google\""); return 2
                print(f"✓ Checkpoint: {wip_start(root, goal, slug, by).relative_to(root)} — fill in the goal, the steps and the next step")
                return 0
            if sub in ("done", "pause", "block", "resume"):
                if len(args) < 3 or args[2].startswith("--"):
                    print(f"Give the name: wip {sub} <name>"); return 2
                status = {"done": "done", "pause": "paused", "block": "blocked", "resume": "active"}[sub]
                print(f"✓ {wip_set_status(root, args[2], status, by).relative_to(root)} — status {status}")
                return 0
            if sub == "snapshot":
                print(f"✓ State snapshot in {snapshot(root, 'manual')} checkpoints"); return 0
            if sub == "show":
                items = [i for i in wip_items(root) if len(args) < 3 or i["slug"] == args[2]]
                for it in items:
                    print(it["path"].read_text(encoding="utf-8"))
                if not items:
                    print("No work in progress")
                return 0
            print("\n".join(wip_lines(root, compact=False)) or "No work in progress")
            return 0
        except (FileExistsError, FileNotFoundError) as e:
            print(f"✗ {e}"); return 1
    if cmd == "evidence":
        errors, warnings, stats = evidence(root)
        for w in warnings:
            print(f"⚠ {w}")
        for e in errors:
            print(f"✗ {e}")
        print((f"✓ Evidence valid ({stats.get('quotes', 0)} quotes, {stats.get('sources', 0)} sources)") if not errors else f"✗ {len(errors)} errors")
        return 1 if errors else 0
    if cmd == "report":
        out = Path(args[args.index("--out") + 1]) if "--out" in args else None
        print(f"✓ Report: {report(root, out).relative_to(root) if not out else out}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
