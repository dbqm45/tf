#!/usr/bin/env python3
"""T6: lista zatwierdzonych modeli (`approved_models`) — silnik models_policy.py, build.py check, profile.py i hook
model_guard.

python3 tests/test_models_policy.py

Organizacja wpisuje w konfiguracji modele, których wolno używać (alias albo pełny identyfikator, opcjonalnie z terminem
`until`). Bez listy fabryka działa jak dotąd. Z listą: model tieru i ustawienia sesji aktywnego profilu spoza listy to
błąd `build.py check`, inne profile i `inherit` to ostrzeżenia, `profile.py` nie przełącza na profil z modelem spoza
listy, a hook `model_guard` odrzuca delegację z parametrem `model` spoza listy.
Plan: docs/plans/2026-11-11-program-ai-luki-w-fabryce.md (repozytorium fabryki), krok 1.
"""
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "build.py").is_file())
ENGINE = ROOT / ".tf" / "factory"
HOOK = ROOT / ".claude" / "hooks" / "model_guard.py"
TODAY = dt.date(2026, 11, 11)


def load():
    spec = importlib.util.spec_from_file_location("tf_models_policy_test", ENGINE / "models_policy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cfg(models=None, tiers=None, profiles=None, managed=None, **extra) -> dict:
    c = {"tiers": tiers or {"fast": {"model": "haiku"}, "std": {"model": "sonnet"}, "deep": {"model": "opus"}},
         "default_profile": "zrownowazony",
         "profiles": profiles if profiles is not None else {
             "oszczedny": {"tiers": {"deep": {"model": "sonnet"}}, "settings": {"effortLevel": "low"}},
             "zrownowazony": {"tiers": {}, "settings": {}},
             "jakosc": {"tiers": {"std": {"effort": "high"}}, "settings": {"advisorModel": "opus"}}}}
    if models is not None:
        c["approved_models"] = {"models": models}
    if managed is not None:
        c["managed_agents"] = {"models": managed}
    c.update(extra)
    return c


def run_py(script: Path, *args: str, cwd: Path, env: dict | None = None, stdin: str | None = None):
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, input=stdin, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300, env={**os.environ, **(env or {})})


