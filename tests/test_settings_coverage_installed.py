#!/usr/bin/env python3
"""Test pokrycia uprawnień (`.claude/tests/test_settings_coverage.py`, PRB-32) w zainstalowanym projekcie poza
drzewem fabryki: sprawdza zainstalowane `.claude/settings*.json` względem zainstalowanych skilli `talos-story-run`
i `pdi-decisions`, a bez nich pomija sprawdzenie z jasnym komunikatem (zamiast szukać `core/settings.json`).
python3 tests/test_settings_coverage_installed.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
TEST = Path(".claude") / "tests" / "test_settings_coverage.py"


def install(proj: Path, packs: str, *extra: str) -> subprocess.CompletedProcess:
    proj.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=proj, check=False)
    return subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(proj), "--yes",
                           "--packs", packs, *extra], capture_output=True, text=True, timeout=600)


def coverage(proj: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TEST)], cwd=proj, capture_output=True, text=True, timeout=120)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        # C-1/C-2: oba tryby, ustawienia prywatne (settings.local.json) — sprawdza zainstalowany układ
        proj = Path(t) / "both"
        r = install(proj, "mode-talos,mode-pdi")
        check(r.returncode == 0, f"C-0: instalacja mode-talos,mode-pdi: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "pokrytych przez allow" in r.stdout and "decision_record.py" not in r.stdout,
              f"C-1: zainstalowany układ (talos + pdi) przechodzi: {r.stdout[-800:]} {r.stderr[-300:]}")

        # C-2: usunięta reguła w zainstalowanych ustawieniach → test czerwony (sprawdza instalację, nie źródło)
        set_p = proj / ".claude" / "settings.local.json"
        data = json.loads(set_p.read_text(encoding="utf-8"))
        data["permissions"]["allow"] = [a for a in data["permissions"]["allow"] if "decision_record.py" not in a
                                        and "git switch" not in a]
        set_p.write_text(json.dumps(data), encoding="utf-8")
        r = coverage(proj)
        check(r.returncode == 1 and "decision_record.py check" in r.stdout and "git switch main" in r.stdout,
              f"C-2: brak reguły w zainstalowanych ustawieniach wykryty: {r.stdout[-800:]}")

        # C-3: tryb zespołowy (settings.json), sam mode-talos — bez pdi-decisions polecenie pdi pominięte
        proj = Path(t) / "talos"
        r = install(proj, "mode-talos", "--shared")
        check(r.returncode == 0, f"C-0: instalacja mode-talos --shared: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "decision_record.py" not in r.stdout and "pokrytych przez allow" in r.stdout,
              f"C-3: sam mode-talos przechodzi bez poleceń pdi: {r.stdout[-800:]} {r.stderr[-300:]}")

        # C-4: bez talos i pdi — pominięcie z jasnym komunikatem, kod 0
        proj = Path(t) / "none"
        r = install(proj, "none")
        check(r.returncode == 0, f"C-0: instalacja bez nakładek: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "pomijam" in r.stdout and "brak katalogu" not in r.stdout,
              f"C-4: bez talos i pdi — pominięcie, nie błąd: {r.stdout[-800:]} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} test_settings_coverage w zainstalowanym projekcie")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
