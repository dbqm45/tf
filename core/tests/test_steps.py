#!/usr/bin/env python3
"""Testy przydziału modelu i effortu do kroków pętli /tf (`steps` w konfiguracji fabryki, .tf/factory/build.py):
domyślne wartości dają dzisiejsze modele, nadpisanie zmienia wykonawcę, tabela w skillu zgadza się z konfiguracją.
python3 .claude/tests/test_steps.py"""
import copy
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
BUILD = ROOT / ".tf" / "factory" / "build.py"
SKILL = ROOT / ".claude" / "skills" / "tf" / "SKILL.md"
# wartości sprzed kroku E5 (profil domyślny): wykonawca → model
TODAY = {"scout": "haiku", "researcher": "haiku", "quick-fixer": "haiku", "tf": "sonnet", "scope-reviewer": "sonnet",
         "architect": "opus", "security-reviewer": "opus"}


def load_build():
    spec = importlib.util.spec_from_file_location("tf_build_steps", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    build = load_build()
    cfg = build.load_config()
    steps = cfg.get("steps") or {}
    check(len(steps) == 7 and all({"label", "who", "tier"} <= set(s) for s in steps.values()),
          f"K-1: konfiguracja ma 7 kroków z opisem, wykonawcą i tierem: {sorted(steps)}")
    got = {s["who"]: cfg["tiers"][cfg["shared_agents"][s["who"]]["tier"]]["model"] for s in steps.values()
           if s.get("who") in cfg["shared_agents"]}
    check(got == TODAY or cfg.get("_profile") != cfg.get("default_profile"),
          f"K-2: domyślne `steps` dają dzisiejsze modele wykonawców: {got}")
    generated = {}
    for name in TODAY:
        f = next(iter((ROOT / ".claude" / "agents" / "_generated").rglob(f"{name}.md")), None)
        text = f.read_text(encoding="utf-8") if f else ""
        generated[name] = next((ln.split(":", 1)[1].strip() for ln in text.splitlines() if ln.startswith("model:")), None)
    check(generated == TODAY or cfg.get("_profile") != cfg.get("default_profile"),
          f"K-3: wygenerowani agenci mają dzisiejsze modele: {generated}")

    # nadpisanie tieru kroku zmienia tier (a więc model) jego wykonawcy
    base = build.packs_mod.compose(ROOT, build.packs_mod.load_config(ROOT))
    over = copy.deepcopy(base)
    key = next(k for k, s in over["steps"].items() if s["who"] == "scope-reviewer")
    over["steps"][key]["tier"] = "deep"
    build.apply_steps(over)
    check(over["shared_agents"]["scope-reviewer"]["tier"] == "deep" and over["shared_agents"]["scout"]["tier"] == "fast",
          f"K-4: nadpisanie tieru kroku zmienia tier wykonawcy: {over['shared_agents']['scope-reviewer']['tier']}")

    # sprawdzenia konfiguracji kroków
    bad = copy.deepcopy(base)
    bad["steps"]["nowy"] = {"label": "coś", "who": "nie-ma-takiego", "tier": "std"}
    check(any("nie-ma-takiego" in e for e in build.steps_errors(bad)), "K-5: nieznany wykonawca kroku → błąd")
    bad = copy.deepcopy(base)
    bad["steps"][key]["tier"] = "turbo"
    check(any("turbo" in e for e in build.steps_errors(bad)), "K-6: nieznany tier kroku → błąd")
    bad = copy.deepcopy(base)
    bad["steps"]["drugi"] = {"label": "inny krok", "who": "scout", "tier": "deep"}
    check(any("scout" in e for e in build.steps_errors(bad)), "K-7: ten sam wykonawca z dwoma tierami → błąd")
    check(build.steps_errors(base) == [], f"K-8: konfiguracja domyślna bez błędów: {build.steps_errors(base)}")

    # tabela „Kto co robi” w skillu zgadza się z konfiguracją; rozjazd to błąd
    text = SKILL.read_text(encoding="utf-8")
    check(build.steps_table_errors(base, text) == [], f"K-9: tabela w skillu zgodna z `steps`: {build.steps_table_errors(base, text)}")
    row = next(ln for ln in text.splitlines() if "`scope-reviewer`" in ln and ln.startswith("|") and "std" in ln)
    check(build.steps_table_errors(base, text.replace(row, row.replace("| std |", "| deep |"))) != [],
          "K-10: inny tier w tabeli niż w konfiguracji → błąd")
    check(build.steps_table_errors(base, text.replace(row + "\n", "")) != [], "K-11: brak wiersza kroku w tabeli → błąd")

    # podgląd dla człowieka
    r = subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "tf.py"), "config", "show", "steps"], cwd=ROOT,
                       capture_output=True, text=True, timeout=120, env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    check(r.returncode == 0 and all(a in r.stdout for a in TODAY) and "sonnet" in r.stdout and "effort" in r.stdout.lower()
          and "przegląd zakresu kawałka" in r.stdout,
          f"K-12: tf config show steps drukuje tabelę kroków z modelem i effortem: {r.returncode} {r.stdout[:400]}{r.stderr[:200]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów przydziału kroków")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
