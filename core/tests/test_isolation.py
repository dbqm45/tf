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
        data = json.loads(iso(p, "show", "--json").stdout or "{}")
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

    r = subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "tf.py"), "doctor"], cwd=ROOT, capture_output=True,
                       text=True, timeout=300, env={**HUMAN, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check("Isolation:" in r.stdout, f"IS-12: tf doctor shows the isolation level: {r.stdout[-600:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} isolation tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
