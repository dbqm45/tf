#!/usr/bin/env python3
"""The /tf-task loop in an installed plugin-layout project (the default), as on Windows.

The tf-task SKILL.md tells the agent to call `python3 .claude/skills/tf/scripts/<script>` from the project root. In the
plugin layout the skill lives in `.tf/plugin/skills/`, and `.claude/skills/tf/scripts/` holds the copies the skill
texts call (without SKILL.md). A Windows user saw `run_state.py` fail on `ui_snap.py`: ui_snap's `signal.SIGKILL` default
does not exist on Windows. And an update did not restore a missing script of those copies (no SKILL.md beside them).
The commands run here with the POSIX-only signals and fcntl removed (a sitecustomize), as Python has them on Windows.
python3 tests/test_plugin_task_loop.py"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
SKILL = ROOT / "core" / "skills" / "tf-task" / "SKILL.md"
PREFIX = ".claude/skills/tf/scripts/"
WINDOWS_PYTHON = ("import signal, sys\n"
                  "for n in ('SIGKILL', 'SIGHUP', 'SIGPIPE', 'SIGALRM', 'SIGUSR1', 'SIGUSR2', 'SIGCHLD', 'SIGQUIT'):\n"
                  "    hasattr(signal, n) and delattr(signal, n)\n"
                  "sys.modules['fcntl'] = None\n")
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given a price of 100, when the discount applies, then the price is "
        "90.\n\n## Unchanged\n\n- Prices without a discount.\n\n## Out of scope\n\n- Coupons.\n")
PLAN = "# Plan\n\n- [ ] S1 — the discount · criteria: AC-1 · files: price.py, test_price.py\n"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    text = SKILL.read_text(encoding="utf-8")
    check(f"python3 {PREFIX}run_report.py" in text, "TL-1: tf-task SKILL.md names the scripts by .claude/skills/tf/scripts/")
    names = sorted(set(re.findall(r"`(\w+\.py)`", text.split("(below: names)")[0])))
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = base / "proj"
        p.mkdir()
        sim = base / "winsim"
        sim.mkdir()
        (sim / "sitecustomize.py").write_text(WINDOWS_PYTHON, encoding="utf-8")
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(base), "CI": "1", "TF_DASHBOARD_OPEN": "0",
               "CLAUDE_PROJECT_DIR": str(p), "CLAUDE_CONFIG_DIR": str(base / "cfg"), "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "T",
               "GIT_COMMITTER_EMAIL": "t@example.com", "TF_NO_PLUGIN_REGISTER": "1"}

        def git(*args):
            return subprocess.run(["git", "-C", str(p), "-c", "commit.gpgsign=false", *args], capture_output=True,
                                  text=True, env=env, timeout=60)

        def install():
            return subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none"], capture_output=True,
                                  text=True, timeout=600, env=env)

        git("init", "-q", "-b", "main")
        (p / "README.md").write_text("x\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "chore: init")
        r = install()
        check(r.returncode == 0 and (p / ".tf" / "plugin" / "skills" / "tf-task" / "SKILL.md").is_file(),
              f"TL-2: plugin-layout install: {r.returncode} {r.stdout[-400:]} {r.stderr[-400:]}")
        git("add", "-A")
        git("commit", "-q", "-m", "chore: factory")
        git("checkout", "-q", "-b", "story/discount")
        check(len(names) >= 5 and all((p / PREFIX / n).is_file() for n in names),
              f"TL-3: every script tf-task names exists at {PREFIX}: {[n for n in names if not (p / PREFIX / n).is_file()]}")
        plugin_scripts = sorted(x.name for x in (p / ".tf/plugin/skills/tf/scripts").glob("*.py"))
        check(plugin_scripts and all((p / PREFIX / n).is_file() for n in plugin_scripts),
              f"TL-3: the copies in {PREFIX} hold every script of the plugin's tf skill: {plugin_scripts}")

        def run(script, *args):
            return subprocess.run([sys.executable, f"{PREFIX}{script}", *args], cwd=p, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=180,
                                  env={**env, "PYTHONPATH": str(sim)})

        d = ".tf/runs/T-1"
        steps = [("security_scan.py", "cooldown"), ("intake.py", "resolve", "Add a discount"),
                 ("run_report.py", "start", "Discount", "--key", "T-1", "--story", "As a buyer I want a discount."),
                 ("run_state.py", "stage", d, "intake"), ("run_state.py", "mode", d, "normal"),
                 ("run_state.py", "spec", d, "new")]
        for script, *args in steps:
            r = run(script, *args)
            check(r.returncode == 0 and "Traceback" not in r.stderr,
                  f"TL-4: `{script} {' '.join(args)}` on simulated Windows: {r.returncode} {r.stdout[-300:]} {r.stderr[-600:]}")
        doc = p / "docs" / "project" / "changes" / "T-1"
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
        (doc / "plan.md").write_text(PLAN, encoding="utf-8")
        (p / "test_price.py").write_text("from price import discount\n\n\ndef test_ac1_discount():  # AC-1\n"
                                         "    assert discount(100) == 90\n\n\nif __name__ == '__main__':\n"
                                         "    test_ac1_discount()\n    print('1 passed')\n", encoding="utf-8")
        (p / "price.py").write_text("def discount(price):\n    return price * 9 // 10\n", encoding="utf-8")
        for script, *args in [("run_state.py", "spec", d),
                              ("run_state.py", "flag", d, "none", "--reason", "no flag, because the change is small"),
                              ("run_state.py", "stage", d, "plan"), ("run_state.py", "approve", d),
                              ("ui_snap.py", "worth", d, "--base", "main"),
                              ("run_state.py", "step", d, "S1", "R1", "test", "run"),
                              ("run_state.py", "park", d, "rounding of odd prices"),
                              ("run_state.py", "verify", d, "S1", "--files", "price.py,test_price.py", "--command",
                               f"{Path(sys.executable).as_posix()} test_price.py"),
                              ("plan_drift.py", d, "--base", "main")]:
            r = run(script, *args)
            ok = (0, 1) if args[0] == "worth" else (0,)   # `worth`: 0 = yes, 1 = no
            check(r.returncode in ok and "Traceback" not in r.stderr,
                  f"TL-5: `{script} {' '.join(args)}`: {r.returncode} {r.stdout[-400:]} {r.stderr[-600:]}")

        # TL-6: an update restores a missing script of the copies in .claude/skills/tf/scripts/ (no SKILL.md beside them)
        snap = p / PREFIX / "ui_snap.py"
        snap.unlink()
        r = install()
        check(r.returncode == 0 and snap.is_file(), f"TL-6: the update restores {PREFIX}ui_snap.py: {r.stdout[-600:]}")
        r = run("run_state.py", "--help")
        check(r.returncode == 0, f"TL-6: run_state.py works after the update: {r.stderr[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} the /tf-task loop in a plugin-layout project: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
