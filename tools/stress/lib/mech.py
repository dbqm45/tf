"""The mechanical engine of tf stress: no model, no cost. Each probe drives the factory's scripts and hooks with a
corpus of inputs (tools/stress/corpus/) or a load pattern, and returns cases (pass/fail with a reason) and timings."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import CORPUS, ROOT, clean_env, copy_project, git, load_yaml, pct, run, stats, template

PY = sys.executable


def _hook_env(proj: Path, extra: dict | None = None) -> dict:
    env = clean_env({"CLAUDE_PROJECT_DIR": str(proj)})
    env.update(extra or {})
    return env


def _payload(proj: Path, event: str, tool: str | None = None, tinput: dict | None = None, session: str = "stress",
             **kw) -> dict:
    d = {"session_id": session, "transcript_path": "/dev/null", "cwd": str(proj), "hook_event_name": event}
    if tool:
        d["tool_name"] = tool
        d["tool_input"] = tinput or {}
    d.update(kw)
    return d


def _fill(obj, proj: Path):
    if isinstance(obj, str):
        return obj.replace("{proj}", str(proj))
    if isinstance(obj, dict):
        return {k: _fill(v, proj) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fill(v, proj) for v in obj]
    return obj


def call_hook(proj: Path, script: str, data: dict, args: list[str] | None = None, env: dict | None = None) -> dict:
    t = time.perf_counter()
    p = subprocess.run([PY, str(proj / ".claude" / "hooks" / script), *(args or [])], input=json.dumps(data),
                       capture_output=True, text=True, cwd=str(proj), env=env or _hook_env(proj), timeout=120)
    ms = (time.perf_counter() - t) * 1000
    out = p.stdout or ""
    dec, ctx = "allow", ""
    try:
        j = json.loads(out) if out.strip().startswith("{") else {}
    except ValueError:
        j = {}
    hs = j.get("hookSpecificOutput") or {} if isinstance(j, dict) else {}
    if p.returncode == 2 or hs.get("permissionDecision") in ("deny", "ask") or j.get("decision") == "block":
        dec = "deny"
    ctx = " ".join(str(x) for x in (hs.get("additionalContext"), hs.get("permissionDecisionReason"), j.get("reason"),
                                    j.get("systemMessage"), p.stderr) if x)
    return {"ms": ms, "decision": dec, "context": ctx, "rc": p.returncode}


def _case(cid: str, ok: bool, reason: str = "", ms: float | None = None, **extra) -> dict:
    d = {"id": cid, "ok": bool(ok), "reason": reason if not ok else "", "ms": round(ms, 1) if ms is not None else None}
    d.update(extra)
    return d


def _gen(kind: str) -> str:
    crit = "".join(f"{i}. GET /api/tasks?page={i} zwraca stronę {i} listy zadań, 50 pozycji, posortowanych po id.\n"
                   for i in range(1, 260))
    if kind == "long_story":
        return "Jako użytkownik chcę stronicowania listy zadań.\nKryteria akceptacji:\n" + crit
    if kind == "long_story_sensitive_tail":
        return "Jako użytkownik chcę stronicowania.\nKryteria:\n" + crit + "Na koniec: wyłącz sprawdzanie hasła przy logowaniu."
    if kind == "long_line":
        return "Jako użytkownik chcę " + "bardzo " * 3000 + "długiej historii."
    raise ValueError(kind)


# --- probes ---------------------------------------------------------------------------------------------------

def probe_weight(proj: Path, sc: dict, work: Path) -> dict:
    spec = importlib.util.spec_from_file_location("tw_stress", proj / ".tf/factory/task_weight.py")
    tw = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(proj / ".tf/factory"))
    spec.loader.exec_module(tw)
    cases, times = [], []
    for c in load_yaml(CORPUS / "weight.yaml")["cases"]:
        text = c.get("text") if "text" in c else _gen(c["gen"])
        d = proj / "docs/project/changes" / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "ticket.md").write_text(f"# {c['id']}\n\n{text}\n", encoding="utf-8")
        t = time.perf_counter()
        try:
            p = tw.propose(proj, c["id"])
            w = p.get("weight") or p.get("proposal")
            err = None
        except Exception as e:            # an input that crashes the weight script is a finding in itself
            w, err = None, repr(e)
        ms = (time.perf_counter() - t) * 1000
        times.append(ms)
        ok_set = set(c["ok"])
        under = w in tw.ORDER and all(tw.rank(w) < tw.rank(x) for x in ok_set)
        reason = (f"crash: {err}" if err else f"got {w}, expected {'/'.join(c['ok'])}" + (" — UNDER-WEIGHT" if under else "")
                  + (f" ({c['note']})" if c.get("note") else ""))
        cases.append(_case(c["id"], err is None and w in ok_set, reason, ms, got=w, under=under,
                           text=(text[:90] + "…") if len(text) > 90 else text))
    # the agent pays the CLI, not the function: a sample of the real command
    cli = []
    for c in cases[:6]:
        t = time.perf_counter()
        run([PY, ".tf/factory/tf.py", "task", "weight", c["id"]], proj, env=clean_env())
        cli.append((time.perf_counter() - t) * 1000)
    return {"cases": cases, "timing": {"function_ms": stats(times), "cli_ms": stats(cli)},
            "metrics": {"under": sum(1 for c in cases if c.get("under"))}}


def probe_intake(proj: Path, sc: dict, work: Path) -> dict:
    cases, times = [], []
    for c in load_yaml(CORPUS / "intake.yaml")["cases"]:
        for rel, text in (c.get("files") or {}).items():
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_text(text, encoding="utf-8")
        arg = c.get("arg") if "arg" in c else _gen(c["gen"])
        t = time.perf_counter()
        p = run([PY, ".claude/skills/tf/scripts/intake.py", "resolve", arg], proj, env=clean_env(), timeout=60)
        ms = (time.perf_counter() - t) * 1000
        times.append(ms)
        out = p.stdout
        fields = dict(re.findall(r"^(Input|Key|Way|Tracker): (.*)$", out, re.M))
        got_in = (fields.get("Input") or "").strip()
        want_in = c["input"] if isinstance(c["input"], list) else [c["input"]]
        problems = []
        if p.returncode not in (0,):
            problems.append(f"exit {p.returncode}: {(p.stderr or out)[-160:]}")
        if got_in not in want_in:
            problems.append(f"Input: {got_in or '∅'} (expected {'/'.join(want_in)})")
        if c.get("key") and fields.get("Key", "").strip() != c["key"]:
            problems.append(f"Key: {fields.get('Key', '∅')} (expected {c['key']})")
        if c.get("way") and not fields.get("Way", "").startswith(c["way"]):
            problems.append(f"Way: {fields.get('Way', '∅')} (expected {c['way']})")
        reason = "; ".join(problems) + (f" ({c['note']})" if c.get("note") and problems else "")
        cases.append(_case(c["id"], not problems, reason, ms, arg=arg[:80]))
    return {"cases": cases, "timing": {"cli_ms": stats(times)}}


def probe_guards(proj: Path, sc: dict, work: Path) -> dict:
    reps = int((sc.get("params") or {}).get("repeat", 3))
    cases, by_hook = [], {}
    for c in load_yaml(CORPUS / "guards.yaml")["cases"]:
        for rel, text in (c.get("files") or {}).items():
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_text(text, encoding="utf-8")
        data = _payload(proj, c.get("event", "PreToolUse"), c["tool"], _fill(c["input"], proj),
                        **({"tool_response": {}} if c.get("event") == "PostToolUse" else {}))
        res = [call_hook(proj, c["hook"] + ".py", data) for _ in range(reps)]
        decs = {r["decision"] for r in res}
        ms = sorted(r["ms"] for r in res)[len(res) // 2]
        by_hook.setdefault(c["hook"], []).extend(r["ms"] for r in res)
        got = res[0]["decision"]
        kind = "false deny (costs a turn)" if c["expect"] == "allow" else "MISSED (evasion passes)"
        reason = f"{got}, expected {c['expect']} — {kind}" + (f" ({c['note']})" if c.get("note") else "")
        if len(decs) > 1:
            reason, got = f"unstable decision {sorted(decs)}", "unstable"
        cases.append(_case(c["id"], got == c["expect"], reason, ms, hook=c["hook"], expect=c["expect"],
                           input=json.dumps(c["input"], ensure_ascii=False)[:100]))
        for rel in (c.get("files") or {}):
            (proj / rel).unlink(missing_ok=True)
    return {"cases": cases, "timing": {f"{h}_ms": stats(v) for h, v in by_hook.items()},
            "metrics": {"false_deny": sum(1 for c in cases if not c["ok"] and c["expect"] == "allow"),
                        "missed": sum(1 for c in cases if not c["ok"] and c["expect"] == "deny")}}


def probe_tdd(proj: Path, sc: dict, work: Path) -> dict:
    cases, times = [], []
    for c in load_yaml(CORPUS / "tdd.yaml")["cases"]:
        session = f"tdd-{c['id']}-{uuid.uuid4().hex[:6]}"
        for rel, text in (c.get("files") or {}).items():
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_text(text, encoding="utf-8")
        problems, ms_all = [], []
        for st in c["steps"]:
            for _ in range(int(st.get("repeat", 1))):
                extra = {}
                if st["tool"] == "Bash" and st["event"].startswith("PostToolUse"):
                    extra["tool_response"] = {"stdout": st.get("out", ""), "stderr": "", "exit_code": st.get("exit", 0)}
                elif st["event"] == "PostToolUse":
                    extra["tool_response"] = {}
                if st.get("agent"):
                    extra["agent_id"] = st["agent"]
                data = _payload(proj, st["event"], st["tool"], _fill(st["input"], proj), session=session, **extra)
                r = call_hook(proj, "tdd_guard.py", data)
                ms_all.append(r["ms"])
                if "expect" in st and r["decision"] != st["expect"]:
                    problems.append(f"{st['tool']} {Path(str(st['input'].get('file_path', ''))).name}: "
                                    f"{r['decision']}, expected {st['expect']}")
                if "note" in st and st["note"].lower() not in r["context"].lower():
                    problems.append(f"no '{st['note']}' warning")
        times.extend(ms_all)
        cases.append(_case(c["id"], not problems, "; ".join(problems) + f" — {c['name']}", sum(ms_all), name=c["name"]))
    return {"cases": cases, "timing": {"per_call_ms": stats(times)}}


def _registered(proj: Path) -> dict[str, list[tuple[str, list[str]]]]:
    s = json.loads((proj / ".claude/settings.local.json").read_text())
    out = {}
    for ev, arr in (s.get("hooks") or {}).items():
        for m in arr:
            for h in m.get("hooks", []):
                args = [a.replace("${CLAUDE_PROJECT_DIR}", str(proj)) for a in (h.get("args") or [])]
                out.setdefault(ev, []).append((m.get("matcher") or "*", args))
    return out


def probe_hook_chains(proj: Path, sc: dict, work: Path) -> dict:
    """The hook overhead the agent pays per action: every hook registered for an event/tool runs (Claude Code runs
    matching hooks in parallel: the wall time is the slowest one, the CPU cost is the sum)."""
    reg = _registered(proj)
    actions = {
        "session start": ("SessionStart", None, {}, {"source": "startup"}),
        "user prompt": ("UserPromptSubmit", None, {}, {"prompt": "Dodaj licznik otwartych zadań w nagłówku"}),
        "Read": ("PreToolUse", "Read", {"file_path": f"{proj}/src/store.js"}, {}),
        "Edit (pre)": ("PreToolUse", "Edit", {"file_path": f"{proj}/README.md", "old_string": "a", "new_string": "b"}, {}),
        "Edit (post)": ("PostToolUse", "Edit", {"file_path": f"{proj}/README.md"}, {"tool_response": {}}),
        "Bash (pre)": ("PreToolUse", "Bash", {"command": "git status"}, {}),
        "Bash (post)": ("PostToolUse", "Bash", {"command": "git status"}, {"tool_response": {"stdout": "", "exit_code": 0}}),
        "Agent (pre)": ("PreToolUse", "Agent", {"subagent_type": "scope-reviewer", "prompt": "x", "description": "x"}, {}),
        "Stop": ("Stop", None, {}, {"stop_hook_active": False}),
    }
    reps = int((sc.get("params") or {}).get("repeat", 5))
    cases, rows = [], []
    for name, (ev, tool, tinput, kw) in actions.items():
        match = tool or kw.get("source") or ""      # SessionStart matches on the source (startup|resume)
        hooks = [a for m, a in reg.get(ev, []) if m == "*" or (match and re.fullmatch(m, match))]
        per_hook = {}
        for _ in range(reps):
            for args in hooks:
                data = _payload(proj, ev, tool, tinput, **kw)
                t = time.perf_counter()
                subprocess.run([PY, *args], input=json.dumps(data), capture_output=True, text=True, cwd=str(proj),
                               env=_hook_env(proj), timeout=120)
                per_hook.setdefault(Path(args[0]).name + (" " + " ".join(args[1:]) if len(args) > 1 else ""), []).append(
                    (time.perf_counter() - t) * 1000)
        p50 = {h: sorted(v)[len(v) // 2] for h, v in per_hook.items()}
        wall, cpu = (max(p50.values()) if p50 else 0), sum(p50.values())
        rows.append({"action": name, "hooks": len(hooks), "wall_ms": round(wall, 1), "cpu_ms": round(cpu, 1),
                     "slowest": max(p50, key=p50.get) if p50 else None, "per_hook": {k: round(v, 1) for k, v in p50.items()}})
        lim = (sc.get("expect") or {}).get("max_ms")
        cases.append(_case(name, lim is None or wall <= lim, f"wall {wall:.0f} ms > {lim} ms (slowest: {rows[-1]['slowest']})",
                           wall, cpu_ms=round(cpu, 1), hooks=len(hooks)))
    return {"cases": cases, "chains": rows}


def probe_hook_load(proj: Path, sc: dict, work: Path) -> dict:
    corpus = [c for c in load_yaml(CORPUS / "guards.yaml")["cases"] if not c.get("files")]
    jobs = []
    for c in corpus:
        data = _payload(proj, c.get("event", "PreToolUse"), c["tool"], _fill(c["input"], proj))
        jobs.append((c, data))
    sizes = [int(x) for x in (sc.get("sizes") or [1, 4, 8, 16, 32])]
    rows, cases = [], []
    for n in sizes:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(n) as ex:
            res = list(ex.map(lambda j: (j[0], call_hook(proj, j[0]["hook"] + ".py", j[1])), jobs))
        wall = time.perf_counter() - t0
        lat = [r["ms"] for _, r in res]
        wrong = sum(1 for c, r in res if r["decision"] != c["expect"])
        base_wrong = rows[0]["wrong"] if rows else wrong
        rows.append({"workers": n, "calls": len(res), "wall_s": round(wall, 2), "per_s": round(len(res) / wall, 1),
                     "p50_ms": round(pct(lat, .5), 1), "p95_ms": round(pct(lat, .95), 1), "max_ms": round(max(lat), 1),
                     "wrong": wrong})
        cases.append(_case(f"{n} workers", wrong == base_wrong,
                           f"{wrong} wrong decisions under load vs {base_wrong} at 1 worker (a race in a hook)",
                           pct(lat, .95), workers=n))
    return {"cases": cases, "load": rows}


R = ".claude/skills/tf/scripts"


def _lifecycle_once(proj: Path, key_hint: str, files_mode: str, node: bool, timings: dict) -> list[str]:
    """One scripted /tf-task run without a model: the same script calls the loop makes, in order, timed."""
    problems = []

    def t(name, cmd, ok_codes=(0,)):
        s = time.perf_counter()
        p = run(cmd, proj, env=clean_env({"TF_DASHBOARD_LIVE": "0"} if files_mode == "nolive" else None), timeout=600)
        timings.setdefault(name, []).append((time.perf_counter() - s) * 1000)
        if p.returncode not in ok_codes:
            problems.append(f"{name}: exit {p.returncode} {(p.stdout + p.stderr).strip()[-200:]}")
        return p

    t("intake.py resolve", [PY, f"{R}/intake.py", "resolve", "Jako użytkownik chcę licznik " + key_hint])
    t("security_scan.py cooldown", [PY, f"{R}/security_scan.py", "cooldown"])
    p = t("run_report.py start", [PY, f"{R}/run_report.py", "start", f"Licznik {key_hint}", "--story",
                                  "Jako użytkownik chcę licznik. Kryteria: 1. GET /api/tasks/stats zwraca zera."])
    m = re.search(r"\.tf/runs/([^/\s]+)", p.stdout)
    if not m:
        problems.append(f"no run directory in: {p.stdout[-200:]}")
        return problems
    key = m.group(1)
    d = f".tf/runs/{key}"
    c = proj / "docs/project/changes" / key
    git(proj, "switch", "-q", "-c", f"story/{key.lower()}")
    t("run_state.py stage intake", [PY, f"{R}/run_state.py", "stage", d, "intake", "--auto"])
    t("run_state.py approach", [PY, f"{R}/run_state.py", "approach", d, "--weight", "normal", "--rationale", "src:1",
                                "--slices", "1"])
    t("run_state.py spec new", [PY, f"{R}/run_state.py", "spec", d, "new"])
    (c / "spec.md").write_text("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given an empty store, when GET /api/tasks/stats, "
                               "then it returns zeros.\n- AC-2: Given any store, when POST /api/tasks/stats, then 404.\n\n"
                               "## Unchanged\n\n- the list.\n\n## Out of scope\n\n- none, because one endpoint.\n")
    t("run_state.py spec check", [PY, f"{R}/run_state.py", "spec", d])
    tfile = "test/stats.test.js" if node else "tests/test_stats.py"
    sfile = "src/routes.js" if node else "app/pricing.py"
    (c / "plan.md").write_text(f"# Plan\n\n- [ ] S1 — stats · criteria: AC-1, AC-2 ({tfile}: test_ac1) · files: {sfile}, {tfile}"
                               " · verify: `./verify.sh` · tier: std\n")
    t("run_state.py flag none", [PY, f"{R}/run_state.py", "flag", d, "none", "--reason", "stress"])
    t("run_state.py stage plan", [PY, f"{R}/run_state.py", "stage", d, "plan"])
    t("run_state.py step test run", [PY, f"{R}/run_state.py", "step", d, "S1", "R1", "test", "run"])
    if node:
        (proj / tfile).write_text("import { test } from \"node:test\";\nimport assert from \"node:assert/strict\";\n"
                                  "test(\"test_ac1\", () => { assert.equal(1, 1); }); // AC-1 AC-2\n")
        with open(proj / sfile, "a") as fh:
            fh.write(f"// stats {key_hint}\n")
    else:
        (proj / tfile).write_text("import unittest\n\n\nclass T(unittest.TestCase):\n    def test_ac1(self):  # AC-1 AC-2\n"
                                  "        self.assertTrue(True)\n")
        with open(proj / sfile, "a") as fh:
            fh.write(f"# stats {key_hint}\n")
    t("run_state.py finish-slice", [PY, f"{R}/run_state.py", "finish-slice", d, "S1", "--files", f"{sfile},{tfile}",
                                    "--message", "feat(api): stats"])
    t("run_state.py trace", [PY, f"{R}/run_state.py", "trace", d, "--base", "main"], ok_codes=(0, 1))
    t("plan_drift.py", [PY, f"{R}/plan_drift.py", d, "--base", "main"], ok_codes=(0, 1))
    t("pr_budget.py", [PY, ".claude/skills/core-delivery-lifecycle/scripts/pr_budget.py", "--base", "main"], ok_codes=(0, 1))
    t("run_state.py stage pr", [PY, f"{R}/run_state.py", "stage", d, "pr"])
    t("run_state.py pr-body", [PY, f"{R}/run_state.py", "pr-body", d, "--base", "main"])
    t("run_report.py finish", [PY, f"{R}/run_report.py", "finish", d], ok_codes=(0, 2))
    git(proj, "add", "-A", "docs")
    git(proj, "commit", "-qm", f"docs(task): record {key}")
    git(proj, "switch", "-q", "main")
    return problems


def _lifecycle_composite(proj: Path, key_hint: str, node: bool, timings: dict) -> list[str]:
    """The same task as `_lifecycle_once` with the composite commands (start --begin, plan, finish-slice, close)."""
    problems = []

    def t(name, cmd, ok_codes=(0,)):
        s = time.perf_counter()
        p = run(cmd, proj, env=clean_env({"CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}), timeout=600)
        timings.setdefault(name, []).append((time.perf_counter() - s) * 1000)
        if p.returncode not in ok_codes:
            problems.append(f"{name}: exit {p.returncode} {(p.stdout + p.stderr).strip()[-200:]}")
        return p

    t("intake.py resolve", [PY, f"{R}/intake.py", "resolve", "Jako użytkownik chcę licznik " + key_hint])
    p = t("run_report.py start --begin", [PY, f"{R}/run_report.py", "start", f"Licznik {key_hint}", "--story",
                                          "Jako użytkownik chcę licznik. Kryteria: 1. GET /api/tasks/stats zwraca zera.",
                                          "--begin", "--auto"])
    m = re.search(r"\.tf/runs/([^/\s]+)", p.stdout)
    if not m:
        return problems + [f"no run directory in: {p.stdout[-200:]}"]
    key = m.group(1)
    d = f".tf/runs/{key}"
    c = proj / "docs/project/changes" / key
    t("run_state.py spec new", [PY, f"{R}/run_state.py", "spec", d, "new"])
    (c / "spec.md").write_text("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given an empty store, when GET /api/tasks/stats, "
                               "then it returns zeros.\n- AC-2: Given any store, when POST /api/tasks/stats, then 404.\n\n"
                               "## Unchanged\n\n- the list.\n\n## Out of scope\n\n- none, because one endpoint.\n")
    tfile = "test/stats.test.js" if node else "tests/test_stats.py"
    sfile = "src/routes.js" if node else "app/pricing.py"
    (c / "plan.md").write_text(f"# Plan\n\n- [ ] S1 — stats · criteria: AC-1, AC-2 ({tfile}: test_ac1) · files: {sfile}, {tfile}"
                               " · verify: `./verify.sh` · tier: std\n")
    t("run_state.py plan", [PY, f"{R}/run_state.py", "plan", d, "--weight", "normal", "--rationale", "src:1", "--slices", "1",
                            "--flag", "none", "--flag-reason", "stress", "--base", "main", "--auto"])
    if node:
        (proj / tfile).write_text("import { test } from \"node:test\";\nimport assert from \"node:assert/strict\";\n"
                                  "test(\"test_ac1\", () => { assert.equal(1, 1); }); // AC-1 AC-2\n")
    else:
        (proj / tfile).write_text("import unittest\n\n\nclass T(unittest.TestCase):\n    def test_ac1(self):  # AC-1 AC-2\n"
                                  "        self.assertTrue(True)\n")
    with open(proj / sfile, "a") as fh:
        fh.write(("// " if node else "# ") + f"stats {key_hint}\n")
    t("run_state.py finish-slice", [PY, f"{R}/run_state.py", "finish-slice", d, "S1", "--files", f"{sfile},{tfile}",
                                    "--message", "feat(api): stats"])
    t("run_state.py close", [PY, f"{R}/run_state.py", "close", d, "--base", "main"], ok_codes=(0, 3))
    git(proj, "add", "-A", "docs")
    git(proj, "commit", "-qm", f"docs(task): record {key}")
    git(proj, "switch", "-q", "main")
    return problems


def _servers(proj: Path) -> int:
    p = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True)
    return sum(1 for l in p.stdout.splitlines() if "dashboard_live.py serve" in l and str(proj) in l)


def probe_lifecycle(proj: Path, sc: dict, work: Path) -> dict:
    n = int((sc.get("params") or {}).get("tasks", 3))
    node = (proj / "package.json").exists()
    timings, problems = {}, []
    t0 = time.perf_counter()
    composite = bool((sc.get("params") or {}).get("composite"))
    for i in range(n):
        problems += (_lifecycle_composite(proj, f"#{i}", node, timings) if composite
                     else _lifecycle_once(proj, f"#{i}", "live", node, timings))
    total = time.perf_counter() - t0
    leaked = _servers(proj)
    run([PY, f"{R}/dashboard_live.py", "stop", "--project", str(proj)], proj, env=clean_env())
    per = {k: stats(v) for k, v in timings.items()}
    cases = [_case(k, True, "", v["p50"], **v) for k, v in sorted(per.items(), key=lambda kv: -kv[1]["p50"])]
    lim = (sc.get("expect") or {}).get("max_ms")
    for c in cases:
        if lim and c["ms"] > lim:
            c["ok"], c["reason"] = False, f"p50 {c['ms']:.0f} ms > {lim} ms for one script call"
    for p in problems:
        cases.append(_case("script error", False, p))
    calls = sum(len(v) for v in timings.values())
    cases.append(_case("live dashboard servers left running", leaked == 0,
                       f"{leaked} server process(es) alive after {n} finished runs (each idles 30 min, ~25 MB)",
                       None, leaked=leaked))
    return {"cases": cases, "metrics": {"tasks": n, "script_calls_per_task": round(calls / max(n, 1), 1),
                                        "script_s_per_task": round(total / max(n, 1), 2), "servers_left": leaked},
            "timing": per}


def probe_scan(proj: Path, sc: dict, work: Path) -> dict:
    """The security scan the loop runs per slice: semgrep startup and the ruleset."""
    cases = []
    if not shutil.which("semgrep"):
        return {"cases": [_case("semgrep present", False, "semgrep not in PATH — the loop stops every slice with STOP scan")]}
    target = "src/routes.js" if (proj / "src/routes.js").exists() else "app/pricing.py"
    for name, cmd in (("semgrep --version (startup)", ["semgrep", "--version"]),
                      ("semgrep p/owasp-top-ten, 1 file", ["semgrep", "scan", "--config", "p/owasp-top-ten", "--metrics", "off",
                                                           "-q", target])):
        ms = []
        for _ in range(int((sc.get("params") or {}).get("repeat", 3))):
            t = time.perf_counter()
            run(cmd, proj, env=clean_env(), timeout=300)
            ms.append((time.perf_counter() - t) * 1000)
        lim = (sc.get("expect") or {}).get("max_ms")
        med = sorted(ms)[len(ms) // 2]
        cases.append(_case(name, lim is None or med <= lim, f"{med:.0f} ms > {lim} ms per slice", med, **stats(ms)))
    return {"cases": cases}


def probe_status_scale(proj: Path, sc: dict, work: Path) -> dict:
    sizes = [int(x) for x in (sc.get("sizes") or [10, 100, 500])]
    rows, cases, made = [], [], 0
    lim = (sc.get("expect") or {}).get("max_ms")
    for n in sizes:
        t = time.perf_counter()
        while made < n:
            made += 1
            k = f"SC-{made}"
            d = proj / "docs/project/changes" / k
            d.mkdir(parents=True, exist_ok=True)
            (d / "task.json").write_text(json.dumps({"schema": 1, "key": k, "title": f"Task {made}", "stage": "slices",
                                                     "weight": "normal", "mode": "auto"}))
            r = proj / ".tf/runs" / k
            r.mkdir(parents=True, exist_ok=True)
            (r / "run.json").write_text(json.dumps({"key": k, "stage": "slices", "slices": {"S1": {"state": "verified"}}}))
        mk = (time.perf_counter() - t) * 1000
        res = {}
        for name, cmd in (("tf status", [PY, ".tf/factory/tf.py", "status"]),
                          ("tf status --all", [PY, ".tf/factory/tf.py", "status", "--all"]),
                          ("dashboard", [PY, f"{R}/run_state.py", "dashboard", "--no-cost", "--out", str(work / "dash.html")])):
            s = time.perf_counter()
            p = run(cmd, proj, env=clean_env(), timeout=600)
            res[name] = round((time.perf_counter() - s) * 1000, 1)
            if p.returncode:
                cases.append(_case(f"{name} @ {n}", False, f"exit {p.returncode}: {(p.stdout + p.stderr)[-200:]}"))
        rows.append({"tasks": n, **res, "setup_ms": round(mk)})
        worst = max(res.values())
        cases.append(_case(f"{n} tasks", lim is None or worst <= lim, f"slowest view {worst:.0f} ms > {lim} ms", worst, **res))
    return {"cases": cases, "scale": rows}


def probe_work_race(proj: Path, sc: dict, work: Path) -> dict:
    params = sc.get("params") or {}
    workers, tasks = int(params.get("workers", 8)), int(params.get("tasks", 3))
    stub = work / "_stub_agent.sh"
    stub.write_text("#!/bin/sh\nsleep 2\necho '{\"total_cost_usd\":0.01,\"result\":\"stub\"}'\n")
    stub.chmod(0o755)
    keys = []
    for i in range(tasks):
        k = f"RACE-{i + 1}"
        keys.append(k)
        run([PY, ".tf/factory/tf.py", "task", "start", k, "--title", f"Race {i}"], proj, env=clean_env())
        (proj / "docs/project/changes" / k / "ticket.md").write_text("# Race\n\nPopraw literówkę w README.\n")
        run([PY, ".tf/factory/tf.py", "task", "mode", k, "auto"], proj, env=clean_env())
    git(proj, "add", "-A", "docs")
    git(proj, "commit", "-qm", "docs: race tasks")
    env = clean_env({"TF_WORK_AGENT": str(stub)})
    t0 = time.perf_counter()
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda i: run([PY, ".tf/factory/tf.py", "work", "--once", "--budget", "1"], proj, env=env,
                                        timeout=300), range(workers)))
    wall = time.perf_counter() - t0
    took = [re.search(r"✓ (RACE-\d+)", p.stdout).group(1) for p in res if re.search(r"✓ (RACE-\d+)", p.stdout)]
    dup = len(took) - len(set(took))
    codes = sorted(p.returncode for p in res)
    cases = [_case("each task taken once", dup == 0 and len(set(took)) == min(tasks, workers),
                   f"taken {took} by {workers} workers for {tasks} tasks (duplicates: {dup})", wall * 1000,
                   exit_codes=codes)]
    return {"cases": cases, "metrics": {"workers": workers, "tasks": tasks, "taken": len(took), "dup": dup,
                                        "wall_s": round(wall, 2)}}


def probe_install(proj: Path, sc: dict, work: Path) -> dict:
    """Install and update cost for pack sets and layouts (a fresh project per variant)."""
    rows, cases = [], []
    lim = (sc.get("expect") or {}).get("max_ms")
    for packs, layout in [tuple(x.split(":")) for x in (sc.get("params") or {}).get("variants", ["none:default", "pack-it:default",
                                                                                                 "pack-it:plugin"])]:
        d = work / f"_inst-{packs}-{layout}"
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(proj, d, ignore=shutil.ignore_patterns(".claude", ".tf", "CLAUDE.local.md", "verify.sh"))
        res = {}
        for name in ("install", "update (no change)"):
            s = time.perf_counter()
            p = run([PY, str(ROOT / "core/factory/install.py"), "--yes", "--packs", packs, "--layout", layout], d,
                    env=clean_env(), timeout=900)
            res[name] = round((time.perf_counter() - s) * 1000)
            if p.returncode:
                cases.append(_case(f"{packs}/{layout} {name}", False, (p.stdout + p.stderr)[-200:]))
        files = sum(1 for _ in (d / ".tf").rglob("*")) + sum(1 for _ in (d / ".claude").rglob("*"))
        rows.append({"packs": packs, "layout": layout, **res, "files": files})
        cases.append(_case(f"{packs}/{layout}", lim is None or res["update (no change)"] <= lim,
                           f"update with nothing to change took {res['update (no change)']} ms > {lim} ms",
                           res["install"], **res, files=files))
        shutil.rmtree(d, ignore_errors=True)
    return {"cases": cases, "install": rows}


def probe_context(proj: Path, sc: dict, work: Path) -> dict:
    """What every session loads before the first token of work: instructions and skill/agent descriptions
    (≈ 4 bytes per token). More context = slower first response and a bigger cache write on every new session."""
    parts = {}
    for f in ("CLAUDE.local.md", "CLAUDE.md", ".claude/CLAUDE.md"):
        if (proj / f).exists():
            parts[f] = (proj / f).stat().st_size
    import yaml

    def front(path: Path) -> dict:
        m = re.match(r"---\n(.*?)\n---", path.read_text(encoding="utf-8", errors="ignore"), re.S)
        try:
            return (yaml.safe_load(m.group(1)) or {}) if m else {}
        except Exception:
            return {}

    # Claude Code lists each skill by name and description (none for disable-model-invocation), each agent by its
    # name and description in the Agent tool; metadata/keywords stay on disk.
    desc, hidden = 0, 0
    skills = list((proj / ".claude/skills").glob("*/SKILL.md"))
    for s in skills:
        f = front(s)
        if f.get("disable-model-invocation"):
            hidden += 1
            continue
        desc += len(str(f.get("name", ""))) + len(str(f.get("description", ""))) + len(str(f.get("when_to_use", ""))) + 8
    agents = list((proj / ".claude/agents").rglob("*.md"))
    adesc = 0
    for a in agents:
        f = front(a)
        adesc += len(str(f.get("name", ""))) + len(str(f.get("description", ""))) + 8
    parts["skill names + descriptions"] = desc
    parts["agent names + descriptions"] = adesc
    tf_task = (proj / ".claude/skills/tf-task/SKILL.md")
    parts["tf-task SKILL.md (loaded on /tf-task)"] = tf_task.stat().st_size if tf_task.exists() else 0
    total = sum(parts.values())
    lim = (sc.get("expect") or {}).get("max_ms")      # here: max kilo-tokens
    ktok = total / 4 / 1000
    cases = [_case(k, True, "", None, bytes=v, ktok=round(v / 4000, 1)) for k, v in parts.items()]
    cases.append(_case("total", lim is None or ktok <= lim, f"≈{ktok:.1f}k tokens > {lim}k before the first step", None,
                       bytes=total, ktok=round(ktok, 1)))
    return {"cases": cases, "metrics": {"skills": len(skills), "skills_hidden": hidden, "agents": len(agents), "ktok": round(ktok, 1)}}


PROBES = {"weight": probe_weight, "intake": probe_intake, "guards": probe_guards, "tdd": probe_tdd,
          "hook_chains": probe_hook_chains, "hook_load": probe_hook_load, "lifecycle": probe_lifecycle,
          "scan": probe_scan, "status_scale": probe_status_scale, "work_race": probe_work_race,
          "install": probe_install, "context": probe_context}


def run_mech(sc: dict, work: Path) -> dict:
    fixture = sc.get("fixture", "node-tasks")
    tpl = template(fixture, work, sc.get("layout", "default"), "pack-it" if fixture == "node-tasks" else "none")
    proj = copy_project(tpl, work / "mech" / sc["id"])
    t = time.time()
    try:
        res = PROBES[sc["probe"]](proj, sc, work)
    except Exception as e:
        import traceback
        res = {"cases": [_case("probe", False, f"probe crashed: {e!r} {traceback.format_exc()[-400:]}")]}
    res["wall_s"] = round(time.time() - t, 2)
    return res
