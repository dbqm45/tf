#!/usr/bin/env python3
"""
tf task — task state in one place: `docs/project/changes/<KEY>/task.json`. The only writer of this file;
the model calls commands, it does not edit the state by hand. No model and no network.

  tf task start <KEY> --title "<title>" [--weight light|normal|full] [--mode plan|normal|auto]
  tf task start <CHG>-<TSK> --title "<title>" --change <CHG> --cut <TSK>      # a pdi change cut task
  tf task stage <KEY> <stage> [--force]
  tf task status <KEY> [--json]
  tf task slice <KEY> S1 planned|implemented|blocked [--title "<value>"] [--reason "<block reason>"]
  tf task verify <KEY> S1 --files <file>[,<file>…] [--command "<command>"] [--timeout <s>]
  tf task artifact <KEY> <file> --stage <stage> --by <executor> [--inputs <file>[,<file>…]]
  tf task approve <KEY> <file> --by human:<id>
  tf task check <KEY>
  tf task weight <KEY> [--apply | --set light|normal|full] [--by human:<id> --reason "<why>"] [--json]
  tf task mode <KEY> [plan|normal|auto]
  tf task deployed <KEY> [--version <X>] [--timeout <s>]           # smoke test from the operations card after deployment
  tf task deployed <KEY> --rolled-back --by human:<id> [--note "<what was done>"]   # the human's rollback decision
  tf task finding <KEY> add "<important review finding>" [--slice S1] [--round 1]
  tf task finding <KEY> control F1 "<test, hook, rule or the reason there is none>"   # what will catch it next time
  tf task review <KEY> <reviewer> pass|fail [--note "<remark>"]   # panel verdict at full weight
  tf task close <KEY> [--lesson "<lesson>" --by human:<id>] [--base <branch>] [--force --by human:<id>]

`tf status` (that is `task_state.py list [--json]`) lists all tasks: stage, how many slices have current evidence
and which files need refreshing — state computed at read time, not from INDEX.md. Under a task that waits for a human
there is a “waiting for you” line: a plan to approve, a run stop (what happened, the reason, the question
and the recommended option — from `.tf/runs/<KEY>/run.json` and the loop messages) or a slice blocked by a question;
in `--json` this is the `waiting` field.

Key: a tracker number (PROJ-123), a pdi key (CHG-12, TSK-57) or T-<YYYYMMDD>-<slug>. Stages go in order:
intake → spec → plan → implementation → review → pr → deploy → closed; going back requires --force.
`start` in an existing change directory (e.g. from pdi mode) adds only `task.json` and touches no other files.
`tf status` gives the task list — it computes it from the folders, so the agent need not browse them. There is no index file:
`docs/project/changes/INDEX.md` was rewritten on every task write, so two task pull requests open at once had
a conflict in it. A file that is already in the repository is replaced on the first write with a fixed note (“the list is given by tf
status”) and not changed again; the script does not create a new file.

A pdi change cut task (`--change CHG-12 --cut TSK-57`) has the key `<CHG>-<TSK>` (`CHG-12-TSK-57`) and the `change`
and `cut` fields in `task.json`; `list` and `status` show them together with their change. The change plan
was approved by a human at the pdi gate before the implementation phase, so a full-weight cut can run in `auto` mode.

A slice is “verified” only when it has evidence. `verify` itself runs the command (by default the one from
`.claude/quality-gate.json`), so the exit code cannot be declared, and writes `evidence/S1-<n>.json`
(command, exit code, commit SHA, time, slice file hashes); the full output goes to `.tf/runs/<KEY>/`. The state is computed on every read: no evidence or a change of a
file after the evidence → unverified; an exit code other than 0 → red. A task moves to the `review` stage and later
only when all slices are verified (or with --force). When a task has `spec.md`, it moves to the `plan` stage
and later only with an error-free specification (`tf spec check <KEY>`), and to the `review` stage and later —
when every criterion has a test (`tf trace <KEY>`); a task without `spec.md` works as before.

Task weight (`weight`, rules in `task_weight.py`): without options it shows the current weight and a proposal with the reason; `--apply`
assigns the proposal (the first time any, later only a higher one; after a human decision it changes nothing); `--set` raises freely, and lowers only with
`--by human:<id>` and `--reason`. Effects: a task of weight `full` enters the `implementation` stage only with a plan
approved by a human (`approve <KEY> plan.md`); a task of weight `light` has at most one slice in the plan.

Task mode (`mode`; chosen by a human in the command): `plan` — the task does not enter the `implementation` stage (the run
ends at the plan); `normal` — a task with a registered `plan.md` enters implementation after the human's consent
(`approve <KEY> plan.md`); `auto` — without consent, unless the weight is full. `auto` mode cannot be set at full
weight: `normal` stays, and the command says why (exception: a cut task, described above).

Task files (`spec.md`, `plan.md`…) are registered by `artifact`: who generated them and from which files they were made (the input
hashes). Only a human approves (`approve --by human:<id>`). A file's state is computed: an input change → stale;
a file change after approval → needs re-approval. The state is in `task.json`, not in file headers — the script never
changes the files (the pdi contract headers stay untouched). Executor: `<tool>/<version>`,
`human:<id>` or `process:<id>` (as in OKF 0.2). `check` exits with code 1 when any file is not current.

Task oracle: `freeze <KEY> <file>[,<file>…] --by human:<id>` freezes files outside the task directory (e.g. acceptance
tests) — the `guard_paths` hook asks the human before writing to them, to the task's approved files and to
`spec.md` from the implementation stage, and a change to a frozen file by another route blocks `check` and the `review` stage.
`reopen <KEY> <file> --by human:<id> --reason "<reason>"` removes an approval or a freeze and records the reason.

Feature flag: `flag <KEY> set <key> [--remove-by YYYY-MM-DD]` records the flag behind which new behavior hides;
`flag <KEY> none --reason "bez flagi, bo …"` — an explicit absence of a flag; `flag <KEY> allow <environment> --by human:<id>` —
a human's consent to enabling outside the test environment. A task with `spec.md` moves to the `pr` stage only
with a flag or the reason for its absence and without a `tf flag check <KEY>` error (a flag enabled outside the test without consent).

Exit code: 0 — done; 1 — refusal (the task exists, does not exist, a stage backwards); 2 — invocation error.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8

SCHEMA = 1
CHANGES = Path("docs") / "project" / "changes"
RUNS = Path(".tf") / "runs"                       # working directories of /tf loop runs (run.json: stage, stop)
STOP_MESSAGES = Path(".claude") / "skills" / "tf" / "templates" / "stop_messages.json"
CARD = Path(".tf") / "config" / "operations.json"   # the project's operations card; the `deploy` section: how to check and roll back a deployment
PANEL = ("security-reviewer", "spec-reviewer")   # reviewer panel at full weight (step H11, decision D11)
LESSONS = Path("docs") / "project" / "lessons.md"
LESSON_HEAD = "Execution and verification"        # category of lessons recorded when a task is closed
BASES = ("origin/main", "main", "origin/master", "master")
DEPLOY_STATES = {"ok": "the smoke test is green", "red": "the smoke test is red — waits for a rollback decision",
                 "rolled-back": "rolled back by the human's decision"}
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
STAGES = ("intake", "spec", "plan", "implementation", "review", "pr", "deploy", "closed")
WEIGHTS = ("light", "normal", "full")
MODES = ("plan", "normal", "auto")
PDI_KEY = re.compile(r"[A-Z][A-Z0-9]+-[0-9]+")   # key of a pdi change and cut (CHG-12, TSK-57)
SLICE = re.compile(r"S[1-9][0-9]?")   # S<n> (K<n> of tasks from before 14.0.0: migrated in 19.0.0)
SLICE_STATES = ("planned", "implemented", "blocked")
GATED = STAGES[STAGES.index("review"):]   # stages a task with an unverified slice does not enter
ACTOR = re.compile(r"(human|process):[\w.@-]+|[\w.-]+/[\w.-]+")
INDEX_NOTE = ("# Tasks\n\nThe `tf status` command gives the list of tasks with their stage and state — it computes it live from the "
              "folders next to this file (one folder is one task or one change).\n\nThis file is no longer an index. In the "
              "past every task record rewrote it, so two task pull requests open at the same time had a conflict in it. "
              "It can be deleted.\n")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fail(msg: str, code: int = 1) -> int:
    print(f"✗ {msg}")
    return code


def task_path(root: Path, key: str) -> Path:
    return root / CHANGES / key / "task.json"


def load(root: Path, key: str) -> dict | None:
    try:
        data = json.loads(task_path(root, key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_atomic(path: Path, text: str) -> None:
    """Write via a temporary file and a rename — an interrupted write does not leave half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save(root: Path, task: dict) -> None:
    write_atomic(task_path(root, task["key"]), json.dumps(task, ensure_ascii=False, indent=1) + "\n")
    retire_index(root)


