#!/usr/bin/env python3
"""Testy bramki jakości skilli (skill_gate, new-skill, build check, hook skill_change_guard)."""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOKS = ROOT / ".claude" / "hooks"


def run(cmd, cwd=None, env=None, stdin=""):
    return subprocess.run([sys.executable, *cmd], cwd=cwd, env=env or os.environ, input=stdin, capture_output=True,
                          text=True, timeout=600)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    # ── bramka na kopii fabryki ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip", "docs"))
        gate = str(root / "factory" / "skill_gate.py")

        total += 1
        r = run([gate, "core-grounding", "--fast"], cwd=root)
        reg = load(root / "factory" / "build.py", "b_copy").gate_registry()
        if r.returncode != 0 or "fingerprint" not in reg.get("core-grounding", {}):
            fails.append(f"gate: istniejący skill powinien przejść i trafić do rejestru — {r.stdout[-600:]}")

        total += 1
        p = root / ".claude" / "skills" / "core-grounding" / "SKILL.md"
        p.write_text(p.read_text() + "\nZmiana.\n")
        st = run([gate, "--status"], cwd=root).stdout
        chk = run([str(root / "factory" / "build.py"), "check"], cwd=root).stdout
        if "core-grounding" not in st or "zmieniony po bramce" not in st or "core-grounding: zmieniony po ostatniej bramce" not in chk:
            fails.append(f"gate: zmiana skilla nie wykryta — {st[-300:]} / {chk[-300:]}")

        total += 1
        r = run([str(root / "factory" / "build.py"), "new-skill", "core-demo-gate", "Użyj przy demo. Nie do niczego innego."], cwd=root)
        ev = next((d / "skill_evals" / "core-demo-gate.json" for d in (root / "tests", root / ".claude" / "tests")
                   if (d / "skill_evals" / "core-demo-gate.json").exists()), root / "tests" / "skill_evals" / "core-demo-gate.json")
        g = run([gate, "core-demo-gate", "--fast"], cwd=root)
        if not ev.exists() or g.returncode == 0 or "TODO" not in g.stdout:
            fails.append(f"new-skill: brak szkieletu scenariuszy albo bramka przepuściła TODO — {g.stdout[-400:]}")

        total += 1
        sess = {"session_id": "s1", "hook_event_name": "PostToolUse", "tool_input": {"file_path": str(p)}}
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        first = run([str(HOOKS / "skill_change_guard.py")], env=env, stdin=json.dumps(sess)).stdout
        second = run([str(HOOKS / "skill_change_guard.py")], env=env, stdin=json.dumps(sess)).stdout
        stop = run([str(HOOKS / "skill_change_guard.py")], env=env,
                   stdin=json.dumps({"session_id": "s1", "hook_event_name": "Stop"})).stdout
        if "skill_gate.py core-grounding" not in first or second.strip() or "core-grounding" not in stop:
            fails.append(f"skill_change_guard: {first[:120]!r} / {second!r} / {stop!r}")

    # 5. każda runda ewaluacji ma własny raport (bez mieszania wyników kilku rund)
    total += 1
    with tempfile.TemporaryDirectory() as d:
        g = load(ROOT / "factory" / "skill_gate.py", "gate_mod")
        out = Path(d)
        first = g.report_path(out, "x")
        first.with_suffix(".jsonl").write_text("{}\n")
        second = g.report_path(out, "x")
        if first == second or not second.name.endswith("-bramka-x-2.md"):
            fails.append(f"report_path: {first.name} / {second.name}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów bramki skilli")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
