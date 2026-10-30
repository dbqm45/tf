#!/usr/bin/env python3
"""Testy dziennika projektu: python3 tests/test_project_record.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude" / "hooks" / "project_record.py"
TEMPLATES = SCRIPT.parent.parent / "skills" / "core-project-record" / "templates"


def run(root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, env=env, timeout=30)


def artifact(root: Path, rel: str, **fields) -> Path:
    meta = {"artifact": "brief", "phase": "discovery", "status": "proposed", "version": "1", "author": "ewa",
            "created": "2026-09-27", "updated": "2026-09-27", "inputs": "[]"} | fields
    body = fields.pop("_body", "# Brief\n## TL;DR\nKrótko o wyniku.\n## Otwarte pytania\n- [ ] Pytanie → PO\n## Przekazanie\n- Dla: tomasz\n")
    p = root / "docs" / "project" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items() if not k.startswith("_")) + "\n---\n" + body)
    return p


WIP_TESTS = 8


def wip_tests() -> list[str]:
    """Punkt kontrolny pracy w toku: start, sesja, migawka, przypomnienie Stop, zakończenie."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        git_ok = subprocess.run(["git", "init", "-q", str(root)], capture_output=True).returncode == 0
        r = run(root, "wip", "start", "Logowanie przez Google", "--by", "ola")
        wip = root / "docs/project/wip/logowanie-przez-google.md"
        if r.returncode != 0 or not wip.exists():
            fails.append(f"wip start: {r.stdout[-200:]}")
            return fails
        text = wip.read_text().replace("<!-- Jedna konkretna czynność, od której zacznie kolejna sesja: plik, funkcja, polecenie. -->",
                                       "Dopisać test callbacku w auth.service.spec.ts")
        wip.write_text(text)
        s = run(root, "--hook-session").stdout
        if "logowanie-przez-google" not in s or "Dopisać test callbacku" not in s:
            fails.append("hook sesji nie pokazuje pracy w toku i następnej czynności")
        if run(root, "check").returncode != 0:
            fails.append("check nie powinien traktować wip/ jak artefaktów fazy")
        if run(root, "wip", "start", "Logowanie przez Google").returncode == 0:
            fails.append("wip start nie powinien nadpisać istniejącego punktu kontrolnego")
        (root / "app.ts").write_text("x")
        before = wip.stat().st_mtime
        run(root, "--hook-snapshot", "koniec sesji")
        body = wip.read_text()
        if "zdarzenie: koniec sesji" not in body or (git_ok and "`app.ts`" not in body) or wip.stat().st_mtime != before:
            fails.append("migawka: brak stanu automatycznego, pliku app.ts albo zmieniony czas modyfikacji")
        old = before - 3600
        os.utime(wip, (old, old))
        out = run(root, "--hook-stop", stdin="{}").stdout
        if git_ok and '"block"' not in out:
            fails.append("Stop nie przypomina o nieaktualnym punkcie kontrolnym")
        if run(root, "--hook-stop", stdin='{"stop_hook_active": true}').stdout.strip():
            fails.append("Stop nie może blokować drugi raz (stop_hook_active)")
        r = run(root, "wip", "done", "logowanie-przez-google", "--by", "ola")
        if r.returncode != 0 or wip.exists() or not list((root / "docs/project/archive/wip").glob("*logowanie-przez-google.md")) \
                or run(root, "--hook-stop", stdin="{}").stdout.strip():
            fails.append("wip done: plik nie trafił do archiwum albo Stop nadal przypomina")
    return fails


RESUME_TESTS = 3


