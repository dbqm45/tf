#!/usr/bin/env python3
"""Registering the factory plugin for the project folder (core/factory/plugin_register.py): in the plugin layout install,
update and `--layout plugin` run `claude plugin marketplace add <abs .tf/.claude-plugin/local-marketplace.json> --scope
local` and `claude plugin install tf@<folder marketplace> --scope local`, so every Claude Code session in the folder (a
plain `claude`, the Desktop app) loads the factory. Idempotent; re-registers after the folder moved; without `claude` the
install still succeeds and prints both commands; `--layout default` and `tf uninstall` unregister; `tf doctor` reports
the state and `--fix` registers; `tf code` does not pass --plugin-dir to a registered folder; the shared settings.json
never gets an absolute path. A FAKE `claude` on PATH logs its argv and answers `plugin list --json` from a state file
(the real CLI is never called).
python3 tests/test_plugin_register.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
REGISTERED = "✓ Plugin registered for this folder (local scope)"
WARNING = "⚠ Plugin layout: only `tf code` loads the factory"
CLASSIC = "✓ Classic layout: the factory is in .claude/"

FAKE = r'''#!{py}
"""A fake Claude Code CLI: logs argv and cwd, keeps installs and marketplaces in a state file, edits the folder's
.claude/settings.local.json the way the real CLI does (local scope)."""
import json, os, sys
from pathlib import Path
log, state_f = os.environ["FAKE_CLAUDE_LOG"], Path(os.environ["FAKE_CLAUDE_STATE"])
a = sys.argv[1:]
if os.environ.get("FAKE_CLAUDE_FAIL"):    # e.g. the organization's settings gateway is unreachable
    print(os.environ["FAKE_CLAUDE_FAIL"], file=sys.stderr); sys.exit(1)
with open(log, "a", encoding="utf-8") as f:
    f.write(json.dumps({{"argv": a, "cwd": os.getcwd()}}) + "\n")
st = json.loads(state_f.read_text()) if state_f.is_file() else {{"installs": [], "markets": {{}}}}
loc = Path.cwd() / ".claude" / "settings.local.json"
s = json.loads(loc.read_text()) if loc.is_file() else {{}}
def save():
    state_f.write_text(json.dumps(st))
    loc.parent.mkdir(parents=True, exist_ok=True)
    loc.write_text(json.dumps(s, indent=2) + "\n")
if a[:2] == ["plugin", "list"]:
    print(json.dumps(st["installs"]))
elif a[:3] == ["plugin", "marketplace", "add"]:
    path = a[3]
    name = json.loads(Path(path).read_text())["name"]
    st["markets"][name] = path
    s.setdefault("extraKnownMarketplaces", {{}})[name] = {{"source": {{"source": "file", "path": path}}}}
    save()
elif a[:2] == ["plugin", "install"]:
    pid = a[2]
    path = st["markets"].get(pid.split("@")[1])
    if not path:
        print("marketplace not found"); sys.exit(1)
    st["installs"] = [x for x in st["installs"] if not (x["id"] == pid and x["projectPath"] == os.getcwd())]
    st["installs"].append({{"id": pid, "scope": "local", "enabled": True, "projectPath": os.getcwd(),
                           "readFromFolder": str(Path(path).parent.parent / "plugin")}})
    s.setdefault("enabledPlugins", {{}})[pid] = True
    save()
elif a[:2] in (["plugin", "uninstall"], ["plugin", "remove"]):
    pid = a[2]
    st["installs"] = [x for x in st["installs"] if not (x["id"] == pid and x["projectPath"] == os.getcwd())]
    (s.get("enabledPlugins") or {{}}).pop(pid, None)
    save()
elif a[:3] == ["plugin", "marketplace", "remove"]:
    name = a[3]
    st["markets"].pop(name, None)
    st["installs"] = [x for x in st["installs"] if not x["id"].endswith("@" + name)]
    (s.get("extraKnownMarketplaces") or {{}}).pop(name, None)
    save()
'''


def clean_path() -> str:
    """PATH without the real Claude Code CLI."""
    return os.pathsep.join(d for d in os.environ.get("PATH", "/usr/bin:/bin").split(os.pathsep)
                           if d and not (Path(d) / "claude").exists())


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t).resolve()
        fake_bin = base / "fakebin"
        fake_bin.mkdir()
        (fake_bin / "claude").write_text(FAKE.format(py=sys.executable), encoding="utf-8")
        (fake_bin / "claude").chmod(0o755)
        log, state = base / "claude.log", base / "claude-state.json"

        def env(fake: bool = True) -> dict:
            e = {"PATH": (str(fake_bin) + os.pathsep if fake else "") + clean_path(), "HOME": str(base),
                 "FAKE_CLAUDE_LOG": str(log), "FAKE_CLAUDE_STATE": str(state)}
            return e

        def calls() -> list[dict]:
            return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []

        def writes(since: int) -> list[list[str]]:
            return [c["argv"] for c in calls()[since:] if c["argv"][:2] != ["plugin", "list"]]

        def install(p: Path, *opts: str, fake: bool = True) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts],
                                  capture_output=True, text=True, timeout=600, env=env(fake))

        def update(p: Path, *opts: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, str(p / ".tf" / "factory" / "update.py"), "--yes", *opts], cwd=p,
                                  capture_output=True, text=True, timeout=900, env=env())

        def tf(p: Path, *args: str, fake: bool = True, extra: dict | None = None) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, ".tf/factory/tf.py", *args], cwd=p, capture_output=True, text=True,
                                  timeout=600, env={**env(fake), **(extra or {})})

        def project(name: str) -> Path:
            p = base / name
            p.mkdir()
            subprocess.run(["git", "init", "-q", str(p)], check=True)
            return p

        def reg(p: Path):
            sys.path.insert(0, str(p / ".tf" / "factory"))
            import importlib
            import plugin_register
            importlib.reload(plugin_register)
            sys.path.pop(0)
            return plugin_register

        def local(p: Path) -> dict:
            f = p / ".claude" / "settings.local.json"
            return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}

        # PR-1: a plugin-layout install registers the plugin with the absolute path, local scope, cwd = the project
        p = project("app")
        r = install(p)
        m = reg(p)
        mfile, pid = str(p / ".tf" / ".claude-plugin" / "local-marketplace.json"), m.plugin_id(p)
        w = writes(0)
        check(r.returncode == 0 and w == [["plugin", "marketplace", "add", mfile, "--scope", "local"],
                                          ["plugin", "install", pid, "--scope", "local"]]
              and all(c["cwd"] == str(p) for c in calls()) and REGISTERED in r.stdout and WARNING not in r.stdout,
              f"PR-1: install registers the plugin (abs path, local scope): {r.returncode} {w} {r.stdout[-500:]}")
        mk = json.loads(Path(mfile).read_text(encoding="utf-8"))
        s = local(p)
        check(mk["name"] == m.market_name(p) and mk["plugins"][0]["source"] == "./plugin"
              and mk["plugins"][0]["name"] == "tf" and s.get("enabledPlugins", {}).get(pid) is True
              and pid.startswith("tf@tf-app-"),
              f"PR-2: the folder's marketplace file and settings.local.json: {mk} {s}")
        desc = json.loads((p / ".tf" / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        check("Loaded only by a factory session" not in json.dumps(desc),
              f"PR-3: marketplace.json no longer says only tf code loads the plugin: {desc}")

        # PR-4: idempotent — an update of a registered folder runs only `plugin list`
        n = len(calls())
        r = update(p, "--force")
        check(r.returncode == 0 and writes(n) == [] and REGISTERED in r.stdout,
              f"PR-4: nothing is registered again when already registered: {writes(n)} {r.stdout[-300:]}")

        # PR-5: tf doctor reports the registration; tf code does not pass --plugin-dir to a registered folder
        r = tf(p, "doctor")
        check("✓ plugin: registered for this folder" in r.stdout and pid in r.stdout,
              f"PR-5: tf doctor reports the registration: {r.stdout[:600]}")

        # PR-5b: claude cannot reach the organization's gateway → a hint about the company network / VPN;
        # inside a sandboxed tf code session → a hint to run it in a plain terminal
        gw = ("Couldn't load settings from Cloud gateway https://gw.example.com/settings. Check your connection, and join "
              "your organization's network if the gateway needs it")
        r = tf(p, "doctor", extra={"FAKE_CLAUDE_FAIL": gw})
        check("Cloud gateway" in r.stdout and "connect to the company network or VPN" in r.stdout
              and "sandboxed session" not in r.stdout,
              f"PR-5b: a gateway failure names the VPN: {r.stdout[:900]}")
        r = tf(p, "doctor", extra={"FAKE_CLAUDE_FAIL": gw, "TF_ISOLATION": "sandbox", "CLAUDECODE": "1"})
        check("connect to the company network or VPN" in r.stdout and "sandboxed session (tf code)" in r.stdout,
              f"PR-5c: inside a sandboxed tf code session → run it in a plain terminal: {r.stdout[:900]}")
        r = tf(p, "doctor", extra={"FAKE_CLAUDE_FAIL": "Unknown option --json"})
        check("company network or VPN" not in r.stdout, f"PR-5d: no VPN hint for an unrelated failure: {r.stdout[:600]}")
        n = len(calls())
        r = tf(p, "code", "--continue", extra={"TF_CLAUDE": str(fake_bin / "claude")})
        argv = (calls()[n:] or [{"argv": []}])[-1]["argv"]
        check("--plugin-dir" not in argv and "--settings" in argv and argv[-1] == "--continue",
              f"PR-6: tf code in a registered folder loads the plugin once (no --plugin-dir): {argv} {r.stderr[-300:]}")

        # PR-7: the project folder moved → doctor says so, the update re-registers with the new path
        q = base / "moved-app"
        p.rename(q)
        r = tf(q, "doctor")
        check(WARNING in r.stdout and "claude plugin install" in r.stdout,
              f"PR-7: tf doctor after a move: not registered, with the commands: {r.stdout[:700]}")
        n = len(calls())
        r = update(q, "--force")
        m2 = reg(q)
        w = writes(n)
        qfile = str(q / ".tf" / ".claude-plugin" / "local-marketplace.json")
        check(r.returncode == 0 and ["plugin", "marketplace", "remove", m.market_name(p), "--scope", "local"] in w
              and w[-2:] == [["plugin", "marketplace", "add", qfile, "--scope", "local"],
                             ["plugin", "install", m2.plugin_id(q), "--scope", "local"]]
              and set(local(q).get("extraKnownMarketplaces") or {}) == {m2.market_name(q)}
              and set(local(q).get("enabledPlugins") or {}) == {m2.plugin_id(q)} and REGISTERED in r.stdout,
              f"PR-8: re-registered after the move, the old registration dropped: {w} {local(q)} {r.stdout[-300:]}")

        # PR-9: --layout default unregisters (uninstall + marketplace remove, local scope), no keys left
        n = len(calls())
        r = update(q, "--layout", "default")
        w = writes(n)
        s = local(q)
        check(r.returncode == 0 and ["plugin", "uninstall", m2.plugin_id(q), "--scope", "local"] in w
              and ["plugin", "marketplace", "remove", m2.market_name(q), "--scope", "local"] in w
              and "enabledPlugins" not in s and "extraKnownMarketplaces" not in s and CLASSIC in r.stdout
              and not (q / ".tf" / ".claude-plugin").exists() and "local-marketplace" not in r.stdout,
              f"PR-9: --layout default unregisters the plugin: {w} {s} {r.stdout[-500:]}")

        # PR-10: no `claude` on PATH → the install succeeds and prints the warning with both commands
        log.unlink(missing_ok=True)
        n2 = project("nocli")
        r = install(n2, fake=False)
        m3 = reg(n2)
        check(r.returncode == 0 and WARNING in r.stdout and all(c in r.stdout for c in m3.commands(n2))
              and REGISTERED not in r.stdout and not calls()
              and (n2 / ".tf" / ".claude-plugin" / "local-marketplace.json").is_file(),
              f"PR-10: without claude: the warning and both commands, install ok: {r.returncode} {r.stdout[-700:]}")

        # PR-11: tf doctor reports it unregistered, --fix registers it
        r = tf(n2, "doctor")
        check(WARNING in r.stdout and "not installed for this folder" in r.stdout,
              f"PR-11: tf doctor reports the missing registration: {r.stdout[:600]}")
        r = tf(n2, "doctor", "--fix")
        r2 = tf(n2, "doctor")
        check(REGISTERED in r.stdout and "✓ plugin: registered for this folder" in r2.stdout
              and ["plugin", "install", m3.plugin_id(n2), "--scope", "local"] in writes(0),
              f"PR-12: tf doctor --fix registers the plugin: {r.stdout[:500]} / {r2.stdout[:300]}")

        # PR-13: TF_NO_PLUGIN_REGISTER skips the CLI (and says so with the commands)
        n = len(calls())
        n3 = project("skip")
        r = subprocess.run([sys.executable, str(INSTALL), str(n3), "--yes", "--packs", "none"], capture_output=True,
                           text=True, timeout=600, env={**env(), "TF_NO_PLUGIN_REGISTER": "1"})
        check(r.returncode == 0 and len(calls()) == n and "TF_NO_PLUGIN_REGISTER" in r.stdout and WARNING in r.stdout,
              f"PR-13: TF_NO_PLUGIN_REGISTER skips the registration: {calls()[n:]} {r.stdout[-400:]}")

        # PR-14: team mode: the registration goes to settings.local.json (git-ignored), never the shared settings.json
        tm = project("team")
        r = install(tm, "--shared")
        shared = (tm / ".claude" / "settings.json").read_text(encoding="utf-8") \
            if (tm / ".claude" / "settings.json").is_file() else ""
        ign = subprocess.run(["git", "check-ignore", ".claude/settings.local.json",
                              ".tf/.claude-plugin/local-marketplace.json"], cwd=tm, capture_output=True, text=True)
        check(r.returncode == 0 and REGISTERED in r.stdout and str(base) not in shared
              and "extraKnownMarketplaces" not in shared and "enabledPlugins" not in shared
              and reg(tm).plugin_id(tm) in json.dumps(local(tm)) and len(ign.stdout.split()) == 2,
              f"PR-14: team mode registers locally, settings.json without an absolute path, both git-ignored: "
              f"{r.returncode} {shared[:200]!r} {ign.stdout!r} {r.stdout[-300:]}")
        r = update(tm, "--layout", "default")
        shared = (tm / ".claude" / "settings.json").read_text(encoding="utf-8")
        check(r.returncode == 0 and str(base) not in shared and "enabledPlugins" not in shared
              and "enabledPlugins" not in local(tm),
              f"PR-15: team mode back to classic: settings.json without an absolute path, unregistered: {shared[:300]}")

        # PR-16: tf uninstall removes the registration
        n = len(calls())
        r = tf(n2, "uninstall", "--yes")
        check(r.returncode == 0 and ["plugin", "uninstall", m3.plugin_id(n2), "--scope", "local"] in writes(n)
              and "enabledPlugins" not in local(n2),
              f"PR-16: tf uninstall unregisters the plugin: {writes(n)} {local(n2)} {r.stdout[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} plugin registration tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
