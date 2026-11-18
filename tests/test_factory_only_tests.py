#!/usr/bin/env python3
"""Factory tests that make sense only in the factory repository (the N5 flow evals: `test_flow_evals.py`,
`flow_evals_runner.py`, `flow_evals/`, `test_export_pdi_runs.py` — they import `scripts/export_pdi_runs.py`
and `modes/mode-pdi/.../phase_result.py` from the factory source), do not reach the project (`.claude/tests/`),
an update removes their copies from earlier versions, and `tools/workspace.py check` still runs them (from the source).
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
        r = install(proj, "mode-pdi,mode-team")
        check(r.returncode == 0, f"FO-0: install of mode-pdi,mode-team: {r.stdout[-600:]} {r.stderr[-300:]}")
        present = [rel for rel in FACTORY_ONLY if (proj / rel).exists()]
        check(not present, f"FO-1: factory-only tests do not reach the project: {present}")
        check(not (proj / ".claude" / "tests" / "flow_evals").exists(), "FO-1: no .claude/tests/flow_evals/ directory")
        files = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))["files"]
        listed = [rel for rel in files if "flow_evals" in rel or "export_pdi_runs" in rel]
        check(not listed, f"FO-2: the manifest does not list factory-only tests: {listed}")
        check((proj / ".claude" / "tests" / "run_skill_evals.py").exists(),
              "FO-3: the skill scenario validator (run_skill_evals.py) is still installed")
        leftovers = [p.name for p in sorted((proj / ".claude" / "tests").glob("test_*.py"))
                     if any(m in p.read_text(encoding="utf-8")
                            for m in ("import export_pdi_runs", "import flow_evals_runner"))]
        check(not leftovers, f"FO-4: installed tests do not import modules from the factory source: {leftovers}")

        # FO-5: a project from a version that installed them (unchanged copies in the manifest) → the update removes them
        inst = load("tf_install_fo", ROOT / "core" / "factory" / "install.py")
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        old = {".claude/tests/test_flow_evals.py": ROOT / "core/tests/test_flow_evals.py",
               ".claude/tests/flow_evals/kappa.py": ROOT / "core/tests/flow_evals/kappa.py"}
        for rel, src in old.items():
            (proj / rel).parent.mkdir(parents=True, exist_ok=True)
            (proj / rel).write_bytes(src.read_bytes())
            man["files"][rel] = inst.sha(src.read_bytes())
        (proj / MANIFEST).write_text(json.dumps(man), encoding="utf-8")
        r = install(proj, "mode-pdi,mode-team", "--update")
        check(r.returncode == 0, f"FO-5: update: {r.stdout[-600:]} {r.stderr[-300:]}")
        still = [rel for rel in old if (proj / rel).exists()]
        check(not still, f"FO-5: the update removes the factory-only test copies from the previous version: {still}")

    # FO-6: the factory workspace runs them from the source (core/tests/), so they are still checked in `workspace.py check`
    ws = load("tf_workspace_fo", ROOT / "tools" / "workspace.py")
    tests = ws.factory_only_tests()
    names = sorted(p.name for p in tests)
    check(names == ["test_export_pdi_runs.py", "test_flow_evals.py"],
          f"FO-6: workspace.py check runs the factory-only tests: {names}")
    check(all(p.is_file() and p.parent == ROOT / "core" / "tests" for p in tests),
          f"FO-6: from the core/tests/ source: {tests}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} factory-only tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
