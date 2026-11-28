#!/usr/bin/env python3
"""Coverage of the /tf-task loop's Bash commands by permissions.allow (PRB-32): the tf skills (SKILL.md and scripts/)
and the pdi delivery-phase scripts (phase_run.py cuts publish) run git and gh; every such call must be
in `permissions.allow` of the project's assembled settings (.claude/settings.json, core + mode-pdi).

Source (read 2026-11-05 code.claude.com/docs/en/permissions): without a covering `permissions.allow` rule a Bash command
in `claude --print --permission-mode acceptEdits` asks the human, and in `-p` the request ends in a refusal.

Two layouts: in the factory workspace (source `core/` + `modes/`) the test assembles settings from the overlay files, in an installed
project (`.claude/tests/` next to `.claude/skills/`) it reads `.claude/settings.json` and `.claude/settings.local.json`
and checks only the commands of skills that are installed (without pdi-decisions — without its commands).

  python3 .claude/tests/test_settings_coverage.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
# installed project: <project>/.claude/tests/test_settings_coverage.py (takes precedence — also in the factory's .work/)
INSTALLED = HERE.parent.name == "tests" and HERE.parent.parent.name == ".claude" \
    and (HERE.parent.parent / "skills").is_dir()
ROOT = HERE.parents[2] if INSTALLED else next(
    (p for p in HERE.parents if (p / "core" / "settings.json").is_file() and (p / "core" / "skills" / "tf").is_dir()),
    None)
LOOP = ".claude/skills/tf/"
PDI = ".claude/skills/pdi-decisions/"
PY = "python3"

# Commands the /tf-task loop and the pdi phases run in a session (a persona in --print). Each must have an `allow` rule.
# We do not list `git push` or `gh pr …` of the cuts publish phase here, because they are in phase_run.py (run outside the session
# of the persona), not in the loop's prompt.
REQUIRED = [
    # the loop during a run (SKILL.md: start, slice loop, completion)
    "git status",
    "git status --porcelain",
    "git diff",
    "git diff --name-only HEAD",
    "git log --oneline -5",
    "git show HEAD",
    "git branch --show-current",
    "git switch main",                         # back to the default branch after a slice
    "git switch -c story/tsk-1-fundament",     # story branch (cut)
    "git switch -c story/import-invoices",          # story branch (ordinary)
    "git add -A",
    "git add src/payments/retry.ts",
    "git commit -m 'feat(x): y'",
    # loop scripts
    "python3 .claude/skills/tf/scripts/run_report.py start --task TSK-1",
    "python3 .claude/skills/tf/scripts/run_report.py finish .tf/runs/PROJ-1",
    "python3 .claude/skills/tf/scripts/plan_drift.py .tf/runs/PROJ-1 --base main",
    "python3 .claude/skills/tf/scripts/security_scan.py scan --slice S1 --attempt 1",
    "python3 .claude/skills/tf/scripts/ui_snap.py worth .tf/runs/PROJ-1 --base main",
    "python3 .claude/skills/tf/scripts/ui_snap.py capture .tf/runs/PROJ-1 --label before --start",
    "python3 .claude/skills/tf/scripts/run_state.py verify .tf/runs/PROJ-1 S1 --files src/a.py",
    "python3 .claude/skills/core-delivery-lifecycle/scripts/pr_budget.py --base main",
    # the design session record (tf-design)
    "python3 .claude/skills/tf-design/scripts/design_session.py stage uprawnienia 1 accept --decision x",
    # a pdi script called at the end of the architecture/design phase (decision_record.py check — in the phase_run.py prompt)
    "python3 .claude/skills/pdi-decisions/scripts/decision_record.py check",
    # the PR loop (N2, pr_loop.py fix): fixing comments, N3 verification and a commit with three -m
    "./verify.sh",
    "git commit -m 'fix(x): y' -m 'PR loop round 1' -m 'Change: TSK-1'",
    # PR loop steps in the phase container (pdi runs them outside the persona session; an entry in case of manual use)
    "python3 .claude/skills/pdi-decisions/scripts/pr_loop.py verify",
]


def installed_python() -> str:
    """The Python command from the install manifest — the installer writes it into the rules instead of `python3` (apply_python)."""
    try:
        data = json.loads((ROOT / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
        return str(data.get("python") or PY)
    except (OSError, ValueError):
        return PY


def load_installed_allow() -> list[str]:
    """The `permissions.allow` rules of the installed project (team and private mode), with `python3` in place
    the Python command chosen at install time."""
    py = installed_python()
    rules: list[str] = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            rules += (json.loads(f.read_text(encoding="utf-8")).get("permissions") or {}).get("allow") or []
    if py != PY:
        rules = [f"Bash({PY} " + r[len(f"Bash({py} "):] if r.startswith(f"Bash({py} ") else r for r in rules]
    return rules


def load_allow() -> list[str]:
    """The `permissions.allow` rules assembled from core + mode-pdi + pack-it (the loop's SKILL calls
    `requirements_lint.py` from pack-it if it is installed — the installer assembles settings the same way)."""
    if INSTALLED:
        return load_installed_allow()
    rules: list[str] = []
    for rel in ("core/settings.json", "modes/mode-pdi/settings.json",
                "packs/pack-it/settings.json"):
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        rules += (data.get("permissions") or {}).get("allow") or []
    return rules


def bash_patterns(rules: list[str]) -> list[str]:
    """`Bash(...)` patterns from the assembled rules — returns only the commands (without `Bash(` and `)`)."""
    return [m.group(1) for r in rules if (m := re.fullmatch(r"Bash\((.*)\)", r))]


def to_regex(pattern: str) -> re.Pattern:
    """The rule `Bash(foo *)` matches every command starting with `foo` (with or without an argument).
    The rule `Bash(foo)` matches only exactly `foo` (without a trailing *)."""
    # also handle the ':*' variant (equivalent per code.claude.com/docs/en/permissions)
    if pattern.endswith(":*"):
        pattern = pattern[:-2] + " *"
    if pattern.endswith(" *"):
        # `foo *` matches `foo`, `foo arg`, `foo arg1 arg2 …`
        head = re.escape(pattern[:-2])
        return re.compile(rf"^{head}(?:\s.*)?$")
    return re.compile(f"^{re.escape(pattern)}$")


def covers(cmd: str, patterns: list[re.Pattern]) -> bool:
    return any(p.match(cmd) for p in patterns)


def skill_path() -> Path:
    if INSTALLED:
        return ROOT / ".claude/skills/tf-task/" / "SKILL.md"
    return ROOT / "core" / "skills" / "tf-task" / "SKILL.md"


def required() -> list[str]:
    """Commands to check: in an installed project only those whose skill is installed."""
    if not INSTALLED:
        return REQUIRED
    loop, pdi = (ROOT / LOOP).is_dir(), (ROOT / PDI).is_dir()
    return [c for c in REQUIRED if (PDI in c and pdi) or (PDI not in c and loop)]


def main() -> int:
    if ROOT is None:
        print("✗ no root directory with core/settings.json and core/skills/tf/")
        return 1
    cmds = required()
    if not cmds:
        print("– skipping: the project has neither the tf skills nor pdi-decisions — "
              "nothing to check; the full check is in the factory workspace (tools/workspace.py check)")
        return 0
    allow = load_allow()
    patterns = [to_regex(p) for p in bash_patterns(allow)]
    fails: list[str] = []
    for cmd in cmds:
        if not covers(cmd, patterns):
            fails.append(f"Bash command without an allow rule: {cmd!r}")
    # The loop's SKILL.md lists script commands — check that each has a prefix allowance.
    # In an installed project we skip scripts of skills outside the install (e.g. requirements_lint.py from pack-it).
    skill = skill_path()
    text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    for extra in sorted((skill.parent / "references").glob("*.md")):   # commands from the skill's detail files too
        text += "\n" + extra.read_text(encoding="utf-8")
    script_calls = set(re.findall(r"python3 \.claude/skills/[^\s`]+\.py", text))
    if INSTALLED:
        script_calls = {c for c in script_calls if (ROOT / c.split(" ", 1)[1]).is_file()}
    # every script of the tf skill (scripts/*.py) has an allow rule
    scripts_dir = skill.parent / "scripts"
    script_calls |= {f"python3 {LOOP}scripts/{p.name}" for p in sorted(scripts_dir.glob("*.py"))} \
        if skill.is_file() else set()
    for call in sorted(script_calls):
        if not covers(f"{call} --test", patterns):
            fails.append(f"loop script (SKILL.md or scripts/) without an allow rule: {call}")
    for f in fails:
        print(f"✗ {f}")
    total = len(cmds) + len(script_calls)
    where = "installed .claude/settings*.json" if INSTALLED else "core + overlays"
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} Bash commands covered by allow ({where})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
