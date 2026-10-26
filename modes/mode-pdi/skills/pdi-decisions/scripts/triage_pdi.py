#!/usr/bin/env python3
"""
Triaż zgłoszenia z pdi (F3) — tryb mode-pdi. Procedura triażu: skill proc-issue-triage; ten skrypt sprawdza wejście
i składa rekomendację w stanach pdi (kontrakt 0.6.0, R7).

  python3 .claude/skills/pdi-decisions/scripts/triage_pdi.py check <prb.json>
      zgłoszenie PRB w JSON wobec contract/problem.schema.json (kopia obok skryptu); triaż tylko dla stanów
      new, clarifying, ready_for_triage
  python3 .claude/skills/pdi-decisions/scripts/triage_pdi.py recommend <prb.json> --status S --rationale "…" […]
      S: clarifying (--question … ×n) · accepted (--brief "…", --executor agent|human) · rejected (--reason R
      [--note "…"], przy out_of_scope_recorded --out-of-scope-file .out-of-scope/<pojęcie>.md) · parked
      (--return-when "…") · duplicate (--duplicate-of PRB-n); opcjonalnie --category bug|enhancement,
      --observation "…" i --evidence "…" (dowody: obserwacja albo wniosek AI), --out PLIK
      JSON rekomendacji (triage-recommendation.schema.json obok skryptu) z tf_state z tabeli mapowania kontraktu.

Rekomendacja nie zmienia zgłoszenia: decyzję podejmuje człowiek w pdi, a zmianę (CHG) tworzy pdi po przyjęciu.
Kod wyjścia: 0 — w porządku, 1 — błędy (z podpowiedzią), 2 — złe wywołanie.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from decision_record import validate  # noqa: E402  (ten sam walidator podzbioru JSON Schema co dla release.yaml)

CONTRACT = "0.6.0"
PROBLEM_SCHEMA = HERE / "problem.schema.json"                  # kopia z kontraktu pdi 0.6.0
RECOMMENDATION_SCHEMA = HERE / "triage-recommendation.schema.json"   # kopia z kontraktu pdi 0.6.0
TRIAGE_INPUT = ("new", "clarifying", "ready_for_triage")
# Tabela „Stany zgłoszenia i mapowanie na tf” z contract/README.md (R7).
TF_STATE = {"clarifying": "needs-info", "rejected": "wontfix", "duplicate": "wontfix", "parked": "needs-triage"}
REASONS = ("out_of_strategy", "works_as_designed", "cost_disproportionate", "already_exists", "out_of_scope_recorded",
           "other")


def load(path: str) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        return None, [f"nie mogę odczytać {path}: {e}"]
    except ValueError as e:
        return None, [f"niepoprawny JSON w {path}: {e}"]
    return (data, []) if isinstance(data, dict) else (None, [f"{path}: oczekiwano obiektu JSON (zgłoszenie PRB)"])


def check_problem(data: dict) -> list[str]:
    errs = [f"schemat kontraktu: {e}" for e in validate(data, json.loads(PROBLEM_SCHEMA.read_text(encoding="utf-8")), "")]
    if not errs and data["status"] not in TRIAGE_INPUT:
        errs.append(f"status '{data['status']}' — triaż już był (decyzja należy do pdi); triaż tylko dla: "
                    f"{', '.join(TRIAGE_INPUT)}")
    return errs


def build(prb: dict, a) -> tuple[dict, list[str]]:
    errs = []
    if a.status not in ("clarifying", "accepted", "rejected", "parked", "duplicate"):
        errs.append(f"--status '{a.status}' — rekomendacja to clarifying, accepted, rejected, parked albo duplicate "
                    "(new i ready_for_triage to stany wejścia)")
    rec = {"problem": prb["id"], "contract_version": CONTRACT, "recommended_status": a.status,
           "tf_state": "ready-for-human" if a.executor == "human" else TF_STATE.get(a.status, "ready-for-agent"),
           "rationale": (a.rationale or "").strip(), "drafted_by": "ai"}
    if not rec["rationale"]:
        errs.append("brak --rationale (uzasadnienie rekomendacji dla PO)")
    if a.status == "parked":
        rec["tf_labels"] = ["deferred"]
    if a.category or prb.get("category"):
        rec["category"] = a.category or prb["category"]
    if a.status == "clarifying":
        if not a.question:
            errs.append("clarifying wymaga pytań do zgłaszającego: --question \"…\" (konkretne, nie „podaj więcej”)")
        rec["questions"] = a.question
    if a.status == "accepted":
        if not (a.brief or "").strip():
            errs.append("accepted wymaga briefu dla wykonawcy: --brief \"…\" (format z proc-issue-triage)")
        rec.update(brief=a.brief, executor=a.executor or "agent")
    if a.status == "rejected":
        if not a.reason:
            errs.append(f"rejected wymaga powodu: --reason {'|'.join(REASONS)}")
        elif a.reason not in REASONS:
            errs.append(f"--reason '{a.reason}' spoza listy kontraktu: {', '.join(REASONS)}")
        rec["rejection_reason"] = a.reason
        if a.note:
            rec["rejection_note"] = a.note
        if a.reason == "out_of_scope_recorded":
            f = a.out_of_scope_file
            if not f or not Path(f).is_file() or not f.startswith(".out-of-scope/"):
                errs.append("out_of_scope_recorded wymaga istniejącego wpisu: --out-of-scope-file .out-of-scope/<pojęcie>.md")
            rec["out_of_scope_file"] = f
    if a.status == "parked":
        if not a.return_when:
            errs.append("parked wymaga progu powrotu: --return-when \"…\" (np. 3 nowe zgłoszenia albo incydent)")
        rec["return_when"] = a.return_when
    if a.status == "duplicate":
        if not a.duplicate_of:
            errs.append("duplicate wymaga oryginału: --duplicate-of PRB-n")
        elif a.duplicate_of == prb["id"]:
            errs.append(f"--duplicate-of {a.duplicate_of} — zgłoszenie nie jest duplikatem samego siebie")
        rec["duplicate_of"] = a.duplicate_of
    evidence = [{"text": t, "epistemic_status": "observation"} for t in a.observation or []]
    evidence += [{"text": t, "epistemic_status": "ai_inference"} for t in a.evidence or []]
    if evidence:
        rec["evidence"] = evidence
    rec = {k: v for k, v in rec.items() if v is not None}
    if not errs:
        errs = [f"schemat rekomendacji: {e}" for e in
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
            print(f"✓ {prb['id']} ({prb['status']}) — zgodne z kontraktem pdi {CONTRACT}, gotowe do triażu")
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
