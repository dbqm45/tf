#!/usr/bin/env python3
"""Testy dziennika zmiany (tryb mode-pdi, skill pdi-decisions, scripts/decision_record.py): `change new` i `check`
wobec nagłówka z kontraktu pdi 0.3.0 (contract/change.schema.json). python3 .claude/tests/test_decision_record.py"""
import datetime as dt
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

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów dziennika zmiany (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
