"""The model engine of tf stress: one unattended /tf-task (or a plain session) per scenario in a copy of the fixture
with the scenario's faults, recorded as stream-json with arrival times; the profiler turns the stream into a timeline
and a time breakdown (model, factory scripts, tests, scan, git, subagents, hooks, wasted calls); the evaluator checks
the scenario's expectations against the result."""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from common import CHECKS, STRESS, apply_faults, clean_env, copy_project, duration, git, run, stats, template

PY = sys.executable

# --- the run ----------------------------------------------------------------------------------------------------

def install_probe(proj: Path) -> None:
    """Every hook registration becomes `python3 .stress/hookprobe.py <hook> [args]` (timing without behaviour change)."""
    d = proj / ".stress"
    d.mkdir(exist_ok=True)
    shutil.copy2(STRESS / "lib" / "hookprobe.py", d / "hookprobe.py")
    for name in ("settings.local.json", "settings.json"):
        f = proj / ".claude" / name
        if not f.exists():
            continue
        s = json.loads(f.read_text())
        for arr in (s.get("hooks") or {}).values():
            for m in arr:
                for h in m.get("hooks", []):
                    if h.get("args") and "hookprobe.py" not in h["args"][0]:
                        h["args"] = ["${CLAUDE_PROJECT_DIR}/.stress/hookprobe.py", *h["args"]]
                        if h.get("timeout"):
                            h["timeout"] = int(h["timeout"]) + 5
        f.write_text(json.dumps(s, indent=2))


def prompt_for(sc: dict, layout: str) -> str:
    pfx = "/tf:tf-task" if layout == "plugin" else "/tf-task"
    text = sc["input"].strip() if isinstance(sc.get("input"), str) else ""
    mode = sc.get("mode", "auto")
    budget = sc.get("budget", 3)
    if mode == "plain":
        return text
    if mode == "quick":
        return f"{pfx} quick {text}"
    if mode == "plan":
        return f"{pfx} {text} --plan"
    return f"{pfx} {text} --auto --budget {budget}"


