#!/usr/bin/env python3
"""
tf bench: an A/B benchmark of the factory on reference tasks, before a release of changes to the /tf-task loop, hooks or
gates (the idea: Google's Harness² — the same task under matched conditions with the reference harness and with a
candidate harness, then compare the trajectories).

  python3 tools/bench.py tasks                                         # the reference tasks and what each must produce
  python3 tools/bench.py run --ref <git-ref|path> --cand <git-ref|path> [--task simple|medium|sensitive|all] [--runs N]
                             [--out DIR] [--budget USD] [--timeout MIN] [--model M] [--permission-mode acceptEdits]
                             [--packs none] [--layout default|plugin] [--fake-claude PATH] [--yes]
                             [--max-slower 0.2] [--max-more-turns 0.2] [--max-costlier 0.2] [--min-seconds 10]
                             [--no-proposals] [--proposals FILE]
  python3 tools/bench.py compare <out-dir> [the same thresholds and proposal options]   # recompute from bench.json

One run of one side: the fixture (tools/bench/fixture/, a tiny Python stdlib project with a unittest suite and a
quality-gate command) is copied to a fresh directory and committed with `git init`; the factory of that side is
installed into it with the normal installer (`core/factory/install.py --yes --packs none --layout default`, with
`TF_NO_PLUGIN_REGISTER=1`); then the task runs unattended:

  claude -p "/tf-task <task text> --auto --budget <USD>" --output-format json --permission-mode acceptEdits
         --max-budget-usd <USD> --strict-mcp-config --permission-prompts none [--model M]

(the same flags `tf work --once` uses, plus `--permission-prompts none`; CLI reference: code.claude.com/docs/en/cli-reference,
headless: code.claude.com/docs/en/headless). There is no CLI flag for a wall-clock limit, so the bench stops the process
after `--timeout` minutes (SIGINT, then SIGKILL). No API keys: the user's logged-in Claude Code CLI runs it. The runs
alternate ref, cand, ref, cand… so both sides see the same time of day and the same service load.

Collected per run (into <out>/<task>/<side>-r<n>/): the JSON result (cost, turns, duration), `run.json`, `task.json`,
`plan.md`, `report.md` and the gate log `.tf/logs/quality-gate-runs.jsonl`; the bench itself runs the fixture's tests
(`python3 run_tests.py`) and the task's hidden acceptance check (tools/bench/checks/<task>.py) on the result.
The comparison prints a table ref vs cand with the median over the runs and flags a regression when cand is clearly
worse: slower, more turns or costlier beyond the thresholds; slower verification or gate hook time; fewer green tests,
accepted results or commits; a weight outside the task's expectation; a gate missing on the sensitive task. It writes
<out>/bench-<date>.md and <out>/bench.json; the exit code is 1 when a regression was flagged.

Proposals: every flagged regression becomes an entry in the factory's `docs/proposals.md` (`--proposals FILE` elsewhere,
`--no-proposals` off) with a stable id (`BENCH-<hash of task, metric, ref and cand>`): a re-run of the same comparison
updates its entry instead of adding one, keeping a status the owner changed. The entry format is shared with the
proposals projects send (`## <id> — <title>`, then `Status:`, `Date:`, `Evidence:`, `Proposed change:`; bench entries
add `Ref:`, `Cand:`, `Task:` and `Metric:`). The bench only appends entries and updates its own ids.

The run costs tokens (one /tf-task loop per task, side and run): run it only with the owner's consent — without
`--fake-claude` it asks for a confirmation (`--yes` skips it). `--fake-claude <path>` runs a fake claude binary instead
(tools/bench/fake_claude.py), so the repository tests and CI never call the model. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "tools" / "bench"
FIXTURE = BENCH / "fixture"
TASKS = BENCH / "tasks"
CHECKS = BENCH / "checks"
PROPOSALS = ROOT / "docs" / "proposals.md"
PROPOSALS_NOTE = "> Entries come from projects and bench runs; review before acting."
SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT")   # a nested claude must not see a parent session
SLICE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*S\d+\b")
TEMPLATE_ROW = re.compile(r"S\d+\s*—\s*<")      # the plan template's placeholder row
# files whose change can move the loop's speed or its gates: the suspected cause of a regression
LOOP_PATHS = ("core/skills/tf-task/", "core/skills/tf/", "core/hooks/", "core/settings.json", "core/factory/task_",
              "core/factory/risk_triage.py", "core/factory/config.yaml", "core/factory/build.py", "core/factory/work.py",
              "core/factory/install.py", "core/factory/trace_check.py", "core/factory/spec_check.py", "core/agents/",
              "core/factory/traits/", "core/CLAUDE.md")
# metric → (label, how it is compared): "time" relative with --max-slower (and --min-seconds), "turns", "cost", "share"
METRICS = (("time_s", "wall time (s)", "time"), ("wall_s", "measured by the bench (s)", "info"), ("turns", "model turns", "turns"), ("cost_usd", "cost (USD)", "cost"),
           ("requests", "model requests (report)", "info"), ("verify_s", "verify time (s)", "time"),
           ("gate_s", "gate hook time (s)", "time"), ("gate_runs", "gate hook runs", "info"),
           ("slices", "slices", "info"), ("weight", "weight", "info"), ("approach", "approach", "info"),
           ("escalations", "escalations", "info"), ("tests_green", "tests green", "share"),
           ("accepted", "hidden check passed", "share"), ("commits", "code commits", "info"),
           ("committed", "commit produced", "share"), ("pr", "PR opened", "info"), ("stop", "stop code", "info"),
           ("gates", "gates that fired", "info"))


# ---------------------------------------------------------------------------------------------------------------- tasks

def load_tasks() -> dict[str, dict]:
    expect = json.loads((TASKS / "expect.json").read_text(encoding="utf-8"))
    order = [k for k in expect if not k.startswith("_")]
    files = sorted(TASKS.glob("*.txt"), key=lambda p: (order.index(p.stem) if p.stem in order else len(order), p.stem))
    return {p.stem: {"text": p.read_text(encoding="utf-8").strip(), "expect": expect.get(p.stem, {})} for p in files}


def cmd_tasks() -> int:
    for name, t in load_tasks().items():
        e = t["expect"]
        print(f"{name}: {t['text'].splitlines()[0]}\n  expects weight {'/'.join(e.get('weights') or ['any'])}"
              + (f", {e['slices']} slice(s)" if e.get("slices") else "")
              + (f", a gate: {' or '.join(e['gate_any'])}" if e.get("gate_any") else "")
              + (", the hidden check passes" if e.get("accept") else ""))
    return 0


# ----------------------------------------------------------------------------------------------------- the two sides

def git(cwd: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=tf bench", "-c", "user.email=bench@example.invalid", *args], cwd=cwd,
                          capture_output=True, text=True, check=check)


def resolve_side(spec: str, work: Path, name: str) -> dict:
    """A side of the comparison: a factory checkout path (used as it is) or a git ref of this repository (exported with
    `git archive` into <work>/factory-<name>). {"spec", "dir", "sha"}; SystemExit with a message when it is neither."""
    p = Path(spec).expanduser()
    if p.is_dir():
        if not (p / "core" / "factory" / "install.py").is_file():
            sys.exit(f"✗ {spec}: not a factory checkout (no core/factory/install.py)")
        r = git(p, "rev-parse", "HEAD")
        sha = r.stdout.strip() if r.returncode == 0 else None
        if sha and git(p, "status", "--porcelain").stdout.strip():
            sha += "+dirty"
        return {"spec": spec, "dir": str(p.resolve()), "sha": sha}
    r = git(ROOT, "rev-parse", "--verify", f"{spec}^{{commit}}")
    if r.returncode != 0:
        sys.exit(f"✗ {spec}: neither a directory nor a git ref of {ROOT}")
    sha = r.stdout.strip()
    dest = work / f"factory-{name}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "archive", "--format=tar", sha], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        try:
            tf.extractall(dest, filter="data")
        except TypeError:   # Python < 3.12 without extraction filters: git archive of our own repo is trusted
            tf.extractall(dest)
    return {"spec": spec, "dir": str(dest), "sha": sha}


def short(sha: str | None) -> str:
    if not sha:
        return "unknown"
    head, plus, rest = sha.partition("+")
    return head[:12] + plus + rest


def clean_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}
    env.update(TF_NO_PLUGIN_REGISTER="1", PYTHONDONTWRITEBYTECODE="1", **(extra or {}))
    return env


def prepare_project(dest: Path) -> Path:
    """The fixture in a fresh git repository on `main`, with its gate config in .claude/quality-gate.json, committed."""
    shutil.copytree(FIXTURE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / ".claude").mkdir(exist_ok=True)
    (dest / "_quality-gate.json").rename(dest / ".claude" / "quality-gate.json")
    git(dest, "init", "-q", "-b", "main", check=True)
    git(dest, "add", "-A", check=True)
    git(dest, "commit", "-qm", "init: the bench fixture", check=True)
    return dest


def install_factory(factory: Path, project: Path, packs: str, layout: str) -> dict:
    """The normal installer of that side; an older installer without --layout gets no --layout."""
    installer = factory / "core" / "factory" / "install.py"
    cmd = [sys.executable, str(installer), str(project), "--yes", "--packs", packs]
    if "--layout" in installer.read_text(encoding="utf-8", errors="replace"):
        cmd += ["--layout", layout]
    t0 = time.monotonic()
    r = subprocess.run(cmd, cwd=project, capture_output=True, text=True, env=clean_env(), timeout=600)
    (project.parent / "install.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    return {"ok": r.returncode == 0, "s": round(time.monotonic() - t0, 1),
            "tree_clean": not git(project, "status", "--porcelain").stdout.strip()}


def claude_base(fake: str | None, claude: str | None) -> list[str]:
    if fake:
        f = Path(fake).resolve()
        return [sys.executable, str(f)] if f.suffix == ".py" else [str(f)]
    return shlex.split(claude or "claude")


def agent_command(base: list[str], task_text: str, project: Path, o: argparse.Namespace) -> list[str]:
    plugin = []
    command = "/tf-task"
    if o.layout == "plugin":
        plugin = ["--plugin-dir", str(project / ".tf" / "plugin"),
                  "--settings", str(project / ".tf" / "plugin" / "session-settings.json")]
        command = "/tf:tf-task"
    budget = f"{o.budget:g}"
    argv = [*base, *plugin, "-p", f"{command} {task_text}\n\n--auto --budget {budget}", "--output-format", "json",
            "--permission-mode", o.permission_mode, "--max-budget-usd", budget, "--strict-mcp-config"]
    if o.permission_prompts:
        argv += ["--permission-prompts", "none"]
    if o.model:
        argv += ["--model", o.model]
    return argv


def run_agent(argv: list[str], cwd: Path, env: dict, timeout_s: float) -> dict:
    """The agent process with a wall-clock limit: SIGINT first (the turn ends cleanly), SIGKILL after 30 s."""
    t0 = time.monotonic()
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        return {"rc": 127, "stdout": "", "stderr": str(e), "wall_s": 0.0, "timed_out": False}
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            proc.send_signal(signal.SIGINT)
            out, err = proc.communicate(timeout=30)
        except (subprocess.TimeoutExpired, OSError, ValueError):
            proc.kill()
            out, err = proc.communicate()
    return {"rc": proc.returncode, "stdout": out or "", "stderr": err or "", "wall_s": round(time.monotonic() - t0, 1),
            "timed_out": timed_out}


# ------------------------------------------------------------------------------------------------------- collecting

def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def parse_result(stdout: str) -> dict:
    """The `--output-format json` result: one JSON object; lenient about text around it (the last object wins)."""
    text = stdout.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):   # some versions print the message list: take the result message
            data = next((m for m in reversed(data) if isinstance(m, dict) and m.get("type") == "result"), {})
        return data if isinstance(data, dict) else {}
    except ValueError:
        pass
    for line in reversed(text.splitlines()):
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def report_numbers(text: str) -> dict:
    """Numbers from report.md (run_report.py finish): the time, model requests and the "Where the time went" section."""
    out: dict = {}
    m = re.search(r"^- Time: (\d+) min (\d+) s", text, re.M)
    if m:
        out["report_time_s"] = int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"^- Model requests: (\d+)", text, re.M)
    if m:
        out["requests"] = int(m.group(1))
    m = re.search(r"^## Where the time went\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if m:
        out["time_went"] = m.group(1).strip()
    return out


def latest_run(project: Path) -> Path | None:
    runs = [p for p in (project / ".tf" / "runs").glob("*/run.json") if p.parent.name != "cuts"]
    return max(runs, key=lambda p: p.stat().st_mtime).parent if runs else None


def collect(project: Path, agent: dict, dest: Path, task: str) -> dict:
    """The run's measures from its files; the files themselves are copied to `dest`."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "claude.json").write_text(agent.get("stdout") or "", encoding="utf-8")
    (dest / "claude.stderr").write_text(agent.get("stderr") or "", encoding="utf-8")
    res = parse_result(agent.get("stdout") or "")
    m: dict = {"rc": agent.get("rc"), "wall_s": agent.get("wall_s"), "timed_out": agent.get("timed_out", False),
               "is_error": res.get("is_error"), "turns": res.get("num_turns"), "cost_usd": res.get("total_cost_usd"),
               "duration_s": round(res["duration_ms"] / 1000, 1) if isinstance(res.get("duration_ms"), (int, float))
               else None, "permission_denials": len(res.get("permission_denials") or [])}
    m["time_s"] = m["duration_s"] if m["duration_s"] is not None else m["wall_s"]
    run_dir = latest_run(project)
    meta = read_json(run_dir / "run.json") if run_dir else {}
    key = meta.get("key") or (run_dir.name if run_dir else None)
    task_dir = project / (meta.get("task_dir") or f"docs/project/changes/{key}") if key else None
    tj = read_json(task_dir / "task.json") if task_dir else {}
    for src, name in ((run_dir and run_dir / "run.json", "run.json"), (task_dir and task_dir / "task.json", "task.json"),
                      (task_dir and task_dir / "plan.md", "plan.md"), (task_dir and task_dir / "report.md", "report.md"),
                      (project / ".tf" / "logs" / "quality-gate-runs.jsonl", "quality-gate-runs.jsonl")):
        if src and Path(src).is_file():
            shutil.copyfile(src, dest / name)
    m["key"], m["stage"] = key, meta.get("stage")
    m["stop"] = meta.get("stop_code") or (meta.get("needs") if meta.get("stage") == "needs" else None)
    m["pr"] = meta.get("pr")
    m["weight"] = tj.get("weight")
    app = tj.get("approach") if isinstance(tj.get("approach"), dict) else {}
    m["approach"] = app.get("weight")
    m["escalations"] = sum(1 for a in tj.get("approach_log") or [] if isinstance(a, dict) and a.get("escalated"))
    plan = (task_dir / "plan.md").read_text(encoding="utf-8", errors="replace") if task_dir and (task_dir / "plan.md").is_file() else ""
    rows = [ln for ln in plan.splitlines() if SLICE.match(ln) and not TEMPLATE_ROW.search(ln)]
    m["slices"] = len(rows)
    m["slices_done"] = sum(1 for ln in rows if re.match(r"^\s*-\s*\[[xX]\]", ln))
    verify = runs = 0.0
    for f in (task_dir / "evidence").glob("S*-*.json") if task_dir else []:
        ev = read_json(f)
        if isinstance(ev.get("duration_s"), (int, float)):
            verify += ev["duration_s"]
            runs += 1
    m["verify_s"], m["verify_runs"] = round(verify, 1), int(runs)
    gate = gate_runs = gate_fail = 0
    try:
        rows = (project / ".tf" / "logs" / "quality-gate-runs.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        rows = []
    for ln in rows:
        try:
            row = json.loads(ln)
        except ValueError:
            continue
        if isinstance(row, dict) and isinstance(row.get("duration_s"), (int, float)):
            gate += row["duration_s"]
            gate_runs += 1
            gate_fail += 0 if row.get("ok") else 1
    m["gate_s"], m["gate_runs"], m["gate_fails"] = round(gate, 1), gate_runs, gate_fail
    rep = (dest / "report.md").read_text(encoding="utf-8") if (dest / "report.md").is_file() else ""
    m.update({k: v for k, v in report_numbers(rep).items() if k != "time_went"})
    m.setdefault("requests", None)
    m["report"] = bool(rep)
    # git: code commits (app/ or tests/ changed after the fixture's commit), on any branch
    code = git(project, "rev-list", "--all", "--count", "--", "app", "tests", "run_tests.py").stdout.strip()
    m["commits"] = max(0, int(code or 1) - 1)
    m["committed"] = m["commits"] > 0
    m["branch"] = git(project, "branch", "--show-current").stdout.strip()
    t = subprocess.run([sys.executable, "run_tests.py"], cwd=project, capture_output=True, text=True, timeout=300,
                       env=clean_env())
    m["tests_green"] = t.returncode == 0
    check = CHECKS / f"{task}.py"
    if check.is_file():
        a = subprocess.run([sys.executable, "-I", str(check), str(project)], cwd=dest, capture_output=True, text=True,
                           timeout=120, env=clean_env())
        m["accepted"] = a.returncode == 0
        (dest / "accept.txt").write_text(a.stdout + a.stderr, encoding="utf-8")
    else:
        m["accepted"] = None
    gates = []
    if gate_runs:
        gates.append("quality-gate")
    if runs:
        gates.append("verify")
    if run_dir and (run_dir / "security").is_dir():
        gates.append("security-scan")
    rounds = (meta.get("current") or {}).get("rounds") if isinstance(meta.get("current"), dict) else None
    if tj.get("findings") or any(isinstance(r, dict) and r.get("scope") in ("pass", "fail") for r in rounds or []):
        gates.append("scope-review")
    for name in sorted(tj.get("reviews") or {}):
        gates.append(f"panel:{name}")
    if m["stop"]:
        gates.append(f"stop:{m['stop']}")
    m["gates"] = gates
    (dest / "metrics.json").write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return m


def misses(task: dict, m: dict) -> list[str]:
    """What a run did differently from the task's expectation (tools/bench/tasks/expect.json)."""
    e, out = task.get("expect") or {}, []
    if e.get("weights") and m.get("weight") not in e["weights"]:
        out.append(f"weight {m.get('weight')} (expected {'/'.join(e['weights'])})")
    if e.get("slices") and m.get("slices") != e["slices"]:
        out.append(f"{m.get('slices')} slice(s) (expected {e['slices']})")
    if e.get("gate_any") and not set(e["gate_any"]) & set(m.get("gates") or []):
        out.append(f"no gate of {', '.join(e['gate_any'])}")
    if e.get("accept") and not m.get("accepted"):
        out.append("the hidden check failed")
    return out


# ----------------------------------------------------------------------------------------------------- comparing

def median(values: list) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return round(statistics.median(nums), 4) if nums else None


def summarize(runs: list[dict], task: dict) -> dict:
    """The side's runs of one task: medians of numbers, the share of yes for booleans, the values seen otherwise."""
    out: dict = {"runs": len(runs)}
    for key, _, kind in METRICS:
        vals = [r.get(key) for r in runs]
        if kind == "share":
            out[key] = [sum(1 for v in vals if v), len(vals)]
        elif key == "gates":
            seen = sorted({g for v in vals for g in (v or [])})
            out[key] = seen
        elif key in ("weight", "approach", "stop", "pr"):
            out[key] = sorted({str(v) for v in vals if v not in (None, "")})
        else:
            out[key] = median(vals)
    out["misses"] = sorted({x for r in runs for x in misses(task, r)})
    out["gate_missing"] = bool((task.get("expect") or {}).get("gate_any")) and any(
        not set(task["expect"]["gate_any"]) & set(r.get("gates") or []) for r in runs)
    out["weight_wrong"] = bool((task.get("expect") or {}).get("weights")) and any(
        r.get("weight") not in task["expect"]["weights"] for r in runs)
    out["slices_wrong"] = bool((task.get("expect") or {}).get("slices")) and any(
        r.get("slices") != task["expect"]["slices"] for r in runs)
    return out


def worse(ref, cand, limit: float, floor: float = 0.0) -> bool:
    if not isinstance(ref, (int, float)) or not isinstance(cand, (int, float)):
        return False
    if cand - ref <= floor:
        return False
    return ref <= 0 or (cand - ref) / ref > limit


def compare(name: str, ref: dict, cand: dict, o) -> list[dict]:
    """The regressions of cand against ref on one task: [{"task", "metric", "label", "ref", "cand", "why"}]."""
    out = []

    def flag(metric, label, why):
        out.append({"task": name, "metric": metric, "label": label, "ref": shown(ref.get(metric)),
                    "cand": shown(cand.get(metric)), "why": why})

    limits = {"time": (o.max_slower, o.min_seconds), "turns": (o.max_more_turns, 0.0), "cost": (o.max_costlier, 0.0)}
    for key, label, kind in METRICS:
        if kind in limits and worse(ref.get(key), cand.get(key), *limits[kind]):
            pct = (f"+{100 * (cand[key] - ref[key]) / ref[key]:.0f}%" if ref[key] else "from 0")
            flag(key, label, f"{label}: {shown(ref[key])} → {shown(cand[key])} ({pct}, limit +{100 * limits[kind][0]:.0f}%)")
        elif kind == "share":
            (rk, rn), (ck, cn) = ref.get(key) or [0, 0], cand.get(key) or [0, 0]
            if rn and cn and ck / cn < rk / rn:
                flag(key, label, f"{label}: {rk}/{rn} → {ck}/{cn}")
    if cand.get("gate_missing"):
        flag("gates", "gates that fired", "a required gate did not fire on cand: " + ", ".join(cand.get("misses") or []))
    if cand.get("weight_wrong") and (cand.get("gate_missing") or not ref.get("weight_wrong")):
        flag("weight", "weight", f"weight {', '.join(cand.get('weight') or ['none'])} outside the task's expectation")
    if cand.get("slices_wrong") and not ref.get("slices_wrong"):
        flag("slices", "slices", f"slices {shown(ref.get('slices'))} → {shown(cand.get('slices'))} (ref met the expectation)")
    return out


def shown(v) -> str:
    if v is None or v == []:
        return "—"
    if isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) for x in v):
        return f"{v[0]}/{v[1]}"
    if isinstance(v, list):
        return ", ".join(map(str, v))
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 10 else f"{v:.1f}".rstrip("0").rstrip(".")
    return str(v)


