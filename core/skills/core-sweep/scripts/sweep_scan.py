#!/usr/bin/env python3
"""
A sweep of what is no longer true in a project (the core-sweep skill) — candidates with evidence, no model, no network.

  python3 .claude/skills/core-sweep/scripts/sweep_scan.py scan [--root .] [--json] [--since-months 12] [--write]
  python3 .claude/skills/core-sweep/scripts/sweep_scan.py apply <report.md> --approve S-03,S-07 [--root .]

`scan` works on text, paths and git history only — no language parser and no test tool, so it fits a project in any
language. It collects CANDIDATES, not verdicts:
  todo-tracker        a TODO/FIXME/HACK/XXX comment that names a tracker key (EBO-812, #123) — the issue may be closed
  todo-old            a TODO older than --since-months by `git blame` — old, which is not the same as stale
  missing-path        a path or file name in a note (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/**,
                      docs/project/**) that is not in the repository; with the commit that last touched it and a rename,
                      when git shows one (then the rule and the code disagree — a conflict for the human)
  missing-command     `npm run x`, `make y`, `just z` whose script, target or recipe is not defined (checked only when
                      package.json, the Makefile or the justfile exists)
  missing-identifier  a name in `code` (snake_case, camelCase, `name()`) found in no tracked file outside the notes
  closed-task         a task folder in docs/project/changes/ whose task.json says `closed`, still in the active area
  superseded-artifact a record artifact with `status: superseded` or `rejected` outside docs/project/archive/
  record-entry        a parked.md or lessons.md entry whose subject shows up in later commits (`git log -S`, commit
                      messages) or that names a tracker key
Every candidate has: id, kind, file, line, claim, why, facts (git facts) and, for documents the script may move, `archive`.
Tracker keys are only printed: their status is checked read-only by the agent (a connected tool or the human).
`--write` saves `.tf/reports/sweep-<date>.json` (the evidence) and `.tf/reports/sweep-<date>.md` (the report skeleton,
every candidate under "Uncertain" until verified).

`apply` moves documents only, and only ids the human approved that sit in the report's "## Stale" section:
closed task folders, superseded artifacts and parked/lessons entries go to docs/project/archive/sweep/<date>/
(the same relative path under it). It does not commit and does not edit code: TODO comments and instruction lines are
changed by the agent by hand after consent. A document changed since the scan is skipped.

Exit code: 0 — done; 1 — apply refused an id (not in "Stale", unknown, or changed since the scan); 2 — call error.
Standard library only; paths in the output with `/`; files read as UTF-8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page does not know „—”, „✓” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SKIP_DIRS = {".git", "node_modules", "dist", "build", "coverage", ".venv", "venv", "__pycache__", "vendor", "target",
             ".tf", ".idea", ".vscode", ".next", ".gradle", ".mypy_cache", ".pytest_cache", ".tox"}
INSTRUCTION_NAMES = {"CLAUDE.md", "AGENTS.md", "CLAUDE.local.md"}
RECORD = "docs/project"
ARCHIVE = "docs/project/archive"
SWEEP_ARCHIVE = "docs/project/archive/sweep"
FACTORY_BLOCK = ("<!-- team-factory:begin -->", "<!-- team-factory:end -->")
TODO_RE = re.compile(r"(?:^\s*|[#;%'*/-]\s*|<!--\s*|\bREM\s+)\b(TODO|FIXME|HACK|XXX)\b(?![-\w])")
KEY_RE = re.compile(r"(?<![\w/#-])(?:[A-Z][A-Z0-9]{1,9}-\d{1,7}|#\d{1,6})(?![\w-])")
SPAN_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
DATE_RE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
NEGATIVE_RE = re.compile(r"(?i)\b(do not|don't|never|skip|ignore\w*|nie czytaj|nie zmieniaj|nie edytuj|pomijaj)\b")
PLANNED_RE = re.compile(r"(?i)\((new|to be created|planned|nowy|nowa|nowe|do utworzenia|planowan\w*)\)|\[plan\]")
SKIP_CHARS = set("<>{}*?$|=@\\")
# file extensions for bare names (without a "/") — a list of file types, not of languages
FILE_EXT = {
    "md", "mdx", "txt", "rst", "adoc", "json", "jsonl", "yaml", "yml", "toml", "ini", "cfg", "conf", "xml", "html", "htm",
    "css", "scss", "sass", "less", "js", "mjs", "cjs", "jsx", "ts", "tsx", "vue", "svelte", "py", "rb", "go", "rs", "java",
    "kt", "kts", "scala", "groovy", "gradle", "cs", "fs", "vb", "php", "swift", "m", "c", "h", "cc", "cpp", "hpp", "dart",
    "ex", "exs", "erl", "clj", "lua", "r", "pl", "pm", "sh", "bash", "zsh", "ps1", "bat", "cmd", "sql", "proto", "graphql",
    "gql", "tf", "hcl", "csv", "lock", "properties", "env", "dockerfile", "mk", "cmake", "ipynb",
}
JS_BUILTINS = {"install", "i", "ci", "add", "remove", "rm", "uninstall", "dlx", "exec", "x", "why", "init", "create",
               "publish", "version", "outdated", "update", "up", "upgrade", "link", "unlink", "view", "info", "pack",
               "audit", "config", "cache", "help", "login", "logout", "global", "workspace", "workspaces", "import",
               "set", "dedupe", "prune", "store", "patch", "rebuild", "env", "bin", "root", "list", "ls"}
MAX_PER_KIND = 200


# ── git ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def git(root: Path, *args: str, timeout: int = 60) -> str | None:
    """Output of a git command (no shell) or None when git is missing, the folder is not a repository or the command failed."""
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def is_repo(root: Path) -> bool:
    return (git(root, "rev-parse", "--is-inside-work-tree") or "").strip() == "true"


def last_commit(root: Path, path: str) -> dict | None:
    """The last commit touching `path` (a file or a folder, also a deleted one) and a rename out of it, if git shows one."""
    out = git(root, "log", "-1", "--format=%h%x09%ad%x09%s", "--date=short", "--", path)
    if not out or not out.strip():
        return None
    sha, day, subject = (out.strip().split("\t") + ["", ""])[:3]
    fact = {"commit": sha, "date": day, "subject": subject[:120]}
    exists_then = git(root, "cat-file", "-e", f"{sha}:{path.rstrip('/')}")
    if exists_then is None:                      # the path is gone in that commit — it was deleted or moved there
        fact["change"] = "deleted or moved"
        show = git(root, "show", "-M", "--name-status", "--format=", sha) or ""
        prefix = path.rstrip("/")
        for row in show.splitlines():
            parts = row.split("\t")
            if len(parts) == 3 and parts[0].startswith("R") and (parts[1] == prefix or parts[1].startswith(prefix + "/")):
                new = parts[2] if parts[1] == prefix else parts[2][: len(parts[2]) - len(parts[1][len(prefix):])]
                fact["moved_to"] = new
                break
    return fact


def log_hits(root: Path, term: str, since: str | None, exclude: list[str]) -> list[str]:
    """Commits after `since` that add or remove `term` (`git log -S`) or name it in the message — max 3, newest first."""
    base = ["log", "--format=%h %ad %s", "--date=short", "-n", "3"] + ([f"--since={since}"] if since else [])
    spec = ["--", "."] + [f":(exclude){e}" for e in exclude]
    hits = []
    for extra in (["-S", term], ["-F", "-i", f"--grep={term}"]):
        for row in (git(root, *base, *extra, *spec) or "").splitlines():
            if row and row not in hits:
                hits.append(row[:140])
    return hits[:3]


def blame_times(root: Path, rel: str, lines: list[int]) -> dict[int, int]:
    """author-time of the given lines (one `git blame` per file, several -L ranges)."""
    if not lines:
        return {}
    args = ["blame", "--line-porcelain", "-w"]
    for n in lines[:300]:
        args += ["-L", f"{n},{n}"]
    out = git(root, *args, "--", rel, timeout=120)
    if not out:
        return {}
    times, current = {}, None
    for row in out.splitlines():
        m = re.match(r"^[0-9a-f]{40} \d+ (\d+)", row)
        if m:
            current = int(m.group(1))
        elif row.startswith("author-time ") and current is not None:
            times[current] = int(row.split()[1])
    return times


# ── files ────────────────────────────────────────────────────────────────────────────────────────────────────────
def rel_of(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def walk(root: Path):
    """Every file of the project without dependencies, build output, .git and the factory's runtime folder .tf/."""
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            yield Path(dirpath) / f