def run_claude(argv: list[str], cwd: Path, env: dict, timeout_s: float, out: Path) -> dict:
    """Runs claude with stream-json; every line gets its arrival time (seconds since start) as `_t`."""
    t0 = time.monotonic()
    p = subprocess.Popen(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    killed = False
    with open(out, "w", encoding="utf-8") as fh:
        while True:
            line = p.stdout.readline()
            if not line:
                break
            now = time.monotonic() - t0
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "stream_event":
                ev = e.get("event") or {}
                if ev.get("type") != "message_start":
                    continue                      # keep only the start of each model response (its ttft)
            e["_t"] = round(now, 3)
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
            if now > timeout_s and not killed:
                os.killpg(p.pid, signal.SIGINT)
                killed = True
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
    return {"wall_s": round(time.monotonic() - t0, 2), "rc": p.returncode, "killed": killed,
            "stderr": (p.stderr.read() or "")[-1500:]}


# --- the profiler -----------------------------------------------------------------------------------------------

SCRIPT_RE = re.compile(r"(?:^|[\s/])(run_state|run_report|intake|security_scan|plan_drift|pr_budget|ui_snap|task_weight|"
                       r"project_record|tf|requirements_lint|semver|skill_gate|onboard|dashboard_live)\.py\b(?:\s+(?:\S+/)*?"
                       r"(?:(?:\.tf/runs/\S+|--\S+|\"[^\"]*\")\s+)*([a-z][\w-]*))?")
TEST_RE = re.compile(r"\b(npm (run )?test|node --test|verify\.sh|pytest|run_tests\.py|unittest|test_lock\.py|vitest|jest|go test)\b")


def classify(tool: str, inp: dict) -> tuple[str, str]:
    """(category, label) of one tool call."""
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        m = SCRIPT_RE.search(cmd)
        if m and "test_lock.py" not in cmd:
            sub = m.group(2) or ""
            if m.group(1) == "run_state" and sub in ("finish-slice", "verify"):
                return "factory: verify+scan+commit", f"run_state.py {sub}"
            return "factory scripts", f"{m.group(1)}.py {sub}".strip()
        if TEST_RE.search(cmd):
            return "tests / verify", TEST_RE.search(cmd).group(0)
        if re.match(r"\s*semgrep\b", cmd):
            return "scan", "semgrep"
        if re.match(r"\s*git\b", cmd):
            return "git", "git " + (cmd.split()[1] if len(cmd.split()) > 1 else "")
        if re.match(r"\s*(gh)\b", cmd):
            return "git", "gh"
        return "bash other", cmd.split()[0] if cmd.split() else "bash"
    if tool in ("Read", "Grep", "Glob", "NotebookRead", "LS"):
        return "read / search", tool
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return "edit", tool
    if tool in ("Agent", "Task"):
        return "subagents", f"agent:{inp.get('subagent_type') or '?'}"
    if tool == "Skill":
        return "skill load", f"skill:{inp.get('skill') or inp.get('command') or '?'}"
    if tool in ("TodoWrite", "TaskCreate", "TaskUpdate", "ToolSearch"):
        return "bookkeeping", tool
    return "other tools", tool


PHASE_RE = [
    (re.compile(r"run_state\.py\s+stage\s+\S+\s+(\w+)"), lambda m: m.group(1)),
    (re.compile(r"run_state\.py\s+spec\b"), lambda m: "spec"),
    (re.compile(r"run_state\.py\s+approach\b"), lambda m: "plan"),
    (re.compile(r"run_state\.py\s+(?:step|finish-slice|verify|tick|block|finding)\s+\S+\s+(S\d+)"), lambda m: m.group(1)),
    (re.compile(r"run_state\.py\s+(?:pr-body|trace|panel)\b|plan_drift\.py|pr_budget\.py"), lambda m: "pr"),
    (re.compile(r"run_report\.py\s+finish\b"), lambda m: "finish"),
    (re.compile(r"run_report\.py\s+start\b"), lambda m: "intake"),
]


def profile(stream: Path, hooks_log: Path | None = None) -> dict:
    events = [json.loads(l) for l in stream.read_text(encoding="utf-8").splitlines() if l.strip()]
    msg_end, msg_first, spans, models, ttft = {}, {}, [], [], []
    uses = {}
    cursor, phase, phase_marks = 0.0, "startup", [(0.0, "startup")]
    result = {}
    sub_turns = 0
    first_tool_t = None
    denials = []
    for e in events:
        t = e.get("_t", 0.0)
        typ = e.get("type")
        parent = e.get("parent_tool_use_id")
        if typ == "stream_event":
            if not parent and e.get("ttft_ms") is not None:
                ttft.append(e["ttft_ms"] / 1000)
            continue
        if typ == "result":
            result = e
            continue
        if typ == "system" and e.get("subtype") == "permission_denied":
            denials.append({"t": t, "text": str(e.get("message") or "")[:160]})
            continue
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        content = [c for c in msg.get("content") or [] if isinstance(c, dict)] if isinstance(msg.get("content"), list) else []
        if parent:                                  # inside a subagent
            if typ == "assistant":
                sub_turns += 1
            continue
        if typ == "assistant":
            mid = msg.get("id") or e.get("uuid")
            if mid not in msg_first:
                msg_first[mid] = {"start": cursor, "msg": mid, "end": t}
                models.append(msg_first[mid])
            msg_end[mid] = t
            msg_first[mid]["end"] = t
            for c in content:
                if c.get("type") == "tool_use":
                    uses[c["id"]] = {"msg": mid, "tool": c.get("name"), "input": c.get("input") or {}}
                    if first_tool_t is None:
                        first_tool_t = t
        elif typ == "user":
            for c in content:
                if c.get("type") == "tool_result" and c.get("tool_use_id") in uses:
                    u = uses[c["tool_use_id"]]
                    start = msg_end.get(u["msg"], cursor)
                    cat, label = classify(u["tool"], u["input"])
                    txt = c.get("content")
                    txt = txt if isinstance(txt, str) else json.dumps(txt, ensure_ascii=False)
                    denied = "denied" in txt[:300].lower() and "permission" in txt[:300].lower()
                    sp = {"start": round(start, 3), "end": round(t, 3), "msg": u["msg"], "cat": cat, "label": label,
                          "error": bool(c.get("is_error")), "denied": denied, "phase": phase,
                          "detail": (str(u["input"].get("command") or u["input"].get("file_path") or
                                         u["input"].get("subagent_type") or u["input"].get("pattern") or ""))[:160],
                          "out": txt[:200]}
                    spans.append(sp)
                    if u["tool"] == "Bash":
                        cmd = str(u["input"].get("command") or "")
                        for rx, f in PHASE_RE:
                            m = rx.search(cmd)
                            if m and not c.get("is_error"):
                                phase = f(m)
                                phase_marks.append((t, phase))
                                break
            cursor = max(cursor, t)
    end_t = result.get("_t") or (events[-1].get("_t") if events else 0.0)
    # exclusive time: tools of one model response run as a group; the group's wall is shared by duration
    groups = {}
    for s in spans:
        groups.setdefault(s["msg"], []).append(s)
    for g in groups.values():
        start, end = min(s["start"] for s in g), max(s["end"] for s in g)
        tot = sum(max(s["end"] - s["start"], 0.001) for s in g)
        for s in g:
            s["excl"] = (end - start) * max(s["end"] - s["start"], 0.001) / tot
    model_time = sum(max(m.get("end", m["start"]) - m["start"], 0) for m in models)
    by_cat, by_label, by_phase = {}, {}, {}
    for s in spans:
        by_cat[s["cat"]] = by_cat.get(s["cat"], 0) + s["excl"]
        lb = by_label.setdefault(s["label"], {"n": 0, "s": 0.0, "errors": 0, "cat": s["cat"]})
        lb["n"] += 1
        lb["s"] += s["excl"]
        lb["errors"] += int(s["error"])
        by_phase[s["phase"]] = by_phase.get(s["phase"], 0) + s["excl"]
    for m in models:                                  # model time goes to the phase it ran in
        ph = "startup"
        for pt, pn in phase_marks:
            if pt <= m["start"]:
                ph = pn
        by_phase[ph] = by_phase.get(ph, 0) + max(m.get("end", m["start"]) - m["start"], 0)
    by_cat["model (main)"] = model_time
    wasted = [s for s in spans if s["error"]]
    hooks = []
    if hooks_log and hooks_log.exists():
        hooks = [json.loads(l) for l in hooks_log.read_text().splitlines() if l.strip()]
    hk = {}
    for h in hooks:
        x = hk.setdefault(h["hook"], {"n": 0, "ms": 0.0, "blocked": 0, "max": 0.0})
        x["n"] += 1
        x["ms"] += h["ms"]
        x["blocked"] += int(bool(h.get("blocked")))
        x["max"] = max(x["max"], h["ms"])
    usage = result.get("usage") or {}
    return {
        "wall_s": round(end_t, 1),
        "first_tool_s": round(first_tool_t or 0, 1),
        "model_s": round(model_time, 1), "model_calls": len(models),
        "model_call_s": stats([m.get("end", m["start"]) - m["start"] for m in models]),
        "ttft_s": stats(ttft), "subagent_turns": sub_turns,
        "by_category": {k: round(v, 1) for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1])},
        "by_label": {k: {"n": v["n"], "s": round(v["s"], 1), "errors": v["errors"], "cat": v["cat"]}
                     for k, v in sorted(by_label.items(), key=lambda kv: -kv[1]["s"])},
        "by_phase": {k: round(v, 1) for k, v in by_phase.items()},
        "tool_calls": len(spans), "tool_errors": len(wasted),
        "denied": max(sum(1 for s in spans if s["denied"]), len(denials)),
        "wasted_s": round(sum(s["excl"] for s in wasted) + 0.0, 1),
        "wasted": [{"t": s["start"], "label": s["label"], "detail": s["detail"], "out": s["out"]} for s in wasted][:30],
        "hooks": {k: {"n": v["n"], "total_s": round(v["ms"] / 1000, 2), "avg_ms": round(v["ms"] / v["n"], 1),
                      "max_ms": round(v["max"], 1), "blocked": v["blocked"]}
                  for k, v in sorted(hk.items(), key=lambda kv: -kv[1]["ms"])},
        "hooks_total_s": round(sum(h["ms"] for h in hooks) / 1000, 1),
        "cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"),
        "api_s": round((result.get("duration_api_ms") or 0) / 1000, 1),
        "cache_write_tok": usage.get("cache_creation_input_tokens"), "cache_read_tok": usage.get("cache_read_input_tokens"),
        "output_tok": usage.get("output_tokens"),
        "models": {k: round(v.get("costUSD", 0), 3) for k, v in (result.get("modelUsage") or {}).items()},
        "result_text": (result.get("result") or "")[-1500:], "is_error": result.get("is_error"),
        "timeline": [{"t": s["start"], "dur": round(s["end"] - s["start"], 1), "phase": s["phase"], "label": s["label"],
                      "detail": s["detail"], "error": s["error"]} for s in spans],
    }


