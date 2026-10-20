#!/usr/bin/env python3
"""
Profil kosztów zespołu — jeden przełącznik między ceną a jakością.

  python3 factory/profile.py                 # aktywny profil, modele tierów i ustawienia sesji
  python3 factory/profile.py oszczedny       # przełącz (też: zrownowazony, jakosc)
  python3 factory/profile.py jakosc --dry-run
  python3 factory/profile.py oszczedny --tylko-zespol   # bez zmian w .claude/settings.local.json

Profil (factory/config.yaml → profiles) robi dwie rzeczy:
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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_FILE = ROOT / ".claude" / "factory-profile.json"
LOCAL_SETTINGS = ROOT / ".claude" / "settings.local.json"
MANAGED = ("effortLevel", "autoCompactWindow", "advisorModel", "model")


def load_cfg() -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("✗ Brak pyyaml: pip install pyyaml (Windows: py -m pip install pyyaml)")
    return yaml.safe_load((ROOT / "factory" / "config.yaml").read_text(encoding="utf-8")) or {}


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except json.JSONDecodeError:
        sys.exit(f"✗ {p.relative_to(ROOT)} nie jest poprawnym JSON-em — popraw go ręcznie i spróbuj ponownie")


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
    print(f"Aktywny profil: {active}" + ("" if PROFILE_FILE.exists() else " (domyślny)"))
    for name, prof in (cfg.get("profiles") or {}).items():
        mark = "→" if name == active else " "
        print(f" {mark} {name:<13} {prof.get('opis', '')}")
    print("\nTiery w aktywnym profilu:")
    for tier, t in effective_tiers(cfg, active).items():
        print(f"  {tier:<5} {t.get('model', '?'):<7} effort {t.get('effort') or 'domyślny modelu'}")
    print("\nSesja (.claude/settings.local.json): " +
          (", ".join(f"{k}={local[k]}" for k in MANAGED if k in local) or "brak ustawień profilu"))
    return 0


def main(argv: list[str]) -> int:
    cfg = load_cfg()
    args = [a for a in argv[1:] if not a.startswith("--")]
    dry, tiers_only = "--dry-run" in argv, "--tylko-zespol" in argv
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if not args:
        return show(cfg)
    name = args[0]
    profiles = cfg.get("profiles") or {}
    if name not in profiles:
        print(f"✗ Nie ma profilu „{name}”. Dostępne: {', '.join(profiles)}")
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
            changes.append(f"  − {k} (ustawił poprzedni profil)")
    for k, v in want.items():
        if new_local.get(k) != v:
            if k in local and local.get(k) != prev_set.get(k):
                changes.append(f"  ~ {k}: {local[k]} → {v} (nadpisuję Twoją wartość)")
            else:
                changes.append(f"  + {k} = {v}")
            new_local[k] = v

    tiers = effective_tiers(cfg, name)
    print(f"Profil: {name} — {profiles[name].get('opis', '')}")
    print("Tiery: " + ", ".join(f"{t} → {v.get('model')}{'/' + v['effort'] if v.get('effort') else ''}"
                                for t, v in tiers.items()))
    print("Sesja (.claude/settings.local.json):" + ("\n" + "\n".join(changes) if changes else " bez zmian"))
    if dry:
        print("(--dry-run: nic nie zapisano)")
        return 0

    if new_local != local:
        LOCAL_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_SETTINGS.write_text(json.dumps(new_local, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps({"profile": name, "settings": want}, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "factory" / "build.py")], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print("⚠ build.py zgłosił problemy:\n" + r.stdout[-1500:] + r.stderr[-500:])
        return 1
    print("✓ Agenci przebudowani. Zmiana działa od nowej sesji (`/clear` albo ponowne `claude`).")
    if want.get("advisorModel"):
        print("  Doradca (advisor) działa tylko przez API Anthropic (nie Bedrock/Vertex/Foundry) i zużywa dodatkowe "
              "tokeny przy każdej konsultacji; `/advisor off` wyłącza go w bieżącej sesji.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
