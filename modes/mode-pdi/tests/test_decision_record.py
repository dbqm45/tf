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

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów dziennika zmiany (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
