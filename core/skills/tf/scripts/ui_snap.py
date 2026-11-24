#!/usr/bin/env python3
"""Screenshots of the screens a UI change touches, before and after, for the /tf-task loop. The agent LOOKS at them (the Read
tool shows images) against the acceptance criteria; the PR description lists the result.

    ui_snap.py capture <run_dir> --label before|after [--url URL ...] [--route /path ...] [--viewport 1280x800,390x844]
                                  [--start [COMMAND]] [--timeout S] [--browser PATH]
    ui_snap.py compare <run_dir>
    ui_snap.py worth <run_dir> [--base BRANCH]      # is a visual check worth it? yes/no with reasons; exit 0 yes, 1 no

`worth` decides deterministically from the UI files of the task (the plan's `files:` and, with a base branch, the diff):
no UI files = no visual check at all; yes when there are at least `visual_check.min_ui_files` of them, or at least
`visual_check.min_ui_lines` changed UI lines, or an acceptance criterion names something visible
(`visual_check.keywords`); the light weight needs such a criterion. `--visual` / `--no-visual` of the /tf-task command
(recorded in run.json) win. The thresholds: `.tf/factory/config.yaml`, overridden in `.tf/config/config.yaml`.

`capture` writes `<run_dir>/screens/<label>/<route-slug>@<W>x<H>.png` and `screens/<label>/index.json`; `compare` pairs
before/after by route and viewport (same sha256 = identical) and writes `screens/compare.md`.
Where the addresses come from, in order: `--url` / `--route`; the operations card `.tf/config/operations.json`
(`{"preview": {"url": "http://localhost:4200", "start": "npm start", "routes": ["/", "/login"]}}`); detection from
package.json (the dev/start/serve script, the framework's default port) — what was assumed is printed.
Only localhost / 127.0.0.1 / [::1] are opened: no data leaves the machine. `--start` starts the dev server (the command
after it, else `preview.start`, else the detected script) in its own process group, waits until the address answers,
and stops it with its children at the end; an address that already answers is left alone.

The browser: CTF_BROWSER, Chromium/Chrome/Edge from PATH or known paths (headless, a temporary profile); without one,
`node_modules/.bin/playwright` of the project when it exists. Nothing is installed.
Exit codes (capture, compare): 0 done, 1 a screenshot failed, 2 call error (also a non-local address), 3 no browser or the server did not
start (a message for the human). Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CARD = Path(".tf") / "config" / "operations.json"
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
DEFAULT_VIEWPORT = "1280x800"
# The one place that says what a "UI file" is (run_state.py pr-body imports it; the tf skill refers to it).
UI_FILE = re.compile(r"\.(html?|css|scss|sass|less|vue|svelte|jsx|tsx|astro|cshtml|razor|ejs|hbs|xaml)$", re.I)
NOT_UI = re.compile(r"(^|/)(tests?|__tests__|e2e|node_modules)/|\.(test|spec|stories)\.[a-z]+$", re.I)
FRAMEWORKS = (("@angular/core", 4200), ("next", 3000), ("react-scripts", 3000), ("nuxt", 3000), ("astro", 4321),
              ("@sveltejs/kit", 5173), ("vite", 5173))
MAC_APPS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium")
WIN_APPS = ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe",
            "Chromium/Application/chrome.exe")
NAMES = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "microsoft-edge",
         "microsoft-edge-stable", "msedge")


DEFAULT_VISUAL = {   # the fallback when the factory configuration cannot be read; the values live in config.yaml (visual_check)
    "min_ui_files": 2, "min_ui_lines": 30,
    "keywords": ["screen", "page", "button", "form", "modal", "dialog", "layout", "error message", "banner", "menu",
                 "ekran", "stron", "przycisk", "formularz", "komunikat", "okno", "układ", "baner", "menu"]}
BASES = ("origin/main", "main", "origin/master", "master")
PLAN_SLICE = re.compile(r"^\s*- \[[ xX]\]\s+S\d+\s*[—-]")
PLAN_FILES = re.compile(r"files:\s*([^·]+)")
AC_LINE = re.compile(r"^\s*[-*]\s*AC-\d+\s*:\s*(.+)$", re.M)


class Fail(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


# ---- small pure helpers -------------------------------------------------------------------------------------------

def is_ui_file(path: str) -> bool:
    p = path.replace("\\", "/")
    return bool(UI_FILE.search(p)) and not NOT_UI.search(p)


def parse_viewports(text: str):
    out = []
    for part in text.split(","):
        m = re.fullmatch(r"\s*(\d{2,5})x(\d{2,5})\s*", part)
        if not m:
            return None
        out.append((int(m.group(1)), int(m.group(2))))
    return out or None


def route_slug(route: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", route).strip("-")
    return slug[:80] or "index"


def is_local(url: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(url)
        parts.port  # noqa: B018 — a bad port raises ValueError
    except ValueError:
        return False
    return (parts.scheme in ("http", "https") and parts.hostname in LOCAL_HOSTS and parts.username is None
            and parts.password is None)


def png_size(path: Path):
    """(width, height) from the IHDR chunk, or None when it is not a PNG."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---- the address: card, detection ---------------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def detect_preview(root: Path):
    """{"url", "start", "routes"} from package.json (a frontend framework and its dev script), else None."""
    pkg = _read_json(root / "package.json")
    deps = {**(pkg.get("devDependencies") or {}), **(pkg.get("dependencies") or {})}
    port = next((p for name, p in FRAMEWORKS if name in deps), None)
    if port is None:
        return None
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    pm = next((n for lock, n in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"),
                                 ("bun.lockb", "bun")) if (root / lock).is_file()), "npm")
    name = next((n for n in ("dev", "start", "serve") if isinstance(scripts.get(n), str)), None)
    start = "" if name is None else (f"{pm} start" if name == "start" and pm == "npm" else f"{pm} run {name}")
    return {"url": f"http://localhost:{port}", "start": start, "routes": ["/"]}


