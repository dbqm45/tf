#!/usr/bin/env python3
"""Testy tablicy Event Storming prowadzonej przez agenta (skill ddd-event-storming, scripts/es_board.py):
dziennik zdarzeń z cofnięciem, kartki dozwolone w fazie, kontrola struktury fazy, zapis tablicy w Markdown.
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
        check(r.returncode == 0 and (board / "board.jsonl").is_file(), f"B-1: init zakłada dziennik: {r.stdout}{r.stderr}")

        # faza 1 (kontekst): aktorzy i systemy tak, komendy nie — mieszanie poziomów jest blokowane z podpowiedzią
        check(es("add", "actor", "Klient").returncode == 0, "B-2: aktor w fazie 1")
        r = es("add", "command", "Złóż zamówienie")
        check(r.returncode == 2 and "faz" in r.stdout + r.stderr and "3" in r.stdout + r.stderr,
              f"B-3: komenda w fazie 1 → kod 2 z numerem fazy: {r.returncode} {r.stdout}{r.stderr}")

        es("phase", "2")
        ids = [es("add", "event", txt).stdout.strip() for txt in ("Zamówienie złożone", "Płatność potwierdzona",
                                                                  "Paczka wysłana")]
        check(ids == ["E1", "E2", "E3"], f"B-4: kolejne identyfikatory zdarzeń: {ids}")
        es("add", "hotspot", "Kto sprawdza dostępność towaru?", "--at", "E1")
        es("add", "event", "Koszyk porzucony")
        es("undo")
        md = es("show").stdout
        check("Koszyk porzucony" not in md and "Paczka wysłana" in md, "B-5: undo cofa ostatnią zmianę")
        es("move", "E3", "--after", "E1")
        md = es("show").stdout
        check(md.find("Paczka wysłana") < md.find("Płatność potwierdzona"), "B-6: move ustawia kolejność na osi")
        es("move", "E3", "--after", "E2")

        # faza 3: gramatyka procesu — luki zgłasza check (kod 1), domknięty łańcuch przechodzi
        es("phase", "3")
        es("add", "command", "Złóż zamówienie", "--causes", "E1", "--actor", "Klient")
        r = es("check")
        out = r.stdout
        check(r.returncode == 1 and "E2" in out and "E3" in out and "wyzwalacza" in out,
              f"B-7: zdarzenia bez wyzwalacza: {out}")
        es("add", "system", "Operator płatności")
        es("edit", "E2", "--by", "S1")
        es("add", "command", "Wyślij paczkę", "--causes", "E3")
        es("add", "policy", "Kiedy płatność potwierdzona, wyślij paczkę", "--on", "E2", "--issues", "C2")
        r = es("add", "command", "Anuluj zamówienie")
        r2 = es("check")
        check(r2.returncode == 1 and "C3" in r2.stdout and "bez zdarzenia" in r2.stdout,
              f"B-8: komenda bez zdarzenia: {r2.stdout}")
        es("remove", "C3")
        r = es("check")
        check(r.returncode == 0, f"B-9: domknięta faza 3: {r.stdout}")
        r = es("add", "policy", "Kiedy coś", "--on", "E9", "--issues", "C1")
        check(r.returncode == 2 and "E9" in r.stdout + r.stderr, f"B-10: odwołanie do nieznanej kartki → kod 2: {r.stdout}{r.stderr}")

        # faza 4: każda komenda trafia do agregatu (albo systemu); duży agregat to ostrzeżenie
        es("phase", "4")
        r = es("check")
        check(r.returncode == 1 and "C1" in r.stdout and "agregat" in r.stdout, f"B-11: komenda bez agregatu: {r.stdout}")
        es("add", "aggregate", "Zamówienie", "--handles", "C1")
        es("add", "aggregate", "Wysyłka", "--handles", "C2")
        check(es("check").returncode == 0, "B-12: agregaty przypisane")
        extra = [es("add", "command", f"Zmień coś {i}", "--causes", "E1").stdout.strip() for i in range(8)]
        check(extra[0] == "C4", f"B-13a: identyfikator usuniętej kartki (C3) nie wraca: {extra[:2]}")
        es("edit", "A1", "--handles", ",".join(["C1"] + extra))
        r = es("check")
        check("duży agregat" in r.stdout and r.returncode == 0, f"B-13: duży agregat to ostrzeżenie: {r.stdout}")

        # faza 5: konteksty z typem subdomeny, relacje z nazwanym wzorcem mapy kontekstów
        es("phase", "5")
        r = es("check")
        check(r.returncode == 1 and "A1" in r.stdout and "kontekst" in r.stdout, f"B-14: agregat bez kontekstu: {r.stdout}")
        es("add", "context", "Sprzedaż", "--contains", "A1", "--kind", "core")
        es("add", "context", "Logistyka", "--contains", "A2")
        r = es("check")
        check(r.returncode == 1 and "K2" in r.stdout and "typu" in r.stdout, f"B-15: kontekst bez typu subdomeny: {r.stdout}")
        es("edit", "K2", "--kind", "supporting")
        r = es("add", "link", "Sprzedaż → Logistyka", "--from", "K1", "--to", "K2", "--pattern", "magia")
        check(r.returncode == 2 and "customer-supplier" in r.stdout + r.stderr, f"B-16: nieznany wzorzec → lista wzorców: {r.stdout}{r.stderr}")
        es("add", "link", "Zamówienie do wysyłki", "--from", "K1", "--to", "K2", "--pattern", "customer-supplier")
        es("resolve", "H1", "Magazyn, przy rezerwacji")
        r = es("check")
        check(r.returncode == 0, f"B-17: kompletna faza 5: {r.stdout}")

        r = es("show")
        md = (board / "board.md").read_text(encoding="utf-8") if (board / "board.md").exists() else ""
        check(r.returncode == 0 and md and "```mermaid" in md and "Sprzedaż" in md and "customer-supplier" in md
              and "core" in md, "B-18: show zapisuje board.md z diagramem, kontekstami i mapą")
        check("[x] H1" in md and "Magazyn, przy rezerwacji" in md, "B-19: rozwiązany hot spot z odpowiedzią")

        log = board / "board.jsonl"
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        check(lines and all(json.loads(x).get("op") for x in lines), "B-20: dziennik to linie JSON z operacją")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("{zepsute\n", encoding="utf-8")
        r = es("show")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"B-21: zepsuty dziennik → kod 2 bez śladu stosu: {r.stderr[-200:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tablicy Event Storming")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
