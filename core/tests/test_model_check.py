#!/usr/bin/env python3
"""Model names in the configuration (step H20): every `claude-…` identifier in the factory configuration and in the engine code
is known (current or an allowed older one), aliases point to current models, and an old check date is a warning.
python3 .claude/tests/test_model_check.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
CHECK = ROOT / ".tf" / "factory" / "model_check.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"


def call(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(project / ".tf" / "factory" / "model_check.py"), *args], cwd=project,
                          capture_output=True, text=True, timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def project(base: Path, name: str, override: str | None = None) -> Path:
    """A copy of the factory engine (without the rest of the installation) and an optional override of the project configuration."""
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__"))
    if override is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(override, encoding="utf-8")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not CHECK.is_file():
        print(f"✗ missing {CHECK}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "clean")
        r = call(p, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        checked = data.get("checked") or ""
        r2 = call(p, "--today", checked) if checked else r
        check(r.returncode == 0 and data.get("errors") == [] and len(checked) == 10
              and {"fable", "opus", "sonnet", "haiku"} <= set(data.get("current") or {})
              and r2.returncode == 0 and "⚠" not in r2.stdout and "✓" in r2.stdout,
              f"MC-1: the factory configuration and engine without unknown models, with a price for every current one: "
              f"{r.returncode} {r.stdout[:600]} {r2.stdout}")
        check(all(v.startswith("claude-") for v in (data.get("current") or {}).values())
              and not set((data.get("current") or {}).values()) & set(data.get("legacy") or []),
              f"MC-2: current and older identifiers are disjoint: {data.get('current')} {data.get('legacy')}")

        p = project(base, "unknown", "tiers:\n  deep: {model: claude-opus-4-1, effort: high}\n")
        r = call(p)
        check(r.returncode == 1 and "claude-opus-4-1" in r.stdout and ".tf/config/config.yaml" in r.stdout
              and "claude-api" in r.stdout,
              f"MC-3: an unknown identifier in the project configuration → an error naming the file and source: {r.returncode} {r.stdout}")

        p = project(base, "alias", "managed_agents:\n  models: {fable: claude-fable-5-1}\n")
        r = call(p)
        check(r.returncode == 1 and "claude-fable-5-1" in r.stdout and "fable" in r.stdout and "older" in r.stdout,
              f"MC-4: an alias pointing to an older model → error: {r.returncode} {r.stdout}")

        p = project(base, "pinned", "tiers:\n  deep: {model: claude-fable-5-1, effort: high}\n")
        r = call(p)
        check(r.returncode == 0 and "✗" not in r.stdout,
              f"MC-5: a deliberately pinned older but allowed model is not an error: {r.returncode} {r.stdout}")

        p = project(base, "old")
        r = call(p, "--today", "2099-01-01")
        check(r.returncode == 0 and "⚠" in r.stdout and "90" in r.stdout and "models_checked" in r.stdout,
              f"MC-6: an old check date is a warning, not an error: {r.returncode} {r.stdout}")

        p = project(base, "code")
        (p / ".tf" / "factory" / "extra_tool.py").write_text('MODEL = "claude-sonnet-3-9"\n', encoding="utf-8")
        r = call(p)
        check(r.returncode == 1 and "claude-sonnet-3-9" in r.stdout and "extra_tool.py" in r.stdout,
              f"MC-7: an identifier in the engine code is checked too: {r.returncode} {r.stdout}")

        p = project(base, "broken", "tiers: [not: a dictionary\n")
        r = call(p)
        check(r.returncode in (0, 1) and "Traceback" not in r.stdout + r.stderr,
              f"MC-8: an unreadable project configuration does not end in an exception trace: {r.returncode} {r.stdout} {r.stderr[-300:]}")

    # tf doctor shows the model check result (informational; does not change the exit code)
    r = subprocess.run([sys.executable, str(CTF), "doctor"], cwd=ROOT, capture_output=True, text=True, timeout=300,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check("models:" in r.stdout.lower() and "Traceback" not in r.stderr,
          f"MC-9: tf doctor shows the model name check: {r.stdout[-600:]} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} model name tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
