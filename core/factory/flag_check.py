#!/usr/bin/env python3
"""
Kontrola flagi funkcji zadania (krok D osi przebiegu): stan flagi poza środowiskiem testowym zmienia tylko człowiek.

  tf flag check <KEY> [--base <gałąź>] [--json]

Flagę zadania zapisuje `tf task flag <KEY> set <klucz> [--remove-by RRRR-MM-DD]`, jej brak —
`tf task flag <KEY> none --reason "bez flagi, bo …"`, a zgodę człowieka na inne środowisko —
`tf task flag <KEY> allow <środowisko> --by human:<id>`.

Skąd skrypt wie, jak w projekcie działają flagi: z karty operacyjnej `.tf/config/operations.json` (zakłada ją
`tf onboard`): {"flags": {"file": "config/flags.json", "envs": ["test", "prod"], "test_env": "test"}}.
Obsługiwany jest plik JSON (a YAML, gdy dostępny jest PyYAML) w układzie `środowisko → flaga → stan` albo
`flaga → środowisko → stan`; stan to wartość logiczna albo obiekt z polem `enabled`. Porównanie: plik w bazie (git)
wobec pliku roboczego.

Reguła FLAG-001: flaga zadania włączona na środowisku innym niż testowe, której nie było włączonej w bazie i dla
której zadanie nie ma zapisanej zgody człowieka. Z tym błędem `tf task stage <KEY> pr` (i dalsze) kończy się odmową.

Gdy karty nie ma, nie wskazuje pliku, plik ma inny format albo flagami steruje inny mechanizm (zmienne środowiska,
usługa), skrypt mówi wprost „sprawdź ręcznie” i kończy kodem 0 — nie udaje kontroli, której nie umie zrobić.

Wyłącznik: `feature_flags.auto` w konfiguracji (`.tf/config/config.yaml`, domyślnie `true`). Z `auto: false` flagi
dodaje człowiek sam — zadanie bez flagi przechodzi bez błędu, a flaga zapisana w zadaniu jest sprawdzana jak zwykle.

Kod wyjścia: 0 — zgodnie z regułą (albo kontroli nie dało się wykonać); 1 — FLAG-001 albo zadanie ze specyfikacją
bez flagi i bez powodu; 2 — błąd wywołania. Tylko biblioteka standardowa (PyYAML opcjonalnie).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")

CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
BASES = ("main", "origin/main", "master", "origin/master")


def load_task(root: Path, key: str) -> dict | None:
    try:
        task = json.loads((root / CHANGES / key / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return task if isinstance(task, dict) else None


def card(root: Path) -> dict:
    try:
        data = json.loads((root / CARD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    flags = data.get("flags") if isinstance(data, dict) else None
    return flags if isinstance(flags, dict) else {}


def auto_flags(root: Path) -> bool:
    """`feature_flags.auto` z konfiguracji: domyślna silnika (config.yaml obok skryptu) z nadpisaniem projektu
    (.tf/config/config.yaml). Gdy konfiguracji nie da się odczytać — włączone, jak domyślnie."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_cfg", Path(__file__).resolve().with_name("packs.py"))
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        cfg = packs.load_yaml(Path(__file__).resolve().with_name("config.yaml"))
        own = root / ".tf" / "config" / "config.yaml"
        if own.is_file():
            cfg = packs.deep_merge(cfg, packs.load_yaml(own))
        return (cfg.get("feature_flags") or {}).get("auto", True) is not False
    except Exception:  # noqa: BLE001 — brak konfiguracji to ustawienie domyślne, nie awaria
        return True


def parse(text: str, name: str):
    """Treść pliku flag jako słownik; None, gdy formatu nie da się odczytać."""
    try:
        if name.lower().endswith((".yaml", ".yml")):
            try:
                import yaml
            except ImportError:
                vendor = Path(__file__).resolve().parent / "_vendor"
                if not vendor.is_dir():
                    return None
                sys.path.insert(0, str(vendor))
                import yaml
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception:  # noqa: BLE001 — nieczytelny plik to „sprawdź ręcznie”, nie awaria
        return None
    return data if isinstance(data, dict) else None


