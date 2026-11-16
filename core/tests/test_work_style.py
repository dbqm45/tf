#!/usr/bin/env python3
"""Warstwa osoby i styl pracy (docs/todo.md, „Warstwy zespołu i preferencji osoby”, punkt 1).

Preferencje osoby (`~/.tf/preferences.yaml`, w testach `TF_PREFERENCES`, oraz `.tf/config/me.yaml` w projekcie) są
ostatnią warstwą konfiguracji. Osoba ustawia tylko styl i przełączniki sposobu pracy; polityki autonomii nie
rozluźnia, a domyślny tryb zadania musi mieścić się w `task.allowed_modes` wyższych warstw. Styl (`autonomous`,
`step-by-step`, `conversation`) to gotowe wartości tych przełączników. Wszystko liczą skrypty, bez modelu.
python3 .claude/tests/test_work_style.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
FACTORY = ROOT / ".tf" / "factory"
TF = FACTORY / "tf.py"
TASK = FACTORY / "task_state.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
RUN_STATE, REPORT = SCRIPTS / "run_state.py", SCRIPTS / "run_report.py"
GUARD = ROOT / ".claude" / "hooks" / "guard_bash.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci kartą, wtedy opłata "
        "wynosi 45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
PLAN = ("# Plan\n\n- [ ] K1 — płatność kartą · kryteria: AC-1 · pliki: pay.py\n"
        "- [ ] K2 — paragon · kryteria: AC-1 · pliki: receipt.py\n")


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
    """Projekt z silnikiem fabryki (kopia `.tf/factory` przestrzeni roboczej) i opcjonalną konfiguracją projektu."""
    p = base / name
    (p / ".tf").mkdir(parents=True)
    os.symlink(FACTORY, p / ".tf" / "factory")
    (p / ".claude").mkdir()
    (p / ".claude" / "factory-manifest.json").write_text("{}", encoding="utf-8")   # tf: „fabryka zainstalowana”
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

        # WS-1..4: warstwa osoby, styl, filtr kluczy, me.yaml
        p = project(base, "a")
        check(not any("osoba" in lbl for lbl, _ in packs.config_layers(p)),
              "WS-1: bez pliku preferencji nie ma warstwy osoby")
        prefs.write_text("style: autonomous\nloop:\n  blocked_slices: false\nwork:\n  budget_usd: 400\n"
                         "autonomy:\n  operations:\n    publish: deny\n  triage:\n    always_review: []\n",
                         encoding="utf-8")
        layers = packs.config_layers(p)
        lbl, person = layers[-1]
        check("osoba" in lbl, f"WS-1: preferencje to ostatnia warstwa, oznaczona „osoba”: {[l for l, _ in layers]}")
        check(person.get("style") == "autonomous" and (person.get("task") or {}).get("default_mode") == "auto",
              f"WS-2: styl rozwinięty do wartości przełączników: {person}")
        check((person.get("loop") or {}).get("blocked_slices") is False,
              f"WS-3: wartość podana wprost wygrywa z wartością stylu: {person}")
        check("work" not in person and "triage" not in (person.get("autonomy") or {})
              and (person.get("autonomy") or {}).get("operations") == {"publish": "deny"},
              f"WS-2: osoba nie ustawia limitów work ani reguł triage, zaostrza tylko operacje: {person}")
        (p / ".tf" / "config").mkdir()
        (p / ".tf" / "config" / "me.yaml").write_text("style: step-by-step\n", encoding="utf-8")
        cfg = packs.load_config(p)
        check(cfg.get("style") == "step-by-step" and cfg["task"]["default_mode"] == "zwykly"
              and cfg["loop"]["confirm_each_slice"] is True and cfg["loop"]["blocked_slices"] is False,
              f"WS-4: .tf/config/me.yaml nadpisuje preferencje ogólne: {cfg.get('style')} {cfg.get('task')} {cfg.get('loop')}")

        # WS-5: sufit trybów z wyższej warstwy
        q = project(base, "b", "task:\n  allowed_modes: [plan, zwykly]\n")
        prefs.write_text("style: autonomous\n", encoding="utf-8")
        ws = packs.work_style(q)
        check(ws["default_mode"] == "zwykly" and any("allowed_modes" in w for w in ws["warnings"]),
              f"WS-5: tryb Auto spoza task.allowed_modes nie przechodzi z preferencji osoby: {ws}")

        # WS-6: polityka autonomii — osoba zaostrza, nie rozluźnia
        prefs.write_text("autonomy:\n  operations:\n    publish: deny\n    git_push: allow\n", encoding="utf-8")
        guard = load(GUARD, "ws_guard")
        levels, warns = guard.load_policy(p)
        check(levels.get("publish") == "deny" and levels.get("git_push") == "confirm",
              f"WS-6: osoba zaostrza (deny), a „allow” jest ignorowane: {levels} {warns}")

        # WS-7, WS-8: domyślny tryb zadania i sufit przy tf task
        prefs.write_text("style: conversation\n", encoding="utf-8")
        r = run(q, prefs, TASK, "start", "IMP-7", "--title", "Domyślny tryb")
        mode = json.loads((q / CHANGES / "IMP-7" / "task.json").read_text(encoding="utf-8")).get("mode") \
            if r.returncode == 0 else None
        check(mode == "plan", f"WS-7: zadanie bez --mode dostaje domyślny tryb stylu (conversation → plan): {mode} {r.stdout}{r.stderr}")
        r = run(q, prefs, TASK, "mode", "IMP-7", "auto")
        check(r.returncode != 0 and "allowed_modes" in r.stdout + r.stderr,
              f"WS-8: tf task mode auto odrzucone, gdy wyższa warstwa nie dopuszcza Auto: {r.returncode} {r.stdout}{r.stderr}")

        # WS-9: tf style
        prefs.unlink()
        r = run(p, prefs, TF, "style", "step-by-step")
        check(r.returncode == 0 and "style: step-by-step" in prefs.read_text(encoding="utf-8"),
              f"WS-9: tf style zapisuje styl w preferencjach osoby: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style", "conversation", "--here")
        check(r.returncode == 0 and "style: conversation" in (p / ".tf/config/me.yaml").read_text(encoding="utf-8"),
              f"WS-9: tf style --here zapisuje styl tylko dla tego projektu: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style")
        check(r.returncode == 0 and "conversation" in r.stdout and "plan" in r.stdout,
              f"WS-9: tf style bez nazwy pokazuje styl i jego wartości: {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "style", "turbo")
        check(r.returncode == 2 and "autonomous" in r.stdout + r.stderr,
              f"WS-9: nieznany styl → kod 2 z listą stylów: {r.returncode} {r.stdout}{r.stderr}")
        r = run(p, prefs, TF, "config", "show")
        check(any(ln.split()[:2] == ["style", "osoba"] for ln in r.stdout.splitlines()),
              f"WS-10: tf config show podaje źródło „osoba”: {r.stdout}{r.stderr}")

        # WS-11: step-by-step — po kawałku przebieg czeka na zgodę człowieka
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
        run(s, prefs, RUN_STATE, "step", d, "K1", "R1", "test", "run")
        (s / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
        (s / "test_pay.py").write_text("def test_ac1_card_fee():  # AC-1\n    assert True\n", encoding="utf-8")
        run(s, prefs, RUN_STATE, "verify", d, "K1", "--files", "pay.py,test_pay.py", "--command", OK)
        r = run(s, prefs, RUN_STATE, "done", d, "K1", "--message", "feat(pay): card payment")
        check(r.returncode == 0 and "STOP" in r.stdout and "proceed" in r.stdout and "Dalej: K2" not in r.stdout,
              f"WS-11: po kawałku styl step-by-step zatrzymuje przebieg do zgody człowieka: {r.returncode} {r.stdout}{r.stderr}")
        (s / "receipt.py").write_text("R = 1\n", encoding="utf-8")
        r = run(s, prefs, RUN_STATE, "verify", d, "K2", "--files", "receipt.py,test_pay.py", "--command", OK)
        check(r.returncode != 0 and "proceed" in r.stdout + r.stderr,
              f"WS-11: następny kawałek odrzucony przed zgodą: {r.returncode} {r.stdout}{r.stderr}")
        r = run(s, prefs, RUN_STATE, "proceed", d)
        check(r.returncode == 0 and "Dalej: K2" in r.stdout, f"WS-11: proceed zdejmuje wstrzymanie: {r.stdout}{r.stderr}")
        r = run(s, prefs, RUN_STATE, "verify", d, "K2", "--files", "receipt.py,test_pay.py", "--command", OK)
        check(r.returncode == 0, f"WS-11: po zgodzie następny kawałek idzie dalej: {r.returncode} {r.stdout}{r.stderr}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów stylu pracy")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
