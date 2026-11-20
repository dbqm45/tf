#!/usr/bin/env python3
"""Tests of the skill quality gate (skill_gate, new-skill, build check, the skill_change_guard hook)."""
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

    # -- content language: an English skill does not go through the Polish linter; selection rules and boundaries in both languages --
    gate_mod = load(ROOT / ".tf" / "factory" / "skill_gate.py", "g_lang")
    total += 1
    en = "---\nname: x\n---\n# Title\nUse the ledger when you post. The flag is `zażółć` in code only.\n```\nżółw ćma\n```\n"
    pl = "---\nname: x\nmetadata:\n  keywords: \"księga, zaksięgować\"\n---\n# Tytuł\nUżyj księgi przy księgowaniu. Zażółć gęślą jaźń.\n"
    if gate_mod.content_language(en) != "en" or gate_mod.content_language(pl) != "pl":
        fails.append(f"content language: en={gate_mod.content_language(en)} pl={gate_mod.content_language(pl)} (without the heading and code)")
    b_mod = load(ROOT / ".tf" / "factory" / "build.py", "b_lang")
    total += 1
    if b_mod.boundary("Use for invoices. Not for payments") != ("Use for invoices.", " Not for ", "payments") \
            or b_mod.boundary("Użyj przy fakturach. Nie do płatności")[1] != " Nie do ":
        fails.append("skill boundaries: ' Not for ' and ' Nie do ' recognised the same way")

    # -- the gate on a copy of the factory --
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip", "docs"))
        gate = str(root / ".tf" / "factory" / "skill_gate.py")

        total += 1
        r = run([gate, "core-grounding", "--fast"], cwd=root)
        reg = load(root / ".tf" / "factory" / "build.py", "b_copy").gate_registry()
        if r.returncode != 0 or "fingerprint" not in reg.get("core-grounding", {}):
            fails.append(f"gate: an existing skill should pass and land in the registry — {r.stdout[-600:]}")

        total += 1
        p = root / ".claude" / "skills" / "core-grounding" / "SKILL.md"
        p.write_text(p.read_text() + "\nZmiana.\n")
        st = run([gate, "--status"], cwd=root).stdout
        chk = run([str(root / ".tf" / "factory" / "build.py"), "check"], cwd=root).stdout
        if "core-grounding" not in st or "changed after the gate" not in st or "core-grounding: changed after the last gate" not in chk:
            fails.append(f"gate: a skill change not detected — {st[-300:]} / {chk[-300:]}")

        total += 1
        r = run([str(root / ".tf" / "factory" / "build.py"), "new-skill", "core-demo-gate", "Użyj przy demo. Nie do niczego innego."], cwd=root)
        ev = next((d / "skill_evals" / "core-demo-gate.json" for d in (root / "tests", root / ".claude" / "tests")
                   if (d / "skill_evals" / "core-demo-gate.json").exists()), root / "tests" / "skill_evals" / "core-demo-gate.json")
        g = run([gate, "core-demo-gate", "--fast"], cwd=root)
        if not ev.exists() or g.returncode == 0 or "TODO" not in g.stdout:
            fails.append(f"new-skill: no scenario skeleton, or the gate let a TODO through — {g.stdout[-400:]}")

        total += 1
        sess = {"session_id": "s1", "hook_event_name": "PostToolUse", "tool_input": {"file_path": str(p)}}
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        first = run([str(HOOKS / "skill_change_guard.py")], env=env, stdin=json.dumps(sess)).stdout
        second = run([str(HOOKS / "skill_change_guard.py")], env=env, stdin=json.dumps(sess)).stdout
        stop = run([str(HOOKS / "skill_change_guard.py")], env=env,
                   stdin=json.dumps({"session_id": "s1", "hook_event_name": "Stop"})).stdout
        if "skill_gate.py core-grounding" not in first or second.strip() or "core-grounding" not in stop:
            fails.append(f"skill_change_guard: {first[:120]!r} / {second!r} / {stop!r}")

    # 5. each evaluation round has its own report (no mixing of results of several rounds)
    total += 1
    with tempfile.TemporaryDirectory() as d:
        g = load(ROOT / ".tf" / "factory" / "skill_gate.py", "gate_mod")
        out = Path(d)
        first = g.report_path(out, "x")
        first.with_suffix(".jsonl").write_text("{}\n")
        second = g.report_path(out, "x")
        if first == second or not second.name.endswith("-gate-x-2.md"):
            fails.append(f"report_path: {first.name} / {second.name}")

    # 6. B4: scenarios that pass without skills are a step-8 warning, not an error
    total += 1
    g = load(ROOT / ".tf" / "factory" / "skill_gate.py", "gate_mod")
    warns = g.paid_warnings({"haiku": "5/5", "no_uplift": ["a", "b"]})
    if len(warns) != 1 or "a, b" not in warns[0] or g.paid_warnings({"haiku": "5/5"}):
        fails.append(f"paid_warnings: a warning only for scenarios that pass without skills: {warns}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} skill gate tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
