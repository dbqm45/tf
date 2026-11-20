#!/usr/bin/env python3
"""The person layer and work style (docs/todo.md, "Team and person preference layers", point 1).

A person's preferences (`~/.tf/preferences.yaml`, `TF_PREFERENCES` in the tests, and `.tf/config/me.yaml` in the project) are
the last configuration layer. A person sets only the style and the work-mode switches; they do not
loosen the autonomy policy, and the default task mode must fit within `task.allowed_modes` of the higher layers. A style (`autonomous`,
`step-by-step`, `conversation`) is a ready set of values for those switches. Everything is computed by scripts, without a model.
python3 .claude/tests/test_work_style.py"""
import importlib.util
import json
import shutil
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())


def link_or_copy(src: Path, dst: Path) -> None:
    """A symbolic link, or a copy where the system refuses links (Windows without the developer mode: WinError 1314)."""
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())   # link-ok
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True)
        else:
            shutil.copy2(src, dst)
FACTORY = ROOT / ".tf" / "factory"
TF = FACTORY / "tf.py"
TASK = FACTORY / "task_state.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
RUN_STATE, REPORT = SCRIPTS / "run_state.py", SCRIPTS / "run_report.py"
GUARD = ROOT / ".claude" / "hooks" / "guard_bash.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci kartą, then opłata "
        "wynosi 45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
PLAN = ("# Plan\n\n- [ ] S1 — płatność kartą · criteria: AC-1 · files: pay.py\n"
        "- [ ] S2 — paragon · criteria: AC-1 · files: receipt.py\n")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


def env(project: Path, prefs: Path) -> dict:
    return {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
            "TF_PREFERENCES": str(prefs), "TF_DASHBOARD_OPEN": "0", "GIT_AUTHOR_NAME": "T",
            "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
            "GIT_CONFIG_GLOBAL": os.devnull}


def run(project: Path, prefs: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True,
                          env=env(project, prefs), timeout=120)


def git(project: Path, prefs: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "commit.gpgsign=false", *args], capture_output=True,
                          text=True, env=env(project, prefs), timeout=60)