def hook_decision(project: Path, tool_input: dict) -> str:
    p = run_py(HOOK, cwd=project, env={"CLAUDE_PROJECT_DIR": str(project)},
               stdin=json.dumps({"tool_name": "Agent", "tool_input": tool_input}))
    if p.returncode != 0:
        return f"exit {p.returncode}: {p.stderr[-200:]}"
    if not p.stdout.strip():
        return "none"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def hook_project(base: Path, name: str, config: str | None) -> Path:
    """Minimalny projekt dla hooka: silnik (bez nakładek) i opcjonalna konfiguracja projektu."""
    p = base / name
    shutil.copytree(ENGINE, p / ".tf" / "factory", ignore=shutil.ignore_patterns("packs", "__pycache__", "analyzers"))
    if config is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(config, encoding="utf-8")
    return p


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    mp = load()
    all_four = {m: {"provider": "anthropic"} for m in ("haiku", "sonnet", "opus", "fable")}
    no_opus = {"haiku": {"provider": "anthropic", "regions": ["eu"]}, "sonnet": {}}

    # MP-1: bez listy (brak klucza, pusty klucz, puste models) — żadnych uwag
    for c in (cfg(), cfg(approved_models={}), cfg(models={})):
        check(mp.check(c, today=TODAY) == ([], []), f"MP-1: bez listy brak błędów i ostrzeżeń: {mp.check(c, today=TODAY)}")
    check(mp.check(cfg(models=all_four), today=TODAY) == ([], []),
          f"MP-1b: wszystkie modele na liście: {mp.check(cfg(models=all_four), today=TODAY)}")

    # MP-2: tier aktywnego profilu spoza listy → błąd z nazwą tieru i modelu
    errors, warnings = mp.check(cfg(models=no_opus), today=TODAY)
    check(len(errors) == 1 and "tiers.deep" in errors[0] and "'opus'" in errors[0] and "approved_models" in errors[0],
          f"MP-2: tier deep z opus spoza listy → jeden błąd: {errors}")
    check("haiku" in errors[0] and "sonnet" in errors[0], f"MP-2b: błąd wymienia zatwierdzone modele: {errors}")

    # MP-3: aktywny profil nadpisuje tier — liczy się model po nałożeniu; inne profile tylko ostrzegają
    errors, warnings = mp.check(cfg(models=no_opus), profile="oszczedny", today=TODAY)
    check(errors == [], f"MP-3: profil oszczedny (deep → sonnet) bez błędów: {errors}")
    check(any("profiles.zrownowazony" in w and "opus" in w for w in warnings)
          and any("profiles.jakosc" in w and "opus" in w for w in warnings),
          f"MP-3b: pozostałe profile z opus → ostrzeżenia: {warnings}")
    prof = {"a": {"tiers": {"std": {"model": "claude-opus-5-5"}}, "settings": {}}, "b": {"tiers": {}, "settings": {}}}
    errors, _ = mp.check(cfg(models=all_four, profiles=prof, default_profile="a"), profile="a", today=TODAY)
    check(len(errors) == 1 and "tiers.std" in errors[0] and "claude-opus-5-5" in errors[0],
          f"MP-3c: alias na liście nie zatwierdza pełnego identyfikatora: {errors}")
    errors, _ = mp.check(cfg(models={**all_four, "claude-opus-5-5": {}}, profiles=prof, default_profile="a"),
                         profile="a", today=TODAY)
    check(errors == [], f"MP-3d: identyfikator na liście zatwierdza identyfikator: {errors}")

    # MP-4: ustawienia sesji aktywnego profilu (advisorModel, model)
    errors, _ = mp.check(cfg(models=no_opus, tiers={"std": {"model": "sonnet"}}), profile="jakosc", today=TODAY)
    check(len(errors) == 1 and "advisorModel" in errors[0] and "jakosc" in errors[0],
          f"MP-4: advisorModel aktywnego profilu spoza listy → błąd: {errors}")
    prof = {"p": {"tiers": {}, "settings": {"model": "fable"}}}
    errors, _ = mp.check(cfg(models=no_opus, tiers={"std": {"model": "sonnet"}}, profiles=prof, default_profile="p"),
                         today=TODAY)
    check(len(errors) == 1 and "settings.model" in errors[0] and "fable" in errors[0],
          f"MP-4b: model sesji profilu spoza listy → błąd: {errors}")

    # MP-5: termin until
    tiers = {"std": {"model": "sonnet"}}
    one = {"zrownowazony": {"tiers": {}, "settings": {}}}
    errors, _ = mp.check(cfg(models={"sonnet": {"until": "2026-11-10"}}, tiers=tiers, profiles=one), today=TODAY)
    check(len(errors) == 1 and "tiers.std" in errors[0] and "2026-11-10" in errors[0],
          f"MP-5: zatwierdzenie po terminie → model niezatwierdzony, błąd z datą: {errors}")
    errors, _ = mp.check(cfg(models={"sonnet": {"until": "2026-11-11"}}, tiers=tiers, profiles=one), today=TODAY)
    check(errors == [], f"MP-5b: termin dziś jeszcze obowiązuje: {errors}")
    errors, _ = mp.check(cfg(models={"sonnet": {"until": "czerwiec"}}, tiers=tiers, profiles=one), today=TODAY)
    check(any("until" in e and "RRRR-MM-DD" in e for e in errors), f"MP-5c: zły format daty → błąd konfiguracji: {errors}")
    errors, _ = mp.check(cfg(models={"sonnet": {"until": dt.date(2027, 1, 1)}}, tiers=tiers, profiles=one), today=TODAY)
    check(errors == [], f"MP-5d: data YAML bez cudzysłowu też działa: {errors}")

    # MP-6: inherit — model sesji poza kontrolą listy
    errors, warnings = mp.check(cfg(models=no_opus, tiers={"std": {"model": "inherit"}}, profiles=one), today=TODAY)
    check(errors == [] and any("inherit" in w and "tiers.std" in w for w in warnings),
          f"MP-6: inherit → ostrzeżenie, nie błąd: {errors} {warnings}")

    # MP-7: target managed-agents — liczy się identyfikator z mapy, chyba że zatwierdzony jest alias
    managed = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
    two = {"fast": {"model": "haiku"}, "std": {"model": "sonnet"}}
    c = cfg(models={"haiku": {}, "claude-sonnet-5-5": {}}, tiers=two, profiles=one, managed=managed)
    errors, _ = mp.check(c, targets=["claude", "managed-agents"], today=TODAY)
    check(len(errors) == 1 and "tiers.std" in errors[0] and "'sonnet'" in errors[0],
          f"MP-7: target claude wymaga aliasu na liście (sam identyfikator nie wystarcza): {errors}")
    errors, _ = mp.check(c, targets=["managed-agents"], today=TODAY)
    check(errors == [], f"MP-7b: tylko managed-agents — alias haiku zatwierdzony, sonnet przez identyfikator: {errors}")
    c = cfg(models={"haiku": {}, "claude-sonnet-5-0": {}}, tiers=two, profiles=one, managed=managed)
    errors, _ = mp.check(c, targets=["managed-agents"], today=TODAY)
    check(len(errors) == 1 and "claude-sonnet-5-5" in errors[0] and "managed" in errors[0],
          f"MP-7c: identyfikator z mapy managed spoza listy → błąd: {errors}")

    # MP-8: zły kształt konfiguracji → błąd, nie wyjątek
    for bad, what in (({"models": ["sonnet"]}, "lista zamiast słownika"), ({"models": {"sonnet": "tak"}}, "wpis nie jest słownikiem"),
                      ("sonnet", "napis zamiast słownika")):
        try:
            errors, _ = mp.check(cfg(approved_models=bad, tiers=tiers, profiles=one), today=TODAY)
        except Exception as e:  # noqa: BLE001 — test wymaga braku wyjątku
            errors = [f"WYJĄTEK {type(e).__name__}: {e}"]
        check(len(errors) >= 1 and all("approved_models" in e for e in errors) and not any("WYJĄTEK" in e for e in errors),
              f"MP-8: {what} → błąd konfiguracji: {errors}")
    errors, _ = mp.check(cfg(models={"sonnet": None}, tiers=tiers, profiles=one), today=TODAY)
    check(errors == [], f"MP-8b: wpis bez opisu (`sonnet:`) jest poprawny: {errors}")

    # MP-9: lista użyć (dla człowieka i dla bramki modeli)
    uses = mp.usage(cfg(models=no_opus), profile="oszczedny")
    active = {(u["where"], u["model"]) for u in uses if u["active"]}
    check(("tiers.fast", "haiku") in active and ("tiers.deep", "sonnet") in active,
          f"MP-9: użycia aktywnego profilu po nałożeniu nadpisań: {sorted(active)}")
    check(any(u["where"] == "profiles.jakosc.settings.advisorModel" and u["model"] == "opus" and not u["active"]
              for u in uses), f"MP-9b: użycia nieaktywnych profili oznaczone active=False: {uses}")

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        # MG: hook model_guard (PreToolUse Agent|Task)
        plain = hook_project(t, "plain", None)
        limited = hook_project(t, "limited", "approved_models:\n  models:\n    haiku: {provider: anthropic}\n    sonnet: {}\n")
        broken = hook_project(t, "broken", "approved_models: [to nie jest słownik\n")
        check(HOOK.is_file(), "MG-0: hook .claude/hooks/model_guard.py jest zainstalowany")
        if HOOK.is_file():
            for proj, ti, want, why in (
                    (plain, {"model": "opus", "prompt": "x"}, "none", "MG-1: bez listy hook nie decyduje"),
                    (limited, {"model": "sonnet", "prompt": "x"}, "none", "MG-2: model z listy przechodzi"),
                    (limited, {"model": "opus", "prompt": "x"}, "deny", "MG-3: model spoza listy → deny"),
                    (limited, {"prompt": "x"}, "none", "MG-4: delegacja bez parametru model przechodzi"),
                    (broken, {"model": "opus", "prompt": "x"}, "none", "MG-5: uszkodzona konfiguracja nie blokuje"),
                    (limited, "nie słownik", "none", "MG-6: dane spoza formatu nie wywołują awarii")):
                got = hook_decision(proj, ti)
                check(got == want, f"{why}: {got}")
            p = run_py(HOOK, cwd=limited, env={"CLAUDE_PROJECT_DIR": str(limited)},
                       stdin=json.dumps({"tool_name": "Agent", "tool_input": {"model": "opus"}}))
            reason = (json.loads(p.stdout)["hookSpecificOutput"]["permissionDecisionReason"] if p.stdout.strip() else "")
            check("haiku" in reason and "sonnet" in reason and "approved_models" in reason,
                  f"MG-3b: powód odmowy wymienia zatwierdzone modele i klucz konfiguracji: {reason}")

        # MP-9c: CLI --json w projekcie
        p = run_py(limited / ".tf" / "factory" / "models_policy.py", "--json", cwd=limited)
        try:
            data = json.loads(p.stdout)
        except json.JSONDecodeError:
            data = {}
        check(p.returncode == 1 and sorted(data.get("approved", {})) == ["haiku", "sonnet"]
              and any(u["where"] == "tiers.deep" for u in data.get("usage", [])) and data.get("errors"),
              f"MP-9c: CLI --json: lista, użycia, błędy i kod 1 przy modelu spoza listy: rc={p.returncode} {p.stdout[:300]} {p.stderr[-200:]}")
        p = run_py(plain / ".tf" / "factory" / "models_policy.py", cwd=plain)
        check(p.returncode == 0 and "approved_models" in p.stdout,
              f"MP-9d: CLI bez listy: kod 0 i informacja, że lista nie jest ustawiona: rc={p.returncode} {p.stdout[:200]}")

        # MP-10/11: build.py check i profile.py w kopii tego projektu
        proj = t / "proj"
        shutil.copytree(ROOT, proj, ignore=shutil.ignore_patterns("__pycache__", "logs", ".git", "*.zip", ".work"))
        own = proj / ".tf" / "config" / "config.yaml"
        base = own.read_text(encoding="utf-8") if own.is_file() else ""
        build = proj / ".tf" / "factory" / "build.py"
        rc0 = run_py(build, "check", cwd=proj).returncode

        def with_list(models: str) -> None:
            own.parent.mkdir(parents=True, exist_ok=True)
            own.write_text(base.rstrip("\n") + ("\n" if base.strip() else "") + f"approved_models:\n  models: {models}\n",
                           encoding="utf-8")

        with_list("{haiku: {}, sonnet: {}, opus: {}, fable: {}}")
        p = run_py(build, "check", cwd=proj)
        check(p.returncode == rc0 and "approved_models" not in p.stdout,
              f"MP-10: pełna lista nie zmienia wyniku build.py check (rc {rc0}): rc={p.returncode} {p.stdout[-300:]}")
        with_list("{haiku: {}, sonnet: {}}")
        p = run_py(build, "check", cwd=proj)
        check(p.returncode == 1 and "approved_models" in p.stdout and "tiers.deep" in p.stdout,
              f"MP-10b: lista bez opus → build.py check z błędem tieru deep: rc={p.returncode} {p.stdout[-400:]}")

        profile_file = proj / ".claude" / "factory-profile.json"
        before = profile_file.read_text(encoding="utf-8") if profile_file.exists() else None
        p = run_py(proj / ".tf" / "factory" / "profile.py", "jakosc", cwd=proj)
        after = profile_file.read_text(encoding="utf-8") if profile_file.exists() else None
        check(p.returncode == 1 and "approved_models" in p.stdout and "opus" in p.stdout and before == after,
              f"MP-11: profile.py jakosc przy liście bez opus → kod 1, profil bez zmian: rc={p.returncode} {p.stdout[-300:]}")
        p = run_py(proj / ".tf" / "factory" / "profile.py", "oszczedny", "--dry-run", cwd=proj)
        check(p.returncode == 0, f"MP-11b: profil bez modeli spoza listy przechodzi (--dry-run): rc={p.returncode} {p.stdout[-300:]}")

    print(f"test_models_policy: {total - len(fails)}/{total} OK")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