def cut_note(task: dict) -> str:
    """“cut TSK-57 of change CHG-12” for a cut task; empty text for an ordinary task."""
    return f"cut {task.get('cut')} of the change {task['change']}" if task.get("change") else ""


def retire_index(root: Path) -> None:
    """Replaces the old `INDEX.md` index once with a fixed note; does not create a new file. An index rewritten on every
    write caused a conflict between the branches of two tasks — the list is given by `tf status`."""
    index = root / CHANGES / "INDEX.md"
    try:
        if index.is_file() and index.read_text(encoding="utf-8") != INDEX_NOTE:
            write_atomic(index, INDEX_NOTE)
    except OSError:
        pass


def sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


TICKED = re.compile(rb"(?m)^(\s*-\s*)\[[xX]\](\s*S\d+\b)")


def approval_sha(path: Path) -> str | None:
    """The hash of a file for approval. In `plan.md` ticking a slice (`- [x] S1`) does not count: the loop ticks slices
    after the plan is approved and thereby does not change its content; a new or changed slice changes the hash."""
    if path.name != "plan.md":
        return sha256(path)
    try:
        return hashlib.sha256(TICKED.sub(rb"\1[ ]\2", path.read_bytes())).hexdigest()
    except OSError:
        return None


def evidence_of(root: Path, key: str, sl: dict) -> dict | None:
    rel = sl.get("evidence")
    if not rel:
        return None
    try:
        data = json.loads((root / CHANGES / key / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def slice_state(root: Path, key: str, sl: dict) -> tuple[str, str]:
    """(state, reason) computed from the evidence and the current files — not from a declaration."""
    if sl.get("state") == "blocked":
        return "blocked", sl.get("reason") or "no reason given"
    ev = evidence_of(root, key, sl)
    if ev is None:
        return ("planned", "") if sl.get("state") == "planned" else ("unverified", "no evidence")
    if ev.get("exit_code") != 0:
        return "red", f"`{ev.get('command')}` ended with code {ev.get('exit_code')}"
    changed = [f for f, h in (ev.get("files") or {}).items() if sha256(root / f) != h]
    if changed:
        return "unverified", "files changed after the evidence: " + ", ".join(changed)
    return "verified", ""


def slice_states(root: Path, task: dict) -> dict[str, tuple[str, str]]:
    return {k: slice_state(root, task["key"], v) for k, v in sorted((task.get("slices") or {}).items())}


def inside(folder: Path, name: str) -> Path | None:
    """A task file by name relative to the task directory; None when it points outside the directory or does not exist."""
    target = (folder / name).resolve()
    if Path(name).is_absolute() or folder.resolve() not in target.parents or not target.is_file():
        return None
    return target


def artifact_state(root: Path, key: str, art: dict, name: str) -> tuple[str, str]:
    """(state, reason) of a task file computed from hashes: draft / approved / stale / changed-after-approval."""
    folder = root / CHANGES / key
    changed = [f for f, h in (art.get("inputs") or {}).items() if sha256(folder / f) != h]
    if changed:
        return "stale", "changed inputs: " + ", ".join(changed)
    if art.get("status") == "approved":
        if approval_sha(folder / name) != art.get("approved_sha"):
            return "changed-after-approval", "needs a new approval by the human"
        return "approved", ""
    return "draft", ""


def artifact_states(root: Path, task: dict) -> dict[str, tuple[str, str]]:
    return {n: artifact_state(root, task["key"], a, n) for n, a in sorted((task.get("artifacts") or {}).items())}


def frozen_changed(root: Path, task: dict) -> list[str]:
    """Frozen files whose content differs from what was recorded at freezing (or that no longer exist)."""
    return [rel for rel, f in sorted((task.get("frozen") or {}).items()) if sha256(root / rel) != f.get("sha")]


def cmd_freeze(root: Path, key: str, files: list[str], by: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    entries = {}
    for rel in files:
        target = inside(root, rel)
        if target is None:
            return fail(f"\"{rel}\" is not a file in the project — give a path relative to the root directory", 2)
        entries[target.relative_to(root).as_posix()] = {"sha": sha256(target), "by": by, "at": now()}
    task.setdefault("frozen", {}).update(entries)
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: frozen {', '.join(entries)} — a change needs: tf task reopen {key} <file> --by human:<id> --reason \"…\"")
    return 0


def cmd_reopen(root: Path, key: str, name: str, by: str, reason: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    art = (task.get("artifacts") or {}).get(name)
    if art is not None and art.get("status") == "approved":
        art["status"] = "draft"
        art.pop("approved_sha", None)
        what = "approval removed"
    elif name in (task.get("frozen") or {}):
        del task["frozen"][name]
        what = "freeze removed"
    else:
        return fail(f"{name} is neither an approved file of the task {key} nor a frozen file — there is nothing to reopen")
    task.setdefault("reopened", []).append({"file": name, "by": by, "at": now(), "reason": reason})
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: {what} ({reason}). After the change register and approve the file again.")
    return 0


def cmd_artifact(root: Path, key: str, name: str, stage: str, by: str, inputs: list[str]) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    folder = root / CHANGES / key
    if inside(folder, name) is None:
        return fail(f"there is no file {name} in {CHANGES / key}/ — you register an existing task file", 2)
    hashes = {}
    for f in inputs:
        target = inside(folder, f)
        if target is None:
            return fail(f"the input \"{f}\" is not a file in {CHANGES / key}/", 2)
        hashes[f] = sha256(target)
    task.setdefault("artifacts", {})[name] = {"stage": stage, "status": "draft", "generated": {"by": by, "at": now()},
                                              "inputs": hashes}
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: draft (stage {stage}" + (f"; inputs: {', '.join(hashes)}" if hashes else "") + ")")
    return 0


def cmd_approve(root: Path, key: str, name: str, by: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    art = (task.get("artifacts") or {}).get(name)
    if art is None:
        return fail(f"the file {name} is not registered — first: tf task artifact {key} {name} --stage … --by …", 2)
    state, why = artifact_state(root, key, art, name)
    if state == "stale":
        return fail(f"{name} is out of date ({why}) — refresh it and register it again before the approval")
    art["status"] = "approved"
    art["approved_sha"] = approval_sha(root / CHANGES / key / name)
    art["verified"] = [{"by": by, "at": now()}]
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {name}: approved by {by}")
    return 0


def cmd_check(root: Path, key: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    bad = {n: (s, w) for n, (s, w) in artifact_states(root, task).items() if s in ("stale", "changed-after-approval")}
    for n, (s, w) in bad.items():
        print(f"⚠ {n}: {s} ({w})")
    changed = frozen_changed(root, task)
    for rel in changed:
        print(f"⚠ {rel}: a frozen file changed without the human's decision — revert the change or: tf task reopen {key} {rel} "
              "--by human:<id> --reason \"…\"")
    if not bad and not changed:
        print(f"✓ {key}: the task's files are current")
    return 1 if bad or changed else 0


def cmd_slice(root: Path, key: str, slice_id: str, state: str, title: str | None, reason: str | None) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    sl = task.setdefault("slices", {}).setdefault(slice_id, {})
    sl["state"] = state
    if title:
        sl["title"] = title.strip()
    if state == "blocked":
        sl["reason"] = (reason or "").strip()
    else:
        sl.pop("reason", None)
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key} {slice_id}: {slice_state(root, key, sl)[0]}")
    return 0


def run_command(root: Path, command: str, timeout: float) -> tuple[int, str]:
    """Runs the verification command (without a shell; through the test lock when the factory has one): (exit code, output)."""
    argv = shlex.split(command)
    lock = root / ".claude" / "hooks" / "test_lock.py"
    if lock.is_file():
        argv = [sys.executable, str(lock), "--", *argv]
    try:
        r = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)})
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", "replace")
        return 124, f"przekroczony limit czasu {timeout:g} s\n{out}"
    except OSError as e:
        return 127, str(e)
    return r.returncode, r.stdout + r.stderr


def clip(out: str, saved: str) -> str:
    if len(out) <= 3000:
        return out
    return out[:1000] + f"\n… [{len(out) - 3000} characters skipped; the whole output: {saved}] …\n" + out[-2000:]


def red_tests(root: Path, files: list[str]) -> dict[str, str]:
    """Slice files that the TDD hook saw as a red test (`.tf/logs/tdd-red.jsonl`): file → time of the first
    red run. The journal is outside git, so the entry goes into the slice's evidence."""
    out: dict[str, str] = {}
    try:
        lines = (root / ".tf" / "logs" / "tdd-red.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        for rel in (row.get("tests") or []) if isinstance(row, dict) else []:
            if rel in files and str(row.get("at", "")) < out.get(rel, "~"):
                out[rel] = str(row.get("at", ""))
    return out


def cmd_verify(root: Path, key: str, slice_id: str, command: str, files: list[str], timeout: float) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    hashes = {}
    for f in files:
        target = (root / f).resolve()
        if Path(f).is_absolute() or root not in target.parents:
            return fail(f"the file \"{f}\" is outside the project — give relative paths of the slice's files", 2)
        digest = sha256(target)
        if digest is None:
            return fail(f"there is no file {f} — evidence is tied to the slice's existing files", 2)
        hashes[f] = digest
    folder = root / CHANGES / key / "evidence"
    n = 1 + max([int(m.group(1)) for m in (re.fullmatch(rf"{slice_id}-(\d+)\.json", x.name) for x in folder.glob(f"{slice_id}-*.json")) if m]
                or [0]) if folder.is_dir() else 1
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        commit = head.stdout.strip() if head.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        commit = None
    code, out = run_command(root, command, timeout)
    log = Path(".tf") / "runs" / key / f"{slice_id}-{n}.log"
    try:   # the full output is outside git; only the path stays in the evidence
        (root / log).parent.mkdir(parents=True, exist_ok=True)
        (root / log).write_text(out, encoding="utf-8")
    except OSError:
        pass
    rel = f"evidence/{slice_id}-{n}.json"
    write_atomic(root / CHANGES / key / rel, json.dumps(
        {"slice": slice_id, "command": command, "exit_code": code, "sha": commit, "at": now(), "files": hashes,
         "log": str(log), **({"red_tests": red} if (red := red_tests(root, list(hashes))) else {})},
        ensure_ascii=False, indent=1) + "\n")
    sl = task.setdefault("slices", {}).setdefault(slice_id, {})
    if sl.get("state") != "implemented":
        sl["state"] = "implemented"
        sl.pop("reason", None)
    sl["evidence"] = rel
    task["updated"] = now()
    save(root, task)
    state, why = slice_state(root, key, sl)
    print(f"{'✓' if code == 0 else '✗'} {key} {slice_id}: {state} (evidence: {CHANGES / key / rel})"
          + (f" — {why}" if why else ""))
    if code != 0:
        print(f"--- output ---\n{clip(out, str(log))}")
    return 0 if code == 0 else 1


def deploy_card(root: Path) -> dict:
    """The `deploy` section of the operations card: `smoke` (smoke test), `rollback`, `rollback_minutes`, `approval`, `logs`.
    Empty when there is no card or it cannot be read."""
    try:
        dep = json.loads((root / CARD).read_text(encoding="utf-8")).get("deploy")
    except (OSError, ValueError, AttributeError):
        return {}
    return dep if isinstance(dep, dict) else {}


def one_line(value, limit: int = 300) -> str:
    """One line without control characters — text from the card and from commands goes to the terminal and to task.json."""
    return " ".join(re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(value)).split())[:limit]


def minutes(value) -> str:
    """“ok. N min” for a sensible number of minutes from the card; empty text for any other value."""
    try:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < 100000
        return f"ok. {float(value):g} min" if ok else ""
    except (OverflowError, ValueError):
        return ""


def rollback_text(dep: dict) -> str:
    """How to roll back a deployment: steps from the card (text or a list) with the time, and the default step without them."""
    value = dep.get("rollback")
    lines = value.splitlines() if isinstance(value, str) else value if isinstance(value, list) else []
    steps = [one_line(x) for x in lines if isinstance(x, str) and x.strip()][:10]
    if not steps:
        return ("git revert of the merge commit on the default branch and an ordinary deployment (the operations card does not "
                "describe a rollback: the deploy.rollback field)")
    timed = minutes(dep.get("rollback_minutes"))
    return "; ".join(steps) + (f" ({timed})" if timed else "")


def cmd_deployed(root: Path, key: str, version: str | None, timeout: float, rolled_back: bool, by: str | None,
                 note: str) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    stage = task.get("stage", STAGES[0])
    if stage not in STAGES or STAGES.index(stage) < STAGES.index("pr"):
        return fail(f"the task {key} is at the stage {stage} — you record a deployment after the PR is merged (the pr stage)")
    prev = task.get("deploy") if isinstance(task.get("deploy"), dict) else {}
    if rolled_back:
        if prev.get("state") != "red":
            return fail(f"a rollback is recorded after a red smoke test, and the task {key} has no such result "
                        f"(first: tf task deployed {key})")
        task["deploy"] = {**prev, "state": "rolled-back", "decided_by": by, "decided_at": now(),
                          **({"note": one_line(note)} if note.strip() else {})}
        task["updated"] = now()
        save(root, task)
        print(f"✓ {key}: the deployment rollback is recorded ({by}). After a fix and a new deployment: tf task deployed {key}")
        return 0
    card = deploy_card(root)
    smoke = card.get("smoke")
    if not isinstance(smoke, str) or not smoke.strip():
        print(f"• {key}: the operations card has no smoke test (the `deploy.smoke` field in {CARD.as_posix()}) — the factory "
              "ends at the merge and does not check the deployment.\n  Enter the smoke test command (`tf onboard` shows what "
              f"the card is missing) and run again: tf task deployed {key}")
        return 0
    smoke = smoke.strip()
    folder = root / CHANGES / key / "evidence"
    n = 1 + max([int(m.group(1)) for m in (re.fullmatch(r"deploy-(\d+)\.json", x.name) for x in folder.glob("deploy-*.json")) if m]
                or [0]) if folder.is_dir() else 1
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        commit = head.stdout.strip() if head.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        commit = None
    try:
        code, out = run_command(root, smoke, timeout)
    except ValueError as e:          # the command from the card cannot be split into arguments (e.g. an unclosed quote)
        code, out = 127, f"the smoke test command is invalid: {e}"
    log = RUNS / key / f"deploy-{n}.log"
    try:   # the full output is outside git; only the path stays in the evidence
        (root / log).parent.mkdir(parents=True, exist_ok=True)
        (root / log).write_text(out, encoding="utf-8")
    except OSError:
        pass
    rel, at = f"evidence/deploy-{n}.json", now()
    ver = one_line(version, 60) if version and version.strip() else None
    write_atomic(root / CHANGES / key / rel, json.dumps(
        {"kind": "deploy", "command": smoke, "exit_code": code, "version": ver, "sha": commit, "at": at, "log": str(log)},
        ensure_ascii=False, indent=1) + "\n")
    why = f"`{smoke}` ended with code {code}"
    task["deploy"] = {"state": "ok" if code == 0 else "red", "evidence": rel, "at": at,
                      **({"version": ver} if ver else {}), **({} if code == 0 else {"why": why})}
    if code == 0 and STAGES.index(stage) < STAGES.index("deploy"):
        task["stage"] = "deploy"
    task["updated"] = at
    save(root, task)
    where = CHANGES / key / rel
    if code == 0:
        print(f"✓ {key}: the smoke test after the deployment is green (`{smoke}`) — stage {task['stage']}; evidence: {where}")
        if isinstance(card.get("approval"), str) and card["approval"].strip():
            print(f"  The human approves: {one_line(card['approval'])}")
        return 0
    print(f"✗ {key}: the smoke test after the deployment is red — {why} (evidence: {where})\n--- output ---\n{clip(out, str(log))}\n"
          "Roll back the deployment? The decision is yours — the factory rolls nothing back by itself.\n"
          f"  How to roll back: {rollback_text(card)}")
    if isinstance(card.get("logs"), str) and card["logs"].strip():
        print(f"  Logs (the command from the card, the factory does not run it): {one_line(card['logs'])}")
    print(f"  After rolling back: tf task deployed {key} --rolled-back --by human:<id>\n"
          f"  After a fix and a new deployment: tf task deployed {key}")
    return 1


def cmd_finding(root: Path, key: str, action: str, first: str | None, second: str | None, slice_id: str | None,
                rnd: int | None) -> int:
    """Important review findings (`findings` in task.json) and the control that will catch them next time."""
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    found = task.setdefault("findings", [])
    if action == "add":
        text = one_line(first or "", 400)
        if not text:
            return fail(f"give the finding: tf task finding {key} add \"<what the review found important>\"", 2)
        fid = f"F{len(found) + 1}"
        found.append({"id": fid, "text": text, **({"slice": slice_id} if slice_id else {}),
                      **({"round": rnd} if rnd else {}), "at": now()})
        task["updated"] = now()
        save(root, task)
        print(f"✓ {key}: the finding {fid} is recorded. Now revert the code and do a new round of the slice; the control that will "
              "catch it next time is added when the task is closed (tf task close shows what is missing)")
        return 0
    item = next((f for f in found if f.get("id") == first), None)
    if item is None:
        return fail(f"there is no finding {first} in the task {key} — recorded: "
                    + (", ".join(f.get("id", "?") for f in found) or "none"))
    text = one_line(second or "", 400)
    if not text:
        return fail(f"give the control: tf task finding {key} control {first} \"<a test, a hook, a rule or the reason it is missing>\"", 2)
    item["control"], item["control_at"] = text, now()
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: the control for {first} is recorded")
    return 0


def merged_on(root: Path, key: str, base: str | None) -> tuple[bool | None, str]:
    """Whether the change is merged: the task's task.json file is on the default branch (works with squash and rebase too).
    (True, branch) | (False, checked branches) | (None, reason) — None when this cannot be checked."""
    rel, seen = (CHANGES / key / "task.json").as_posix(), []
    for cand in ([base] if base else BASES):
        try:
            if subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{cand}:{rel}"], capture_output=True,
                              timeout=20).returncode == 0:
                return True, cand
            known = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{cand}^{{commit}}"],
                                   capture_output=True, timeout=20).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return None, "git does not respond"
        if known:
            seen.append(cand)
    return (False, ", ".join(seen)) if seen else (None, "git does not know the branch " + (base or "main or master"))


