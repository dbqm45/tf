#!/usr/bin/env python3
"""Tests of the run_report.py hook: a session reported to pdi as one agent run (contract 0.15.0)."""
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

REL_WORK = Path(".claude") / "hooks" / "run_report.py"
REL_SRC = Path("modes") / "mode-pdi" / "hooks" / "run_report.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL_WORK).is_file() or (p / REL_SRC).is_file()), None)
HOOK = (ROOT / REL_WORK) if ROOT and (ROOT / REL_WORK).is_file() else ((ROOT / REL_SRC) if ROOT else None)
if HOOK is None:
    raise SystemExit("nie znaleziono run_report.py")
FIX = next((p / "modes" / "mode-pdi" / "tests" / "fixtures" / "pdi-contract" for p in Path(__file__).resolve().parents
            if (p / "modes" / "mode-pdi" / "tests" / "fixtures" / "pdi-contract").is_dir()),
           Path(__file__).resolve().parent / "fixtures" / "pdi-contract")
SECRET = "sekret-tf"  # noqa: S105 — test secret


class Receiver(BaseHTTPRequestHandler):
    got: list = []
    status = 200

    def do_POST(self) -> None:  # noqa: N802 — http.server API
        body = self.rfile.read(int(self.headers["content-length"]))
        ts, sig = self.headers["x-pdi-timestamp"], self.headers["x-pdi-signature"]
        good = "v1=" + hmac.new(SECRET.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        Receiver.got.append({"path": self.path, "event": self.headers["x-pdi-event"], "signed": sig == good,
                             "body": json.loads(body)})
        self.send_response(Receiver.status)
        self.end_headers()

    def log_message(self, *args) -> None:  # noqa: D102 — quiet
        pass


def run_hook(project: Path, event: str, env: dict, session: str = "abc-123") -> subprocess.CompletedProcess:
    stdin = json.dumps({"hook_event_name": event, "session_id": session, "cwd": str(project)})
    full = {"PATH": os.environ.get("PATH", ""), "HOME": str(project), "CLAUDE_PROJECT_DIR": str(project), **env}
    if HOOK.parent.name != "hooks" or not (HOOK.parent / "project_record.py").is_file():
        full["PYTHONPATH"] = str(ROOT / "core" / "hooks")   # source tree: the core hooks live apart from the mode's
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, env=full,
                          timeout=30)


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    srv = HTTPServer(("127.0.0.1", 0), Receiver)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    on = {"PDI_EVENTS_URL": url, "PDI_TF_SIGNING_SECRET": SECRET}

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        subprocess.run(["git", "-C", str(project), "config", "user.name", "Ola"], check=True)
        wip = project / ".tf" / "wip"
        wip.mkdir(parents=True)
        (wip / "retry.md").write_text("---\nstatus: active\n---\n# Retry a failed payment\n", encoding="utf-8")

        # R-1: off without the pdi address and secret, or with TF_RUN_REPORT=0 — nothing sent, exit 0
        Receiver.got = []
        r1 = run_hook(project, "SessionStart", {})
        r2 = run_hook(project, "SessionStart", {**on, "TF_RUN_REPORT": "0"})
        check(r1.returncode == 0 and r2.returncode == 0 and Receiver.got == [], f"R-1: off: {Receiver.got}")

        # R-2: a manual session: start → progress → finish, one run id, signed, to /events/tf
        Receiver.got = []
        for ev in ("SessionStart", "Stop", "SessionEnd"):
            r = run_hook(project, ev, on)
            check(r.returncode == 0, f"R-2: {ev} exit {r.returncode} {r.stderr}")
        types = [g["event"] for g in Receiver.got]
        check(types == ["run.started", "run.progress", "run.finished"], f"R-2: events {types}")
        check(all(g["signed"] and g["path"] == "/events/tf" for g in Receiver.got), "R-2: signed, /events/tf")
        bodies = [g["body"] for g in Receiver.got]
        runs = {b["payload"]["run"] for b in bodies}
        check(runs == {"session-abc-123"}, f"R-2: one run id: {runs}")
        check(len({b["id"] for b in bodies}) == 3, "R-2: three distinct event ids")
        if len(bodies) == 3:
            start, prog, end = (b["payload"] for b in bodies)
            check(start["started_by"] == {"name": "Ola", "kind": "human"} and start["trigger"] == "manual"
                  and start["phase"] == "session" and "change" not in start, f"R-2: start {start}")
            check(prog["status"] == "in_progress" and prog.get("activity") == "Retry a failed payment", f"R-2: progress {prog}")
            check(end["outcome"] == "done" and isinstance(end.get("duration_s"), int), f"R-2: finish {end}")
        state = project / ".tf" / "cache" / "run-report" / "session-abc-123.json"
        check(not state.exists(), "R-2: the session state is removed at the end")

        # R-3: the envelope and payload keys follow the contract examples (0.15.x)
        for b in bodies:
            ex = json.loads((FIX / f"event-{b['type']}.json").read_text(encoding="utf-8"))
            check(set(b) == set(ex) and b["contract_version"] == ex["contract_version"] and b["source"] == "tf",
                  f"R-3: envelope like the example: {sorted(b)} vs {sorted(ex)}")
            check(set(b["payload"]) <= set(ex["payload"]) | {"activity", "duration_s", "started_by"},
                  f"R-3: {b['type']} payload keys {sorted(b['payload'])}")

        # R-4: a phase started by pdi carries the change and phase; started by automation
        Receiver.got = []
        pdi = {**on, "TF_RUN_TRIGGER": "pdi", "TF_RUN_CHANGE": "CHG-12", "TF_RUN_PHASE": "delivery"}
        run_hook(project, "SessionStart", pdi, session="p-1")
        p = Receiver.got[0]["body"]["payload"] if Receiver.got else {}
        check(p.get("trigger") == "pdi" and p.get("change") == "CHG-12" and p.get("phase") == "delivery"
              and p.get("started_by") == {"name": "pdi", "kind": "automation"}, f"R-4: {p}")

        # R-5: progress with no start seen (reporting turned on mid-session) sends nothing
        Receiver.got = []
        run_hook(project, "Stop", on, session="late")
        check(Receiver.got == [], f"R-5: {Receiver.got}")

        # R-6: pdi down or refusing: the session is not blocked, the error is logged without content
        Receiver.status = 500
        r = run_hook(project, "SessionStart", on, session="down")
        Receiver.status = 200
        log = project / ".tf" / "logs" / "hook-errors.jsonl"
        entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
        check(r.returncode == 0 and r.stdout == "" and any(e.get("hook") == "run_report" for e in entries),
              f"R-6: exit {r.returncode}, logged {entries}")
        r = run_hook(project, "SessionStart", {**on, "PDI_EVENTS_URL": "http://pdi.example.com"}, session="plain")
        check(r.returncode == 0, "R-6: plain http to a remote host is refused quietly")

    srv.shutdown()
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of run_report")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
