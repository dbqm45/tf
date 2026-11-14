#!/usr/bin/env python3
"""Przegląd, który się kończy (krok F2): `scope-reviewer` oznacza ustalenia jako ważne / drobne / zastane, nową rundę
zaczyna tylko ważne, a limitu rund kawałka pilnuje skrypt — trzecia runda bez decyzji człowieka to odmowa.
python3 .claude/tests/test_review_rounds.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
SKILL = ROOT / ".claude" / "skills" / "tf" / "SKILL.md"


def call(project: Path, cfg: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "CLAUDE_PROJECT_DIR": str(project), "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=project, capture_output=True, text=True,
                          env=env, timeout=120)


def rounds(project: Path) -> int:
    meta = json.loads((project / ".tf" / "runs" / "IMP-1" / "run.json").read_text(encoding="utf-8"))
    return len((meta.get("current") or {}).get("rounds") or [])


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        p.mkdir()
        call(p, cfg, "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        call(p, cfg, "run_state.py", "weight", d, "--set", "zwykla")
        subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "task_state.py"), "mode", "IMP-1", "auto"], cwd=p,
                       capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        (p / "docs" / "project" / "changes" / "IMP-1" / "spec.md").write_text(
            "# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi "
            "45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n",
            encoding="utf-8")
        call(p, cfg, "run_state.py", "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")

        r1 = call(p, cfg, "run_state.py", "step", d, "K1", "R1", "zakres", "fail")
        r2 = call(p, cfg, "run_state.py", "step", d, "K1", "R2", "kod", "run")
        check(r1.returncode == 0 and r2.returncode == 0 and rounds(p) == 2,
              f"PR-1: dwie rundy kawałka przechodzą: {r1.stdout}{r1.stderr} | {r2.stdout}{r2.stderr}")
        r = call(p, cfg, "run_state.py", "step", d, "K1", "R3", "test", "run")
        check(r.returncode == 2 and "STOP" in r.stdout and "--needs stop --code" in r.stdout and rounds(p) == 2,
              f"PR-2: trzecia runda bez decyzji człowieka → odmowa z podpowiedzią STOP, stan bez zmian: {r.returncode} {r.stdout}")

        # po zatrzymaniu i decyzji człowieka pętla dostaje kolejne dwie próby
        call(p, cfg, "run_state.py", "stage", d, "needs", "--needs", "stop", "--code", "testy", "--reason", "pytest: 1 failed")
        r3 = call(p, cfg, "run_state.py", "step", d, "K1", "R3", "test", "run")
        r4 = call(p, cfg, "run_state.py", "step", d, "K1", "R4", "kod", "run")
        r5 = call(p, cfg, "run_state.py", "step", d, "K1", "R5", "test", "run")
        meta = json.loads((p / ".tf" / "runs" / "IMP-1" / "run.json").read_text(encoding="utf-8"))
        check(r3.returncode == 0 and r4.returncode == 0 and r5.returncode == 2 and rounds(p) == 4,
              f"PR-3: po decyzji człowieka dwie kolejne rundy, piąta znów odmowa: {r3.returncode} {r4.returncode} "
              f"{r5.returncode} {r5.stdout}")
        check(meta.get("stage") == "slices" and not any(k in meta for k in ("needs", "stop_text", "stop_code", "needs_at")),
              f"PR-4: wznowienie przez step czyści cały zapis zatrzymania: {sorted(meta)}")
        r = call(p, cfg, "run_state.py", "step", d, "K2", "R1", "test", "run")
        check(r.returncode == 0 and rounds(p) == 1, f"PR-5: nowy kawałek liczy rundy od początku: {r.returncode} {r.stdout}")
        r = call(p, cfg, "run_state.py", "step", d, "K2", "R3", "test", "run")
        check(r.returncode == 2, f"PR-6: nowy kawałek też nie zaczyna od trzeciej rundy: {r.returncode} {r.stdout}")

    # agent przeglądu: etykiety ustaleń i reguła nowej rundy
    cfg_text = (ROOT / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8")
    prompt = cfg_text.split("\n  scope-reviewer:", 1)[-1][:2500] if "\n  scope-reviewer:" in cfg_text else ""
    check(all(w in prompt for w in ("[ważne]", "[drobne]", "[zastane]")),
          "PR-7: scope-reviewer oznacza każde ustalenie: [ważne], [drobne] albo [zastane]")
    check("SPOZA ZAKRESU" in prompt and "tylko" in prompt and "ważne" in prompt and "sprzed zmiany" in prompt
          and "poprzedniej rundy" in prompt,
          "PR-8: werdykt SPOZA ZAKRESU tylko przy ustaleniu ważnym; zastane to kod sprzed zmiany; druga runda ogląda "
          "tylko zmiany od poprzedniej rundy")
    body = SKILL.read_text(encoding="utf-8")
    step4 = body.split("**Przegląd zakresu:**", 1)[-1].split("5. **Commit**", 1)[0]
    check(all(w in step4 for w in ("ważne", "drobne", "zastane", "parked.md")) and len(body) <= 15000,
          f"PR-9: pętla wycofuje kod tylko przy ustaleniu ważnym, drobne i zastane odkłada; SKILL.md w limicie: {len(body)}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów przeglądu i limitu rund")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
