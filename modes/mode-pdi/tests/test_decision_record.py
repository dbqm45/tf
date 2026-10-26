#!/usr/bin/env python3
"""Testy dziennika zmiany (tryb mode-pdi, skill pdi-decisions, scripts/decision_record.py): `change new` i `check`
wobec nagłówka z kontraktu pdi 0.3.0 (contract/change.schema.json). python3 .claude/tests/test_decision_record.py"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "decision_record.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None

# Pola nagłówka z pdi/contract/change.schema.json 0.3.0 (additionalProperties: false).
SCHEMA_KEYS = {"artifact", "phase", "status", "version", "author", "created", "updated", "inputs", "change", "source",
               "tasks", "superseded_by"}
REQUIRED = {"artifact", "phase", "status", "version", "created", "updated", "change"}
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-contract"   # kopia kontraktu pdi (wersja w VERSION, bez zmian)

# Plan wydania z pdi docs/plan-g1-g2.md §5.2 (wiersze TSK-59 i TSK-60 dopisane do R2, jak w przykładzie kontraktu).
RELEASE_OK = """# docs/project/changes/CHG-12/release.yaml   (kontrakt 0.4.0)
change: CHG-12
mvp:
  release: R1
  outcome: Klient może ponowić nieudaną płatność bez podwójnego obciążenia
  metric: { name: odzyskane_platnosci, target: ">= 25%", horizon_days: 30 }
  guardrails: [podwojne_obciazenia = 0]
releases:
  - { id: R1, name: MVP, tasks: [TSK-57, TSK-58] }
  - { id: R2, tasks: [TSK-59, TSK-60] }
flags:
  - key: payment-retry
    tasks: [TSK-57, TSK-58]
    owner: PO Payments
    remove_by: 2026-12-31
    rollout:
      - { stage: internal, min_days: 3, exit: "0 błędów krytycznych" }
      - { stage: "10%", min_days: 7, exit: "odzyskane >= 15%, duplikaty = 0" }
      - { stage: "100%" }
