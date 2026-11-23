#!/usr/bin/env python3
"""Tests of decision_publish.py: project decisions published to the suite index in pdi (D3, contract 0.17.0)."""
import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REL_WORK = Path(".claude") / "hooks" / "decision_publish.py"
REL_SRC = Path("modes") / "mode-pdi" / "hooks" / "decision_publish.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL_WORK).is_file() or (p / REL_SRC).is_file()), None)
HOOK = (ROOT / REL_WORK) if ROOT and (ROOT / REL_WORK).is_file() else ((ROOT / REL_SRC) if ROOT else None)
FIX = next((p / "modes" / "mode-pdi" / "tests" / "fixtures" / "pdi-contract" for p in Path(__file__).resolve().parents
            if (p / "modes" / "mode-pdi" / "tests" / "fixtures" / "pdi-contract").is_dir()),
           Path(__file__).resolve().parent / "fixtures" / "pdi-contract")
SECRET = "sekret-tf"  # noqa: S105 — test secret

REGISTER = """---
artifact: decisions
phase: meta
status: accepted
version: 1
author: system
created: 2026-11-01
updated: 2026-11-02
inputs: []
---
# Decision register

| ID | Date | Decision | Rationale (1 sentence) | Status | Author | Details |
|---|---|---|---|---|---|---|
| D-001 | 2026-11-01 | Postgres as the event queue | One database less to run | accepted | Ola | 04-architecture/adr/0001-queue.md |
| D-002 | 2026-11-02 | Retry payments three times | Card networks allow it | proposed | Ola | — |
"""
ADR = """---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz
created: 2026-11-01
updated: 2026-11-01
inputs: []
---
# 0001. Event queue on Postgres

## Context
Order events need a queue.

## Decision
Use Postgres with SKIP LOCKED instead of Redis Streams.
The database is already in the stack.

## Options considered
- Postgres — no new service
- Redis Streams — a new service
## Consequences
"""


