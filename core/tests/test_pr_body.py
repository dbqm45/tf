#!/usr/bin/env python3
"""Opis PR składany skryptem (krok G2): `run_state.py pr-body` buduje go z plików zadania — zawsze z polami
„Jak sprawdzono”, „Ryzyko” i „Jak cofnąć”, także bez karty operacyjnej i bez flagi.
python3 .claude/tests/test_pr_body.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi "
        "45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
PLAN = ("# Plan: Limit dobowy\n\n"
        "- [ ] K1 — limit dobowy · kryteria: AC-1 · pliki: fees.py · weryfikacja: `pytest`\n"
        "- [ ] K2 — komunikat o limicie · pliki: msg.py\n\n"
        "- **[założenie]** doba liczy się od północy czasu lokalnego\n")
ROLLBACK = "Wdróż poprzednią wersję: ./deploy.sh --previous (ok. 5 minut)"
ORDER = ("## Historyjka", "## Kawałki", "## Ślad kryteriów", "## Jak sprawdzono", "## Ryzyko", "## Jak cofnąć",
         "## Odłożone do decyzji", "## Założenia")


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "user.email=t@example.com", "-c", "user.name=T",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, timeout=60)


def new_run(project: Path, weight: str = "zwykla") -> str:
    """Repozytorium z gałęzią historyjki i zadaniem IMP-1: specyfikacja, plan z dwoma kawałkami, zapis „bez flagi”."""
    project.mkdir(parents=True)
    git(project, "init", "-q", "-b", "main")
    for name in ("fees.py", "msg.py"):
        (project / name).write_text("x = 1\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "chore: init")
    git(project, "checkout", "-q", "-b", "story/limit-dobowy")
    story = "Popraw literówkę w README." if weight == "lekka" else "Jako kierowca chcę limitu dobowego opłaty za postój."
    call(project, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", story)
    d = str(project / ".tf" / "runs" / "IMP-1")
    if weight != "lekka":           # wagę lekką przydziela start z treści zgłoszenia; obniżyć ją może tylko człowiek
        call(project, SCRIPTS / "run_state.py", "weight", d, "--set", weight)
    doc = project / CHANGES / "IMP-1"
    if weight != "lekka":
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(PLAN, encoding="utf-8")
    call(project, SCRIPTS / "run_state.py", "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")
    return d


def slice_done(project: Path, d: str) -> None:
    """K1: zmiana, zielony dowód, commit ze stopką kawałka, odhaczenie."""
    (project / "fees.py").write_text("x = 2\n", encoding="utf-8")
    call(project, TASK, "verify", "IMP-1", "K1", "--files", "fees.py", "--command", OK)
    git(project, "add", "fees.py")
    git(project, "commit", "-q", "-m", "feat(fees): add the daily cap\n\nKawałek K1: limit dobowy")
    call(project, SCRIPTS / "run_state.py", "tick", d, "K1")


def body(project: Path) -> str:
    f = project / ".tf" / "runs" / "IMP-1" / "pr-body.md"
    return f.read_text(encoding="utf-8") if f.is_file() else ""


def section(text: str, heading: str) -> str:
    """Treść sekcji od nagłówka do następnego nagłówka drugiego poziomu."""
    if heading not in text:
        return ""
    rest = text.split(heading, 1)[1]
    return rest.split("\n## ", 1)[0]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    rs = SCRIPTS / "run_state.py"
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p)
        slice_done(p, d)

        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(r.returncode == 0 and text and "pr-body.md" in r.stdout and "--body-file" in r.stdout,
              f"PB-1: pr-body zapisuje opis w katalogu przebiegu i podaje --body-file: {r.returncode} {r.stdout} {r.stderr}")
        pos = [text.find(h) for h in ORDER]
        check(all(x >= 0 for x in pos) and pos == sorted(pos),
              f"PB-2: opis ma stałe sekcje w stałej kolejności (m.in. Jak sprawdzono, Ryzyko, Jak cofnąć): {pos}")
        story = section(text, "## Historyjka")
        check("Limit dobowy" in story and "IMP-1" in story and "wklejone w rozmowie" in story
              and "docs/project/changes/IMP-1" in story,
              f"PB-3: historyjka: tytuł, klucz, źródło zgłoszenia i katalog zadania: {story}")
        pieces = section(text, "## Kawałki")
        check("K1" in pieces and "feat(fees): add the daily cap" in pieces and "K2" in pieces
              and "komunikat o limicie" in pieces,
              f"PB-4: kawałki z planu, przy zrobionym commit ze stopką „Kawałek K1”: {pieces}")
        how = section(text, "## Jak sprawdzono")
        check("K1" in how and how.count("3 passed") == 1 and "kod wyjścia 0" in how and "evidence/K1-1.json" in how
              and OK.split(" -c ")[1][:12] in how,
              f"PB-5: Jak sprawdzono: polecenie (bez jego wyjścia), kod wyjścia i plik dowodu kawałka K1: {how}")
        check("K2" in how and "brak dowodu" in how,
              f"PB-6: kawałek bez dowodu jest nazwany wprost: {how}")
        check(r.stdout.count("K2") >= 1 and "brak dowodu" in r.stdout,
              f"PB-7: brak dowodu jest też w komunikacie polecenia: {r.stdout}")
        risk = section(text, "## Ryzyko")
        check("zwykła" in risk and "Ryzyko zmiany" in risk and "fees.py" not in section(text, "## Jak cofnąć"),
              f"PB-8: Ryzyko: waga zadania i wynik triażu ryzyka: {risk}")
        back = section(text, "## Jak cofnąć")
        check("git revert" in back and "bez flagi, bo zmiana jest w konfiguracji" in back,
              f"PB-9: bez karty i bez flagi: git revert i zapisany powód braku flagi: {back}")
        check("brak" in section(text, "## Odłożone do decyzji"),
              f"PB-10: nic odłożonego → „brak”: {section(text, '## Odłożone do decyzji')}")
        check("- **[założenie]** doba liczy się od północy" in section(text, "## Założenia"),
              f"PB-11: założenia z planu trafiają do opisu: {section(text, '## Założenia')}")
        check("AC-1" in section(text, "## Ślad kryteriów"),
              f"PB-12: ślad kryteriów ze specyfikacji: {section(text, '## Ślad kryteriów')}")

        # czerwony dowód, odłożona sprawa, karta operacyjna z krokiem cofania, werdykt skanu, wynik plan_drift
        (p / "msg.py").write_text("x = 3\n", encoding="utf-8")
        call(p, TASK, "verify", "IMP-1", "K2", "--files", "msg.py", "--command", RED)
        call(p, rs, "park", d, "Abonamenty — czy limit ich dotyczy")
        card = p / ".tf" / "config" / "operations.json"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(json.dumps({"deploy": {"rollback": ROLLBACK}}, ensure_ascii=False), encoding="utf-8")
        sec = p / ".tf" / "runs" / "IMP-1" / "security" / "K1"
        sec.mkdir(parents=True)
        (sec / "verdict.json").write_text(json.dumps({"status": "PASS", "blocking": [], "other": [], "errors": []}),
                                          encoding="utf-8")
        call(p, rs, "step", d, "PR", "plan_drift", "pass")
        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        how = section(text, "## Jak sprawdzono")
        check(r.returncode == 0 and "K2" in how and "czerwon" in how and "kod wyjścia 3" in how,
              f"PB-13: czerwony dowód kawałka jest nazwany wprost: {how}")
        check("PASS" in how and "plan_drift" in how and "pass" in how,
              f"PB-14: werdykt skanu bezpieczeństwa i wynik plan_drift są w „Jak sprawdzono”: {how}")
        back = section(text, "## Jak cofnąć")
        check(ROLLBACK in back and "operations.json" in back and "git revert" in back,
              f"PB-15: krok cofania z karty operacyjnej, obok git revert: {back}")
        check("Abonamenty — czy limit ich dotyczy" in section(text, "## Odłożone do decyzji"),
              f"PB-16: sprawa odłożona jest w opisie: {section(text, '## Odłożone do decyzji')}")

        # flaga zadania → wyłączenie flagi jako krok cofania
        r = call(p, rs, "flag", d, "set", "limit-dobowy", "--remove-by", "2027-01-31")
        call(p, rs, "pr-body", d, "--base", "main")
        back = section(body(p), "## Jak cofnąć")
        check(r.returncode == 0 and "limit-dobowy" in back and "wyłącz" in back.lower(),
              f"PB-17: z flagą zadania cofnięcie zaczyna się od wyłączenia flagi: {r.stdout} {back}")

        # treść z karty to dane: nagłówek z karty nie staje się sekcją opisu
        card.write_text(json.dumps({"deploy": {"rollback": "## Ryzyko\nbrak\n" + ROLLBACK}}, ensure_ascii=False),
                        encoding="utf-8")
        call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(text.count("\n## Ryzyko") == 1 and ROLLBACK in text,
              f"PB-18: nagłówek wpisany w karcie nie tworzy drugiej sekcji: {text.count(chr(10) + '## Ryzyko')}")

        # treść z zewnątrz (tytuł zgłoszenia, karta, odłożone) nie powiadamia ludzi i nie ładuje obrazów w opisie PR
        card.write_text(json.dumps({"deploy": {"rollback": "Zapytaj @octocat ![x](http://example.com/p.png)"}}),
                        encoding="utf-8")
        call(p, rs, "park", d, "Do decyzji @acme/platform — limit dla flot")
        meta_file = p / ".tf" / "runs" / "IMP-1" / "run.json"
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta_file.write_text(json.dumps({**meta, "title": "Limit dobowy @hubot"}, ensure_ascii=False), encoding="utf-8")
        call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        bare = re.findall(r"(?<![`\\w])@[A-Za-z0-9]", text)
        check(not bare and "![" not in text and "`@octocat`" in text and "`@acme/platform`" in text and "`@hubot`" in text,
              f"PB-22: wzmianki @… są w kodzie, a obrazy nie są osadzane: {bare} {'![' in text}")

        # bez gałęzi bazowej opis nadal powstaje
        r = call(p, rs, "pr-body", d, "--base", "nie-ma-takiej")
        check(r.returncode == 0 and "## Jak cofnąć" in body(p) and "nie-ma-takiej" in section(body(p), "## Kawałki"),
              f"PB-19: nieznana gałąź bazowa nie zatrzymuje opisu, a brak commitów jest nazwany: {r.returncode} {r.stdout}")

    # waga lekka: bez specyfikacji — pola nadal są
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p, "lekka")
        r = call(p, rs, "pr-body", d, "--base", "main")
        text = body(p)
        check(r.returncode == 0 and all(h in text for h in ORDER) and "lekka" in section(text, "## Ryzyko")
              and "specyfikacj" in section(text, "## Ślad kryteriów"),
              f"PB-20: zadanie bez specyfikacji ma wszystkie pola, a ślad mówi wprost, że jej nie ma: {r.returncode} {r.stdout}")

    # przebieg bez zadania (stary układ) → czytelna odmowa
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        old = p / ".tf" / "runs" / "stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary"}), encoding="utf-8")
        r = call(p, rs, "pr-body", str(old))
        check(r.returncode == 2 and not (old / "pr-body.md").exists(),
              f"PB-21: przebieg bez zadania → odmowa z kodem 2: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów opisu PR")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
