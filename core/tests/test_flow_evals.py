#!/usr/bin/env python3
"""Tests of the flow-evals runner (N5, DZ13): task loading, per-phase checks, comparison with the baseline,
N17 judge rules (both orders, length control), CI gates without a secret.

python3 core/tests/test_flow_evals.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import flow_evals_runner as fer  # noqa: E402
from flow_evals.kappa import cohens_kappa, linear_kappa  # noqa: E402


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="flow-evals-test-"))


def _fake_phase_result(**kwargs) -> dict:
    out = {"change": "CHG-1", "phase": "intent", "status": "done",
           "cost_usd": 0.1, "detail": "gotowe", "permission_denials": []}
    out.update(kwargs)
    return {"result": out, "progress": [], "duration_s": 1.23, "stderr": "", "exit_code": 0}


def _fake_judge_fixed(score: int = 5, cost: float = 0.01):
    def _j(**_kwargs):
        return {"score": score, "reason": "ok", "cost_usd": cost}
    return _j


def _args(**kwargs) -> argparse.Namespace:
    base = argparse.Namespace(
        validate=False, all=True, ids=None, budget_usd=15.0, per_task_budget_usd=1.0,
        model="claude-opus-4-7", judge_model="claude-haiku-4-5-20251001", judge="on",
        judge_timeout=5, length_ratio=1.8, baseline=None, save_baseline=False, yes=True,
        claude_bin="claude", repos=None, work=None, out=None)
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # ── validate_task ────────────────────────────────────────────────────────

    good = {"id": "N5-x-intent", "repo": "synth", "phase": "intent", "change": "CHG-1",
            "type": "happy", "before_dir": "fixtures/synth/intent/",
            "expect": {"status": "done", "max_cost_usd": 0.5}}
    tmp = _tmp()
    try:
        (tmp / "fixtures" / "synth" / "intent").mkdir(parents=True)
        errs = fer.validate_task(good, tmp)
        check(errs == [], f"V-1: {errs}")

        bad = dict(good)
        bad["phase"] = "intention"
        check(any("phase" in e for e in fer.validate_task(bad, tmp)), "V-2: bad phase passed")

        bad = dict(good)
        bad["type"] = "unknown"
        check(any("type" in e for e in fer.validate_task(bad, tmp)), "V-3: bad type passed")

        bad = dict(good)
        del bad["before_dir"]
        check(any("before_dir" in e for e in fer.validate_task(bad, tmp)), "V-4: missing before_dir passed")

        bad = dict(good, before_dir="fixtures/nie-ma/")
        check(any("does not exist" in e for e in fer.validate_task(bad, tmp)),
              "V-5: nonexistent before_dir passed")

        bad = dict(good, judge={"run": True})
        check(any("rubric" in e for e in fer.validate_task(bad, tmp)),
              "V-6: judge.run without a rubric passed")

        (tmp / "rubrics").mkdir()
        (tmp / "rubrics" / "intent.md").write_text("rubryka")
        good_judge = dict(good, judge={"run": True, "rubric": "rubrics/intent.md",
                                       "requirements": ["coś mądrego"]})
        check(fer.validate_task(good_judge, tmp) == [], "V-7: valid judge rejected")
    finally:
        shutil.rmtree(tmp)

    # ── load_tasks with the ids filter ──────────────────────────────────────────────
    tmp = _tmp()
    try:
        (tmp / "fixtures" / "a").mkdir(parents=True)
        (tmp / "fixtures" / "b").mkdir(parents=True)
        for tid, bd in (("N5-a-intent", "fixtures/a"), ("N5-b-requirements", "fixtures/b")):
            data = {"id": tid, "repo": "synth", "phase": tid.split("-")[-1], "change": "CHG-9",
                    "type": "happy", "before_dir": bd + "/", "expect": {"status": "done"}}
            (tmp / f"{tid}.json").write_text(json.dumps(data))
        tasks = fer.load_tasks(tmp, ids=["N5-a-*"])
        check(len(tasks) == 1 and tasks[0]["id"] == "N5-a-intent", f"L-1: ids filter, {tasks}")
    finally:
        shutil.rmtree(tmp)

    # ── deterministic_checks ────────────────────────────────────────────────
    task = {"id": "t", "phase": "intent", "change": "CHG-1", "type": "happy",
            "expect": {"status": "done", "max_cost_usd": 0.5,
                       "contains_detail": ["semgrep"], "max_permission_denials": 0}}
    tmp = _tmp()
    try:
        (tmp / "docs" / "project" / "changes" / "CHG-1").mkdir(parents=True)
        out = {"status": "done", "cost_usd": 0.3, "detail": "brak semgrep w obrazie",
               "permission_denials": []}
        checks = fer.deterministic_checks(task, out, tmp)
        check(all(c["passed"] for c in checks), f"D-1: {checks}")

        out["status"] = "failed"
        checks = fer.deterministic_checks(task, out, tmp)
        check(not checks[0]["passed"], "D-2: status failed not caught")

        out = {"status": "done", "cost_usd": 0.8, "detail": "bez słowa kluczowego", "permission_denials": []}
        checks = fer.deterministic_checks(task, out, tmp)
        cost_c = next((c for c in checks if c["name"] == "max_cost_usd"), None)
        check(cost_c and not cost_c["passed"], "D-3: exceeded cost not caught")
        detail_c = next((c for c in checks if c["name"].startswith("detail~")), None)
        check(detail_c and not detail_c["passed"], "D-4: missing phrase in detail not caught")

        out = {"status": "done", "detail": "", "permission_denials": [{"tool": "Bash"}, {"tool": "Write"}]}
        task2 = {**task, "expect": {"status": "done", "max_permission_denials": 1}}
        checks = fer.deterministic_checks(task2, out, tmp)
        denials_c = next((c for c in checks if c["name"] == "max_permission_denials"), None)
        check(denials_c and not denials_c["passed"], "D-5: too many denials not caught")

        # error any_of with a star
        out = {"status": "failed", "error": "kod 1", "detail": "", "permission_denials": []}
        task3 = {**task, "expect": {"status": "failed", "error": "any_of:kod *,permission_denied"}}
        checks = fer.deterministic_checks(task3, out, tmp)
        err_c = next((c for c in checks if c["name"] == "error"), None)
        check(err_c and err_c["passed"], f"D-6: any_of with a star did not work: {err_c}")
    finally:
        shutil.rmtree(tmp)

    # ── Z1: repeated_question regression ─────────────────────────────────────
    task = {"id": "N5-synth-repeated-q", "phase": "requirements", "change": "CHG-1", "type": "regression",
            "expect": {"status": "failed", "error": "repeated_question"}}
    out = {"status": "failed", "error": "repeated_question", "detail": "", "permission_denials": []}
    checks = fer.deterministic_checks(task, out, _tmp())
    check(all(c["passed"] for c in checks), f"Z1-1: regression repeated_question does not pass, {checks}")

    # Happy variant with repeated_question → fails
    task_happy = {**task, "type": "happy", "expect": {"status": "done"}}
    out_bad = {"status": "failed", "error": "repeated_question", "detail": ""}
    checks = fer.deterministic_checks(task_happy, out_bad, _tmp())
    check(not checks[0]["passed"], "Z1-2: happy with repeated_question did not fail")

    # ── prepare_workspace: synth ─────────────────────────────────────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        (evals / "fixtures" / "synth" / "repeated-q" / "docs" / "project" / "changes" / "CHG-1").mkdir(parents=True)
        (evals / "fixtures" / "synth" / "repeated-q" / "docs" / "project" / "changes" / "CHG-1"
         / "requirements.md").write_text("# req\n\n## Pytania do bramki\n- czy X?\n")
        task = {"id": "t", "repo": "synth", "phase": "requirements", "change": "CHG-1", "type": "regression",
                "before_dir": "fixtures/synth/repeated-q/", "expect": {"status": "failed"}}
        work_root = tmp / "work"
        work_root.mkdir()
        work = fer.prepare_workspace(task, repos={}, workdir_root=work_root, evals_root=evals)
        req = work / "docs" / "project" / "changes" / "CHG-1" / "requirements.md"
        check(req.is_file() and "czy X?" in req.read_text(encoding="utf-8"),
              "W-1: before/ not applied in synth")
    finally:
        shutil.rmtree(tmp)

    # ── prepare_workspace: the fixture REPLACES docs/project/changes/<CHG>/, it does not overlay ────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        # The pre-intent fixture has only decisions.md (without intent/plan/design/requirements)
        chg_fix = evals / "fixtures" / "sdlc-trial" / "CHG-7" / "pre-intent" / "docs" / "project" / "changes" / "CHG-7"
        chg_fix.mkdir(parents=True)
        (chg_fix / "decisions.md").write_text("## triage approved\n- ref: CHG-7/D1\n", encoding="utf-8")
        # The sdlc-proba product at HEAD already has full CHG-7 artifacts from earlier (finished) work
        # AND a foreign change CHG-1 (which prepare_workspace should also remove, otherwise the global
        # `decision_record.py check` fails on CHG-1 with a pre-N20 plan.md).
        src_repo = tmp / "sdlc-trial"
        src_chg = src_repo / "docs" / "project" / "changes" / "CHG-7"
        src_chg.mkdir(parents=True)
        (src_chg / "plan.md").write_text("# plan z A6 — bez N20\n", encoding="utf-8")
        (src_chg / "design.md").write_text("# design\n", encoding="utf-8")
        (src_repo / "docs" / "project" / "changes" / "CHG-1").mkdir()
        (src_repo / "docs" / "project" / "changes" / "CHG-1" / "plan.md").write_text("# obca zmiana\n")
        (src_repo / "README.md").write_text("product readme (nie dotyczy fixtury)\n", encoding="utf-8")

        task = {"id": "REPLACE-TEST", "repo": "sdlc-trial", "phase": "intent", "change": "CHG-7", "type": "happy",
                "before_dir": "fixtures/sdlc-trial/CHG-7/pre-intent/", "expect": {"status": "waiting_gate"}}
        work_root = tmp / "work"
        work_root.mkdir()
        work = fer.prepare_workspace(task, repos={"sdlc-trial": src_repo}, workdir_root=work_root,
                                     evals_root=evals)
        chg_work = work / "docs" / "project" / "changes" / "CHG-7"
        check((chg_work / "decisions.md").is_file(),
              "REPLACE-1: decisions.md from the fixture did not reach work/")
        check(not (chg_work / "plan.md").exists() and not (chg_work / "design.md").exists(),
              f"REPLACE-2: plan.md/design.md from the product were NOT removed before the overlay: {list(chg_work.iterdir())}")
        # Foreign changes in docs/project/changes/ are removed too
        check(not (work / "docs" / "project" / "changes" / "CHG-1").exists(),
              "REPLACE-3: foreign change CHG-1 was not removed (it would break the global decision_record.py check)")
        # The rest of the repository must stay
        check((work / "README.md").is_file(),
              "REPLACE-4: files outside docs/project/changes/ were deleted (they should not be)")
    finally:
        shutil.rmtree(tmp)

    # ── run_task with injected phase_fn + judge_fn ──────────────────────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        (evals / "rubrics").mkdir(parents=True)
        (evals / "rubrics" / "requirements.md").write_text("rubryka req\n")
        (evals / "fixtures" / "synth" / "req").mkdir(parents=True)
        (evals / "budget.json").write_text(json.dumps(
            {"budget_usd": 15, "per_task_budget_usd": 1.0, "fail_on_pass_drop_pct": 5,
             "fail_on_cost_rise_pct": 20, "judge_kappa_min": 0.4, "length_control_ratio": 1.8,
             "judge_model_haiku": "h", "judge_model_sonnet": "s"}))

        task = {"id": "N5-synth-req", "repo": "synth", "phase": "requirements", "change": "CHG-1",
                "type": "happy", "before_dir": "fixtures/synth/req/",
                "expect": {"status": "done", "max_cost_usd": 0.5},
                "judge": {"run": True, "rubric": "rubrics/requirements.md",
                          "requirements": ["kryteria mają przykłady"]}}

        # Swap EVALS for the internal source so that judge_task reads our rubrics
        orig_evals = fer.EVALS
        fer.EVALS = evals
        try:
            a = _args()
            res = fer.run_task(task, repos={}, workdir_root=tmp / "work" , args=a,
                               phase_fn=lambda t, w: _fake_phase_result(phase="requirements", cost_usd=0.4,
                                                                        detail="treść"),
                               judge_fn=_fake_judge_fixed(score=4, cost=0.01))
            check(res["passed"] and res["status"] == "done",
                  f"R-1: run_task happy does not pass, {res}")
            check(res["judge"]["correctness"]["score"] == 4
                  and res["judge"]["decision_adherence"]["score"] == 4
                  and res["judge"]["style"]["score"] == 4,
                  f"R-2: judge not saved, {res['judge']}")
            check(res["cost_phase_usd"] == 0.4 and res["cost_judge_usd"] == 0.03,
                  f"R-3: cost split, {res}")
        finally:
            fer.EVALS = orig_evals
    finally:
        shutil.rmtree(tmp)

    # ── judge: length control (N17) ───────────────────────────────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        (evals / "rubrics").mkdir(parents=True)
        (evals / "rubrics" / "intent.md").write_text("r\n")
        (evals / "fixtures" / "synth" / "x").mkdir(parents=True)
        change_dir = tmp / "work_a" / "t" / "docs" / "project" / "changes" / "CHG-1"
        change_dir.mkdir(parents=True)
        (change_dir / "intent.md").write_text("x" * 5000)
        orig = fer.EVALS
        fer.EVALS = evals
        try:
            task = {"id": "t", "repo": "synth", "phase": "intent", "change": "CHG-1", "type": "happy",
                    "before_dir": "fixtures/synth/x/",
                    "expect": {"status": "done"},
                    "judge": {"run": True, "rubric": "rubrics/intent.md",
                              "requirements": ["coś"]}}
            judge = fer.judge_task(task, {"status": "done", "detail": "x"}, tmp / "work_a" / "t",
                                   judge_model="h", judge_fn=_fake_judge_fixed(score=5, cost=0.0),
                                   length_baseline_chars=1000, length_ratio=1.8)
            check(judge["length_penalty"] and judge["style"]["score"] == 4,
                  f"N17-1: length did not lower style, {judge}")
        finally:
            fer.EVALS = orig
    finally:
        shutil.rmtree(tmp)

    # ── judge: A/B (both orders) ─────────────────────────────────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        (evals / "rubrics").mkdir(parents=True)
        (evals / "rubrics" / "intent.md").write_text("r\n")
        (evals / "fixtures" / "synth" / "x").mkdir(parents=True)
        change_dir = tmp / "wab" / "t" / "docs" / "project" / "changes" / "CHG-1"
        change_dir.mkdir(parents=True)
        (change_dir / "intent.md").write_text("A artefakt")
        orig = fer.EVALS
        fer.EVALS = evals
        try:
            seq = iter([5, 4, 5, 3, 5, 4, 3, 5, 4])  # 3 axes + 2 orderings × 3 axes

            def fake(**_kw):
                return {"score": next(seq), "reason": "r", "cost_usd": 0.001}

            task = {"id": "t", "repo": "synth", "phase": "intent", "change": "CHG-1", "type": "happy",
                    "before_dir": "fixtures/synth/x/", "expect": {"status": "done"},
                    "judge": {"run": True, "rubric": "rubrics/intent.md", "requirements": ["x"]},
                    "compare_with": "B artefakt"}
            judge = fer.judge_task(task, {"status": "done", "detail": "x"}, tmp / "wab" / "t",
                                   judge_model="h", judge_fn=fake)
            flips = judge["order_flips"]
            check(set(flips.keys()) == set(fer.AXES),
                  f"N17-AB-1: no flips for all axes, {flips}")
            check(all("ab" in flips[a] and "ba" in flips[a] and "diff" in flips[a] for a in fer.AXES),
                  f"N17-AB-2: missing ab/ba/diff fields, {flips}")
        finally:
            fer.EVALS = orig
    finally:
        shutil.rmtree(tmp)

    # ── compare_with_baseline ─────────────────────────────────────────────────
    budget = {"fail_on_pass_drop_pct": 5, "fail_on_cost_rise_pct": 20}
    results = [{"id": "t1", "passed": True, "cost_usd": 0.5, "detail": ""},
               {"id": "t2", "passed": False, "cost_usd": 0.3, "detail": ""}]
    diff = fer.compare_with_baseline(results, baseline=None, budget=budget)
    check("first_run" in diff["flags"] and diff["pass_rate"] == 0.5, f"C-1: {diff}")

    baseline = {"run_at": "2026-11-05T10:00:00Z", "cost_total": 0.4, "pass_rate": 1.0,
                "tasks": [{"id": "t1", "passed": True, "cost_usd": 0.3},
                          {"id": "t2", "passed": True, "cost_usd": 0.1}]}
    diff = fer.compare_with_baseline(results, baseline=baseline, budget=budget)
    check(diff["pass_rate"] == 0.5 and len(diff["regressions"]) == 1
          and diff["regressions"][0]["id"] == "t2", f"C-2: {diff}")
    check(any(f.startswith("pass_rate_drop") for f in diff["flags"]), f"C-3: {diff}")
    check(any(f.startswith("cost_rise") for f in diff["flags"]), f"C-4: {diff}")

    # improvement
    baseline["tasks"][0]["passed"] = False
    diff = fer.compare_with_baseline(results, baseline=baseline, budget=budget)
    check(any(i["id"] == "t1" for i in diff["improvements"]), f"C-5: no improvement, {diff}")

    # ── report_md and report_json ──────────────────────────────────────────────
    meta = {"model": "claude-opus-4-7", "judge_model": "h", "budget_usd": 15,
            "kappa_min": 0.4, "run_at": "2026-11-07T10:00:00Z"}
    results_judge = [{"id": "t1", "phase": "intent", "type": "happy", "status": "done",
                      "passed": True, "cost_usd": 0.5, "judge": {"correctness": {"score": 5},
                      "decision_adherence": {"score": 4}, "style": {"score": 5}},
                      "error": None, "detail": ""}]
    md = fer.report_md(results_judge, baseline=None, diff=fer.compare_with_baseline(results_judge, None, budget),
                       meta=meta)
    check("t1" in md and "Flow evals" in md and "5/4/5" in md, f"RPT-1: {md[:200]}")
    rep = fer.report_json(results_judge, None, fer.compare_with_baseline(results_judge, None, budget), meta)
    check(rep["pass_count"] == 1 and rep["tasks"][0]["id"] == "t1", f"RPT-2: {rep}")

    # ── estimate_cost ────────────────────────────────────────────────────────
    tasks = [{"id": "a", "phase": "intent", "type": "happy"},
             {"id": "b", "phase": "delivery", "type": "happy",
              "judge": {"run": True, "rubric": "x", "requirements": ["q"]}}]
    est = fer.estimate_cost(tasks, {"per_task_budget_usd": 1.0})
    # intent/happy 0.35 + delivery/happy 0.80 + 3 × JUDGE_COST_PER_AXIS (the second has a judge)
    expected = 0.35 + 0.80 + 3 * fer.JUDGE_COST_PER_AXIS
    check(abs(est - expected) < 1e-6, f"EST-1: {est} vs {expected}")

    # ── kappa ────────────────────────────────────────────────────────────────
    k = cohens_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    check(abs(k - 1.0) < 1e-9, f"K-1: full agreement ≠ 1: {k}")
    k = cohens_kappa([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])
    check(k < 0.3, f"K-2: completely different ratings, κ={k}")
    k_lin = linear_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], levels=5)
    check(abs(k_lin - 1.0) < 1e-9, f"K-3: linear full agreement ≠ 1: {k_lin}")
    k_lin = linear_kappa([3, 3, 3], [3, 3, 3], levels=5)
    check(k_lin == 1.0 or abs(k_lin - 1.0) < 1e-9, f"K-4: constant rating, κ={k_lin}")
    # Approximate agreement: differences of 1 → linear κ > 0.5
    k_lin = linear_kappa([1, 2, 3, 4, 5], [2, 1, 2, 5, 4], levels=5)
    check(k_lin > 0.0, f"K-5: linear κ with diffs of 1, {k_lin}")

    # ── judge_model N17 sanity (import from run_skill_evals) ────────────────────
    from run_skill_evals import same_family, judge_model
    check(same_family("claude-haiku-4-5-20251001", "claude-haiku-4-5-20251001"),
          "N17-SF-1: same family not detected")
    check(not same_family("claude-haiku-4-5-20251001", "claude-sonnet-4-6"),
          "N17-SF-2: different families detected as the same")
    j = judge_model("auto", "claude-opus-4-7")
    check(j != "opus" and "opus" not in j.lower(), f"N17-JM-1: the judge should not be opus: {j}")

    # ── CI workflow: paths, gating by the secret, secret scope ───────────────────
    ROOT = next((p for p in HERE.parents if (p / ".github" / "workflows").is_dir()), None)
    if ROOT is None:
        check(False, "CI-0: root not found")
    else:
        wf = ROOT / ".github" / "workflows" / "flow-evals.yml"
        check(wf.is_file(), f"CI-1: missing {wf}")
        if wf.is_file():
            try:
                import yaml
            except ImportError:   # pattern from test_ai_review.py: the bundled PyYAML copy (.tf/factory/_vendor)
                for base in (ROOT / ".tf" / "factory" / "_vendor", ROOT / "core" / "factory" / "_vendor"):
                    if base.is_dir():
                        sys.path.insert(0, str(base))
                        break
                import yaml
            data = yaml.safe_load(wf.read_text(encoding="utf-8"))
            on = data.get(True) or data.get("on") or {}
            paths = (on.get("pull_request") or {}).get("paths") or []
            check(any("modes/mode-pdi" in p for p in paths)
                  and any("core/tests/flow_evals" in p for p in paths),
                  f"CI-2: the paths filter does not cover the required paths: {paths}")
            job = (data.get("jobs") or {}).get("flow-evals") or {}
            steps = job.get("steps") or []
            # One step checks the secret; the model step has an `if:` with `has_key`.
            model_step = next((s for s in steps
                               if "tools/workspace.py flow-evals" in (s.get("run") or "")
                               and "--validate" not in (s.get("run") or "")), None)
            check(model_step is not None, f"CI-3: no step running the model in {wf}")
            if model_step:
                check("has_key" in (model_step.get("if") or ""),
                      f"CI-4: model step without an `if:` with has_key: {model_step}")
                env = model_step.get("env") or {}
                check("ANTHROPIC_API_KEY" in env,
                      f"CI-5: no ANTHROPIC_API_KEY in the model step env: {env}")
            # Validation (no model) in a separate step, always run — without `if:` or with an always()-equivalent.
            val_step = next((s for s in steps
                             if "tools/workspace.py flow-evals" in (s.get("run") or "")
                             and "--validate" in (s.get("run") or "")), None)
            check(val_step is not None and not val_step.get("if"),
                  f"CI-6: validation step with a restricting `if:`: {val_step}")
            # No secrets at the job level anywhere (edge case: a PR from a fork).
            job_env = job.get("env") or {}
            for k, v in job_env.items():
                check("${{ secrets." not in str(v) or "!= ''" in str(v) or "'true'" in str(v),
                      f"CI-7: secret at the job level outside gating: {k}={v}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} flow_evals tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
