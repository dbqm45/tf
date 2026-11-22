#!/usr/bin/env python3
"""
Triage of a pdi report (F3) — mode-pdi. The triage procedure: skill proc-issue-triage; this script checks the input
and assembles a recommendation in pdi states (contract 0.14.0, R7).

  python3 .claude/skills/pdi-decisions/scripts/triage_pdi.py check <prb.json>
      a PRB report in JSON against contract/problem.schema.json (a copy next to the script); triage only for the states
      new, clarifying, ready_for_triage
  python3 .claude/skills/pdi-decisions/scripts/triage_pdi.py recommend <prb.json> --status S --rationale "…" […]
      S: clarifying (--question … ×n) · accepted (--brief "…", --executor agent|human) · rejected (--reason R
      [--note "…"], with out_of_scope_recorded --out-of-scope-file .out-of-scope/<concept>.md) · parked
      (--return-when "…") · duplicate (--duplicate-of PRB-n); opcjonalnie --category bug|enhancement,
      --observation "…" and --evidence "…" (evidence: an observation or an AI conclusion), --out FILE
      recommendation JSON (triage-recommendation.schema.json next to the script) with tf_state from the contract's mapping table.

A recommendation does not change the report: a human makes the decision in pdi, and the change (CHG) is created by pdi after acceptance.
Exit code: 0 — OK, 1 — errors (with a hint), 2 — bad invocation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decision_record import validate  # noqa: E402  (the same JSON Schema subset validator as for release.yaml)

CONTRACT = "0.14.0"
PROBLEM_SCHEMA = HERE / "problem.schema.json"                  # kopia z kontraktu pdi (tools/pdi-contract.json)
RECOMMENDATION_SCHEMA = HERE / "triage-recommendation.schema.json"   # kopia z kontraktu pdi (tools/pdi-contract.json)
TRIAGE_INPUT = ("new", "clarifying", "ready_for_triage")
# The table „Stany zgłoszenia i mapowanie na tf” (report states and mapping to tf) from contract/README.md (R7).
TF_STATE = {"clarifying": "needs-info", "rejected": "wontfix", "duplicate": "wontfix", "parked": "needs-triage"}
REASONS = ("out_of_strategy", "works_as_designed", "cost_disproportionate", "already_exists", "out_of_scope_recorded",
           "other")


def load(path: str) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        return None, [f"cannot read {path}: {e}"]
    except ValueError as e:
        return None, [f"invalid JSON in {path}: {e}"]
    return (data, []) if isinstance(data, dict) else (None, [f"{path}: expected a JSON object (a PRB problem)"])


def check_problem(data: dict) -> list[str]:
    errs = [f"contract schema: {e}" for e in validate(data, json.loads(PROBLEM_SCHEMA.read_text(encoding="utf-8")), "")]
    if not errs and data["status"] not in TRIAGE_INPUT:
        errs.append(f"status '{data['status']}' — already triaged (the decision belongs to pdi); triage only for: "
                    f"{', '.join(TRIAGE_INPUT)}")
    return errs


def build(prb: dict, a) -> tuple[dict, list[str]]:
    errs = []
    if a.status not in ("clarifying", "accepted", "rejected", "parked", "duplicate"):
        errs.append(f"--status '{a.status}' — the recommendation is clarifying, accepted, rejected, parked or duplicate "
                    "(new and ready_for_triage are input states)")
    rec = {"problem": prb["id"], "contract_version": CONTRACT, "recommended_status": a.status,
           "tf_state": "ready-for-human" if a.executor == "human" else TF_STATE.get(a.status, "ready-for-agent"),
           "rationale": (a.rationale or "").strip(), "drafted_by": "ai"}
    if not rec["rationale"]:
        errs.append("no --rationale (the reason for the recommendation, for the PO)")
    if a.status == "parked":
        rec["tf_labels"] = ["deferred"]
    if a.category or prb.get("category"):
        rec["category"] = a.category or prb["category"]
    if a.status == "clarifying":
        if not a.question:
            errs.append("clarifying needs questions for the reporter: --question \"…\" (specific, not „tell us more”)")
        rec["questions"] = a.question
    if a.status == "accepted":
        if not (a.brief or "").strip():
            errs.append("accepted needs a brief for the executor: --brief \"…\" (format from proc-issue-triage)")
        rec.update(brief=a.brief, executor=a.executor or "agent")
    if a.status == "rejected":
        if not a.reason:
            errs.append(f"rejected needs a reason: --reason {'|'.join(REASONS)}")
        elif a.reason not in REASONS:
            errs.append(f"--reason '{a.reason}' is not in the contract list: {', '.join(REASONS)}")
        rec["rejection_reason"] = a.reason
        if a.note:
            rec["rejection_note"] = a.note
        if a.reason == "out_of_scope_recorded":
            f = a.out_of_scope_file
            if not f or not Path(f).is_file() or not f.startswith(".out-of-scope/"):
                errs.append("out_of_scope_recorded needs an existing entry: --out-of-scope-file .out-of-scope/<concept>.md")
            rec["out_of_scope_file"] = f
    if a.status == "parked":
        if not a.return_when:
            errs.append("parked needs a return threshold: --return-when \"…\" (e.g. 3 new problems or an incident)")
        rec["return_when"] = a.return_when
    if a.status == "duplicate":
        if not a.duplicate_of:
            errs.append("duplicate needs the original: --duplicate-of PRB-n")
        elif a.duplicate_of == prb["id"]:
            errs.append(f"--duplicate-of {a.duplicate_of} — a problem cannot duplicate itself")
        rec["duplicate_of"] = a.duplicate_of
    evidence = [{"text": t, "epistemic_status": "observation"} for t in a.observation or []]
    evidence += [{"text": t, "epistemic_status": "ai_inference"} for t in a.evidence or []]
    if evidence:
        rec["evidence"] = evidence
    rec = {k: v for k, v in rec.items() if v is not None}
    if not errs:
        errs = [f"recommendation schema: {e}" for e in
                validate(rec, json.loads(RECOMMENDATION_SCHEMA.read_text(encoding="utf-8")), "")]
    return rec, errs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("prb")
    r = sub.add_parser("recommend")
    r.add_argument("prb")
    r.add_argument("--status", required=True)
    r.add_argument("--rationale")
    r.add_argument("--category", choices=("bug", "enhancement"))
    r.add_argument("--question", action="append")
    r.add_argument("--brief")
    r.add_argument("--executor", choices=("agent", "human"))
    r.add_argument("--reason")
    r.add_argument("--note")
    r.add_argument("--out-of-scope-file")
    r.add_argument("--return-when")
    r.add_argument("--duplicate-of")
    r.add_argument("--observation", action="append")
    r.add_argument("--evidence", action="append")
    r.add_argument("--out")
    a = ap.parse_args(argv)
    prb, errs = load(a.prb)
    errs = errs or check_problem(prb)
    if a.cmd == "check" or errs:
        for e in errs:
            print(f"✗ {a.prb}: {e}")
        if not errs:
            print(f"✓ {prb['id']} ({prb['status']}) — matches pdi contract {CONTRACT}, ready for triage")
        return 1 if errs else 0
    rec, errs = build(prb, a)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        return 1
    text = json.dumps(rec, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