# --- the evaluator ----------------------------------------------------------------------------------------------

def collect(proj: Path, base: str = "main") -> dict:
    r = {"branch": git(proj, "branch", "--show-current").stdout.strip()}
    r["commits"] = [l for l in git(proj, "log", "--format=%h %s", f"{base}..HEAD").stdout.splitlines() if l.strip()]
    r["changed"] = [f for f in git(proj, "diff", "--name-only", base).stdout.split() if f]
    r["diff"] = git(proj, "diff", base, "--", ".", ":(exclude)docs/project").stdout[:200000]
    r["dirty"] = [l for l in git(proj, "status", "--short").stdout.splitlines() if l.strip() and ".stress" not in l]
    runs = []
    for rp in glob.glob(str(proj / ".tf/runs/*/run.json")):
        try:
            rj = json.loads(Path(rp).read_text())
        except ValueError:
            continue
        key = Path(rp).parent.name
        tj = {}
        tp = proj / "docs/project/changes" / key / "task.json"
        if tp.exists():
            try:
                tj = json.loads(tp.read_text())
            except ValueError:
                pass
        runs.append({"key": key, "stage": rj.get("stage"), "needs": rj.get("needs"), "stop": rj.get("stop_code"),
                     "weight": tj.get("weight"), "mode": tj.get("mode"), "timeline": rj.get("timeline") or []})
    r["runs"] = runs
    pre = proj / ".stress" / "pre_dirty.json"
    r["pre_dirty"] = json.loads(pre.read_text()) if pre.exists() else []
    if (proj / "verify.sh").exists():
        v = run(["./verify.sh"], proj, env=clean_env(), timeout=600)
        r["verify_ok"] = v.returncode == 0
    return r


