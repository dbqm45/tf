#!/usr/bin/env python3
"""
Team cost profile — one switch between price and quality.

  python3 .tf/factory/profile.py                 # the active profile, tier models and session settings
  python3 .tf/factory/profile.py economy       # switch (also: balanced, quality)
  python3 .tf/factory/profile.py quality --dry-run
  python3 .tf/factory/profile.py economy --team-only   # without changes in .claude/settings.local.json

With a list of approved models (`models_approved`, see model_check.py) a profile that would use a model outside the
list is refused (exit code 1, nothing saved).

A profile (.tf/config/config.yaml → profiles) does two things:
1. overrides the model and effort of the tiers (fast/std/deep), so after a rebuild all agents and personas get
   new models — roles still point to a tier, not a model;
2. sets the session in `.claude/settings.local.json` (a personal file, outside git): effortLevel, autoCompactWindow
   and advisorModel (the advisor: a stronger model that Claude itself calls on hard decisions).

The choice is saved in `.claude/factory-profile.json`. Keys set by the previous profile are removed only if
they still hold the value the profile wrote — your own settings are not touched.
The change takes effect from a new session (`/clear` or restarting `claude`); changing the model mid-session clears the cache.
"""
from __future__ import annotations

import json
import subprocess
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = ROOT / ".claude" / "factory-profile.json"
LOCAL_SETTINGS = ROOT / ".claude" / "settings.local.json"
MANAGED = ("effortLevel", "autoCompactWindow", "advisorModel", "model")



def _tf_config(root: Path) -> dict:
    """Factory configuration: the engine default with project overrides (.tf/config/config.yaml) — packs.load_config."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_cfg", root / ".tf" / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_config(root)

def load_cfg() -> dict:
    try:
        import yaml
    except ImportError:  # bundled copy of PyYAML (.tf/factory/_vendor)
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


def approved_violations(name: str, session: bool) -> list[str]:
    """Models of the profile `name` outside the approved list (`models_approved`, model_check.py); empty without a list."""
    path = Path(__file__).resolve().parent / "model_check.py"
    if not path.is_file():
        return []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_model_check", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.profile_violations(ROOT, name, session=session)
    except Exception as e:  # noqa: BLE001 — a failed check does not take profile switching away
        print(f"⚠ models_approved could not be checked ({str(e).splitlines()[0][:120] if str(e) else type(e).__name__}) — "
              "run: python3 .tf/factory/model_check.py")
        return []


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
    blocked = approved_violations(name, session=not tiers_only)
    if blocked:
        print(f"✗ Profile „{name}” uses a model outside the approved list (models_approved) — nothing was changed:")
        for b in blocked:
            print(f"  • {b}")
        return 1

    state = read_json(PROFILE_FILE)
    prev_set: dict = state.get("settings") or {}
    want: dict = {} if tiers_only else dict(profiles[name].get("settings") or {})
    local = read_json(LOCAL_SETTINGS)
    new_local = dict(local)
    changes = []
    for k, v in prev_set.items():                      # cleaning up after the previous profile
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
