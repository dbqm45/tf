#!/usr/bin/env python3
"""
SessionStart: a read-only local copy of the suite decision index from pdi (D8), searched with the local decisions.

  python3 .claude/hooks/decision_cache.py                 # as the hook: refresh, one line into the session context
  python3 .claude/hooks/decision_cache.py refresh|status  # by hand
  python3 .claude/hooks/decision_cache.py search <words>  # the suite copy and docs/project/decisions.md + ADRs

The copy comes from `pdi-records changes` (pdi D7) run locally — today the pdi register lives on the owner's machine;
an HTTP API comes with the pdi service (DA4). The command is TF_DECISION_CACHE_CMD (e.g.
`uv run --directory ~/pdi pdi-records`), default `pdi-records`, with the register from PDI_REGISTRY_PATH. Opt-in: on
only when one of the two is set; TF_DECISION_CACHE=0 turns it off.

Files: .tf/cache/suite-decisions/DEC-n.md (outside git) — the Decision Record file from pdi as is, with a "copy, do
not edit" comment under the header, read-only; meta.json keeps the cursor, the fetch time and a hash per file. A copy
edited by hand is found by its hash and the whole copy is fetched again. Decisions of this repo published by the
factory itself (origin app tf, scope = this repo) are left out — they are here already. Superseded decisions stay
with their status, so they never look binding. Without pdi the last copy stays and the context line says how old it
is; the session is never blocked (errors to .tf/logs/hook-errors.jsonl, exit 0). Plan:
docs/plans/2026-11-23-d8-pamiec-decyzji-suity.md. Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOOK = "decision_cache"
CACHE = Path(".tf") / "cache" / "suite-decisions"
REGISTER = Path("docs") / "project" / "decisions.md"
ADR_DIR = Path("docs") / "project" / "04-architecture" / "adr"
MARK = "<!-- kopia z indeksu suity, nie edytuj (pdi): decyzję zmienia aplikacja, z której pochodzi -->"
BUDGET_S = 8           # whole refresh as a hook (the hook timeout is 10 s)
MAX_PAGES = 50
ID = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
GITHUB = re.compile(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$")
WORD = re.compile(r"\w{2,}")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record   # core hook in the same directory
except ImportError:   # the hook copied alone: errors go nowhere, the session still never breaks
    def record(hook: str, exc: BaseException) -> None:  # noqa: ARG001
        return None


def now() -> datetime:
    return datetime.now(timezone.utc)


def enabled(env: dict[str, str]) -> bool:
    return env.get("TF_DECISION_CACHE", "1") != "0" and bool(env.get("TF_DECISION_CACHE_CMD") or env.get("PDI_REGISTRY_PATH"))


def repo_scope(root: Path) -> str:
    r = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], capture_output=True, text=True, timeout=10)
    found = GITHUB.match(r.stdout.strip()) if r.returncode == 0 else None
    return found.group(1) if found else root.resolve().name


def load_meta(cache: Path) -> dict:
    path = cache / "meta.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save_meta(cache: Path, meta: dict) -> None:
    (cache / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def with_mark(text: str) -> str:
    """The pdi file with the copy marker right under the Decision Record header (the header stays first)."""
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        head, body = text[4:].split("\n---\n", 1)
        return f"---\n{head}\n---\n{MARK}\n{body}"
    return f"{MARK}\n{text}"


def edited_by_hand(cache: Path, meta: dict) -> list[str]:
    files = meta.get("files", {})
    return sorted(i for i, entry in files.items()
                  if not (cache / f"{i}.md").is_file() or sha((cache / f"{i}.md").read_text(encoding="utf-8")) != entry["sha"])


def fetch(env: dict[str, str], since: str | None, deadline: float) -> tuple[list[dict], str | None]:
    """All pages after `since`; raises on a failing command or when the time budget runs out."""
    cmd = shlex.split(env.get("TF_DECISION_CACHE_CMD") or "pdi-records")
    page = env.get("TF_DECISION_CACHE_PAGE", "200")
    found: list[dict] = []
    cursor = since
    for _ in range(MAX_PAGES):
        args = ["changes", *(["--since", cursor] if cursor else []), "--limit", page]
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("refresh took too long")
        r = subprocess.run([*cmd, *args], capture_output=True, text=True, timeout=left, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"pdi-records changes exited {r.returncode}")
        answer = json.loads(r.stdout)
        found += answer["decisions"]
        cursor = answer.get("next") or cursor
        if answer.get("complete", True):
            return found, cursor
    raise RuntimeError("too many pages")


def refresh(root: Path, env: dict[str, str], budget_s: float = BUDGET_S) -> dict:
    """Brings the copy up to date; returns {"ok": bool, "meta": meta}. Never raises for pdi problems."""
    cache = root / CACHE
    cache.mkdir(parents=True, exist_ok=True)
    meta = load_meta(cache)
    changed = edited_by_hand(cache, meta)
    if changed:
        record(HOOK, RuntimeError(f"edited by hand, fetched again from pdi: {', '.join(changed)}"))
        meta = {}
    own = repo_scope(root)
    try:
        decisions, cursor = fetch(env, meta.get("next"), time.monotonic() + budget_s)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as e:
        record(HOOK, e)
        return {"ok": False, "meta": meta}
    files = meta.setdefault("files", {})
    for d in decisions:
        ident = str(d.get("id", ""))
        origin = d.get("origin") or {}
        if not ID.match(ident) or not isinstance(d.get("text"), str):
            continue
        path = cache / f"{ident}.md"
        if origin.get("app") == "tf" and origin.get("scope") == own:
            if path.exists():
                path.chmod(0o644)
                path.unlink()
            files.pop(ident, None)
            continue
        text = with_mark(d["text"])
        if path.exists():
            path.chmod(0o644)
        path.write_text(text, encoding="utf-8")
        path.chmod(0o444)
        link = origin.get("url") or (d.get("source") or {}).get("url") or ""
        files[ident] = {"sha": sha(text), "status": d.get("status", ""), "statement": d.get("statement", ""),
                        "app": origin.get("app") or "pdi", "link": link if str(link).startswith("http") else ""}
    meta["next"] = cursor
    meta["fetched_at"] = now().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_meta(cache, meta)
    return {"ok": True, "meta": meta}


def plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return f"{n} {one}"
    return f"{n} {few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many}"


def age(fetched_at: str | None) -> str:
    if not fetched_at:
        return "nigdy nie pobrana"
    then = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    minutes = int((now() - then).total_seconds() // 60)
    if minutes < 60:
        return f"kopia z {fetched_at} ({minutes} min temu)"
    hours = minutes // 60
    return f"kopia z {fetched_at} ({hours} h temu)" if hours < 48 else f"kopia z {fetched_at} ({hours // 24} dni temu)"


def status_line(meta: dict, ok: bool) -> str:
    files = meta.get("files", {}).values()
    active = sum(1 for f in files if f.get("status") == "recorded")
    superseded = sum(1 for f in files if f.get("status") == "superseded")
    counts = (f"{plural(active, 'obowiązująca', 'obowiązujące', 'obowiązujących')}, "
              f"{plural(superseded, 'zastąpiona', 'zastąpione', 'zastąpionych')}")
    state = age(meta.get("fetched_at")) if ok else f"nieaktualna, pdi niedostępne — {age(meta.get('fetched_at'))}"
    return (f"Decyzje suity (pdi): {counts}; {state}. Przed planem zadania: "
            f"python3 .claude/hooks/decision_cache.py search <słowa>")


def local_rows(root: Path) -> list[tuple[str, str, str]]:
    """(id, status, text) of local decisions: register rows and ADRs."""
    out = []
    reg = root / REGISTER
    if reg.is_file():
        for line in reg.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*(D-\d+)\s*\|(.*)\|\s*$", line)
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                out.append((m.group(1), cells[3] if len(cells) > 3 else "", " ".join(cells[1:3])))
    adr = root / ADR_DIR
    for path in sorted(adr.glob("[0-9]*.md")) if adr.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        status = re.search(r"^status:\s*(\S+)", text, re.M)
        out.append((f"ADR-{path.name[:4]}", status.group(1) if status else "", text))
    return out


def search(root: Path, words: list[str]) -> str:
    wanted = [w.lower() for w in WORD.findall(" ".join(words))]
    cache = root / CACHE
    meta = load_meta(cache)
    lines = [f"Decyzje suity: {age(meta.get('fetched_at'))}."]
    for ident, entry in sorted(meta.get("files", {}).items()):
        path = cache / f"{ident}.md"
        text = path.read_text(encoding="utf-8").lower() if path.is_file() else ""
        if wanted and all(w in text for w in wanted):
            state = "zastąpiona" if entry.get("status") == "superseded" else "obowiązuje"
            link = f" — {entry['link']}" if entry.get("link") else ""
            lines.append(f"- {ident} [{entry.get('app')}, {state}] {entry.get('statement')}{link} ({path.relative_to(root)})")
    for ident, status, text in local_rows(root):
        if wanted and all(w in text.lower() for w in wanted):
            lines.append(f"- {ident} [lokalnie, {status or 'bez statusu'}] {text.strip().splitlines()[0][:160]}")
    if len(lines) == 1:
        lines.append("- nic nie pasuje")
    return "\n".join(lines)


def main(argv: list[str], stdin: str, env: dict[str, str]) -> int:
    root = Path(env.get("CLAUDE_PROJECT_DIR") or ".")
    command = argv[0] if argv else "hook"
    if command == "search":
        print(search(root, argv[1:]))
        return 0
    if command == "status":
        print(status_line(load_meta(root / CACHE), ok=True))
        return 0
    if not enabled(env):
        return 0
    if command == "hook":
        hook = json.loads(stdin) if stdin.strip() else {}
        root = Path(env.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or ".")
    result = refresh(root, env)
    print(status_line(result["meta"], result["ok"]))
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        raise SystemExit(main(sys.argv[1:], "" if sys.stdin.isatty() else sys.stdin.read(), dict(os.environ)))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — a hook never blocks the session
        record(HOOK, exc)
        raise SystemExit(0) from None