def delta(ref, cand) -> str:
    if isinstance(ref, (int, float)) and isinstance(cand, (int, float)) and not isinstance(ref, bool) and ref:
        return f"{100 * (cand - ref) / ref:+.0f}%"
    return ""


def report_md(data: dict, regressions: list[dict], proposals_line: str) -> str:
    ref, cand = data["ref"], data["cand"]
    lines = [f"# Factory bench {data['date']}", "",
             f"- ref: `{ref['spec']}` ({short(ref.get('sha'))}) · cand: `{cand['spec']}` ({short(cand.get('sha'))})",
             f"- runs per side and task: {data['runs']} · claude: `{data['claude']}` · budget {data['budget']} USD per run",
             f"- thresholds: slower > +{100 * data['thresholds']['max_slower']:.0f}% (and > {data['thresholds']['min_seconds']:g} s), "
             f"more turns > +{100 * data['thresholds']['max_more_turns']:.0f}%, costlier > "
             f"+{100 * data['thresholds']['max_costlier']:.0f}%", "",
             "Values are medians over the runs; `k/n` is how many runs out of n had it.", ""]
    for name, t in data["tasks"].items():
        lines += [f"## {name}", "", "| Metric | ref | cand | Δ | |", "|---|---|---|---|---|"]
        flagged = {r["metric"] for r in regressions if r["task"] == name}
        for key, label, _ in METRICS:
            r, c = t["ref"].get(key), t["cand"].get(key)
            lines.append(f"| {label} | {shown(r)} | {shown(c)} | {delta(r, c)} | {'**regression**' if key in flagged else ''} |")
        for side in ("ref", "cand"):
            if t[side].get("misses"):
                lines.append(f"\n- {side} missed the expectation: {'; '.join(t[side]['misses'])}")
        lines += ["", "Runs: " + ", ".join(f"`{p}`" for p in t.get("run_dirs", [])), ""]
    lines += ["## Verdict", ""]
    lines += ([f"- **{r['task']}**: {r['why']}" for r in regressions] or ["- no regression: cand is not clearly worse than ref"])
    lines += ["", proposals_line, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------- proposals

def changed_loop_files(ref: dict, cand: dict) -> list[str] | None:
    """Files changed between ref and cand that touch the loop, hooks or gates (`git diff --name-only ref..cand`; a cand
    checkout with uncommitted changes: its working tree against ref); None when git cannot say."""
    a, b = (ref.get("sha") or ""), (cand.get("sha") or "")
    if not a or "+" in a or not b:
        return None
    if "+" in b:
        r = git(Path(cand["dir"]), "diff", "--name-only", a)
    else:
        r = git(ROOT, "diff", "--name-only", f"{a}..{b}")
    if r.returncode != 0:
        return None
    return [f for f in r.stdout.split() if f.startswith(LOOP_PATHS)]


def proposal_id(reg: dict, ref: dict, cand: dict) -> str:
    raw = "|".join((reg["task"], reg["metric"], ref.get("sha") or ref["spec"], cand.get("sha") or cand["spec"]))
    return "BENCH-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def proposal_entry(pid: str, reg: dict, data: dict, report: Path, run_dirs: list[str], status: str = "open") -> str:
    ref, cand = data["ref"], data["cand"]
    files = changed_loop_files(ref, cand)
    cause = ("the files changed between ref and cand that touch the loop, hooks or gates: " + ", ".join(files)
             if files else "unknown (no file of the loop, hooks or gates changed between ref and cand)" if files == []
             else "unknown (git cannot compare ref and cand)")
    return "\n".join([
        f"## {pid} — {reg['task']}: {reg['label']} regressed ({short(ref.get('sha'))} → {short(cand.get('sha'))})", "",
        f"Status: {status}",
        f"Date: {data['date']}",
        f"Ref: {ref['spec']} ({ref.get('sha') or 'unknown'})",
        f"Cand: {cand['spec']} ({cand.get('sha') or 'unknown'})",
        f"Task: {reg['task']}",
        f"Metric: {reg['label']}: {reg['ref']} → {reg['cand']}",
        f"Evidence: {reg['why']}; the table in {report}; runs: {', '.join(run_dirs) or '—'}",
        f"Proposed change: find and fix the cause before releasing cand; suspected cause: {cause}.", ""])


def write_proposals(path: Path, regressions: list[dict], data: dict, report: Path) -> list[tuple[str, str]]:
    """Appends an entry per regression or updates the bench's own entry with the same id (its Status kept); other
    entries stay byte for byte. [(id, "added"|"updated")]."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if "review before acting" not in text.lower():     # the header note, once, at the top
        if text.startswith("# "):
            head, _, rest = text.partition("\n")
            text = f"{head}\n\n{PROPOSALS_NOTE}\n\n{rest.lstrip(chr(10))}"
        else:
            text = f"# Factory proposals\n\n{PROPOSALS_NOTE}\n\n{text}"
    done = []
    for reg in regressions:
        pid = proposal_id(reg, data["ref"], data["cand"])
        runs = data["tasks"].get(reg["task"], {}).get("run_dirs", [])
        m = re.search(rf"^## {re.escape(pid)} — .*?(?=^## |\Z)", text, re.M | re.S)
        if m:
            st = re.search(r"^Status: (.+)$", m.group(0), re.M)
            entry = proposal_entry(pid, reg, data, report, runs, st.group(1).strip() if st else "open")
            text = text[:m.start()] + entry + ("\n" if text[m.end():] else "") + text[m.end():]
            done.append((pid, "updated"))
        else:
            text = text.rstrip("\n") + "\n\n" + proposal_entry(pid, reg, data, report, runs)
            done.append((pid, "added"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
    return done


# ----------------------------------------------------------------------------------------------------------- run

def finish(data: dict, out: Path, o) -> int:
    """Summaries, the comparison, bench-<date>.md, bench.json and the proposals; exit code 1 on a regression."""
    tasks = load_tasks()
    data["thresholds"] = {k: getattr(o, k) for k in ("max_slower", "max_more_turns", "max_costlier", "min_seconds")}
    regressions = []
    for name, t in data["tasks"].items():
        t["ref"] = summarize(t["runs"]["ref"], tasks.get(name, {}))
        t["cand"] = summarize(t["runs"]["cand"], tasks.get(name, {}))
        regressions += compare(name, t["ref"], t["cand"], o)
    report = out / f"bench-{data['date']}.md"
    if not regressions:
        line = "Proposals: none — a clean comparison adds nothing to docs/proposals.md."
    elif o.no_proposals:
        line = f"Proposals: {len(regressions)} regression(s), not written (--no-proposals)."
    else:
        path = Path(o.proposals) if o.proposals else PROPOSALS
        done = write_proposals(path, regressions, data, report)
        line = f"Proposals in {path}: " + ", ".join(f"{pid} ({how})" for pid, how in done) + "."
    report.write_text(report_md(data, regressions, line), encoding="utf-8")
    data["regressions"] = regressions
    (out / "bench.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))
    print(f"Report: {report}")
    return 1 if regressions else 0


def consent(o, n_runs: int) -> bool:
    if o.fake_claude or o.yes:
        return True
    msg = (f"tf bench runs {n_runs} unattended /tf-task loop(s) with the real claude CLI (your subscription), up to "
           f"{o.budget:g} USD each. Continue? [y/N] ")
    if not sys.stdin.isatty():
        print("✗ the bench costs tokens: confirm with --yes (only with the owner's consent), or use --fake-claude")
        return False
    return input(msg).strip().lower() in ("y", "yes")


def cmd_run(o) -> int:
    tasks = load_tasks()
    names = list(tasks) if o.task == "all" else [o.task]
    unknown = [n for n in names if n not in tasks]
    if unknown:
        print(f"✗ unknown task {', '.join(unknown)}; the tasks: {', '.join(tasks)}")
        return 2
    if not consent(o, len(names) * 2 * o.runs):
        return 2
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(o.out).resolve() if o.out else ROOT / ".work" / "bench" / stamp
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="tf-bench-"))
    base = claude_base(o.fake_claude, o.claude)
    data = {"date": date.today().isoformat(), "runs": o.runs, "budget": o.budget, "claude": shlex.join(base),
            "out": str(out), "tasks": {}}
    try:
        data["ref"] = resolve_side(o.ref, work, "ref")
        data["cand"] = resolve_side(o.cand, work, "cand")
        for name in names:
            t = data["tasks"][name] = {"runs": {"ref": [], "cand": []}, "run_dirs": []}
            for n in range(1, o.runs + 1):
                for side in ("ref", "cand"):        # alternating: both sides see the same conditions
                    proj_root = work / name / f"{side}-r{n}"
                    project = prepare_project(proj_root / "shop")
                    inst = install_factory(Path(data[side]["dir"]), project, o.packs, o.layout)
                    dest = out / name / f"{side}-r{n}"
                    if not inst["ok"]:
                        print(f"✗ {name} {side} r{n}: the install failed — {proj_root / 'install.log'}")
                        dest.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(proj_root / "install.log", dest / "install.log")
                        return 2
                    argv = agent_command(base, tasks[name]["text"], project, o)
                    print(f"• {name} {side} r{n}: /tf-task in {project}", flush=True)
                    agent = run_agent(argv, project, clean_env({"TF_BENCH_TASK": name, "TF_BENCH_SIDE": side,
                                                                "TF_BENCH_RUN": str(n)}), o.timeout * 60)
                    m = collect(project, agent, dest, name)
                    m.update(install_s=inst["s"], tree_clean=inst["tree_clean"])
                    shutil.copyfile(proj_root / "install.log", dest / "install.log")
                    t["runs"][side].append(m)
                    t["run_dirs"].append(str(dest))
                    print(f"  {m['time_s']} s · turns {m['turns']} · weight {m['weight']} · slices {m['slices']} · "
                          f"tests {'green' if m['tests_green'] else 'red'} · gates {', '.join(m['gates']) or '—'}",
                          flush=True)
                    if not o.keep:
                        shutil.rmtree(proj_root, ignore_errors=True)
        return finish(data, out, o)
    finally:
        if not o.keep:
            shutil.rmtree(work, ignore_errors=True)
        else:
            print(f"Kept the projects in {work}")


def cmd_compare(o) -> int:
    out = Path(o.dir).resolve()
    data = read_json(out / "bench.json")
    if not data.get("tasks"):
        print(f"✗ {out / 'bench.json'}: no bench result")
        return 2
    return finish(data, out, o)


def add_thresholds(p: argparse.ArgumentParser) -> None:
    p.add_argument("--max-slower", type=float, default=0.20, help="flag cand slower than ref by more than this share")
    p.add_argument("--max-more-turns", type=float, default=0.20, help="flag cand with more turns by more than this share")
    p.add_argument("--max-costlier", type=float, default=0.20, help="flag cand costlier by more than this share")
    p.add_argument("--min-seconds", type=float, default=10.0, help="ignore time differences up to this many seconds")
    p.add_argument("--no-proposals", action="store_true", help="do not write regressions to docs/proposals.md")
    p.add_argument("--proposals", default=None, help="the proposals file (default: docs/proposals.md of this repo)")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tasks")
    r = sub.add_parser("run")
    r.add_argument("--ref", required=True)
    r.add_argument("--cand", required=True)
    r.add_argument("--task", default="all")
    r.add_argument("--runs", type=int, default=1)
    r.add_argument("--out", default=None)
    r.add_argument("--budget", type=float, default=5.0, help="USD per run: --max-budget-usd and /tf-task --budget")
    r.add_argument("--timeout", type=float, default=30.0, help="minutes per run")
    r.add_argument("--model", default=None)
    r.add_argument("--permission-mode", default="acceptEdits")
    r.add_argument("--no-permission-prompts-flag", dest="permission_prompts", action="store_false",
                   help="omit --permission-prompts none (Claude Code older than v2.1.259)")
    r.add_argument("--packs", default="none")
    r.add_argument("--layout", choices=("default", "plugin"), default="default")
    r.add_argument("--claude", default=None, help="the claude command (default: claude)")
    r.add_argument("--fake-claude", default=None, help="a fake claude binary (tests, CI): no model is called")
    r.add_argument("--yes", action="store_true", help="the owner consented to the token cost")
    r.add_argument("--keep", action="store_true", help="keep the temporary projects")
    add_thresholds(r)
    c = sub.add_parser("compare")
    c.add_argument("dir")
    add_thresholds(c)
    o = ap.parse_args(argv[1:])
    if o.cmd == "tasks":
        return cmd_tasks()
    if o.cmd == "run":
        if o.runs < 1:
            ap.error("--runs must be at least 1")
        return cmd_run(o)
    return cmd_compare(o)


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv))
