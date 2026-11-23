#!/usr/bin/env python3
"""Installer tests: the factory test paths (`tests/` → `.claude/tests/`) are rewritten only where factory tests are meant
(the CI workflow, settings), and not in the content of skills and scenarios, where `tests/` means the project's tests.
python3 tests/test_install_paths.py"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import os
os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        src = Path(t) / "src"
        shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
        major = int((src / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        pack = src / "packs" / "pack-a"
        write(pack / "pack.yaml", f"id: pack-a\nversion: 1.0.0\ntitle: A\ndescription: A test.\n"
                                  f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                                  "facets:\n  - {prefix: aa-, order: 900, name: a, question: \"a\"}\n")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              "---\nname: aa-run\ndescription: Użyj przy A.\nmetadata:\n  catalog: \"Użyj przy A. Nie do niczego.\"\n"
              "  review: 2099-01-01\n---\n# aa-run\nPrzykład: `python3 tests/test_orders.py`\n")
        write(pack / "skills" / "aa-run" / "references" / "examples.md", "```python\n# tests/test_discount.py\n```\n")
        write(pack / "tests" / "skill_evals" / "aa-run.json",
              json.dumps({"skill": "aa-run", "scenarios": [{"id": "x", "expect": "trigger",
                                                             "prompt": "W tests/test_discount.py mam kopie testu."}]}))
        write(pack / "workflows" / "aa-audit.js", "export const meta = {name: 'aa-audit', description: 'A'}\n")
        proj = Path(t) / "proj"
        proj.mkdir()
        r = subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", "--layout", "default",
                            "--shared", "--packs", "pack-a"], capture_output=True, text=True, timeout=300)
        check(r.returncode == 0, f"I-1: install: {r.stdout[-600:]} {r.stderr[-300:]}")
        # T-1…T-5 (step 4c): the engine in .tf/factory/, the project configuration in .tf/config/, nothing in a factory/ directory
        tfd = proj / ".tf"
        check((tfd / "factory" / "build.py").is_file() and (tfd / "factory" / "VERSION").is_file()
              and (tfd / "factory" / "packs" / "pack-a" / "pack.yaml").is_file() and not (proj / "factory").exists(),
              f"T-1: the engine and overlay metadata in .tf/factory/, no factory/ in the root directory: "
              f"{sorted(x.name for x in proj.iterdir())}")
        own_cfg = tfd / "config" / "config.yaml"
        check(own_cfg.is_file() and not any(ln.startswith("tiers:") for ln in own_cfg.read_text(encoding="utf-8").splitlines())
              and all((tfd / "config" / d).is_dir() for d in ("personas", "roles", "traits")),
              f"T-2: .tf/config/ — config.yaml only for overrides and the directories of own personas, roles, traits")
        own_cfg.parent.mkdir(parents=True, exist_ok=True)
        own_cfg.write_text("default_profile: economy\ntiers:\n  fast: {maxTurns: 7}\n", encoding="utf-8")
        r2 = subprocess.run([sys.executable, str(tfd / "factory" / "packs.py"), "--json"], cwd=proj,
                            capture_output=True, text=True, timeout=120)
        try:
            composed = json.loads(r2.stdout)
        except ValueError:
            composed = {}
        cfg = composed.get("config", composed)
        check(cfg.get("default_profile") == "economy" and (cfg.get("tiers") or {}).get("fast", {}).get("maxTurns") == 7
              and (cfg.get("tiers") or {}).get("fast", {}).get("model") and "std" in (cfg.get("tiers") or {}),
              f"T-3: overrides from .tf/config/config.yaml layered over the engine defaults: {r2.stdout[:300]} {r2.stderr[-300:]}")
        caches = sorted(str(x.relative_to(proj)) for x in (tfd / "factory").rglob("__pycache__"))
        check(not caches, f"T-6: the engine leaves no __pycache__ in .tf/factory/ (install, packs.py): {caches}")
        instr = (proj / "CLAUDE.md").read_text(encoding="utf-8") if (proj / "CLAUDE.md").exists() else ""
        check(".tf/factory/build.py" in instr and "python3 factory/" not in instr,
              f"T-4: the project instructions point to .tf/factory/: {instr[-400:]}")
        r3 = subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", "--layout", "default"],
                            capture_output=True, text=True, timeout=300)
        check(r3.returncode == 0 and "economy" in own_cfg.read_text(encoding="utf-8"),
              f"T-5: the update does not touch .tf/config/config.yaml: {r3.stdout[-400:]}")
        skill = proj / ".claude" / "skills" / "aa-run"
        read = lambda p: p.read_text(encoding="utf-8") if p.exists() else ""
        check("python3 tests/test_orders.py" in read(skill / "SKILL.md"),
              f"I-2: SKILL.md without changes to the project test paths: {read(skill / 'SKILL.md')[-120:]}")
        check("# tests/test_discount.py" in read(skill / "references" / "examples.md"),
              f"I-3: examples in references unchanged: {read(skill / 'references' / 'examples.md')}")
        check("W tests/test_discount.py" in read(proj / ".claude" / "tests" / "skill_evals" / "aa-run.json"),
              "I-4: the evaluation scenario unchanged")
        wf = read(proj / ".github" / "workflows" / "team-factory.yml")
        check(".claude/tests/test_hooks.py" in wf and " tests/test_hooks.py" not in wf,
              "I-5: the factory CI workflow runs the tests from .claude/tests/")
        check("\n  workflow_dispatch:" in wf,
              "I-5a: the factory CI workflow can be run manually (workflow_dispatch), e.g. after enabling Actions")
        check("name: 'aa-audit'" in read(proj / ".claude" / "workflows" / "aa-audit.js"),
              "I-7: the overlay workflow in .claude/workflows/ (where Claude Code looks for saved workflows)")
        guide, faq = read(proj / ".tf" / "factory" / "GUIDE.md"), read(proj / ".tf" / "factory" / "FAQ.md")
        check(guide.startswith("# ") and faq.startswith("# ") and "tf " in guide,
              "I-9: the core guide and FAQ in .tf/factory/ (no README in the project root)")
        sett = read(proj / ".claude" / "settings.json")
        check("python3 .claude/tests/test_cleanroom.py" in sett, "I-6: permission for the factory test in .claude/tests/")

        # private mode: the factory workflow ignored by file name (the project's own workflows stay in the repo)
        priv = Path(t) / "priv"
        priv.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=priv, check=True)
        subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(priv), "--yes", "--layout", "default",
                        "--packs", "pack-a"], capture_output=True, text=True, timeout=300)
        exclude = read(priv / ".git" / "info" / "exclude").splitlines()
        check(".claude/workflows/aa-audit.js" in exclude and ".claude/workflows/" not in exclude,
              f"I-8: the factory workflow in .git/info/exclude by name: {[e for e in exclude if 'workflows' in e]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} installer path tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