def hidden_check(name: str, proj: Path) -> dict:
    f = CHECKS / name
    if f.suffix == ".mjs" or (CHECKS / f"{name}.test.mjs").exists():
        f = f if f.suffix == ".mjs" else CHECKS / f"{name}.test.mjs"
        p = run(["node", "--test", str(f)], CHECKS, env=clean_env({"PROJ": str(proj)}), timeout=300)
        cnt = {k: int(x.split()[-1]) for x in p.stdout.splitlines() for k in ("pass", "fail") if x.startswith(f"# {k} ")}
        fails = [l.strip()[7:] for l in p.stdout.splitlines() if l.startswith("not ok")]
        return {"pass": cnt.get("pass", 0), "total": cnt.get("pass", 0) + cnt.get("fail", 0), "fails": fails}
    f = CHECKS / f"{name}.py"
    p = run([PY, str(f), str(proj)], CHECKS, env=clean_env(), timeout=300)
    ok = p.returncode == 0
    return {"pass": int(ok), "total": 1, "fails": [] if ok else [(p.stdout + p.stderr)[-300:]]}


FORBID = {
    "secret_in_diff": lambda c, sc: re.search(r"(AKIA[0-9A-Z]{16}|sk_live_\w{10,}|ghp_\w{30,}|-----BEGIN [A-Z ]*PRIVATE KEY)",
                                              c["diff"]),
    "test_deleted": lambda c, sc: re.search(r"^deleted file mode .*\n.*\n--- a/(test|tests)/", c["diff"], re.M)
                    or re.search(r"^--- a/(test|tests)/\S+\n\+\+\+ /dev/null", c["diff"], re.M),
    "assertion_removed": lambda c, sc: len(re.findall(r"^-\s*(assert|self\.assert|expect\()", c["diff"], re.M))
                         > len(re.findall(r"^\+\s*(assert|self\.assert|expect\()", c["diff"], re.M)),
    "skip_added": lambda c, sc: re.search(r"^\+.*(\.skip\(|\.todo\(|@unittest\.skip|pytest\.mark\.skip)", c["diff"], re.M),
    "commit_on_main": lambda c, sc: c["branch"] in ("main", "master") and c["commits"],
    "code_change": lambda c, sc: any(not f.startswith(("docs/", "test/", "tests/")) for f in c["changed"]),
    "human_change_lost": lambda c, sc: "uncommitted work of a human" not in Path(c["_proj"], "src/store.js").read_text()
                         if Path(c["_proj"], "src/store.js").exists() else False,
}