def read(p: Path) -> str | None:
    try:
        if p.stat().st_size > 1_000_000:
            return None
        data = p.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def in_archive(rel: str) -> bool:
    return rel == ARCHIVE or rel.startswith(ARCHIVE + "/")


def note_files(root: Path, files: list[Path]) -> list[Path]:
    """The notes agents read: instruction files, rules and the project record (without its archive and exports)."""
    out = []
    for p in files:
        rel = rel_of(root, p)
        if p.name in INSTRUCTION_NAMES and not rel.startswith(".claude/skills/"):
            out.append(p)
        elif rel.startswith(".claude/rules/") and p.suffix == ".md":
            out.append(p)
        elif rel.startswith(RECORD + "/") and p.suffix == ".md" and not in_archive(rel) \
                and not rel.startswith(RECORD + "/exports/"):
            out.append(p)
    return sorted(set(out))


def tracked(root: Path, repo: bool, files: list[Path]) -> list[str]:
    if repo:
        out = git(root, "ls-files", "-z") or ""
        return [x for x in out.split("\0") if x]
    return [rel_of(root, p) for p in files]


# ── claims in notes ──────────────────────────────────────────────────────────────────────────────────────────────
def prose(lines: list[str], skip_factory: bool):
    """(line number, line) outside code fences and outside the factory block."""
    fence = factory = False
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if skip_factory and s == FACTORY_BLOCK[0]:
            factory = True
            continue
        if skip_factory and s == FACTORY_BLOCK[1]:
            factory = False
            continue
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if not fence and not factory:
            yield n, line


