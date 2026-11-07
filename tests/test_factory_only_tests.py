#!/usr/bin/env python3
"""Testy fabryki, które mają sens tylko w repozytorium fabryki (evale przebiegu N5: `test_flow_evals.py`,
`flow_evals_runner.py`, `flow_evals/`, `test_export_pdi_runs.py` — importują `scripts/export_pdi_runs.py`
i `modes/mode-pdi/.../phase_result.py` ze źródła fabryki), nie trafiają do projektu (`.claude/tests/`),
aktualizacja usuwa ich kopie z wcześniejszych wersji, a `tools/workspace.py check` dalej je uruchamia (ze źródła).
python3 tests/test_factory_only_tests.py"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
FACTORY_ONLY = (".claude/tests/test_flow_evals.py", ".claude/tests/flow_evals_runner.py",
                ".claude/tests/test_export_pdi_runs.py", ".claude/tests/flow_evals/budget.json",
                ".claude/tests/flow_evals/kappa.py")
MANIFEST = ".claude/factory-manifest.json"


def install(proj: Path, packs: str, *extra: str) -> subprocess.CompletedProcess:
    proj.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=proj, check=False)
    return subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(proj), "--yes",
                           "--packs", packs, *extra], capture_output=True, text=True, timeout=600)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj = Path(t) / "app"
        r = install(proj, "mode-pdi,mode-talos")
        check(r.returncode == 0, f"FO-0: instalacja mode-pdi,mode-talos: {r.stdout[-600:]} {r.stderr[-300:]}")
        present = [rel for rel in FACTORY_ONLY if (proj / rel).exists()]
        check(not present, f"FO-1: testy tylko dla fabryki nie trafiają do projektu: {present}")
        check(not (proj / ".claude" / "tests" / "flow_evals").exists(), "FO-1: brak katalogu .claude/tests/flow_evals/")
        files = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))["files"]
        listed = [rel for rel in files if "flow_evals" in rel or "export_pdi_runs" in rel]
        check(not listed, f"FO-2: manifest nie wymienia testów tylko dla fabryki: {listed}")
        check((proj / ".claude" / "tests" / "run_skill_evals.py").exists(),
              "FO-3: walidator scenariuszy skilli (run_skill_evals.py) dalej instalowany")
        leftovers = [p.name for p in sorted((proj / ".claude" / "tests").glob("test_*.py"))
                     if any(m in p.read_text(encoding="utf-8")
                            for m in ("import export_pdi_runs", "import flow_evals_runner"))]
        check(not leftovers, f"FO-4: zainstalowane testy nie importują modułów ze źródła fabryki: {leftovers}")

        # FO-5: projekt z wersji, która je instalowała (niezmienione kopie w manifeście) → aktualizacja je usuwa
        inst = load("tf_install_fo", ROOT / "core" / "factory" / "install.py")
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        old = {".claude/tests/test_flow_evals.py": ROOT / "core/tests/test_flow_evals.py",
               ".claude/tests/flow_evals/kappa.py": ROOT / "core/tests/flow_evals/kappa.py"}
        for rel, src in old.items():
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_bytes(src.read_bytes())
            man["files"][rel] = inst.sha(src.read_bytes())
        (proj / MANIFEST).write_text(json.dumps(man), encoding="utf-8")
        r = install(proj, "mode-pdi,mode-talos", "--update")
        check(r.returncode == 0, f"FO-5: aktualizacja: {r.stdout[-600:]} {r.stderr[-300:]}")
        still = [rel for rel in old if (proj / rel).exists()]
        check(not still, f"FO-5: aktualizacja usuwa kopie testów tylko dla fabryki z poprzedniej wersji: {still}")

    # FO-6: przestrzeń fabryki uruchamia je ze źródła (core/tests/), więc dalej są sprawdzane w `workspace.py check`
    ws = load("tf_workspace_fo", ROOT / "tools" / "workspace.py")
    tests = ws.factory_only_tests()
    names = sorted(p.name for p in tests)
    check(names == ["test_export_pdi_runs.py", "test_flow_evals.py"],
          f"FO-6: workspace.py check uruchamia testy tylko dla fabryki: {names}")
    check(all(p.is_file() and p.parent == ROOT / "core" / "tests" for p in tests),
          f"FO-6: ze źródła core/tests/: {tests}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testy tylko dla fabryki")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
