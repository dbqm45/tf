#!/usr/bin/env python3
"""Tests of assigning a model and effort to the /tf-task loop's steps (`steps` in the factory configuration, .tf/factory/build.py):
the defaults give today's models, an override changes the executor, the table in the skill matches the configuration.
python3 .claude/tests/test_steps.py"""
import copy
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
BUILD = ROOT / ".tf" / "factory" / "build.py"
SKILL = ROOT / ".claude" / "skills" / "tf-task" / "SKILL.md"
# values from before step E5 (the default profile): executor → model
TODAY = {"scout": "haiku", "researcher": "haiku", "quick-fixer": "haiku", "tf-task": "sonnet", "scope-reviewer": "sonnet",
         "architect": "opus", "security-reviewer": "opus"}


def load_build():
    spec = importlib.util.spec_from_file_location("tf_build_steps", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    build = load_build()
    cfg = build.load_config()
    steps = cfg.get("steps") or {}
    check(len(steps) == 7 and all({"label", "who", "tier"} <= set(s) for s in steps.values()),
          f"K-1: the configuration has 7 steps with a description, an executor and a tier: {sorted(steps)}")
    got = {s["who"]: cfg["tiers"][cfg["shared_agents"][s["who"]]["tier"]]["model"] for s in steps.values()
           if s.get("who") in cfg["shared_agents"]}
    check(got == TODAY or cfg.get("_profile") != cfg.get("default_profile"),
          f"K-2: the default `steps` give today's executor models: {got}")
    generated = {}
    for name in TODAY:
        f = next(iter((ROOT / ".claude" / "agents" / "_generated").rglob(f"{name}.md")), None)
        text = f.read_text(encoding="utf-8") if f else ""
        generated[name] = next((ln.split(":", 1)[1].strip() for ln in text.splitlines() if ln.startswith("model:")), None)
    check(generated == TODAY or cfg.get("_profile") != cfg.get("default_profile"),
          f"K-3: the generated agents have today's models: {generated}")

    # overriding a step's tier changes the tier (and so the model) of its executor
    base = build.packs_mod.compose(ROOT, build.packs_mod.load_config(ROOT))
    over = copy.deepcopy(base)
    key = next(k for k, s in over["steps"].items() if s["who"] == "scope-reviewer")
    over["steps"][key]["tier"] = "deep"
    build.apply_steps(over)
    check(over["shared_agents"]["scope-reviewer"]["tier"] == "deep" and over["shared_agents"]["scout"]["tier"] == "fast",
          f"K-4: overriding a step's tier changes the executor's tier: {over['shared_agents']['scope-reviewer']['tier']}")

    # checks of the steps configuration
    bad = copy.deepcopy(base)
    bad["steps"]["nowy"] = {"label": "something", "who": "no-such-one", "tier": "std"}
    check(any("no-such-one" in e for e in build.steps_errors(bad)), "K-5: an unknown step executor → error")
    bad = copy.deepcopy(base)
    bad["steps"][key]["tier"] = "turbo"
    check(any("turbo" in e for e in build.steps_errors(bad)), "K-6: an unknown step tier → error")
    bad = copy.deepcopy(base)
    bad["steps"]["drugi"] = {"label": "inny krok", "who": "scout", "tier": "deep"}
    check(any("scout" in e for e in build.steps_errors(bad)), "K-7: the same executor with two tiers → error")
    check(build.steps_errors(base) == [], f"K-8: the default configuration without errors: {build.steps_errors(base)}")

    # the “Who does what” table in the skill matches the configuration; a mismatch is an error
    text = SKILL.read_text(encoding="utf-8")
    check(build.steps_table_errors(base, text) == [], f"K-9: the table in the skill matches `steps`: {build.steps_table_errors(base, text)}")
    row = next(ln for ln in text.splitlines() if "`scope-reviewer`" in ln and ln.startswith("|") and "std" in ln)
    check(build.steps_table_errors(base, text.replace(row, row.replace("| std |", "| deep |"))) != [],
          "K-10: a different tier in the table than in the configuration → error")
    check(build.steps_table_errors(base, text.replace(row + "\n", "")) != [], "K-11: a missing step row in the table → error")

    # a preview for a human
    r = subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "tf.py"), "config", "show", "steps"], cwd=ROOT,
                       capture_output=True, text=True, timeout=120, env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check(r.returncode == 0 and all(a in r.stdout for a in TODAY) and "sonnet" in r.stdout and "effort" in r.stdout.lower()
          and "the scope review of a slice" in r.stdout,
          f"K-12: tf config show steps prints the steps table with the model and effort: {r.returncode} {r.stdout[:400]}{r.stderr[:200]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} step assignment tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
