#!/usr/bin/env python3
"""The five configuration layers together (docs/todo.md, "Team and person preference layers", the tests point):
engine ← company (org_defaults) ← team (team_defaults) ← project ← person. One project with all five layers:
- CL-1 the order of the layers and the value of the lowest layer that sets a key;
- CL-2 the company's and the team's ceiling: autonomy operations only tighten, a person cannot loosen them;
- CL-3 task.allowed_modes is an intersection; a person's default mode outside it is refused with a warning;
- CL-4 a style preset changes only the person's defaults — a value the person gives explicitly wins over the preset;
- CL-5 `tf config show` names the source of each value;
- CL-6 the person's file never goes into the repository (it is in the installer's ignored paths, also in team mode).
python3 .claude/tests/test_config_layers.py"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(base: Path) -> Path:
    p = base / "proj"
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    shutil.copytree(ROOT / ".claude" / "hooks", p / ".claude" / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / ".claude" / "factory-manifest.json", p / ".claude" / "factory-manifest.json")
    write(p / ".tf" / "factory" / "packs" / "pack-acme" / "pack.yaml",
          "id: pack-acme\nversion: 1.0.0\ntitle: ACME\norg_defaults:\n  config:\n"
          "    work: {budget_usd: 9}\n    default_profile: balanced\n"
          "    task: {allowed_modes: [plan, normal]}\n"
          "    autonomy: {operations: {git_push: deny}}\n")
    write(p / ".tf" / "factory" / "packs" / "pack-acme-web" / "pack.yaml",
          "id: pack-acme-web\nversion: 1.0.0\ntitle: ACME Web\nrequires: {packs: [pack-acme]}\nteam_defaults:\n  config:\n"
          "    work: {budget_usd: 7}\n    autonomy: {operations: {git_push: confirm}}\n")
    write(p / ".tf" / "config" / "config.yaml", "work:\n  budget_usd: 5\n")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base)
        prefs = base / "home" / "preferences.yaml"
        os.environ["TF_PREFERENCES"] = str(prefs)
        write(prefs, "style: conversation\ntask: {default_mode: normal}\nautonomy: {operations: {git_push: full}}\n")
        packs = load(p / ".tf" / "factory" / "packs.py", "tf_packs_cl")

        layers = packs.config_layers(p)
        labels = [label for label, _ in layers]
        kinds = ["engine" if "factory/config.yaml" in label else "company" if "org_defaults" in label
                 else "team" if "team_defaults" in label else "project" if label.startswith(".tf/config/")
                 else "person" if "(person)" in label else label for label in labels]
        check(kinds == ["engine", "company", "team", "project", "person"],
              f"CL-1: five layers in order engine → company → team → project → person: {labels}")
        cfg = packs.load_config(p)
        check((cfg.get("work") or {}).get("budget_usd") == 5 and cfg.get("default_profile") == "balanced",
              f"CL-1b: the lowest layer that sets a key wins (project budget 5), the others stay (company profile): "
              f"{cfg.get('work')} {cfg.get('default_profile')}")

        guard = load(p / ".claude" / "hooks" / "guard_bash.py", "tf_guard_cl")
        levels, warns = guard.load_policy(p)
        check(levels.get("git_push") == "deny" and any("git_push" in w for w in warns),
              f"CL-2: the company's deny is a ceiling — the team's confirm and the person's full do not loosen it: "
              f"{levels.get('git_push')} {warns}")

        check(cfg["task"]["allowed_modes"] == ["plan", "normal"],
              f"CL-3: allowed modes = the intersection of the layers: {cfg['task'].get('allowed_modes')}")
        write(prefs, "task: {default_mode: auto}\n")
        person, pwarns, _ = packs.person_layer(p, {"task": {"allowed_modes": ["plan", "normal"]}})
        check("default_mode" not in (person.get("task") or {}) and any("allowed_modes" in w for w in pwarns),
              f"CL-3b: a person's mode outside the allowed ones is refused with a warning: {person} {pwarns}")

        styles = (packs.load_yaml(p / ".tf" / "factory" / "config.yaml").get("styles") or {})
        name = next((n for n, v in styles.items() if ((v or {}).get("task") or {}).get("default_mode")), None)
        check(name is not None, f"CL-4 setup: a style with a default mode in the engine configuration: {list(styles)}")
        if name:
            preset_mode = styles[name]["task"]["default_mode"]
            other = next(m for m in ("plan", "normal") if m != preset_mode)
            write(prefs, f"style: {name}\n")
            person, _, _ = packs.person_layer(p, {"styles": styles})
            check((person.get("task") or {}).get("default_mode") == preset_mode and person.get("style") == name,
                  f"CL-4: the style preset gives the person's default ({name} → {preset_mode}): {person}")
            write(prefs, f"style: {name}\ntask: {{default_mode: {other}}}\n")
            person, _, _ = packs.person_layer(p, {"styles": styles})
            check((person.get("task") or {}).get("default_mode") == other,
                  f"CL-4b: a value the person gives explicitly wins over the preset: {person}")

        r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "tf.py"), "config", "show"], cwd=p,
                           capture_output=True, text=True, timeout=120,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        src = {ln.split()[0]: ln.split()[1] for ln in r.stdout.splitlines() if ln and not ln.startswith(("#", "⚠"))
               and len(ln.split()) > 1}
        check(r.returncode == 0 and src.get("work") == "project" and src.get("default_profile") == "organisation"
              and src.get("task") == "person",
              f"CL-5: tf config show names the source of each key (project, organisation, person): {src} {r.stderr[-300:]}")

    install = ROOT / ".tf" / "factory" / "install.py"
    if install.is_file():
        inst = load(install, "tf_install_cl")
        private = inst.ignored_paths()
        check(".tf/" in private or ".tf/config/me.yaml" in private,
              f"CL-6: a private install keeps the person's file out of git: {private}")
        src = install.read_text(encoding="utf-8")
        check('".tf/config/me.yaml"' in src, "CL-6b: team mode lists .tf/config/me.yaml among the ignored paths")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} configuration layer tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