"""
PLAN_ROWS = """| Cięcie | Wydanie | Flaga | Wartość | Pliki | Weryfikacja |
|---|---|---|---|---|---|
| TSK-57 | R1 | payment-retry | ponowienie płatności | | |
| TSK-58 | R1 | payment-retry | brak podwójnego obciążenia | | |
| TSK-59 | R2 | — | historia prób | | |
| TSK-60 | R2 | | powiadomienie | | |
"""


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def header(path: Path) -> dict:
    """Prosty YAML nagłówka: `klucz: wartość` i listy `[a, b]`."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    out = {}
    for line in text.split("---\n")[1].splitlines():
        k, _, v = line.partition(":")
        v = v.split(" #")[0].strip()
        out[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") else v
    return out


def jl(r) -> list:
    try:
        return json.loads(r.stdout) if r.returncode == 0 else []
    except ValueError:
        return []


def write(path: Path, head: str, body: str = "# x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{head.strip()}\n---\n{body}", encoding="utf-8")


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
    today = dt.date.today().isoformat()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        r = run(["change", "new", "CHG-12", "--source", "PRB-34"], repo)
        d = repo / "docs" / "project" / "changes" / "CHG-12"
        check(r.returncode == 0, f"D-1: change new kończy się sukcesem: {r.stdout}{r.stderr}")
        names = sorted(p.name for p in d.glob("*.md")) if d.is_dir() else []
        check(names == ["decisions.md", "intent.md", "plan.md"], f"D-2: trzy artefakty zmiany: {names}")
        for n in names:
            h = header(d / n)
            check(set(h) <= SCHEMA_KEYS, f"D-3 {n}: tylko pola ze schematu: {set(h) - SCHEMA_KEYS}")
            check(REQUIRED <= set(h), f"D-4 {n}: pola wymagane: {REQUIRED - set(h)}")
            check(h.get("artifact") == n[:-3] and h.get("change") == "CHG-12" and h.get("source") == "PRB-34"
                  and h.get("status") == "draft" and h.get("version") == "1"
                  and h.get("created") == today and h.get("updated") == today,
                  f"D-5 {n}: wartości nagłówka: {h}")
            check(("tasks" in h) == (n == "plan.md"), f"D-6 {n}: tasks tylko w plan.md")
        r = run(["check"], repo)
        check(r.returncode == 0, f"D-7: świeży dziennik przechodzi check: {r.stdout}{r.stderr}")
        r = run(["change", "new", "CHG-12"], repo)
        check(r.returncode != 0 and "istnieje" in r.stdout + r.stderr, "D-8: istniejący katalog → błąd")
        check(header(d / "intent.md").get("source") == "PRB-34", "D-9: bez nadpisania istniejących plików")
        r = run(["change", "new", "chg-1"], repo)
        check(r.returncode != 0, "D-10: zły kształt klucza zmiany → błąd")
        r = run(["change", "new", "CHG-13", "--source", "34"], repo)
        check(r.returncode != 0 and not (d.parent / "CHG-13").exists(), "D-11: zły klucz zgłoszenia → błąd bez katalogu")
        r = run(["change", "new", "CHG-14"], repo)
        check(r.returncode == 0 and "source" not in header(d.parent / "CHG-14" / "intent.md"),
              "D-12: bez --source nagłówek nie ma pola source")

    bad = {
        "brak change": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\nupdated: 2026-10-23",
        "change != katalog": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\n"
                             "updated: 2026-10-23\nchange: CHG-99",
        "nieznany artifact": "artifact: memo\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\n"
                             "updated: 2026-10-23\nchange: CHG-1",
        "nieznany status": "artifact: intent\nphase: discovery\nstatus: done\nversion: 1\ncreated: 2026-10-23\n"
                           "updated: 2026-10-23\nchange: CHG-1",
        "nieznane pole": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\n"
                         "updated: 2026-10-23\nchange: CHG-1\nowner: ja",
        "tasks poza plan": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\n"
                           "updated: 2026-10-23\nchange: CHG-1\ntasks: [TSK-1]",
        "zły klucz source": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 2026-10-23\n"
                            "updated: 2026-10-23\nchange: CHG-1\nsource: prb-1",
        "zła data": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 1\ncreated: 23.10.2026\n"
                    "updated: 2026-10-23\nchange: CHG-1",
        "zła wersja": "artifact: intent\nphase: discovery\nstatus: draft\nversion: 0\ncreated: 2026-10-23\n"
                      "updated: 2026-10-23\nchange: CHG-1",
    }
    for label, head in bad.items():
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "docs" / "project" / "changes" / "CHG-1" / "intent.md", head)
            r = run(["check"], tmp)
            check(r.returncode != 0, f"D-13 check wykrywa: {label} ({r.stdout.strip()[:200]})")
    with tempfile.TemporaryDirectory() as tmp:
        write(Path(tmp) / "docs" / "project" / "changes" / "CHG-1" / "plan.md",
              "artifact: plan\nphase: plan\nstatus: accepted\nversion: 2\nauthor: x\ncreated: 2026-10-23\n"
              "updated: 2026-10-24\ninputs: [docs/project/changes/CHG-1/intent.md]\nchange: CHG-1\nsource: PRB-3\n"
              "tasks: [TSK-57, TSK-58]")
        r = run(["check"], tmp)
        check(r.returncode == 0, f"D-14: poprawny plan (przykład z kontraktu) przechodzi: {r.stdout}{r.stderr}")
        r = run(["check"], Path(tmp) / "docs")
        check(r.returncode == 0 and "brak" in r.stdout.lower(), f"D-15: bez docs/project/changes — nic do sprawdzenia: {r.stdout}")

    # F0b: decyzje — add, pending, mark, export, check wpisów.
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run(["change", "new", "CHG-12", "--source", "PRB-34"], repo)
        dec = repo / "docs" / "project" / "changes" / "CHG-12" / "decisions.md"
        add = ["decision", "add", "CHG-12", "--statement", "Eksport do CSV zamiast XLSX.",
               "--why", "Klienci i tak otwierają go w arkuszu.", "--kind", "product", "--by", "właściciel produktu"]
        r = run(add, repo)
        check(r.returncode == 0 and "CHG-12/D1" in r.stdout, f"E-1: decision add zwraca ref CHG-12/D1: {r.stdout}{r.stderr}")
        text = dec.read_text(encoding="utf-8")
        check("## Eksport do CSV zamiast XLSX." in text and "- ref: CHG-12/D1" in text and "- id:\n" in text
              and "- wyslano: nie" in text and f"- kiedy: {today}" in text and "- szkic: ai" in text,
              f"E-2: wpis w decisions.md z ref, pustym id, wyslano: nie, datą i szkicem: {text[-400:]}")
        r = run(add[:3] + ["--statement", "Druga.", "--why", "Bo tak.", "--kind", "technical", "--by", "zespół",
                           "--source-kind", "slack", "--drafted-by", "human"], repo)
        check(r.returncode == 0 and "CHG-12/D2" in r.stdout, "E-3: kolejny wpis dostaje D2")
        r = run(add[:3] + ["--statement", "Zła.", "--why", "x", "--kind", "decyzja", "--by", "x"], repo)
        check(r.returncode != 0, "E-4: nieznany rodzaj decyzji → błąd")
        r = run(["decision", "add", "CHG-99", "--statement", "x", "--why", "x", "--kind", "other", "--by", "x"], repo)
        check(r.returncode != 0 and "change new" in r.stdout + r.stderr, "E-5: brak dziennika zmiany → błąd z podpowiedzią")
        r = run(["decision", "pending"], repo)
        items = jl(r)
        first = items[0] if items else {}
        check(r.returncode == 0 and [i.get("ref") for i in items] == ["CHG-12/D1", "CHG-12/D2"],
              f"E-6: pending wypisuje niewysłane w kolejności: {r.stdout[:300]}")
        check(first.get("record_decision") == {
                  "statement": "Eksport do CSV zamiast XLSX.", "why": "Klienci i tak otwierają go w arkuszu.",
                  "kind": "product", "source": {"kind": "claude-cli"}, "drafted_by": "ai",
                  "decided_by": "właściciel produktu", "decided_at": today, "links": {"chg": "CHG-12", "prb": "PRB-34"}},
              f"E-7: argumenty record_decision zgodne z kontraktem decyzji: {first}")
        r = run(["decision", "mark", "CHG-12/D1", "--id", "DEC-41"], repo)
        text = dec.read_text(encoding="utf-8")
        check(r.returncode == 0 and "- id: DEC-41" in text and text.count("- wyslano: tak") == 1,
              f"E-8: mark wpisuje id i wyslano: tak: {r.stdout}{r.stderr}")
        r = run(["decision", "mark", "CHG-12/D1", "--id", "DEC-42"], repo)
        check(r.returncode != 0 and "DEC-41" in dec.read_text(encoding="utf-8"), "E-9: ponowne mark innym id → błąd, bez zmiany")
        r = run(["decision", "mark", "CHG-12/D2", "--id", "dec-1"], repo)
        check(r.returncode != 0, "E-10: zły kształt numeru DEC → błąd")
        r = run(["decision", "pending"], repo)
        check([i.get("ref") for i in jl(r)] == ["CHG-12/D2"], "E-11: po mark zostaje jeden niewysłany")
        r = run(["decision", "export"], repo)
        allx = jl(r)
        check([(d.get("ref"), d.get("id"), d.get("sent")) for d in allx] == [("CHG-12/D1", "DEC-41", True),
                                                                            ("CHG-12/D2", None, False)]
              and len(allx) > 1 and allx[1].get("source") == {"kind": "slack"} and allx[1].get("drafted_by") == "human",
              f"E-12: export wszystkich decyzji z id i stanem wysłania: {r.stdout[:400]}")
        r = run(["check"], repo)
        check(r.returncode == 0, f"E-13: dziennik z decyzjami przechodzi check: {r.stdout}")
        dec.write_text(dec.read_text(encoding="utf-8").replace("- id: DEC-41", "- id: 41"), encoding="utf-8")
        r = run(["check"], repo)
        check(r.returncode != 0 and "CHG-12/D1" in r.stdout, f"E-14: check wykrywa zły numer w decyzji: {r.stdout}")
        dec.write_text(dec.read_text(encoding="utf-8").replace("- id: 41\n- wyslano: tak", "- id:\n- wyslano: tak"),
                       encoding="utf-8")
        r = run(["check"], repo)
        check(r.returncode != 0, f"E-15: check wykrywa wyslano: tak bez numeru: {r.stdout}")

    # G1.1: plan wydania release.yaml (kontrakt pdi 0.4.0, release-plan.schema.json) i spójność z plan.md
    near = SCRIPT.parent / "release-plan.schema.json"
    check(near.is_file() and FIX.is_dir() and json.loads(near.read_text(encoding="utf-8"))
          == json.loads((FIX / "release-plan.schema.json").read_text(encoding="utf-8"))
          and (FIX / "VERSION").read_text(encoding="utf-8").strip() == "0.6.0",
          "R-0: schemat obok skryptu = kopia z kontraktu pdi 0.6.0")
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        r = run(["change", "new", "CHG-12"], repo)
        rel = repo / "docs" / "project" / "changes" / "CHG-12" / "release.yaml"
        text = rel.read_text(encoding="utf-8") if rel.is_file() else ""
        check(r.returncode == 0 and "change: CHG-12" in text and "R1" in text and "release.yaml" in r.stdout,
              f"R-1: change new zakłada release.yaml z linią R1: {r.stdout} {text[:300]}")
        r = run(["check"], repo)
        check(r.returncode == 0, f"R-2: świeży release.yaml przechodzi check: {r.stdout}")

    def release_case(release: str, plan_tasks: str = "TSK-57, TSK-58, TSK-59, TSK-60", rows: str = PLAN_ROWS):
        tmp = tempfile.mkdtemp()
        d = Path(tmp) / "docs" / "project" / "changes" / "CHG-12"
        write(d / "plan.md", "artifact: plan\nphase: plan\nstatus: draft\nversion: 1\ncreated: 2026-10-25\n"
              f"updated: 2026-10-25\nchange: CHG-12\ntasks: [{plan_tasks}]", "# Plan zmiany CHG-12\n\n" + rows)
        (d / "release.yaml").write_text(release, encoding="utf-8")
        return run(["check"], tmp)

    example = (FIX / "release-plan.json").read_text(encoding="utf-8") if FIX.is_dir() else ""
    r = release_case(RELEASE_OK)
    check(r.returncode == 0, f"R-3: plan wydania z §5.2 planu G1 (YAML) + zgodny plan.md przechodzi: {r.stdout}")
    r = release_case(example)
    check(r.returncode == 0, f"R-4: przykład z kontraktu (JSON to też YAML) przechodzi: {r.stdout}")
    bad_release = {
        "schemat: linia X1": (RELEASE_OK.replace("id: R2", "id: X2"), "X2"),
        "schemat: zły klucz TSK": (RELEASE_OK.replace("TSK-60]", "tsk-60]"), "tsk-60"),
        "schemat: nieznane pole": (RELEASE_OK.replace("change: CHG-12", "change: CHG-12\nowner: ja"), "owner"),
        "mvp.release spoza linii": (RELEASE_OK.replace("release: R1", "release: R3"), "R3"),
        "TSK różne od plan.md": (RELEASE_OK.replace(", TSK-60]", "]"), "TSK-60"),
        "TSK w dwóch liniach": (RELEASE_OK.replace("tasks: [TSK-59, TSK-60]", "tasks: [TSK-58, TSK-59, TSK-60]"), "TSK-58"),
        "flaga bez etapów": (RELEASE_OK.split("    rollout:")[0], "payment-retry"),
        "flaga bez remove_by": (RELEASE_OK.replace("    remove_by: 2026-12-31\n", ""), "remove_by"),
        "TSK flagi spoza linii": (RELEASE_OK.replace("tasks: [TSK-57, TSK-58]\n    owner", "tasks: [TSK-57, TSK-99]\n    owner"),
                                  "TSK-99"),
        "niepoprawny YAML": ("change: CHG-12\nreleases: [\n", "YAML"),
    }
    for label, (text, needle) in bad_release.items():
        r = release_case(text)
        check(r.returncode != 0 and needle in r.stdout and "release.yaml" in r.stdout,
              f"R-5 check wykrywa: {label} ({r.stdout.strip()[:300]})")
    r = release_case(RELEASE_OK, rows=PLAN_ROWS.replace("| TSK-59 | R2 |", "| TSK-59 | R1 |"))
    check(r.returncode != 0 and "TSK-59" in r.stdout and "Wydanie" in r.stdout,
          f"R-6: kolumna „Wydanie” w plan.md niezgodna z release.yaml: {r.stdout}")
    r = release_case(RELEASE_OK, rows=PLAN_ROWS.replace("| TSK-58 | R1 | payment-retry |", "| TSK-58 | R1 | — |"))
    check(r.returncode != 0 and "TSK-58" in r.stdout and "Flaga" in r.stdout,
          f"R-7: kolumna „Flaga” w plan.md niezgodna z release.yaml: {r.stdout}")
    with tempfile.TemporaryDirectory() as tmp:
        write(Path(tmp) / "docs" / "project" / "changes" / "CHG-1" / "plan.md",
              "artifact: plan\nphase: plan\nstatus: draft\nversion: 1\ncreated: 2026-10-23\nupdated: 2026-10-23\n"
              "change: CHG-1\ntasks: [TSK-1]")
        r = run(["check"], tmp)
        check(r.returncode == 0, f"R-8: zmiana sprzed G1.1 (bez release.yaml) nadal przechodzi: {r.stdout}")

    # decision gate: decyzja z bramki w pdi (gate.decided) zapisana w repo z numerem z rejestru (F4, D2/R1)
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run(["change", "new", "CHG-12"], repo)
        dec = repo / "docs" / "project" / "changes" / "CHG-12" / "decisions.md"
        gate = ["decision", "gate", "CHG-12", "--gate", "B1", "--outcome", "approved", "--id", "DEC-41"]
        r = run(gate, repo)
        text = dec.read_text(encoding="utf-8")
        check(r.returncode == 0 and "CHG-12/D1" in r.stdout, f"G-1: decision gate dopisuje wpis D1: {r.stdout}{r.stderr}")
        check("## Bramka B1: approved" in text and "- id: DEC-41" in text and "- wyslano: tak" in text
              and "- rodzaj: gate" in text and "- kto: pdi" in text and "- zrodlo: manual" in text
              and "- szkic: human" in text and "DEC-41" in text.split("- dlaczego:")[-1].splitlines()[0],
              f"G-2: wpis z numerem z pdi, wyslano: tak, rodzaj gate: {text[-500:]}")
        r = run(gate, repo)
        check(r.returncode == 0 and dec.read_text(encoding="utf-8").count("DEC-41") == text.count("DEC-41")
              and "już" in r.stdout, f"G-3: ponowienie z tym samym numerem nic nie dopisuje: {r.stdout}")
        r = run(["decision", "pending"], repo)
        check(jl(r) == [], "G-4: decyzja z bramki nie czeka na wysłanie")
        r = run(["check"], repo)
        check(r.returncode == 0, f"G-5: dziennik z decyzją z bramki przechodzi check: {r.stdout}")
        r = run(["decision", "gate", "CHG-12", "--gate", "B2", "--outcome", "changes_requested", "--id", "DEC-42",
                 "--by", "PO Payments", "--date", "2026-10-26"], repo)
        text = dec.read_text(encoding="utf-8")
        check(r.returncode == 0 and "## Bramka B2: changes_requested" in text and "- kto: PO Payments" in text
              and "- kiedy: 2026-10-26" in text, f"G-6: --by i --date: {r.stdout}{text[-300:]}")
        for bad, why in ((["--outcome", "maybe"], "outcome"), (["--id", "41"], "id"), (["--gate", ""], "gate")):
            args = gate[:3] + ["--gate", "B3", "--outcome", "approved", "--id", "DEC-43"]
            i = args.index(bad[0])
            args[i + 1] = bad[1]
            r = run(args, repo)
            check(r.returncode != 0, f"G-7: zły {why} → błąd: {r.stdout}")
        r = run(["decision", "gate", "CHG-99", "--gate", "B1", "--outcome", "approved", "--id", "DEC-44"], repo)
        check(r.returncode != 0 and "change new" in r.stdout, "G-8: brak dziennika zmiany → błąd z podpowiedzią")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów dziennika zmiany (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
