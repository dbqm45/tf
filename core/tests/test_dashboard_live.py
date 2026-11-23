#!/usr/bin/env python3
"""Live dashboard tests (the tf skill, scripts/dashboard_live.py and `run_state.py dashboard --live`).
python3 .claude/tests/test_dashboard_live.py"""
import http.client
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
LIVE = SCRIPT.with_name("dashboard_live.py")
REPORT = SCRIPT.with_name("run_report.py")
TEMPLATE = SCRIPT.parent.parent / "templates" / "dashboard.html"
STATE = Path(".tf") / "runs" / ".live.json"
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given a list, when the admin sorts it, then it is sorted.\n"
        "\n## Unchanged\n\n- Paging.\n\n## Out of scope\n\n- Filters.\n")


def env_for(cfg: Path, extra=None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("CI", "TF_DASHBOARD", "TF_DASHBOARD_LIVE")}
    return {**env, "CLAUDE_CONFIG_DIR": str(cfg), "TF_DASHBOARD_OPEN": "0", **(extra or {})}


def run(script, args, cwd, cfg, extra=None):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=env_for(cfg, extra), timeout=60)


def state(proj: Path) -> dict | None:
    try:
        return json.loads((proj / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def get(port: int, path: str, method: str = "GET"):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        conn.request(method, path)
        r = conn.getresponse()
        return r.status, r.read().decode("utf-8", "replace")
    finally:
        conn.close()


def alive(pid: int) -> bool:
    if os.name == "nt":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:                                   # a zombie (not yet reaped) counts as gone
        return "Z" not in Path(f"/proc/{pid}/stat").read_text().split()[2]
    except (OSError, IndexError):
        return True


def gone(pid: int, wait: float = 3.0) -> bool:
    end = time.monotonic() + wait
    while time.monotonic() < end:
        if not alive(pid):
            return True
        time.sleep(0.05)
    return not alive(pid)


def kill(pid: int) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            os.kill(pid, 9)
    except OSError:
        pass


class Sse:
    """A minimal SSE reader: collects `event: runs` payloads in a thread."""

    def __init__(self, port: int, path: str):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        self.sock.sendall(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nAccept: text/event-stream\r\n\r\n".encode())
        self.events: list[tuple[float, str]] = []
        self.buf = b""
        threading.Thread(target=self.read, daemon=True).start()

    def read(self):
        try:
            while True:
                chunk = self.sock.recv(65536)
                if not chunk:
                    return
                self.buf += chunk
                while b"\n\n" in self.buf:
                    block, self.buf = self.buf.split(b"\n\n", 1)
                    lines = block.decode("utf-8", "replace").splitlines()
                    if "event: runs" in lines:
                        data = "".join(ln[6:] for ln in lines if ln.startswith("data: "))
                        self.events.append((time.monotonic(), data))
        except OSError:
            return

    def wait(self, count: int, timeout: float) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if len(self.events) >= count:
                return True
            time.sleep(0.02)
        return len(self.events) >= count

    def until(self, pred, timeout: float):
        """The first event whose RUNS satisfy `pred` (intermediate writes of one command may come first): (time, runs)."""
        end = time.monotonic() + timeout
        seen = 0
        while time.monotonic() < end:
            for at, data in self.events[seen:]:
                seen += 1
                runs = json.loads(data)
                if runs and pred(runs[0]):
                    return at, runs
            time.sleep(0.02)
        return None, None

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def main() -> int:
    fails = []
    pids: set[int] = set()

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    t0 = time.monotonic()
    try:
        with tempfile.TemporaryDirectory() as t:
            proj, cfg = Path(t) / "proj", Path(t) / "cfg"
            proj.mkdir()
            r = run(REPORT, ["start", "Sort the list", "--story", "As an admin I want to sort."], proj, cfg)
            d = next((proj / ".tf" / "runs").glob("T-*-sort-the-list"), None)
            check(r.returncode == 0 and d is not None, f"L-0: preparing the run: {r.stdout} {r.stderr}")
            check(state(proj) is None, "L-0b: TF_DASHBOARD_OPEN=0 — run start does not start a server nobody looks at")
            if d is None:
                print("✗ no run directory")
                return 1
            (proj / "docs" / "project" / "changes" / d.name / "spec.md").write_text(SPEC, encoding="utf-8")
            run(SCRIPT, ["flag", str(d), "none", "--reason", "live dashboard test"], proj, cfg)

            # L-1: --live starts the server and prints the address with the token; 404 without the token
            r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg)
            info = state(proj) or {}
            if info.get("pid"):
                pids.add(info["pid"])
            url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            check(r.returncode == 0 and info and url == f"http://127.0.0.1:{info['port']}/{info['token']}/",
                  f"L-1a: dashboard --live prints the http address with the token: {r.stdout!r} {r.stderr!r} {info}")
            if not info:
                print("✗ no live server")
                return 1
            port, tok = info["port"], info["token"]
            check(port != 0 and len(tok) >= 16, f"L-1b: a free port from the system and a long token: {info}")
            code, body = get(port, f"/{tok}/")
            check(code == 200 and "EventSource" in body and "const RUNS = [" in body and "Sort the list" in body,
                  f"L-1c: the page with the token is the dashboard with the data: {code} {body[:120]!r}")
            other = tok[:-1] + ("y" if tok[-1] == "x" else "x")   # a wrong token: the last character always differs
            for path in ("/", "/data", "/events", f"/{other}/", f"/{tok}x/data", "/health"):
                code, _ = get(port, path)
                check(code == 404, f"L-1d: no token → 404: {path} {code}")
            code, _ = get(port, f"/{tok}/.live.json")
            check(code == 404, f"L-1e: dot files (the state file with the token) are not served: {code}")
            code, _ = get(port, f"/{tok}/..%2f..%2fetc/passwd")
            check(code == 404, f"L-1f: no path outside .tf/runs/: {code}")
            (d / "screens").mkdir()
            (d / "screens" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            code, body = get(port, f"/{tok}/{d.name}/screens/a.png")
            check(code == 200, f"L-1g: the files the page links to (relative to .tf/runs/) are served: {code}")
            (d / "screens" / "a.png").unlink()
            (d / "screens").rmdir()

            # L-2: /data returns RUNS
            code, body = get(port, f"/{tok}/data")
            data = json.loads(body) if code == 200 else []
            check(isinstance(data, list) and data and data[0].get("title") == "Sort the list",
                  f"L-2: /data returns RUNS: {code} {body[:120]!r}")
            code, body = get(port, f"/{tok}/health")
            h = json.loads(body) if code == 200 else {}
            check(h.get("app") == "tf-dashboard-live" and h.get("project") == str(proj.resolve()) and h.get("pid") == info["pid"],
                  f"L-2b: health answers with the factory marker, the project and the pid: {h}")

            # L-3: an SSE client gets an event within ~2 s after a `run_state.py stage` / `step` write
            sse = Sse(port, f"/{tok}/events")
            check(sse.wait(1, 3), "L-3a: the stream sends the current state at once on connect")
            r = run(SCRIPT, ["stage", str(d), "plan", "--auto"], proj, cfg)
            done = time.monotonic()
            at, runs = sse.until(lambda o: o.get("stage") == "plan", 3)
            lag = max(0.0, at - done) if at else None
            check(r.returncode == 0 and at and lag < 2,
                  f"L-3b: stage plan → an event within 2 s: rc={r.returncode} {r.stdout} lag={lag} {len(sse.events)} events")
            r = run(SCRIPT, ["step", str(d), "S1", "R1", "test", "run"], proj, cfg)
            done = time.monotonic()
            at, runs = sse.until(lambda o: (o.get("cur") or {}).get("k") == "S1", 3)
            lag = max(0.0, at - done) if at else None
            check(r.returncode == 0 and at and lag < 2,
                  f"L-3c: step → an event within 2 s with the round: rc={r.returncode} {r.stdout} lag={lag}")
            print(f"  SSE lag after a write: {lag:.2f} s" if lag is not None else "  SSE: no event")
            sse.close()

            # L-4: single instance — a second start reuses the first
            r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg)
            info2 = state(proj) or {}
            check(r.stdout.strip() == url and info2.get("pid") == info["pid"],
                  f"L-4: a second --live reuses the running server: {r.stdout!r} {info2}")
            r = run(LIVE, ["status"], proj, cfg)
            check(r.returncode == 0 and r.stdout.strip() == url, f"L-4b: status prints the address: {r.stdout!r}")

            # L-5: --stop stops it, the state file goes away
            r = run(SCRIPT, ["dashboard", "--live", "--stop"], proj, cfg)
            check(r.returncode == 0 and "stopped" in r.stdout and gone(info["pid"]) and state(proj) is None,
                  f"L-5: --live --stop stops the server: {r.stdout!r} alive={alive(info['pid'])} {state(proj)}")
            r = run(SCRIPT, ["dashboard", "--live", "--stop"], proj, cfg)
            check(r.returncode == 0 and "No live dashboard" in r.stdout, f"L-5b: --stop without a server: {r.stdout!r}")

            # L-6: a foreign app on the recorded port — treated as dead: a new server on another port, the foreign one untouched
            class Foreign(http.server.BaseHTTPRequestHandler):
                hits = 0

                def do_GET(self):
                    Foreign.hits += 1
                    body = b'{"app": "something-else"}'
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, *a):
                    return
            foreign = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Foreign)
            threading.Thread(target=foreign.serve_forever, daemon=True).start()
            fport = foreign.server_address[1]
            (proj / STATE).write_text(json.dumps({"pid": info["pid"], "port": fport, "token": tok,
                                                  "started": "2026-01-01T00:00:00+00:00"}), encoding="utf-8")
            r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg)
            info3 = state(proj) or {}
            if info3.get("pid"):
                pids.add(info3["pid"])
            code, body = get(fport, "/anything")
            check(info3.get("port") not in (None, fport) and info3.get("token") != tok
                  and r.stdout.strip().startswith(f"http://127.0.0.1:{info3.get('port')}/")
                  and Foreign.hits >= 1 and code == 200 and "something-else" in body,
                  f"L-6: a foreign server on the recorded port → a new server on a fresh port, the foreign one untouched: "
                  f"{r.stdout!r} {info3} fport={fport} hits={Foreign.hits} {code}")
            r = run(SCRIPT, ["dashboard", "--live", "--stop"], proj, cfg)
            check(gone(info3.get("pid", 0)), f"L-6b: the new server stops: {r.stdout!r}")
            foreign.shutdown()
            foreign.server_close()

            # L-7: dashboard: false / dashboard_live: false / TF_DASHBOARD_LIVE=0 / CI turn it off (the file instead)
            (proj / ".claude").mkdir(exist_ok=True)
            for label, text, extra in (("dashboard_live false", '{"dashboard_live": false}', None),
                                       ("dashboard false", '{"dashboard": false}', None),
                                       ("TF_DASHBOARD_LIVE=0", None, {"TF_DASHBOARD_LIVE": "0"}),
                                       ("CI", None, {"CI": "1"})):
                cfgf = proj / ".claude" / "tf.json"
                if text:
                    cfgf.write_text(text, encoding="utf-8")
                elif cfgf.exists():
                    cfgf.unlink()
                r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg, extra)
                check(r.returncode == 0 and r.stdout.strip().startswith("file://") and "⚠" in r.stderr
                      and state(proj) is None, f"L-7: {label} — no server, the file address and a ⚠ reason: "
                                               f"{r.stdout!r} {r.stderr!r} {state(proj)}")
            (proj / ".claude" / "tf.json").unlink(missing_ok=True)

            # L-8: idle shutdown with a short timeout (no page, no change)
            r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg, {"TF_DASHBOARD_LIVE_IDLE": "0.6"})
            info4 = state(proj) or {}
            if info4.get("pid"):
                pids.add(info4["pid"])
            check(bool(info4) and gone(info4["pid"], 4) and state(proj) is None,
                  f"L-8: the server exits by itself after the idle time: {info4} {state(proj)}")

            # L-9: the server cannot start (a blocked socket) → the file address and a reason; the run is not failed
            sys.path.insert(0, str(SCRIPT.parent))
            import dashboard_live
            import run_state
            real_cmd = dashboard_live.SERVER_CMD
            cwd = os.getcwd()
            try:
                dashboard_live.SERVER_CMD = [sys.executable, "-c",
                                             "print('cannot bind 127.0.0.1: [Errno 1] Operation not permitted')"
                                             "; raise SystemExit(3)"]
                address, why = dashboard_live.start(proj)
                check(address is None and "Operation not permitted" in (why or ""),
                      f"L-9a: a failed bind → no address and the reason from the log: {address} {why}")
                dashboard_live.SERVER_CMD = [sys.executable, "-c", "import time; time.sleep(30)"]
                began = time.monotonic()
                address, why = dashboard_live.start(proj, wait=0.5)
                check(address is None and "did not answer" in (why or "") and time.monotonic() - began < 3,
                      f"L-9b: no answer in time → the fallback, the child killed: {address} {why}")
                dashboard_live.SERVER_CMD = [sys.executable, "-c", "raise SystemExit(3)"]
                os.chdir(proj)
                old_env = {k: os.environ.get(k) for k in ("CI", "TF_DASHBOARD_OPEN", "TF_DASHBOARD", "TF_DASHBOARD_LIVE")}
                for k in old_env:
                    os.environ.pop(k, None)
                real_open = run_state.open_file
                opened = []
                run_state.open_file = lambda target: opened.append(target)
                import io
                import contextlib
                err = io.StringIO()
                try:
                    with contextlib.redirect_stderr(err):
                        uri = run_state.launch(proj)
                finally:
                    run_state.open_file = real_open
                    for k, v in old_env.items():
                        if v is not None:
                            os.environ[k] = v
                check(uri and uri.startswith("file://") and "⚠ The live dashboard did not start" in err.getvalue()
                      and opened and not str(opened[0]).startswith("http"),
                      f"L-9c: launch falls back to the file and opens it: {uri} {err.getvalue()!r} {opened}")
                # serve itself: a bind error is an exit code and a reason, not a traceback
                real_server = dashboard_live.LiveServer

                class NoBind:
                    def __init__(self, *a, **k):
                        raise PermissionError(1, "Operation not permitted")
                dashboard_live.LiveServer = NoBind
                out = io.StringIO()
                try:
                    with contextlib.redirect_stdout(out):
                        code = dashboard_live.serve(proj, 1, 0.1)
                finally:
                    dashboard_live.LiveServer = real_server
                check(code == 3 and "cannot bind" in out.getvalue() and state(proj) is None,
                      f"L-9d: serve with a blocked socket → exit 3 and a reason: {code} {out.getvalue()!r}")
            finally:
                dashboard_live.SERVER_CMD = real_cmd
                os.chdir(cwd)

            # L-10: the template listens to events and does not reload in live mode; the file fallback re-reads data.js
            html = TEMPLATE.read_text(encoding="utf-8")
            live_part, _, file_part = html.partition("} else {")
            check("new EventSource(\"events\")" in html and "location.reload" not in live_part.split("REFRESH =====")[-1]
                  and "location.reload(); return setTimeout" not in html.split("setTimeout(function tick")[0],
                  "L-10a: EventSource in the template and no reload in the live branch")
            check(html.count("location.reload") == 2 and all("!sel" in ln for ln in html.splitlines() if "location.reload" in ln),
                  "L-10b: the file fallback reloads only while the panel is closed (and only without data.js)")
            check("RUNS.splice(" in html and "fillDrawer(r)" in html and "offline — retrying" in html,
                  "L-10c: the data is replaced in place, the open panel is re-rendered, an offline indicator")
            side = proj / ".tf" / "runs" / "dashboard.data.js"
            page = (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
            check(side.read_text(encoding="utf-8").startswith("tfRuns([") and 'const DATA_JS = "dashboard.data.js"' in page,
                  f"L-10d: the file build writes the side data file the page re-reads: {side.exists()}")
            check(page.count("</script>") == 1, "L-10e: still one script element in the page")

            # L-12: the project's .tf/runs/ removed (a deleted clone, a temporary directory) → the server exits at once
            r = run(SCRIPT, ["dashboard", "--live", "--no-cost"], proj, cfg)
            info5 = state(proj) or {}
            if info5.get("pid"):
                pids.add(info5["pid"])
            import shutil
            shutil.rmtree(proj / ".tf" / "runs", ignore_errors=True)
            check(bool(info5) and gone(info5["pid"], 3), f"L-12: no .tf/runs/ → the server exits: {info5}")
    finally:
        for pid in pids:
            if alive(pid):
                kill(pid)
    elapsed = time.monotonic() - t0
    check(elapsed < 30, f"L-11: the tests are fast: {elapsed:.1f} s")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} live dashboard tests: {'all passed' if not fails else len(fails)} ({elapsed:.1f} s)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
