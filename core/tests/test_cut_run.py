#!/usr/bin/env python3
"""Przebieg cięcia zmiany pdi w układzie zadania (krok E6): `/tf TSK-57 --change CHG-12` zakłada zadanie
`CHG-12-TSK-57` ze specyfikacją, dowodami i flagą z planu wydania, a pdi dostaje to, co dotąd — raport cięcia
w `docs/project/changes/CHG-12/runs/TSK-57.md`, gałąź `story/tsk-57-…` i pierwszy commit z kawałkiem.
python3 .claude/tests/test_cut_run.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'

PLAN_MD = """---
artifact: plan
phase: plan
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
tasks: [TSK-57, TSK-58, TSK-59]
---
# Plan zmiany CHG-12

| Cięcie | Wydanie | Flaga | Wartość | Pliki | Weryfikacja |
|---|---|---|---|---|---|
| TSK-57 | R1 | payment-retry | klient ponawia nieudaną płatność | src/retry.py | `pytest -k retry` |
| TSK-58 | R1 | payment-retry | brak podwójnego obciążenia | src/charge.py | `pytest -k charge` |
| TSK-59 | R2 | — | historia prób w panelu | src/history.py | `pytest -k history` |
"""
INTENT_MD = """---
artifact: intent
phase: discovery
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
---
# Zamiar zmiany CHG-12

## Problem
Klient nie może ponowić nieudanej płatności i porzuca zamówienie.
"""
RELEASE = """change: CHG-12
flags:
  - key: payment-retry
    tasks: [TSK-57, TSK-58]
    owner: PO Payments
    remove_by: 2026-12-31