def add_lesson(root: Path, key: str, lesson: str) -> bool:
    """Appends the human's lesson to docs/project/lessons.md (once); True when the file changed."""
    path = root / LESSONS
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Project lessons\n"
    if lesson in text:
        return False
    entry = f"- {now()[:10]} {lesson} · Task: {key}"
    lines = text.rstrip("\n").split("\n")
    at = next((i for i, ln in enumerate(lines) if re.fullmatch(rf"##\s+{re.escape(LESSON_HEAD)}\s*", ln, re.I)), None)
    if at is None:
        lines += ["", f"## {LESSON_HEAD}", "", entry]
    elif at + 1 < len(lines) and not lines[at + 1].strip():
        lines.insert(at + 2, entry)                 # under the heading, before older entries (newest on top)
    else:
        lines[at + 1:at + 1] = ["", entry]
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, "\n".join(lines) + "\n")
    return True


def cmd_close(root: Path, key: str, by: str | None, lesson: str | None, base: str | None, force: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — the list of tasks: tf status --all")
    stage = task.get("stage", STAGES[0])
    if stage == "closed":
        print(f"• {key} is already closed" + (f" ({task['closed']['at']})" if isinstance(task.get("closed"), dict)
                                              and task["closed"].get("at") else ""))
        return 0
    if stage not in STAGES or STAGES.index(stage) < STAGES.index("pr"):
        return fail(f"the task {key} is at the stage {stage} — you close it after the PR is merged (the pr or deploy stage)")
    if not force:
        merged, where = merged_on(root, key, base)
        if merged is None:
            return fail(f"it cannot be confirmed that the change {key} is merged ({where}). Closing it anyway is "
                        f"the human's decision: tf task close {key} --force --by human:<id>")
        if not merged:
            return fail(f"the change {key} is not merged: the default branch ({where}) has no file "
                        f"{(CHANGES / key / 'task.json').as_posix()}. After the PR is merged fetch the branch (git fetch) and repeat; "
                        f"closing it anyway: tf task close {key} --force --by human:<id>")
    dep = task.get("deploy") if isinstance(task.get("deploy"), dict) else {}
    if dep.get("state") == "red":
        return fail(f"the deployment of {key} waits for a rollback decision (a red smoke test). After rolling back: tf task deployed "
                    f"{key} --rolled-back --by human:<id>; after a fix and a new deployment: tf task deployed {key}")
    open_ = [f for f in task.get("findings") or [] if isinstance(f, dict) and not f.get("control")]
    if open_:
        return fail("important review findings without a control that will catch them next time: "
                    + "; ".join(f"{f.get('id')} — {f.get('text')}" for f in open_)
                    + f". Record one for each: tf task finding {key} control <F-n> \"<a test, a hook, a rule or the reason "
                      "it is missing>\"")
    wrote = add_lesson(root, key, lesson) if lesson else False
    task["stage"], task["updated"] = "closed", now()
    task["closed"] = {"at": now(), **({"by": by} if by else {}), **({"forced": True} if force else {}),
                      **({"lesson": True} if lesson else {})}
    save(root, task)
    print(f"✓ {key} closed ({stage} → closed)")
    print("  deployment: " + (DEPLOY_STATES[dep["state"]] if isinstance(dep.get("state"), str) and dep["state"] in DEPLOY_STATES
                             else "not checked with a smoke test (tf task deployed was not run)"))
    flag = task.get("flag") if isinstance(task.get("flag"), dict) else {}
    if flag.get("key") and flag.get("remove_by"):
        print(f"  flag {flag['key']}: to be removed by {flag['remove_by']} — the task is closed, the flag stays until that date")
    elif flag.get("key"):
        print(f"  the flag {flag['key']} has no removal date — set it: tf task flag {key} set {flag['key']} --remove-by YYYY-MM-DD")
    if lesson:
        print(f"  lesson: {'added to' if wrote else 'was already in'} {LESSONS.as_posix()}")
    else:
        print(f"  lesson: not recorded (if the task yields a rule for the future, add it to {LESSONS.as_posix()})")
    return 0


def work_style(root: Path) -> dict:
    """The default and allowed modes after layering (engine ← company ← project ← person, `packs.work_style`); without
    packs.py (the script alone) — the normal mode and all modes, as before."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_packs_style", Path(__file__).resolve().with_name("packs.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.work_style(root)
    except Exception:  # noqa: BLE001 — no configuration means the default settings
        return {"default_mode": "normal", "allowed_modes": list(MODES)}


def mode_refusal(root: Path, mode: str) -> str | None:
    allowed = work_style(root).get("allowed_modes") or list(MODES)
    if mode not in allowed:
        return (f"the mode \"{mode}\" is turned off in this project (task.allowed_modes: {', '.join(allowed)} — set by the company, "
                "the team or the project; tf config show task)")
    return None


def cmd_start(root: Path, key: str, title: str, weight: str, mode: str | None, change: str | None = None,
              cut: str | None = None) -> int:
    if load(root, key) is not None:
        return fail(f"the task {key} already exists ({CHANGES / key / 'task.json'}) — its state: tf task status {key}")
    if mode is None:                 # the default mode from configuration (a person's work style within company and project limits)
        mode = work_style(root).get("default_mode") or "normal"
    elif mode_refusal(root, mode):
        return fail(mode_refusal(root, mode), 2)
    stamp = now()
    task = {"schema": SCHEMA, "key": key, "title": title, "stage": STAGES[0], "weight": weight, "mode": mode,
            "created": stamp, "updated": stamp}
    if change:                       # a pdi change cut task
        task["change"], task["cut"] = change, cut
    if weight != "normal":           # a weight given explicitly at creation is already an assignment — `weight --apply` will not lower it
        task["weight_log"] = [{"from": "normal", "to": weight, "by": "process:start", "at": stamp}]
    save(root, task)
    print(f"✓ the task {key} is created: {CHANGES / key}/ (stage: {STAGES[0]})")
    return 0


def weight_rules():
    """Task weight rules from `task_weight.py` next to this script; None when the file is absent (an older installation)."""
    script = Path(__file__).resolve().with_name("task_weight.py")
    if not script.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_task_weight", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def weight_gate(root: Path, task: dict, stage: str) -> str | None:
    """Effects of weight on a stage change: `light` — a plan with one slice; `full` — a plan approved by a human
    before implementation. Returns the refusal reason or None."""
    key, weight = task["key"], task.get("weight")
    rules = weight_rules()
    if weight == "light" and rules and STAGES.index(stage) >= STAGES.index("plan"):
        try:
            slices = rules.plan_slices((root / CHANGES / key / "plan.md").read_text(encoding="utf-8", errors="replace"))
        except OSError:
            slices = []
        if len(slices) > 1:
            return (f"the task has the light weight, i.e. one slice, and the plan has {len(slices)} — merge the slices or "
                    f"raise the weight: tf task weight {key} --set normal")
    if STAGES.index(stage) < STAGES.index("implementation"):
        return None
    mode = task.get("mode")
    if mode == "plan":
        return (f"the task is in the Plan mode — the run ends at the plan, without code changes. The human starts the delivery "
                f"with a separate command (/tf {key}); then change the mode: tf task mode {key} normal (or auto)")
    art = (task.get("artifacts") or {}).get("plan.md")
    state = artifact_state(root, key, art, "plan.md")[0] if art else "none"
    upstream = bool(task.get("change")) and mode == "auto"   # cut: the change plan was approved at the pdi gate
    if weight == "full" and state != "approved" and not upstream:
        return (f"the task has the full weight (a sensitive area), so it moves to the stage {stage} only with a plan "
                f"approved by the human (the plan's state: {state}): show the plan to the human, and after their consent "
                f"tf task approve {key} plan.md --by human:<id>. An unsupervised run (--auto) ends here "
                "with a STOP block — the human's consent cannot be replaced")
    if mode != "auto" and art and state != "approved":
        return (f"in the normal mode the task moves to the stage {stage} after the human's consent to the plan (the plan's state: "
                f"{state}): show the plan and the specification to the human, and after their consent tf task approve {key} plan.md "
                f"--by human:<id>. The human chooses the mode without approval (--auto) in the /tf command: if they gave it, "
                f"record the mode (tf task mode {key} auto); you do not set it yourself to skip the consent")
    return None


MODE_LABEL = {"plan": "Plan", "normal": "normal", "auto": "Auto"}


def cmd_mode(root: Path, key: str, new: str | None) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    current = task.get("mode") if task.get("mode") in MODES else "normal"
    if new is None:
        print(f"{key}: mode {MODE_LABEL[current]}")
        return 0
    if new not in MODES:
        return fail(f"unknown mode \"{new}\" — choose from: {', '.join(MODES)}", 2)
    if mode_refusal(root, new):
        return fail(mode_refusal(root, new), 2)
    note = ""
    if new == "auto" and task.get("weight") == "full" and task.get("change"):
        note = (f" — the full weight (a sensitive area), but this is a cut of the change {task['change']}: the human approved its plan "
                "at the pdi gate, so the run does not wait for a second consent; the security review stays mandatory")
    elif new == "auto" and task.get("weight") == "full":
        new = "normal"
        note = (" — the Auto mode does not cover full-weight tasks (a sensitive area): the normal mode stays, "
                "the human approves the plan")
    if new != task.get("mode"):
        task["mode"], task["updated"] = new, now()
        save(root, task)
    print(f"✓ {key}: mode {MODE_LABEL[new]}{note}")
    return 0


def cmd_weight(root: Path, key: str, apply: bool, new: str | None, by: str | None, reason: str, as_json: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    rules = weight_rules()
    if rules is None:
        return fail("no .tf/factory/task_weight.py — update the factory (tf update)", 2)
    if new is not None and new not in WEIGHTS:
        return fail(f"unknown weight \"{new}\" — choose from: {', '.join(WEIGHTS)}", 2)
    current = task.get("weight") if task.get("weight") in WEIGHTS else "normal"
    assigned = bool(task.get("weight_log"))
    prop = rules.propose(root, key)
    note = ""

    def record(weight: str, who: str, **extra) -> None:
        task.setdefault("weight_log", []).append({"from": current, "to": weight, "by": who, "at": now(), **extra})
        task["weight"], task["updated"] = weight, now()
        save(root, task)

    if new is not None:
        who = by or "process:tf"
        if not ACTOR.fullmatch(who):
            return fail(f"the performer \"{who}\" — expected form: human:<id> or process:<id>", 2)
        if rules.rank(new) < rules.rank(current):
            if not who.startswith("human:"):
                return fail(f"lowering the weight ({rules.LABEL[current]} → {rules.LABEL[new]}) is the human's decision: "
                            f"tf task weight {key} --set {new} --by human:<id> --reason \"<dlaczego>\"")
            if not reason.strip():
                return fail("give the reason for lowering it: --reason \"<why a lower weight is enough>\"", 2)
        if new != current or not assigned:
            record(new, who, **({"reason": " ".join(reason.split())} if reason.strip() else {}))
        current, assigned = new, True
    elif apply:
        last = (task.get("weight_log") or [{}])[-1]
        if str(last.get("by", "")).startswith("human:"):      # the human's decision stays; the factory only says what it sees
            if prop["weight"] != current:
                note = (f"the human set the weight ({last['by']}) — the factory does not change it; its proposal is "
                        f"{rules.LABEL[prop['weight']]}")
        elif not assigned or rules.rank(prop["weight"]) > rules.rank(current):
            record(prop["weight"], "process:tf", reasons=prop["reasons"])
            current, assigned = prop["weight"], True
        elif rules.rank(prop["weight"]) < rules.rank(current):
            note = (f"the proposal ({rules.LABEL[prop['weight']]}) is lower than the assigned weight — "
                    f"{rules.LABEL[current]} stays; only the human can lower it: tf task weight {key} --set {prop['weight']} "
                    "--by human:<id> --reason \"<why>\"")
    if as_json:
        print(json.dumps({"key": key, "weight": current, "assigned": assigned, "proposal": prop["weight"],
                          "reasons": prop["reasons"], "effect": rules.EFFECT[current], "note": note},
                         ensure_ascii=False, indent=1))
        return 0
    state = "" if assigned else " (the default, not assigned yet)"
    print(f"{key}: weight {rules.LABEL[current]}{state} · proposal: {rules.LABEL[prop['weight']]}")
    for r in prop["reasons"]:
        print(f"  reason: {r}")
    print(f"  effect: {rules.EFFECT[current]}")
    if note:
        print(f"  {note}")
    elif not assigned:
        print(f"  Przydziel: tf task weight {key} --apply")
    return 0


def spec_errors(root: Path, key: str) -> list[dict]:
    """Task spec.md errors per `spec_check.py` next to this script; an empty list when the file or the script is absent."""
    script = Path(__file__).resolve().with_name("spec_check.py")
    if not script.is_file() or not (root / CHANGES / key / "spec.md").is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_spec_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.check_task(root, key)
    return result["errors"] if result else []


def trace_errors(root: Path, key: str) -> list[dict]:
    """Criterion → test trace errors per `trace_check.py` next to this script; an empty list when the task has no spec.md,
    the script is absent or the trace cannot be computed (a directory outside git, no base branch)."""
    script = Path(__file__).resolve().with_name("trace_check.py")
    if not script.is_file() or not (root / CHANGES / key / "spec.md").is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_trace_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.trace(root, key)
    return result["errors"] if result else []


def flag_errors(root: Path, key: str) -> list[dict]:
    """Task flag errors per `flag_check.py` next to this script; an empty list when the script is absent."""
    script = Path(__file__).resolve().with_name("flag_check.py")
    if not script.is_file():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_flag_check", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, key)["errors"]


def cmd_flag(root: Path, key: str, action: str, value: str | None, remove_by: str | None, reason: str, by: str | None) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    if action == "set":
        if not value or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
            return fail("give the flag key (letters, digits, _ . -), e.g. proj_123_csv_export", 2)
        if remove_by and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", remove_by):
            return fail("the flag's removal date in the YYYY-MM-DD format", 2)
        old = task.get("flag") if isinstance(task.get("flag"), dict) else {}
        task["flag"] = {"key": value, "remove_by": remove_by or old.get("remove_by"),
                        "allowed": old.get("allowed", {}) if old.get("key") == value else {}}
        msg = f"flag {value}" + (f", to be removed by {task['flag']['remove_by']}" if task["flag"]["remove_by"] else "")
    elif action == "none":
        if not reason.strip():
            return fail("give the reason: --reason \"no flag, because …\"", 2)
        task["flag"] = {"none": " ".join(reason.split())}
        msg = f"no flag: {task['flag']['none']}"
    else:   # allow
        flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
        if not flag or not flag.get("key"):
            return fail(f"the task has no flag — first: tf task flag {key} set <key>")
        if not value:
            return fail("give the environment, e.g. tf task flag <KEY> allow prod --by human:<id>", 2)
        if not by or not by.startswith("human:") or not ACTOR.fullmatch(by):
            return fail("the human records the consent to turn a flag on outside the test environment: --by human:<id>", 2)
        flag.setdefault("allowed", {})[value] = {"by": by, "at": now()}
        msg = f"flag {flag['key']}: consent of {by} for the environment \"{value}\""
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: {msg}")
    return 0


def git_head(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def cmd_review(root: Path, key: str, reviewer: str, verdict: str, note: str) -> int:
    """A panel reviewer's verdict (full weight): verdict, HEAD commit, time and remark in the task's `reviews`."""
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    head = git_head(root)
    task.setdefault("reviews", {})[reviewer] = {"verdict": verdict, **({"sha": head} if head else {}), "at": now(),
                                                **({"note": one_line(note, 300)} if note.strip() else {})}
    task["updated"] = now()
    save(root, task)
    print(f"✓ {key}: {reviewer} — {verdict}" + (f" (commit {head[:12]})" if head else ""))
    return 0


def panel_errors(root: Path, task: dict) -> list[str]:
    """What is missing from the reviewer panel of a full-weight task; an empty list — the panel is complete (or not required)."""
    if task.get("weight") != "full":
        return []
    head, reviews = git_head(root), task.get("reviews") if isinstance(task.get("reviews"), dict) else {}
    out = []
    for name in PANEL:
        r = reviews.get(name) if isinstance(reviews.get(name), dict) else None
        if r is None:
            out.append(f"{name} (no verdict)")
        elif r.get("verdict") != "pass":
            out.append(f"{name} ({r.get('verdict')}" + (f": {r['note']}" if r.get("note") else "") + ")")
        elif head and r.get("sha") and r["sha"] != head:
            out.append(f"{name} (the verdict is for the commit {str(r['sha'])[:12]}, and the code has a newer {head[:12]} — review again)")
    return out


def cmd_stage(root: Path, key: str, stage: str, force: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    was = task.get("stage", STAGES[0])
    if was in STAGES and STAGES.index(stage) < STAGES.index(was) and not force:
        return fail(f"the stage {stage} is earlier than the current one ({was}); going back needs --force")
    if STAGES.index(stage) >= STAGES.index("plan") and not force:
        spec = spec_errors(root, key)
        if spec:
            return fail(f"a task moves to the stage {stage} with a ready specification; to fix in spec.md: "
                        + "; ".join(f"line {e['line']} {e['rule']} {e['message']}" for e in spec[:3])
                        + (f" (and {len(spec) - 3} more)" if len(spec) > 3 else "") + f". All of it: tf spec check {key}")
    if not force:
        refused = weight_gate(root, task, stage)
        if refused:
            return fail(refused)
    if stage in GATED and not force:
        open_ = [f"{k} ({s}{': ' + w if w else ''})" for k, (s, w) in slice_states(root, task).items() if s != "verified"]
        if open_:
            return fail(f"a task moves to the stage {stage} with verified slices; missing: " + "; ".join(open_)
                        + f". Evidence: tf task verify {key} S<n> --files <the slice's files>")
        stale = [f"{n} ({s})" for n, (s, _) in artifact_states(root, task).items()
                 if s in ("stale", "changed-after-approval")]
        stale += [f"{rel} (a frozen file changed)" for rel in frozen_changed(root, task)]
        missing = trace_errors(root, key)
        if missing:
            return fail(f"a task moves to the stage {stage} when every criterion has a test; to fix: "
                        + "; ".join(e["message"] for e in missing[:3])
                        + (f" (and {len(missing) - 3} more)" if len(missing) > 3 else "") + f". All of it: tf trace {key}")
        if stale:
            return fail(f"a task moves to the stage {stage} with current files; to refresh: " + "; ".join(stale)
                        + f". Details: tf task check {key}")
    if STAGES.index(stage) >= STAGES.index("pr") and not force:
        bad = flag_errors(root, key)
        if bad:
            return fail(f"a task moves to the stage {stage} with a feature flag in order: "
                        + "; ".join(f"{e['rule']} {e['message']}" for e in bad) + f". All of it: tf flag check {key}")
        missing = panel_errors(root, task)
        if missing:
            return fail(f"a full-weight task moves to the stage {stage} after the reviewer panel in separate "
                        f"contexts; missing: {'; '.join(missing)}. The commissions and recording a verdict: run_state.py panel "
                        f"<run directory> (or tf task review {key} <reviewer> pass|fail --note \"…\")")
    task["stage"], task["updated"] = stage, now()
    save(root, task)
    print(f"✓ {key}: {was} → {stage}")
    return 0


def stop_message(root: Path, code: str | None) -> dict:
    """The /tf loop stop message for a human (what, need, question, options); empty when there is no loop or code."""
    for base in (Path(__file__).resolve().parents[2], root):
        try:
            msg = json.loads((base / STOP_MESSAGES).read_text(encoding="utf-8")).get(code or "")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(msg, dict):
            return msg
    return {}


def waiting(root: Path, task: dict) -> list[dict]:
    """What the task is waiting for from a human: a plan to approve or a run stop (`.tf/runs/<KEY>/run.json`)
    and slices blocked by a question. An empty list — nothing is waiting."""
    key, out = task.get("key", ""), []
    try:
        run = json.loads((root / RUNS / key / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        run = {}
    if isinstance(run, dict) and run.get("stage") == "needs":
        since = run.get("needs_at")
        if run.get("needs") == "plan":
            out.append({"kind": "plan", "what": "the plan waits for your consent", "details": f"{(CHANGES / key).as_posix()}/plan.md",
                        "question": "Do you approve the plan?", "options": [], "recommended": None,
                        "how": f"tf task approve {key} plan.md --by human:<id>", "since": since})
        elif run.get("needs") == "stop":
            msg = stop_message(root, run.get("stop_code"))
            options = [{"opcja": o.get("opcja"), "skutek": o.get("skutek"), "rekomendowana": bool(o.get("rekomendowana"))}
                       for o in msg.get("opcje") or [] if isinstance(o, dict)]
            out.append({"kind": "stop", "code": run.get("stop_code"),
                        "what": msg.get("co") or f"the run stopped ({run.get('stop_code') or 'no code'})",
                        "details": run.get("stop_text"), "question": msg.get("question"), "options": options,
                        "recommended": next((o["opcja"] for o in options if o["rekomendowana"]), None),
                        "how": msg.get("potem"), "since": since})
    dep = task.get("deploy") if isinstance(task.get("deploy"), dict) else {}
    if dep.get("state") == "red":
        out.append({"kind": "deploy", "what": "the smoke test after the deployment is red", "details": dep.get("why"),
                    "question": "Roll back the deployment?",
                    "options": [{"opcja": "roll back", "skutek": rollback_text(deploy_card(root)), "rekomendowana": True},
                                {"opcja": "fix and deploy again",
                                 "skutek": "the change stays deployed until the fix", "rekomendowana": False}],
                    "recommended": "roll back",
                    "how": f"after rolling back: tf task deployed {key} --rolled-back --by human:<id>; after a fix "
                           f"and a new deployment: tf task deployed {key}", "since": dep.get("at")})
    for k, (state, why) in slice_states(root, task).items():
        if state == "blocked":
            out.append({"kind": "slice", "slice": k, "what": f"slice {k} waits for your answer", "details": why,
                        "question": None, "options": [], "recommended": None,
                        "how": f"after the answer: tf task slice {key} {k} planned", "since": None})
    return out


def task_rows(root: Path) -> list[dict]:
    """All tasks with the state computed now (slices, files to refresh)."""
    rows = []
    for f in sorted((root / CHANGES).glob("*/task.json")):
        t = load(root, f.parent.name)
        if not t:
            continue
        slices = {k: s for k, (s, _) in slice_states(root, t).items()}
        stale = [n for n, (s, _) in artifact_states(root, t).items() if s in ("stale", "changed-after-approval")]
        rows.append({"key": t.get("key", f.parent.name), "title": t.get("title", ""), "stage": t.get("stage", "?"),
                     "updated": t.get("updated", ""), "slices": slices,
                     "verified": sum(s == "verified" for s in slices.values()), "stale": stale,
                     "waiting": waiting(root, t),
                     **({"change": t["change"], "cut": t.get("cut")} if t.get("change") else {})})
    return rows


def cmd_list(root: Path, as_json: bool, show_all: bool = False) -> int:
    rows = task_rows(root)
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print(f"No tasks in {CHANGES}/. You create the first one with: tf task start <KEY> --title \"<title>\"")
        return 0
    closed = sum(r["stage"] == "closed" for r in rows)
    if not show_all:
        rows = [r for r in rows if r["stage"] != "closed"]
        if not rows:
            print("No tasks in progress.")
    for r in rows:
        print(f"{r['key']}  {r['stage']}  slices with evidence {r['verified']}/{len(r['slices'])}  {r['title']}"
              + (f"  ({cut_note(r)})" if cut_note(r) else ""))
        for k, s in r["slices"].items():
            if s != "verified":
                print(f"    {k}: {s}")
        for name in r["stale"]:
            print(f"    {name}: to refresh (tf task check {r['key']})")
        for w in r["waiting"]:
            print(f"    waiting for you: {w['what']}" + (f" — {w['details']}" if w.get("details") else ""))
            if w.get("question"):
                print(f"      question: {w['question']}"
                      + (f" (recommended: {w['recommended']})" if w.get("recommended") else ""))
            if w.get("how") and w["kind"] != "stop":
                print(f"      {w['how']}")
    if closed and not show_all:
        print(f"closed: {closed} (show all: tf status --all)")
    return 0


def cmd_status(root: Path, key: str, as_json: bool) -> int:
    task = load(root, key)
    if task is None:
        return fail(f"there is no task {key} — create it: tf task start {key} --title \"…\"")
    states = slice_states(root, task)
    if as_json:
        print(json.dumps({**task, "slice_states": {k: s for k, (s, _) in states.items()},
                          "artifact_states": {n: s for n, (s, _) in artifact_states(root, task).items()}},
                         ensure_ascii=False, indent=1))
        return 0
    done = STAGES.index(task["stage"]) + 1 if task.get("stage") in STAGES else 0
    print(f"{task['key']} — {task.get('title', '')}\n"
          f"stage: {task.get('stage', '?')} ({done} of {len(STAGES)}) · weight: {task.get('weight', '?')} · "
          f"mode: {task.get('mode', '?')} · changed: {task.get('updated', '?')}"
          + (f"\n{cut_note(task)}" if cut_note(task) else ""))
    for k, (state, why) in states.items():
        title = (task["slices"][k].get("title") or "").strip()
        print(f"  {k}: {state}" + (f" — {title}" if title else "") + (f" ({why})" if why else ""))
    for n, (state, why) in artifact_states(root, task).items():
        print(f"  {n}: {state}" + (f" ({why})" if why else ""))
    flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
    if flag and flag.get("key"):
        print(f"  flag: {flag['key']}" + (f" (to be removed by {flag['remove_by']})" if flag.get("remove_by") else "")
              + (f" — consent for: {', '.join(sorted(flag['allowed']))}" if flag.get("allowed") else ""))
    elif flag and flag.get("none"):
        print(f"  flag: none — {flag['none']}")
    for f in task.get("findings") or []:
        if isinstance(f, dict):
            print(f"  finding {one_line(f.get('id'), 8)}" + (f" ({one_line(f['slice'], 4)})" if f.get("slice") else "")
                  + f": {one_line(f.get('text'), 400)} — "
                  + (f"control: {one_line(f['control'], 400)}" if f.get("control") else "no control"))
    for name, r in sorted((task.get("reviews") or {}).items()) if isinstance(task.get("reviews"), dict) else []:
        if isinstance(r, dict):
            print(f"  review {one_line(name, 40)}: {one_line(r.get('verdict'), 10)}"
                  + (f" (commit {str(r['sha'])[:12]})" if r.get("sha") else "") + (f" — {one_line(r['note'], 200)}" if r.get("note") else ""))
    if isinstance(task.get("closed"), dict):
        print(f"  closed: {task['closed'].get('at', '?')}" + (f" ({task['closed']['by']})" if task["closed"].get("by") else ""))
    dep = task.get("deploy") if isinstance(task.get("deploy"), dict) else None
    if dep and isinstance(dep.get("state"), str) and dep["state"] in DEPLOY_STATES:
        print(f"  deployment: {DEPLOY_STATES[dep['state']]}" + (f" · version {one_line(dep['version'], 60)}" if dep.get("version") else "")
              + (f" · {one_line(dep['at'], 40)}" if dep.get("at") else ""))
    changed = set(frozen_changed(root, task))
    for rel in sorted(task.get("frozen") or {}):
        print(f"  {rel}: frozen" + (" — changed without the human's decision" if rel in changed else ""))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf task", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("key")
    s.add_argument("--title", default=None)
    s.add_argument("--weight", default="normal")
    s.add_argument("--mode", default=None, help="plan|normal|auto; without the option — task.default_mode (the working style, tf style)")
    s.add_argument("--change", default=None, help="the pdi change key, e.g. CHG-12 (a cut task; together with --cut)")
    s.add_argument("--cut", default=None, help="the cut key from the change plan, e.g. TSK-57 (together with --change)")
    g = sub.add_parser("stage")
    g.add_argument("key")
    g.add_argument("stage")
    g.add_argument("--force", action="store_true")
    c = sub.add_parser("slice")
    c.add_argument("key")
    c.add_argument("slice_id")
    c.add_argument("state")
    c.add_argument("--title", default=None)
    c.add_argument("--reason", default=None)
    v = sub.add_parser("verify")
    v.add_argument("key")
    v.add_argument("slice_id")
    v.add_argument("--command", default=None)
    v.add_argument("--timeout", type=float, default=900)
    v.add_argument("--files", default="")
    r = sub.add_parser("artifact")
    r.add_argument("key")
    r.add_argument("name")
    r.add_argument("--stage", required=True)
    r.add_argument("--by", required=True)
    r.add_argument("--inputs", default="")
    o = sub.add_parser("approve")
    o.add_argument("key")
    o.add_argument("name")
    o.add_argument("--by", required=True)
    k = sub.add_parser("check")
    k.add_argument("key")
    md = sub.add_parser("mode")
    md.add_argument("key")
    md.add_argument("new", nargs="?")
    w = sub.add_parser("weight")
    w.add_argument("key")
    w.add_argument("--apply", action="store_true")
    w.add_argument("--set", dest="new", default=None)
    w.add_argument("--by", default=None)
    w.add_argument("--reason", default="")
    w.add_argument("--json", action="store_true")
    fl = sub.add_parser("flag")
    fl.add_argument("key")
    fl.add_argument("action", choices=["set", "none", "allow"])
    fl.add_argument("value", nargs="?")
    fl.add_argument("--remove-by", default=None)
    fl.add_argument("--reason", default="")
    fl.add_argument("--by", default=None)
    fz = sub.add_parser("freeze")
    fz.add_argument("key")
    fz.add_argument("files")
    fz.add_argument("--by", required=True)
    ro = sub.add_parser("reopen")
    ro.add_argument("key")
    ro.add_argument("name")
    ro.add_argument("--by", required=True)
    ro.add_argument("--reason", default="")
    dp = sub.add_parser("deployed")
    dp.add_argument("key")
    dp.add_argument("--version", default=None)
    dp.add_argument("--timeout", type=float, default=600)
    dp.add_argument("--rolled-back", action="store_true")
    dp.add_argument("--by", default=None)
    dp.add_argument("--note", default="")
    q = sub.add_parser("status")
    q.add_argument("key")
    q.add_argument("--json", action="store_true")
    ls = sub.add_parser("list")
    ls.add_argument("--json", action="store_true")
    ls.add_argument("--all", action="store_true", help="closed tasks too")
    fi = sub.add_parser("finding")
    fi.add_argument("key")
    fi.add_argument("action", choices=["add", "control"])
    fi.add_argument("first", nargs="?")
    fi.add_argument("second", nargs="?")
    fi.add_argument("--slice", default=None)
    fi.add_argument("--round", type=int, default=None)
    rv = sub.add_parser("review")
    rv.add_argument("key")
    rv.add_argument("reviewer")
    rv.add_argument("verdict", choices=["pass", "fail"])
    rv.add_argument("--note", default="")
    cl = sub.add_parser("close")
    cl.add_argument("key")
    cl.add_argument("--by", default=None)
    cl.add_argument("--lesson", default=None)
    cl.add_argument("--base", default=None)
    cl.add_argument("--force", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if a.cmd == "list":
        return cmd_list(root, a.json, a.all)
    if not KEY.fullmatch(a.key):
        return fail(f"the key \"{a.key}\" does not match the pattern (e.g. PROJ-123, CHG-12, T-20261113-limit)", 2)
    if a.cmd == "start":
        if not a.title or not a.title.strip():
            return fail("give the title: tf task start <KEY> --title \"<title>\"", 2)
        if a.weight not in WEIGHTS:
            return fail(f"unknown weight \"{a.weight}\" — choose from: {', '.join(WEIGHTS)}", 2)
        if a.mode is not None and a.mode not in MODES:
            return fail(f"unknown mode \"{a.mode}\" — choose from: {', '.join(MODES)}", 2)
        if bool(a.change) != bool(a.cut):
            return fail("a cut task gives both: --change <CHG> and --cut <TSK>", 2)
        if a.change:
            if not PDI_KEY.fullmatch(a.change) or not PDI_KEY.fullmatch(a.cut):
                return fail("the change and cut keys in the LETTERS-number shape, e.g. --change CHG-12 --cut TSK-57", 2)
            if a.key != f"{a.change}-{a.cut}":
                return fail(f"a cut task has the key <CHG>-<TSK>: tf task start {a.change}-{a.cut} --title \"…\" "
                            f"--change {a.change} --cut {a.cut}", 2)
        return cmd_start(root, a.key, a.title.strip(), a.weight, a.mode, a.change, a.cut)
    if a.cmd == "finding":
        if a.slice and not SLICE.fullmatch(a.slice):
            return fail(f"the slice \"{a.slice}\" — expected form S1, S2…", 2)
        if a.action == "control" and not (a.first and re.fullmatch(r"F[1-9][0-9]*", a.first)):
            return fail(f"give the finding's identifier: tf task finding {a.key} control F1 \"<control>\"", 2)
        return cmd_finding(root, a.key, a.action, a.first, a.second, a.slice, a.round if a.round and a.round > 0 else None)
    if a.cmd == "review":
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,39}", a.reviewer):
            return fail(f"the reviewer \"{a.reviewer}\" — the agent's name, e.g. {', '.join(PANEL)}", 2)
        return cmd_review(root, a.key, a.reviewer, a.verdict, a.note)
    if a.cmd == "close":
        human = bool(a.by) and a.by.startswith("human:") and bool(ACTOR.fullmatch(a.by))
        if a.by and not ACTOR.fullmatch(a.by):
            return fail(f"the performer \"{a.by}\" — expected form: human:<id> or process:<id>", 2)
        if a.force and not human:
            return fail("closing without a confirmed merge is the human's decision: --force --by human:<id>", 2)
        lesson = one_line(a.lesson, 600) if a.lesson and a.lesson.strip() else None
        if lesson and not human:
            return fail("the human records a lesson: --lesson \"…\" --by human:<id>", 2)
        if lesson and "Instead:" not in lesson and "Zamiast tego:" not in lesson:
            return fail("a lesson has an \"Instead: <action>\" part — without it, it is a description of a mistake, not a rule "
                        "(format: **rule** — Context: … · Instead: … · Applies to: plan|implementation|review|all)", 2)
        return cmd_close(root, a.key, a.by, lesson, a.base, a.force)
    if a.cmd == "deployed":
        if a.rolled_back and not ((a.by or "").startswith("human:") and ACTOR.fullmatch(a.by)):
            return fail("rolling back a deployment is the human's decision: --rolled-back --by human:<id>", 2)
        if not 0 < a.timeout <= 86400:      # also rejects nan and inf
            return fail("smoke test time limit: a number of seconds from 1 to 86400", 2)
        return cmd_deployed(root, a.key, a.version, a.timeout, a.rolled_back, a.by, a.note)
    if a.cmd == "stage":
        if a.stage not in STAGES:
            return fail(f"unknown stage \"{a.stage}\" — in order: {', '.join(STAGES)}", 2)
        return cmd_stage(root, a.key, a.stage, a.force)
    if a.cmd == "check":
        return cmd_check(root, a.key)
    if a.cmd == "mode":
        return cmd_mode(root, a.key, a.new)
    if a.cmd == "weight":
        if a.apply and a.new is not None:
            return fail("give one: --apply (the factory's proposal) or --set <weight>", 2)
        return cmd_weight(root, a.key, a.apply, a.new, a.by, a.reason, a.json)
    if a.cmd == "flag":
        return cmd_flag(root, a.key, a.action, a.value, a.remove_by, a.reason, a.by)
    if a.cmd in ("freeze", "reopen"):
        if not a.by.startswith("human:") or not ACTOR.fullmatch(a.by):
            return fail(f"{a.cmd} is the human's decision: --by human:<id>", 2)
        if a.cmd == "freeze":
            files = [f.strip() for f in a.files.split(",") if f.strip()]
            return cmd_freeze(root, a.key, files, a.by) if files else fail("give the files to freeze", 2)
        if not a.reason.strip():
            return fail("give the reason: --reason \"<why the file changes>\"", 2)
        return cmd_reopen(root, a.key, a.name, a.by, " ".join(a.reason.split()))
    if a.cmd in ("artifact", "approve"):
        if not ACTOR.fullmatch(a.by):
            return fail(f"the performer \"{a.by}\" — expected form: <tool>/<version>, human:<id> or process:<id>", 2)
        if a.cmd == "approve":
            if not a.by.startswith("human:"):
                return fail("only the human approves: --by human:<id>", 2)
            return cmd_approve(root, a.key, a.name, a.by)
        if a.stage not in STAGES:
            return fail(f"unknown stage \"{a.stage}\" — in order: {', '.join(STAGES)}", 2)
        return cmd_artifact(root, a.key, a.name, a.stage, a.by, [f.strip() for f in a.inputs.split(",") if f.strip()])
    if a.cmd in ("slice", "verify"):
        if not SLICE.fullmatch(a.slice_id):
            return fail(f"the slice identifier \"{a.slice_id}\" — expected S1…S99", 2)
        if a.cmd == "slice":
            if a.state not in SLICE_STATES:
                return fail(f"unknown state \"{a.state}\" — choose from: {', '.join(SLICE_STATES)} "
                            "(verified comes from the evidence: tf task verify)", 2)
            return cmd_slice(root, a.key, a.slice_id, a.state, a.title, a.reason)
        files = [f.strip() for f in a.files.split(",") if f.strip()]
        if not files:
            return fail("give the slice's files: --files <file>[,<file>…] — without them the evidence is not tied to the code", 2)
        command = a.command
        if not command:   # by default the same command the quality gate watches
            try:
                gate = json.loads((root / ".claude" / "quality-gate.json").read_text(encoding="utf-8")).get("command")
            except (OSError, ValueError, AttributeError):
                gate = None
            command = gate if isinstance(gate, str) else (" ".join(map(shlex.quote, gate)) if gate else None)
        if not command:
            return fail("there is nothing to run: give --command or set the command in .claude/quality-gate.json "
                        "(tf onboard --yes)", 2)
        return cmd_verify(root, a.key, a.slice_id, command, files, a.timeout)
    return cmd_status(root, a.key, a.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
