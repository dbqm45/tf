#!/usr/bin/env python3
"""
Task run state and the preview (skill tf): the only writer of the stage and round in run.json
and the dashboard generator. The state is written by the script, not the model — the model only calls the command.

  python3 .claude/skills/tf/scripts/run_state.py stage <run-directory> <stage> [--needs plan|stop] [--code <code>] [--auto|--plan]
  python3 .claude/skills/tf/scripts/run_state.py mode <run-directory> [plan|normal|auto]   # the task's mode
  python3 .claude/skills/tf/scripts/run_state.py approve <run-directory>                   # the human's consent to the plan
  python3 .claude/skills/tf/scripts/run_state.py message <code> [--json]                   # the stop message for the human
        [--reason "<STOP reason>"] [--pr N] [--auto] [--visual|--no-visual] [--effort low|medium|high]
  python3 .claude/skills/tf/scripts/run_state.py step <katalog-przebiegu> S2 R1 verify fail
  python3 .claude/skills/tf/scripts/run_state.py step <katalog-przebiegu> PR plan_drift run
  python3 .claude/skills/tf/scripts/run_state.py spec <katalog-przebiegu> [new]
  python3 .claude/skills/tf/scripts/run_state.py flag <katalog-przebiegu> mode      # auto | manual
  python3 .claude/skills/tf/scripts/run_state.py flag <run-directory> set <key> [--remove-by YYYY-MM-DD]
  python3 .claude/skills/tf/scripts/run_state.py flag <run-directory> none --reason "no flag, because …"
  python3 .claude/skills/tf/scripts/run_state.py trace <run-directory> [--base <branch>]
  python3 .claude/skills/tf/scripts/run_state.py pr-body <run-directory> [--base <branch>]   # the PR description for --body-file
  python3 .claude/skills/tf/scripts/run_state.py panel <run-directory> [--record <reviewer> pass|fail --note "…"]
  python3 .claude/skills/tf/scripts/run_state.py finding <run-directory> S2 "<important review finding>" [--round R]
  python3 .claude/skills/tf/scripts/run_state.py verify <run-directory> S2 --files <file>[,<file>…]
        [--command "<command>"] [--timeout <s>]
  python3 .claude/skills/tf/scripts/run_state.py tick <katalog-przebiegu> S2
  python3 .claude/skills/tf/scripts/run_state.py park <run-directory> "<matter for a decision>"
  python3 .claude/skills/tf/scripts/run_state.py block <run-directory> S2 --question "<question for the human>"
  python3 .claude/skills/tf/scripts/run_state.py answer <run-directory> S2 "<answer>" --by human:<id>
  python3 .claude/skills/tf/scripts/run_state.py next <katalog-przebiegu>
  python3 .claude/skills/tf/scripts/run_state.py dashboard [--no-cost] [--out FILE]

`stage` sets the run's stage: intake, plan, slices, pr, needs, done. The `needs` stage requires `--needs plan` (the plan waits
for acceptance) or `--needs stop --code <code>` (a STOP block; the code from the closed list `STOP_CODES`, `--reason` is the reason
with evidence; without a code or with a code outside the list the command exits with code 2 and prints the list). `--auto` and `--plan`
record the task's mode (`tf task mode`): Plan ends the run at the plan, the normal (default) lets the slice loop in after
the human's consent to the plan (`approve`), Auto — without consent, unless the weight is full. `step` records the result of a loop step in the round
of the current slice: steps test, code, verify, scan, scope; states run, pass, fail. A round starts with the next attempt at the slice
after a failed gate (R1, R2). The script refuses a third round: the slice ends with a STOP block, and after the human's decision
(the `needs` stage) it gets two more. Steps earlier than the one being written that have no state or are running get pass —
the loop reports only what it starts and what it ends with. The first `step` moves the run from intake/plan to slices, and after
the human's decision (needs) it returns to slices. The target `PR` records the plan_drift and pr steps.

`spec <directory> new` creates the `spec.md` template (only when the loop starts the specification — after an early STOP
no empty file stays in the repository). `spec` checks the task's `spec.md` (`tf spec check`): AC-n criteria with Given / When / Then, the „Unchanged”
and „Out of scope” sections, no [blocking] questions. The `plan` stage (and every later one) is rejected while the specification has errors;
`stage plan` also records which files the plan was built from — a change of `spec.md` after the plan blocks the `pr` stage until
`stage plan` is called again.

`flag mode` says who handles flags: `auto` (default — the factory, after asking the human for a name) or `manual`
(`feature_flags.auto: false` in `.tf/config/config.yaml` — the human adds flags themselves, the loop does not create them).
`flag` records the story's feature flag (`tf task flag`) or an explicit reason for its absence; without it, or with a flag enabled
outside the test environment without the human's consent, the `pr` stage is rejected. The loop does not record consent for another environment.

`weight` shows the task's weight (light / normal / full) with the reason and consequences. The weight is assigned by `run_report.py start`
from the issue content, and the `intake` and `plan` stages repeat the assignment (`tf task weight --apply`: upward only, e.g. when the
plan touches migrations; they do not change the human's decisions); `weight --set <weight>` raises the weight, and only a human can lower it (`tf task weight … --by
human:<id>`). A light task does not need `spec.md`; a full task will not enter the slice loop
without a plan approved by a human.

`trace` prints the criterion → test → commit → evidence table (`tf trace --md`) for the PR description; a criterion without a test or
a test with an `AC-n` outside the specification is exit code 1 and a refusal of the `pr` stage.

`pr-body` assembles the PR description from the task files and writes it to `<run-directory>/pr-body.md`: the story, slices
with commits, the criteria trace, **How it was checked** (evidence, scan, plan_drift), **Risk** (weight and `tf risk`), **How to
roll back** (the operations card `deploy.rollback`, `git revert`, the flag), postponed matters and assumptions. A slice without
green evidence is named explicitly in the description. The script pushes nothing and creates no PR.

`panel` (full weight, step H11): the composition of the reviewer panel in separate contexts (`security-reviewer`, `spec-reviewer`)
with a ready assignment for each and the recorded verdicts; `--record` records a verdict in the task (`tf task review`).
The `pr` stage of a full-weight task requires a `pass` verdict from both for the current commit.

`finding` records in the task an important finding of the scope review (with the slice and round). `step … scope fail` is
rejected while the slice has no finding from this round — when the task is closed (`tf task close`) every important
finding must have a check that will catch it next time.

`verify` records a slice's evidence: it runs the verification command (by default the one from `.claude/quality-gate.json`) through
`tf task verify` and writes the result in `docs/project/changes/<KEY>/evidence/`. `tick` ticks off in plan.md only a slice
with current evidence, and the `pr` stage passes only when every slice of the task has it. The run's stage also goes
to `task.json` (intake → intake, plan → plan, slices → implementation, pr → pr). A run directory without a task in run.json
(the old cut layout `.tf/runs/cuts/`) does not accept task commands (`spec`, `flag`, `verify`, `trace`, `mode`, `weight`,
`approve`) — the command says how to start the cut anew.

`tick` ticks off a slice in plan.md, `park` appends a matter at the end of parked.md — one command from the allowed list
instead of `sed`, `>>` and a heredoc in the shell, which Claude Code asks the human about (measurement E0, 2026-11-13).

`block`, `answer` and `next` work with the `loop.blocked_slices` switch (`.tf/config/config.yaml`, off
by default): a question blocks only its own slice (`block`), the script says which slice can be done next (`Next: S3`
or `Next: STOP`, when none is independent), and `answer` records the human's answer and unblocks the slice.
Slice dependencies are recorded by the plan (`· after: S1`, `· after: none`; without a note — after the previous one), questions and answers —
the task's `events.jsonl` (one entry per line: `at`, `type` — `question`
or `answer`, `slice`, `text`, `by`; the file records decisions, it does not steer the run state). With the switch on, a STOP with the code `question` for the current slice
is rejected when an independent slice remains; a question about the whole task goes through with `--task`.

`proceed` works with the `loop.confirm_each_slice` switch (the `step-by-step` or `conversation` work style, `tf style`):
after `done` the run waits for the human's consent (`Next: STOP`), and `verify` and `step` of the next slice refuse until
`proceed` records the consent. In Auto mode the switch does not work — there is no human to give it.

`launch` (called by `run_report.py start`) builds the dashboard and opens it in the browser; you turn this off in
`.claude/tf.json`: {"dashboard": false} (entirely) or {"dashboard_open": false} (builds, but does not open);
both on by default. The variables TF_DASHBOARD=0 and TF_DASHBOARD_OPEN=0 do the same without the file.

`dashboard` builds a standalone file .tf/runs/dashboard.html from all runs in .tf/runs/<KEY>/ and cut runs
in .tf/runs/cuts/ (ignored by git along with the runs): columns by stage, cards with rounds, a file panel. It computes the cost and time from the transcripts
(run_report.py) and stores them in run.json; `stage` and `step` refresh the file without computing the cost. The task card
shows the stage from task.json and a slice bar; a ticked-off slice that lost its current evidence has a separate state (`stale`).
A task without a run (just `tf task`, a fresh clone without `.tf/runs/`) also gets a card. The file panel splits
files into the task directory (git), the working directory and evidence. A stage that nobody
recorded is derived from plan.md (slices ticked off and not) and report.md.
The state write serves the preview: an error of this script is not a reason for a run STOP.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_report  # noqa: E402
import ui_snap  # noqa: E402  (UI file patterns live there, in one place)

STAGES = ("intake", "plan", "slices", "pr", "needs", "done")
STEPS = ("test", "code", "verify", "scan", "scope")
STATES = ("run", "pass", "fail")
PR_STEPS = {"plan_drift": "drift", "pr": "pr"}
NEEDS = ("plan", "stop")
# A closed list of stop codes (`stage … needs --needs stop --code <code>`): code → what happened, in a plain sentence.
STOP_CODES = {
    "question": "information is missing, without which the work cannot start",
    "split": "the task is too big or combines several actions — it has to be split",
    "source": "there is no task content or no access to the issue",
    "plan-approval": "the plan waits for the human's consent",
    "tests": "the tests or the verification fail after two repair attempts",
    "scan": "the security scan blocks after two attempts",
    "budget": "the run's budget is exceeded",
    "environment": "the repository is not ready (uncommitted changes, no remote repository or a missing tool)",
    "dependency": "a new dependency or the version cooldown needs a decision",
    "contract": "a contract change or a business decision (a public API, a data schema, a migration)",
    "permissions": "an operation reserved for the human (production, publishing, a flag outside the test environment)",
}
TASK_STAGE = {"intake": "intake", "plan": "plan", "slices": "implementation", "pr": "pr"}   # the run's stage → the task's stage
TASK_ORDER = ("intake", "spec", "plan", "implementation", "review", "pr", "deploy", "closed")
BARE_STAGE = {"intake": "intake", "spec": "intake", "plan": "plan", "implementation": "slices",
              "review": "slices", "pr": "pr", "deploy": "done", "closed": "done"}   # a task without a run
PROOF_STATE = {"verified": "done", "red": "fail", "blocked": "fail", "planned": "todo"}
_TASK_API = None
SLICE = re.compile(r"^\s*- \[([ xX])\]\s+(S\d+)\s*[—-]\s*(.+)$")   # S<n> (K<n> from before 14.0.0: migrated in 19.0.0)
SLICE_ID = r"S\d+"
MAX_TEXT = 40000
MAX_RUNS = 40
MAX_ROUNDS = 2      # rounds of one slice without a human decision (the first attempt and one repair); then a STOP block
TEMPLATE = HERE.parent / "templates" / "dashboard.html"
MESSAGES = HERE.parent / "templates" / "stop_messages.json"   # stop messages for the human, one per code
CONFIG = Path(".claude") / "tf.json"         # preview options; a personal file, a factory update does not touch it
DEFAULTS = {"dashboard": True, "dashboard_open": True}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_run(run_dir: Path) -> dict:
    return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


def write_run(run_dir: Path, meta: dict) -> None:
    """Atomic write (a temporary file and a replace) — the preview never reads half a file."""
    meta["updated_at"] = now_iso()
    tmp = run_dir / "run.json.tmp"
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, run_dir / "run.json")


def fail(msg: str) -> int:
    print(f"✗ {msg}")
    return 2


def load(run_dir: Path) -> dict | None:
    try:
        return read_run(run_dir)
    except (OSError, ValueError):
        return None


# ---- task (task.json is written only by `tf task`) -------------------------------------------------------------------

def task_api(project: Path):
    """The engine's `task_state.py` as a module — reading task state without a subprocess for every card; None when it is not there."""
    global _TASK_API
    if _TASK_API is None:
        _TASK_API = False
        for base in (run_report.ROOT, project):
            f = base / ".tf" / "factory" / "task_state.py"
            if f.is_file():
                spec = importlib.util.spec_from_file_location("tf_task_state", f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _TASK_API = mod
                break
    return _TASK_API or None


def task_view(project: Path, key: str) -> dict | None:
    """The task and the computed states of its slices; None when there is no task or it cannot be read."""
    try:
        api = task_api(project)
        root = project.resolve()
        task = api.load(root, key) if api else None
        if not task:
            return None
        return {"task": task, "slices": {k: s for k, (s, _) in api.slice_states(root, task).items()}}
    except Exception:  # noqa: BLE001 — the preview never breaks the run
        return None


def task_field(run_dir: Path, meta: dict, name: str) -> str | None:
    """A task field from task.json (e.g. weight, mode); None when the run has no task."""
    try:
        return json.loads((run_report.docs_dir(run_dir, meta) / "task.json").read_text(encoding="utf-8")).get(name)
    except (OSError, ValueError, AttributeError):
        return None


def task_weight(run_dir: Path, meta: dict) -> str | None:
    """The task's weight (light / normal / full); None when the run has no task."""
    return task_field(run_dir, meta, "weight")


def sync_task(project: Path, run_dir: Path, meta: dict, stage: str) -> str | None:
    """Moves the run's stage to task.json (forward only). Returns a `tf task` refusal (a specification with errors,
    a slice without current evidence, a stale file) — it is a gate, not a preview error."""
    key, target = meta.get("key"), TASK_STAGE.get(stage)
    if not key or not target:
        return None
    try:
        cur = json.loads((run_report.docs_dir(run_dir, meta) / "task.json").read_text(encoding="utf-8")).get("stage")
    except (OSError, ValueError, AttributeError):
        cur = None
    if TASK_ORDER.index(target) >= TASK_ORDER.index("plan") and task_weight(run_dir, meta) != "light" \
            and not (run_report.docs_dir(run_dir, meta) / "spec.md").is_file():
        return (f"✗ the task {key} has no specification yet — create the template: run_state.py spec {run_dir} new, "
                f"fill it in and check it: run_state.py spec {run_dir}")
    if cur in TASK_ORDER and TASK_ORDER.index(target) <= TASK_ORDER.index(cur):
        return None
    r = run_report.task_state(project, "stage", key, target)
    if r is not None and r.returncode != 0:
        hint = (f"Flag: run_state.py flag {run_dir} set <key> or none --reason \"no flag, because …\" · "
                f"specification: run_state.py spec {run_dir} · slice evidence: run_state.py verify {run_dir} S<n> "
                f"--files <the slice's files> · the plan after a specification change: run_state.py stage {run_dir} plan")
        return ((r.stdout + r.stderr).strip() or f"✗ the task {key} did not move to the stage {target}") + "\n" + hint
    return None


def register_plan(project: Path, run_dir: Path, meta: dict) -> None:
    """Records in task.json which files the plan was built from (hashes of spec.md and ticket.md) — a change of the specification after
    the plan marks the plan as stale, which `tf task` detects, not the model."""
    docs = run_report.docs_dir(run_dir, meta)
    inputs = [n for n in ("spec.md", "ticket.md") if (docs / n).is_file()]
    if meta.get("key") and inputs and (docs / "plan.md").is_file():
        run_report.task_state(project, "artifact", meta["key"], "plan.md", "--stage", "plan", "--by", "process:tf",
                              "--inputs", ",".join(inputs))


def no_task(meta: dict) -> int:
    """A run directory without a task (the old cut layout `.tf/runs/cuts/`): task commands cannot be executed on it."""
    again = f"/tf {meta['task']}" + (f" --change {meta['change']}" if meta.get("change") else "") if meta.get("task") \
        else "/tf <TSK-n>"
    return fail(f"this run directory has the old layout (without a task) — start the cut again: {again}")


def cmd_flag(run_dir: Path, action: str, value: str | None, remove_by: str | None, reason: str, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if action == "mode":
        r = run_report.engine(project, "flag_check.py", meta["key"], "--json")
        try:
            auto = json.loads(r.stdout).get("auto", True)
        except (AttributeError, ValueError):
            auto = True
        print("auto — the factory runs the story's flag; ask the human for its name" if auto else
              "manual — the human adds flags themselves (feature_flags.auto: false); you do not create a flag or record it")
        return 0
    args = ["flag", meta["key"], action, *([value] if value else [])]
    if remove_by:
        args += ["--remove-by", remove_by]
    if reason:
        args += ["--reason", reason]
    r = run_report.task_state(project, *args)
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def stop_message(code: str | None) -> dict | None:
    """The stop message for the human (plain language): what, need, question, options, then. None when there is none."""
    try:
        msg = json.loads(MESSAGES.read_text(encoding="utf-8")).get(code or "")
    except (OSError, ValueError, AttributeError):
        return None
    return msg if isinstance(msg, dict) and isinstance(msg.get("opcje"), list) else None


def message_lines(msg: dict, reason: str | None = None) -> list[str]:
    lines = [f"What happened: {msg.get('co', '')}"] + ([f"Details: {reason.strip()}"] if reason and reason.strip() else [])
    lines += [f"What is needed: {msg.get('potrzeba', '')}", f"Question: {msg.get('question', '')}"]
    for n, o in enumerate(msg.get("opcje") or [], 1):
        lines.append(f"  {n}. {o.get('opcja', '')} — {o.get('skutek', '')}" + (" (recommended)" if o.get("rekomendowana") else ""))
    return lines + [f"Then: {msg.get('potem', '')}"]


def cmd_message(code: str, as_json: bool) -> int:
    msg = stop_message(code) if code in STOP_CODES else None
    if msg is None:
        return fail(f"there is no message for the code \"{code}\". Codes: {', '.join(STOP_CODES)}.")
    print(json.dumps({"code": code, **msg}, ensure_ascii=False, indent=1) if as_json else "\n".join(message_lines(msg)))
    return 0


def cmd_mode(run_dir: Path, new: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.task_state(project, "mode", meta["key"], *([new] if new else []))
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    if r.returncode == 0 and new:
        mode = task_field(run_dir, meta, "mode")
        meta["auto"], meta["plan_only"] = mode == "auto", mode == "plan"
        write_run(run_dir, meta)
        refresh(project)
    return r.returncode


def human_id(project: Path) -> str:
    """The human's identifier for recording consent: the name from git (a variable or the configuration), otherwise the system user."""
    name = os.environ.get("GIT_AUTHOR_NAME") or ""
    if not name:
        try:
            name = subprocess.run(["git", "config", "user.name"], cwd=project, capture_output=True, text=True,
                                  timeout=10).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            name = ""
    name = name or os.environ.get("USER") or os.environ.get("USERNAME") or "human"
    return "human:" + (run_report.slugify(name) or "human")


def cmd_approve(run_dir: Path, project: Path) -> int:
    """The human's consent to the plan (and the specification it was built from). In Auto mode there is no human — a refusal."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if task_field(run_dir, meta, "mode") == "auto":
        return fail("the run is in the Auto mode — there is no human to approve the plan. You record consent only "
                    "after the human's answer in the conversation; then first: run_state.py mode <directory> normal.")
    r = run_report.task_state(project, "approve", meta["key"], "plan.md", "--by", human_id(project))
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return 0 if r.returncode == 0 else 2


def cmd_weight(run_dir: Path, new: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.task_state(project, "weight", meta["key"], *(["--set", new] if new else ["--apply"]))
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def cmd_trace(run_dir: Path, base: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.engine(project, "trace_check.py", meta["key"], "--md", *(["--base", base] if base else []))
    if r is None:
        return fail("no .tf/factory/trace_check.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def cmd_spec(run_dir: Path, project: Path, new: bool = False) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    r = run_report.engine(project, "spec_check.py", "new" if new else "check", meta["key"])
    if r is None:
        return fail("no .tf/factory/spec_check.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


def slice_evidence(project: Path, meta: dict, slice_id: str) -> str:
    """The slice state computed by `tf task` (verified, unverified, red…); without an entry — no evidence."""
    r = run_report.task_state(project, "status", meta["key"], "--json")
    try:
        return json.loads(r.stdout).get("slice_states", {}).get(slice_id) or "no evidence"
    except (AttributeError, ValueError):
        return "the task's state is unreadable"


def cmd_verify(run_dir: Path, slice_id: str, files: str, command: str | None, timeout: float | None, project: Path,
               full: bool = False) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if hold_refusal(meta, slice_id, run_dir):
        return fail(hold_refusal(meta, slice_id, run_dir))
    args = ["verify", meta["key"], slice_id, "--files", files]
    if command:
        args += ["--command", command]
    if full:   # the whole `command` of the quality gate instead of its `related`
        args.append("--full")
    if timeout:
        args += ["--timeout", str(timeout)]
    r = run_report.task_state(project, *args)
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    for line in criterion_hints(project, run_dir, meta, files):
        print(line)
    refresh(project)
    return r.returncode


TEST_FILE = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                       r"(Test|Tests)\.(java|cs)$")          # the same patterns as in the criteria trace (trace_check.py)
CRITERION = re.compile(r"\bAC[-_ ]?\d+\b", re.I)


def criterion_hints(project: Path, run_dir: Path, meta: dict, files: str) -> list[str]:
    """Warnings when verifying a task slice with a specification: a test without a criterion identifier (`AC-n`) or
    no test file among the slice's files. Adding it now goes into the slice's commit, not a separate commit."""
    if not (run_report.docs_dir(run_dir, meta) / "spec.md").is_file():
        return []
    tests = [f.strip() for f in files.split(",") if f.strip() and TEST_FILE.search(f.strip())]
    if not tests:
        return ["⚠ there is no test file among the slice's files — add it to `--files`, otherwise the criterion will have no "
                "evidence in the trace (the pr stage will be rejected)"]
    bare = []
    for rel in tests:
        try:
            text = (project / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not CRITERION.search(text):
            bare.append(rel)
    if bare:
        return [f"⚠ a test without a criterion identifier: {', '.join(bare)} — add AC-n to the test's name or comment "
                "now, before the slice's commit (and repeat verify); adding it later is a separate commit"]
    return []


# ---- state write -------------------------------------------------------------------------------------------------

def cmd_stage(run_dir: Path, stage: str, needs: str | None, reason: str | None, pr: int | None, auto: bool,
              effort: str | None, project: Path, plan_mode: bool = False, code: str | None = None,
              whole_task: bool = False, visual: str | None = None) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if stage not in STAGES:
        return fail(f"the stage \"{stage}\" does not exist; allowed: {', '.join(STAGES)}.")
    if stage == "needs" and needs not in NEEDS:
        return fail("the needs stage requires `--needs plan` (the plan waits for acceptance) or `--needs stop` (a STOP block).")
    if stage != "needs" and (needs or reason or code):
        return fail("`--needs`, `--code` and `--reason` apply only to the needs stage.")
    if auto and plan_mode:
        return fail("give one mode: `--plan` (end at the plan) or `--auto` (without plan approval).")
    codes = "; ".join(f"{k} — {v}" for k, v in STOP_CODES.items())
    if stage == "needs" and needs == "stop" and code not in STOP_CODES:
        return fail(("a STOP block needs a code from the list" if not code else f"the stop code \"{code}\" does not exist")
                    + f": `--needs stop --code <code> --reason \"<the reason with evidence>\"`. Codes: {codes}.")
    if code and needs != "stop":
        return fail("`--code` applies only to `--needs stop`.")
    if code == "question" and not whole_task and meta.get("key") and blocked_slices_enabled(project):
        cur_k = (meta.get("current") or {}).get("k") if meta.get("stage") == "slices" else None
        slices, blocked = plan_and_blocked(project, run_dir, meta)
        open_cur = cur_k and cur_k not in blocked and any(s["id"] == cur_k and not s["checked"] for s in slices)
        other = next_slice(slices, blocked | {cur_k}) if open_cur else None
        if other:       # a question about one slice does not stop the whole when there is something to do next
            return fail(f"the question concerns the slice {cur_k}, and {other['id']} does not depend on it — block only {cur_k}: "
                        f"run_state.py block {run_dir} {cur_k} --question \"<question>\" and do {other['id']}. When the question "
                        "concerns the whole task, add `--task`.")
    if (auto or plan_mode) and meta.get("key"):               # the task's mode is chosen by the human in the /tf command
        m = run_report.task_state(project, "mode", meta["key"], "auto" if auto else "plan")
        if m is not None and "—" in m.stdout:                  # e.g. Auto at full weight: the normal mode stays
            print(m.stdout.strip())
    if stage in ("intake", "plan") and meta.get("key"):      # weight: a repeated assignment (upward only) after the content and the plan
        before = task_weight(run_dir, meta)
        w = run_report.task_state(project, "weight", meta["key"], "--apply")
        if w is not None and w.returncode == 0 and task_weight(run_dir, meta) != before:
            print("The task's weight changed — " + " ".join(ln.strip() for ln in w.stdout.splitlines()[:3] if ln.strip()))
    refused = sync_task(project, run_dir, meta, stage)
    if refused:
        print(refused)
        return 2
    if stage == "plan":
        register_plan(project, run_dir, meta)
    meta["stage"] = stage
    meta.pop("needs", None)
    meta.pop("stop_text", None)
    meta.pop("stop_code", None)
    meta.pop("needs_at", None)
    if stage == "needs":
        meta["needs"] = needs
        meta["needs_at"] = now_iso()                # since when the task has been waiting for the human (the "Waiting for you" list)
        if needs == "stop":
            meta["stop_code"] = code
            if reason:
                meta["stop_text"] = reason.strip()
    if pr is not None:
        meta["pr"] = pr
    if visual:                                      # the human's choice in the /tf command: on | off (`ui_snap.py worth` obeys it)
        meta["visual"] = visual
    if auto:
        meta["auto"] = True
    if plan_mode:
        meta["plan_only"] = True
    if effort:
        meta["effort"] = effort
    write_run(run_dir, meta)
    refresh(project)
    print(f"✓ stage: {stage}" + (f" ({needs})" if needs else ""))
    if stage == "plan" and meta.get("key") and blocked_slices_enabled(project):
        print("Slice dependencies: add `· after: S<n>` to the slice's row (after which it can start) or `· after: none` "
              "(independent); without it a slice depends on the previous one. That way a question in one slice does not "
              "stop the others.")
    msg = stop_message(code) if needs == "stop" else None
    if msg:     # a message for the human: the loop shows it instead of its own description
        print("A message for the human — show it with evidence (the command and the output); in a conversation ask the question with "
              "the AskUserQuestion tool with these options, in an unsupervised run write it into the report:")
        print("\n".join(message_lines(msg, reason)))
    return 0


def cmd_step(run_dir: Path, target: str, rest: list[str], project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if re.fullmatch(SLICE_ID, target) and hold_refusal(meta, target, run_dir):
        return fail(hold_refusal(meta, target, run_dir))
    if target.upper() == "PR":
        if len(rest) != 2 or rest[0] not in PR_STEPS or rest[1] not in STATES:
            return fail(f"usage: step <directory> PR <{'|'.join(PR_STEPS)}> <{'|'.join(STATES)}>")
        entering = meta.get("stage") in (None, "intake", "plan", "slices", "needs")
        refused = sync_task(project, run_dir, meta, "pr") if entering else None
        if refused:
            print(refused)
            return 2
        steps = meta.setdefault("pr_steps", {})
        steps[PR_STEPS[rest[0]]] = rest[1]
        if entering:
            meta["stage"] = "pr"
            meta.pop("needs", None)
            meta.pop("stop_text", None)
        write_run(run_dir, meta)
        refresh(project)
        print(f"✓ PR: {rest[0]} = {rest[1]}")
        return 0
    if not re.fullmatch(SLICE_ID, target) or len(rest) != 3 or not re.fullmatch(r"R[1-9]", rest[0]) \
            or rest[1] not in STEPS or rest[2] not in STATES:
        return fail(f"usage: step <directory> S<n> R<k> <{'|'.join(STEPS)}> <{'|'.join(STATES)}>")
    rnd, step, state = int(rest[0][1:]), rest[1], rest[2]
    cur = meta.get("current")
    if not isinstance(cur, dict) or cur.get("k") != target:
        cur = {"k": target, "rounds": []}      # a new slice: rounds count from R1
    rounds = cur.setdefault("rounds", [])
    limit = cur.get("limit") or MAX_ROUNDS
    if rnd > limit and meta.get("stage") == "needs":
        limit = cur["limit"] = len(rounds) + MAX_ROUNDS     # the human decided after STOP: further attempts
    if rnd > limit:                                         # the round limit is enforced by the script, not by the model's declaration
        return fail(f"{target} already had {limit} rounds — the next one starts only after the human's decision. Finish "
                    f"with a STOP block: run_state.py stage {run_dir} needs --needs stop --code <code> --reason \"<the reason "
                    "with evidence>\" (codes: tests — the verification is red, scan — the scan blocks, contract — a review "
                    "finding that cannot be removed within the slice's scope).")
    if step == "scope" and state == "fail" and meta.get("key") and not slice_finding(project, meta["key"], target, rnd):
        return fail(f"the scope review {target} R{rnd} failed, and the important finding is not recorded — first: "
                    f"run_state.py finding {run_dir} {target} \"<the [important] finding from the review>\" --round {rnd}, then "
                    "repeat this command. The record serves closing the task: every important finding gets a control, "
                    "which will catch it next time.")
    while len(rounds) < rnd:
        rounds.append({s: "todo" for s in STEPS})
    row = rounds[rnd - 1]
    for earlier in STEPS[:STEPS.index(step)]:
        if row.get(earlier, "todo") in ("todo", "run"):
            row[earlier] = "pass"             # the loop reports only the start and the end — the earlier ones passed
    row[step] = state
    for later in STEPS[STEPS.index(step) + 1:]:
        if state == "run" or row.get(later) not in STATES:
            row[later] = "todo"               # a new start of a step invalidates the states of the later ones
    meta["current"] = cur
    if meta.get("stage") in (None, "intake", "plan", "needs", "pr", "done"):
        refused = sync_task(project, run_dir, meta, "slices")
        if refused:
            print(refused)
            return 2
        meta["stage"] = "slices"
        for name in ("needs", "stop_text", "stop_code", "needs_at"):
            meta.pop(name, None)
    write_run(run_dir, meta)
    refresh(project)
    print(f"✓ {target} R{rnd}: {step} = {state}")
    return 0


def slice_finding(project: Path, key: str, slice_id: str, rnd: int) -> bool:
    """Whether the task has a recorded important scope-review finding for this slice and this round."""
    view = task_view(project, key)
    return any(isinstance(f, dict) and f.get("slice") == slice_id and f.get("round") == rnd
               for f in ((view or {}).get("task") or {}).get("findings") or [])


PANEL_BRIEFS = {
    "security-reviewer": "a security review of `git diff {base}...HEAD` (authentication, permissions, secrets, "
                         "user input, payments, migrations); the result: Critical / Important / To consider with file:line "
                         "and at the end `Verdict: PASS` (no critical or important ones) or `Verdict: FAIL`",
    "spec-reviewer": "verification of `{spec}` rule by rule against `git diff {base}...HEAD`: every AC-n criterion "
                     "(met / not met / cannot be checked, with file:line and the test) and every \"Unchanged\" rule "
                     "(kept / broken); at the end `Verdict: PASS` or `Verdict: FAIL`",
}


def cmd_panel(run_dir: Path, record: list[str] | None, note: str, base: str | None, project: Path) -> int:
    """The reviewer panel at full weight: composition, assignments, recorded verdicts and recording a new one (`--record`)."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if record:
        r = run_report.task_state(project, "review", meta["key"], record[0], record[1], "--note", note)
        if r is None:
            return fail("no .tf/factory/task_state.py — update the factory (tf update).")
        print((r.stdout + r.stderr).rstrip("\n"))
        return r.returncode
    weight = task_weight(run_dir, meta)
    if weight != "full":
        print(f"The task's weight: {WEIGHT_EN.get(weight, weight or '?')}. This task does not need the reviewer panel (it applies only "
              "to the full weight); the slices' scope review stays as usual.")
        return 0
    docs = run_report.docs_dir(run_dir, meta)
    try:
        spec = docs.resolve().relative_to(project.resolve()).joinpath("spec.md").as_posix()
    except ValueError:
        spec = str(docs / "spec.md")
    found = pick_base(project, base) or "<the default branch>"
    reviews = ((task_view(project, meta["key"]) or {}).get("task") or {}).get("reviews") or {}
    print(f"The reviewer panel (full weight): each in a separate context, through the Agent tool, before the pr stage.")
    for name, brief in PANEL_BRIEFS.items():
        done = reviews.get(name) if isinstance(reviews.get(name), dict) else None
        state = f"{done.get('verdict')}" + (f" — {as_data(done['note'], 200)}" if done.get("note") else "") if done else "no verdict"
        print(f"- {name}: {state}\n  commission: {brief.format(spec=spec, base=found)}\n  record: run_state.py panel {run_dir} "
              f"--record {name} pass|fail --note \"<the most important finding>\"")
    print("Verdict FAIL → a fix in a new commit, then the review again (the verdict concerns a commit).")
    return 0


def cmd_finding(run_dir: Path, slice_id: str, text: str, rnd: int | None, project: Path) -> int:
    """Records an important scope-review finding in the task (`tf task finding … add`), with the slice and round."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    cur = meta.get("current") if isinstance(meta.get("current"), dict) else {}
    rnd = rnd or (len(cur.get("rounds") or []) if cur.get("k") == slice_id else 0) or 1
    r = run_report.task_state(project, "finding", meta["key"], "add", text, "--slice", slice_id, "--round", str(rnd))
    if r is None:
        return fail("no .tf/factory/task_state.py — update the factory (tf update).")
    print((r.stdout + r.stderr).rstrip("\n"))
    return r.returncode


# ---- state read and dashboard ------------------------------------------------------------------------------------

def cmd_tick(run_dir: Path, slice_id: str, project: Path) -> int:
    """Ticks off a slice in plan.md (`- [ ] S<n>` → `- [x] S<n>`); a repeat changes nothing. A run with a task
    ticks off only a slice with current evidence (`verify`) and with a recorded, passed scope review (`step … scope
    pass`) — a measurement after step G: without this condition the review result was recorded in 7 of 15 runs."""
    meta = load(run_dir) or {}
    path = run_report.docs_dir(run_dir, meta) / "plan.md"
    if not path.is_file():
        return fail(f"{path} does not exist")
    lines = path.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        m = SLICE.match(line)
        if m and m.group(2) == slice_id and not m.group(3).lstrip().startswith("<"):   # not a template row
            if m.group(1) == " ":
                state = slice_evidence(project, meta, slice_id) if meta.get("key") else "verified"
                if state != "verified":
                    return fail(f"{slice_id} has no current evidence ({state}) — first: run_state.py verify "
                                f"{run_dir} {slice_id} --files <the slice's files>")
                refused = review_missing(run_dir, meta, slice_id) if meta.get("key") else None
                if refused:
                    return fail(refused)
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                path.write_text("\n".join(lines), encoding="utf-8")
            print(f"✓ {slice_id} ticked off in {path.name}")
            refresh(project)
            return 0
    return fail(f"{path.name} has no slice {slice_id}")


def review_missing(run_dir: Path, meta: dict, slice_id: str) -> str | None:
    """The reason for refusing to tick off, when the slice's last round has no passed scope review; None — there is one."""
    cur = meta.get("current") if isinstance(meta.get("current"), dict) else {}
    rounds = cur.get("rounds") if cur.get("k") == slice_id and isinstance(cur.get("rounds"), list) else []
    last = rounds[-1].get("scope") if rounds and isinstance(rounds[-1], dict) else None
    if last == "pass":
        return None
    k = len(rounds) or 1
    if last == "fail":
        return (f"{slice_id}: the scope review in R{k} failed — revert the [important] finding and do a new round: "
                f"run_state.py step {run_dir} {slice_id} R{k + 1} code run, and after scope-reviewer's new review "
                f"run_state.py step {run_dir} {slice_id} R{k + 1} scope pass")
    return (f"{slice_id}: there is no recorded result of the scope review (R{k}: {last or 'not recorded'}). After "
            f"scope-reviewer's review record it: run_state.py step {run_dir} {slice_id} R{k} scope pass — and with an "
            f"[important] finding: run_state.py finding {run_dir} {slice_id} \"<finding>\" and step … scope fail, then a new round")


CONVENTIONAL = re.compile(r"^[a-z]+(\([^()\s]+\))?!?: \S")
TRAILER = re.compile(r"^[\w-]+: \S")


def slice_files(project: Path, key: str, slice_id: str) -> list[str]:
    """Files from a slice's evidence (`verify --files`), in the order of recording; an empty list — there is no evidence."""
    view = task_view(project, key)
    sl = (((view or {}).get("task") or {}).get("slices") or {}).get(slice_id) or {}
    rel = sl.get("evidence") if isinstance(sl, dict) else None
    try:
        data = json.loads((project / run_report.CHANGES / key / rel).read_text(encoding="utf-8")) if rel else {}
    except (OSError, ValueError):
        return []
    files = data.get("files") if isinstance(data, dict) else None
    return [f for f in files if isinstance(f, str)] if isinstance(files, dict) else []


def commit_message(message: str, slice_id: str, value: str, footers: list[str]) -> str:
    """Title and body from `--message`; appends `Slice S<n>: <value>` and missing footers (the last paragraph)."""
    text = message.strip().replace("\r\n", "\n")
    if not re.search(rf"^Slice {re.escape(slice_id)}:", text, re.M):
        title, _, rest = text.partition("\n")
        text = f"{title}\n\nSlice {slice_id}: {value}" + (f"\n{rest.strip(chr(10))}" if rest.strip() else "")
    missing = [f for f in footers if not re.search(rf"^{re.escape(f.split(':', 1)[0])}:", text, re.M)]
    if not missing:
        return text + "\n"
    paras = text.split("\n\n")
    if len(paras) > 1 and all(TRAILER.match(ln) for ln in paras[-1].splitlines() if ln.strip()):
        return text + "\n" + "\n".join(missing) + "\n"
    return text + "\n\n" + "\n".join(missing) + "\n"


def cmd_done(run_dir: Path, slice_id: str, message: str, project: Path) -> int:
    """The end of a slice in one command: a passed scope review of the current round, a commit of the evidence files with the body
    and footers, ticking off and the next slice. A refusal before writing when there is no evidence or the title is bad."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if not re.fullmatch(SLICE_ID, slice_id):
        return fail("usage: done <directory> S<n> --message \"<type>(<scope>): <description>\"")
    if not CONVENTIONAL.match(message.strip()):
        return fail(f"the commit title is outside Conventional Commits: \"{message.strip().splitlines()[0] if message.strip() else ''}\" "
                    "— give --message \"<type>(<scope>): <description>\", e.g. feat(pay): add card payment")
    slices = plan_and_blocked(project, run_dir, meta)[0]
    entry = next((s for s in slices if s["id"] == slice_id), None)
    if entry is None:
        return fail(f"plan.md has no slice {slice_id}")
    state = slice_evidence(project, meta, slice_id)
    files = slice_files(project, meta["key"], slice_id)
    if state != "verified" or not files:
        return fail(f"{slice_id} has no current evidence ({state}) — first: run_state.py verify {run_dir} "
                    f"{slice_id} --files <the slice's files>; nothing was recorded")
    cur = meta.get("current") if isinstance(meta.get("current"), dict) else {}
    rnd = len(cur.get("rounds") or []) if cur.get("k") == slice_id else 0
    code = cmd_step(run_dir, slice_id, [f"R{rnd or 1}", "scope", "pass"], project)
    if code:
        return code
    meta = load(run_dir) or meta
    flag = task_field(run_dir, meta, "flag")
    flag_key = (flag.get("key") if isinstance(flag, dict) else None) or meta.get("flag")
    footers = ([f"Change: {meta['task']}"] if meta.get("task") else []) + ([f"Flag: {flag_key}"] if flag_key else [])
    try:
        add = subprocess.run(["git", "-C", str(project), "add", "--", *files], capture_output=True, text=True, timeout=60)
        staged = subprocess.run(["git", "-C", str(project), "diff", "--cached", "--quiet", "--", *files],
                                capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return fail(f"git does not respond ({e}) — the slice is not ticked off")
    if add.returncode != 0 or staged.returncode not in (0, 1):
        return fail(f"git add was rejected — the slice is not ticked off:\n{(add.stdout + add.stderr + staged.stderr).strip()}")
    if staged.returncode == 0:
        print(f"• the files of {slice_id} are already committed — no new commit")
    else:
        msg = commit_message(message, slice_id, entry["value"], footers)
        r = subprocess.run(["git", "-C", str(project), "commit", "-q", "-F", "-", "--", *files], input=msg,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return fail(f"the commit was rejected — the slice is not ticked off; fix it and repeat done:\n{(r.stdout + r.stderr).strip()}")
        sha = subprocess.run(["git", "-C", str(project), "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, timeout=30).stdout.strip()
        print(f"✓ commit {sha}: {msg.splitlines()[0]} ({', '.join(files)})")
    code = cmd_tick(run_dir, slice_id, project)
    if code:
        return code
    meta = load(run_dir) or meta
    rest = [s for s in plan_and_blocked(project, run_dir, meta)[0] if not s["checked"]]
    if rest and confirm_each_slice(project) and task_field(run_dir, meta, "mode") != "auto":
        meta["hold"] = slice_id
        write_run(run_dir, meta)
        nxt = rest[0]["id"]
        print(f"Next: STOP — the step-by-step style: show the human the changes of {slice_id} (git show --stat HEAD) and ask "
              f"with AskUserQuestion: \"Go on to {nxt} (Recommended)\" · \"Fix {slice_id} first\" · \"Stop here\". "
              f"After consent: run_state.py proceed {run_dir}")
        return 0
    print_next(project, run_dir, meta)
    return 0


def cmd_proceed(run_dir: Path, project: Path) -> int:
    """The human's consent to the next slice after a pause (the step-by-step style); without a pause — only `Next:`."""
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if meta.pop("hold", None):
        write_run(run_dir, meta)
        print("✓ the human's consent to the next slice")
    print_next(project, run_dir, meta)
    return 0


# ---- questions and slice dependencies (step F3, the loop.blocked_slices switch) ---------------------------------
NO_DEPS = ("none", "-", "—", "–")
HUMAN = re.compile(r"human:[\w.@-]+")


def loop_setting(project: Path, name: str) -> bool:
    """The `loop.<name>` switch after composing the configuration layers (engine ← company ← project ← person, packs.work_style);
    an older installation without work_style — engine and project; without configuration — off."""
    for base in (next((p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs.py").is_file()),
                      project), project):
        try:
            spec = importlib.util.spec_from_file_location("tf_packs_cfg", base / ".tf" / "factory" / "packs.py")
            packs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(packs)
            if hasattr(packs, "work_style"):
                return packs.work_style(project).get(name) is True
            cfg = packs.load_yaml(base / ".tf" / "factory" / "config.yaml")
            own = project / ".tf" / "config" / "config.yaml"
            if own.is_file():
                cfg = packs.deep_merge(cfg, packs.load_yaml(own))
            return (cfg.get("loop") or {}).get(name) is True
        except Exception:  # noqa: BLE001 — no configuration means the default setting, not a failure
            continue
    return False


def blocked_slices_enabled(project: Path) -> bool:
    """`loop.blocked_slices`: a question blocks only its own slice (the `autonomous` style)."""
    return loop_setting(project, "blocked_slices")


def confirm_each_slice(project: Path) -> bool:
    """`loop.confirm_each_slice`: after each slice the human's consent before the next (the `step-by-step`, `conversation` styles)."""
    return loop_setting(project, "confirm_each_slice")


def hold_refusal(meta: dict, slice_id: str, run_dir: Path) -> str | None:
    """A pause after a slice (step-by-step): another slice only after `proceed` — after the human's consent in the conversation."""
    held = meta.get("hold")
    if held and slice_id != held:
        return (f"the run waits for the human's consent after the slice {held} (the step-by-step style) — show the changes "
                f"(git show --stat HEAD), and after consent: run_state.py proceed {run_dir}")
    return None


def plan_with_deps(text: str) -> list[dict]:
    """The plan's slices in order: `id`, `checked`, `value` and `deps` — the list of slices after which one can start."""
    out: list[dict] = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m or m.group(3).lstrip().startswith("<"):      # a plan template row is not a slice
            continue
        parts = [p.strip() for p in m.group(3).split("·")]
        deps: list[str] | None = None
        for part in parts[1:]:
            k, _, v = part.partition(":")
            if k.strip().lower() == "after":
                names = [x.strip().strip("`") for x in v.split(",") if x.strip()]
                deps = [] if any(n.lower() in NO_DEPS for n in names) else [n.upper() for n in names if re.fullmatch(r"[Ss]\d+", n)]
        if deps is None:                                       # without a note: after the previous slice
            deps = [out[-1]["id"]] if out else []
        out.append({"id": m.group(2), "checked": m.group(1) != " ", "value": parts[0], "deps": deps})
    return out


def next_slice(slices: list[dict], blocked: set[str]) -> dict | None:
    """The first unticked and unblocked slice whose dependencies are all ticked."""
    done = {s["id"] for s in slices if s["checked"]}
    for s in slices:
        if not s["checked"] and s["id"] not in blocked and all(d in done for d in s["deps"]):
            return s
    return None


def held_slices(slices: list[dict], blocked: set[str]) -> list[tuple[str, list[str]]]:
    """Unticked slices that wait for others: (slice, unticked dependencies)."""
    done = {s["id"] for s in slices if s["checked"]}
    return [(s["id"], [d for d in s["deps"] if d not in done]) for s in slices
            if not s["checked"] and s["id"] not in blocked and any(d not in done for d in s["deps"])]


def append_event(task_dir: Path, kind: str, slice_id: str, text: str, by: str) -> dict:
    """Appends an entry to the task's events.jsonl and returns it."""
    event = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "type": kind, "slice": slice_id,
             "text": " ".join(text.split()), "by": by}
    with (task_dir / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def plan_and_blocked(project: Path, run_dir: Path, meta: dict) -> tuple[list[dict], set[str]]:
    """The plan's slices with dependencies and the set of slices blocked by a question (from task.json)."""
    try:
        text = (run_report.docs_dir(run_dir, meta) / "plan.md").read_text(encoding="utf-8")
    except OSError:
        text = ""
    view = task_view(project, meta["key"]) if meta.get("key") else None
    blocked = {k for k, s in (view["slices"] if view else {}).items() if s == "blocked"}
    return plan_with_deps(text), blocked


def print_next(project: Path, run_dir: Path, meta: dict) -> None:
    """`Next: S<n>` — a slice that can be done; `Next: STOP` — when every one waits for the human's answer."""
    slices, blocked = plan_and_blocked(project, run_dir, meta)
    nxt = next_slice(slices, blocked)
    if nxt:
        print(f"Next: {nxt['id']} — {nxt['value']}")
        return
    if not blocked:
        print("Next: finishing — all the plan's slices are ticked off." if slices and all(s["checked"] for s in slices)
              else "Next: no slice to do — check plan.md.")
        return
    view = task_view(project, meta["key"]) or {"task": {}}
    asked = {k: ((view["task"].get("slices") or {}).get(k) or {}).get("reason") or "(no question text)"
             for k in sorted(blocked, key=lambda x: int(x[1:]))}
    print("Next: STOP — every remaining slice waits for the human's answer.")
    for k, q in asked.items():
        print(f"  {k}: {q}")
    for k, deps in held_slices(slices, blocked):
        print(f"  {k} waits for {', '.join(deps)}")
    print(f"Finish with a STOP block: run_state.py stage {run_dir} needs --needs stop --code question --reason "
          f"\"{'; '.join(f'{k}: {q}' for k, q in asked.items())}\"")


def cmd_block(run_dir: Path, slice_id: str, question: str, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if not blocked_slices_enabled(project):
        return fail("the `loop.blocked_slices` switch is off (.tf/config/config.yaml) — a question ends the run "
                    f"with a STOP block: run_state.py stage {run_dir} needs --needs stop --code question --reason \"<question>\".")
    question = " ".join(question.split())
    slices, blocked = plan_and_blocked(project, run_dir, meta)
    found = next((s for s in slices if s["id"] == slice_id), None)
    if not question or found is None or found["checked"]:
        return fail(f"give a question and an unticked slice from plan.md (there are: {', '.join(s['id'] for s in slices) or 'none'}).")
    r = run_report.task_state(project, "slice", meta["key"], slice_id, "blocked", "--reason", question)
    if r is None or r.returncode != 0:
        return fail(((r.stdout + r.stderr).strip() if r else "no .tf/factory/task_state.py — update the factory (tf update)."))
    if slice_id not in blocked:
        append_event(run_report.docs_dir(run_dir, meta), "question", slice_id, question, "process:tf")
    refresh(project)
    print(f"✓ {slice_id} waits for the human's answer: {question}")
    print_next(project, run_dir, meta)
    return 0


def cmd_answer(run_dir: Path, slice_id: str, text: str, by: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    if not by or not HUMAN.fullmatch(by):
        return fail("you record an answer with the identifier of the human who gave it: --by human:<id>.")
    text = " ".join(text.split())
    _, blocked = plan_and_blocked(project, run_dir, meta)
    if not text or slice_id not in blocked:
        return fail(f"give an answer and a slice that waits for the human (waiting: {', '.join(sorted(blocked)) or 'none'}).")
    r = run_report.task_state(project, "slice", meta["key"], slice_id, "planned")
    if r is None or r.returncode != 0:
        return fail(((r.stdout + r.stderr).strip() if r else "no .tf/factory/task_state.py — update the factory (tf update)."))
    append_event(run_report.docs_dir(run_dir, meta), "answer", slice_id, text, by)
    if meta.get("stage") == "needs" and meta.get("stop_code") == "question" and blocked == {slice_id}:
        meta["stage"] = "slices"            # the last question has an answer: the run no longer waits for anyone
        for name in ("needs", "stop_text", "stop_code", "needs_at"):
            meta.pop(name, None)
        write_run(run_dir, meta)
    refresh(project)
    print(f"✓ {slice_id} unblocked — the answer is recorded ({by}).")
    print_next(project, run_dir, meta)
    return 0


def cmd_next(run_dir: Path, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    print_next(project, run_dir, meta)
    return 0


# --- the PR description assembled from the task files (step G2) -------------------------------------------------------------------
WEIGHT_EN = {"light": "light", "normal": "normal", "full": "full"}
CARD = Path(".tf") / "config" / "operations.json"
ASSUMPTION = re.compile(r"\[assumption", re.I)
BASES = ("origin/main", "main", "origin/master", "master")


def as_data(value, limit: int = 600) -> str:
    """Text from the task files and the operations card inserted into the PR description: one line without header and list characters at
    the start — the content is data, not the structure of the description. A `@name` mention goes into code (it notifies nobody),
    and an image becomes a plain link (the description fetches nothing from a foreign address)."""
    text = re.sub(r"^(?:[#>]+\s*|[-*+]\s+)+", "", " ".join(str(value).split()))
    text = re.sub(r"(?<![`\w])@([A-Za-z0-9][\w/-]*)", r"`@\1`", text.replace("![", "["))
    return text[:limit] + ("…" if len(text) > limit else "")


def code_span(value) -> str:
    text = " ".join(str(value).split())
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def pick_base(project: Path, base: str | None) -> str | None:
    """The base branch for the commit list: the given one, and without it the first existing of the typical ones; None when git does not know it."""
    for cand in ([base] if base else BASES):
        try:
            r = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "--quiet", f"{cand}^{{commit}}"],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode == 0:
            return cand
    return None


def slice_commits(project: Path, base: str) -> dict[str, str]:
    """A slice → the newest commit with the footer „Slice S<n>” on the branch (hash and title). Commits from before 19.0.0
    with the footer „Kawałek K<n>” are history and are not mapped."""
    try:
        r = subprocess.run(["git", "-C", str(project), "log", "--format=%h%x1f%s%x1f%b%x1e", f"{base}..HEAD"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, str] = {}
    for rec in (r.stdout.split("\x1e") if r.returncode == 0 else []):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) == 3:
            for k in re.findall(r"^Slice (S\d+)\b", parts[2], re.M):
                out.setdefault(k, f"{parts[0]} {parts[1]}")
    return out


def last_evidence(docs: Path) -> dict[str, tuple[str, dict]]:
    """A slice → (relative path, content) of the latest evidence `evidence/S<n>-<m>.json`."""
    best: dict[str, tuple[int, Path]] = {}
    for f in docs.glob("evidence/*-*.json"):
        m = re.fullmatch(r"(S\d+)-(\d+)\.json", f.name)
        if m and int(m.group(2)) >= best.get(m.group(1), (0, f))[0]:
            best[m.group(1)] = (int(m.group(2)), f)
    out = {}
    for k, (_, f) in best.items():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        out[k] = (f"evidence/{f.name}", data if isinstance(data, dict) else {})
    return out


def scan_status(run_dir: Path, slice_id: str) -> str | None:
    """The verdict of a slice's security scan (the last attempt); None when there was no scan or the result is unreadable."""
    base = run_dir / "security" / slice_id
    tries = sorted([*base.glob("attempt-*/verdict.json"), *base.glob("proba-*/verdict.json")],   # proba-: older runs
                   key=lambda f: int(re.sub(r"\D", "", f.parent.name) or 0))
    try:
        status = json.loads((tries[-1] if tries else base / "verdict.json").read_text(encoding="utf-8")).get("status")
    except (OSError, ValueError, AttributeError):
        return None
    return status if isinstance(status, str) and re.fullmatch(r"[A-Z]{2,12}", status) else None


def rollback_steps(project: Path) -> tuple[list[str], str]:
    """The deployment rollback steps from the operations card (`deploy.rollback`: text or a list) and the rollback time
    (`deploy.rollback_minutes`); without a card — an empty list and an empty text."""
    try:
        dep = json.loads((project / CARD).read_text(encoding="utf-8"))["deploy"]
        value, mins = dep["rollback"], dep.get("rollback_minutes")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return [], ""
    lines = value.splitlines() if isinstance(value, str) else value if isinstance(value, list) else []
    steps = [s for s in (as_data(x) for x in lines if isinstance(x, str)) if s][:10]
    try:
        timed = isinstance(mins, (int, float)) and not isinstance(mins, bool) and 0 < mins < 100000
        return steps, (f"about {float(mins):g} min" if steps and timed else "")
    except (OverflowError, ValueError):
        return steps, ""


def engine_md(project: Path, name: str, *args: str) -> str | None:
    """An engine script's output to paste under our own header: its headers become bold."""
    r = run_report.engine(project, name, *args)
    text = (r.stdout if r is not None else "").strip("\n")
    if r is None or not text:
        return None
    return "\n".join(f"**{ln.lstrip('# ').strip()}**" if ln.startswith("#") else ln for ln in text.splitlines())


# ---- the visual check: screenshots in <run>/screens/ (ui_snap.py), the agent's verdicts in screens/check.md ----------
VISUAL_RESULTS = ("identical", "changed", "only before", "only after")
VISUAL_SKIP = re.compile(r"^\s*(?:[-*]\s*)?Skipped:\s*(.+)$", re.I | re.M)
VISUAL_VERDICT = re.compile(r"\*\*(matches|does not match)\*\*", re.I)
VISUAL_REF = re.compile(r"(/[^\s@`]*)\s*@(\d+x\d+)")


def visual_check(run_dir: Path, docs: Path, project: Path, base: str | None | bool, rel_to: Path | None = None) -> dict | None:
    """The state of the visual check, or None = it does not exist for this task (backend work, a trivial UI touch, the
    human's --no-visual): no section, no dashboard block. Otherwise a dict: state `skipped` (with `reason`) | `done`
    (with `counts`, `mismatches`, `matches`, `items`, `dir`). `base`: the base branch; False = the plan only (no git)."""
    screens = run_dir / "screens"
    meta = load(run_dir) or {}
    if meta.get("visual") == "off":
        return None
    check_text = read_text(screens / "check.md") or ""
    compare_text = read_text(screens / "compare.md") or ""
    skip = VISUAL_SKIP.search(check_text)
    if skip:
        return {"state": "skipped", "reason": as_data(skip.group(1), 300)}
    if not compare_text:
        if base is False and not screens.is_dir():
            return None
        res = ui_snap.worth(run_dir, project, base)
        if not res["yes"]:
            return None
        return {"state": "skipped", "reason": "the change is worth a visual check (" + as_data("; ".join(res["reasons"]), 200)
                                              + ") but none was recorded (`screens/` is missing)"}
    rows = {}
    for ln in compare_text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[2] in VISUAL_RESULTS:
            rows[(cells[0], cells[1])] = cells[2]
    verdicts: dict[tuple, str] = {}
    matches = mismatches = 0
    for ln in check_text.splitlines():
        v = VISUAL_VERDICT.search(ln)
        if not v:
            continue
        bad = v.group(1).lower() != "matches"
        matches, mismatches = matches + (not bad), mismatches + bad
        for ref in VISUAL_REF.findall(ln):
            if bad or verdicts.get(ref) != "does not match":
                verdicts[ref] = "does not match" if bad else "matches"
    base_dir = os.path.relpath(run_dir.resolve(), (rel_to or project).resolve()).replace(os.sep, "/")
    items = []
    idx = {lb: ui_snap._load_index(run_dir, lb) for lb in ("before", "after")}
    for key in sorted(rows):
        b, a = idx["before"].get(key), idx["after"].get(key)
        items.append({"route": key[0], "viewport": key[1], "status": rows[key],
                      "before": f"{base_dir}/screens/before/{b['file']}" if b and "file" in b else None,
                      "after": f"{base_dir}/screens/after/{a['file']}" if a and "file" in a else None,
                      "verdict": verdicts.get(key, "not checked")})
    counts = {r: sum(1 for x in rows.values() if x == r) for r in VISUAL_RESULTS}
    return {"state": "done", "counts": counts, "matches": matches, "mismatches": mismatches, "items": items,
            "checked": bool(check_text.strip()), "dir": f"{base_dir}/screens"}


def visual_section(vis: dict | None, project: Path, run_dir: Path) -> list[str]:
    """The `## Visual check` section of the PR description."""
    if not vis:
        return []                      # no UI work worth a visual check: the section does not exist
    out = ["", "## Visual check", ""]
    if vis["state"] == "skipped":
        return out + [f"- skipped: {vis['reason']}"]
    try:
        shown = (run_dir / "screens").resolve().relative_to(project.resolve()).as_posix() + "/"
    except ValueError:
        shown = str(run_dir / "screens") + "/"
    c = vis["counts"]
    out.append(f"- screens compared: {sum(c.values())} — {c['identical']} identical, {c['changed']} changed, "
               f"{c['only before']} only before, {c['only after']} only after (screenshots: `{shown}`, outside git)")
    if not vis["checked"]:
        out.append("- **not checked**: `screens/check.md` is missing — the screenshots were not compared with the acceptance criteria")
    else:
        n = vis["mismatches"]
        out.append(f"- looked at against the criteria: {vis['matches']} match, {n} {'mismatch' if n == 1 else 'mismatches'}"
                   + (" — **red result**" if n else ""))
    return out


def pr_body(run_dir: Path, meta: dict, project: Path, base: str | None) -> tuple[str, list[str]]:
    """The PR description and the list of slices without green evidence."""
    key, docs = meta["key"], run_report.docs_dir(run_dir, meta)
    view = task_view(project, key) or {"task": {}, "slices": {}}
    task, states = view["task"], view["slices"]
    slices, proofs = parse_slices(run_dir), last_evidence(docs)
    found = pick_base(project, base)
    commits = slice_commits(project, found) if found else {}
    base_args = ["--base", found] if found else []

    ticket = read_text(docs / "ticket.md") or ""
    source = next((ln for ln in ticket.splitlines() if ln.startswith("Source:")), None)
    out = ["## Story", "", f"**{as_data(meta.get('title') or task.get('title') or key, 200)}** ({code_span(key)})", ""]
    if source:
        out.append(f"- {as_data(source, 300)}")
    if meta.get("change") or task.get("change"):
        out.append(f"- pdi change: {as_data(meta.get('change') or task.get('change'), 40)}"
                   + (f", cut {as_data(meta['task'], 40)}" if meta.get("task") else ""))
    try:
        rel_docs = docs.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        rel_docs = str(docs)
    out.append(f"- Task files: `{rel_docs}/` (issue, specification, plan, evidence)")

    out += ["", "## Slices", ""]
    for s in slices:
        out.append(f"- [{'x' if s['checked'] else ' '}] **{s['id']}** — {as_data(s['value'], 200)} · state: "
                   f"{states.get(s['id'], 'no entry in the task')} · commit: "
                   + (code_span(commits[s['id']]) if s['id'] in commits else "none"))
    if not slices:
        out.append("- no plan (`plan.md`)")
    if not found:
        out.append(f"- The slices' commits were not determined: git does not know the base branch {code_span(base or ', '.join(BASES))}.")

    out += ["", "## Criteria trace", ""]
    if (docs / "spec.md").is_file():
        out.append(engine_md(project, "trace_check.py", key, "--md", *base_args)
                   or "- The trace could not be computed (`tf trace`).")
    else:
        out.append("- The task has no specification (`spec.md`) — the light weight does not need one, so there is no criteria trace.")

    out += ["", "## How it was checked", ""]
    missing = []
    for s in slices:
        rel, ev = proofs.get(s["id"], (None, {}))
        scan = scan_status(run_dir, s["id"]) or "no result"
        if rel is None:
            line, why = "**no verification evidence**", "no evidence"
        else:
            code = ev.get("exit_code")
            green = code == 0
            why = None if green else f"red evidence, exit code {code}"
            line = (f"{'green' if green else '**red**'}: {code_span(ev.get('command') or '?')} (exit code {code}, "
                    f"{as_data(ev.get('at') or 'no date', 40)}, evidence `{rel}`)")
            state = states.get(s["id"])
            if green and state and state != "verified":
                line += f" — **evidence out of date** (state: {state})"
                why = f"evidence out of date, state: {state}"
        if why:
            missing.append(f"{s['id']} ({why})")
        out.append(f"- **{s['id']}** — {line} · security scan: {scan}")
    if not slices:
        out.append("- no slices in the plan, so there is no verification evidence")
    drift = (meta.get("pr_steps") or {}).get("drift")
    out += [f"- Agreement with the plan (`plan_drift`): {drift if drift in STATES else 'not recorded'}",
            f"- The evidence is in `{rel_docs}/evidence/` (in this PR); the full command output stays outside the repository."]

    out += visual_section(visual_check(run_dir, docs, project, found or None), project, run_dir)

    sysdiff = (engine_md(project, "system_diff.py", "--md", *base_args) or "").splitlines()
    out += ["", "## System diff", ""]
    out += [ln for ln in sysdiff if ln.strip() and not ln.startswith("**System diff")] or \
        ["- The system diff could not be computed (`system_diff.py`)."]
    out += ["", "## Risk", "", f"- The task's weight: {WEIGHT_EN.get(task.get('weight'), 'not recorded')}", ""]
    out.append(engine_md(project, "risk_triage.py", "--md", *base_args) or "- The risk triage could not be computed (`tf risk`).")

    flag = task.get("flag") if isinstance(task.get("flag"), dict) else {}
    steps = []
    if flag.get("key"):
        steps.append(f"Turn off the flag {code_span(flag['key'])} — the change stops working without a deployment.")
    card_steps, card_time = rollback_steps(project)
    steps += [f"{s} _(from the operations card `{CARD.as_posix()}`)_" for s in card_steps]
    steps.append("Code: `git revert <merge commit>` on the default branch, then an ordinary deployment.")
    out += ["", "## How to roll back", "", *(f"{i}. {s}" for i, s in enumerate(steps, 1)), ""]
    if not flag.get("key"):
        out.append(f"- Flag: none — {as_data(flag['none'], 300)}." if flag.get("none") else
                   "- Flag: not recorded in the task (a human may run the flags).")
    if card_time:
        out.append(f"- The rollback time according to the operations card: {card_time}.")
    if not card_steps:
        out.append(f"- The operations card (`{CARD.as_posix()}`, the `deploy.rollback` field) does not describe rolling back a "
                   "deployment — the default step above.")

    out += ["", "## Postponed for a decision", "", *([f"- {as_data(x, 400)}" for x in run_report.parked_items(run_dir)] or ["- none"])]
    notes = [as_data(ln, 400) for name in ("plan.md", "spec.md")
             for ln in (read_text(docs / name) or "").splitlines() if ASSUMPTION.search(ln)]
    out += ["", "## Assumptions", "", *([f"- {n}" for n in notes] or ["- no recorded assumptions"])]
    usage = meta.get("usage") if isinstance(meta.get("usage"), dict) else None
    if usage and isinstance(usage.get("cost_usd"), (int, float)):
        tok = usage.get("tokens") if isinstance(usage.get("tokens"), dict) else None
        out += ["", "## Run", "", f"- The cost so far: {usage['cost_usd']:.2f} USD (an estimate from the API price list), "
                f"time: {usage.get('minutes', '?')} min"
                + (f", tokens: {run_report.tokens_line(tok)}" if tok else "")
                + ". The full report: `report.md` in the task directory."]
    out += ["", "_The description was assembled by the `run_state.py pr-body` script from the task's files._"]
    return "\n".join(out) + "\n", missing


def cmd_pr_body(run_dir: Path, base: str | None, project: Path) -> int:
    meta = load(run_dir)
    if meta is None:
        return fail(f"missing or invalid {run_dir / 'run.json'} — `run_report.py start` creates the run.")
    if not meta.get("key"):
        return no_task(meta)
    try:
        update_usage(run_dir, meta, project)
    except Exception:  # noqa: BLE001 — the cost is an addition to the description
        pass
    text, missing = pr_body(run_dir, meta, project, base)
    target = run_dir / "pr-body.md"
    target.write_text(text, encoding="utf-8")
    try:
        shown = target.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        shown = str(target)
    print(f"✓ the PR description: {shown}\n  use: gh pr create --title \"<type>(<scope>): <description>\" --body-file {shown}\n"
          "  add your own remarks (deviations from the plan, an artifact budget exception) at the end of the file")
    if missing:
        print(f"⚠ without green evidence: {', '.join(missing)} — the description says so plainly")
    if not has_remote(project):
        print(f"⚠ the repository has no remote (git remote) — the branch cannot be pushed or a PR opened. Do not "
              f"try to push; finish with a STOP block: run_state.py stage {run_dir} needs --needs stop --code environment "
              "--reason \"no remote repository; the PR description is ready in pr-body.md\"")
    return 0


def has_remote(project: Path) -> bool:
    """Whether the repository has a remote configured; on a git error we assume it has (no false STOP)."""
    try:
        r = subprocess.run(["git", "-C", str(project), "remote"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return True
    return r.returncode != 0 or bool(r.stdout.strip())


def cmd_park(run_dir: Path, item: str, project: Path) -> int:
    """Appends a matter postponed for the human's decision at the end of parked.md (one row)."""
    item = " ".join(item.split())
    if not item:
        return fail("an empty item — give what you postpone and why")
    path = run_dir / "parked.md"
    if not run_dir.is_dir():
        return fail(f"the run directory {run_dir} does not exist")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(text.rstrip("\n") + ("\n" if text.strip() else "") + f"- {item.lstrip('- ')}\n", encoding="utf-8")
    print(f"✓ postponed for a decision in {path.name}")
    refresh(project)
    return 0


def parse_slices(run_dir: Path) -> list[dict]:
    path = run_report.docs_dir(run_dir) / "plan.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out = []
    for line in text.splitlines():
        m = SLICE.match(line)
        if not m:
            continue
        value = m.group(3).split(" · ")[0].strip()
        if value.startswith("<"):               # a row from the plan.md template, not yet a plan
            continue
        out.append({"id": m.group(2), "value": value, "checked": m.group(1) in "xX"})
    return out


def infer_stage(meta: dict, run_dir: Path, slices: list[dict]) -> str:
    if meta.get("stage") in STAGES:
        return meta["stage"]
    if (run_report.docs_dir(run_dir, meta) / "report.md").is_file():
        return "done"
    if not slices:
        return "intake"
    if all(s["checked"] for s in slices):
        return "pr"
    if any(s["checked"] for s in slices) or meta.get("current"):
        return "slices"
    return "plan"


def clip(text: str) -> str:
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + "\n…(cut)"


def read_text(path: Path) -> str | None:
    try:
        return clip(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None


def dot_for(text: str) -> str:
    if re.search(r"\bFAIL\b", text):
        return "bad"
    return "ok" if re.search(r"\bPASS\b", text) else "warn"


def evidence_items(docs: Path) -> list[dict]:
    """The latest evidence of every slice (evidence/S<n>-<m>.json): a green dot when the exit code is 0."""
    last: dict[int, tuple[int, Path]] = {}
    for f in docs.glob("evidence/*-*.json"):
        m = re.fullmatch(r"S(\d+)-(\d+)\.json", f.name)
        if m and int(m.group(2)) >= last.get(int(m.group(1)), (0, f))[0]:
            last[int(m.group(1))] = (int(m.group(2)), f)
    out = []
    for _, (_, f) in sorted(last.items()):
        text = read_text(f)
        if text is None:
            continue
        try:
            ok = json.loads(text).get("exit_code") == 0
        except (ValueError, AttributeError):
            ok = False
        out.append({"name": f"evidence/{f.name}", "dot": "ok" if ok else "bad", "text": text})
    return out


def code_items(run_dir: Path, proofs: list[dict]) -> list[dict]:
    """The code files of every slice — from the last verification evidence, so also those the agent did not mention."""
    project, out = run_dir.resolve().parents[2], []
    for proof in proofs:
        m = re.match(r"evidence/(S\d+)-", proof["name"])
        try:
            files = json.loads(proof["text"]).get("files") or {}
        except (ValueError, AttributeError):
            files = {}
        for rel in sorted(files) if m else []:
            text = read_text(project / rel)
            out.append({"name": f"{m.group(1)} · {rel}", "dot": "ok" if text is not None else "warn",
                        "text": text if text is not None else "(the file no longer exists)"})
    return out


def file_groups(run_dir: Path, meta: dict, stage: str, needs: str | None, parked: list[str]) -> list[dict]:
    groups: list[dict] = []
    main, work = [], []
    task_dir = meta.get("task_dir")
    docs = run_report.docs_dir(run_dir, meta)       # the new layout: the story, plan and report in the task directory
    for path in (run_report.story_file(run_dir, meta), docs / "spec.md", docs / "plan.md", docs / "events.jsonl",
                 run_dir / "parked.md"):
        name, text = path.name, read_text(path)
        if text is None:
            continue
        dot = "ok"
        if name == "plan.md":
            dot = "warn" if stage == "needs" and needs == "plan" else "ok"
        if name == "parked.md":
            dot = "warn" if parked else ""
        (work if task_dir and name == "parked.md" else main).append({"name": name, "dot": dot, "text": text})
    if main:
        groups.append({"grp": f"Task (git) · {task_dir}/" if task_dir else "Run", "items": main})
    if work:
        groups.append({"grp": f"Working · .tf/runs/{meta.get('key')}/", "items": work})
    proofs = evidence_items(docs) if task_dir else []
    if proofs:
        groups.append({"grp": "Evidence", "items": proofs})
    code = code_items(run_dir, proofs) if task_dir else []
    if code:
        groups.append({"grp": "The slices' code (files from the evidence)", "items": code})
    sec_root = run_dir / "security"
    sec = []
    for f in sorted(sec_root.glob("**/summary.md")) if sec_root.is_dir() else []:
        text = read_text(f)
        if text is not None:
            sec.append({"name": f"security/{f.parent.relative_to(sec_root).as_posix()}/summary.md".replace("//", "/"),
                        "dot": dot_for(text), "text": text})
    if sec:
        groups.append({"grp": "Security", "items": sec})
    result = []
    if stage == "needs" and needs == "stop":
        cur = (meta.get("current") or {}).get("k")
        result.append({"name": "STOP", "dot": "bad", "text": "\n".join(
            [f"Stopped — {cur or 'the run'}"]
            + (message_lines(stop_message(meta.get("stop_code")), meta.get("stop_text"))
               if stop_message(meta.get("stop_code")) else [f"Reason: {meta.get('stop_text') or '(no description)'}"])
            + [
             f"Resume: from {cur or 'the place where the factory stopped'}"])})
    report = read_text(docs / "report.md")
    if report is not None:
        result.append({"name": "report.md", "dot": "ok", "text": report})
    if result:
        groups.append({"grp": "Result", "items": result})
    if not groups:
        groups.append({"grp": "Run", "items": [{"name": "run.json", "dot": "",
                                                       "text": json.dumps(meta, ensure_ascii=False, indent=1)}]})
    return groups


def normalize_rounds(cur: dict) -> list[dict]:
    rounds = []
    for r in cur.get("rounds") or []:
        rounds.append({s: (r.get(s) if r.get(s) in STATES else "todo") for s in STEPS})
    return rounds


def update_usage(run_dir: Path, meta: dict, project: Path) -> None:
    """Cost, time and models from the transcripts (run_report.collect), stored in run.json (`usage`). A finished run
    with an already computed cost is not computed again. Missing transcripts are not an error — the card will not show the cost."""
    if meta.get("stage") == "done" and isinstance(meta.get("usage"), dict) and "tokens" in meta["usage"]:
        return
    since = run_report.parse_ts(meta.get("started_at", ""))
    if since is None:
        return
    try:
        data = run_report.collect(project, since, None)
    except OSError:
        return
    if not data or not data.get("requests"):
        return
    models = data["models"]
    meta["usage"] = {"cost_usd": round(sum(t.get("_cost", 0.0) for t in models.values()), 4),
                     "minutes": max(0, round((data["last"] - since).total_seconds() / 60)),
                     "tokens": run_report.token_totals(models), "requests": data["requests"],
                     "models": sorted(models), "at": now_iso()}
    write_run(run_dir, meta)


def run_object(run_dir: Path, project: Path, costs: bool, rel_to: Path | None = None) -> dict | None:
    meta = load(run_dir)
    if meta is None:
        return None
    if costs:
        update_usage(run_dir, meta, project)
    slices = parse_slices(run_dir)
    stage = infer_stage(meta, run_dir, slices)
    needs = meta.get("needs") if stage == "needs" else None
    cur = meta.get("current") if isinstance(meta.get("current"), dict) else None
    view = task_view(project, meta["key"]) if meta.get("key") else None
    out_slices = slice_items(slices, view, cur, stage, needs)
    parked = [ln[2:].strip() for ln in run_report.parked_items(run_dir)]
    m = re.match(r"(\d{4}-\d{2}-\d{2})-", run_dir.name)
    usage = meta.get("usage") if isinstance(meta.get("usage"), dict) else {}
    pr_steps = meta.get("pr_steps") or {}
    obj = {"slug": meta.get("slug") or run_dir.name, "title": meta.get("title") or run_dir.name,
           "date": m.group(1) if m else str(meta.get("started_at", ""))[:10],
           "stage": stage, "needs": needs, "auto": bool(meta.get("auto")), "effort": meta.get("effort"),
           "key": meta.get("task") or meta.get("key"), "change": meta.get("change"), "flag": meta.get("flag"), "pr": meta.get("pr"),
           "stopText": meta.get("stop_text"), "stopCode": meta.get("stop_code"),
           "stopLabel": (stop_message(meta.get("stop_code")) or {}).get("co") or STOP_CODES.get(meta.get("stop_code") or ""),
           "stopHint": stop_hint(meta, cur) if needs == "stop" else None,
           "stopNeed": (stop_message(meta.get("stop_code")) or {}).get("potrzeba"),
           "stopQuestion": (stop_message(meta.get("stop_code")) or {}).get("question"),
           "stopOptions": [{"opcja": o.get("opcja"), "skutek": o.get("skutek"), "rekomendowana": bool(o.get("rekomendowana"))}
                           for o in (stop_message(meta.get("stop_code")) or {}).get("opcje") or []],
           "slices": out_slices, "parked": len(parked), "parkedList": parked,
           "cost": usage.get("cost_usd"), "min": usage.get("minutes"), "models": usage.get("models") or [],
           "tokens": usage.get("tokens") if isinstance(usage.get("tokens"), dict) else None,
           "started": meta.get("started_at", ""),
           "dir": run_dir.resolve().relative_to(project.resolve()).as_posix()
           if run_dir.resolve().is_relative_to(project.resolve()) else str(run_dir),
           "taskDir": meta.get("task_dir"), "taskStage": view["task"].get("stage") if view else None,
           "waiting": waiting_items(project, view)}
    if cur and stage in ("slices", "needs"):
        obj["cur"] = {"k": cur.get("k"), "rounds": normalize_rounds(cur) or [{s: "todo" for s in STEPS}]}
    if stage == "pr":
        obj["prSteps"] = {"drift": pr_steps.get("drift", "todo"), "pr": pr_steps.get("pr", "todo")}
    obj["files"] = file_groups(run_dir, meta, stage, needs, parked)
    if (run_dir / "screens").is_dir():     # the visual check: relative paths to the screenshots (from the dashboard file)
        vis = visual_check(run_dir, run_report.docs_dir(run_dir, meta), project, False, rel_to or project / run_report.WORK)
        if vis:
            obj["visual"] = vis
    return obj


def sentence(text: str | None, capital: bool = False) -> str:
    """Text ending with a single period (without „..”), capitalized on request; empty stays empty."""
    s = (text or "").strip()
    if not s:
        return s
    return (s[0].upper() + s[1:] if capital else s) + ("" if s[-1] in ".!?…" else ".")


def stop_hint(meta: dict, cur: dict | None) -> str:
    """The stop description on the card: what happened, the reason from the run and what to do — each part in a separate sentence."""
    label = (stop_message(meta.get("stop_code")) or {}).get("co") or STOP_CODES.get(meta.get("stop_code") or "")
    resume = (cur or {}).get("k") or "the current slice"
    return " ".join(x for x in (sentence(label, capital=True), sentence(meta.get("stop_text") or "STOP"),
                                f"Decide and write in the session: resume from {resume}") if x)


def waiting_items(project: Path, view: dict | None) -> list[dict]:
    """What the task waits for from the human — the same list as in `tf status` (`task_state.waiting`)."""
    try:
        api = task_api(project)
        return api.waiting(project.resolve(), view["task"]) if api and view and hasattr(api, "waiting") else []
    except Exception:  # noqa: BLE001 — the preview never breaks the run
        return []


def slice_items(slices: list[dict], view: dict | None, cur: dict | None, stage: str, needs: str | None) -> list[dict]:
    """The state of the plan's slices on the card. With a task (`view`) a ticked-off slice without current evidence has the state `stale`,
    and every slice carries `proof` — the state computed by `tf task`."""
    out = []
    first_open = next((s["id"] for s in slices if not s["checked"]), None)
    for s in slices:
        proof = (view["slices"].get(s["id"]) or "no evidence") if view else None
        if s["checked"]:
            state = "stale" if view and proof != "verified" else "done"
        elif cur and cur.get("k") == s["id"]:
            state = "fail" if stage == "needs" and needs == "stop" else "cur"
        elif not cur and stage == "slices" and s["id"] == first_open:
            state = "cur"
        else:
            state = "todo"
        item = {"id": s["id"], "value": s["value"], "state": state}
        if view:
            item["proof"] = proof
        out.append(item)
    return out


def task_object(task_dir: Path, project: Path) -> dict | None:
    """A card of a task that has no run in `.tf/runs/` (just `tf task` or a fresh clone): the stage from task.json,
    the slices from plan.md, and without a plan — from the task itself."""
    key = task_dir.name
    view = task_view(project, key)
    if view is None:
        return None
    task = view["task"]
    stage = BARE_STAGE.get(task.get("stage"), "intake")
    rel = task_dir.resolve().relative_to(project.resolve()).as_posix()
    meta = {"key": key, "task_dir": rel}
    plan = parse_slices(task_dir)
    if plan:
        slices = slice_items(plan, view, None, stage, None)
    else:
        slices = [{"id": k, "value": (task.get("slices", {}).get(k) or {}).get("title") or "", "proof": s,
                   "state": PROOF_STATE.get(s, "stale")} for k, s in view["slices"].items()]
    work = project / run_report.WORK / key          # may not exist — then the panel shows only the task directory
    files = file_groups(work, meta, stage, None, [])
    if not any(g["grp"] != "Dowody" for g in files):
        files.insert(0, {"grp": f"Task (git) · {rel}/", "items": [
            {"name": "task.json", "dot": "", "text": json.dumps(task, ensure_ascii=False, indent=1)}]})
    created = str(task.get("created", ""))
    obj = {"slug": key, "title": task.get("title") or key, "date": created[:10], "stage": stage, "needs": None,
           "auto": False, "effort": None, "key": key, "change": None, "flag": None, "pr": None, "stopText": None,
           "slices": slices, "parked": 0, "parkedList": [], "cost": None, "min": None, "models": [],
           "waiting": waiting_items(project, view),
           "started": created, "dir": None, "taskDir": rel, "taskStage": task.get("stage"), "files": files}
    if stage == "pr":
        obj["prSteps"] = {"drift": "todo", "pr": "todo"}
    return obj


def build_dashboard(project: Path, out: Path | None = None, costs: bool = True) -> Path:
    root = project / run_report.RUNS                # the old cut layout (no longer created): the history stays in the preview
    work = project / run_report.WORK                # the tasks' working directories: .tf/runs/<KEY>/
    runs = []
    target = out or (work / "dashboard.html")
    for d in sorted({*root.glob("*/run.json"), *work.glob("*/run.json")}):
        obj = run_object(d.parent, project, costs, target.parent)
        if obj:
            runs.append(obj)
    seen = {r["key"] for r in runs}
    for f in sorted((project / run_report.CHANGES).glob("*/task.json")):   # tasks without a run in .tf/runs/
        obj = task_object(f.parent, project) if f.parent.name not in seen else None
        if obj:
            runs.append(obj)
    runs.sort(key=lambda r: (r["date"], r["started"]), reverse=True)
    html = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(runs[:MAX_RUNS], ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*RUNS_JSON*/[]", data, 1).replace("/*GENERATED*/", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    os.replace(tmp, target)
    return target


def options(project: Path) -> dict:
    """Options from `.claude/tf.json` (no file or key = on by default); the variables TF_DASHBOARD=0
    and TF_DASHBOARD_OPEN=0 turn the option off without editing the file."""
    opts = dict(DEFAULTS)
    try:
        data = json.loads((project / CONFIG).read_text(encoding="utf-8"))
        opts.update({k: bool(v) for k, v in data.items() if k in DEFAULTS})
    except (OSError, ValueError, AttributeError):
        pass
    for key, env in (("dashboard", "TF_DASHBOARD"), ("dashboard_open", "TF_DASHBOARD_OPEN")):
        if os.environ.get(env, "").strip().lower() in ("0", "false", "no", "off"):
            opts[key] = False
    if os.environ.get("CI"):          # CI and tests: without opening the browser
        opts["dashboard_open"] = False
    return opts


def open_file(path: Path) -> str | None:
    """Opens a local file in the default browser: Windows `os.startfile` (a native path — `webbrowser` with a file:// address
    can do nothing there without a message), macOS `open`, otherwise `webbrowser`. None = opened, else the reason it was not."""
    try:
        if os.name == "nt":
            os.startfile(str(path.resolve()))  # type: ignore[attr-defined]  # noqa: S606 — a local file, no shell
            return None
        if sys.platform == "darwin":
            r = subprocess.run(["open", str(path.resolve())], capture_output=True, text=True)
            return None if r.returncode == 0 else (r.stderr.strip() or f"open: exit code {r.returncode}")
        return None if webbrowser.open(path.resolve().as_uri()) else "no browser found (a cloud or SSH session)"
    except Exception as e:  # noqa: BLE001 — no browser is not an error of the run
        return str(e) or type(e).__name__


def launch(project: Path, open_browser: bool = True) -> str | None:
    """Run start: build the dashboard and (when the options and `open_browser` allow) open it in the browser.
    Returns the file's address or None when the dashboard is off. An error never interrupts the run."""
    opts = options(project)
    if not opts["dashboard"]:
        return None
    try:
        path = build_dashboard(project, costs=False).resolve()
        uri = path.as_uri()
    except Exception:  # noqa: BLE001 — the preview never breaks the run
        return None
    if open_browser and opts["dashboard_open"]:
        why = open_file(path)
        if why:
            print(f"⚠ The dashboard did not open ({why}) — open it with `tf status --open` or the address below.",
                  file=sys.stderr)
    elif open_browser and os.environ.get("CI"):
        print("ℹ The dashboard does not open by itself: the CI variable is set.", file=sys.stderr)
    return uri


def refresh(project: Path) -> None:
    """Refreshing the preview after a state write; without computing the cost, without interrupting the run on an error."""
    try:
        build_dashboard(project, costs=False)
    except Exception:  # noqa: BLE001 — the preview never breaks the run
        pass


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage")
    s.add_argument("run_dir")
    s.add_argument("stage")
    s.add_argument("--needs", default=None)
    s.add_argument("--reason", default=None)
    s.add_argument("--pr", type=int, default=None)
    s.add_argument("--auto", action="store_true")
    s.add_argument("--plan", dest="plan_mode", action="store_true")
    s.add_argument("--visual", dest="visual", action="store_const", const="on", default=None,
                   help="force the visual check (screenshots before/after), recorded in run.json")
    s.add_argument("--no-visual", dest="visual", action="store_const", const="off",
                   help="no visual check, even for a UI change")
    s.add_argument("--code", default=None)
    s.add_argument("--task", dest="whole_task", action="store_true",
                   help="the question concerns the whole task, not one slice (with the loop.blocked_slices switch)")
    s.add_argument("--effort", default=None, choices=["low", "medium", "high", "xhigh", "max"])
    t = sub.add_parser("step")
    t.add_argument("run_dir")
    t.add_argument("target")
    t.add_argument("rest", nargs="*")
    sp = sub.add_parser("spec")
    sp.add_argument("run_dir")
    sp.add_argument("action", nargs="?", choices=["new"])
    fg = sub.add_parser("flag")
    fg.add_argument("run_dir")
    fg.add_argument("action", choices=["mode", "set", "none"])      # consent to another environment is recorded by the human: tf task flag … allow
    fg.add_argument("value", nargs="?")
    fg.add_argument("--remove-by", default=None)
    fg.add_argument("--reason", default="")
    ms = sub.add_parser("message")
    ms.add_argument("code")
    ms.add_argument("--json", action="store_true")
    mo = sub.add_parser("mode")
    mo.add_argument("run_dir")
    mo.add_argument("new", nargs="?")
    apv = sub.add_parser("approve")
    apv.add_argument("run_dir")
    wg = sub.add_parser("weight")
    wg.add_argument("run_dir")
    wg.add_argument("--set", dest="new", default=None)      # lowering is recorded by the human: tf task weight … --by human:<id>
    tr = sub.add_parser("trace")
    tr.add_argument("run_dir")
    tr.add_argument("--base", default=None)
    v = sub.add_parser("verify")
    v.add_argument("run_dir")
    v.add_argument("slice_id")
    v.add_argument("--files", default="")
    v.add_argument("--command", default=None)
    v.add_argument("--timeout", type=float, default=None)
    v.add_argument("--full", action="store_true")
    dn = sub.add_parser("done")
    dn.add_argument("run_dir")
    dn.add_argument("slice_id")
    dn.add_argument("--message", required=True)
    k = sub.add_parser("tick")
    k.add_argument("run_dir")
    k.add_argument("slice_id")
    p = sub.add_parser("park")
    p.add_argument("run_dir")
    p.add_argument("item")
    bl = sub.add_parser("block")
    bl.add_argument("run_dir")
    bl.add_argument("slice_id")
    bl.add_argument("--question", required=True)
    an = sub.add_parser("answer")
    an.add_argument("run_dir")
    an.add_argument("slice_id")
    an.add_argument("text")
    an.add_argument("--by", default=None)
    nx = sub.add_parser("next")
    nx.add_argument("run_dir")
    pc = sub.add_parser("proceed")
    pc.add_argument("run_dir")
    pn = sub.add_parser("panel")
    pn.add_argument("run_dir")
    pn.add_argument("--record", nargs=2, metavar=("REVIEWER", "VERDICT"), default=None)
    pn.add_argument("--note", default="")
    pn.add_argument("--base", default=None)
    fd = sub.add_parser("finding")
    fd.add_argument("run_dir")
    fd.add_argument("slice_id")
    fd.add_argument("text")
    fd.add_argument("--round", type=int, default=None)
    pb = sub.add_parser("pr-body")
    pb.add_argument("run_dir")
    pb.add_argument("--base", default=None)
    d = sub.add_parser("dashboard")
    d.add_argument("--no-cost", action="store_true")
    d.add_argument("--out", default=None)
    d.add_argument("--open", action="store_true", help="open the file in a browser")
    args = ap.parse_args(argv[1:])
    project = Path.cwd()
    if args.cmd == "stage":
        return cmd_stage(Path(args.run_dir), args.stage, args.needs, args.reason, args.pr, args.auto, args.effort,
                         project, plan_mode=args.plan_mode, code=args.code, whole_task=args.whole_task, visual=args.visual)
    if args.cmd == "step":
        return cmd_step(Path(args.run_dir), args.target, args.rest, project)
    if args.cmd == "flag":
        return cmd_flag(Path(args.run_dir), args.action, args.value, args.remove_by, args.reason, project)
    if args.cmd == "weight":
        return cmd_weight(Path(args.run_dir), args.new, project)
    if args.cmd == "message":
        return cmd_message(args.code, args.json)
    if args.cmd == "mode":
        return cmd_mode(Path(args.run_dir), args.new, project)
    if args.cmd == "approve":
        return cmd_approve(Path(args.run_dir), project)
    if args.cmd == "trace":
        return cmd_trace(Path(args.run_dir), args.base, project)
    if args.cmd == "spec":
        return cmd_spec(Path(args.run_dir), project, new=args.action == "new")
    if args.cmd == "verify":
        return cmd_verify(Path(args.run_dir), args.slice_id, args.files, args.command, args.timeout, project, args.full)
    if args.cmd == "done":
        return cmd_done(Path(args.run_dir), args.slice_id, args.message, project)
    if args.cmd == "tick":
        return cmd_tick(Path(args.run_dir), args.slice_id, project)
    if args.cmd == "park":
        return cmd_park(Path(args.run_dir), args.item, project)
    if args.cmd == "block":
        return cmd_block(Path(args.run_dir), args.slice_id, args.question, project)
    if args.cmd == "answer":
        return cmd_answer(Path(args.run_dir), args.slice_id, args.text, args.by, project)
    if args.cmd == "next":
        return cmd_next(Path(args.run_dir), project)
    if args.cmd == "proceed":
        return cmd_proceed(Path(args.run_dir), project)
    if args.cmd == "panel":
        return cmd_panel(Path(args.run_dir), args.record, args.note, args.base, project)
    if args.cmd == "finding":
        return cmd_finding(Path(args.run_dir), args.slice_id, args.text, args.round, project)
    if args.cmd == "pr-body":
        return cmd_pr_body(Path(args.run_dir), args.base, project)
    path = build_dashboard(project, Path(args.out) if args.out else None, costs=not args.no_cost)
    print(path.resolve().as_uri())
    if args.open:
        why = open_file(path)
        if why:
            print(f"⚠ Not opened ({why}) — open the address above in a browser.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
