#!/usr/bin/env python3
"""CI speed-ups of `tools/workspace.py check` (docs/RELEASING.md, "CI"): the shards of the test suite (`--shard i/n`)
together run exactly the tests of one full run, without overlap; the selection by changed files (`--changed-from`)
picks the related tests and falls back to the full suite when unsure; the workflows wire both up, and the release
runs after main's full CI instead of repeating it. python3 tests/test_workspace_ci.py"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
WF = ROOT / ".github" / "workflows"


def load():
    spec = importlib.util.spec_from_file_location("tf_workspace_ci", ROOT / "tools" / "workspace.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source_test_names() -> list[str]:
    roots = [ROOT / "core" / "tests", *(p / "tests" for r in ("packs", "modes") for p in sorted((ROOT / r).glob("*")))]
    return sorted({t.name for r in roots for t in r.glob("test_*.py")})


def filler(n: int) -> dict[str, str]:
    """Unrelated tests, so that a small selection stays under the full-suite share."""
    return {f"test_filler_{i:02d}.py": "import unittest  # nothing related\n" for i in range(n)}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    ws = load()

    # --- shards ---------------------------------------------------------------------------------------------------
    names = source_test_names()
    check(len(names) > 50, f"W-0: the factory's tests are found: {len(names)}")
    durations = ws.load_durations()
    check(len(durations) > 50, f"W-1: tools/test-durations.json holds the measured times: {len(durations)}")
    for dur in (durations, {}, {names[0]: 500.0}):
        for n in (1, 2, 3, 4, 5):
            parts = ws.shards(names, n, dur)
            flat = [x for p in parts for x in p]
            check(len(parts) == n and sorted(flat) == names and len(flat) == len(set(flat)),
                  f"W-2: {n} shards ({'durations' if dur else 'by name'}) are disjoint and cover all tests")
            check(parts == ws.shards(list(reversed(names)), n, dur), f"W-3: {n} shards are deterministic")
    parts = ws.shards(names, 3, durations)
    loads = [sum(durations.get(x, 1.0) for x in p) for p in parts]
    check(max(loads) <= 1.5 * min(loads) + 30, f"W-4: the duration-balanced shards are balanced: {loads}")
    check(ws.parse_shard("2/3") == (2, 3) and ws.parse_shard(None) == (1, 1), "W-5: --shard i/n is parsed")
    for bad in ("0/3", "4/3", "x"):
        try:
            ws.parse_shard(bad)
            check(False, f"W-5: --shard {bad} is refused")
        except SystemExit:
            pass

    # the real command: the shards of a workspace list exactly the tests of the full list
    def listed(*args: str) -> list[str]:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "workspace.py"), "check", "--packs", "none", "--list",
                            "--out", str(ROOT / ".work" / "ci-shard-test"), *args],
                           capture_output=True, text=True, timeout=300)
        check(r.returncode == 0, f"W-6: check --list {args}: {r.stdout[-500:]}{r.stderr[-500:]}")
        return [x.strip() for x in r.stdout.splitlines() if x.startswith("    test_")]

    full = listed()
    sharded = [x for i in (1, 2, 3) for x in listed("--shard", f"{i}/3")]
    check(full and sorted(sharded) == sorted(full) and len(sharded) == len(set(sharded)),
          f"W-6: --shard 1/3..3/3 together = the full run ({len(sharded)} vs {len(full)})")

    # --- selection by changed files -------------------------------------------------------------------------------
    tests = {
        **filler(20),
        "test_hooks.py": 'HOOK = ROOT / ".claude" / "hooks" / "guard_bash.py"\n',
        "test_tdd.py": 'spec_from_file_location("tdd_guard", HOOKS / "tdd_guard.py")\n',
        "test_semver.py": 'SKILL = "core-semver"\n',
        "test_dev_tools.py": "", "test_skill_evals.py": "", "test_skill_gate.py": "", "test_skill_audit.py": "",
        "test_skill_hint_stack.py": "", "test_es_board.py": 'import es_board\n',
        "test_kb.py": 'from kb import search\n',
    }
    modules = {"guard_bash": "import json\n", "tdd_guard": "", "es_board": "",
               "kb_lib": "", "kb": "from kb_lib import index\n", "packs_helper": ""}
    sel = lambda changed, packs=("pack-it",), infra=(): ws.select_tests(changed, tests, set(packs), modules, set(infra))

    picked, why = sel(["core/hooks/guard_bash.py"])
    check(picked == {"test_hooks.py"}, f"W-10: a hook change selects its tests: {picked} {why}")
    picked, why = sel(["core/hooks/tdd_guard.py"])
    check(picked == {"test_tdd.py"}, f"W-10: a hook loaded by path selects its tests: {picked} {why}")
    picked, why = sel(["core/skills/core-semver/SKILL.md"])
    gate = {"test_dev_tools.py", "test_skill_evals.py", "test_skill_gate.py", "test_skill_audit.py", "test_skill_hint_stack.py"}
    check(picked == gate | {"test_semver.py"}, f"W-11: a skill change selects the skill-gate and hint tests: {picked} {why}")
    picked, why = sel(["core/tests/skill_evals/core-semver.json"])
    check(picked == gate | {"test_semver.py"}, f"W-11: a skill's scenarios select like the skill: {picked} {why}")
    picked, why = sel(["packs/pack-it/skills/ddd-event-storming/scripts/es_board.py"])
    check(picked is not None and "test_es_board.py" in picked and gate <= picked,
          f"W-11: a skill script selects its tests and the gate tests: {picked} {why}")
    for f in ("core/factory/build.py", "core/factory/install.py", "core/factory/packs.py", "core/factory/config.yaml",
              "core/factory/update.py", "core/settings.json", "tools/workspace.py", ".github/workflows/release.yml"):
        picked, why = sel([f, "core/tests/test_kb.py"])
        check(picked is None and f in why[-1], f"W-12: {f} falls back to the full suite, with the reason: {picked} {why}")
    picked, why = sel(["core/tests/test_kb.py"])
    check(picked == {"test_kb.py"}, f"W-13: a test-only change selects just that test: {picked} {why}")
    picked, why = sel(["core/tests/test_gone.py"])
    check(picked == set(), f"W-13: a deleted test selects nothing: {picked} {why}")
    for f in ("weird/new_tool.cfg", "Makefile", "core/factory/unknown_module.py", "core/guide/no-one-reads-this.md"):
        picked, why = sel([f])
        check(picked is None and f in why[-1], f"W-14: {f} (no rule or no test) falls back to the full suite: {why}")
    picked, why = sel(["core/hooks/guard_bash.py", "Makefile"])
    check(picked is None, "W-14: one unknown file among known ones → the full suite")
    picked, why = sel(["core/factory/kb_lib.py"])
    check(picked == {"test_kb.py"}, f"W-15: a module selects the tests of the modules that import it: {picked} {why}")
    picked, why = sel(["core/factory/packs_helper.py"], infra=("packs_helper",))
    check(picked is None and "shared infrastructure" in why[-1], f"W-16: a module the installer loads → full: {why}")
    picked, why = sel(["modes/mode-pdi/hooks/x.py", "modes/mode-pdi/pack.yaml"], packs=("pack-it",))
    check(picked == set(), f"W-17: a change to an overlay outside this pack set selects nothing here: {picked} {why}")
    picked, why = sel(["packs/pack-it/pack.yaml"])
    check(picked is None, f"W-17: the manifest of an installed overlay → full: {why}")
    picked, why = sel(["docs/RELEASING.md", "tests/test_release.py", "scripts/check_commit_message.py"])
    check(picked == set(), f"W-18: files outside the project (run by the repo job) select no workspace test: {picked} {why}")
    many = {f"core/tests/test_filler_{i:02d}.py" for i in range(15)}
    picked, why = sel(sorted(many))
    check(picked is None and "over" in why[-1], f"W-19: a selection over 40% of the tests → the full suite: {why}")
    picked, why = ws.select_tests(["core/tests/test_kb.py"], tests, set(), modules)
    check(picked == {"test_kb.py"}, "W-20: works without the infrastructure set")
    infra = ws.loaded_by_infrastructure()
    check({"install", "build", "update", "packs", "migrations", "skill_audit"} <= infra,
          f"W-21: the modules the installer and the build load are infrastructure: {sorted(infra)}")

    # --- the workflows --------------------------------------------------------------------------------------------
    fc = (WF / "factory-checks.yml").read_text(encoding="utf-8")
    shards = re.findall(r"\{packs: all, shard: (\d+)/(\d+)\}", fc)
    n = {int(b) for _, b in shards}
    check(len(n) == 1 and sorted(int(a) for a, _ in shards) == list(range(1, max(n) + 1)) and max(n) > 1,
          f"W-30: the `all` set runs as shards 1/n..n/n: {shards}")
    check(re.search(r"exclude:\s*\n\s*- packs: all", fc) and re.search(r"^\s*packs: \[.*\ball\]$", fc, re.M),
          "W-31: the matrix keeps `all` in its list (new-pack inserts before it) and replaces it with the shards")
    check('--shard "${{ matrix.shard' in fc and "--changed-from" in fc and "github.event.pull_request.base.sha" in fc
          and "github.event_name == 'pull_request'" in fc, "W-32: the selection is used on pull requests only")
    rel = (WF / "release.yml").read_text(encoding="utf-8")
    check(re.search(r"workflow_run:\s*\n\s*workflows: \[factory-checks\]\s*\n\s*types: \[completed\]\s*\n\s*branches: \[main\]",
                    rel), "W-33: the release starts after factory-checks on main")
    check("github.event.workflow_run.conclusion == 'success'" in rel and "github.event.workflow_run.event == 'push'" in rel
          and "ref: ${{ github.event.workflow_run.head_sha" in rel, "W-34: only after success on push, exactly that commit")
    check("  push:" not in rel.split("jobs:")[0], "W-35: no own push trigger (it would race CI)")
    full_runs = [l for l in rel.splitlines() if l.strip().startswith("python3 tools/workspace.py check --packs all")]
    check(len(full_runs) == 2 and any("--no-tests" in l for l in full_runs),
          f"W-36: the full suite only on a manual run, the cheap checks otherwise: {full_runs}")
    check("cancel-in-progress: false" in rel and "HEAD:refs/heads/main" in rel and "skip=true" in rel,
          "W-37: the queue, the push of the release commit and the moved-on main logic stay")

    print(f"{total - len(fails)}/{total} OK")
    for f in fails:
        print("✗", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