def resume_tests() -> list[str]:
    """Wznowienie: stan repo zapisany w punkcie kontrolnym porównany z bieżącym (gałąź, commit)."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        def g(*a: str) -> int:
            return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                  capture_output=True).returncode

        if g("init", "-q", "-b", "main") != 0:
            return fails                                   # bez gita nie ma czego porównywać
        (root / "a.txt").write_text("1")
        g("add", "a.txt")
        g("commit", "-q", "-m", "start")
        run(root, "wip", "start", "Eksport zamówień", "--by", "ola")
        run(root, "--hook-snapshot", "koniec sesji")
        if "różni się od punktu kontrolnego" in run(root, "--hook-session").stdout:
            fails.append("wznowienie: ostrzeżenie o rozjeździe, choć stan repo się nie zmienił")
        (root / "a.txt").write_text("2")
        g("commit", "-q", "-am", "zmiana spoza sesji")
        s = run(root, "--hook-session").stdout
        if "różni się od punktu kontrolnego" not in s or "1 commit" not in s:
            fails.append(f"wznowienie: brak ostrzeżenia o nowym commicie od zapisu: {s[-300:]}")
        g("checkout", "-q", "-b", "inna")
        s = run(root, "--hook-session").stdout
        if "gałąź" not in s or "inna" not in s:
            fails.append(f"wznowienie: brak ostrzeżenia o innej gałęzi: {s[-300:]}")
    return fails


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        if run(root, "init").returncode != 0 or not (root / "docs/project/journal.md").exists():
            fails.append("init")
        if run(root, "check").returncode != 0:
            fails.append("check pustego dziennika")
        artifact(root, "01-discovery/brief.md")
        if run(root, "check").returncode != 0:
            fails.append("poprawny brief")
        artifact(root, "03-requirements/requirements.md", artifact="requirements", phase="requirements",
                 inputs="[docs/project/01-discovery/brief.md]")
        if run(root, "check").returncode != 0:
            fails.append("wymagania z poprawnym wejściem")
        artifact(root, "05-plan/test-plan.md", artifact="test-plan", phase="plan",
                 inputs="[docs/project/03-requirements/requirements.md]")
        chk = run(root, "check")
        if chk.returncode != 0 or "brak głównego" in chk.stdout + chk.stderr or "test-plan" not in (root / "docs/project/README.md").read_text():
            fails.append(f"plan testów jako artefakt fazy plan: {chk.stdout[-200:]}")
        artifact(root, "07-review/2026-09-27-retro.md", artifact="review", phase="review",
                 _body="# Retro\n## TL;DR\nWiem że zespół napewno zdąży.\n## Otwarte pytania\n## Przekazanie\n- Dla: ewa\n")
        chk = run(root, "check")
        lint = SCRIPT.parent.parent / "skills" / "txt-polish-correctness" / "scripts" / "polish_lint.py"   # pack-editorial-pl
        if chk.returncode != 0 or (lint.exists() and "uwag językowych" not in chk.stdout):
            fails.append(f"check: ostrzeżenie językowe dla artefaktu po polsku: {chk.stdout[-300:]}")
        (root / "docs/project/07-review/2026-09-27-retro.md").unlink()
        artifact(root, "08-operations/2026-10-03-przeglad-utrzymania.md", artifact="operations-review", phase="operations",
                 _body="# Przegląd utrzymania\n## TL;DR\nTrzy łatki wdrożone.\n## Otwarte pytania\n## Przekazanie\n- Dla: piotr\n")
        chk = run(root, "check")
        idx = (root / "docs/project/README.md").read_text() if (root / "docs/project/README.md").exists() else ""
        if chk.returncode != 0 or "Utrzymanie" not in idx:
            fails.append(f"faza 9 (operations, 08-operations/) jako artefakt dziennika: {chk.stdout[-300:]}")
        (root / "docs/project/08-operations/2026-10-03-przeglad-utrzymania.md").unlink()
        bad = [
            ("brak TL;DR", dict(_body="# X\n## Przekazanie\n- Dla: a\n")),
            ("zła faza vs katalog", dict(phase="plan")),
            ("nieistniejące wejście", dict(inputs="[docs/project/nie-ma.md]")),
            ("nieznany status", dict(status="done")),
            ("niewypełnione przekazanie", dict(_body="# X\n## TL;DR\nok\n## Przekazanie\n- **Dla:** <persona>\n")),
            ("superseded bez superseded_by", dict(status="superseded")),
        ]
        for name, fields in bad:
            p = artifact(root, "01-discovery/brief.md", **fields)
            if run(root, "check").returncode == 0:
                fails.append(f"nie wykryto: {name}")
        artifact(root, "01-discovery/brief.md")
        run(root, "log", "--by", "ewa", "--phase", "discovery", "Brief | gotowy")
        if "Brief \\| gotowy" not in (root / "docs/project/journal.md").read_text():
            fails.append("log z escapowaniem |")
        readme = (root / "docs/project/README.md").read_text()
        if "Wymagania" not in readme or "Krótko o wyniku" not in readme:
            fails.append("indeks README")
        hook = run(root, "--hook-session").stdout
        if "bieżąca faza:" not in hook:
            fails.append(f"hook sesji: {hook!r}")
        (root / "docs/project/README.md").unlink()
        run(root, "--hook-index", stdin=json.dumps({"tool_input": {"file_path": str(root / "docs/project/01-discovery/brief.md")}}))
        if not (root / "docs/project/README.md").exists():
            fails.append("hook indeksu po zapisie")
        rep = run(root, "report").stdout
        exports = list((root / "docs/project/exports").glob("report-*.md"))
        if not exports or "Pytanie → PO" not in exports[0].read_text():
            fails.append(f"raport: {rep!r}")
    # ── dowody (evidence) ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init")
        (root / "input").mkdir()
        (root / "input/wywiad.md").write_text("Wstęp.\nKierownik sam wybiera ludzi,\nale nie wie, kto jest wolny.\nKara to 2% za tydzień.\n")
        (root / "input/notatki.md").write_text("Planista blokuje specjalistów na etapy.\nUrlop wyklucza przydział.\n")
        dom = root / "docs/project/02-domain"
        corpus = ("# Bank\n## TL;DR\nok\n## S1 — input/wywiad.md\n"
                  "- **E1** > „Kierownik sam wybiera ludzi, ale nie wie, kto jest wolny.” — L2-3\n"
                  "- **E2** > „Kara to 2% za tydzień.” — L4\n"
                  "## S2 — input/notatki.md\n"
                  "- **E3** > „Planista blokuje specjalistów na etapy.” — L1\n"
                  "- **E4** > „Urlop wyklucza przydział.” — L2 [wzmianka]\n")
        (dom / "corpus.md").write_text(corpus)
        area = "# Obszary\n## TL;DR\nok\n## Obszary\n### A1 — Przydział\n- **Dowody:** E1, E2, E3\n"
        (dom / "areas.md").write_text(area)
        if run(root, "evidence").returncode != 0:
            fails.append("evidence: poprawny bank i obszar " + run(root, "evidence").stdout[-200:])
        (dom / "corpus.md").write_text(corpus + "- **E5** > „Zmyślony cytat o fakturach.” — L9\n")
        if run(root, "evidence").returncode == 0:
            fails.append("evidence: nie wykryto zmyślonego cytatu")
        (dom / "corpus.md").write_text(corpus)
        (dom / "areas.md").write_text(area.replace("E1, E2, E3", "E1, E2, E4"))
        if run(root, "evidence").returncode == 0:
            fails.append("evidence: nie wykryto obszaru poniżej progu (wzmianka i jedno źródło)")
        (dom / "areas.md").write_text(area.replace("E1, E2, E3", "E1, E3") + "- **Wskazany przez człowieka:** tak\n")
        r = run(root, "evidence")
        if r.returncode != 0 or "wskazany przez człowieka" not in r.stdout:
            fails.append("evidence: obszar wskazany przez człowieka powinien dać ostrzeżenie, nie błąd")
    with tempfile.TemporaryDirectory() as d:
        if run(Path(d), "--hook-session").stdout.strip():
            fails.append("hook sesji powinien milczeć bez docs/project")
    fails += wip_tests()
    fails += resume_tests()
    total = 18 + WIP_TESTS + RESUME_TESTS + len(bad)
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów dziennika projektu")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
