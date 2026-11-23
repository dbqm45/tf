#!/usr/bin/env python3
"""
The live task dashboard (skill tf): a small local server that pushes every state change to the open page over
Server-Sent Events, so the page updates in place — no reload, no flicker, the open panel and the scroll stay.

  python3 .claude/skills/tf/scripts/dashboard_live.py serve [--project DIR] [--idle SECONDS] [--poll SECONDS]
  python3 .claude/skills/tf/scripts/dashboard_live.py start|status|stop [--project DIR]

You normally do not call it yourself: `run_report.py start` starts it with the run (when the page is to open),
`run_state.py dashboard --live [--open]` and `tf status --open` start it or reuse the running one, and
`run_state.py dashboard --live --stop` stops it. Turn it off with {"dashboard_live": false} in `.claude/tf.json`
or TF_DASHBOARD_LIVE=0 (then the page is the file `.tf/runs/dashboard.html`, which re-reads the data every 5 s).

Security: it binds only to 127.0.0.1, always on a port the system picks (port 0, never a fixed one), and every
address carries a random token (`http://127.0.0.1:<port>/<token>/`); a request without the token gets 404, so other
local pages and programs cannot read the state. It reads only the project's files, runs no shell, makes no network
calls beyond localhost. Endpoints under the token: `/` the page (the same renderer as the file, `run_state.render_html`),
`data` the RUNS JSON, `events` the SSE stream (`event: runs` on a change, a heartbeat comment every 15 s),
`health` (a factory marker, the project and the pid — reuse requires this answer, not just an open port),
`shutdown` (POST) and the files under `.tf/runs/` that the page links to (screenshots).

One server per project: `.tf/runs/.live.json` holds {pid, port, token, started}. Before a start the recorded server
is asked for `health` with its token; only an answer with the marker and this project counts — a port that is closed
or answers something else (another app took it) is treated as dead, and a new server starts on a fresh port and
overwrites the file. Change detection: the mtimes and sizes of `.tf/runs/*/run.json`, `.tf/runs/cuts/*/run.json`,
`docs/project/changes/*/task.json` (and `plan.md`), and `.tf/runs/dashboard.html` (rewritten by `run_state.py` after
every state write) every 0.25 s; on a change the data is rebuilt without the cost computation and pushed when it
differs. The server exits by itself after 30 min without a connected page and without a state change (`--idle`,
or TF_DASHBOARD_LIVE_IDLE in seconds), and at once when the project's `.tf/runs/` is gone. The log: `.tf/logs/dashboard-live.log`.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import queue
import secrets
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

APP = "tf-dashboard-live"
HOST = "127.0.0.1"
STATE = Path(".tf") / "runs" / ".live.json"
LOG = Path(".tf") / "logs" / "dashboard-live.log"
IDLE = 30 * 60.0
POLL = 0.25
HEARTBEAT = 15.0
START_WAIT = 2.0
WATCH = (".tf/runs/*/run.json", ".tf/runs/cuts/*/run.json", "docs/project/changes/*/task.json",
         "docs/project/changes/*/plan.md")
SERVER_CMD = [sys.executable, str(Path(__file__).resolve()), "serve"]   # tests replace it to simulate a failed start


# ---- the client side: state file, health check, start, stop -----------------------------------------------------------

def read_state(project: Path) -> dict | None:
    try:
        data = json.loads((project / STATE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and isinstance(data.get("port"), int) and data.get("token") else None
    except (OSError, ValueError):
        return None


def request(port: int, method: str, path: str, timeout: float = 1.5) -> tuple[int, bytes] | None:
    """One request to 127.0.0.1 (http.client: no proxy from the environment); None when nothing answers."""
    try:
        conn = http.client.HTTPConnection(HOST, port, timeout=timeout)
        try:
            conn.request(method, path, headers={"Connection": "close"})
            r = conn.getresponse()
            return r.status, r.read(65536)
        finally:
            conn.close()
    except (OSError, http.client.HTTPException):
        return None


def healthy(project: Path, info: dict) -> bool:
    """Our server of this project: `health` with the token answers 200 with the factory marker, the project path
    and the recorded pid. An open port that answers anything else belongs to another app — dead for us."""
    r = request(info["port"], "GET", f"/{info['token']}/health")
    if not r or r[0] != 200:
        return False
    try:
        h = json.loads(r[1].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False
    return (isinstance(h, dict) and h.get("app") == APP and h.get("project") == str(project.resolve())
            and h.get("pid") == info.get("pid"))


def running(project: Path) -> dict | None:
    info = read_state(project)
    return info if info and healthy(project, info) else None


def url(info: dict) -> str:
    return f"http://{HOST}:{info['port']}/{info['token']}/"


def log_tail(project: Path, limit: int = 300) -> str:
    try:
        lines = [ln.strip() for ln in (project / LOG).read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        return lines[-1][-limit:] if lines else ""
    except OSError:
        return ""


def start(project: Path, wait: float = START_WAIT) -> tuple[str | None, str | None]:
    """Start the server detached (or reuse the running one). Returns (address, None) or (None, the reason) —
    a sandbox that blocks the socket, a port error, no answer within `wait` seconds. Never raises."""
    try:
        info = running(project)
        if info:
            return url(info), None
        (project / LOG).parent.mkdir(parents=True, exist_ok=True)
        (project / STATE).parent.mkdir(parents=True, exist_ok=True)
        kw: dict = {"stdin": subprocess.DEVNULL, "cwd": str(project), "close_fds": True}
        if os.name == "nt":
            kw["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        else:
            kw["start_new_session"] = True
        with open(project / LOG, "w", encoding="utf-8") as log:
            child = subprocess.Popen([*SERVER_CMD, "--project", str(project.resolve())], stdout=log, stderr=log, **kw)
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            info = read_state(project)
            if info and healthy(project, info):
                return url(info), None
            if child.poll() is not None:
                info = running(project)           # another start won the race: its server is as good
                if info:
                    return url(info), None
                return None, log_tail(project) or f"the server exited with code {child.returncode}"
            time.sleep(0.05)
        child.kill()
        return None, f"the server did not answer within {wait:g} s"
    except Exception as e:  # noqa: BLE001 — the preview never breaks the run
        return None, str(e) or type(e).__name__


def stop(project: Path) -> bool:
    """Stop the recorded server (POST shutdown with the token: no signals, the same on Windows). True = it was running."""
    info = read_state(project)
    if not info:
        return False
    ok = healthy(project, info) and bool(request(info["port"], "POST", f"/{info['token']}/shutdown"))
    if ok:
        for _ in range(40):                      # the server removes the state file on exit
            if read_state(project) != info:
                break
            time.sleep(0.05)
    if read_state(project) == info:             # a dead record: a crashed server or a port another app took
        try:
            (project / STATE).unlink()
        except OSError:
            pass
    return ok


# ---- the server -----------------------------------------------------------------------------------------------------

class LiveServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False      # never share a port with another listener (SO_REUSEADDR differs on Windows)


class Live:
    def __init__(self, project: Path, idle: float, poll: float):
        import run_state
        self.rs = run_state
        self.project = project.resolve()
        self.root = (self.project / ".tf" / "runs").resolve()       # the dashboard file's directory: relative links
        self.idle, self.poll = idle, poll
        self.token = secrets.token_urlsafe(18)
        self.lock = threading.Lock()
        self.clients: list[queue.Queue] = []
        self.sig = None
        self.data = None
        self.dirty = True
        self.last_active = time.monotonic()
        self.stopping = threading.Event()

    # data
    def signature(self) -> tuple:
        out = []
        for pattern in (*WATCH, ".tf/runs/dashboard.html"):
            for f in sorted(self.project.glob(pattern)):
                try:
                    st = f.stat()
                    out.append((f.as_posix(), st.st_mtime_ns, st.st_size))
                except OSError:
                    pass
        return tuple(out)

    def build(self) -> str:
        with self.lock:
            if self.dirty or self.data is None:
                self.data = self.rs.runs_data(self.rs.collect_runs(self.project, self.root, costs=False))
                self.dirty = False
            return self.data

    def broadcast(self, data: str | None) -> None:
        with self.lock:
            for q in list(self.clients):
                q.put(data)

    def watch(self, server: LiveServer) -> None:
        while not self.stopping.is_set():
            try:
                sig = self.signature()
                if sig != self.sig:
                    first = self.sig is None
                    self.sig, self.dirty = sig, True
                    self.last_active = time.monotonic()
                    if self.clients and not first:
                        before = self.data
                        data = self.build()
                        if data != before:
                            self.broadcast(data)
                if not (self.project / ".tf" / "runs").is_dir():
                    print(f"{now()} the project's .tf/runs/ is gone — exiting", flush=True)
                    break
                if self.clients:
                    self.last_active = time.monotonic()
                elif time.monotonic() - self.last_active > self.idle:
                    print(f"{now()} idle for {self.idle:g} s with no page connected — exiting", flush=True)
                    break
            except Exception as e:  # noqa: BLE001 — one bad read does not stop the watcher
                print(f"{now()} watch error: {e}", flush=True)
            self.stopping.wait(self.poll)
        self.stopping.set()
        self.broadcast(None)
        threading.Thread(target=server.shutdown, daemon=True).start()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def handler_for(live: Live):
    class Handler(BaseHTTPRequestHandler):
        server_version = "tf-live"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # noqa: D401 — no per-request log lines (the token is in the path)
            return

        def send(self, code: int, body: bytes, ctype: str = "text/plain; charset=utf-8") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def route(self) -> str | None:
            """The path after the token, or None (no token → 404)."""
            path = self.path.split("?", 1)[0].split("#", 1)[0]
            prefix = f"/{live.token}/"
            if path == prefix[:-1]:
                return ""
            if not path.startswith(prefix):
                return None
            return path[len(prefix):]

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            rest = self.route()
            if rest is None:
                return self.send(404, b"not found\n")
            if rest == "":
                if not self.path.split("?", 1)[0].endswith("/"):        # relative links need the trailing slash
                    self.send_response(301)
                    self.send_header("Location", f"/{live.token}/")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                body = live.rs.render_html(json.loads(live.build())).encode("utf-8")
                return self.send(200, body, "text/html; charset=utf-8")
            if rest == "data":
                return self.send(200, live.build().encode("utf-8"), "application/json; charset=utf-8")
            if rest == "health":
                body = json.dumps({"app": APP, "project": str(live.project), "pid": os.getpid()}).encode("utf-8")
                return self.send(200, body, "application/json; charset=utf-8")
            if rest == "events":
                return self.events()
            return self.static(rest)

        def do_POST(self):
            rest = self.route()
            if rest != "shutdown":
                return self.send(404, b"not found\n")
            self.send(200, b"stopping\n")
            print(f"{now()} shutdown requested", flush=True)
            live.stopping.set()

        def static(self, rest: str):
            """Files the page links to (screenshots, evidence) — only inside .tf/runs/, no dot files (the state file)."""
            from urllib.parse import unquote
            rel = unquote(rest)
            parts = [p for p in rel.replace("\\", "/").split("/") if p]
            if not parts or any(p.startswith(".") for p in parts):
                return self.send(404, b"not found\n")
            f = (live.root / Path(*parts)).resolve()
            if not f.is_relative_to(live.root) or not f.is_file():
                return self.send(404, b"not found\n")
            types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
                     ".webp": "image/webp", ".svg": "image/svg+xml", ".md": "text/plain; charset=utf-8",
                     ".txt": "text/plain; charset=utf-8", ".json": "application/json; charset=utf-8",
                     ".log": "text/plain; charset=utf-8", ".html": "text/plain; charset=utf-8",
                     ".js": "text/plain; charset=utf-8"}
            try:
                body = f.read_bytes()
            except OSError:
                return self.send(404, b"not found\n")
            return self.send(200, body, types.get(f.suffix.lower(), "application/octet-stream"))

        def events(self):
            q: queue.Queue = queue.Queue()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.close_connection = True
            with live.lock:
                live.clients.append(q)
            live.last_active = time.monotonic()
            try:
                self.push(live.build())                  # the current state at once (also after a reconnect)
                while not live.stopping.is_set():
                    try:
                        data = q.get(timeout=HEARTBEAT)
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                        continue
                    if data is None:
                        break
                    self.push(data)
            except OSError:
                pass                                     # the page went away
            finally:
                with live.lock:
                    if q in live.clients:
                        live.clients.remove(q)
                live.last_active = time.monotonic()

        def push(self, data: str) -> None:
            self.wfile.write(b"retry: 2000\nevent: runs\ndata: " + data.encode("utf-8") + b"\n\n")
            self.wfile.flush()

    return Handler


def serve(project: Path, idle: float, poll: float) -> int:
    project = project.resolve()
    os.chdir(project)
    other = running(project)
    if other:
        print(f"{now()} already running: {url(other)}", flush=True)
        return 0
    live = Live(project, idle, poll)
    try:
        server = LiveServer((HOST, 0), handler_for(live))        # port 0: always a free port the system picks
    except OSError as e:
        print(f"cannot bind {HOST}: {e}", flush=True)
        return 3
    port = server.server_address[1]
    info = {"pid": os.getpid(), "port": port, "token": live.token, "started": now()}
    state = project / STATE
    state.parent.mkdir(parents=True, exist_ok=True)
    tmp = state.with_name(state.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(info), encoding="utf-8")
    os.replace(tmp, state)
    print(f"{now()} serving {project.as_posix()} on {HOST}:{port} (idle {idle:g} s)", flush=True)
    live.sig = live.signature()
    watcher = threading.Thread(target=live.watch, args=(server,), daemon=True)
    watcher.start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        live.stopping.set()
        server.server_close()
        if read_state(project) == info:
            try:
                state.unlink()
            except OSError:
                pass
        print(f"{now()} stopped", flush=True)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["serve", "start", "status", "stop"])
    ap.add_argument("--project", default=".")
    ap.add_argument("--idle", type=float, default=None, help="seconds without a page and a change before exiting")
    ap.add_argument("--poll", type=float, default=POLL)
    args = ap.parse_args(argv[1:])
    project = Path(args.project).resolve()
    if args.cmd == "serve":
        idle = args.idle
        if idle is None:
            try:
                idle = float(os.environ.get("TF_DASHBOARD_LIVE_IDLE") or IDLE)
            except ValueError:
                idle = IDLE
        return serve(project, idle, args.poll)
    if args.cmd == "start":
        address, why = start(project)
        print(address or f"⚠ The live dashboard did not start ({why}).")
        return 0 if address else 1
    if args.cmd == "status":
        info = running(project)
        print(url(info) if info else "ℹ No live dashboard is running.")
        return 0 if info else 1
    print("✓ The live dashboard stopped." if stop(project) else "ℹ No live dashboard is running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