def project(base: Path, name: str, config: str = "") -> Path:
    """A project with the factory engine (a copy of the workspace's `.tf/factory`) and an optional project configuration."""
    p = base / name
    (p / ".tf").mkdir(parents=True)
    link_or_copy(Path(FACTORY), p / ".tf" / "factory")
    (p / ".claude").mkdir()
    (p / ".claude" / "factory-manifest.json").write_text("{}", encoding="utf-8")   # tf: "factory installed"
    if config:
        (p / ".tf" / "config").mkdir()
        (p / ".tf" / "config" / "config.yaml").write_text(config, encoding="utf-8")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    packs = load(FACTORY / "packs.py", "ws_packs")
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        prefs = base / "home" / "preferences.yaml"
        prefs.parent.mkdir()
        os.environ["TF_PREFERENCES"] = str(prefs)

        # WS-1..4: the person layer, style, key filter, me.yaml
        p = project(base, "a")
        check(not any("person" in lbl for lbl, _ in packs.config_layers(p)),
              "WS-1: without a preferences file there is no person layer")
        prefs.write_text("style: autonomous\nloop:\n  blocked_slices: false\nwork:\n  budget_usd: 400\n"
                         "autonomy:\n  operations:\n    publish: deny\n  triage:\n    always_review: []\n",
                         encoding="utf-8")
        layers = packs.config_layers(p)
        lbl, person = layers[-1]
        check("person" in lbl, f"WS-1: the preferences are the last layer, labelled 'person': {[l for l, _ in layers]}")
        check(person.get("style") == "autonomous" and (person.get("task") or {}).get("default_mode") == "auto",
              f"WS-2: the style expanded into switch values: {person}")
        check((person.get("loop") or {}).get("blocked_slices") is False,
              f"WS-3: an explicitly given value wins over the style's value: {person}")
        check("work" not in person and "triage" not in (person.get("autonomy") or {})
              and (person.get("autonomy") or {}).get("operations") == {"publish": "deny"},
              f"WS-2: a person sets neither the work limits nor the triage rules, only tightens operations: {person}")
        (p / ".tf" / "config").mkdir()
        (p / ".tf" / "config" / "me.yaml").write_text("style: step-by-step\n", encoding="utf-8")
        cfg = packs.load_config(p)
        check(cfg.get("style") == "step-by-step" and cfg["task"]["default_mode"] == "normal"
              and cfg["loop"]["confirm_each_slice"] is True and cfg["loop"]["blocked_slices"] is False,
              f"WS-4: .tf/config/me.yaml overrides the general preferences: {cfg.get('style')} {cfg.get('task')} {cfg.get('loop')}")

        # WS-5: the mode ceiling from a higher layer
        q = project(base, "b", "task:\n  allowed_modes: [plan, normal]\n")
        prefs.write_text("style: autonomous\n", encoding="utf-8")
        ws = packs.work_style(q)
        check(ws["default_mode"] == "normal" and any("allowed_modes" in w for w in ws["warnings"]),
              f"WS-5: Auto mode outside task.allowed_modes does not pass from the person's preferences: {ws}")

        # WS-6: the autonomy policy — a person tightens, does not loosen
        prefs.write_text("autonomy:\n  operations:\n    publish: deny\n    git_push: allow\n", encoding="utf-8")
        guard = load(GUARD, "ws_guard")
        levels, warns = guard.load_policy(p)
        check(levels.get("publish") == "deny" and levels.get("git_push") == "confirm",
              f"WS-6: a person tightens (deny), and 'allow' is ignored: {levels} {warns}")

        # WS-7, WS-8: the default task mode and the ceiling for tf task
        prefs.write_text("style: conversation\n", encoding="utf-8")
        r = run(q, prefs, TASK, "start", "IMP-7", "--title", "Domyślny tryb")
        mode = json.loads((q / CHANGES / "IMP-7" / "task.json").read_text(encoding="utf-8")).get("mode") \
            if r.returncode == 0 else None
        check(mode == "plan", f"WS-7: a task without --mode gets the style's default mode (conversation -> plan): {mode} {r.stdout}{r.stderr}")
        r = run(q, prefs, TASK, "mode", "IMP-7", "auto")
        check(r.returncode != 0 and "allowed_modes" in r.stdout + r.stderr,
              f"WS-8: tf task mode auto rejected when a higher layer does not allow Auto: {r.returncode} {r.stdout}{r.stderr}")

        # WS-9: tf style
        prefs.unlink()
        r = run(p, prefs, TF, "style", "step-by-step")
        check(r.returncode == 0 and "style: step-by-step" in prefs.read_text(encoding="utf-8"),
              f"WS-9: tf style writes the style into the person's preferences: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style", "conversation", "--here")
        check(r.returncode == 0 and "style: conversation" in (p / ".tf/config/me.yaml").read_text(encoding="utf-8"),
              f"WS-9: tf style --here writes the style for this project only: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style")
        check(r.returncode == 0 and "conversation" in r.stdout and "plan" in r.stdout,
              f"WS-9: tf style without a name shows the style and its values: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style", "turbo")
        check(r.returncode == 2 and "autonomous" in r.stdout + r.stderr,
              f"WS-9: an unknown style -> code 2 with the list of styles: {r.returncode} {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "config", "show")
        check(any(ln.split()[:2] == ["style", "person"] for ln in r.stdout.splitlines()),
              f"WS-10: tf config show gives the source 'person': {r.stdout}{r.stderr}")

        # WS-12: the conversation style turns on Claude Code's planning mode in .claude/settings.local.json and gives it back
        local = p / ".claude" / "settings.local.json"
        local.write_text('{"permissions": {"defaultMode": "default", "allow": ["Bash(ls)"]}}', encoding="utf-8")
        (p / ".tf/config/me.yaml").unlink()
        mode_of = lambda: (json.loads(local.read_text(encoding="utf-8")).get("permissions", {}).get("defaultMode")
                           if local.is_file() else None)
        r = run(p, prefs, TF, "style", "conversation")
        check(r.returncode == 0 and mode_of() == "plan"
              and json.loads(local.read_text(encoding="utf-8"))["permissions"]["allow"] == ["Bash(ls)"],
              f"WS-12: conversation -> defaultMode plan, the rest of the settings unchanged: {mode_of()} {r.stdout}{r.stderr}")
        check(not any("claude" in w for w in packs.work_style(p)["warnings"]),
              f"WS-12: the style's Claude Code settings are not a key of the person's configuration: {packs.work_style(p)['warnings']}")
        r = run(p, prefs, TF, "style", "step-by-step")
        check(r.returncode == 0 and mode_of() == "default",
              f"WS-12: changing the style restores the previous permission mode: {mode_of()} {r.stdout}{r.stderr}")
        local.write_text('{"permissions": {"defaultMode": "acceptEdits"}}', encoding="utf-8")
        r = run(p, prefs, TF, "style", "conversation")
        check(r.returncode == 0 and mode_of() == "acceptEdits" and "acceptEdits" in r.stdout,
              f"WS-12: the style does not overwrite a human's own permission mode, it only mentions it: {mode_of()} {r.stdout}{r.stderr}")
        local.unlink()
        r = run(p, prefs, TF, "style")
        check(r.returncode == 0 and mode_of() == "plan",
              f"WS-12: tf style without a name reconciles the permission mode in this project (style from the general preferences): {r.stdout}{r.stderr}")
        run(p, prefs, TF, "style", "autonomous")
        check(not local.is_file() or mode_of() is None,
              f"WS-12: with no earlier value a style change removes the set mode: {local.read_text(encoding='utf-8') if local.is_file() else ''}")

        # WS-11: step-by-step — after a slice the run waits for the human's consent
        prefs.write_text("style: step-by-step\n", encoding="utf-8")
        s = project(base, "s")
        git(s, prefs, "init", "-q", "-b", "main")
        (s / "README.md").write_text("x\n", encoding="utf-8")
        git(s, prefs, "add", "-A")
        git(s, prefs, "commit", "-q", "-m", "chore: init")
        git(s, prefs, "checkout", "-q", "-b", "story/karta")
        run(s, prefs, REPORT, "start", "Płatność kartą", "--key", "IMP-1", "--story", "Jako kierowca chcę zapłacić kartą.")
        d = str(s / ".tf" / "runs" / "IMP-1")
        (s / CHANGES / "IMP-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (s / CHANGES / "IMP-1" / "plan.md").write_text(PLAN, encoding="utf-8")
        run(s, prefs, RUN_STATE, "flag", d, "none", "--reason", "bez flagi, bo zmiana jest za zgodą człowieka w planie")
        run(s, prefs, RUN_STATE, "stage", d, "plan")
        run(s, prefs, RUN_STATE, "approve", d)
        run(s, prefs, RUN_STATE, "step", d, "S1", "R1", "test", "run")
        (s / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
        (s / "test_pay.py").write_text("def test_ac1_card_fee():  # AC-1\n    assert True\n", encoding="utf-8")
        run(s, prefs, RUN_STATE, "verify", d, "S1", "--files", "pay.py,test_pay.py", "--command", OK)
        r = run(s, prefs, RUN_STATE, "done", d, "S1", "--message", "feat(pay): card payment")
        check(r.returncode == 0 and "STOP" in r.stdout and "proceed" in r.stdout and "Next: S2" not in r.stdout,
              f"WS-11: after a slice the step-by-step style stops the run until the human consents: {r.returncode} {r.stdout}{r.stderr}")
        (s / "receipt.py").write_text("R = 1\n", encoding="utf-8")
        r = run(s, prefs, RUN_STATE, "verify", d, "S2", "--files", "receipt.py,test_pay.py", "--command", OK)
        check(r.returncode != 0 and "proceed" in r.stdout + r.stderr,
              f"WS-11: the next slice rejected before consent: {r.returncode} {r.stdout}{r.stderr}")
        r = run(s, prefs, RUN_STATE, "proceed", d)
        check(r.returncode == 0 and "Next: S2" in r.stdout, f"WS-11: proceed lifts the hold: {r.stdout}{r.stderr}")
        r = run(s, prefs, RUN_STATE, "verify", d, "S2", "--files", "receipt.py,test_pay.py", "--command", OK)
        check(r.returncode == 0, f"WS-11: after consent the next slice goes on: {r.returncode} {r.stdout}{r.stderr}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} work style tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