def resolve_targets(args, root: Path):
    """(list of (base_url, route), start command, notes). Raises Fail(2) when no address can be determined."""
    notes = []
    card = _read_json(root / CARD).get("preview")
    card = card if isinstance(card, dict) else {}
    start = card.get("start") if isinstance(card.get("start"), str) else ""
    if args.url:
        bases = []
        for u in args.url:
            parts = urllib.parse.urlsplit(u)
            bases.append((f"{parts.scheme}://{parts.netloc}", (parts.path or "/") + (f"?{parts.query}" if parts.query else "")))
        if args.route:
            targets = [(bases[0][0], r) for r in args.route]
        else:
            targets = bases
        return targets, start, notes
    url = card.get("url") if isinstance(card.get("url"), str) and card.get("url") else None
    routes = [r for r in (card.get("routes") or []) if isinstance(r, str)] if url else []
    if not url:
        det = detect_preview(root)
        if not det:
            raise Fail(2, "no address to capture: give --url, or fill `preview.url` in .tf/config/operations.json "
                          "(no frontend framework found in package.json)")
        url, start = det["url"], start or det["start"]
        notes.append(f"assumed from package.json: {url}" + (f", started with `{start}`" if start else ""))
    if args.route:
        routes = args.route
    return [(url.rstrip("/"), r) for r in (routes or ["/"])], start, notes


# ---- browser ------------------------------------------------------------------------------------------------------

def _executable(path) -> bool:
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def find_browser(env=None, extra=None):
    """Path to Chromium / Chrome / Edge, or None: CTF_BROWSER, PATH, known paths, the Playwright browser."""
    env = os.environ if env is None else env
    if _executable(env.get("CTF_BROWSER")):
        return env["CTF_BROWSER"]
    for name in NAMES:
        found = shutil.which(name, path=env.get("PATH", ""))
        if found:
            return found
    candidates = list(MAC_APPS) if extra is None else list(extra)
    if extra is None:
        for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            if env.get(var):
                candidates += [os.path.join(env[var], *rel.split("/")) for rel in WIN_APPS]
    if env.get("PLAYWRIGHT_BROWSERS_PATH"):
        candidates += sorted(glob.glob(os.path.join(env["PLAYWRIGHT_BROWSERS_PATH"], "chromium-*", "chrome-linux",
                                                    "chrome")), reverse=True)
    return next((c for c in candidates if _executable(c)), None)