def on(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
        return value["enabled"]
    return None


def states(data: dict | None, flag: str, envs: list[str]) -> dict[str, bool]:
    """Stan flagi na środowiskach z karty, w obu obsługiwanych układach pliku."""
    out: dict[str, bool] = {}
    if not data:
        return out
    for env in envs:
        by_env = data.get(env) if isinstance(data.get(env), dict) else {}
        by_flag = data.get(flag) if isinstance(data.get(flag), dict) else {}
        value = on(by_env.get(flag)) if flag in by_env else on(by_flag.get(env))
        if value is not None:
            out[env] = value
    return out


def git_show(root: Path, base: str | None, rel: str) -> str | None:
    """Plik w bazie porównania; None, gdy nie ma repozytorium, bazy albo pliku w bazie."""
    for ref in ([base] if base else BASES):
        try:
            r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=root, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if r.returncode == 0:
            return r.stdout
    return None


def check(root: Path, key: str, base: str | None = None) -> dict:
    """Wynik kontroli: `checked` (czy dało się ją wykonać), `errors`, `note` (dlaczego nie albo co sprawdzono)."""
    task = load_task(root, key) or {}
    flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
    has_spec = (root / CHANGES / key / "spec.md").is_file()
    auto = auto_flags(root)
    result = _check(root, key, base, flag, has_spec, auto)
    result["auto"] = auto
    return result


def _check(root: Path, key: str, base: str | None, flag: dict | None, has_spec: bool, auto: bool) -> dict:
    if flag is None:
        if not auto:
            return {"checked": False, "flag": None, "errors": [],
                    "note": "automatyczne flagi są wyłączone (feature_flags.auto: false) — flagę dodajesz samodzielnie; "
                            "fabryka jej nie zakłada i nie wymaga"}
        if has_spec:
            return {"checked": True, "flag": None, "errors": [{
                "rule": "FLAG-000", "env": None,
                "message": f"zadanie nie ma flagi ani powodu jej braku — tf task flag {key} set <klucz> albo "
                           f"tf task flag {key} none --reason \"bez flagi, bo …\""}], "note": ""}
        return {"checked": False, "flag": None, "errors": [], "note": "zadanie bez specyfikacji nie wymaga flagi"}
    if flag.get("none"):
        return {"checked": True, "flag": None, "errors": [], "note": f"bez flagi: {flag['none']}"}
    name = flag.get("key")
    cfg = card(root)
    rel, envs, test_env = cfg.get("file"), cfg.get("envs") or [], cfg.get("test_env")
    manual = (f"flaga {name}: stanu na środowiskach nie da się sprawdzić skryptem — sprawdź ręcznie, że poza "
              "środowiskiem testowym jest wyłączona. ")
    if not rel or not envs or not test_env:
        return {"checked": False, "flag": name, "errors": [],
                "note": manual + f"Uzupełnij kartę {CARD.as_posix()} (plik flag, środowiska, środowisko testowe)."}
    try:
        now = parse((root / rel).read_text(encoding="utf-8", errors="replace"), rel)
    except OSError:
        now = None
    if now is None:
        return {"checked": False, "flag": name, "errors": [],
                "note": manual + f"Pliku {rel} nie ma albo ma format, którego skrypt nie czyta."}
    before_text = git_show(root, base, rel)
    before = states(parse(before_text, rel) if before_text else None, name, envs)
    current = states(now, name, envs)
    allowed = flag.get("allowed") or {}
    errors = []
    for env in envs:
        if env != test_env and current.get(env) is True and before.get(env) is not True and env not in allowed:
            errors.append({"rule": "FLAG-001", "env": env,
                           "message": f"flaga {name} włączona na środowisku „{env}” bez decyzji człowieka — wyłącz ją tam "
                                      f"albo zapisz zgodę: tf task flag {key} allow {env} --by human:<id>"})
    summary = ", ".join(f"{env}: {'włączona' if current.get(env) else 'wyłączona'}" for env in envs)
    return {"checked": True, "flag": name, "errors": errors, "note": f"flaga {name} w {rel} — {summary}"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf flag check", description="Kontrola flagi funkcji zadania.")
    ap.add_argument("key")
    ap.add_argument("--base", default=None)
    ap.add_argument("--json", action="store_true")
    args = [a for a in argv[1:] if a != "check"] if argv[1:2] == ["check"] else argv[1:]
    try:
        a = ap.parse_args(args)
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        print(f"✗ klucz „{a.key}” nie pasuje do wzorca (np. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    if load_task(root, a.key) is None:
        print(f"✗ nie ma zadania {a.key} — załóż je: tf task start {a.key} --title \"…\"")
        return 2
    result = check(root, a.key, a.base)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 1 if result["errors"] else 0
    if result["note"]:
        print(("✓ " if result["checked"] and not result["errors"] else "⚠ " if not result["checked"] else "") + result["note"])
    for e in result["errors"]:
        print(f"✗ {e['rule']}  {e['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
