#!/usr/bin/env python3
"""Isolation level (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I1): the `isolation` key (basic | sandbox |
container, default sandbox), `tf isolation [<level>]` that refuses inside an agent session, and the level with what
actually protects the session in `tf isolation` and `tf doctor`.
python3 .claude/tests/test_isolation.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")
HUMAN = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}   # a human's terminal, not an agent session


def project(base: Path, name: str, config: str | None = None) -> Path:
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    if config is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(config, encoding="utf-8")
    return p


def iso(p: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(p / ".tf" / "factory" / "isolation.py"), *args], cwd=p, capture_output=True,
                          text=True, timeout=60, env={**(env or HUMAN), "CLAUDE_PROJECT_DIR": str(p)})


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    script = ROOT / ".tf" / "factory" / "isolation.py"
    check(script.is_file(), f"IS-0: the engine has {script.relative_to(ROOT)}")
    if not script.is_file():
        print(f"✗ {fails[0]}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "default")
        r = iso(p, "show", "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(r.returncode == 0 and data.get("level") == "sandbox" and data.get("source") == "factory"
              and data.get("sandbox_enabled") is False and data.get("gaps"),
              f"IS-1: default level sandbox, the sandbox not enabled yet → a gap is named: {r.stdout}{r.stderr}")
        r = iso(p, "show")
        check(r.returncode == 0 and "sandbox" in r.stdout and "not enabled" in r.stdout,
              f"IS-1b: the readable view names the level and the gap: {r.stdout}")

        p = project(base, "set", "# own comment\nloop:\n  blocked_slices: true\n")
        r = iso(p, "set", "container")
        cfg = (p / ".tf" / "config" / "config.yaml").read_text(encoding="utf-8")
        check(r.returncode == 0 and "isolation: container" in cfg and "# own comment" in cfg and "blocked_slices: true" in cfg,
              f"IS-2: `set` writes the key into the project configuration and keeps the rest of the file: {r.stdout}{r.stderr} {cfg!r}")
        r = iso(p, "set", "basic")
        cfg = (p / ".tf" / "config" / "config.yaml").read_text(encoding="utf-8")
        check(r.returncode == 0 and cfg.count("isolation:") == 1 and "isolation: basic" in cfg,
              f"IS-3: a second `set` replaces the value, not a second key: {cfg!r}")

        for var in SESSION_VARS:
            r = iso(p, "set", "container", env={**HUMAN, var: "1"})
            cfg = (p / ".tf" / "config" / "config.yaml").read_text(encoding="utf-8")
            check(r.returncode == 2 and "isolation: basic" in cfg and "terminal" in r.stdout + r.stderr,
                  f"IS-4: inside an agent session ({var}) the level is not changed: {r.returncode} {r.stdout}{r.stderr}")

        r = iso(p, "set", "vm")
        check(r.returncode == 2 and "basic" in r.stdout + r.stderr, f"IS-5: an unknown level → error with the list: {r.stdout}{r.stderr}")

        p = project(base, "on")
        (p / ".claude").mkdir()
        (p / ".claude" / "settings.local.json").write_text(json.dumps({"sandbox": {"enabled": True}}), encoding="utf-8")
        fake_bin = base / "bin"                   # a stand-in bwrap: this check is about the settings, not the machine
        fake_bin.mkdir()
        (fake_bin / "bwrap").write_text("#!/bin/sh\n", encoding="utf-8")
        (fake_bin / "bwrap").chmod(0o755)
        with_bwrap = {**HUMAN, "PATH": f"{fake_bin}{os.pathsep}{HUMAN.get('PATH', '')}"}
        data = json.loads(iso(p, "show", "--json", env=with_bwrap).stdout or "{}")
        check(data.get("sandbox_enabled") is True and data.get("sandbox_where") == ".claude/settings.local.json"
              and not data.get("gaps"), f"IS-6: a sandbox enabled in the settings → no gap: {data}")
        (p / ".claude" / "settings.json").write_text(json.dumps({"sandbox": {"enabled": False}}), encoding="utf-8")
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
        check(data.get("sandbox_enabled") is True, f"IS-7: settings.local.json wins over settings.json: {data}")

        p = project(base, "basic", "isolation: basic\n")
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
        check(data.get("level") == "basic" and data.get("source") == "project" and data.get("gaps")
              and "not isolation" in " ".join(data.get("gaps")),
              f"IS-8: basic is named as no isolation: {data}")

        p = project(base, "container", "isolation: container\n")
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
        check(data.get("in_container") is False and any("container" in g for g in data.get("gaps", [])),
              f"IS-9: container chosen, the session is not in a container → a gap: {data}")
        data = json.loads(iso(p, "show", "--json", env={**HUMAN, "TF_CONTAINER": "1"}).stdout or "{}")
        check(data.get("in_container") is True, f"IS-10: TF_CONTAINER=1 (set by the image) → the session is in a container: {data}")

        p = project(base, "tf")
        (p / ".claude").mkdir()
        shutil.copy(ROOT / ".claude" / "factory-manifest.json", p / ".claude" / "factory-manifest.json")
        r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "tf.py"), "isolation"], cwd=p, capture_output=True,
                           text=True, timeout=60, env={**HUMAN, "CLAUDE_PROJECT_DIR": str(p)})
        check(r.returncode == 0 and "sandbox" in r.stdout, f"IS-11: `tf isolation` shows the level: {r.stdout}{r.stderr}")

        # I7: the company's minimum (isolation_min in org_defaults.config) — a gap below it, `set` below it refused
        p = project(base, "min", "isolation: basic\nisolation_min: sandbox\n")
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
        check(data.get("minimum") == "sandbox" and any("minimum" in g for g in data.get("gaps", [])),
              f"IS-19: a level below isolation_min → a gap naming the minimum: {data}")
        p = project(base, "min-set", "isolation: container\nisolation_min: sandbox\n")
        r = iso(p, "set", "basic")
        cfg = (p / ".tf" / "config" / "config.yaml").read_text(encoding="utf-8")
        check(r.returncode == 2 and "isolation: container" in cfg and "sandbox" in r.stdout + r.stderr,
              f"IS-20: `set` below the minimum is refused, the file unchanged: {r.returncode} {r.stdout}{r.stderr}")
        r = iso(p, "set", "sandbox")
        check(r.returncode == 0, f"IS-21: `set` at the minimum passes: {r.stdout}{r.stderr}")

        # I2: the level reaches the session. Plugin layout: `launch` builds the settings `tf code` passes with --settings
        p = project(base, "plug")
        (p / ".claude").mkdir()
        (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"layout": "plugin"}), encoding="utf-8")
        (p / ".tf" / "plugin").mkdir(parents=True)
        (p / ".tf" / "plugin" / "session-settings.json").write_text(json.dumps({"env": {"A": "1"}}), encoding="utf-8")
        r = iso(p, "launch")
        out = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
        got = json.loads(out.read_text(encoding="utf-8")) if out and out.is_file() else {}
        tpl = json.loads((ROOT / ".tf" / "factory" / "templates" / "sandbox.settings.json").read_text(encoding="utf-8"))
        check(got.get("env") == {"A": "1"} and got.get("sandbox") == tpl["sandbox"] and ".tf/cache" in out.as_posix(),
              f"IS-13: plugin layout, level sandbox → session settings + the sandbox template in .tf/cache: {r.stdout}{r.stderr} {got}")
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
        check(data.get("sandbox_enabled") is True and "tf code" in str(data.get("sandbox_where")),
              f"IS-14: plugin layout → the sandbox comes from tf code: {data}")
        data = json.loads(iso(p, "show", "--json", env={**HUMAN, "CLAUDECODE": "1"}).stdout or "{}")
        check(data.get("sandbox_enabled") is False and data.get("gaps"),
              f"IS-14b: a session not started by tf code (no TF_ISOLATION, e.g. a cloud session) → no sandbox from tf code: {data}")
        data = json.loads(iso(p, "show", "--json", env={**HUMAN, "CLAUDECODE": "1", "TF_ISOLATION": "sandbox"}).stdout or "{}")
        check(data.get("sandbox_enabled") is True, f"IS-14c: a session started by tf code (TF_ISOLATION=sandbox): {data}")
        (p / ".tf" / "plugin" / "session-settings.json").write_text(json.dumps({"env": {"A": "1"}, "sandbox": {"enabled": True}}),
                                                                   encoding="utf-8")
        (p / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (p / ".tf" / "config" / "config.yaml").write_text("isolation: basic\n", encoding="utf-8")
        r = iso(p, "launch")
        got = json.loads(Path(r.stdout.strip()).read_text(encoding="utf-8")) if r.returncode == 0 and r.stdout.strip() else {"sandbox": "?"}
        check("sandbox" not in got and got.get("env") == {"A": "1"}, f"IS-15: level basic → no sandbox in the session settings: {got}")

        # default layout: `set` writes the sandbox into .claude/settings.local.json (per person) and keeps the rest
        p = project(base, "deflt")
        (p / ".claude").mkdir()
        local = p / ".claude" / "settings.local.json"
        local.write_text(json.dumps({"permissions": {"allow": ["Bash(ls *)"]}}), encoding="utf-8")
        r = iso(p, "set", "sandbox")
        got = json.loads(local.read_text(encoding="utf-8"))
        check(r.returncode == 0 and got.get("sandbox") == tpl["sandbox"] and got.get("permissions") == {"allow": ["Bash(ls *)"]},
              f"IS-16: default layout, set sandbox → the template in settings.local.json, the rest kept: {r.stdout}{r.stderr} {got}")
        iso(p, "set", "basic")
        got = json.loads(local.read_text(encoding="utf-8"))
        check("sandbox" not in got and got.get("permissions"), f"IS-17: set basic → the sandbox removed from settings.local.json: {got}")

        if sys.platform.startswith("linux"):
            iso(p, "set", "sandbox")
            data = json.loads(iso(p, "show", "--json", env={**HUMAN, "PATH": str(base / "empty")}).stdout or "{}")
            check(any("bubblewrap" in g for g in data.get("gaps", [])),
                  f"IS-18: Linux without bubblewrap → the sandbox cannot start, named as a gap: {data}")

    r = subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "tf.py"), "doctor"], cwd=ROOT, capture_output=True,
                       text=True, timeout=300, env={**HUMAN, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check("Isolation:" in r.stdout, f"IS-12: tf doctor shows the isolation level: {r.stdout[-600:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} isolation tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
