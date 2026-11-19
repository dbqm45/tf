#!/usr/bin/env python3
"""Tests of the Event Storming board run by an agent (skill ddd-event-storming, scripts/es_board.py):
an event log with undo, the stickies allowed in a phase, the phase structure check, saving the board as Markdown.
python3 .claude/tests/test_es_board.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "ddd-event-storming" / "scripts" / "es_board.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj = Path(t)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}

        def es(*args):
            return subprocess.run([sys.executable, str(SCRIPT), *args, "--id", "sklep"], cwd=proj, env=env,
                                  capture_output=True, text=True, timeout=60)

        board = proj / "docs" / "project" / "02-domain" / "event-storming" / "sklep"
        r = es("init", "--topic", "Sklep internetowy", "--question", "Jak przebiega zamówienie?")
        check(r.returncode == 0 and (board / "board.jsonl").is_file(), f"B-1: init creates the log: {r.stdout}{r.stderr}")

        # phase 1 (context): actors and systems yes, commands no — mixing levels is blocked with a hint
        check(es("add", "actor", "Klient").returncode == 0, "B-2: an actor in phase 1")
        r = es("add", "command", "Złóż zamówienie")
        check(r.returncode == 2 and "phase" in r.stdout + r.stderr and "3" in r.stdout + r.stderr,
              f"B-3: a command in phase 1 → code 2 with the phase number: {r.returncode} {r.stdout}{r.stderr}")

        es("phase", "2")
        ids = [es("add", "event", txt).stdout.strip() for txt in ("Zamówienie złożone", "Płatność potwierdzona",
                                                                  "Paczka wysłana")]
        check(ids == ["E1", "E2", "E3"], f"B-4: consecutive event identifiers: {ids}")
        es("add", "hotspot", "Kto sprawdza dostępność towaru?", "--at", "E1")
        es("add", "event", "Koszyk porzucony")
        es("undo")
        md = es("show").stdout
        check("Koszyk porzucony" not in md and "Paczka wysłana" in md, "B-5: undo reverts the last change")
        es("move", "E3", "--after", "E1")
        md = es("show").stdout
        check(md.find("Paczka wysłana") < md.find("Płatność potwierdzona"), "B-6: move sets the order on the timeline")
        es("move", "E3", "--after", "E2")

        # phase 3: the process grammar — check reports gaps (code 1), a closed chain passes
        es("phase", "3")
        es("add", "command", "Złóż zamówienie", "--causes", "E1", "--actor", "Klient")
        r = es("check")
        out = r.stdout
        check(r.returncode == 1 and "E2" in out and "E3" in out and "without a trigger" in out,
              f"B-7: events without a trigger: {out}")
        es("add", "system", "Operator płatności")
        es("edit", "E2", "--by", "S1")
        es("add", "command", "Wyślij paczkę", "--causes", "E3")
        es("add", "policy", "Kiedy płatność potwierdzona, wyślij paczkę", "--on", "E2", "--issues", "C2")
        r = es("add", "command", "Anuluj zamówienie")
        r2 = es("check")
        check(r2.returncode == 1 and "C3" in r2.stdout and "without an event" in r2.stdout,
              f"B-8: a command without an event: {r2.stdout}")
        es("remove", "C3")
        r = es("check")
        check(r.returncode == 0, f"B-9: phase 3 closed: {r.stdout}")
        r = es("add", "policy", "Kiedy coś", "--on", "E9", "--issues", "C1")
        check(r.returncode == 2 and "E9" in r.stdout + r.stderr, f"B-10: a reference to an unknown sticky → code 2: {r.stdout}{r.stderr}")

        # phase 4: every command goes to an aggregate (or a system); a large aggregate is a warning
        es("phase", "4")
        r = es("check")
        check(r.returncode == 1 and "C1" in r.stdout and "aggregate" in r.stdout, f"B-11: a command without an aggregate: {r.stdout}")
        es("add", "aggregate", "Zamówienie", "--handles", "C1")
        es("add", "aggregate", "Wysyłka", "--handles", "C2")
        check(es("check").returncode == 0, "B-12: aggregates assigned")
        extra = [es("add", "command", f"Zmień coś {i}", "--causes", "E1").stdout.strip() for i in range(8)]
        check(extra[0] == "C4", f"B-13a: the identifier of a removed sticky (C3) does not come back: {extra[:2]}")
        es("edit", "A1", "--handles", ",".join(["C1"] + extra))
        r = es("check")
        check("large aggregate" in r.stdout and r.returncode == 0, f"B-13: a large aggregate is a warning: {r.stdout}")

        # phase 5: contexts with a subdomain type, relations with a named context-map pattern
        es("phase", "5")
        r = es("check")
        check(r.returncode == 1 and "A1" in r.stdout and "context" in r.stdout, f"B-14: an aggregate without a context: {r.stdout}")
        es("add", "context", "Sprzedaż", "--contains", "A1", "--kind", "core")
        es("add", "context", "Logistyka", "--contains", "A2")
        r = es("check")
        check(r.returncode == 1 and "K2" in r.stdout and "subdomain type" in r.stdout, f"B-15: a context without a subdomain type: {r.stdout}")
        es("edit", "K2", "--kind", "supporting")
        r = es("add", "link", "Sprzedaż → Logistyka", "--from", "K1", "--to", "K2", "--pattern", "magia")
        check(r.returncode == 2 and "customer-supplier" in r.stdout + r.stderr, f"B-16: an unknown pattern → a list of patterns: {r.stdout}{r.stderr}")
        es("add", "link", "Zamówienie do wysyłki", "--from", "K1", "--to", "K2", "--pattern", "customer-supplier")
        es("resolve", "H1", "Magazyn, przy rezerwacji")
        r = es("check")
        check(r.returncode == 0, f"B-17: phase 5 complete: {r.stdout}")

        r = es("show")
        md = (board / "board.md").read_text(encoding="utf-8") if (board / "board.md").exists() else ""
        check(r.returncode == 0 and md and "```mermaid" in md and "Sprzedaż" in md and "customer-supplier" in md
              and "core" in md, "B-18: show saves board.md with the diagram, contexts and the map")
        check("[x] H1" in md and "Magazyn, przy rezerwacji" in md, "B-19: a resolved hot spot with an answer")

        log = board / "board.jsonl"
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        check(lines and all(json.loads(x).get("op") for x in lines), "B-20: the log is JSON lines with an operation")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("{zepsute\n", encoding="utf-8")
        r = es("show")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"B-21: a corrupted log → code 2 without a stack trace: {r.stderr[-200:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the Event Storming board")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