def kill_tree(proc: subprocess.Popen, sig=None) -> None:
    """Ends the process with its children (a process group, SIGKILL by default; Windows: taskkill /T). The default is
    not `signal.SIGKILL` in the signature: Windows has no SIGKILL, and importing this module (run_state.py does) failed."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=20)
        else:
            os.killpg(proc.pid, sig if sig is not None else signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError, subprocess.SubprocessError):
        pass


def _run_group(cmd, timeout):
    """Runs the command in its own process group; after the timeout the whole group is killed. -> (code, stderr) or (None, stderr)."""
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                start_new_session=os.name != "nt")
    except OSError as e:
        raise Fail(1, f"could not start the browser: {e}") from None
    try:
        _, err = proc.communicate(timeout=timeout)
        return proc.returncode, err
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        try:
            _, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            err = b""
        return None, err


def _reason(stderr: bytes) -> str:
    lines = (stderr or b"").decode("utf-8", errors="replace").strip().splitlines()
    return (next((ln for ln in lines if ":FATAL:" in ln), lines[-1]) if lines else "no output").strip()[:300]


def shoot_chromium(browser: str, url: str, out: Path, size, timeout: int) -> None:
    profile = tempfile.mkdtemp(prefix="ui-snap-")
    try:
        cmd = [browser, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--disable-sync", "--disable-background-networking", "--mute-audio",
               "--disable-dev-shm-usage", "--no-proxy-server", "--hide-scrollbars", f"--user-data-dir={profile}",
               "--virtual-time-budget=5000", f"--window-size={size[0]},{size[1]}", f"--screenshot={out}"]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")  # Chromium does not start as root with its own sandbox
        cmd.append(url)
        code, err = _run_group(cmd, timeout)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if code is None:
        raise Fail(1, f"{url}: time limit of {timeout} s exceeded; browser: {_reason(err)}")
    if code != 0 or png_size(out) is None:
        raise Fail(1, f"{url}: the browser exited with code {code}: {_reason(err)}")


def shoot_playwright(binary: Path, url: str, out: Path, size, timeout: int) -> None:
    code, err = _run_group([str(binary), "screenshot", f"--viewport-size={size[0]},{size[1]}", url, str(out)], timeout)
    if code != 0 or png_size(out) is None:
        raise Fail(1, f"{url}: playwright failed ({code}): {_reason(err)}")


def pick_shooter(args, root: Path):
    """-> (callable(url, out, size, timeout), name). Raises Fail(3) with a message for the human."""
    browser = args.browser if args.browser and _executable(args.browser) else find_browser()
    if browser:
        return (lambda url, out, size, timeout: shoot_chromium(browser, url, out, size, timeout)), browser
    exe = "playwright.cmd" if os.name == "nt" else "playwright"
    pw = root / "node_modules" / ".bin" / exe
    if pw.is_file():
        return (lambda url, out, size, timeout: shoot_playwright(pw, url, out, size, timeout)), str(pw)
    raise Fail(3, "no browser for screenshots: Chromium, Chrome or Edge was not found (set CTF_BROWSER to its path, or "
                  "install one yourself — the script installs nothing); the project has no node_modules/.bin/playwright either")


# ---- dev server ---------------------------------------------------------------------------------------------------

def answers(url: str, timeout: float = 2.0) -> bool:
    """Whether something answers HTTP at the address (any status counts)."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # a local address never goes through a proxy
    try:
        opener.open(url, timeout=timeout).close()
        return True
    except urllib.error.HTTPError:
        return True
    except (OSError, ValueError):
        return False


