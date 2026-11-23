#!/usr/bin/env python3
"""
SessionStart / Stop / SessionEnd: reports the session to pdi as one agent run (contract 0.15.0, DI Team board).

  SessionStart → run.started   (who started it: `git config user.name`; how: manual, or pdi for a phase run)
  Stop         → run.progress  (after each turn: in progress; the activity is the goal of the active .tf/wip/ checkpoint)
  SessionEnd   → run.finished  (done, with the duration)

The run id is `session-<Claude Code session id>`, so the three events form one card in pdi (`agent-runs/`).
A phase started by pdi (`phase_run.py run`) passes TF_RUN_TRIGGER=pdi, TF_RUN_CHANGE and TF_RUN_PHASE, so the run
carries the change and phase; a session started by hand carries neither, and pdi still shows it.

Opt-in, like the rest of mode-pdi: nothing is sent unless PDI_EVENTS_URL and PDI_TF_SIGNING_SECRET are set (the same
variables as phase_run.py); TF_RUN_REPORT=0 turns it off. Never blocks the session: a short timeout, every error goes to
.tf/logs/hook-errors.jsonl, exit code 0. Sends no prompt, code or file content: names, ids, times and the checkpoint's
title only. Standard library only.
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

HOOK = "run_report"
CONTRACT_VERSION = "0.17.0"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
TIMEOUT_S = 4
STATE_DIR = Path(".tf") / "cache" / "run-report"
RUN_ID = re.compile(r"[^A-Za-z0-9._-]")
KEY = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
ACTIVITY_MAX = 200

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record   # core hook in the same directory
except ImportError:   # the hook copied alone: errors go nowhere, the session still never breaks
    def record(hook: str, exc: BaseException) -> None:  # noqa: ARG001
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def enabled(env: dict[str, str]) -> bool:
    return env.get("TF_RUN_REPORT", "1") != "0" and bool(env.get("PDI_EVENTS_URL")) and bool(env.get("PDI_TF_SIGNING_SECRET"))


def run_id(session_id: str) -> str:
    """`session-<id>` within the contract's 1–128 safe characters."""
    return ("session-" + RUN_ID.sub("-", session_id or "unknown"))[:128]


def started_by(root: Path, env: dict[str, str]) -> dict:
    """The person from git; a phase started by pdi is an automation unless pdi names the person."""
    name = env.get("TF_RUN_STARTED_BY", "").strip()
    if not name:
        try:
            r = subprocess.run(["git", "-C", str(root), "config", "user.name"], capture_output=True, text=True, timeout=3)
            name = r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            name = ""
    if env.get("TF_RUN_TRIGGER") == "pdi" and not env.get("TF_RUN_STARTED_BY"):
        return {"name": "pdi", "kind": "automation"}
    return {"name": name or "unknown", "kind": "human"}


def activity(root: Path) -> str | None:
    """The goal of the newest active work checkpoint (.tf/wip/), in the person's own words; no prompt content."""
    try:
        from project_record import title, wip_items   # core hook in the same directory
        items = wip_items(root)
    except Exception:  # noqa: BLE001 — no checkpoint helper or a broken checkpoint: just no activity
        return None
    if not items:
        return None
    newest = max(items, key=lambda w: w["path"].stat().st_mtime)
    text = title(newest["body"], newest["slug"]).strip()
    return text[:ACTIVITY_MAX] or None


def scope(env: dict[str, str]) -> dict:
    out = {}
    if KEY.match(env.get("TF_RUN_CHANGE", "")):
        out["change"] = env["TF_RUN_CHANGE"]
    out["phase"] = env.get("TF_RUN_PHASE") or "session"
    return out


def build(kind: str, hook: dict, root: Path, env: dict[str, str], state: dict) -> dict:
    """The contract event for one hook call; `state` keeps what SessionStart knew (start time, person)."""
    rid = run_id(str(hook.get("session_id", "")))
    at = now_iso()
    payload: dict = {"run": rid, **scope(env)}
    if kind == "run.started":
        state.update(started_at=at, started_by=started_by(root, env))
        payload.update(started_by=state["started_by"], trigger="pdi" if env.get("TF_RUN_TRIGGER") == "pdi" else "manual")
    elif kind == "run.progress":
        payload["status"] = "in_progress"
        what = activity(root)
        if what:
            payload["activity"] = what
        if state.get("started_by"):
            payload["started_by"] = state["started_by"]
    else:
        payload["outcome"] = "done"
        if state.get("started_by"):
            payload["started_by"] = state["started_by"]
        if state.get("started_at"):
            begun = datetime.strptime(state["started_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            payload["duration_s"] = max(0, int((datetime.now(timezone.utc) - begun).total_seconds()))
    seq = state["seq"] = int(state.get("seq", 0)) + 1
    return {"id": f"{rid}-{seq}"[:128], "type": kind, "occurred_at": at, "source": "tf",
            "contract_version": CONTRACT_VERSION, "payload": payload}


def post(event: dict, env: dict[str, str]) -> int:
    """Signed like phase_run.post_event: `x-pdi-signature: v1=<HMAC-SHA256(secret, "<ts>.<body>")>`."""
    base = env["PDI_EVENTS_URL"].rstrip("/")
    url = urllib.parse.urlsplit(base)
    if not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS)):
        raise ValueError("PDI_EVENTS_URL must be https:// (http only for localhost)")
    body = json.dumps(event, ensure_ascii=False).encode()
    ts = str(int(time.time()))
    sig = "v1=" + hmac.new(env["PDI_TF_SIGNING_SECRET"].encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(f"{base}/events/tf", data=body, method="POST", headers={
        "content-type": "application/json", "x-pdi-timestamp": ts, "x-pdi-event": event["type"], "x-pdi-signature": sig})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310 — address checked above
        return resp.status


KINDS = {"SessionStart": "run.started", "Stop": "run.progress", "SessionEnd": "run.finished"}


def main(stdin: str, env: dict[str, str]) -> int:
    if not enabled(env):
        return 0
    hook = json.loads(stdin or "{}")
    kind = KINDS.get(str(hook.get("hook_event_name", "")))
    if kind is None:
        return 0
    root = Path(env.get("CLAUDE_PROJECT_DIR") or hook.get("cwd") or ".")
    state_file = root / STATE_DIR / f"{run_id(str(hook.get('session_id', '')))}.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.is_file() else {}
    if kind == "run.progress" and not state:
        return 0   # no start seen (reporting turned on mid-session): no card to update
    event = build(kind, hook, root, env, state)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if kind == "run.finished":
        state_file.unlink(missing_ok=True)
    else:
        state_file.write_text(json.dumps(state), encoding="utf-8")
    post(event, env)
    return 0


if __name__ == "__main__":
    try:
        for _stream in (sys.stdin, sys.stdout, sys.stderr):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass
        main(sys.stdin.read(), dict(os.environ))
    except Exception as e:  # noqa: BLE001 — reporting must never break the session; record() never raises
        record(HOOK, e)
    sys.exit(0)
