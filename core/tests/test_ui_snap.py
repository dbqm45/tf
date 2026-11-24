#!/usr/bin/env python3
"""Tests of `.claude/skills/tf/scripts/ui_snap.py` (screenshots before/after a UI change, local addresses only).
Most checks use a fake browser (a script that writes a PNG whose bytes depend on the page it was given), so they run
everywhere; one check uses a real headless Chromium/Chrome and is skipped with a note when there is none or it times out
(CTF_REQUIRE_BROWSER=1, CI: a missing or broken browser is an error). python3 tests/test_ui_snap.py"""
import hashlib
import http.server
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "tf" / "scripts" / "ui_snap.py"

FAKE_BROWSER = '''#!{python}
import hashlib, re, struct, sys, urllib.request, zlib
args = sys.argv[1:]
out = next(a.split("=", 1)[1] for a in args if a.startswith("--screenshot="))
w, h = next(a.split("=", 1)[1] for a in args if a.startswith("--window-size=")).split(",")
open({marker!r}, "a").write(" ".join(args) + "\\n")
body = urllib.request.build_opener(urllib.request.ProxyHandler({{}})).open(args[-1], timeout=10).read()
def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
png = (b"\\x89PNG\\r\\n\\x1a\\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", int(w), int(h), 8, 2, 0, 0, 0))
       + chunk(b"tEXt", b"page\\0" + hashlib.sha256(body).hexdigest().encode()) + chunk(b"IEND", b""))
open(out, "wb").write(png)
'''


