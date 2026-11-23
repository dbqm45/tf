#!/usr/bin/env python3
"""Task scenarios of the skill evaluation runner (plan docs/plans/2026-11-23-scenariusze-przebiegu-a3-a2a.md): a scenario
with `"kind": "task"` runs on a fixture project with file edits and Bash allowed, and is checked on the commands it ran,
the files it left and a command run after it — the skill's procedure, not only the words of the answer.
No model: a claude stub runs commands and writes files. python3 tests/test_skill_eval_tasks.py"""
import importlib.util
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_skill_evals_tasks", HERE / "run_skill_evals.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

# The stub "agent": records its arguments, reads the fixture, writes a report and a test, and reports two Bash commands.
FAKE = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
argv = sys.argv[1:]
if os.environ.get("FAKE_ARGV"):
    Path(os.environ["FAKE_ARGV"]).write_text(json.dumps(argv))
prompt = argv[argv.index("-p") + 1]
def tool(name, inp):
    print(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}))
if "SKILL" in prompt:
    tool("Skill", {"skill": os.environ["FAKE_SKILL"]})
tool("Bash", {"command": "python3 scripts/check.py ."})
if "INSTALL" in prompt:
    tool("Bash", {"command": "npm ci && npm test"})
Path("docs").mkdir(exist_ok=True)
Path("docs/report.md").write_text("Verdict: needs-attention\nKEY name only: STRIPE_SECRET_KEY\n")
Path("tests").mkdir(exist_ok=True)
Path("tests/__init__.py").write_text("")
Path("tests/test_new.py").write_text("import unittest\nclass T(unittest.TestCase):\n    def test_a(self): pass\n    def test_b(self): pass\n")
tool("Write", {"file_path": "docs/report.md", "content": "..."})
print(json.dumps({"type": "result", "subtype": "success", "result": "Report in docs/report.md.",
                  "total_cost_usd": 0.02, "num_turns": 5}))