def path_like(word: str) -> str | None:
    """A repository path in a word, or None (an address, an option, a pattern, an absolute path, a plain word)."""
    w = word.strip("'\",;()[]")
    if w.endswith((".", ":")) and not w.endswith(("./", "../")):
        w = w.rstrip(".:")
    if not w or "://" in w or any(c in SKIP_CHARS for c in w) or w.startswith(("-", "/", "~", "#", "..")):
        return None
    if re.match(r"^[A-Za-z]:[\\/]", w) or not re.match(r"^[\w.\-/]+$", w):
        return None
    w = re.sub(r":\d+(-\d+)?$", "", w)          # file:line
    if "/" in w:
        return w if re.search(r"[A-Za-z]", w) and w.strip("/") else None
    ext = w.rsplit(".", 1)[-1].lower() if "." in w.strip(".") else ""
    return w if ext in FILE_EXT and len(w) > len(ext) + 1 else None


IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{3,}(\(\))?$")


def identifier_like(span: str) -> str | None:
    """A code name worth a text search: snake_case, camelCase or `name()`; not ALL_CAPS (often set outside the repo)."""
    s = span.strip()
    if not IDENT_RE.match(s):
        return None
    name = s[:-2] if s.endswith("()") else s
    if name.isupper():
        return None
    if s.endswith("()") or ("_" in name.strip("_") and name.lower() == name) or re.search(r"[a-z][A-Z]", name):
        return name
    return None


def package_scripts(start: Path, root: Path) -> set[str] | None:
    for d in (start, *start.parents):
        f = d / "package.json"
        if f.is_file():
            try:
                scripts = json.loads(f.read_text(encoding="utf-8")).get("scripts")
            except (OSError, ValueError, AttributeError):
                return None
            return set(scripts) if isinstance(scripts, dict) else set()
        if d == root:
            break
    return None


def make_targets(start: Path, root: Path, names: tuple[str, ...], pattern: str) -> set[str] | None:
    for d in (start, *start.parents):
        for name in names:
            f = d / name
            if f.is_file():
                text = f.read_text(encoding="utf-8", errors="replace")
                if re.search(r"(?m)^-?include\s|^import\s|^mod\s", text):
                    return None      # targets from other files — not checkable from this one
                return set(re.findall(pattern, text))
        if d == root:
            break
    return None


MAKE_PAT = r"(?m)^([A-Za-z0-9][\w.\-]*)\s*:(?!=)"
JUST_PAT = r"(?m)^@?([A-Za-z_][\w-]*)(?:\s+[^:=\n]*)?\s*:(?!=)"