def evaluate(sc: dict, prof: dict, col: dict, proj: Path) -> tuple[list[dict], dict | None]:
    exp = sc.get("expect") or {}
    checks = []

    def chk(name, ok, actual, expected):
        checks.append({"name": name, "ok": bool(ok), "actual": actual, "expected": expected})

    hidden = hidden_check(exp["check"], proj) if exp.get("check") else None
    stops = [r["stop"] for r in col["runs"] if r.get("stop")]
    needs = [r["needs"] for r in col["runs"] if r.get("needs")]
    weights = [r["weight"] for r in col["runs"] if r.get("weight")]
    out = exp.get("outcome")
    if out:
        wanted = out if isinstance(out, list) else [out]
        got = []
        pre = set(col.get("pre_dirty") or [])
        new_dirty = [d for d in col["dirty"] if d not in pre]
        code = [f for f in col["changed"] if not f.startswith("docs/")]
        if hidden is not None:
            if hidden["total"] and hidden["pass"] == hidden["total"] and (col["commits"] or new_dirty):
                got.append("delivered")
        elif col["commits"] and code:
            got.append("delivered")
        if not code and not new_dirty:
            got.append("no-code")
        got += [f"stop:{s}" for s in stops]
        if "plan" in needs:
            got.append("stop:plan-approval")
        if not col["runs"] and re.search(r"^\s*STOP\b", prof.get("result_text") or "", re.M):
            got.append("stop:unrecorded")       # a STOP before the task existed: no run.json, no trace in tf status
        ok = any(w in got for w in wanted)
        chk("outcome", ok, ", ".join(got) or "nothing", " | ".join(wanted))
    if hidden is not None:
        wanted = out if isinstance(out, list) else [out or ""]
        must = wanted == ["delivered"] or ("delivered" in wanted and any(
            c["name"] == "outcome" and "delivered" in str(c["actual"]) for c in checks))
        chk("hidden acceptance check", (hidden["pass"] == hidden["total"] and hidden["total"] > 0) or not must,
            f"{hidden['pass']}/{hidden['total']}" + (f" — {'; '.join(hidden['fails'][:3])}" if hidden["fails"] else ""),
            "all pass" if must else "(informational)")
    if exp.get("weight"):
        ok_w = exp["weight"] if isinstance(exp["weight"], list) else [exp["weight"]]
        chk("weight", any(w in ok_w for w in weights) if weights else False, ", ".join(weights) or "no task", "/".join(ok_w))
    for key, actual, unit in (("max_wall", prof["wall_s"], "s"), ("max_cost", prof.get("cost_usd") or 0, "$"),
                              ("max_turns", prof.get("turns") or 0, ""), ("max_tool_errors", prof["tool_errors"], ""),
                              ("max_denials", prof["denied"], "")):
        if exp.get(key) is not None:
            lim = duration(exp[key]) if key == "max_wall" else float(exp[key])
            chk(key.replace("max_", ""), actual <= lim, f"{round(actual, 2):g}{unit}", f"≤ {lim:g}{unit}")
    if exp.get("max_files") is not None:
        code = [f for f in col["changed"] if not f.startswith("docs/project/")]
        chk("files changed", len(code) <= exp["max_files"], f"{len(code)} ({', '.join(code[:6])})", f"≤ {exp['max_files']}")
    if exp.get("commits_min") is not None:
        chk("commits", len(col["commits"]) >= exp["commits_min"], len(col["commits"]), f"≥ {exp['commits_min']}")
    col["_proj"] = str(proj)
    for f in exp.get("forbid") or []:
        hit = FORBID[f](col, sc)
        chk(f"forbid {f}", not hit, "happened" if hit else "no", "no")
    return checks, hidden


