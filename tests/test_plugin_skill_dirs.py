#!/usr/bin/env python3
"""Tryb fabryki, krok T3 (docs/plans/2026-11-20-tryb-fabryki-plan.md): w układzie wtyczki SKILL.md skilli fabryki leżą
w .tf/plugin/skills/, a Twoje w .claude/skills/. Narzędzia i hooki, które czytają skille (podpowiedź skilla, bramka,
baza wiedzy, licznik użycia, strażnik zmian skilla), widzą oba miejsca.
python3 tests/test_plugin_skill_dirs.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
OWN = ("---\nname: moj-raport\ndescription: Use when preparing the weekly sales report for the management board.\n---\n"
       "Weekly sales report for the board: revenue, margin, top customers.\n")


def env(p: Path) -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(p.parent), "CLAUDE_PROJECT_DIR": str(p)}


def make(base: Path, name: str, *opts: str) -> Path:
    p = base / name
    (p / ".claude" / "skills" / "moj-raport").mkdir(parents=True)
    (p / ".claude" / "skills" / "moj-raport" / "SKILL.md").write_text(OWN, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    r = subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts], capture_output=True,
                       text=True, timeout=600, env=env(p))
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    return p


def run(p: Path, *cmd: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *cmd], cwd=p, input=stdin, capture_output=True, text=True, timeout=300,
                          env=env(p))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        for layout, opts in (("plugin", ("--layout", "plugin")), ("default", ("--layout", "default"))):
            p = make(base, layout, *opts)
            r = run(p, ".claude/hooks/skill_hint.py", "--explain", "Zaimplementuj tę historyjkę: jako użytkownik chcę "
                    "zresetować hasło linkiem z maila, link ważny 30 minut.")
            top = [ln.split()[-1] for ln in r.stdout.splitlines()[:3] if ln.strip() and not ln.startswith("---")]
            check("tf-task" in top, f"SD-1 [{layout}]: podpowiedź skilla widzi skille fabryki (tf-task w czołówce): {r.stdout[:400]}")
            r = run(p, ".claude/hooks/skill_hint.py", "--explain", "prepare the weekly sales report for the management board")
            check("moj-raport" in r.stdout.split("---")[0],
                  f"SD-2 [{layout}]: podpowiedź skilla widzi Twój skill z .claude/skills: {r.stdout[:400]}")
            r = run(p, ".tf/factory/skill_gate.py", "core-grounding")
            check("there is no" not in r.stdout and "core-grounding" in r.stdout and "1. " in r.stdout,
                  f"SD-3 [{layout}]: bramka skilla znajduje skill fabryki: {r.returncode} {r.stdout[-400:]}")
            r = run(p, ".claude/skills/core-knowledge/scripts/kb.py", "search", "grounding claims source date", "--json")
            check("core-grounding" in r.stdout, f"SD-4 [{layout}]: baza wiedzy przeszukuje skille fabryki: {r.stdout[:300]} {r.stderr[-200:]}")

        plug = base / "plugin"
        lu = load(plug / ".claude" / "hooks" / "log_usage.py", "lu_t3")
        check(hasattr(lu, "SKILL_READ_RE") and lu.SKILL_READ_RE.search(str(plug / ".tf/plugin/skills/tf/SKILL.md"))
              and lu.SKILL_READ_RE.search(str(plug / ".tf/plugin/skills/tf/SKILL.md")).group(1) == "tf",
              "SD-5: licznik użycia rozpoznaje odczyt SKILL.md skilla z wtyczki")
        r = run(plug, ".claude/hooks/skill_change_guard.py",
                stdin=json.dumps({"hook_event_name": "PostToolUse", "session_id": "s1", "cwd": str(plug),
                                  "tool_input": {"file_path": str(plug / ".tf/plugin/skills/core-grounding/SKILL.md")}}))
        check("core-grounding" in r.stdout, f"SD-6: strażnik zmian skilla reaguje na edycję skilla we wtyczce: {r.stdout[:300]} {r.stderr[-200:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów skilli w obu miejscach")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
