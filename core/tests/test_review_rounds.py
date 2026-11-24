#!/usr/bin/env python3
"""A review that ends (step F2): `scope-reviewer` labels findings as important / minor / pre-existing, only an important one
starts a new round, and the slice's round limit is enforced by a script — a third round without a human decision is a refusal.
python3 .claude/tests/test_review_rounds.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
SKILL = ROOT / ".claude" / "skills" / "tf-task" / "SKILL.md"


def call(project: Path, cfg: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "CLAUDE_PROJECT_DIR": str(project), "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=project, capture_output=True, text=True,
                          env=env, timeout=120)


def rounds(project: Path) -> int:
    meta = json.loads((project / ".tf" / "runs" / "IMP-1" / "run.json").read_text(encoding="utf-8"))
    return len((meta.get("current") or {}).get("rounds") or [])


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        p.mkdir()
        call(p, cfg, "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        call(p, cfg, "run_state.py", "weight", d, "--set", "normal")
        subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "task_state.py"), "mode", "IMP-1", "auto"], cwd=p,
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        (p / "docs" / "project" / "changes" / "IMP-1" / "spec.md").write_text(
            "# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi "
            "45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n",
            encoding="utf-8")
        call(p, cfg, "run_state.py", "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")

        call(p, cfg, "run_state.py", "finding", d, "S1", "kod spoza kryteriów w fees.py")   # step G4: a finding before 'fail'
        r1 = call(p, cfg, "run_state.py", "step", d, "S1", "R1", "scope", "fail")
        r2 = call(p, cfg, "run_state.py", "step", d, "S1", "R2", "code", "run")
        check(r1.returncode == 0 and r2.returncode == 0 and rounds(p) == 2,
              f"PR-1: two rounds of a slice go through: {r1.stdout}{r1.stderr} | {r2.stdout}{r2.stderr}")
        r = call(p, cfg, "run_state.py", "step", d, "S1", "R3", "test", "run")
        check(r.returncode == 2 and "STOP" in r.stdout and "--needs stop --code" in r.stdout and rounds(p) == 2,
              f"PR-2: a third round without a human decision -> refusal with a STOP hint, state unchanged: {r.returncode} {r.stdout}")

        # after a stop and a human decision the loop gets another two attempts
        call(p, cfg, "run_state.py", "stage", d, "needs", "--needs", "stop", "--code", "tests", "--reason", "pytest: 1 failed")
        r3 = call(p, cfg, "run_state.py", "step", d, "S1", "R3", "test", "run")
        r4 = call(p, cfg, "run_state.py", "step", d, "S1", "R4", "code", "run")
        r5 = call(p, cfg, "run_state.py", "step", d, "S1", "R5", "test", "run")
        meta = json.loads((p / ".tf" / "runs" / "IMP-1" / "run.json").read_text(encoding="utf-8"))
        check(r3.returncode == 0 and r4.returncode == 0 and r5.returncode == 2 and rounds(p) == 4,
              f"PR-3: after a human decision two more rounds, the fifth a refusal again: {r3.returncode} {r4.returncode} "
              f"{r5.returncode} {r5.stdout}")
        check(meta.get("stage") == "slices" and not any(k in meta for k in ("needs", "stop_text", "stop_code", "needs_at")),
              f"PR-4: resuming through step clears the whole stop record: {sorted(meta)}")
        waits = meta.get("waits") or []
        check(len(waits) == 1 and waits[0].get("needs") == "stop" and waits[0].get("from") and waits[0].get("to"),
              f"PR-4a: the wait for the human is kept as a span for the report's time breakdown: {waits}")
        r = call(p, cfg, "run_state.py", "step", d, "S2", "R1", "test", "run")
        check(r.returncode == 0 and rounds(p) == 1, f"PR-5: a new slice counts rounds from the start: {r.returncode} {r.stdout}")
        r = call(p, cfg, "run_state.py", "step", d, "S2", "R3", "test", "run")
        check(r.returncode == 2, f"PR-6: a new slice does not start from the third round either: {r.returncode} {r.stdout}")

    # ticking off a slice requires a recorded scope review result (after the measurement after step G: recorded in 7 of 15 runs)
    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        p.mkdir()
        (p / "fees.py").write_text("x = 1\n", encoding="utf-8")
        call(p, cfg, "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        (p / "docs" / "project" / "changes" / "IMP-1" / "plan.md").write_text(
            "# Plan\n\n- [ ] S1 — literówka · files: fees.py · verify: `pytest`\n", encoding="utf-8")
        ok = f'{sys.executable} -c "print(1)"'
        subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "task_state.py"), "verify", "IMP-1", "S1", "--files",
                        "fees.py", "--command", ok], cwd=p, capture_output=True, text=True,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        plan = lambda: (p / "docs" / "project" / "changes" / "IMP-1" / "plan.md").read_text(encoding="utf-8")
        r = call(p, cfg, "run_state.py", "tick", d, "S1")
        check(r.returncode == 2 and "scope" in r.stdout and "scope-reviewer" in r.stdout and "- [ ] S1" in plan(),
              f"PR-10: without a recorded scope review result a slice is not ticked off: {r.returncode} {r.stdout}")
        call(p, cfg, "run_state.py", "step", d, "S1", "R1", "scope", "run")
        r = call(p, cfg, "run_state.py", "tick", d, "S1")
        check(r.returncode == 2 and "- [ ] S1" in plan(), f"PR-11: a review in progress is not a result: {r.returncode} {r.stdout}")
        call(p, cfg, "run_state.py", "finding", d, "S1", "kod spoza kryteriów")
        call(p, cfg, "run_state.py", "step", d, "S1", "R1", "scope", "fail")
        r = call(p, cfg, "run_state.py", "tick", d, "S1")
        check(r.returncode == 2 and "R2" in r.stdout and "- [ ] S1" in plan(),
              f"PR-12: after a failed review the refusal points to a new round: {r.returncode} {r.stdout}")
        call(p, cfg, "run_state.py", "step", d, "S1", "R2", "scope", "pass")
        r = call(p, cfg, "run_state.py", "tick", d, "S1")
        check(r.returncode == 0 and "- [x] S1" in plan(), f"PR-13: a review recorded as passed -> ticking off: {r.returncode} {r.stdout}")
        r = call(p, cfg, "run_state.py", "finding", d, "S1", "drugie ustalenie")
        check("closed" in r.stdout and "control:" not in r.stdout,
              f"PR-14: the message after recording a finding defers the check to closing the task, it does not demand it right away: {r.stdout}")

    # the review agent: finding labels and the new-round rule
    cfg_text = (ROOT / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8")
    prompt = cfg_text.split("\n  scope-reviewer:", 1)[-1][:2500] if "\n  scope-reviewer:" in cfg_text else ""
    check(all(w in prompt for w in ("[important]", "[minor]", "[pre-existing]")),
          "PR-7: scope-reviewer labels every finding: [important], [minor] or [pre-existing] (like the tf skill)")
    check("OUT OF SCOPE" in prompt and "only" in prompt and "[important]" in prompt and "before the change" in prompt
          and "previous round" in prompt,
          "PR-8: the OUT OF SCOPE verdict only for an important finding; pre-existing is code from before the change; the second round looks at "
          "only the changes since the previous round")
    body = SKILL.read_text(encoding="utf-8")
    step4 = body.split("**The scope review:**", 1)[-1].split("5. **", 1)[0]
    check(all(w in step4 for w in ("important", "minor", "pre-existing", "parked.md")) and len(body) <= 15000,
          f"PR-9: the loop reverts code only for an important finding, parks minor and pre-existing; SKILL.md within the limit: {len(body)}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} review and round limit tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
