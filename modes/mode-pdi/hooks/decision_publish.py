#!/usr/bin/env python3
"""
SessionStart / SessionEnd: publishes the project's decisions to the suite decision index in pdi (D3, contract 0.17.0).

  docs/project/decisions.md          rows | D-NNN | date | decision | rationale | status | author | details |
  docs/project/04-architecture/adr/  NNNN-*.md with status accepted

Each decision becomes one `decision.recorded` event with its origin (app tf, the repo as scope, D-012 / ADR-0003,
the file, its last commit, a GitHub link). The files in the repo do not change: the event and the pdi index carry the
Decision Record format (owner's decision, 2026-11-23; tf docs/plans/2026-11-23-d3-publikacja-decyzji.md). Proposals,
rejected and superseded rows are not published. Decisions of a change (changes/CHG-n/decisions.md) keep their own path
(decision_record.py decision pending).

The event id comes from the scope, the local id and the content (without path, commit and url), so resending the same
decision returns the same DEC in pdi and an edited decision becomes a new version there. What pdi accepted is kept in
.tf/cache/decision-publish/sent.json (outside git); a network error or 5xx is retried next session, a 4xx is logged and
not retried until the decision changes.

Opt-in like the rest of mode-pdi: nothing is sent unless PDI_EVENTS_URL and PDI_TF_SIGNING_SECRET are set;
TF_DECISION_PUBLISH=0 turns it off. As a hook it never blocks the session (time budget, errors to
.tf/logs/hook-errors.jsonl, exit 0). By hand: `python3 .claude/hooks/decision_publish.py --dry-run` prints the events
and sends nothing. Standard library only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOOK = "decision_publish"
CONTRACT_VERSION = "0.19.0"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
TIMEOUT_S = 4
BUDGET_S = 7            # whole run as a hook (the hook timeout is 10 s); what is left goes next session
STATE = Path(".tf") / "cache" / "decision-publish" / "sent.json"
REGISTER = Path("docs") / "project" / "decisions.md"
ADR_DIR = Path("docs") / "project" / "04-architecture" / "adr"
NOT_DECISIONS = {"proposed", "draft", "rejected", "superseded", "withdrawn",
                 "proponowana", "propozycja", "szkic", "odrzucona", "zastąpiona", "wycofana"}
ROW = re.compile(r"^\|\s*(D-\d+)\s*\|(.*)\|\s*$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
GITHUB = re.compile(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$")
ORIGIN_NOT_CONTENT = ("path", "commit", "url")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record   # core hook in the same directory
except ImportError:   # the hook copied alone: errors go nowhere, the session still never breaks
    def record(hook: str, exc: BaseException) -> None:  # noqa: ARG001
        return None


def log_error(root: Path, message: str) -> None:  # noqa: ARG001 — the log path comes from CLAUDE_PROJECT_DIR
    """A refused or failed send in the hook error log (`tf doctor`); names and reasons only, never decision text."""
    record(HOOK, RuntimeError(message))


def enabled(env: dict[str, str]) -> bool:
    return (env.get("TF_DECISION_PUBLISH", "1") != "0" and bool(env.get("PDI_EVENTS_URL"))
            and bool(env.get("PDI_TF_SIGNING_SECRET")))


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else ""


def repo_scope(root: Path) -> tuple[str, bool]:
    """(owner/name, is GitHub) from the origin remote; without one, the directory name."""
    remote = git(root, "remote", "get-url", "origin")
    found = GITHUB.match(remote)
    if found:
        return found.group(1), True
    tail = re.sub(r"\.git$", "", remote.rstrip("/")).replace(":", "/").split("/")[-2:]
    return ("/".join(tail), False) if len(tail) == 2 and all(tail) else (root.resolve().name, False)


def front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    head = text[4:].split("\n---\n", 1)[0]
    out = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "-")):
            out[key.strip()] = value.strip().strip("'\"")
    return out


def section_paragraph(text: str, name: str) -> str:
    """The first paragraph of `## name` (lines joined), or ''."""
    m = re.search(rf"^## {re.escape(name)}\s*$\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return ""
    para = m.group(1).strip().split("\n\n", 1)[0]
    return " ".join(l.strip() for l in para.splitlines() if l.strip())[:2000]


def register_decisions(root: Path) -> list[dict]:
    path = root / REGISTER
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) < 5:
            continue
        day, statement, why, status, author = cells[:5]
        if status.lower() in NOT_DECISIONS or not statement:
            continue
        out.append({"local_id": m.group(1), "path": REGISTER.as_posix(), "day": day, "statement": statement,
                    "why": why, "decided_by": author or "unknown", "kind": "other",
                    "decision_type": "project.decision"})
    return out


def adr_decisions(root: Path) -> list[dict]:
    out = []
    for path in sorted((root / ADR_DIR).glob("[0-9]*.md")) if (root / ADR_DIR).is_dir() else []:
        text = path.read_text(encoding="utf-8")
        meta = front_matter(text)
        if meta.get("status") != "accepted":
            continue
        title = re.search(r"^#\s+(\d+)\.\s+(.+?)\s*$", text, re.M)
        if not title:
            continue
        why = section_paragraph(text, "Decision") or section_paragraph(text, "Context")
        out.append({"local_id": f"ADR-{int(title.group(1)):04d}", "path": path.relative_to(root).as_posix(),
                    "day": meta.get("updated") or meta.get("created") or "", "statement": title.group(2),
                    "why": why, "decided_by": meta.get("author") or "unknown", "kind": "technical",
                    "decision_type": "architecture.decision"})
    return out


def build(found: dict, root: Path, scope: str, github: bool) -> dict:
    """The decision.recorded event for one decision; the id depends on what the decision says, not where it lies."""
    origin = {"app": "tf", "scope": scope, "local_id": found["local_id"], "path": found["path"]}
    commit = git(root, "log", "-1", "--format=%H", "--", found["path"])
    if COMMIT.match(commit):
        origin["commit"] = commit
        if github:
            origin["url"] = f"https://github.com/{scope}/blob/{commit}/{found['path']}"
    payload = {"decision_type": found["decision_type"], "ref": found["local_id"], "origin": origin,
               "statement": found["statement"], "kind": found["kind"], "decided_by": found["decided_by"],
               "drafted_by": "human"}
    if found["why"]:
        payload["why"] = found["why"]
    content = {**{k: v for k, v in payload.items() if k != "origin"},
               "origin": {k: v for k, v in origin.items() if k not in ORIGIN_NOT_CONTENT}}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    day = found["day"] if DAY.match(found["day"]) else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {"id": f"tf-decision-{digest[:32]}", "type": "decision.recorded", "occurred_at": f"{day}T00:00:00Z",
            "source": "tf", "contract_version": CONTRACT_VERSION, "payload": payload}


def events(root: Path) -> list[dict]:
    scope, github = repo_scope(root)
    return [build(d, root, scope, github) for d in register_decisions(root) + adr_decisions(root)]


def post(event: dict, env: dict[str, str]) -> tuple[int, dict]:
    """Signed like run_report.post; returns (status, JSON answer). Raises on network errors."""
    base = env["PDI_EVENTS_URL"].rstrip("/")
    url = urllib.parse.urlsplit(base)
    if not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS)):
        raise ValueError("PDI_EVENTS_URL must be https:// (http only for localhost)")
    body = json.dumps(event, ensure_ascii=False).encode()
    ts = str(int(time.time()))
    sig = "v1=" + hmac.new(env["PDI_TF_SIGNING_SECRET"].encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(f"{base}/events/tf", data=body, method="POST", headers={
        "content-type": "application/json", "x-pdi-timestamp": ts, "x-pdi-event": event["type"], "x-pdi-signature": sig})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310 — address checked above
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, {}


def publish(root: Path, env: dict[str, str], budget_s: float | None) -> int:
    """Sends what pdi has not accepted yet; returns the number of events sent successfully."""
    state_file = root / STATE
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.is_file() else {}
    start, done = time.monotonic(), 0
    for event in events(root):
        key = f"{event['payload']['origin']['scope']}/{event['payload']['ref']}"
        if state.get(key, {}).get("event") == event["id"]:
            continue   # accepted or refused in this version already
        if budget_s is not None and time.monotonic() - start > budget_s:
            break      # the rest goes next session
        try:
            status, answer = post(event, env)
        except (OSError, ValueError) as e:
            log_error(root, f"{key}: not sent ({type(e).__name__}); retried next session")
            break
        if status >= 500:
            log_error(root, f"{key}: pdi answered {status}; retried next session")
            break
        entry = {"event": event["id"], "sent_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if status >= 400:
            entry["refused"] = status
            log_error(root, f"{key}: pdi refused with {status}; not retried until the decision changes")
        else:
            entry["decision"] = answer.get("decision")
            done += 1
        state[key] = entry
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return done


def main(argv: list[str], stdin: str, env: dict[str, str]) -> int:
    if "--dry-run" in argv:
        root = Path(env.get("CLAUDE_PROJECT_DIR") or ".")
        print(json.dumps(events(root), ensure_ascii=False, indent=1))
        return 0
    if not enabled(env):
        return 0
    hook = json.loads(stdin) if stdin.strip() else {}
    root = Path(env.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or ".")
    publish(root, env, BUDGET_S if hook else None)
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
