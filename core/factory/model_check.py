#!/usr/bin/env python3
"""Nazwy modeli w konfiguracji fabryki (krok H20): czy konfiguracja i silnik nie odwołują się do modeli, których nie ma.

  python3 .tf/factory/model_check.py            # wynik dla człowieka (też w `tf doctor`)
  python3 .tf/factory/model_check.py --json     # wynik dla skryptów
  python3 .tf/factory/model_check.py --today RRRR-MM-DD   # data odniesienia (testy)

Jedno źródło prawdy to trzy klucze `.tf/factory/config.yaml`: `models_current` (alias → bieżący identyfikator),
`models_legacy` (starsze identyfikatory, nadal dozwolone, gdy ktoś przypnie je celowo) i `models_checked` (data
sprawdzenia, źródło: skill `claude-api`). Sprawdzane są:
- każdy identyfikator `claude-…` w konfiguracji rdzenia, w nadpisaniach projektu (`.tf/config/config.yaml`)
  i w kodzie silnika (`.tf/factory/*.py`) — nieznany to błąd (literówka albo model, którego już nie ma);
- aliasy w `managed_agents.models` — muszą wskazywać model z `models_current`, nie starszy;
- cennik `prices_usd_per_mtok` — każdy bieżący alias ma cenę (brak to ostrzeżenie: raport kosztów pokaże same tokeny);
- data `models_checked` — starsza niż 90 dni to ostrzeżenie (nie błąd: CI nie zaczerwieni się od upływu czasu).

Kod wyjścia: 0 — bez błędów (ostrzeżenia możliwe), 1 — błędy, 2 — błąd wywołania. Tylko biblioteka standardowa
(PyYAML opcjonalnie, jak reszta silnika).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne też piszą i czytają UTF-8
sys.dont_write_bytecode = True

ENGINE = Path(".tf") / "factory"
OWN = Path(".tf") / "config" / "config.yaml"
ID = re.compile(r"\bclaude-[a-z]+(?:-[a-z0-9]+)*-\d+(?:-\d+)?\b")
MAX_AGE_DAYS = 90
SOURCE = "check in the claude-api skill (table of current models) and fix `models_current` / `models_legacy`"


def packs_module(root: Path):
    spec = importlib.util.spec_from_file_location("tf_packs_models", root / ENGINE / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strings(value, path: str = "") -> list[tuple[str, str]]:
    """(ścieżka klucza, tekst) dla każdego napisu i klucza w strukturze konfiguracji."""
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            out.append((f"{path}{k}", str(k)))
            out += strings(v, f"{path}{k}.")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += strings(v, f"{path}{i}.")
    elif isinstance(value, str):
        out.append((path.rstrip("."), value))
    return out


def check(root: Path, today: date) -> dict:
    errors, warnings = [], []
    mod = packs_module(root)
    try:
        core = mod.load_yaml(root / ENGINE / "config.yaml") or {}
    except Exception as e:  # noqa: BLE001 — konfiguracja rdzenia nieczytelna: nie ma czego sprawdzać
        return {"errors": [f"cannot read {ENGINE / 'config.yaml'}: {e}"], "warnings": [], "current": {},
                "legacy": [], "checked": None, "ids": []}
    own = {}
    if (root / OWN).is_file():
        try:
            own = mod.load_yaml(root / OWN) or {}
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{OWN.as_posix()} is unreadable ({str(e).splitlines()[0][:120]}) — its models were not checked")
        if not isinstance(own, dict):
            own = {}
    cfg = mod.deep_merge(core, own)
    current = cfg.get("models_current") if isinstance(cfg.get("models_current"), dict) else {}
    legacy = [x for x in cfg.get("models_legacy") or [] if isinstance(x, str)]
    known = set(current.values()) | set(legacy)
    seen: dict[str, set[str]] = {}

    def note(where: str, text: str) -> None:
        for mid in ID.findall(text):
            seen.setdefault(mid, set()).add(where)

    for label, data in (((ENGINE / "config.yaml").as_posix(), core), (OWN.as_posix(), own)):
        for key, text in strings(data):
            if not key.startswith(("models_current", "models_legacy")):
                note(f"{label} ({key})", text)
    for f in sorted((root / ENGINE).glob("*.py")):
        if f.name == Path(__file__).name:
            continue
        try:
            note((ENGINE / f.name).as_posix(), f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    for mid, where in sorted(seen.items()):
        if mid not in known:
            errors.append(f"unknown model {mid} in: {', '.join(sorted(where))} — {SOURCE}")
    managed = ((cfg.get("managed_agents") or {}).get("models") or {}) if isinstance(cfg.get("managed_agents"), dict) else {}
    for alias, mid in sorted(managed.items()) if isinstance(managed, dict) else []:
        if alias in current and mid != current[alias] and mid in legacy:
            errors.append(f"alias {alias} in managed_agents.models points to an older model {mid} instead of {current[alias]}")
    prices = cfg.get("prices_usd_per_mtok") if isinstance(cfg.get("prices_usd_per_mtok"), dict) else {}
    for alias, mid in sorted(current.items()):
        if alias not in prices and mid not in prices:
            warnings.append(f"price list prices_usd_per_mtok has no price for {alias} ({mid}) — the cost report will show tokens only")
    checked = str(cfg.get("models_checked") or "")
    try:
        age = (today - date.fromisoformat(checked)).days
    except ValueError:
        age = None
        warnings.append("no models_checked date in the configuration — it is not known when the model names were checked")
    if age is not None and age > MAX_AGE_DAYS:
        warnings.append(f"model names and prices were checked on {checked} (more than {MAX_AGE_DAYS} days ago): models_checked — {SOURCE}")
    return {"errors": errors, "warnings": warnings, "current": current, "legacy": legacy, "checked": checked or None,
            "ids": sorted(seen)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--today", default=None, help="reference date YYYY-MM-DD (default: today)")
    a = ap.parse_args(argv[1:])
    try:
        today = date.fromisoformat(a.today) if a.today else date.today()
    except ValueError:
        print("✗ --today: expected a date YYYY-MM-DD")
        return 2
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (root / ENGINE / "config.yaml").is_file():
        print(f"✗ {ENGINE / 'config.yaml'} does not exist — run in a project directory with the factory")
        return 2
    res = check(root, today)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for e in res["errors"]:
            print(f"✗ models: {e}")
        for w in res["warnings"]:
            print(f"⚠ models: {w}")
        if not res["errors"]:
            print(f"✓ models: {len(res['ids'])} identifiers in the configuration and the engine, all known "
                  f"(checked {res['checked'] or '—'})")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
