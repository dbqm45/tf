#!/usr/bin/env python3
"""`install.py --isolation <level>` (plan docs/plans/2026-11-20-poziomy-izolacji.md, slices I1–I2): the level goes into the
project's .tf/config/config.yaml, and in the default layout the sandbox into .claude/settings.local.json; an unknown level and an agent session (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT) are refused
before anything is installed.
python3 tests/test_isolation_install.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")
HUMAN = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}


def install(proj: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(proj), "--yes",
                           "--packs", "none", *args], capture_output=True, text=True, timeout=300, env=env or HUMAN)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = base / "ok"
        p.mkdir()
        r = install(p, "--isolation", "basic")
        cfg = p / ".tf" / "config" / "config.yaml"
        text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
        check(r.returncode == 0 and "isolation: basic" in text,
              f"II-1: --isolation basic → in .tf/config/config.yaml: {r.returncode} {r.stdout[-400:]}{r.stderr[-400:]}")

        p = base / "bad"
        p.mkdir()
        r = install(p, "--isolation", "vm")
        check(r.returncode == 2 and "sandbox" in r.stdout and not (p / ".tf").exists(),
              f"II-2: an unknown level → refused, nothing installed: {r.returncode} {r.stdout[-300:]}")

        p = base / "agent"
        p.mkdir()
        r = install(p, "--isolation", "basic", env={**HUMAN, "CLAUDECODE": "1"})
        check(r.returncode == 2 and "terminal" in r.stdout and not (p / ".tf").exists(),
              f"II-3: an agent session does not choose its own isolation: {r.returncode} {r.stdout[-300:]}")

        # I2, default layout: the sandbox goes into .claude/settings.local.json (per person, not the shared settings)
        p = base / "dflt"
        p.mkdir()
        r = install(p, "--layout", "default")
        local = p / ".claude" / "settings.local.json"
        got = json.loads(local.read_text(encoding="utf-8")) if local.is_file() else {}
        check(r.returncode == 0 and (got.get("sandbox") or {}).get("enabled") is True,
              f"II-4: default layout, default level → sandbox enabled in settings.local.json: {r.stdout[-300:]} {list(got)}")
        got.setdefault("sandbox", {})["enabled"] = False
        local.write_text(json.dumps(got), encoding="utf-8")
        install(p, "--layout", "default")
        got = json.loads(local.read_text(encoding="utf-8"))
        check((got.get("sandbox") or {}).get("enabled") is False, "II-5: an update keeps a person's own sandbox setting")
        r = install(p, "--layout", "default", "--isolation", "basic")
        got = json.loads(local.read_text(encoding="utf-8"))
        check(r.returncode == 0 and "sandbox" not in got, f"II-6: --isolation basic → no sandbox in settings.local.json: {list(got)}")
        p = base / "team"
        p.mkdir()
        r = install(p, "--layout", "default", "--shared")
        shared_s = json.loads((p / ".claude" / "settings.json").read_text(encoding="utf-8"))
        local = p / ".claude" / "settings.local.json"
        got = json.loads(local.read_text(encoding="utf-8")) if local.is_file() else {}
        check(r.returncode == 0 and "sandbox" not in shared_s and (got.get("sandbox") or {}).get("enabled") is True,
              f"II-8: team mode → the shared settings.json without a sandbox, the person's settings.local.json with it: "
              f"{list(shared_s)} {list(got)} {r.stdout[-300:]}")
        p = base / "plug"
        p.mkdir()
        install(p, "--layout", "plugin")
        sess = json.loads((p / ".tf" / "plugin" / "session-settings.json").read_text(encoding="utf-8"))
        check("sandbox" not in sess, "II-7: plugin layout → the plugin files do not depend on the level (tf code adds it)")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} isolation install tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