class DevServer:
    """Starts the command in its own process group, waits until the address answers; stop() ends the whole group."""

    def __init__(self, command: str, url: str, log: Path, wait: float):
        self.proc = None
        log.parent.mkdir(parents=True, exist_ok=True)
        self.log = open(log, "wb")
        try:
            argv = command if os.name == "nt" else shlex.split(command)
            self.proc = subprocess.Popen(argv, stdout=self.log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                         shell=os.name == "nt", start_new_session=os.name != "nt")
        except (OSError, ValueError) as e:
            self.log.close()
            raise Fail(3, f"could not start the dev server `{command}`: {e}") from None
        end = time.monotonic() + wait
        while time.monotonic() < end:
            if self.proc.poll() is not None:
                break
            if answers(url):
                return
            time.sleep(0.5)
        tail = ""
        try:
            tail = log.read_text(encoding="utf-8", errors="replace").strip()[-400:]
        except OSError:
            pass
        died = self.proc.poll() is not None
        self.stop()
        raise Fail(3, f"the dev server `{command}` " + (f"exited with code {self.proc.returncode}" if died
                   else f"did not answer at {url} within {wait:g} s") + (f"; its output: {tail}" if tail else ""))

    def stop(self) -> None:
        if self.proc is not None:
            kill_tree(self.proc, signal.SIGTERM if os.name != "nt" else None)
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                kill_tree(self.proc)
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
            if os.name != "nt":
                kill_tree(self.proc)   # stragglers of the group that ignored SIGTERM
        self.log.close()



# ---- is it worth it: the one deterministic decision (the loop, the PR section and the dashboard use it) ---------------