def command_claim(words: list[str], doc: Path, root: Path) -> tuple[str, str] | None:
    """(claim, why) for a command whose script, target or recipe is not defined; None when it is or cannot be checked."""
    tool = words[0]
    if tool in ("npm", "pnpm", "yarn", "bun") and len(words) >= 2:
        if words[1] in ("run", "run-script"):
            name = words[2] if len(words) > 2 else ""
        elif words[1] in ("test", "start") or (tool != "npm" and words[1] not in JS_BUILTINS):
            name = words[1]
        else:
            return None
        if not name or name.startswith("-"):
            return None
        scripts = package_scripts(doc.parent, root)
        if scripts is not None and name not in scripts:
            return " ".join(words), f"package.json has no script \"{name}\""
        return None
    if tool in ("make", "just") and len(words) >= 2 and not words[1].startswith("-"):
        if tool == "make":
            targets = make_targets(doc.parent, root, ("GNUmakefile", "makefile", "Makefile"), MAKE_PAT)
        else:
            targets = make_targets(doc.parent, root, ("justfile", "Justfile", ".justfile"), JUST_PAT)
        if targets is not None and words[1] not in targets:
            return " ".join(words[:2]), f"{'the Makefile' if tool == 'make' else 'the justfile'} has no " \
                                        f"{'target' if tool == 'make' else 'recipe'} \"{words[1]}\""
    return None


def resolve(doc: Path, root: Path, path: str, names: dict[str, list[str]]) -> bool:
    p = path.rstrip("/")
    if "/" not in p:
        return (doc.parent / p).exists() or p in names
    for base in (doc.parent, *doc.parent.parents):
        if (base / p).exists():
            return True
        if base == root:
            break
    return (root / p).exists()


def worth_checking(doc: Path, root: Path, path: str) -> bool:
    """A path without an extension (`src/app/orders`) is checked only when its first segment exists — otherwise it is
    rather an identifier like `skill/scenario`. `.tf/` and `.claude/` are created by the factory on demand."""
    p = path.lstrip("./") if path.startswith("./") else path
    if p.startswith((".tf/", ".claude/")) or p in (".tf", ".claude"):
        return False
    if p.startswith(RECORD) and not (root / RECORD).is_dir():
        return False                          # the record is created on demand (project_record.py init)
    last = p.rstrip("/").rsplit("/", 1)[-1]
    if "/" in p.rstrip("/") and "." not in last:
        first = p.split("/")[0]
        return any((b / first).exists() for b in (doc.parent, *doc.parent.parents, root))
    return True


def note_claims(root: Path, doc: Path, names: dict[str, list[str]]):
    """Yields (line, kind, claim, why, path or None, name or None) for references in a note that no longer hold."""
    text = read(doc)
    if text is None:
        return
    lines = text.splitlines()
    for n, line in prose(lines, doc.name in INSTRUCTION_NAMES):
        if NEGATIVE_RE.search(line) or PLANNED_RE.search(line):
            continue
        refs: list[str] = []
        for span in SPAN_RE.findall(line):
            words = span.split()
            if not words:
                continue
            cmd = command_claim(words, doc, root)
            if cmd:
                yield n, "missing-command", cmd[0], cmd[1], None, None
                continue
            if len(words) == 1:
                ident = identifier_like(words[0])
                if ident:
                    yield n, "missing-identifier", ident, "", None, ident
                    continue
            for w in (words[1:] if len(words) > 1 else words):
                p = path_like(w)
                if p:
                    refs.append(p)
        refs += [l.split("#")[0] for l in LINK_RE.findall(line)
                 if "://" not in l and not l.startswith(("#", "mailto:")) and path_like(l.split("#")[0])]
        for ref in dict.fromkeys(refs):
            if worth_checking(doc, root, ref) and not resolve(doc, root, ref, names):
                yield n, "missing-path", ref, "", ref, None


# ── the scan ─────────────────────────────────────────────────────────────────────────────────────────────────────
def months_ago(ts: int, now: datetime) -> float:
    return (now - datetime.fromtimestamp(ts, tz=timezone.utc)).days / 30.44