class Receiver(BaseHTTPRequestHandler):
    got: list = []
    status = 200

    def do_POST(self) -> None:  # noqa: N802 — http.server API
        body = self.rfile.read(int(self.headers["content-length"]))
        ts, sig = self.headers["x-pdi-timestamp"], self.headers["x-pdi-signature"]
        good = "v1=" + hmac.new(SECRET.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        event = json.loads(body)
        Receiver.got.append({"path": self.path, "event": self.headers["x-pdi-event"], "signed": sig == good,
                             "body": event})
        self.send_response(Receiver.status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        if Receiver.status < 300:
            number = len(Receiver.got)
            self.wfile.write(json.dumps({"status": "recorded", "item": None, "decision": f"DEC-{number:04d}"}).encode())
        else:
            self.wfile.write(json.dumps({"error": "refused"}).encode())

    def log_message(self, *args) -> None:  # noqa: D102 — quiet
        pass


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True)


def run_hook(project: Path, env: dict, event: str = "SessionStart", args: tuple = ()) -> subprocess.CompletedProcess:
    stdin = "" if args else json.dumps({"hook_event_name": event, "session_id": "s-1", "cwd": str(project)})
    full = {"PATH": os.environ.get("PATH", ""), "HOME": str(project), "CLAUDE_PROJECT_DIR": str(project), **env}
    if not (HOOK.parent / "hook_errors.py").is_file():
        full["PYTHONPATH"] = str(ROOT / "core" / "hooks")   # source tree: the core hooks live apart from the mode's
    return subprocess.run([sys.executable, str(HOOK), *args], input=stdin, capture_output=True, text=True, env=full,
                          cwd=project, timeout=60)


def main() -> int:
    if HOOK is None:
        print("✗ nie znaleziono decision_publish.py")
        return 1
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    srv = HTTPServer(("127.0.0.1", 0), Receiver)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    on = {"PDI_EVENTS_URL": f"http://127.0.0.1:{srv.server_address[1]}", "PDI_TF_SIGNING_SECRET": SECRET}

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        git(project, "init", "-q")
        git(project, "config", "user.name", "Ola")
        git(project, "config", "user.email", "ola@example.com")
        git(project, "remote", "add", "origin", "git@github.com:dbqm45/sklep.git")
        rec = project / "docs" / "project"
        (rec / "04-architecture" / "adr").mkdir(parents=True)
        (rec / "decisions.md").write_text(REGISTER, encoding="utf-8")
        (rec / "04-architecture" / "adr" / "0001-queue.md").write_text(ADR, encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "decisions")
        head = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

        # P-1: off without the pdi address and secret, or with TF_DECISION_PUBLISH=0
        Receiver.got = []
        r1 = run_hook(project, {})
        r2 = run_hook(project, {**on, "TF_DECISION_PUBLISH": "0"})
        check(r1.returncode == 0 and r2.returncode == 0 and Receiver.got == [], f"P-1: off: {Receiver.got}")

        # P-2: accepted register rows and accepted ADRs are published; proposals are not
        Receiver.got = []
        r = run_hook(project, on)
        check(r.returncode == 0, f"P-2: exit {r.returncode} {r.stderr}")
        refs = sorted(g["body"]["payload"]["ref"] for g in Receiver.got)
        check(refs == ["ADR-0001", "D-001"], f"P-2: published {refs}")
        check(all(g["signed"] and g["path"] == "/events/tf" and g["event"] == "decision.recorded" for g in Receiver.got),
              "P-2: signed decision.recorded to /events/tf")
        by_ref = {g["body"]["payload"]["ref"]: g["body"] for g in Receiver.got}
        d1 = by_ref.get("D-001", {}).get("payload", {})
        check(d1.get("statement") == "Postgres as the event queue" and d1.get("why") == "One database less to run"
              and d1.get("decided_by") == "Ola" and d1.get("drafted_by") == "human"
              and d1.get("decision_type") == "project.decision" and d1.get("kind") == "other", f"P-2: row payload {d1}")
        origin = d1.get("origin", {})
        check(origin.get("app") == "tf" and origin.get("scope") == "dbqm45/sklep" and origin.get("local_id") == "D-001"
              and origin.get("path") == "docs/project/decisions.md" and origin.get("commit") == head
              and origin.get("url") == f"https://github.com/dbqm45/sklep/blob/{head}/docs/project/decisions.md",
              f"P-2: origin {origin}")
        check(by_ref.get("D-001", {}).get("occurred_at") == "2026-11-01T00:00:00Z", "P-2: occurred_at is the decision day")
        adr = by_ref.get("ADR-0001", {}).get("payload", {})
        check(adr.get("statement") == "Event queue on Postgres" and adr.get("kind") == "technical"
              and adr.get("decision_type") == "architecture.decision" and adr.get("decided_by") == "tomasz"
              and adr.get("why", "").startswith("Use Postgres with SKIP LOCKED")
              and adr.get("origin", {}).get("path") == "docs/project/04-architecture/adr/0001-queue.md",
              f"P-2: ADR payload {adr}")

        # P-3: envelope and payload keys follow the contract example (0.17.0)
        ex = json.loads((FIX / "event-decision.recorded.json").read_text(encoding="utf-8"))
        schema = json.loads((FIX / "event.schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["$defs"]["decision_recorded"]["properties"])
        required = set(schema["$defs"]["decision_recorded"]["required"])
        for g in Receiver.got:
            b = g["body"]
            check(set(b) == set(ex) and b["contract_version"] == ex["contract_version"] and b["source"] == "tf",
                  f"P-3: envelope like the example: {sorted(b)}")
            check(required <= set(b["payload"]) <= allowed, f"P-3: payload keys {sorted(b['payload'])}")

        # P-4: the next session sends nothing; the DEC numbers from pdi are kept outside git
        Receiver.got = []
        run_hook(project, on, "SessionEnd")
        check(Receiver.got == [], f"P-4: nothing new: {Receiver.got}")
        sent = json.loads((project / ".tf" / "cache" / "decision-publish" / "sent.json").read_text(encoding="utf-8"))
        check(sorted(v.get("decision") for v in sent.values()) == ["DEC-0001", "DEC-0002"], f"P-4: state {sent}")
        status = subprocess.run(["git", "-C", str(project), "status", "--porcelain"], capture_output=True, text=True)
        check(".tf" not in status.stdout or "?? .tf/" in status.stdout, "P-4: state outside tracked files")

        # P-5: a changed row is a new event (new version in pdi); a new commit alone is not
        Receiver.got = []
        text = (rec / "decisions.md").read_text(encoding="utf-8").replace("One database less to run",
                                                                          "One database less to run and back up")
        (rec / "decisions.md").write_text(text, encoding="utf-8")
        git(project, "commit", "-qam", "edit")
        run_hook(project, on)
        refs = [g["body"]["payload"]["ref"] for g in Receiver.got]
        check(refs == ["D-001"], f"P-5: only the changed decision: {refs}")
        first_id = by_ref.get("D-001", {}).get("id")
        check(bool(Receiver.got) and Receiver.got[0]["body"]["id"] != first_id, "P-5: a new event id")

        # P-6: pdi down (5xx) — nothing recorded, the same event goes again next time
        Receiver.got = []
        Receiver.status = 503
        (rec / "decisions.md").write_text(text.replace("| proposed |", "| accepted |"), encoding="utf-8")
        run_hook(project, on)
        failed = [g["body"]["id"] for g in Receiver.got]
        Receiver.status = 200
        Receiver.got = []
        run_hook(project, on)
        check(failed and [g["body"]["id"] for g in Receiver.got] == failed, f"P-6: resent {failed}")

        # P-7: refused (4xx) — kept with the reason, not resent while the content is the same
        Receiver.got = []
        Receiver.status = 400
        (rec / "decisions.md").write_text(text.replace("| proposed |", "| accepted |").replace("three times", "twice"),
                                          encoding="utf-8")
        run_hook(project, on)
        Receiver.status = 200
        sent_before = len(Receiver.got)
        run_hook(project, on)
        check(sent_before == 1 and len(Receiver.got) == 1, f"P-7: not resent after 400: {len(Receiver.got)}")
        errors = project / ".tf" / "logs" / "hook-errors.jsonl"
        check(errors.is_file() and "400" in errors.read_text(encoding="utf-8"), "P-7: the refusal is logged")

        # P-8: --dry-run prints the events and sends nothing
        Receiver.got = []
        shutil_state = project / ".tf" / "cache" / "decision-publish" / "sent.json"
        shutil_state.unlink()
        r = run_hook(project, on, args=("--dry-run",))
        printed = json.loads(r.stdout or "[]")
        check(r.returncode == 0 and Receiver.got == [] and {e["payload"]["ref"] for e in printed} >= {"D-001", "ADR-0001"},
              f"P-8: dry run {r.stdout[:200]} {r.stderr}")
        check(not shutil_state.exists(), "P-8: dry run keeps no state")

    srv.shutdown()
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów publikacji decyzji (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
