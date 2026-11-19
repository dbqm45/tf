#!/usr/bin/env python3
"""Model names in the factory configuration (step H20): whether the configuration and engine refer to models that do not exist.

  python3 .tf/factory/model_check.py            # human-readable result (also in `tf doctor`)
  python3 .tf/factory/model_check.py --json     # result for scripts
  python3 .tf/factory/model_check.py --today YYYY-MM-DD   # reference date (tests)

The single source of truth is three keys of `.tf/factory/config.yaml`: `models_current` (alias → current identifier),
`models_legacy` (older identifiers, still allowed when someone pins them deliberately) and `models_checked` (the date
of the check, source: the `claude-api` skill). Checked are:
- every `claude-…` identifier in the core configuration, in project overrides (`.tf/config/config.yaml`)
  and in the engine code (`.tf/factory/*.py`) — an unknown one is an error (a typo or a model that no longer exists);
- aliases in `managed_agents.models` — they must point to a model from `models_current`, not an older one;
- the price list `prices_usd_per_mtok` — every current alias has a price (missing is a warning: the cost report will show only tokens);
- the `models_checked` date — older than 90 days is a warning (not an error: CI does not turn red from the passage of time).

Exit code: 0 — no errors (warnings possible), 1 — errors, 2 — invocation error. Standard library only
(PyYAML optional, like the rest of the engine).
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

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8
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
    """(key path, text) for every string and key in the configuration structure."""
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
    except Exception as e:  # noqa: BLE001 — the core configuration is unreadable: there is nothing to check
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