def visual_config(project: Path) -> dict:
    """`visual_check` of the factory configuration (engine <- company <- project <- person), over the defaults."""
    cfg = dict(DEFAULT_VISUAL)
    for base in (next((p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs.py").is_file()),
                      project), project):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("tf_packs_cfg", base / ".tf" / "factory" / "packs.py")
            packs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(packs)
            own = packs.load_config(project).get("visual_check")
            if isinstance(own, dict):
                cfg.update({k: v for k, v in own.items() if k in cfg})
            break
        except Exception:  # noqa: BLE001 — no configuration means the defaults, not a failure
            continue
    return cfg


def docs_dir(run_dir: Path, meta: dict) -> Path:
    rel = meta.get("task_dir")
    return run_dir.resolve().parents[2] / rel if rel else run_dir


def plan_files(docs: Path) -> list[str]:
    """The files named in the `files:` fields of the plan's slices."""
    try:
        text = (docs / "plan.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for ln in text.splitlines():
        f = PLAN_FILES.search(ln) if PLAN_SLICE.match(ln) else None
        if f:
            out += [x for x in re.split(r"[,\s]+", f.group(1).replace("`", "")) if x]
    return out


def pick_base(project: Path, base: str | None) -> str | None:
    for cand in ([base] if base else BASES):
        try:
            r = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "--quiet", f"{cand}^{{commit}}"],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode == 0:
            return cand
    return None


def diff_stat(project: Path, base: str | None) -> dict:
    """{path: changed lines} of the branch against the base; empty without a base."""
    if not base:
        return {}
    try:
        r = subprocess.run(["git", "-C", str(project), "diff", "--numstat", f"{base}...HEAD"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return {}
    out = {}
    for ln in (r.stdout.splitlines() if r.returncode == 0 else []):
        parts = ln.split("\t")
        if len(parts) == 3:
            out[parts[2]] = (int(parts[0]) if parts[0].isdigit() else 0) + (int(parts[1]) if parts[1].isdigit() else 0)
    return out


def worth(run_dir: Path, project: Path, base: str | None = None) -> dict:
    """{"yes": bool, "forced": "on"|"off"|None, "ui_files": [...], "reasons": [...]}. Decided from run.json (`visual`:
    the human's --visual / --no-visual), the UI files of the plan and of the diff, the criteria and the weight."""
    meta = _read_json(run_dir / "run.json")
    docs = docs_dir(run_dir, meta)
    cfg = visual_config(project)
    stat = diff_stat(project, pick_base(project, base) if base is not False else None)
    files = sorted({f for f in [*plan_files(docs), *stat] if is_ui_file(f)})
    forced = meta.get("visual") if meta.get("visual") in ("on", "off") else None
    if forced == "off":
        return {"yes": False, "forced": "off", "ui_files": files, "reasons": ["switched off by --no-visual"]}
    if forced == "on":
        return {"yes": True, "forced": "on", "ui_files": files, "reasons": ["switched on by --visual"]}
    if not files:
        return {"yes": False, "forced": None, "ui_files": [], "reasons": ["no UI files in the plan or the diff"]}
    try:
        spec = (docs / "spec.md").read_text(encoding="utf-8", errors="replace")
        crit = " ".join(AC_LINE.findall(spec))
    except OSError:
        crit = ""
    if not crit:
        try:
            crit = (docs / "ticket.md").read_text(encoding="utf-8", errors="replace")
        except OSError:
            crit = ""
    words = [w for w in cfg["keywords"] if isinstance(w, str) and w]
    hit = next((w for w in words if re.search(r"(?<!\w)" + re.escape(w), crit, re.I)), None)
    lines = sum(n for f, n in stat.items() if f in files)
    short = ", ".join(files[:3]) + (f" and {len(files) - 3} more" if len(files) > 3 else "")
    light = _read_json(docs / "task.json").get("weight") == "light"
    reasons = []
    if hit:
        reasons.append(f"a criterion names something visible (\"{hit}\")")
    if not light and len(files) >= int(cfg["min_ui_files"]):
        reasons.append(f"{len(files)} UI files ({short})")
    if not light and lines >= int(cfg["min_ui_lines"]):
        reasons.append(f"{lines} changed UI lines")
    if reasons:
        return {"yes": True, "forced": None, "ui_files": files, "reasons": reasons}
    why = ("a light task without a criterion about something visible" if light else
           f"only {len(files)} UI file(s) ({short}) and {lines} changed UI lines, below the thresholds "
           f"({cfg['min_ui_files']} files / {cfg['min_ui_lines']} lines), and no criterion about something visible")
    return {"yes": False, "forced": None, "ui_files": files, "reasons": [why]}


def cmd_worth(args) -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    run_dir = Path(args.run_dir)
    if not (run_dir / "run.json").is_file():
        raise Fail(2, f"no run.json in {run_dir}")
    res = worth(run_dir, root, args.base)
    print(f"visual check: {'yes' if res['yes'] else 'no'} — " + "; ".join(res["reasons"]))
    return 0 if res["yes"] else 1


# ---- commands -----------------------------------------------------------------------------------------------------

def cmd_capture(args) -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    run_dir = Path(args.run_dir)
    sizes = parse_viewports(args.viewport)
    if not sizes:
        raise Fail(2, f"bad --viewport {args.viewport!r}: expected e.g. 1280x800,390x844")
    targets, start_cmd, notes = resolve_targets(args, root)
    for base, route in targets:
        if not route.startswith("/"):
            raise Fail(2, f"a route starts with /: {route!r}")
        if not is_local(base + route):
            raise Fail(2, f"only local addresses (localhost, 127.0.0.1, [::1]) are opened, got {base + route!r}")
    shoot, via = pick_shooter(args, root)
    notes.append(f"browser: {via}")
    bases = list(dict.fromkeys(b for b, _ in targets))
    server = None
    try:
        if not all(answers(b) for b in bases):
            if args.start is None:
                raise Fail(3, f"nothing answers at {', '.join(b for b in bases if not answers(b))}: start the dev server "
                              "yourself, or add --start (the command after it, else `preview.start` of the operations card)")
            command = args.start if isinstance(args.start, str) else start_cmd
            if not command:
                raise Fail(3, "--start without a command: give it (`--start \"npm run dev\"`) or fill `preview.start` "
                              "in .tf/config/operations.json")
            if len(bases) != 1:
                raise Fail(2, "--start works with one base address")
            notes.append(f"started: {command}")
            server = DevServer(command, bases[0], run_dir / "screens" / "server.log", args.start_timeout)
        out_dir = run_dir / "screens" / args.label
        shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        shots, errors = [], []
        for base, route in targets:
            for size in sizes:
                name = f"{route_slug(route)}@{size[0]}x{size[1]}.png"
                try:
                    shoot(base + route, out_dir / name, size, args.timeout)
                except Fail as e:
                    errors.append(str(e))
                    continue
                dim = png_size(out_dir / name) or (0, 0)
                shots.append({"url": base + route, "route": route, "viewport": f"{size[0]}x{size[1]}", "file": name,
                              "sha256": sha256(out_dir / name), "width": dim[0], "height": dim[1],
                              "time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")})
        (out_dir / "index.json").write_text(json.dumps({"label": args.label, "shots": shots, "errors": errors},
                                                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    finally:
        if server is not None:
            server.stop()
    for n in notes:
        print(f"· {n}")
    for s in shots:
        print(f"✓ {s['route']} @{s['viewport']} → screens/{args.label}/{s['file']} ({s['width']}x{s['height']})")
    for e in errors:
        print(f"✗ {e}", file=sys.stderr)
    return 1 if errors else 0


def _load_index(run_dir: Path, label: str) -> dict:
    data = _read_json(run_dir / "screens" / label / "index.json")
    return {(s["route"], s["viewport"]): s for s in data.get("shots", []) if isinstance(s, dict)
            and "route" in s and "viewport" in s}


def cmd_compare(args) -> int:
    run_dir = Path(args.run_dir)
    before, after = _load_index(run_dir, "before"), _load_index(run_dir, "after")
    if not before and not after:
        raise Fail(2, f"no screenshots in {run_dir / 'screens'} — run `capture --label before` and `--label after` first")
    rows, counts = [], {"identical": 0, "changed": 0, "only before": 0, "only after": 0}
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key), after.get(key)
        result = ("only before" if a is None else "only after" if b is None else
                  "identical" if b.get("sha256") == a.get("sha256") else "changed")
        counts[result] += 1
        rows.append(f"| {key[0]} | {key[1]} | {result} | "
                    f"{('screens/before/' + b['file']) if b else '—'} | {('screens/after/' + a['file']) if a else '—'} |")
    text = ("# Visual comparison\n\n"
            + ", ".join(f"{n} {k}" for k, n in counts.items()) + "\n\n"
            "| route | viewport | result | before | after |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    (run_dir / "screens" / "compare.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Screenshots before/after a UI change (local addresses only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("run_dir")
    cap.add_argument("--label", required=True, choices=("before", "after"))
    cap.add_argument("--url", action="append", help="address (repeat); with --route it is the base")
    cap.add_argument("--route", action="append", help="path on the base address, e.g. /login (repeat)")
    cap.add_argument("--viewport", default=DEFAULT_VIEWPORT, help=f"WxH list (default {DEFAULT_VIEWPORT})")
    cap.add_argument("--start", nargs="?", const=True, default=None, metavar="COMMAND",
                     help="start the dev server (command, else preview.start / detected) and stop it afterwards")
    cap.add_argument("--start-timeout", type=float, default=90, help="seconds to wait for the dev server (default 90)")
    cap.add_argument("--timeout", type=int, default=60, help="seconds per screenshot (default 60)")
    cap.add_argument("--browser", help="path to Chromium / Chrome / Edge (otherwise CTF_BROWSER or a search)")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("run_dir")
    wt = sub.add_parser("worth")
    wt.add_argument("run_dir")
    wt.add_argument("--base", default=None, help="the default branch, to see the diff (otherwise: the plan only)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return {"capture": cmd_capture, "compare": cmd_compare, "worth": cmd_worth}[args.cmd](args)
    except Fail as e:
        print(f"ui_snap: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    raise SystemExit(main())
