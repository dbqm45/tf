#!/usr/bin/env python3
"""TYMCZASOWE (usunąć przed scaleniem): diagnoza zawieszeń Chromium w test_fetch_page na runnerze CI."""
import http.server, os, subprocess, sys, tempfile, threading, time, shutil

PAGE = b"<!doctype html><html><body><div id=a></div><script>document.getElementById('a').textContent='ok-js'</script></body></html>"


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.send_header("Content-Length", str(len(PAGE)))
        self.end_headers(); self.wfile.write(PAGE)

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/"
browser = sys.argv[1]
n = int(sys.argv[2])
print(subprocess.run([browser, "--version"], capture_output=True, text=True).stdout.strip(), flush=True)
ROOT = ["--no-sandbox"] if os.geteuid() == 0 else []   # jak fetch_page: root bez piaskownicy
BASE = ROOT + ["--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-sync", "--disable-background-networking", "--mute-audio", "--disable-dev-shm-usage"]
VARIANTS = {
    "A-obecne": (BASE + ["--virtual-time-budget=5000"], {}),
    "B-bez-virtual-time": (BASE, {}),
    "C-bez-dbus": (BASE + ["--virtual-time-budget=5000"], {"DBUS_SESSION_BUS_ADDRESS": "disabled:"}),
}
for name, (flags, extra) in VARIANTS.items():
    times, hangs = [], 0
    for i in range(n):
        prof = tempfile.mkdtemp()
        env = {**os.environ, **extra}
        t = time.time()
        p = subprocess.Popen([browser, *flags, f"--user-data-dir={prof}", "--dump-dom", url], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True, env=env)
        try:
            out, err = p.communicate(timeout=60)
            ok = b"ok-js" in out
            if ok:
                times.append(time.time() - t)
            else:
                print(f"  {name} #{i}: brak treści, kod {p.returncode}: {err.decode(errors='replace')[-400:]}", flush=True)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9); out, err = p.communicate()
            hangs += 1
            print(f"  {name} #{i}: ZAWIESZENIE 60 s; stderr:\n{err.decode(errors='replace')[-1500:]}", flush=True)
        shutil.rmtree(prof, ignore_errors=True)
    ts = sorted(times)
    print(f"{name}: {len(times)} ok, {hangs} zawieszeń; czas mediana {ts[len(ts)//2]:.1f} s, max {ts[-1]:.1f} s" if ts
          else f"{name}: 0 ok, {hangs} zawieszeń", flush=True)
