#!/usr/bin/env python3
"""Nazwy modeli w konfiguracji (krok H20): każdy identyfikator `claude-…` w konfiguracji fabryki i w kodzie silnika
jest znany (bieżący albo dozwolony starszy), aliasy wskazują bieżące modele, a stara data sprawdzenia to ostrzeżenie.
python3 .claude/tests/test_model_check.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
CHECK = ROOT / ".tf" / "factory" / "model_check.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"


def call(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(project / ".tf" / "factory" / "model_check.py"), *args], cwd=project,
                          capture_output=True, text=True, timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def project(base: Path, name: str, override: str | None = None) -> Path:
    """Kopia silnika fabryki (bez reszty instalacji) i opcjonalne nadpisanie konfiguracji projektu."""
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__"))
    if override is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(override, encoding="utf-8")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not CHECK.is_file():
        print(f"✗ brak {CHECK}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "clean")
        r = call(p, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        checked = data.get("checked") or ""
        r2 = call(p, "--today", checked) if checked else r
        check(r.returncode == 0 and data.get("errors") == [] and len(checked) == 10
              and {"fable", "opus", "sonnet", "haiku"} <= set(data.get("current") or {})
              and r2.returncode == 0 and "⚠" not in r2.stdout and "✓" in r2.stdout,
              f"MC-1: konfiguracja i silnik fabryki bez nieznanych modeli, z ceną dla każdego bieżącego: "
              f"{r.returncode} {r.stdout[:600]} {r2.stdout}")
        check(all(v.startswith("claude-") for v in (data.get("current") or {}).values())
              and not set((data.get("current") or {}).values()) & set(data.get("legacy") or []),
              f"MC-2: bieżące i starsze identyfikatory są rozłączne: {data.get('current')} {data.get('legacy')}")

        p = project(base, "unknown", "tiers:\n  deep: {model: claude-opus-4-1, effort: high}\n")
        r = call(p)
        check(r.returncode == 1 and "claude-opus-4-1" in r.stdout and ".tf/config/config.yaml" in r.stdout
              and "claude-api" in r.stdout,
              f"MC-3: nieznany identyfikator w konfiguracji projektu → błąd ze wskazaniem pliku i źródła: {r.returncode} {r.stdout}")

        p = project(base, "alias", "managed_agents:\n  models: {fable: claude-fable-5-1}\n")
        r = call(p)
        check(r.returncode == 1 and "claude-fable-5-1" in r.stdout and "fable" in r.stdout and "older" in r.stdout,
              f"MC-4: alias wskazujący starszy model → błąd: {r.returncode} {r.stdout}")

        p = project(base, "pinned", "tiers:\n  deep: {model: claude-fable-5-1, effort: high}\n")
        r = call(p)
        check(r.returncode == 0 and "✗" not in r.stdout,
              f"MC-5: celowo przypięty starszy, ale dozwolony model nie jest błędem: {r.returncode} {r.stdout}")

        p = project(base, "old")
        r = call(p, "--today", "2099-01-01")
        check(r.returncode == 0 and "⚠" in r.stdout and "90" in r.stdout and "models_checked" in r.stdout,
              f"MC-6: stara data sprawdzenia to ostrzeżenie, nie błąd: {r.returncode} {r.stdout}")

        p = project(base, "code")
        (p / ".tf" / "factory" / "extra_tool.py").write_text('MODEL = "claude-sonnet-3-9"\n', encoding="utf-8")
        r = call(p)
        check(r.returncode == 1 and "claude-sonnet-3-9" in r.stdout and "extra_tool.py" in r.stdout,
              f"MC-7: identyfikator w kodzie silnika też jest sprawdzany: {r.returncode} {r.stdout}")

        p = project(base, "broken", "tiers: [nie: słownik\n")
        r = call(p)
        check(r.returncode in (0, 1) and "Traceback" not in r.stdout + r.stderr,
              f"MC-8: nieczytelna konfiguracja projektu nie kończy się śladem wyjątku: {r.returncode} {r.stdout} {r.stderr[-300:]}")

    # tf doctor pokazuje wynik sprawdzenia modeli (informacja; nie zmienia kodu wyjścia)
    r = subprocess.run([sys.executable, str(CTF), "doctor"], cwd=ROOT, capture_output=True, text=True, timeout=300,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check("models:" in r.stdout.lower() and "Traceback" not in r.stderr,
          f"MC-9: tf doctor pokazuje sprawdzenie nazw modeli: {r.stdout[-600:]} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów nazw modeli")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