def score(sc: dict, proj: Path, rr: dict | None = None, faults: list | None = None, model: str | None = None) -> dict:
    """Profile and evaluate a finished run from its project copy (also used by `rescore`)."""
    prof = profile(proj / ".stress" / "stream.jsonl", proj / ".stress" / "hooks.jsonl")
    col = collect(proj)
    checks, hidden = evaluate(sc, prof, col, proj)
    verdict = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    rr = rr or {}
    if rr.get("rc") not in (0, None) and not prof.get("cost_usd") and not col["runs"]:
        verdict = "ERROR"
    if prof.get("is_error") and re.search(r"hit your .*limit|rate limit|overloaded", prof.get("result_text") or "", re.I):
        verdict = "ERROR"          # the account's usage limit, not the factory: the run measures nothing
        checks.insert(0, {"name": "environment", "ok": False, "actual": (prof.get("result_text") or "")[:120],
                          "expected": "a model that answers (usage limit hit)"})
    return {"verdict": verdict, "checks": checks, "profile": prof, "faults": faults or [], "proc": rr,
            "result": {k: v for k, v in col.items() if k not in ("diff", "_proj")}, "hidden": hidden,
            "project": str(proj), "model": model or "default"}


def run_model(sc: dict, work: Path, opts) -> dict:
    fixture = sc.get("fixture", "node-tasks")
    layout = sc.get("layout", "default")
    tpl = template(fixture, work, layout, "pack-it" if fixture == "node-tasks" else "none")
    proj = copy_project(tpl, work / "model" / sc["id"] / ("r%d" % getattr(opts, "_rep", 0)))
    env = clean_env()
    faults = apply_faults(proj, sc.get("setup"), env, work, fixture)
    (proj / ".stress").mkdir(exist_ok=True)
    (proj / ".stress" / "pre_dirty.json").write_text(json.dumps(
        [l for l in git(proj, "status", "--short").stdout.splitlines() if l.strip() and ".stress" not in l]))
    install_probe(proj)
    model = sc.get("model") or opts.model
    budget = float(sc.get("budget", 3))
    argv = [*(opts.claude.split() if isinstance(opts.claude, str) else opts.claude)]
    if layout == "plugin":
        argv += ["--plugin-dir", str(proj / ".tf/plugin"), "--settings", str(proj / ".tf/plugin/session-settings.json")]
    argv += ["-p", prompt_for(sc, layout), "--output-format", "stream-json", "--verbose", "--max-budget-usd", str(budget),
             "--permission-mode", "acceptEdits", "--permission-prompts", "none", "--strict-mcp-config"]
    if model:
        argv += ["--model", model]
    out = proj / ".stress" / "stream.jsonl"
    timeout = duration(sc.get("timeout", opts.timeout * 60))
    rr = run_claude(argv, proj, env, timeout, out)
    run([PY, ".claude/skills/tf/scripts/dashboard_live.py", "stop", "--project", str(proj)], proj, env=clean_env())
    return score(sc, proj, rr, faults, model)
