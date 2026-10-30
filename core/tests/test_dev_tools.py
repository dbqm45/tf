#!/usr/bin/env python3
"""Testy narzędzi oszczędzających tokeny: factory/check.py (pętla CI), build.py new-skill (rozszerzenia),
factory/finish.py (zamknięcie zadania do commita, bez pushu)."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "check.py").is_file())


def run(args, cwd=None, timeout=300):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd, timeout=timeout)


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, capture_output=True, text=True)


def stub(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("import sys\n" + body + "\n", encoding="utf-8")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # ── A: check.py ──
    with tempfile.TemporaryDirectory() as t:
        r0 = Path(t)
        stub(r0 / "factory" / "build.py", "print('ostrzeżenie: x'); print('✓ OK')")
        stub(r0 / "factory" / "skill_gate.py", "print('✓ skilli: 3, do przejścia przez bramkę: 0')")
        stub(r0 / "tests" / "test_ok.py", "print('✓ 2/2 testów ok')")
        stub(r0 / "tests" / "test_bad.py", "print('✗ coś się zepsuło w kroku 7'); print('✗ 0/1 testów bad'); sys.exit(1)")
        stub(r0 / "tests" / "run_skill_evals.py", "print('✓ pliki scenariuszy: 3, błędów: 0')")
        r = run([ROOT / "factory" / "check.py", "--root", r0])
        lines = r.stdout.strip().splitlines()
        check(r.returncode == 1 and "coś się zepsuło w kroku 7" in r.stdout and "test_bad.py" in r.stdout
              and "2/2 testów ok" not in r.stdout and "ostrzeżenie" not in r.stdout and lines and lines[-1].startswith("✗"),
              f"A-1: błąd z szczegółami, zielone tylko jako liczba, ostatnia linia to werdykt: {r.stdout}{r.stderr}")
        check(re.search(r"testy\D+1/2", r.stdout) is not None and "dziennik" in r.stdout and "pominięto" in r.stdout,
              f"A-2: podsumowanie testów (zielone/wszystkie) i pominięte kroki bez skryptów: {r.stdout}")
        r = run([ROOT / "factory" / "check.py", "--root", r0, "-k", "ok"])
        check(r.returncode == 0 and r.stdout.strip().splitlines()[-1].startswith("✓"), f"A-3: -k zawęża testy: {r.stdout}")
        r = run([ROOT / "factory" / "check.py", "--root", r0, "--json"])
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        check(d.get("ok") is False and any(s["name"] == "tests/test_bad.py" and not s["ok"] for s in d.get("steps", [])),
              f"A-4: --json: {r.stdout[:300]}")

    # Podpowiedzi wszystkich skilli naraz: nowy skill nie może „podkraść” podpowiedzi starszemu (krok check.py).
    r = run([ROOT / "factory" / "skill_gate.py", "--hints"], cwd=ROOT)
    check(r.returncode == 0 and "podpowiedzi" in r.stdout and r.stdout.strip().splitlines()[-1].startswith("✓"),
          f"A-5: skill_gate --hints sprawdza trafienia hooka dla scenariuszy wszystkich skilli: {r.stdout[-300:]}{r.stderr[-300:]}")
    with tempfile.TemporaryDirectory() as t:
        r0 = Path(t)
        stub(r0 / "factory" / "skill_gate.py", "print('✗ #x: hook nie podpowie skilla'); print('✗ podpowiedzi: 1 skill'); sys.exit(1)"
             if True else "")
        r = run([ROOT / "factory" / "check.py", "--root", r0])
        check(r.returncode == 1 and "podpowiedzi wszystkich skilli" in r.stdout, f"A-6: krok podpowiedzi w check.py: {r.stdout}")

    # ── B: build.py new-skill — termin przeglądu, słowa, --role, --name-only ──
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "f"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "logs", "__pycache__", "*.zip"))
        r = run([root / "factory" / "build.py", "new-skill", "core-demo-x", "Użyj przy demo. Nie do niczego (core-grounding).",
                 "--role", "nie-ma-takiej"], cwd=root)
        check(r.returncode == 2 and not (root / ".claude" / "skills" / "core-demo-x").exists(),
              f"B-1: nieznana rola → kod 2, nic nie utworzone: {r.stdout}{r.stderr}")
        role_files = sorted(root.glob("factory/packs/*/roles/*.yaml")) or sorted(root.glob("factory/roles/*.yaml"))
        if not role_files:                     # sam rdzeń: rola projektu do testu wpięcia
            (root / "factory" / "roles").mkdir(parents=True, exist_ok=True)
            (root / "factory" / "roles" / "demo.yaml").write_text(
                "name: demo\ntitle: Demo\ntier: std\ntriggers: demo\nidentity: demo\ntools: [Read]\nskills: [core-grounding]\n",
                encoding="utf-8")
            role_files = [root / "factory" / "roles" / "demo.yaml"]
        role_file = role_files[0]
        r = run([root / "factory" / "build.py", "new-skill", "core-demo-x", "Użyj przy demo. Nie do niczego (core-grounding).",
                 "--role", role_file.stem, "--name-only"], cwd=root)
        md = (root / ".claude" / "skills" / "core-demo-x" / "SKILL.md")
        text = md.read_text(encoding="utf-8") if md.exists() else ""
        m = re.search(r"^  przeglad: \"(\d{4}-\d{2}-\d{2})\"$", text, re.M)
        role = role_file.read_text(encoding="utf-8")
        check(r.returncode == 0 and m and "  widocznosc: nazwa" in text and re.search(r"^  slowa: \"", text, re.M)
              and re.search(r"^skills: \[.*\bcore-demo-x\]$", role, re.M),
              f"B-2: termin przeglądu, słowa, widoczność i wpięcie do roli: {r.stdout[-300:]}{r.stderr[-300:]}\n{text[:400]}")
        fr = run([root / "factory" / "freshness.py", "--root", root, "--json"])
        rows = {x["skill"]: x["status"] for x in json.loads(fr.stdout or "{}").get("skills", [])}
        check(rows.get("core-demo-x") == "ok", f"B-3: termin przeglądu poprawny dla freshness.py: {rows.get('core-demo-x')}")

    # ── C: finish.py ──
    if shutil.which("git"):
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t) / "repo"
            repo.mkdir()
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.name", "t")          # runner CI nie ma globalnej tożsamości gita
            git(repo, "config", "user.email", "t@t")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "a.txt").write_text("a\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "chore: init")
            stub(repo / "scripts" / "check_commit_message.py",
                 "t = open(sys.argv[sys.argv.index('--file') + 1]).read()\nsys.exit(0 if t.startswith('feat') else 1)")
            msg = Path(t) / "msg.txt"
            msg.write_text("feat(x): add b\n\nCo-Authored-By: t\n")
            fin = ROOT / "factory" / "finish.py"
            (repo / "b.txt").write_text("b\n")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            n = git(repo, "rev-list", "--count", "HEAD").stdout.strip()
            check(r.returncode == 2 and n == "1", f"C-1: na main odmowa: {r.stdout}{r.stderr}")
            git(repo, "checkout", "-q", "-b", "feature")
            bad = Path(t) / "bad.txt"
            bad.write_text("zła treść\n")
            r = run([fin, "--root", repo, "--message", bad, "--no-check"])
            check(r.returncode == 1 and git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1",
                  f"C-2: zła treść commita → kod 1, bez commita: {r.stdout}{r.stderr}")
            (repo / ".env").write_text("SECRET=1\n")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            check(r.returncode == 2 and ".env" in r.stdout + r.stderr, f"C-3: plik .env w zmianach → odmowa: {r.stdout}{r.stderr}")
            (repo / ".env").unlink()
            stub(repo / "factory" / "check.py", "print('✗ testy 0/1'); sys.exit(1)")
            r = run([fin, "--root", repo, "--message", msg])
            check(r.returncode == 1 and git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1",
                  f"C-4: czerwone sprawdzenia → bez commita: {r.stdout}{r.stderr}")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            last = git(repo, "log", "-1", "--format=%s").stdout.strip()
            check(r.returncode == 0 and last == "feat(x): add b" and "git push -u origin feature" in r.stdout
                  and git(repo, "status", "--porcelain").stdout.strip() == "",
                  f"C-5: commit z treścią z pliku, polecenie pushu wypisane, nie wykonane: {r.stdout}{r.stderr} {last}")
            r = run([fin, "--root", repo, "--message", msg, "--no-check"])
            check(r.returncode == 0 and "nic do commita" in r.stdout, f"C-6: brak zmian → nic do commita: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów narzędzi")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