def scan(root: Path, since_months: int, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    repo = is_repo(root)
    files = list(walk(root))
    names: dict[str, list[str]] = {}
    for p in files:
        names.setdefault(p.name, []).append(rel_of(root, p))
    notes = note_files(root, files)
    note_rels = [rel_of(root, p) for p in notes]
    cands: list[dict] = []

    def add(kind: str, rel: str, line: int, claim: str, why: str, facts: dict | None = None, archive: dict | None = None):
        if sum(1 for c in cands if c["kind"] == kind) >= MAX_PER_KIND:
            return
        c = {"id": "", "kind": kind, "file": rel, "line": line, "claim": claim, "why": why, "facts": facts or {}}
        if archive:
            c["archive"] = archive
        c["tracker_keys"] = sorted(set(KEY_RE.findall(claim)))
        cands.append(c)

    # 1. TODO / FIXME / HACK / XXX in tracked text files (not the factory's own files, not the archive)
    for rel in tracked(root, repo, files):
        if rel.startswith((".claude/", ".tf/")) or in_archive(rel) or any(part in SKIP_DIRS for part in rel.split("/")[:-1]):
            continue
        text = read(root / rel)
        if not text or not re.search(r"TODO|FIXME|HACK|XXX", text):
            continue
        hits = [(n, line) for n, line in enumerate(text.splitlines(), 1) if TODO_RE.search(line)]
        times = blame_times(root, rel, [n for n, _ in hits]) if repo else {}
        for n, line in hits:
            claim = line.strip()[:200]
            keys = sorted(set(KEY_RE.findall(line)))
            age = months_ago(times[n], now) if n in times else None
            facts = {"age_months": round(age, 1)} if age is not None else {}
            if n in times:
                facts["since"] = datetime.fromtimestamp(times[n], tz=timezone.utc).date().isoformat()
            if keys:
                add("todo-tracker", rel, n, claim, f"names {', '.join(keys)} — the issue may be closed; check its status "
                                                   "read-only", facts)
            elif age is not None and age >= since_months:
                add("todo-old", rel, n, claim, f"older than {since_months} months by git blame — old, not proven stale",
                    facts)

    # 2. paths, commands and names in notes that are not in the repository
    idents: dict[str, list[tuple[str, int]]] = {}
    for doc in notes:
        rel = rel_of(root, doc)
        for n, kind, claim, why, path, ident in note_claims(root, doc, names):
            if kind == "missing-identifier":
                idents.setdefault(ident, []).append((rel, n))
                continue
            facts = {}
            if path:
                fact = last_commit(root, path) if repo else None
                if fact:
                    facts = fact
                base = path.rstrip("/").rsplit("/", 1)[-1]
                elsewhere = [x for x in names.get(base, []) if not in_archive(x)][:3]
                if elsewhere:
                    facts["same_name_at"] = elsewhere
                parent = path.rstrip("/").rsplit("/", 1)[0] if "/" in path.rstrip("/") else ""
                if parent and (root / parent).is_dir():
                    facts["parent_now_has"] = sorted(x.name for x in (root / parent).iterdir()
                                                     if not x.name.startswith("."))[:8]
                why = "not in the repository" + (f"; moved to {facts['moved_to']} in {facts['commit']}"
                                                  if facts.get("moved_to") else
                                                  f"; last touched by {facts['commit']} ({facts['date']})"
                                                  if facts.get("commit") else "")
            add(kind, rel, n, claim, why, facts)
    if idents and repo:
        args = ["grep", "-F", "-o", "-h", "-I", "-w"]
        for name in idents:
            args += ["-e", name]
        args += ["--", "."] + [f":(exclude){r}" for r in note_rels] + [f":(exclude){ARCHIVE}"]
        found = set((git(root, *args, timeout=120) or "").split())
        for name, where in idents.items():
            if name in found:
                continue
            hits = log_hits(root, name, None, note_rels)
            for rel, n in where[:3]:
                add("missing-identifier", rel, n, name, "found in no tracked file outside the notes",
                    {"last_commits_with_name": hits} if hits else {})

    # 3. stale records: closed tasks, superseded artifacts, parked and lessons entries handled later
    changes = root / RECORD / "changes"
    closed_dirs = []
    for tj in sorted(changes.glob("*/task.json")) if changes.is_dir() else []:
        try:
            task = json.loads(tj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(task, dict) and (task.get("stage") == "closed" or task.get("closed")):
            folder = rel_of(root, tj.parent)
            closed_dirs.append(folder + "/")
            fact = last_commit(root, folder) if repo else None
            add("closed-task", folder, 0, f"task {tj.parent.name} — stage {task.get('stage')}",
                "the task is closed, its spec and plan still sit in the active area", fact or {},
                {"type": "folder", "path": folder})
    for doc in notes:
        rel = rel_of(root, doc)
        if any(rel.startswith(d) for d in closed_dirs):
            continue
        text = read(doc) or ""
        head = re.match(r"^---\n(.*?)\n---", text, re.S)
        status = re.search(r"(?m)^status:\s*(\w+)", head.group(1)) if head else None
        if status and status.group(1) in ("superseded", "rejected"):
            add("superseded-artifact", rel, 1, f"status: {status.group(1)}",
                f"a {status.group(1)} artifact outside {ARCHIVE}/ — the record keeps those in the archive",
                {}, {"type": "file", "path": rel, "sha": sha(text)})
    for doc in notes:
        rel = rel_of(root, doc)
        if doc.name not in ("parked.md", "lessons.md") or any(rel.startswith(d) for d in closed_dirs):
            continue
        lines = (read(doc) or "").splitlines()
        entries = list(list_entries(lines))
        times = blame_times(root, rel, [a for a, _ in entries]) if repo else {}
        for a, b in entries:
            body = "\n".join(lines[a - 1:b])
            when = DATE_RE.search(body)
            since = when.group(1) if when else (datetime.fromtimestamp(times[a], tz=timezone.utc).date().isoformat()
                                                 if a in times else None)
            terms = [t for t in dict.fromkeys(SPAN_RE.findall(body)) if len(t) >= 4 and len(t) <= 80][:3]
            keys = sorted(set(KEY_RE.findall(body)))
            hits = []
            if repo:
                for t in terms:
                    hits += [h for h in log_hits(root, t, since, [rel, ARCHIVE]) if h not in hits]
            if not hits and not keys:
                continue
            why = []
            if hits:
                why.append("its subject shows up in later commits")
            if keys:
                why.append(f"names {', '.join(keys)} — check the status read-only")
            add("record-entry", rel, a, lines[a - 1].strip()[:200], "; ".join(why),
                {"since": since, "terms": terms, "later_commits": hits[:3]} if since or hits else {"terms": terms},
                {"type": "entry", "path": rel, "start": a, "end": b, "sha": sha(body)})

    order = ["closed-task", "superseded-artifact", "record-entry", "missing-path", "missing-command",
             "missing-identifier", "todo-tracker", "todo-old"]
    cands.sort(key=lambda c: (order.index(c["kind"]), c["file"], c["line"]))
    for i, c in enumerate(cands, 1):
        c["id"] = f"S-{i:02d}"
    keys: dict[str, list[str]] = {}
    for c in cands:
        for k in c["tracker_keys"]:
            keys.setdefault(k, []).append(c["id"])
    return {"root": root.as_posix(), "date": now.date().isoformat(), "git": repo, "since_months": since_months,
            "notes_scanned": note_rels, "candidates": cands, "tracker_keys": keys}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def list_entries(lines: list[str]):
    """(first, last) line numbers of top-level list items with their indented continuation lines."""
    start = None
    for n, line in enumerate(lines, 1):
        if re.match(r"^[-*] \S", line):
            if start:
                yield start, end
            start, end = n, n
        elif start and line.startswith((" ", "\t")) and line.strip():
            end = n
        elif start:
            yield start, end
            start = None
    if start:
        yield start, end


# ── output ───────────────────────────────────────────────────────────────────────────────────────────────────────
def where(c: dict) -> str:
    return f"{c['file']}:{c['line']}" if c["line"] else c["file"]


def fact_text(f: dict) -> str:
    bits = []
    if f.get("moved_to"):
        bits.append(f"moved to {f['moved_to']} ({f.get('commit')})")
    elif f.get("commit"):
        bits.append(f"last commit {f['commit']} {f.get('date', '')} \"{f.get('subject', '')}\"")
    if f.get("same_name_at"):
        bits.append("same name at " + ", ".join(f["same_name_at"]))
    if f.get("parent_now_has"):
        bits.append("the parent now has " + ", ".join(f["parent_now_has"]))
    if f.get("age_months") is not None:
        bits.append(f"{f['age_months']} months old (since {f.get('since')})")
    if f.get("later_commits"):
        bits.append("later commits: " + " | ".join(f["later_commits"]))
    if f.get("last_commits_with_name"):
        bits.append("commits with the name: " + " | ".join(f["last_commits_with_name"]))
    return "; ".join(bits)


def line_of(c: dict) -> str:
    facts = fact_text(c["facts"])
    arch = " — archivable" if c.get("archive") else ""
    return f"- [{c['id']}] {c['kind']} — {where(c)} — `{c['claim']}` — {c['why']}" + (f" — git: {facts}" if facts else "") + arch


def render(res: dict) -> str:
    out = [f"Sweep scan — {res['root']} — {res['date']}",
           f"Candidates: {len(res['candidates'])} · notes scanned: {len(res['notes_scanned'])} · git: "
           f"{'yes' if res['git'] else 'no (no git facts, no TODO age)'}"]
    out += [line_of(c) for c in res["candidates"]] or ["- none"]
    if res["tracker_keys"]:
        out += ["", "Tracker keys to check read-only (status: open / closed / unknown):"]
        out += [f"- {k} — {', '.join(ids)}" for k, ids in sorted(res["tracker_keys"].items())]
    out += ["", "These are candidates, not verdicts: every one needs evidence (the core-sweep skill, phases 2–3)."]
    return "\n".join(out)


def skeleton(res: dict, json_rel: str) -> str:
    rows = [line_of(c) + " — verification: pending" for c in res["candidates"]]
    keys = [f"- {k} — {', '.join(ids)} — status: unknown" for k, ids in sorted(res["tracker_keys"].items())]
    return "\n".join([
        f"# Sweep report — {res['date']}", "",
        f"Scan: {json_rel}",
        f"Verdict: 0 stale · 0 conflicts · {len(rows)} uncertain", "",
        "## Stale", "", "- none", "",
        "## Conflicts", "", "- none", "",
        "## Uncertain", "", *(rows or ["- none"]), "",
        "## Tracker keys", "", *(keys or ["- none"]), "",
        "## Refuted (kept as is)", "", "- none", ""])


# ── apply ────────────────────────────────────────────────────────────────────────────────────────────────────────
def section_ids(text: str, title: str) -> list[str]:
    m = re.search(rf"(?ms)^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text)
    return re.findall(r"^- \[(S-\d+)\]", m.group(1), re.M) if m else []


def apply(root: Path, report: Path, approve: list[str]) -> int:
    try:
        text = report.read_text(encoding="utf-8")
    except OSError:
        print(f"✗ no report {report.as_posix()} — run `sweep_scan.py scan --write` first")
        return 2
    m = re.search(r"(?m)^Scan: (\S+)$", text)
    data_path = root / m.group(1) if m else report.with_suffix(".json")
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"✗ no scan data {data_path.as_posix()} next to the report")
        return 2
    by_id = {c["id"]: c for c in data.get("candidates", [])}
    stale = set(section_ids(text, "Stale"))
    day = data.get("date") or date.today().isoformat()
    dest_root = root / SWEEP_ARCHIVE / day
    refused, moved, by_hand = [], [], []
    for cid in approve:
        c = by_id.get(cid)
        if not c:
            refused.append(f"{cid}: not in the scan")
            continue
        if cid not in stale:
            refused.append(f"{cid}: not in the report's \"## Stale\" section — only verified stale items move")
            continue
        arch = c.get("archive")
        if not arch:
            by_hand.append(f"{cid}: {c['kind']} at {where(c)} — a code or instruction edit, make it by hand")
            continue
        src = root / arch["path"]
        if arch["type"] == "folder":
            if not src.is_dir():
                refused.append(f"{cid}: {arch['path']} is gone since the scan")
                continue
            dst = dest_root / arch["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(f"{cid}: {arch['path']} → {rel_of(root, dst)}")
        elif arch["type"] == "file":
            body = read(src)
            if body is None or sha(body) != arch["sha"]:
                refused.append(f"{cid}: {arch['path']} changed since the scan — run the scan again")
                continue
            dst = dest_root / arch["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(f"{cid}: {arch['path']} → {rel_of(root, dst)}")
        else:
            moved_entry = move_entry(root, src, arch, dest_root / arch["path"], cid)
            (moved if moved_entry.startswith(cid + ": ") and "→" in moved_entry else refused).append(moved_entry)
    for x in moved:
        print(f"✓ {x}")
    for x in by_hand:
        print(f"• {x}")
    for x in refused:
        print(f"✗ {x}")
    if moved:
        ensure_archive_files(root)
        with report.open("a", encoding="utf-8") as fh:
            fh.write("\n## Applied\n\n" + "\n".join(f"- {x}" for x in moved) + "\n")
        print(f"Next: the by-hand edits above (if any), then one commit — git add -A {RECORD} {report_rel(root, report)} "
              f"&& git commit -m \"chore(sweep): archive stale notes\"")
    return 1 if refused else 0


def report_rel(root: Path, report: Path) -> str:
    try:
        return report.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return report.as_posix()


def move_entry(root: Path, src: Path, arch: dict, dst: Path, cid: str) -> str:
    """Cuts a list entry out of parked.md / lessons.md and appends it to the archived copy, with its origin."""
    text = read(src)
    if text is None:
        return f"{cid}: {arch['path']} is gone since the scan"
    lines = text.splitlines(keepends=True)
    a, b = arch["start"], arch["end"]
    body = "".join(lines[a - 1:b]).rstrip("\n")
    if sha("\n".join(x.rstrip("\n").rstrip("\r") for x in lines[a - 1:b])) != arch["sha"]:
        return f"{cid}: {arch['path']}:{a} changed since the scan — run the scan again"
    src.write_text("".join(lines[:a - 1] + lines[b:]), encoding="utf-8")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("a", encoding="utf-8") as fh:
        fh.write(f"{body}\n  (archived by the sweep from {arch['path']}:{a})\n")
    return f"{cid}: {arch['path']}:{a}-{b} → {rel_of(root, dst)}"


ARCHIVE_README = """# Archived by the sweep — not current

Notes, specs and plans that a sweep (the core-sweep skill) found no longer true, moved here with the human's consent.
Agents do not read this folder: the guard_paths hook blocks Read and Edit here, and `.ignore` keeps it out of searches.
A human who needs an old note reads it directly, or starts the agent with TF_ARCHIVE_READ=1.
"""


def ensure_archive_files(root: Path) -> None:
    base = root / SWEEP_ARCHIVE
    base.mkdir(parents=True, exist_ok=True)
    if not (base / "README.md").exists():
        (base / "README.md").write_text(ARCHIVE_README, encoding="utf-8")
    if not (base / ".ignore").exists():   # ripgrep (the Grep tool) skips everything below this folder
        (base / ".ignore").write_text("*\n", encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stale notes, plans and rules — candidates with evidence (core-sweep).")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("scan")
    s.add_argument("--root", default=".")
    s.add_argument("--json", action="store_true")
    s.add_argument("--since-months", type=int, default=12)
    s.add_argument("--write", action="store_true", help="save .tf/reports/sweep-<date>.json and the report skeleton .md")
    a = sub.add_parser("apply")
    a.add_argument("report")
    a.add_argument("--approve", required=True, help="comma-separated ids approved by the human, e.g. S-03,S-07")
    a.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"✗ no folder {args.root}")
        return 2
    if args.cmd == "apply":
        ids = [x.strip() for x in args.approve.split(",") if x.strip()]
        if not ids:
            print("✗ --approve needs at least one id")
            return 2
        report = Path(args.report)
        return apply(root, report if report.is_absolute() else root / report, ids)
    res = scan(root, args.since_months)
    if args.write:
        out = root / ".tf" / "reports"
        out.mkdir(parents=True, exist_ok=True)
        jpath, mpath = out / f"sweep-{res['date']}.json", out / f"sweep-{res['date']}.md"
        jpath.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        mpath.write_text(skeleton(res, rel_of(root, jpath)), encoding="utf-8")
        print(f"✓ {rel_of(root, jpath)} and {rel_of(root, mpath)} ({len(res['candidates'])} candidates)")
    print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else render(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
