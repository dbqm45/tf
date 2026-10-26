#!/usr/bin/env python3
"""Testy triażu zgłoszenia z pdi (tryb mode-pdi, skill pdi-decisions, scripts/triage_pdi.py): wejście PRB w JSON
sprawdzane schematem kontraktu pdi 0.4.0 (problem.schema.json), rekomendacja w stanach pdi (R7) z polami wymaganymi
przy danym stanie i stanem tf z tabeli mapowania (contract/README.md). python3 .claude/tests/test_triage_pdi.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "triage_pdi.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-contract"   # kopia kontraktu pdi 0.4.0 (bez zmian)


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def new_problem(**changes) -> dict:
    """Przykład z kontraktu jako zgłoszenie przed triażem (bez zmiany i decyzji)."""
    p = json.loads((FIX / "problem.json").read_text(encoding="utf-8"))
    for k in ("change", "triage_decision"):
        p.pop(k, None)
    p["status"] = "new"
    p.update(changes)
    return {k: v for k, v in p.items() if v is not None}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if SCRIPT is None:
        print(f"✗ brak skryptu {REL}")
        return 1
    near = SCRIPT.parent / "problem.schema.json"
    check(near.is_file() and json.loads(near.read_text(encoding="utf-8"))
          == json.loads((FIX / "problem.schema.json").read_text(encoding="utf-8")),
          "P-0: schemat zgłoszenia obok skryptu = kopia z kontraktu pdi 0.4.0")

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        def write(name: str, data: dict) -> str:
            (d / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return name

        prb = write("prb.json", new_problem())
        r = run(["check", prb], d)
        check(r.returncode == 0, f"P-1: zgłoszenie z kontraktu (status new) przechodzi check: {r.stdout}{r.stderr}")
        bad = {
            "brak who": (new_problem(who=None), "who"),
            "zły klucz": (new_problem(id="prb-34"), "prb-34"),
            "nieznane pole": (new_problem(priority="high"), "priority"),
            "rejected bez powodu": (new_problem(status="rejected"), "rejection_reason"),
            "zły kanał": (new_problem(channel="email"), "email"),
            "triaż już był": (new_problem(status="accepted", change="CHG-12"), "accepted"),
        }
        for label, (data, needle) in bad.items():
            r = run(["check", write("bad.json", data)], d)
            check(r.returncode == 1 and needle in r.stdout, f"P-2 check odrzuca: {label}: {r.stdout}{r.stderr}")
        r = run(["check", write("bad.json", {"id": "PRB-1"})], d)
        check(r.returncode == 1 and "Traceback" not in r.stderr, f"P-3: niepełne zgłoszenie bez wyjątku: {r.stderr[-200:]}")
        (d / "zly.json").write_text("{nie json", encoding="utf-8")
        r = run(["check", "zly.json"], d)
        check(r.returncode == 1 and "JSON" in r.stdout, f"P-4: niepoprawny JSON: {r.stdout}{r.stderr}")

        def rec(*args):
            r = run(["recommend", prb, *args], d)
            try:
                return r, json.loads(r.stdout) if r.returncode == 0 else {}
            except ValueError:
                return r, {}

        r, out = rec("--status", "accepted", "--category", "enhancement", "--executor", "agent",
                     "--rationale", "5 zgłoszeń w 3 miesiące, dzień pracy przy każdej zmianie taryfy",
                     "--brief", "## Brief dla wykonawcy\n**W skrócie:** zmiana konfiguracji wielu ładowarek naraz",
                     "--observation", "5 zgłoszeń o tym samym w 3 miesiące", "--evidence", "taryfa to częsty przypadek")
        check(r.returncode == 0 and out.get("problem") == "PRB-34" and out.get("recommended_status") == "accepted"
              and out.get("tf_state") == "ready-for-agent" and "change" not in out and out.get("drafted_by") == "ai"
              and out.get("contract_version") == "0.4.0",
              f"R-1: accepted → ready-for-agent, bez change (tworzy pdi): {r.stdout}{r.stderr}")
        ev = {e["epistemic_status"] for e in out.get("evidence", [])}
        check(ev == {"observation", "ai_inference"}, f"R-2: dowody z epistemic_status: {out.get('evidence')}")
        r, out = rec("--status", "accepted", "--executor", "human", "--rationale", "wymaga decyzji o cenniku",
                     "--brief", "brief")
        check(out.get("tf_state") == "ready-for-human", f"R-3: accepted z człowiekiem → ready-for-human: {out}")
        r, out = rec("--status", "clarifying", "--rationale", "nie wiadomo, które ładowarki",
                     "--question", "Ile ładowarek zmieniasz naraz?", "--question", "Jakie parametry?")
        check(out.get("tf_state") == "needs-info" and len(out.get("questions", [])) == 2,
              f"R-4: clarifying → needs-info z pytaniami: {r.stdout}{r.stderr}")
        r, out = rec("--status", "rejected", "--reason", "works_as_designed", "--rationale", "import CSV już to robi",
                     "--note", "Ustawienia → Import")
        check(out.get("tf_state") == "wontfix" and out.get("rejection_reason") == "works_as_designed",
              f"R-5: rejected → wontfix z powodem: {r.stdout}{r.stderr}")
        r, out = rec("--status", "parked", "--return-when", "3 nowe zgłoszenia", "--rationale", "mało zgłoszeń")
        check(out.get("tf_state") == "needs-triage" and out.get("tf_labels") == ["deferred"]
              and out.get("return_when") == "3 nowe zgłoszenia", f"R-6: parked → needs-triage + deferred: {r.stdout}")
        r, out = rec("--status", "duplicate", "--duplicate-of", "PRB-12", "--rationale", "to samo co PRB-12")
        check(out.get("tf_state") == "wontfix" and out.get("duplicate_of") == "PRB-12", f"R-7: duplicate: {r.stdout}")
        (d / ".out-of-scope").mkdir()
        (d / ".out-of-scope" / "operacje-masowe.md").write_text("# Operacje masowe\n", encoding="utf-8")
        r, out = rec("--status", "rejected", "--reason", "out_of_scope_recorded", "--rationale", "decyzja z 2026",
                     "--out-of-scope-file", ".out-of-scope/operacje-masowe.md")
        check(r.returncode == 0 and out.get("out_of_scope_file") == ".out-of-scope/operacje-masowe.md",
              f"R-8: odrzucenie z wpisem w .out-of-scope/: {r.stdout}{r.stderr}")

        missing = {
            "clarifying bez pytań": (["--status", "clarifying", "--rationale", "x"], "question"),
            "rejected bez powodu": (["--status", "rejected", "--rationale", "x"], "reason"),
            "zły powód": (["--status", "rejected", "--reason", "too_hard", "--rationale", "x"], "too_hard"),
            "parked bez progu": (["--status", "parked", "--rationale", "x"], "return-when"),
            "duplicate bez oryginału": (["--status", "duplicate", "--rationale", "x"], "duplicate-of"),
            "duplikat samego siebie": (["--status", "duplicate", "--duplicate-of", "PRB-34", "--rationale", "x"], "PRB-34"),
            "accepted bez briefu": (["--status", "accepted", "--rationale", "x"], "brief"),
            "bez uzasadnienia": (["--status", "parked", "--return-when", "x"], "rationale"),
            "stan wejściowy": (["--status", "new", "--rationale", "x"], "new"),
            "out_of_scope bez pliku": (["--status", "rejected", "--reason", "out_of_scope_recorded", "--rationale", "x"],
                                       ".out-of-scope"),
        }
        for label, (args, needle) in missing.items():
            r, _ = rec(*args)
            check(r.returncode == 1 and needle in r.stdout + r.stderr, f"R-9 odrzuca: {label}: {r.stdout}{r.stderr}")
        r = run(["recommend", write("acc.json", new_problem(status="accepted", change="CHG-12")), "--status", "parked",
                 "--return-when", "x", "--rationale", "x"], d)
        check(r.returncode == 1, f"R-10: rekomendacja dla zgłoszenia po triażu → błąd: {r.stdout}")
        r = run(["recommend", prb, "--status", "parked", "--return-when", "x", "--rationale", "x", "--out", "rec.json"], d)
        saved = json.loads((d / "rec.json").read_text(encoding="utf-8")) if (d / "rec.json").is_file() else {}
        check(r.returncode == 0 and saved.get("recommended_status") == "parked", f"R-11: --out zapisuje JSON: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów triażu zgłoszeń z pdi")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
