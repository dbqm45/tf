#!/usr/bin/env python3
"""A PR description assembled by a script (step G2): `run_state.py pr-body` builds it from the task files — always with the fields
"How it was checked", "Risk" and "How to roll back", also without an operations card and without a flag.
python3 .claude/tests/test_pr_body.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi "
        "45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
PLAN = ("# Plan: Limit dobowy\n\n"
        "- [ ] S1 — limit dobowy · criteria: AC-1 · files: fees.py · verify: `pytest`\n"
        "- [ ] S2 — komunikat o limicie · files: msg.py\n\n"
        "- **[assumption]** doba liczy się od północy czasu lokalnego\n")
ROLLBACK = "Wdróż poprzednią wersję: ./deploy.sh --previous (ok. 5 minut)"
ORDER = ("## Story", "## Slices", "## Criteria trace", "## How it was checked", "## System diff", "## Risk",
         "## How to roll back",
         "## Postponed for a decision", "## Assumptions")


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "user.email=t@example.com", "-c", "user.name=T",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, timeout=60)


def new_run(project: Path, weight: str = "normal") -> str:
    """A repository with a story branch and the IMP-1 task: a specification, a plan with two slices, a 'no flag' record."""
    project.mkdir(parents=True)
    git(project, "init", "-q", "-b", "main")
    for name in ("fees.py", "msg.py"):
        (project / name).write_text("x = 1\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "chore: init")
    git(project, "checkout", "-q", "-b", "story/limit-dobowy")
    story = "Popraw literówkę w README." if weight == "light" else "Jako kierowca chcę limitu dobowego opłaty za postój."
    call(project, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", story)
    d = str(project / ".tf" / "runs" / "IMP-1")
    if weight != "light":           # the light weight is assigned by start from the ticket text; only a human can lower it
        call(project, SCRIPTS / "run_state.py", "weight", d, "--set", weight)
    doc = project / CHANGES / "IMP-1"
    if weight != "light":
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(PLAN, encoding="utf-8")
    call(project, SCRIPTS / "run_state.py", "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")
    return d


def slice_done(project: Path, d: str) -> None:
    """S1: a change, green evidence, a commit with the slice footer, ticking off."""
    (project / "fees.py").write_text("x = 2\n", encoding="utf-8")
    call(project, TASK, "verify", "IMP-1", "S1", "--files", "fees.py", "--command", OK)
    git(project, "add", "fees.py")
    git(project, "commit", "-q", "-m", "feat(fees): add the daily cap\n\nSlice S1: limit dobowy")
    call(project, SCRIPTS / "run_state.py", "step", d, "S1", "R1", "scope", "pass")
    call(project, SCRIPTS / "run_state.py", "tick", d, "S1")


def body(project: Path) -> str:
    f = project / ".tf" / "runs" / "IMP-1" / "pr-body.md"
    return f.read_text(encoding="utf-8") if f.is_file() else ""


def section(text: str, heading: str) -> str:
    """The content of a section from its heading to the next second-level heading."""
    if heading not in text:
        return ""
    rest = text.split(heading, 1)[1]
    return rest.split("\n## ", 1)[0]


def body_after(p, rs, d):
    """The PR description after re-assembling."""
    call(p, rs, "pr-body", d, "--base", "main")
    return (p / ".tf" / "runs" / "IMP-1" / "pr-body.md").read_text(encoding="utf-8")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    rs = SCRIPTS / "run_state.py"
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p)
        slice_done(p, d)

        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(r.returncode == 0 and text and "pr-body.md" in r.stdout and "--body-file" in r.stdout,
              f"PB-1: pr-body saves the description in the run directory and gives --body-file: {r.returncode} {r.stdout} {r.stderr}")
        pos = [text.find(h) for h in ORDER]
        check(all(x >= 0 for x in pos) and pos == sorted(pos),
              f"PB-2: the description has fixed sections in a fixed order (incl. How it was checked, Risk, How to roll back): {pos}")
        story = section(text, "## Story")
        check("Limit dobowy" in story and "IMP-1" in story and "pasted in the conversation" in story
              and "docs/project/changes/IMP-1" in story,
              f"PB-3: story: title, key, ticket source and task directory: {story}")
        pieces = section(text, "## Slices")
        check("S1" in pieces and "feat(fees): add the daily cap" in pieces and "S2" in pieces
              and "komunikat o limicie" in pieces,
              f"PB-4: slices from the plan, with a commit with the 'Slice S1' footer next to the done one: {pieces}")
        how = section(text, "## How it was checked")
        check("S1" in how and how.count("3 passed") == 1 and "exit code 0" in how and "evidence/S1-1.json" in how
              and OK.split(" -c ")[1][:12] in how,
              f"PB-5: How it was checked: the command (without its output), the exit code and the evidence file of slice S1: {how}")
        check("S2" in how and "no verification evidence" in how,
              f"PB-6: a slice without evidence is named explicitly: {how}")
        check(r.stdout.count("S2") >= 1 and "no evidence" in r.stdout,
              f"PB-7: the missing evidence is also in the command's message: {r.stdout}")
        risk = section(text, "## Risk")
        check("normal" in risk and "Change risk" in risk and "fees.py" not in section(text, "## How to roll back"),
              f"PB-8: Risk: the task weight and the risk triage result: {risk}")
        back = section(text, "## How to roll back")
        check("git revert" in back and "bez flagi, bo zmiana jest w konfiguracji" in back,
              f"PB-9: without a card and without a flag: git revert and the recorded reason for no flag: {back}")
        check("none" in section(text, "## Postponed for a decision"),
              f"PB-10: nothing postponed -> 'none': {section(text, '## Postponed for a decision')}")
        check("- **[assumption]** doba liczy się od północy" in section(text, "## Assumptions"),
              f"PB-11: assumptions from the plan go into the description: {section(text, '## Assumptions')}")
        check("AC-1" in section(text, "## Criteria trace"),
              f"PB-12: criteria trace from the specification: {section(text, '## Criteria trace')}")

        # red evidence, a postponed item, an operations card with a rollback step, the scan verdict, the plan_drift result
        (p / "msg.py").write_text("x = 3\n", encoding="utf-8")
        call(p, TASK, "verify", "IMP-1", "S2", "--files", "msg.py", "--command", RED)
        call(p, rs, "park", d, "Abonamenty — czy limit ich dotyczy")
        card = p / ".tf" / "config" / "operations.json"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(json.dumps({"deploy": {"rollback": ROLLBACK}}, ensure_ascii=False), encoding="utf-8")
        sec = p / ".tf" / "runs" / "IMP-1" / "security" / "S1"
        sec.mkdir(parents=True)
        (sec / "verdict.json").write_text(json.dumps({"status": "PASS", "blocking": [], "other": [], "errors": []}),
                                          encoding="utf-8")
        call(p, rs, "step", d, "PR", "plan_drift", "pass")
        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        how = section(text, "## How it was checked")
        check(r.returncode == 0 and "S2" in how and "red" in how and "exit code 3" in how,
              f"PB-13: a slice's red evidence is named explicitly: {how}")
        check("PASS" in how and "plan_drift" in how and "pass" in how,
              f"PB-14: the security scan verdict and the plan_drift result are in 'How it was checked': {how}")
        # PB-24: the slice scan saves attempts in security/<slice>/attempt-<k>/ (security_scan.py) — the description takes the last one
        for k, status in ((1, "PASS"), (2, "FAIL")):
            att = p / ".tf" / "runs" / "IMP-1" / "security" / "S2" / f"attempt-{k}"
            att.mkdir(parents=True)
            (att / "verdict.json").write_text(json.dumps({"status": status, "blocking": [], "other": [], "errors": []}),
                                              encoding="utf-8")
        k2 = [ln for ln in section(body_after(p, rs, d), "## How it was checked").splitlines() if "**S2**" in ln]
        check(k2 and k2[0].rstrip().endswith("FAIL"),
              f"PB-24: the scan verdict from the last attempt-<k> (security_scan.py): {k2}")
        back = section(text, "## How to roll back")
        check(ROLLBACK in back and "operations.json" in back and "git revert" in back,
              f"PB-15: the rollback step from the operations card, next to git revert: {back}")
        check("Abonamenty — czy limit ich dotyczy" in section(text, "## Postponed for a decision"),
              f"PB-16: the postponed item is in the description: {section(text, '## Postponed for a decision')}")

        card.write_text(json.dumps({"deploy": {"rollback": ROLLBACK, "rollback_minutes": 12}}, ensure_ascii=False),
                        encoding="utf-8")
        call(p, rs, "pr-body", d, "--base", "main")
        check("about 12 min" in section(body(p), "## How to roll back"),
              f"PB-23: the rollback time from the card (rollback_minutes) is in the description: {section(body(p), '## How to roll back')}")

        card.write_text('{"deploy": {"rollback": "cofnij", "rollback_minutes": 1%s}}' % ("0" * 400), encoding="utf-8")
        r = call(p, rs, "pr-body", d, "--base", "main")
        check(r.returncode == 0 and "Traceback" not in r.stderr and "cofnij" in section(body(p), "## How to roll back"),
              f"PB-24: a huge number in rollback_minutes does not break the PR description: {r.stderr[-200:]}")

        # task flag -> turning the flag off as the rollback step
        r = call(p, rs, "flag", d, "set", "limit-dobowy", "--remove-by", "2027-01-31")
        call(p, rs, "pr-body", d, "--base", "main")
        back = section(body(p), "## How to roll back")
        check(r.returncode == 0 and "limit-dobowy" in back and "turn off" in back.lower(),
              f"PB-17: with a task flag the rollback starts by turning the flag off: {r.stdout} {back}")

        # card content is data: a heading from the card does not become a section of the description
        card.write_text(json.dumps({"deploy": {"rollback": "## Risk\nnone\n" + ROLLBACK}}, ensure_ascii=False),
                        encoding="utf-8")
        call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(text.count("\n## Risk") == 1 and ROLLBACK in text,
              f"PB-18: a heading written in the card does not create a second section: {text.count(chr(10) + '## Risk')}")

        # external content (ticket title, card, postponed items) does not notify people or load images in the PR description
        card.write_text(json.dumps({"deploy": {"rollback": "Zapytaj @octocat ![x](http://example.com/p.png)"}}),
                        encoding="utf-8")
        call(p, rs, "park", d, "Do decyzji @acme/platform — limit dla flot")
        meta_file = p / ".tf" / "runs" / "IMP-1" / "run.json"
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta_file.write_text(json.dumps({**meta, "title": "Limit dobowy @hubot"}, ensure_ascii=False), encoding="utf-8")
        call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        bare = re.findall(r"(?<![`\\w])@[A-Za-z0-9]", text)
        check(not bare and "![" not in text and "`@octocat`" in text and "`@acme/platform`" in text and "`@hubot`" in text,
              f"PB-22: @... mentions are in code formatting, and images are not embedded: {bare} {'![' in text}")

        # no remote repository: instead of trying a push — a stop with the environment code (measurement after step G)
        r = call(p, rs, "pr-body", d, "--base", "main")
        check("no remote" in r.stdout and "--code environment" in r.stdout and "git push" not in r.stdout.split("⚠", 1)[-1][:40],
              f"PB-25: without a remote repository pr-body says not to push, and gives a STOP with the environment code: {r.stdout}")
        bare = Path(t) / "remote.git"
        git(Path(t), "init", "-q", "--bare", str(bare))
        git(p, "remote", "add", "origin", str(bare))
        r = call(p, rs, "pr-body", d, "--base", "main")
        check("no remote" not in r.stdout and "--body-file" in r.stdout,
              f"PB-26: with a remote repository, no warning: {r.stdout}")

        # without a base branch the description is still produced
        r = call(p, rs, "pr-body", d, "--base", "nie-ma-takiej")
        check(r.returncode == 0 and "## How to roll back" in body(p) and "nie-ma-takiej" in section(body(p), "## Slices"),
              f"PB-19: an unknown base branch does not stop the description, and the lack of commits is named: {r.returncode} {r.stdout}")

    # light weight: without a specification — the fields are still there
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p, "light")
        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(r.returncode == 0 and all(h in text for h in ORDER) and "light" in section(text, "## Risk")
              and "specification" in section(text, "## Criteria trace"),
              f"PB-20: a task without a specification has all the fields, and the trace says outright that there is none: {r.returncode} {r.stdout}")

    # a run without a task (old layout) -> a clear refusal
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        old = p / ".tf" / "runs" / "stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary"}), encoding="utf-8")
        r = call(p, rs, "pr-body", str(old))
        check(r.returncode == 2 and not (old / "pr-body.md").exists(),
              f"PB-21: a run without a task -> refusal with code 2: {r.returncode} {r.stdout}")

    # the "Visual check" section exists only for UI work that is worth it: absent for a backend change, a trivial UI touch
    # and --no-visual; skipped (never silent) when it is worth it and nothing was recorded; counts when recorded
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p)
        slice_done(p, d)
        text = body_after(p, rs, d)
        check("Visual check" not in text, "PB-31: a backend change has no Visual check section at all")
        plan = p / CHANGES / "IMP-1" / "plan.md"
        plan.write_text(PLAN.replace("files: fees.py", "files: fees.py, src/app/home.component.html"), encoding="utf-8")
        check("Visual check" not in body_after(p, rs, d), "PB-32: one UI file below the threshold: still no section")
        plan.write_text(PLAN.replace("files: fees.py", "files: a.component.html, b.component.html"), encoding="utf-8")
        text = body_after(p, rs, d)
        vis = section(text, "## Visual check")
        check("- skipped:" in vis and "not applicable" not in vis
              and text.find("## How it was checked") < text.find("## Visual check") < text.find("## Risk"),
              f"PB-33: two UI files and no record: skipped, between How it was checked and Risk: {vis}")
        r = call(p, rs, "stage", d, "slices", "--no-visual")
        check(r.returncode == 0 and json.loads((Path(d) / "run.json").read_text(encoding="utf-8")).get("visual") == "off",
              f"PB-34a: --no-visual is recorded in run.json: {r.stdout}{r.stderr}")
        check("Visual check" not in body_after(p, rs, d), "PB-34: --no-visual removes the section")
        call(p, rs, "stage", d, "slices", "--visual")
        screens = p / ".tf" / "runs" / "IMP-1" / "screens"
        screens.mkdir()
        (screens / "check.md").write_text("Skipped: no browser in this environment\n", encoding="utf-8")
        vis = section(body_after(p, rs, d), "## Visual check")
        check("- skipped: no browser in this environment" in vis, f"PB-35: the recorded reason is shown: {vis}")
        (screens / "compare.md").write_text(
            "# Visual comparison\n\n| route | viewport | result | before | after |\n|---|---|---|---|---|\n"
            "| / | 1280x800 | changed | screens/before/index@1280x800.png | screens/after/index@1280x800.png |\n"
            "| /login | 1280x800 | identical | screens/before/login@1280x800.png | screens/after/login@1280x800.png |\n"
            "| /about | 1280x800 | identical | screens/before/about@1280x800.png | screens/after/about@1280x800.png |\n",
            encoding="utf-8")
        (screens / "check.md").write_text("- AC-1 · / @1280x800 — heading is blue — **matches**\n"
                                          "- AC-2 · /login @1280x800 — no button — **does not match**\n", encoding="utf-8")
        vis = section(body_after(p, rs, d), "## Visual check")
        check("2 identical" in vis and "1 changed" in vis and "1 match" in vis and "1 mismatch" in vis
              and ".tf/runs/IMP-1/screens" in vis, f"PB-36: counts and the screenshots path: {vis}")
        (screens / "check.md").unlink()
        vis = section(body_after(p, rs, d), "## Visual check")
        check("check.md" in vis and "not checked" in vis, f"PB-37: screenshots without a check are named: {vis}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} PR description tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
