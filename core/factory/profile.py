#!/usr/bin/env python3
"""
Profil kosztów zespołu — jeden przełącznik między ceną a jakością.

  python3 .tf/factory/profile.py                 # aktywny profil, modele tierów i ustawienia sesji
  python3 .tf/factory/profile.py economy       # przełącz (też: balanced, quality)
  python3 .tf/factory/profile.py quality --dry-run
  python3 .tf/factory/profile.py economy --team-only   # bez zmian w .claude/settings.local.json

Profil (.tf/config/config.yaml → profiles) robi dwie rzeczy:
1. nadpisuje model i effort tierów (fast/std/deep), więc po przebudowaniu wszyscy agenci i persony dostają
   nowe modele — role dalej wskazują tier, nie model;
2. ustawia sesję w `.claude/settings.local.json` (osobisty plik, poza gitem): effortLevel, autoCompactWindow
   i advisorModel (doradca: mocniejszy model, którego Claude sam wzywa przy trudnych decyzjach).

Wybór zapisuje w `.claude/factory-profile.json`. Klucze ustawione przez poprzedni profil usuwa tylko wtedy, gdy
mają wciąż wartość, którą profil wpisał — Twoich własnych ustawień nie rusza.
Zmiana działa od nowej sesji (`/clear` albo ponowne uruchomienie `claude`); zmiana modelu w trakcie sesji kasuje cache.
"""
from __future__ import annotations

import json
import subprocess
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = ROOT / ".claude" / "factory-profile.json"
LOCAL_SETTINGS = ROOT / ".claude" / "settings.local.json"
MANAGED = ("effortLevel", "autoCompactWindow", "advisorModel", "model")



def _tf_config(root: Path) -> dict:
    """Konfiguracja fabryki: domyślna silnika z nadpisaniami projektu (.tf/config/config.yaml) — packs.load_config."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_cfg", root / ".tf" / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_config(root)

def load_cfg() -> dict:
    try:
        import yaml
    except ImportError:  # dołączona kopia PyYAML (.tf/factory/_vendor)
        sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
        import yaml
    return _tf_config(ROOT) or {}


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:
        sys.exit(f"✗ {p.relative_to(ROOT)} is not valid JSON — fix it by hand and try again")


def effective_tiers(cfg: dict, name: str) -> dict:
    tiers = {k: dict(v) for k, v in (cfg.get("tiers") or {}).items()}
    for tier, over in (((cfg.get("profiles") or {}).get(name) or {}).get("tiers") or {}).items():
        if tier in tiers:
            tiers[tier].update(over or {})
    return tiers


def show(cfg: dict) -> int:
    state = read_json(PROFILE_FILE)
    active = state.get("profile") or cfg.get("default_profile")
    local = read_json(LOCAL_SETTINGS)
    print(f"Active profile: {active}" + ("" if PROFILE_FILE.exists() else " (default)"))
    for name, prof in (cfg.get("profiles") or {}).items():
        mark = "→" if name == active else " "
        print(f" {mark} {name:<13} {prof.get('description', '')}")
    print("\nTiers in the active profile:")
    for tier, t in effective_tiers(cfg, active).items():
        print(f"  {tier:<5} {t.get('model', '?'):<7} effort {t.get('effort') or 'model default'}")
    print("\nSession (.claude/settings.local.json): " +
          (", ".join(f"{k}={local[k]}" for k in MANAGED if k in local) or "no profile settings"))
    return 0


def main(argv: list[str]) -> int:
    cfg = load_cfg()
    args = [a for a in argv[1:] if not a.startswith("--")]
    dry, tiers_only = "--dry-run" in argv, "--team-only" in argv
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if not args:
        return show(cfg)
    name = args[0]
    profiles = cfg.get("profiles") or {}
    if name not in profiles:
        print(f"✗ No profile „{name}”. Available: {', '.join(profiles)}")
        return 2

    state = read_json(PROFILE_FILE)
    prev_set: dict = state.get("settings") or {}
    want: dict = {} if tiers_only else dict(profiles[name].get("settings") or {})
    local = read_json(LOCAL_SETTINGS)
    new_local = dict(local)
    changes = []
    for k, v in prev_set.items():                      # sprzątanie po poprzednim profilu
        if k not in want and new_local.get(k) == v:
            new_local.pop(k)
            changes.append(f"  − {k} (set by the previous profile)")
    for k, v in want.items():
        if new_local.get(k) != v:
            if k in local and local.get(k) != prev_set.get(k):
                changes.append(f"  ~ {k}: {local[k]} → {v} (overwriting your value)")
            else:
                changes.append(f"  + {k} = {v}")
            new_local[k] = v

    tiers = effective_tiers(cfg, name)
    print(f"Profile: {name} — {profiles[name].get('description', '')}")
    print("Tiers: " + ", ".join(f"{t} → {v.get('model')}{'/' + v['effort'] if v.get('effort') else ''}"
                                for t, v in tiers.items()))
    print("Session (.claude/settings.local.json):" + ("\n" + "\n".join(changes) if changes else " no changes"))
    if dry:
        print("(--dry-run: nothing saved)")
        return 0

    if new_local != local:
        LOCAL_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_SETTINGS.write_text(json.dumps(new_local, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps({"profile": name, "settings": want}, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / ".tf" / "factory" / "build.py")], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("⚠ build.py reported problems:\n" + r.stdout[-1500:] + r.stderr[-500:])
        return 1
    print("✓ Agents rebuilt. The change works from a new session (`/clear` or a new `claude` start).")
    if want.get("advisorModel"):
        print("  The advisor works only through the Anthropic API (not Bedrock/Vertex/Foundry) and uses extra "
              "tokens for each consultation; `/advisor off` turns it off in the current session.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
