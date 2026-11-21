#!/usr/bin/env python3
"""Test of the permission coverage (`.claude/tests/test_settings_coverage.py`, PRB-32) in an installed project outside the
factory tree: checks the installed `.claude/settings*.json` against the installed `tf` and `pdi-decisions`
skills, and without them skips the check with a clear message (instead of looking for `core/settings.json`).
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
    return subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(proj), "--yes", "--layout", "default",
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
        # C-1/C-2: the core loop and the pdi mode, private settings (settings.local.json) — checks the installed layout
        proj = Path(t) / "both"
        r = install(proj, "mode-pdi")
        check(r.returncode == 0, f"C-0: install of mode-pdi: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "allow (" in r.stdout and "✓" in r.stdout and "decision_record.py" not in r.stdout,
              f"C-1: the installed layout (core loop + pdi) passes: {r.stdout[-800:]} {r.stderr[-300:]}")

        # C-2: a rule removed from the installed settings → the test goes red (checks the installation, not the source)
        set_p = proj / ".claude" / "settings.local.json"
        data = json.loads(set_p.read_text(encoding="utf-8"))
        data["permissions"]["allow"] = [a for a in data["permissions"]["allow"] if "decision_record.py" not in a
                                        and "git switch" not in a]
        set_p.write_text(json.dumps(data), encoding="utf-8")
        r = coverage(proj)
        check(r.returncode == 1 and "decision_record.py check" in r.stdout and "git switch main" in r.stdout,
              f"C-2: a missing rule in the installed settings detected: {r.stdout[-800:]}")

        # C-3: team mode (settings.json), the core alone — without pdi-decisions the pdi command is skipped
        proj = Path(t) / "shared"
        r = install(proj, "none", "--shared")
        check(r.returncode == 0, f"C-0: install without overlays --shared: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "decision_record.py" not in r.stdout and "allow (" in r.stdout and "✓" in r.stdout,
              f"C-3: the core alone (team mode) passes without the pdi commands: {r.stdout[-800:]} {r.stderr[-300:]}")

        # C-4: the core alone, private settings — the /tf-task loop is in the core, so the check runs (not skipped)
        proj = Path(t) / "none"
        r = install(proj, "none")
        check(r.returncode == 0, f"C-0: install without overlays: {r.stdout[-600:]} {r.stderr[-300:]}")
        r = coverage(proj)
        check(r.returncode == 0 and "allow (" in r.stdout and "✓" in r.stdout,
              f"C-4: the core alone — the loop commands covered, not skipped: {r.stdout[-800:]} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} test_settings_coverage in an installed project")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