"""
# to samo wyrażenie, którym pdi czyta listę odłożonych spraw z opisu PR cięcia (pdi: src/pdi/pr_loop.py, _outside_plan)
PDI_PARKED = re.compile(r"^## Odłożone do decyzji\s*\n([\s\S]*?)(?=^## |\Z)", re.MULTILINE)


def sh(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=project, capture_output=True, text=True, timeout=60)


def git(project: Path, *args: str) -> str:
    r = sh(project, "git", *args)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout


def script(project: Path, cfg: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "CLAUDE_PROJECT_DIR": str(project), "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=project, capture_output=True, text=True,
                          env=env, timeout=120)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        chg = p / CHANGES / "CHG-12"
        chg.mkdir(parents=True)
        (chg / "plan.md").write_text(PLAN_MD, encoding="utf-8")
        (chg / "intent.md").write_text(INTENT_MD, encoding="utf-8")
        (chg / "release.yaml").write_text(RELEASE, encoding="utf-8")
        (p / "src").mkdir()
        (p / "src" / "retry.py").write_text("def retry():\n    return False\n", encoding="utf-8")
        git(p, "init", "-q", "-b", "main")
        for k, v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            git(p, "config", k, v)
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "docs: plan zmiany CHG-12")
        git(p, "switch", "-q", "-c", "pdi/CHG-12-delivery")
        git(p, "switch", "-q", "-c", "story/tsk-57-ponowienie-platnosci")

        # start: zadanie cięcia zamiast katalogu .tf/runs/cuts/
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-57", "--change", "CHG-12")
        run_dir, doc = p / ".tf" / "runs" / "CHG-12-TSK-57", p / CHANGES / "CHG-12-TSK-57"
        check(r.returncode == 0 and r.stdout.strip() == ".tf/runs/CHG-12-TSK-57" and run_dir.is_dir()
              and not (p / ".tf" / "runs" / "cuts").exists(),
              f"C-1: start --task zakłada katalog roboczy zadania cięcia, bez .tf/runs/cuts/: {r.returncode} {r.stdout} {r.stderr}")
        check(all((doc / n).is_file() for n in ("task.json", "ticket.md", "plan.md")) and not (run_dir / "story.md").exists(),
              f"C-2: pliki trwałe cięcia w docs/project/changes/CHG-12-TSK-57/: {sorted(x.name for x in doc.iterdir()) if doc.is_dir() else '—'}")
        task = json.loads((doc / "task.json").read_text(encoding="utf-8")) if (doc / "task.json").is_file() else {}
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8")) if (run_dir / "run.json").is_file() else {}
        check(task.get("change") == "CHG-12" and task.get("cut") == "TSK-57" and meta.get("key") == "CHG-12-TSK-57"
              and meta.get("task_dir") == "docs/project/changes/CHG-12-TSK-57" and meta.get("change") == "CHG-12"
              and meta.get("task") == "TSK-57" and meta.get("flag") == "payment-retry",
              f"C-3: task.json i run.json wskazują zmianę, cięcie i flagę: {task} {meta}")
        ticket = (doc / "ticket.md").read_text(encoding="utf-8") if (doc / "ticket.md").is_file() else ""
        check("Cięcie TSK-57 zmiany CHG-12" in ticket and "klient ponawia nieudaną płatność" in ticket
              and "Klient nie może ponowić" in ticket and "`Change: TSK-57`" in ticket and "`Flag: payment-retry`" in ticket,
              f"C-4: ticket.md z wiersza cięcia i zamiaru zmiany, ze stopkami commitów: {ticket[:500]}")
        flag = task.get("flag") or {}
        check(flag.get("key") == "payment-retry" and flag.get("remove_by") == "2026-12-31",
              f"C-5: flaga z planu wydania zapisana w zadaniu (klucz i data usunięcia): {flag}")
        check(not (p / CHANGES / "INDEX.md").exists(), "C-6: zadanie cięcia nie zakłada INDEX.md")
        status = git(p, "status", "--porcelain")
        check(status.split() == ["??", "docs/project/changes/CHG-12-TSK-57/"],
              f"C-7: po starcie w repozytorium jest tylko nowy katalog zadania: {status!r}")
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-57", "--change", "CHG-12")
        check(r.returncode == 2 and "już istnieje" in r.stdout, f"C-8: powtórny start → kod 2: {r.returncode} {r.stdout}")
        r = script(p, cfg, "intake.py", "resolve", "--json", "TSK-57 --auto --change CHG-12")
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        check(out.get("kind") == "wznowienie" and out.get("key") == "CHG-12-TSK-57" and ".tf/runs/CHG-12-TSK-57" in out.get("next", ""),
              f"C-9: /tf TSK-57 przy istniejącym zadaniu cięcia wznawia je: {r.stdout[:400]} {r.stderr[-200:]}")

        # cięcie bez flagi w planie wydania: jawny brak flagi z powodem, bez pytania człowieka
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-59", "--change", "CHG-12")
        t59 = json.loads((p / CHANGES / "CHG-12-TSK-59" / "task.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
        check("CHG-12" in ((t59.get("flag") or {}).get("none") or "") and "TSK-59" in ((t59.get("flag") or {}).get("none") or ""),
              f"C-10: cięcie bez flagi w planie wydania → „bez flagi” z powodem: {t59.get('flag')} {r.stdout} {r.stderr}")
        import shutil
        shutil.rmtree(p / CHANGES / "CHG-12-TSK-59")
        shutil.rmtree(p / ".tf" / "runs" / "CHG-12-TSK-59")

        # polecenia przebiegu działają dla cięcia jak dla zadania
        d = str(run_dir)
        r = script(p, cfg, "run_state.py", "stage", d, "intake", "--auto")
        task = json.loads((doc / "task.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and task.get("mode") == "auto" and task.get("weight") == "pelna",
              f"C-11: --auto zapisuje tryb Auto także przy wadze pełnej cięcia (płatności): {r.returncode} {r.stdout} {r.stderr} "
              f"{task.get('mode')} {task.get('weight')}")
        r = script(p, cfg, "run_state.py", "spec", d, "new")
        check(r.returncode == 0 and (doc / "spec.md").is_file(), f"C-12: szablon specyfikacji cięcia: {r.returncode} {r.stdout} {r.stderr}")
        (doc / "spec.md").write_text(
            "# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając nieudaną płatność, gdy klient wybiera ponowienie, wtedy "
            "płatność jest ponawiana raz.\n\n## Bez zmian\n\n- Udana płatność nie jest ponawiana.\n\n## Poza zakresem\n\n"
            "- Płatności cykliczne.\n", encoding="utf-8")
        r = script(p, cfg, "run_state.py", "spec", d)
        check(r.returncode == 0, f"C-13: specyfikacja cięcia przechodzi kontrolę: {r.returncode} {r.stdout} {r.stderr}")
        (doc / "plan.md").write_text("# Plan: TSK-57\n\n- [ ] K1 — ponowienie płatności · kryteria: AC-1 · pliki: src/retry.py, "
                                     "tests/test_retry.py · weryfikacja: `pytest -k retry`\n", encoding="utf-8")
        r = script(p, cfg, "run_state.py", "stage", d, "plan")
        r2 = script(p, cfg, "run_state.py", "step", d, "K1", "R1", "test", "run")
        check(r.returncode == 0 and r2.returncode == 0,
              f"C-14: cięcie o wadze pełnej w trybie Auto przechodzi od planu do kawałka bez zgody człowieka: "
              f"{r.returncode} {r.stdout} {r.stderr} | {r2.returncode} {r2.stdout} {r2.stderr}")

        # kawałek: commit ze stopkami, dowód weryfikacji, odhaczenie
        (p / "src" / "retry.py").write_text("def retry():\n    return True\n", encoding="utf-8")
        (p / "tests").mkdir()
        (p / "tests" / "test_retry.py").write_text("def test_ac_1_retry():   # AC-1\n    assert True\n", encoding="utf-8")
        git(p, "add", "src/retry.py", "tests/test_retry.py")
        git(p, "commit", "-q", "-m", "feat(payments): retry a failed payment\n\nKawałek K1: ponowienie płatności\n\n"
                                     "Change: TSK-57\nFlag: payment-retry")
        r = script(p, cfg, "run_state.py", "verify", d, "K1", "--files", "src/retry.py,tests/test_retry.py", "--command", OK)
        ev = sorted((doc / "evidence").glob("K1-*.json")) if (doc / "evidence").is_dir() else []
        check(r.returncode == 0 and len(ev) == 1, f"C-15: dowód weryfikacji kawałka cięcia: {r.returncode} {r.stdout} {r.stderr}")
        r = script(p, cfg, "run_state.py", "tick", d, "K1")
        check(r.returncode == 0 and "- [x] K1" in (doc / "plan.md").read_text(encoding="utf-8"),
              f"C-16: tick odhacza kawałek z dowodem: {r.returncode} {r.stdout} {r.stderr}")
        r = script(p, cfg, "run_state.py", "trace", d, "--base", "pdi/CHG-12-delivery")
        check(r.returncode == 0 and "AC-1" in r.stdout, f"C-17: ślad kryteriów cięcia: {r.returncode} {r.stdout} {r.stderr}")

        # zakończenie: raport w katalogu zadania i ten sam w miejscu, z którego czyta go pdi
        r = script(p, cfg, "run_state.py", "park", d, "limit prób ponowienia — src/retry.py:2 — brak limitu — dodać limit 3 — do decyzji")
        r = script(p, cfg, "run_report.py", "finish", d)
        kept = chg / "runs" / "TSK-57.md"
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        own = (doc / "report.md").read_text(encoding="utf-8") if (doc / "report.md").is_file() else ""
        check(r.returncode == 2 and text.startswith("# Raport przebiegu TSK-57 (CHG-12)\n\n") and own
              and text == "# Raport przebiegu TSK-57 (CHG-12)\n\n" + own,
              f"C-18: raport cięcia tam, gdzie szuka go pdi, z tą samą treścią co report.md zadania: {r.returncode} {text[:200]}")
        m = PDI_PARKED.search(text)
        items = [ln.strip()[2:] for ln in (m.group(1) if m else "").splitlines() if ln.strip().startswith("- ")]
        check(len(items) == 1 and "limit prób ponowienia" in items[0] and "- Plan: 1/1" in text,
              f"C-19: pdi wyczyta z raportu odłożone sprawy; postęp planu z commitów ze stopką Change: {items} {text[:400]}")
        check("git add docs/project/changes/CHG-12-TSK-57 docs/project/changes/CHG-12/runs/TSK-57.md" in r.stdout
              and "INDEX.md" not in r.stdout and "docs(task): record CHG-12-TSK-57" in r.stdout and "Change: TSK-57" in r.stdout,
              f"C-20: finish podaje jeden commit końcowy: katalog zadania i raport cięcia, bez INDEX.md, ze stopką: {r.stdout[-500:]}")
        git(p, "add", "docs/project/changes/CHG-12-TSK-57", "docs/project/changes/CHG-12/runs/TSK-57.md")
        git(p, "commit", "-q", "-m", "docs(task): record CHG-12-TSK-57\n\nChange: TSK-57")
        subjects = git(p, "log", "--reverse", "--format=%s", "pdi/CHG-12-delivery..HEAD").splitlines()
        check(subjects[:1] == ["feat(payments): retry a failed payment"] and git(p, "status", "--porcelain") == "",
              f"C-21: pierwszy commit gałęzi cięcia to kawałek (tytuł PR w pdi), drzewo czyste: {subjects}")
        body = git(p, "show", "story/tsk-57-ponowienie-platnosci:docs/project/changes/CHG-12/runs/TSK-57.md")
        check(body == text, "C-22: raport cięcia jest na gałęzi cięcia pod ścieżką, którą czyta pdi")

    # przebieg w starym układzie (bez zadania) nie jest już zakładany ani prowadzony
    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        old = p / ".tf" / "runs" / "cuts" / "2026-11-01-tsk-1"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "tsk-1", "started_at": "2026-11-01T10:00:00+00:00",
                                                  "change": "CHG-1", "task": "TSK-1"}), encoding="utf-8")
        r = script(p, cfg, "run_state.py", "verify", str(old), "K1", "--files", "a.py")
        check(r.returncode != 0 and "od nowa" in r.stdout + r.stderr and "/tf TSK-1" in r.stdout + r.stderr,
              f"C-23: przebieg bez zadania → komunikat „zacznij cięcie od nowa”: {r.returncode} {r.stdout} {r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów przebiegu cięcia")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
