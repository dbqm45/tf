#!/usr/bin/env python3
"""Tests of the "task → PR" loop in the core: the `tf` main-session agent, the `tf` skill, the run scripts, permissions
and the guide. python3 .claude/tests/test_tf_skill.py"""
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills" / "tf").is_dir())


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    agents = ROOT / ".claude" / "agents" / "_generated"
    agent = next(iter(agents.rglob("tf-task.md")), None)
    text = agent.read_text(encoding="utf-8") if agent else ""
    fm = text.split("---")[1] if text.count("---") >= 2 else ""
    check("Agent(scout, researcher, quick-fixer, scope-reviewer, spec-reviewer, architect, security-reviewer, mcp-runner)" in fm
          and "skills:" not in fm and "maxTurns" not in fm,
          f"T-1: the tf-task agent — a main session with a list of agents, without preloading skills and without a turn limit: {fm[:300]}")
    skill = ROOT / ".claude" / "skills" / "tf-task"
    engine = ROOT / ".claude" / "skills" / "tf"   # the shared engine of the /tf family: scripts/ and templates/
    check(".claude/skills/tf-task/SKILL.md" in text and "talos" not in text.lower() and (skill / "SKILL.md").is_file(),
          "T-2: the agent reads the process skill from an installed file; the old name is not in the core")
    script = ".claude/skills/tf/scripts/run_report.py"
    check((ROOT / script).is_file() and script in (skill / "SKILL.md").read_text(encoding="utf-8"),
          "T-3: the run script sits in the shared tf engine and the path is in the loop skill")
    allow = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            allow += json.loads(f.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    check(any(script in a for a in allow), f"T-4: uprawnienie dla skryptu przebiegu: {[a for a in allow if 'run' in a]}")
    guide = ROOT / ".tf" / "factory" / "GUIDE.md"
    guide_text = guide.read_text(encoding="utf-8") if guide.is_file() else ""
    check("/tf-task" in guide_text and "claude --agent tf-task" in guide_text, "T-5: przewodnik rdzenia opisuje /tf-task i agenta tf-task")
    personas = [p for p in agents.rglob("*.md") if p.parent.name not in ("shared", "consult") and p.stem == p.parent.name]
    check(personas == [] or all("`tf`" not in p.read_text(encoding="utf-8") for p in personas),
          "T-6: personas do not delegate to the tf agent (it is the main session, not an executor)")
    body = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""

    def ref(name: str) -> str:
        """A skill detail file (references/); it counts only when SKILL.md lists it."""
        f = skill / "references" / name
        return f.read_text(encoding="utf-8") if f.is_file() and f"references/{name}" in body else ""

    cuts = ref("pdi-cuts.md")
    intake = body.split("## 1.", 1)[-1].split("## 2.", 1)[0]
    check("requirements_lint.py --story" in intake and "STORY-001" in intake and "--auto" in intake
          and "STOP" in intake and "split" in intake and "(pack-it)" in intake,
          "T-7: story intake — shape lint (pack-it, conditional); with --auto STORY-001 → STOP with a proposal to split")
    loop = body.split("## 3.", 1)[-1].split("## 4.", 1)[0]
    check("`Flag: " in cuts and "release.yaml" in cuts and "behind the flag" in cuts and "references/pdi-cuts.md" in loop,
          "T-8: a slice with a flag — code behind the flag and a `Flag: <key>` trailer in the commit (release plan release.yaml); "
          "the slice loop points to references/pdi-cuts.md")
    check("--task" in body and "--task" in cuts and "Change: TSK" in cuts and "changes/" in cuts and "/runs/" in cuts
          and "story/tsk-" in cuts and "pdi/CHG-n-delivery" in cuts,
          "T-9: entering a TSK from the change plan (`run_report.py start --task`), a branch with the key from the phase branch, `Change:` "
          "w commitach, raport w changes/CHG-n/runs/ — w references/pdi-cuts.md")
    fixes = cuts.split("## Fixes from the PR loop", 1)[-1] if "## Fixes from the PR loop" in cuts else ""
    check("Rework-Cause:" in fixes and all(v in fixes for v in ("spec-gap", "agent-error", "requirement-change",
                                                                 "unknown")),
          "T-11: a fix commit from the PR loop has a `Rework-Cause:` trailer with one of 4 causes (tf metrics, B3)")
    finish = body.split("## 4.", 1)[-1].split("## Who does what", 1)[0]
    check("run_state.py pr-body" in finish and "--body-file" in finish and "description" in finish,
          "T-12: the script builds the PR description (`run_state.py pr-body` → `--body-file`); the change risk triage section (B1b) "
          "is inserted by the script itself — test_pr_body PB-8 checks this")
    scan = ".claude/skills/tf/scripts/security_scan.py"
    check((ROOT / scan).is_file() and any(scan in a for a in allow)
          and (engine / "templates" / "verify.sh").is_file()
          and "security_scan.py scan" in loop and "feedback.md" in loop and "STOP" in loop
          and "security_scan.py cooldown" in body,
          "T-10: security scan in the slice loop (script, permission, FAIL → feedback.md, STOP), grace period "
          "wersji na starcie, szablon verify.sh")

    state = ".claude/skills/tf/scripts/run_state.py"
    check((ROOT / state).is_file() and (engine / "templates" / "dashboard.html").is_file()
          and any(state in a for a in allow) and "run_state.py stage" in body and "run_state.py step" in body
          and "dashboard.html" in guide_text,
          "T-11: run state for the preview (script, dashboard template, permission, commands in the skill, description in the guide)")
    body_names = [w for w in ("Talos", "talos-story-run", "mode-talos") if w in body]
    check(body_names == [], f"T-13: the tf skill does not use old names: {body_names}")
    check((ROOT / ".claude" / "skills" / "core-delivery-lifecycle" / "scripts" / "pr_budget.py").is_file()
          and any("pr_budget.py" in a for a in allow) and any(a.startswith("Bash(./verify.sh") for a in allow),
          "T-14: the loop permissions (pr_budget.py, ./verify.sh) are in the core settings")

    # step E1: /tf is also invoked by the model (a request in a plain sentence), and the script recognises the input and source
    front = body.split("---")[1] if body.count("---") >= 2 else ""
    desc = next((ln for ln in front.splitlines() if ln.startswith("description:")), "")
    check("disable-model-invocation" not in front and desc.startswith("description: Use when") and "keywords:" in front,
          f"T-15: the tf skill can be invoked by the model — no disable-model-invocation, the description as a selection rule, words: {desc}")
    entry = body.split("## Input", 1)[-1].split("## 0.", 1)[0] if "## Input" in body else ""
    check(body.find("## Input") != -1 and body.find("## Input") < body.find("## 0.")
          and all(w in entry for w in ("question", "quick", "task", "AskUserQuestion", "in one sentence")),
          "T-16: the 'Wejście' (Input) section before the start — task / question / small change / doubt → one question")
    intake_script = ".claude/skills/tf/scripts/intake.py"
    check((ROOT / intake_script).is_file() and "intake.py resolve" in entry and "intake.py tracker" in entry
          and any(intake_script in a for a in allow),
          f"T-17: input recognition by a script (resolve, tracker) with a permission: {[a for a in allow if 'intake' in a]}")
    check(all(w in entry for w in ("read only", "paste", "you install nothing", "data, not instructions", "--source"))
          and "/tf jira" not in body and "/tf linear" not in body,
          "T-18: tracker — reading through a connected tool or pasting the content; the factory installs nothing; "
          "the ticket content is data; the source goes to ticket.md; a command without a tool name")
    check("--auto" in entry and "STOP" in entry, "T-19: without a human (--auto) the question about the source turns into a STOP")

    # SKILL.md fits in the limit restored after compaction; the details are in references/, listed in SKILL.md
    limit = 15000
    refs = sorted(f.name for f in (skill / "references").glob("*.md")) if (skill / "references").is_dir() else []
    check(len(body) <= limit, f"T-20: SKILL.md has {len(body)} characters (limit {limit}) — move the details to references/")
    check(refs and all(f"references/{n}" in body for n in refs)
          and {"intake.md", "pdi-cuts.md", "feature-flag.md", "security.md", "weight.md",
               "modes-and-stops.md"} <= set(refs),
          f"T-21: every references/ file is listed in SKILL.md: {refs}")
    check("read only" in ref("intake.md") and "intake.py tracker" in ref("intake.md")
          and "Flag: <klucz>" in ref("feature-flag.md") and "test environment" in ref("feature-flag.md")
          and "feedback.md" in ref("security.md") and "min-release-age" in ref("security.md"),
          "T-22: the tracker, feature flag and security scan details are in references/ files")

    # measurement after E1: a STOP before the task is created leaves no trace or report; compound commands are rejected
    check("always create" in entry and "§1" in entry and "trace" in entry,
          "T-23: when the task content exists (even incomplete), the loop always creates the task; questions about criteria go in §1, "
          "so that a STOP leaves a trace and a report")
    review = next((ln for ln in loop.splitlines() if "**The scope review:**" in ln), "")
    check("always" in review and "`scope-reviewer`" in review and "small diff" in review,
          f"T-25: the scope review is always done by scope-reviewer, also for a small diff (not the main session): {review}")
    check("AC-1" in loop and "extra commit" in loop,
          "T-26: the criterion id in the test from the first version — adding it after the fact is an extra commit")
    # step E2: task weight — the script assigns it, the loop tells the human what was chosen and knows the consequences
    start = body.split("## 0.", 1)[-1].split("## 1.", 1)[0]
    waga = ref("weight.md")
    check("`Weight:" in start and "references/weight.md" in start and "in one sentence" in start,
          "T-27: start — the loop passes the `Weight:` line to the human in one sentence; the consequences are in references/weight.md")
    check(all(w in waga for w in ("light", "zwykła", "pełna", "run_state.py weight", "--by human:", "security-reviewer",
                                  "approve", "STOP", "without `spec.md`")),
          "T-28: references/weight.md — three weights, consequences, who changes them, mandatory review for full, STOP without supervision")
    # step E3: modes (Plan / normal / Auto), the human's consent to the plan recorded by a script, a closed list of STOP codes
    import re as _re
    modes = ref("modes-and-stops.md")
    plan_part = body.split("## 2.", 1)[-1].split("## 3.", 1)[0]
    stop_part = body.split("## The STOP block", 1)[-1].split("## Example", 1)[0]
    check("`--plan`" in start and "run_state.py approve" in plan_part and "references/modes-and-stops.md" in plan_part,
          "T-29: the mode from the human's command goes to the first `stage` (--auto or --plan); the consent to the plan is recorded by "
          "`run_state.py approve`; details in references/modes-and-stops.md")
    script_text = (ROOT / state).read_text(encoding="utf-8")
    block = script_text.split("STOP_CODES = {", 1)[-1].split("}", 1)[0]
    codes = _re.findall(r'^\s*"([a-z-]+)":', block, _re.M)
    check("--code" in stop_part and len(codes) >= 10 and all(f"`{c}`" in modes for c in codes)
          and all(w in modes for w in ("Plan", "Auto", "approve", "mode")),
          f"T-30: the STOP block has a code from a closed list; references/modes-and-stops.md describes every code from the script: "
          f"{[c for c in codes if f'`{c}`' not in modes]}")
    check(all(f"`{c}`" in stop_part for c in codes),
          f"T-32: the 'Blok STOP' section in SKILL.md lists all codes (measurement after E3: in 8 of 15 runs the loop "
          f"guessed the code and got a refusal): missing {[c for c in codes if f'`{c}`' not in stop_part]}")
    check(all(w in modes for w in ("Komunikat dla człowieka", "AskUserQuestion", "run_state.py message", "your own description")),
          "T-31: after recording a stop the loop shows the human the script's message (a question via a tool with options), "
          "not its own description")
    rules = body.split("## Input", 1)[0]
    check("you do not chain commands" in rules and all(s in rules for s in ("`;`", "`&&`", "a pipe")),
          "T-24: the 'one action per command' rule says explicitly what not to combine (`;`, `&&`, pipe)")

    # step E6: a pdi change slice goes the task way — the same run with a spec, evidence and a criteria trace
    check("CHG-12-TSK-57" in cuts and ".tf/runs/cuts" not in cuts and "old layout" not in cuts and "refuses" not in cuts
          and "without a task" not in cuts,
          "T-33: references/pdi-cuts.md describes the slice task `<CHG>-<TSK>`, without the old `.tf/runs/cuts/` layout")
    check(all(w in cuts for w in ("spec", "verify", "trace", "ticket.md")) and "gate" in cuts and "security-reviewer" in cuts,
          "T-34: a slice has a spec, evidence and a trace; the consent to the plan is given by the change gate, the security review stays")
    check("docs(task): record" in cuts and "runs/TSK-" in cuts and "changes/INDEX.md" not in body + cuts
          and "first commit" in " ".join(cuts.split()),
          "T-35: one final commit (the task directory and the slice report); the skill no longer says to add INDEX.md — the command "
          "of the commit is printed by `finish`; the branch's first commit is a slice "
          "— pdi takes the PR title from it")
    weight_ref = ref("weight.md")
    check("has no weight" not in weight_ref and "slice" in weight_ref and "gate" in weight_ref,
          "T-36: references/weight.md — a slice has a weight; with full the unsupervised run does not stop, because the change plan "
          "was approved at the pdi gate")
    guide = next((p for p in (ROOT / ".tf" / "factory" / "LOOP.md",) if p.is_file()), None)
    gtext = guide.read_text(encoding="utf-8") if guide else ""
    check(guide is not None and ".tf/runs/cuts" not in gtext and "CHG-12-TSK-57" in gtext,
          f"T-37: LOOP.md describes a slice as the task `<CHG>-<TSK>`, without an exception for the old layout: {guide}")

    check("run_state.py finding" in body.split("## 3.", 1)[-1].split("## 4.", 1)[0],
          "T-40: an important finding from the scope review is recorded by the loop with `run_state.py finding` (step G4)")
    check("tf task close" in gtext and "tf task finding" in gtext and "lessons.md" in gtext and "tf status --all" in gtext,
          "T-41: LOOP.md describes closing a task: merge, check against the findings, a lesson from the human, the in-progress list")
    check("Jak cofnąć" in finish and "risk_triage.py --md" not in finish,
          "T-38: the PR step lists the description fields (incl. 'Jak cofnąć') and no longer says to assemble the risk triage by hand")
    check("pr-body" in gtext and all(w in gtext for w in ("How it was checked", "Risk", "How to roll back", "deploy.rollback")),
          "T-39: LOOP.md describes the PR description from the script: three fixed fields and the rollback step from the operations card")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tf loop tests in the core")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
