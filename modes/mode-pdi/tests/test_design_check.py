#!/usr/bin/env python3
"""Testy tabeli ramek w design.md (tryb mode-pdi, skill pdi-decisions, scripts/design_check.py; kontrakt pdi 0.9.0,
conventions.design): parser daje z przykładu kontraktu dokładnie jego odczytaną postać, braki ramek i brakujące stany
minimalne są problemami, a prośba o bramkę design-review niesie je jako pytania. python3 .claude/tests/test_design_check.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "design_check.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-contract"   # kopia kontraktu pdi (wersja w VERSION, bez zmian)
HEADER = "| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |\n|---|---|---|---|---|\n"
LINK = "https://www.figma.com/design/AbC123xyz/Taryfy?node-id={}"


def run(args, cwd, script=None):
    return subprocess.run([sys.executable, str(script or SCRIPT), *args], cwd=cwd, capture_output=True, text=True,
                          timeout=60, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


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
    sys.path.insert(0, str(SCRIPT.parent))
    import design_check as dc

    want = json.loads((FIX / "design-links.json").read_text(encoding="utf-8"))
    got = dc.parse_design_md((FIX / "design.md").read_text(encoding="utf-8"))
    check(got == want, f"D-1: przykład design.md z kontraktu → dokładnie design-links.json: {got}")
    schema = json.loads((SCRIPT.parent / "design-links.schema.json").read_text(encoding="utf-8"))
    check(list(dc.STATES) == schema["$defs"]["row"]["properties"]["state"]["enum"]
          and schema == json.loads((FIX / "design-links.schema.json").read_text(encoding="utf-8")),
          "D-2: stany skryptu = stany schematu z kontraktu; schemat obok skryptu = kopia z kontraktu")
    from decision_record import validate
    check(validate(got, schema, "") == [], f"D-3: wynik parsera przechodzi schemat kontraktu: {validate(got, schema, '')}")

    bad = {
        "nieznany stan": ("| US-3 | zmiana | busy | " + LINK.format("1-2") + " | |", "stan"),
        "link spoza figmy": ("| US-3 | zmiana | idle | https://example.com/x | |", "link"),
        "link bez node-id": ("| US-3 | zmiana | idle | https://www.figma.com/design/K/x | |", "node-id"),
        "brak bez uwagi": ("| US-3 | zmiana | idle | brak | |", "uwag"),
        "zły klucz": ("| us3 | zmiana | idle | " + LINK.format("1-2") + " | |", "wymagani"),
    }
    for label, (row, word) in bad.items():
        try:
            dc.parse_design_md(HEADER + row + "\n")
            check(False, f"D-4 {label}: oczekiwano błędu formatu")
        except dc.DesignFormatError as e:
            check(str(e).startswith("wiersz 1:") and word in str(e), f"D-4 {label}: błąd z numerem wiersza: {e}")

    problems = dc.problems(want["rows"])
    check(any("US-3/AC-3" in p and "server_error" in p and "pytanie do projektanta" in p for p in problems)
          and not any("session_expired" in p for p in problems),
          f"D-5: brak ramki → problem z uwagą; 'nie dotyczy' z powodem nie jest problemem: {problems}")
    check(not any(p.startswith(("US-3:", "US-3/")) and "brak wiersza" in p for p in problems),
          f"D-6a: stany minimalne liczone per historyjka (US-3 i jej AC razem mają idle, success, błąd): {problems}")
    only_idle = [{"requirement": "US-7/AC-1", "journey": "j", "state": "idle", "status": "linked",
                  "frame": {"file_key": "K", "node_id": "1:2", "url": LINK.format("1-2")}}]
    got7 = dc.problems(only_idle)
    check(len(got7) == 1 and got7[0].startswith("US-7:") and "success" in got7[0] and "błędu" in got7[0],
          f"D-6b: historyjka bez stanu wyniku i błędu → jeden problem z listą braków: {got7}")
    full = [{"requirement": "US-9", "journey": "j", "state": s, "status": "linked",
             "frame": {"file_key": "K", "node_id": "1:2", "url": LINK.format("1-2")}}
            for s in ("idle", "success", "server_error")]
    check(dc.problems(full) == [], f"D-7: komplet stanów minimalnych z ramkami → brak problemów: {dc.problems(full)}")

    with tempfile.TemporaryDirectory() as t:
        repo = Path(t)
        d = repo / "docs" / "project" / "changes" / "CHG-12"
        d.mkdir(parents=True)
        (d / "design.md").write_text((FIX / "design.md").read_text(encoding="utf-8"), encoding="utf-8")
        r = run(["check", "CHG-12"], repo)
        check(r.returncode == 1 and "server_error" in r.stdout, f"D-8: check z brakami → 1 i lista: {r.stdout}{r.stderr}")
        r = run(["check", "CHG-12", "--json"], repo)
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        check(out.get("rows") == want["rows"] and out.get("problems"), f"D-9: --json z wierszami i problemami: {r.stdout[:300]}")
        r = run(["check", "CHG-99"], repo)
        check(r.returncode == 2 and "design.md" in r.stdout + r.stderr, f"D-10: brak pliku → 2: {r.stdout}{r.stderr}")

        phase = SCRIPT.parent / "phase_run.py"
        (d / "design.md").write_text((FIX / "design.md").read_text(encoding="utf-8")
                                     + "\n## Pytania do bramki\n- Czy błąd częściowy ma osobny ekran?\n", encoding="utf-8")
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "design", "--dry-run"], repo, script=phase)
        try:
            ev = json.loads(r.stdout).get("would_send", {})
        except ValueError:
            ev = {}
        qs = ev.get("payload", {}).get("questions", [])
        check(ev.get("payload", {}).get("gate") == "design-review" and "Czy błąd częściowy ma osobny ekran?" in qs
              and any("server_error" in q for q in qs),
              f"D-11: bramka design-review niesie pytania z artefaktu i braki tabeli ramek: {r.stdout[:400]}{r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tabeli ramek design.md")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
