#!/usr/bin/env python3
"""Tryb fabryki, krok T4 (docs/plans/2026-11-20-tryb-fabryki-plan.md): w układzie wtyczki `tf work --once` woła agenta
z wtyczką i ustawieniami sesji fabryki z worktree zadania, a `tf cloud-setup` przygotowuje środowisko chmurowe
(marketplace katalogowy w .tf/, włączenie wtyczki i ustawienia sesji w ~/.claude/settings.json kontenera).
Bez wywołań modelu: agent i katalog domowy są podstawione.
python3 tests/test_plugin_work_cloud.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
FAKE = "import json, os, sys\nopen(os.environ['TF_FAKE_OUT'], 'w').write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}))\n"


def env(base: Path, home: Path, **extra: str) -> dict:
    return {"TF_NO_PLUGIN_REGISTER": "1", "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "GIT_AUTHOR_NAME": "T",
            "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
            "TF_WORK_AGENT": f"{sys.executable} {base / 'fake.py'}", "TF_FAKE_OUT": str(base / "argv.json"),
            "TF_WORK_ENV_ALLOW": "TF_FAKE_OUT", **extra}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        home = base / "home"
        home.mkdir()
        (base / "fake.py").write_text(FAKE, encoding="utf-8")
        p = base / "proj"
        p.mkdir()
        e = env(base, home)
        subprocess.run(["git", "init", "-q", "-b", "main", str(p)], check=True)
        (p / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(p), "add", "-A"], check=True, env=e)
        subprocess.run(["git", "-C", str(p), "-c", "commit.gpgsign=false", "commit", "-qm", "init"], check=True, env=e)
        r = subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", "--layout", "plugin"],
                           capture_output=True, text=True, timeout=600, env=e)
        assert r.returncode == 0, r.stdout[-600:] + r.stderr[-600:]
        mk = p / ".tf" / ".claude-plugin" / "marketplace.json"
        try:
            market = json.loads(mk.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            market = {}
        check(any(x.get("name") == "tf" and x.get("source") == "./plugin" for x in market.get("plugins") or []),
              f"PW-1: marketplace katalogowy w .tf/ z wtyczką tf (droga dla chmury): {market}")

        subprocess.run([sys.executable, ".tf/factory/task_state.py", "start", "IMP-1", "--title", "Raport", "--mode", "auto"],
                       cwd=p, capture_output=True, text=True, env=e, timeout=60)
        r = subprocess.run([sys.executable, ".tf/factory/work.py", "--once", "--budget", "1"], cwd=p, capture_output=True,
                           text=True, timeout=300, env=e)
        try:
            call = json.loads((base / "argv.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            call = {}
        argv = call.get("argv") or []
        wt = (p / ".tf" / "worktrees" / "IMP-1").resolve()
        check(r.returncode == 0 and "--plugin-dir" in argv and Path(argv[argv.index("--plugin-dir") + 1]).resolve() == wt / ".tf" / "plugin"
              and "--settings" in argv and Path(argv[argv.index("--settings") + 1]).resolve() == wt / ".tf" / "cache" / "session-settings.json",
              f"PW-2: tf work woła agenta z wtyczką i ustawieniami sesji z worktree: {r.returncode} {argv} {r.stdout[-400:]}")
        check((wt / ".tf" / "plugin" / "skills" / "tf" / "SKILL.md").is_file() and (wt / ".tf" / "plugin" / "hooks" / "hooks.json").is_file(),
              "PW-3: worktree dostaje wtyczkę fabryki")

        r = subprocess.run([sys.executable, ".tf/factory/tf.py", "cloud-setup"], cwd=p, capture_output=True, text=True,
                           timeout=120, env=e)
        check(r.returncode == 0 and "cloud-setup --apply" in r.stdout and "proj" in r.stdout and not (home / ".claude").exists(),
              f"PW-4: cloud-setup bez --apply drukuje skrypt startowy środowiska i niczego nie zapisuje: {r.stdout[-500:]}")
        (home / ".claude").mkdir()
        (home / ".claude" / "settings.json").write_text(json.dumps({"theme": "dark", "permissions": {"allow": ["Bash(make *)"]}}),
                                                       encoding="utf-8")
        for _ in range(2):
            r = subprocess.run([sys.executable, ".tf/factory/tf.py", "cloud-setup", "--apply"], cwd=p, capture_output=True,
                               text=True, timeout=120, env=e)
        try:
            us = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            us = {}
        mkt = (us.get("extraKnownMarketplaces") or {}).get("tf-project") or {}
        allow = (us.get("permissions") or {}).get("allow") or []
        check(r.returncode == 0 and us.get("theme") == "dark" and "Bash(make *)" in allow
              and (us.get("enabledPlugins") or {}).get("tf@tf-project") is True
              and Path((mkt.get("source") or {}).get("path", "")).resolve() == (p / ".tf").resolve()
              and us.get("env") and allow.count("Bash(make *)") == 1 and len(allow) == len(set(allow)),
              f"PW-5: cloud-setup --apply włącza wtyczkę i ustawienia sesji w ustawieniach użytkownika, Twoje zostają, "
              f"ponowienie bez dubli: {r.returncode} {r.stdout[-300:]} {json.dumps(us)[:500]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tf work i chmury w układzie wtyczki")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
