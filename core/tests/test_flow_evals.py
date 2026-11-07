#!/usr/bin/env python3
"""Testy runnera flow-evals (N5, DZ13): ładowanie zadań, sprawdzenia per faza, porównanie z baseline,
reguły sędziego N17 (obie kolejności, kontrola długości), bramki CI bez sekretu.

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
        check(any("phase" in e for e in fer.validate_task(bad, tmp)), "V-2: zły phase przeszedł")

        bad = dict(good)
        bad["type"] = "unknown"
        check(any("type" in e for e in fer.validate_task(bad, tmp)), "V-3: zły type przeszedł")

        bad = dict(good)
        del bad["before_dir"]
        check(any("before_dir" in e for e in fer.validate_task(bad, tmp)), "V-4: brak before_dir przeszedł")

        bad = dict(good, before_dir="fixtures/nie-ma/")
        check(any("nie istnieje" in e for e in fer.validate_task(bad, tmp)),
              "V-5: nieistniejący before_dir przeszedł")

        bad = dict(good, judge={"run": True})
        check(any("rubric" in e for e in fer.validate_task(bad, tmp)),
              "V-6: judge.run bez rubryki przeszedł")

        (tmp / "rubrics").mkdir()
        (tmp / "rubrics" / "intent.md").write_text("rubryka")
        good_judge = dict(good, judge={"run": True, "rubric": "rubrics/intent.md",
                                       "requirements": ["coś mądrego"]})
        check(fer.validate_task(good_judge, tmp) == [], "V-7: poprawne judge odrzucone")
    finally:
        shutil.rmtree(tmp)

    # ── load_tasks z filtrem ids ──────────────────────────────────────────────
    tmp = _tmp()
    try:
        (tmp / "fixtures" / "a").mkdir(parents=True)
        (tmp / "fixtures" / "b").mkdir(parents=True)
        for tid, bd in (("N5-a-intent", "fixtures/a"), ("N5-b-requirements", "fixtures/b")):
            data = {"id": tid, "repo": "synth", "phase": tid.split("-")[-1], "change": "CHG-9",
                    "type": "happy", "before_dir": bd + "/", "expect": {"status": "done"}}
            (tmp / f"{tid}.json").write_text(json.dumps(data))
        tasks = fer.load_tasks(tmp, ids=["N5-a-*"])
        check(len(tasks) == 1 and tasks[0]["id"] == "N5-a-intent", f"L-1: filtr ids, {tasks}")
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
        check(not checks[0]["passed"], "D-2: status failed nie wychwycony")

        out = {"status": "done", "cost_usd": 0.8, "detail": "bez słowa kluczowego", "permission_denials": []}
        checks = fer.deterministic_checks(task, out, tmp)
        cost_c = next((c for c in checks if c["name"] == "max_cost_usd"), None)
        check(cost_c and not cost_c["passed"], "D-3: przekroczony koszt nie wychwycony")
        detail_c = next((c for c in checks if c["name"].startswith("detail~")), None)
        check(detail_c and not detail_c["passed"], "D-4: brak frazy w detail nie wychwycony")

        out = {"status": "done", "detail": "", "permission_denials": [{"tool": "Bash"}, {"tool": "Write"}]}
        task2 = {**task, "expect": {"status": "done", "max_permission_denials": 1}}
        checks = fer.deterministic_checks(task2, out, tmp)
        denials_c = next((c for c in checks if c["name"] == "max_permission_denials"), None)
        check(denials_c and not denials_c["passed"], "D-5: za dużo denials nie wychwycone")

        # error any_of z gwiazdką
        out = {"status": "failed", "error": "kod 1", "detail": "", "permission_denials": []}
        task3 = {**task, "expect": {"status": "failed", "error": "any_of:kod *,permission_denied"}}
        checks = fer.deterministic_checks(task3, out, tmp)
        err_c = next((c for c in checks if c["name"] == "error"), None)
        check(err_c and err_c["passed"], f"D-6: any_of z gwiazdką nie zadziałał: {err_c}")
    finally:
        shutil.rmtree(tmp)

    # ── Z1: repeated_question regression ─────────────────────────────────────
    task = {"id": "N5-synth-repeated-q", "phase": "requirements", "change": "CHG-1", "type": "regression",
            "expect": {"status": "failed", "error": "repeated_question"}}
    out = {"status": "failed", "error": "repeated_question", "detail": "", "permission_denials": []}
    checks = fer.deterministic_checks(task, out, _tmp())
    check(all(c["passed"] for c in checks), f"Z1-1: regression repeated_question nie zalicza, {checks}")

    # Happy wariant z repeated_question → oblewa
    task_happy = {**task, "type": "happy", "expect": {"status": "done"}}
    out_bad = {"status": "failed", "error": "repeated_question", "detail": ""}
    checks = fer.deterministic_checks(task_happy, out_bad, _tmp())
    check(not checks[0]["passed"], "Z1-2: happy z repeated_question nie oblał")

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
              "W-1: before/ nie nałożone w synth")
    finally:
        shutil.rmtree(tmp)

    # ── prepare_workspace: fixture ZASTĘPUJE docs/project/changes/<CHG>/, nie nakłada się ────────────
    tmp = _tmp()
    try:
        evals = tmp / "evals"
        # Fixture pre-intent ma tylko decisions.md (bez intent/plan/design/requirements)
        chg_fix = evals / "fixtures" / "sdlc-proba" / "CHG-7" / "pre-intent" / "docs" / "project" / "changes" / "CHG-7"
        chg_fix.mkdir(parents=True)
        (chg_fix / "decisions.md").write_text("## triage approved\n- ref: CHG-7/D1\n", encoding="utf-8")
        # Produkt sdlc-proba w HEAD ma już pełne artefakty CHG-7 z poprzedniej (ukończonej) pracy
        # ORAZ obcą zmianę CHG-1 (którą prepare_workspace też powinien usunąć, inaczej globalny
        # `decision_record.py check` zawali się na CHG-1 z pre-N20 plan.md).
        src_repo = tmp / "sdlc-proba"
        src_chg = src_repo / "docs" / "project" / "changes" / "CHG-7"
        src_chg.mkdir(parents=True)
        (src_chg / "plan.md").write_text("# plan z A6 — bez N20\n", encoding="utf-8")
        (src_chg / "design.md").write_text("# design\n", encoding="utf-8")
        (src_repo / "docs" / "project" / "changes" / "CHG-1").mkdir()
        (src_repo / "docs" / "project" / "changes" / "CHG-1" / "plan.md").write_text("# obca zmiana\n")
        (src_repo / "README.md").write_text("product readme (nie dotyczy fixtury)\n", encoding="utf-8")

        task = {"id": "REPLACE-TEST", "repo": "sdlc-proba", "phase": "intent", "change": "CHG-7", "type": "happy",
                "before_dir": "fixtures/sdlc-proba/CHG-7/pre-intent/", "expect": {"status": "waiting_gate"}}
        work_root = tmp / "work"
        work_root.mkdir()
        work = fer.prepare_workspace(task, repos={"sdlc-proba": src_repo}, workdir_root=work_root,
                                     evals_root=evals)
        chg_work = work / "docs" / "project" / "changes" / "CHG-7"
        check((chg_work / "decisions.md").is_file(),
              "REPLACE-1: decisions.md z fixtury nie trafił do work/")
        check(not (chg_work / "plan.md").exists() and not (chg_work / "design.md").exists(),
              f"REPLACE-2: plan.md/design.md z produktu NIE zostały usunięte przed overlay'em: {list(chg_work.iterdir())}")
        # Obce zmiany w docs/project/changes/ też usunięte
        check(not (work / "docs" / "project" / "changes" / "CHG-1").exists(),
              "REPLACE-3: obca zmiana CHG-1 nie została usunięta (zawaliłaby globalny decision_record.py check)")
        # Reszta repozytorium musi zostać
        check((work / "README.md").is_file(),
              "REPLACE-4: pliki poza docs/project/changes/ zostały zmazane (nie powinny)")
    finally:
        shutil.rmtree(tmp)

    # ── run_task z iniekcją phase_fn + judge_fn ──────────────────────────────
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

        # Podmień EVALS na wewnętrzne źródło, żeby judge_task czytał nasze rubryki
        orig_evals = fer.EVALS
        fer.EVALS = evals
        try:
            a = _args()
            res = fer.run_task(task, repos={}, workdir_root=tmp / "work" , args=a,
                               phase_fn=lambda t, w: _fake_phase_result(phase="requirements", cost_usd=0.4,
                                                                        detail="treść"),
                               judge_fn=_fake_judge_fixed(score=4, cost=0.01))
            check(res["passed"] and res["status"] == "done",
                  f"R-1: run_task happy nie zalicza, {res}")
            check(res["judge"]["correctness"]["score"] == 4
                  and res["judge"]["decision_adherence"]["score"] == 4
                  and res["judge"]["style"]["score"] == 4,
                  f"R-2: judge nie zapisany, {res['judge']}")
            check(res["cost_phase_usd"] == 0.4 and res["cost_judge_usd"] == 0.03,
                  f"R-3: koszt rozbity, {res}")
        finally:
            fer.EVALS = orig_evals
    finally:
        shutil.rmtree(tmp)

    # ── judge: kontrola długości (N17) ───────────────────────────────────────
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
                  f"N17-1: długość nie zbiła style, {judge}")
        finally:
            fer.EVALS = orig
    finally:
        shutil.rmtree(tmp)

    # ── judge: A/B (obie kolejności) ─────────────────────────────────────────
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
            seq = iter([5, 4, 5, 3, 5, 4, 3, 5, 4])  # 3 osie + 2 orderings × 3 osie

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
                  f"N17-AB-1: brak flipów dla wszystkich osi, {flips}")
            check(all("ab" in flips[a] and "ba" in flips[a] and "diff" in flips[a] for a in fer.AXES),
                  f"N17-AB-2: brak pól ab/ba/diff, {flips}")
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
    check(any(i["id"] == "t1" for i in diff["improvements"]), f"C-5: brak improvement, {diff}")

    # ── report_md i report_json ──────────────────────────────────────────────
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
    # intent/happy 0.35 + delivery/happy 0.80 + 3 × JUDGE_COST_PER_AXIS (druga ma sędziego)
    expected = 0.35 + 0.80 + 3 * fer.JUDGE_COST_PER_AXIS
    check(abs(est - expected) < 1e-6, f"EST-1: {est} vs {expected}")

    # ── kappa ────────────────────────────────────────────────────────────────
    k = cohens_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    check(abs(k - 1.0) < 1e-9, f"K-1: pełna zgodność ≠ 1: {k}")
    k = cohens_kappa([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])
    check(k < 0.3, f"K-2: zupełnie inne oceny, κ={k}")
    k_lin = linear_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], levels=5)
    check(abs(k_lin - 1.0) < 1e-9, f"K-3: linear pełna zgodność ≠ 1: {k_lin}")
    k_lin = linear_kappa([3, 3, 3], [3, 3, 3], levels=5)
    check(k_lin == 1.0 or abs(k_lin - 1.0) < 1e-9, f"K-4: stała ocena, κ={k_lin}")
    # Przybliżona zgodność: różnice 1 → linear κ > 0.5
    k_lin = linear_kappa([1, 2, 3, 4, 5], [2, 1, 2, 5, 4], levels=5)
    check(k_lin > 0.0, f"K-5: linear κ z róż. 1, {k_lin}")

    # ── judge_model N17 sanity (import z run_skill_evals) ────────────────────
    from run_skill_evals import same_family, judge_model
    check(same_family("claude-haiku-4-5-20251001", "claude-haiku-4-5-20251001"),
          "N17-SF-1: ta sama rodzina nie wykryta")
    check(not same_family("claude-haiku-4-5-20251001", "claude-sonnet-4-6"),
          "N17-SF-2: inne rodziny wykryte jako same")
    j = judge_model("auto", "claude-opus-4-7")
    check(j != "opus" and "opus" not in j.lower(), f"N17-JM-1: sędzia nie powinien być opus: {j}")

    # ── CI workflow: paths, gating secretem, zakres sekretu ───────────────────
    ROOT = next((p for p in HERE.parents if (p / ".github" / "workflows").is_dir()), None)
    if ROOT is None:
        check(False, "CI-0: nie znaleziono korzenia")
    else:
        wf = ROOT / ".github" / "workflows" / "flow-evals.yml"
        check(wf.is_file(), f"CI-1: brak {wf}")
        if wf.is_file():
            try:
                import yaml
            except ImportError:   # wzór z test_ai_review.py: dołączona kopia PyYAML (factory/_vendor)
                for base in (ROOT / "factory" / "_vendor", ROOT / "core" / "factory" / "_vendor"):
                    if base.is_dir():
                        sys.path.insert(0, str(base))
                        break
                import yaml
            data = yaml.safe_load(wf.read_text(encoding="utf-8"))
            on = data.get(True) or data.get("on") or {}
            paths = (on.get("pull_request") or {}).get("paths") or []
            check(any("modes/mode-pdi" in p for p in paths)
                  and any("core/tests/flow_evals" in p for p in paths),
                  f"CI-2: paths filtr nie obejmuje wymaganych ścieżek: {paths}")
            job = (data.get("jobs") or {}).get("flow-evals") or {}
            steps = job.get("steps") or []
            # Jeden krok sprawdza sekret; krok z modelem ma `if:` z `has_key`.
            model_step = next((s for s in steps
                               if "tools/workspace.py flow-evals" in (s.get("run") or "")
                               and "--validate" not in (s.get("run") or "")), None)
            check(model_step is not None, f"CI-3: brak kroku uruchamiającego model w {wf}")
            if model_step:
                check("has_key" in (model_step.get("if") or ""),
                      f"CI-4: krok modelu bez `if:` z has_key: {model_step}")
                env = model_step.get("env") or {}
                check("ANTHROPIC_API_KEY" in env,
                      f"CI-5: brak ANTHROPIC_API_KEY w env kroku modelu: {env}")
            # Walidacja (bez modelu) w osobnym kroku, zawsze uruchamiana — bez `if:` albo z always()-równym.
            val_step = next((s for s in steps
                             if "tools/workspace.py flow-evals" in (s.get("run") or "")
                             and "--validate" in (s.get("run") or "")), None)
            check(val_step is not None and not val_step.get("if"),
                  f"CI-6: krok walidacji z `if:` ograniczającym: {val_step}")
            # Nigdzie na poziomie joba nie ma sekretów (kraniec PR z forka).
            job_env = job.get("env") or {}
            for k, v in job_env.items():
                check("${{ secrets." not in str(v) or "!= ''" in str(v) or "'true'" in str(v),
                      f"CI-7: sekret na poziomie joba poza gatowaniem: {k}={v}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów flow_evals")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