"""


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # a skill present in every workspace (core); the stub "agent" triggers it
    skill = "core-grounding" if (ev.SKILLS / "core-grounding" / "SKILL.md").is_file() else \
        next(p.parent.name for p in sorted(ev.SKILLS.glob("*/SKILL.md")))
    os.environ["FAKE_SKILL"] = skill

    # T-1: the stream gives the Bash commands in order
    p = ev.parse_stream([
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "make test"}}]}}),
        json.dumps({"type": "result", "subtype": "success", "result": "ok", "total_cost_usd": 0.01, "num_turns": 1})])
    check(p.get("commands") == ["ls", "make test"], f"T-1: parse_stream collects Bash commands in order: {p.get('commands')}")
    p = ev.parse_stream([json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
        "input": {"command": "cat -n app/x.py; sed -n 1,60p .claude/skills/be-business-app-patterns/SKILL.md"}}]}})])
    check(p["skills"] == ["be-business-app-patterns"] and p["via"].get("be-business-app-patterns") == "Bash",
          f"T-1b: reading a SKILL.md through Bash (cat, sed, head) counts as triggering the skill: {p['skills']} {p['via']}")

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        # T-2: the task checks on a directory, independently of the model
        ws = base / "ws"
        (ws / "docs").mkdir(parents=True)
        (ws / "docs" / "r.md").write_text("Verdict: healthy\n", encoding="utf-8")
        (ws / "t.py").write_text("def test_a(): pass\ndef test_b(): pass\n", encoding="utf-8")
        checks = {"commands": [["readiness_check\\.py"], ["^make test"]], "no_commands": ["npm (ci|install)"],
                  "files": [{"glob": "docs/*.md", "matches": ["healthy|needs-attention"], "not_matches": ["sk_live"]},
                            {"glob": "package.json", "exists": False}],
                  "count": [{"glob": "*.py", "rx": "def test_", "min": 2}],
                  "after": {"cmd": [sys.executable, "-c", "import sys; sys.exit(0)"], "exit": 0}}
        groups, misses = ev.task_checks(checks, ["python3 x/readiness_check.py .", "make test"], ws)
        check(groups == 7 and misses == [], f"T-2: a good run passes every task group: {groups} {misses}")
        groups, misses = ev.task_checks(checks, ["npm ci"], ws)
        check(len(misses) == 3 and all(m.startswith("missing:") for m in misses),
              f"T-2b: missing commands and a forbidden one are misses (each a group): {misses}")
        (ws / "package.json").write_text("{}", encoding="utf-8")
        (ws / "docs" / "r.md").write_text("sk_live_x\n", encoding="utf-8")
        bad = {**checks, "count": [{"glob": "*.py", "rx": "def test_", "min": 3}],
               "after": {"cmd": [sys.executable, "-c", "import sys; sys.exit(1)"], "exit": 0}}
        _, misses = ev.task_checks(bad, ["python3 readiness_check.py", "make test"], ws)
        check(len(misses) == 4, f"T-2c: file content, an absent file, the count and the after command fail: {misses}")

        # T-3: a task run — the fixture copied, edits and Bash allowed, a higher turn limit, checks on what it left
        fake = base / "claude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        argv_file = base / "argv.json"
        os.environ.update(CLAUDE_BIN=str(fake), FAKE_ARGV=str(argv_file))
        tasks = base / "skill_evals" / "tasks"
        (tasks / "fixtures").mkdir(parents=True)
        (tasks / "fixtures" / "app.json").write_text(json.dumps({"files": {"scripts/check.py": "print('ok')\n",
                                                                         ".env.example": "STRIPE_SECRET_KEY=\n"}}))
        ev.TASKS = tasks
        sc = {"skill": skill, "id": "t", "expect": "trigger", "kind": "task", "fixture": "app",
              "prompt": "SKILL: audit this repo", "max_turns": 25, "allowed_tools": ["Bash(python3:*)", "Edit", "Write"],
              "checks": {"commands": [["scripts/check\\.py"]], "no_commands": ["npm (ci|install)"],
                         "files": [{"glob": "docs/report.md", "matches": ["Verdict: (healthy|needs-attention)"]},
                                   {"glob": ".env.example", "exists": True}],
                         "count": [{"glob": "tests/*.py", "rx": "def test_", "min": 2}],
                         "after": {"cmd": ["python3", "-m", "unittest", "-q"], "exit": 0}}}
        args = SimpleNamespace(max_turns=8, timeout=60, isolated=False, judge="none", bare=True)
        r = ev.run_one(sc, "haiku", False, args)
        argv = json.loads(argv_file.read_text()) if argv_file.exists() else []
        check(r["passed"] and r["groups_total"] == 6 and r["groups_met"] == 6,
              f"T-3: a task run that follows the procedure passes all six groups: {r['passed']} {r['groups_met']}/"
              f"{r['groups_total']} {r['misses']} {r['error']}")
        check("acceptEdits" in argv and "plan" not in argv and "--allowedTools" in argv
              and "Bash(python3:*)" in argv and argv[argv.index("--max-turns") + 1] == "25",
              f"T-3b: edits accepted, the scenario's tools allowed, its turn limit: {argv}")
        check(r.get("commands") == ["python3 scripts/check.py ."], f"T-3c: the result keeps the commands: {r.get('commands')}")

        r = ev.run_one({**sc, "prompt": "SKILL INSTALL: audit"}, "haiku", False, args)
        check(not r["passed"] and any("npm" in m for m in r["misses"]),
              f"T-4: a forbidden command fails the run: {r['misses']}")

        # T-5: without skills — Bash stays (the task needs it), no --restricted, no factory skills in the directory
        r = ev.run_one({**sc, "prompt": "audit this repo"}, "haiku", True, args)
        argv = json.loads(argv_file.read_text())
        check("--restricted" not in argv and "--setting-sources" in argv and "--allowedTools" in argv,
              f"T-5: a task without skills keeps Bash and drops personal settings: {argv}")
        check(r["checks_ok"] and not r["error"], f"T-5b: the same procedure passes without skills: {r['misses']} {r['error']}")
        r = ev.run_one(sc, "haiku", True, args)
        check(r["error"] and "skill" in r["error"],
              f"T-5c: a skill triggered in the run without skills makes the result unreliable: {r['error']}")

        # T-6: validation — a task file has its own rules
        f = tasks / f"{skill}.json"
        f.write_text(json.dumps({"skill": skill, "scenarios": [sc]}), encoding="utf-8")
        check(ev.validate_file(f, kind="task") == [], f"T-6: a valid task file: {ev.validate_file(f, kind='task')}")
        broken = [{**sc, "id": "a", "checks": {"all": [["x"]]}},
                  {**sc, "id": "b", "fixture": "nope"},
                  {**sc, "id": "c", "checks": {"commands": [["("]]}},
                  {**sc, "id": "d", "kind": "qa"}]
        f.write_text(json.dumps({"skill": skill, "scenarios": broken}), encoding="utf-8")
        errs = ev.validate_file(f, kind="task")
        check(len(errs) == 4, f"T-6b: no task check, a missing fixture, a bad regex, a wrong kind: {errs}")

        # T-7: task scenarios load only on request (they are costly)
        f.write_text(json.dumps({"skill": skill, "scenarios": [sc]}), encoding="utf-8")
        ev.EVALS = base / "skill_evals"
        (ev.EVALS / f"{skill}.json").write_text(json.dumps({"skill": skill, "scenarios": [
            {"id": "q", "expect": "trigger", "prompt": "a question long enough", "checks": {"all": [["x"]]}}]}))
        plain = [s["id"] for s in ev.load_scenarios([skill])]
        only = [s["id"] for s in ev.load_scenarios([skill], tasks=True)]
        check(plain == ["q"] and only == ["t"], f"T-7: tasks only with tasks=True: {plain} {only}")
        check(any(k == "task" for _p, k in ev.scenario_files()), "T-7b: validation sees the task files")

    for m in fails:
        print(f"✗ {m}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task scenario tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