def load():
    spec = importlib.util.spec_from_file_location("ui_snap", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def serve(pages: dict):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = pages.get(self.path.split("?")[0])
            self.send_response(200 if body is not None else 404)
            data = (body or "not found").encode("utf-8")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def answers(port: int) -> bool:
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return True
    except OSError:
        return False


def run(args, project: Path, env_extra=None, path=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CTF_BROWSER", "PLAYWRIGHT_BROWSERS_PATH")}
    env.update({"CLAUDE_PROJECT_DIR": str(project), "PYTHONDONTWRITEBYTECODE": "1"})
    if path is not None:
        env["PATH"] = path
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=project, capture_output=True,
                          text=True, env=env, timeout=180)


def main() -> int:
    sys.dont_write_bytecode = True
    ui = load()
    fails = []

    def check(name, cond, extra=""):
        if not cond:
            fails.append(name)
            print(f"✗ {name} {extra}")

    # pure helpers
    check("viewports: parsing", ui.parse_viewports("1280x800, 390x844") == [(1280, 800), (390, 844)])
    check("viewports: a bad value is rejected", ui.parse_viewports("wide") is None)
    check("slug: root", ui.route_slug("/") == "index")
    check("slug: path with query", ui.route_slug("/a/b?x=1") == "a-b-x-1")
    check("local: localhost, 127.0.0.1, ::1", all(ui.is_local(u) for u in (
        "http://localhost:4200", "http://127.0.0.1:5173/x", "http://[::1]:3000/")))
    check("local: foreign hosts and schemes are refused", not any(ui.is_local(u) for u in (
        "https://example.com/", "http://192.168.0.5/", "file:///etc/passwd", "http://localhost.evil.com/",
        "http://127.0.0.1@evil.com/")))
    check("ui files: patterns", all(ui.is_ui_file(f) for f in ("src/app/a.component.html", "x/Button.tsx", "s.scss",
                                                                 "App.vue", "a.svelte", "style.css"))
          and not any(ui.is_ui_file(f) for f in ("api/handler.py", "Button.test.tsx", "tests/a.html", "README.md")))

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        project = base / "proj"
        project.mkdir()
        fake = base / "fakebrowser"
        marker = base / "browser-calls.txt"
        fake.write_text(FAKE_BROWSER.format(python=sys.executable, marker=str(marker)), encoding="utf-8")
        fake.chmod(0o755)
        envb = {"CTF_BROWSER": str(fake)}

        # non-local URL → exit 2 and no browser started
        r = run(["capture", base / "run0", "--label", "before", "--url", "https://example.com/"], project, envb)
        check("non-local URL → exit 2", r.returncode == 2, r.stderr + r.stdout)
        check("non-local URL: no browser launched", not marker.exists())

        # no browser at all → exit 3 with a message, nothing installed
        r = run(["capture", base / "run0", "--label", "before", "--url", "http://127.0.0.1:9/"], project,
                {"CTF_BROWSER": str(base / "nowhere")}, path=os.path.dirname(sys.executable) + "-none")
        check("no browser → exit 3", r.returncode == 3, r.stderr + r.stdout)
        check("no browser: a message for the human", "browser" in (r.stderr + r.stdout).lower()
              and "CTF_BROWSER" in (r.stderr + r.stdout))

        # before / after / compare with a fake browser
        pages = {"/": "<h1>Home</h1>", "/about": "<h1>About</h1>"}
        server, port = serve(pages)
        run_dir = base / "run1"
        run_dir.mkdir()
        url = f"http://127.0.0.1:{port}"
        try:
            r = run(["capture", run_dir, "--label", "before", "--url", url, "--route", "/", "--route", "/about"],
                    project, envb)
            check("capture before → exit 0", r.returncode == 0, r.stderr + r.stdout)
            pages["/"] = "<h1>Home — changed</h1>"
            r = run(["capture", run_dir, "--label", "after", "--url", url, "--route", "/", "--route", "/about",
                     "--viewport", "1280x800"], project, envb)
            check("capture after → exit 0", r.returncode == 0, r.stderr + r.stdout)
        finally:
            server.shutdown()
        idx_path = run_dir / "screens" / "before" / "index.json"
        check("index.json exists", idx_path.is_file())
        if idx_path.is_file():
            idx = json.loads(idx_path.read_text(encoding="utf-8"))
            shots = idx.get("shots", [])
            check("index: two shots", len(shots) == 2, str(idx))
            s = shots[0] if shots else {}
            check("index: fields", all(k in s for k in ("url", "route", "viewport", "file", "sha256", "width", "height",
                                                         "time")), str(s))
            f = run_dir / "screens" / "before" / s.get("file", "x")
            check("index: file name is route@WxH.png", s.get("file") == "index@1280x800.png", str(s.get("file")))
            check("index: PNG size from IHDR", f.is_file() and (s.get("width"), s.get("height")) == (1280, 800)
                  and ui.png_size(f) == (1280, 800))
            check("index: sha256 of the file", f.is_file() and s.get("sha256") == hashlib.sha256(f.read_bytes()).hexdigest())
        calls = marker.read_text(encoding="utf-8")
        check("browser flags", "--headless" in calls and "--hide-scrollbars" in calls
              and "--window-size=1280,800" in calls and "--user-data-dir=" in calls)
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            check("browser flags: --no-sandbox as root", "--no-sandbox" in calls)
        r = run(["compare", run_dir], project)
        cmp = run_dir / "screens" / "compare.md"
        text = cmp.read_text(encoding="utf-8") if cmp.is_file() else ""
        check("compare → exit 0 and compare.md", r.returncode == 0 and bool(text), r.stderr)
        check("compare: 1 changed + 1 identical",
              sum("| changed |" in ln for ln in text.splitlines()) == 1
              and sum("| identical |" in ln for ln in text.splitlines()) == 1, text)
        check("compare: file paths in the table", "before/index@1280x800.png" in text and "after/index@1280x800.png" in text)
        # only-before / only-after
        (run_dir / "screens" / "after" / "about@1280x800.png").unlink()
        ai = json.loads((run_dir / "screens" / "after" / "index.json").read_text(encoding="utf-8"))
        ai["shots"] = [x for x in ai["shots"] if x["route"] != "/about"]
        (run_dir / "screens" / "after" / "index.json").write_text(json.dumps(ai), encoding="utf-8")
        run(["compare", run_dir], project)
        check("compare: only before", "| only before |" in cmp.read_text(encoding="utf-8"))
        r = run(["compare", base / "empty-run"], project)
        check("compare without screenshots → exit 2", r.returncode == 2)

        # --start: a fake server command is started, used and stopped (no orphan)
        port2 = free_port()
        card = project / ".tf" / "config" / "operations.json"
        card.parent.mkdir(parents=True)
        cmd = f"sh -c '{sys.executable} -m http.server {port2} --bind 127.0.0.1 & wait'"
        card.write_text(json.dumps({"preview": {"url": f"http://127.0.0.1:{port2}", "start": cmd,
                                                "routes": ["/"]}}), encoding="utf-8")
        run_dir2 = base / "run2"
        run_dir2.mkdir()
        if os.name != "nt":
            check("start: the port is free before", not answers(port2))
            r = run(["capture", run_dir2, "--label", "before", "--start"], project, envb)
            check("start: capture → exit 0", r.returncode == 0, r.stderr + r.stdout)
            check("start: screenshot taken", (run_dir2 / "screens" / "before" / "index@1280x800.png").is_file())
            time.sleep(0.5)
            check("start: the server is stopped afterwards (no orphan)", not answers(port2))
            # a server that already answers is not started again
            server3, port3 = serve({"/": "ok"})
            try:
                card.write_text(json.dumps({"preview": {"url": f"http://127.0.0.1:{port3}", "start": "false",
                                                        "routes": ["/"]}}), encoding="utf-8")
                r = run(["capture", run_dir2, "--label", "after", "--start"], project, envb)
                check("start: an answering server is not started", r.returncode == 0, r.stderr + r.stdout)
                check("start: routes from the operations card", (run_dir2 / "screens" / "after" / "index@1280x800.png").is_file())
            finally:
                server3.shutdown()
            # a server that never comes up → exit 3
            card.write_text(json.dumps({"preview": {"url": f"http://127.0.0.1:{free_port()}", "start": "false"}}),
                            encoding="utf-8")
            r = run(["capture", run_dir2, "--label", "after", "--start", "--timeout", "3"], project, envb)
            check("start: the server does not come up → exit 3", r.returncode == 3, r.stderr + r.stdout)
        # a URL answering nothing and no --start → exit 3 with a hint
        r = run(["capture", run_dir2, "--label", "after", "--url", f"http://127.0.0.1:{free_port()}/"], project, envb)
        check("no server and no --start → exit 3", r.returncode == 3 and "--start" in (r.stderr + r.stdout),
              r.stderr + r.stdout)

        # detection from package.json when there is no card
        card.unlink()
        (project / "package.json").write_text(json.dumps({"scripts": {"dev": "vite"},
                                                          "devDependencies": {"vite": "^5"}}), encoding="utf-8")
        d = ui.detect_preview(project)
        check("detect: vite → 5173 and dev script", d and d["url"] == "http://localhost:5173" and "dev" in d["start"], str(d))
        (project / "package.json").write_text(json.dumps({"scripts": {"start": "ng serve"},
                                                          "dependencies": {"@angular/core": "^17"}}), encoding="utf-8")
        d = ui.detect_preview(project)
        check("detect: angular → 4200 and npm start", d and d["url"] == "http://localhost:4200" and d["start"] == "npm start", str(d))
        (project / "package.json").write_text(json.dumps({"scripts": {"test": "jest"}}), encoding="utf-8")
        check("detect: a non-frontend project → None", ui.detect_preview(project) is None)

    # worth: the deterministic decision whether a visual check exists for the task
    with tempfile.TemporaryDirectory() as t:
        proj = Path(t) / "proj"

        def mk(name, files, criteria="Given x, when y, then z.", weight="normal", visual=None):
            rd = proj / ".tf" / "runs" / name
            rd.mkdir(parents=True)
            meta = {"key": name, "task_dir": f"docs/project/changes/{name}"}
            if visual:
                meta["visual"] = visual
            (rd / "run.json").write_text(json.dumps(meta), encoding="utf-8")
            docs = proj / "docs" / "project" / "changes" / name
            docs.mkdir(parents=True)
            (docs / "task.json").write_text(json.dumps({"weight": weight}), encoding="utf-8")
            (docs / "spec.md").write_text(f"# Spec\n\n## Acceptance criteria\n\n- AC-1: {criteria}\n", encoding="utf-8")
            (docs / "plan.md").write_text(f"# Plan\n- [ ] S1 — slice · criteria: AC-1 · files: {files} · verify: `x`\n", encoding="utf-8")
            return rd

        def worth(rd, *extra):
            r = run(["worth", rd, *extra], proj)
            return r.returncode, r.stdout

        code, out = worth(mk("B1", "api/handler.py, api/models.py"))
        check("worth: a backend-only plan → no", code == 1 and "no UI files" in out, out)
        code, out = worth(mk("B2", "src/i18n/pl.json"))
        check("worth: a one-string i18n change → no", code == 1, out)
        code, out = worth(mk("B3", "src/app/a.component.html"))
        check("worth: one UI file, no visible criterion → no", code == 1 and "below the thresholds" in out, out)
        code, out = worth(mk("B4", "src/app/a.component.html, src/app/b.component.html",
                             "Given the user opens the registration form, then a Save button is shown."))
        check("worth: two components and a criterion about a form → yes", code == 0 and "visible" in out, out)
        code, out = worth(mk("B5", "src/app/a.component.html, src/app/b.component.html"))
        check("worth: two UI files → yes", code == 0 and "2 UI files" in out, out)
        code, out = worth(mk("B6", "src/app/a.component.html", "Pokaż przycisk Zapisz."))
        check("worth: one UI file and a Polish visible criterion → yes", code == 0 and "przycisk" in out, out)
        code, out = worth(mk("B7", "a.html, b.html", weight="light"))
        check("worth: light weight without a visible criterion → no", code == 1 and "light" in out, out)
        code, out = worth(mk("B8", "a.html", "The page shows a banner.", weight="light"))
        check("worth: light weight with a visible criterion → yes", code == 0, out)
        code, out = worth(mk("B8q", "a.component.html, b.component.html", "Show a form.", weight="quick"))
        check("worth: the fast lane → not by default, one question at the end", code == 1 and "ask at the end" in out
              and "question" in out, out)
        code, out = worth(mk("B9", "a.component.html, b.component.html", "Show a form.", visual="off"))
        check("worth: --no-visual overrides yes", code == 1 and "--no-visual" in out, out)
        code, out = worth(mk("B10", "api/handler.py", visual="on"))
        check("worth: --visual overrides no", code == 0 and "--visual" in out, out)
        code, out = worth(mk("B11", "tests/a.html, Button.test.tsx, Button.stories.tsx"))
        check("worth: tests and stories only → no", code == 1, out)
        (proj / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (proj / ".tf" / "config" / "config.yaml").write_text("visual_check:\n  min_ui_files: 1\n", encoding="utf-8")
        code, out = worth(mk("B14", "src/app/a.component.html"))
        check("worth: a threshold from .tf/config/config.yaml is obeyed", code == 0 and "1 UI files" in out, out)
        (proj / ".tf" / "config" / "config.yaml").unlink()
        # the diff: changed UI lines against the base branch
        def g(*a):
            return subprocess.run(["git", "-C", str(proj), "-c", "user.email=t@e.x", "-c", "user.name=T",
                                   "-c", "commit.gpgsign=false", *a], capture_output=True, text=True)
        g("init", "-q", "-b", "main")
        g("commit", "-q", "--allow-empty", "-m", "init")
        g("checkout", "-q", "-b", "story/x")
        (proj / "big.css").write_text("a{}\n" * 40, encoding="utf-8")
        g("add", "big.css")
        g("commit", "-q", "-m", "style")
        code, out = worth(mk("B12", "api/x.py"), "--base", "main")
        check("worth: 40 changed UI lines in the diff → yes", code == 0 and "40 changed UI lines" in out, out)
        (proj / "big.css").write_text("a{}\n" * 5, encoding="utf-8")
        g("add", "big.css")
        g("commit", "-q", "-m", "shrink")
        code, out = worth(mk("B13", "api/x.py"), "--base", "main")
        check("worth: 5 changed UI lines → no", code == 1, out)

    # a real headless browser (skipped with a note when it is missing or too slow here)
    browser = ui.find_browser(os.environ)
    if browser:
        server, port = serve({"/": "<h1>Real</h1>"})
        with tempfile.TemporaryDirectory() as t:
            rd = Path(t) / "run"
            rd.mkdir()
            try:
                r = run(["capture", rd, "--label", "before", "--url", f"http://127.0.0.1:{port}", "--route", "/",
                         "--timeout", "60"], Path(t), {"CTF_BROWSER": browser})
                ok = r.returncode == 0 and (rd / "screens" / "before" / "index@1280x800.png").is_file()
                if ok:
                    check("real browser: PNG size", ui.png_size(rd / "screens" / "before" / "index@1280x800.png")[0] == 1280)
                elif os.environ.get("CTF_REQUIRE_BROWSER") == "1":
                    check("real browser: capture", False, r.stderr + r.stdout)
                else:
                    print(f"— test_ui_snap: real browser skipped ({(r.stderr + r.stdout).strip()[-120:]})")
            finally:
                server.shutdown()
    elif os.environ.get("CTF_REQUIRE_BROWSER") == "1":
        check("real browser: none found and CTF_REQUIRE_BROWSER=1", False)
    else:
        print("— test_ui_snap: real browser check skipped (no Chromium/Chrome)")

    print(f"{'✓' if not fails else '✗'} test_ui_snap: {'OK' if not fails else f'{len(fails)} errors'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
