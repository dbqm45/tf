#!/usr/bin/env python3
"""
Lista zatwierdzonych modeli (`approved_models` w konfiguracji fabryki): których modeli wolno używać w tym projekcie.

  python3 .tf/factory/models_policy.py              # lista, miejsca użycia modeli, błędy i ostrzeżenia
  python3 .tf/factory/models_policy.py --json       # to samo jako JSON (np. dla bramki modeli organizacji)
  --root <katalog projektu>

Konfiguracja (`.tf/factory/config.yaml`, nadpisanie projektu w `.tf/config/config.yaml`):

  approved_models:
    source: "Polityka AI 2026-11"                   # skąd lista — opcjonalne
    models:
      haiku:  {provider: anthropic, regions: [eu], data: [public, internal], contract: "DPA 2026-03"}
      sonnet: {until: "2027-06-30"}                 # po terminie model przestaje być zatwierdzony

Kluczem jest nazwa użyta w konfiguracji: alias (haiku, sonnet, opus, fable) albo pełny identyfikator `claude-…`.
Dopasowanie jest dokładne: alias zatwierdza alias, identyfikator zatwierdza identyfikator. Pola opisu (provider,
regions, data, contract, note) są dla ludzi i dla bramki modeli; fabryka ich nie interpretuje. Bez `models` nie ma
ograniczeń. Z listą: model tieru po nałożeniu aktywnego profilu i ustawienia sesji aktywnego profilu (model,
advisorModel) spoza listy to błąd `build.py check`; pozostałe profile i `inherit` to ostrzeżenia. Target
`managed-agents` sprawdza identyfikator z `managed_agents.models`, chyba że zatwierdzony jest alias. Parametr `model`
delegacji sprawdza hook `.claude/hooks/model_guard.py`. Modelu sesji wybranego ręcznie (`/model`) fabryka nie
kontroluje. Tylko biblioteka standardowa (konfigurację czyta `.tf/factory/packs.py`).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY = "approved_models"
SESSION_SETTINGS = ("model", "advisorModel")   # ustawienia sesji profilu, które wskazują model
MANAGED_IDS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5",
               "fable": "claude-fable-5-1", "inherit": "claude-opus-5-5"}   # jak w target_managed.py (MODEL_IDS)


def _date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def approved(cfg: dict, today: dt.date | None = None) -> tuple[dict | None, dict, list[str]]:
    """(zatwierdzone, wygasłe, błędy konfiguracji). `zatwierdzone` to None, gdy lista nie jest ustawiona (brak
    ograniczeń); inaczej słownik nazwa → opis. `wygasłe`: nazwa → termin `until`, który minął."""
    today = today or dt.date.today()
    raw = cfg.get(KEY)
    if raw is None or raw == {}:
        return None, {}, []
    if not isinstance(raw, dict):
        return {}, {}, [f"{KEY}: oczekiwany słownik z kluczem `models`, jest {type(raw).__name__}"]
    models = raw.get("models")
    if models is None or models == {}:
        return None, {}, []
    if not isinstance(models, dict):
        return {}, {}, [f"{KEY}.models: oczekiwany słownik nazwa modelu → opis, jest {type(models).__name__}"]
    ok, expired, errors = {}, {}, []
    for name, entry in models.items():
        name = str(name)
        if entry is None:
            entry = {}
        if not isinstance(entry, dict):
            errors.append(f"{KEY}.models.{name}: oczekiwany słownik (np. {{provider: anthropic}}) albo pusty wpis, "
                          f"jest {type(entry).__name__}")
            continue
        until = entry.get("until")
        if until is not None:
            limit = _date(until)
            if limit is None:
                errors.append(f"{KEY}.models.{name}.until: data w formacie RRRR-MM-DD, jest „{until}”")
                continue
            if limit < today:
                expired[name] = limit.isoformat()
                continue
        ok[name] = entry
    return ok, expired, errors


def effective_tiers(cfg: dict, profile: str | None) -> dict:
    tiers = {k: dict(v or {}) for k, v in (cfg.get("tiers") or {}).items()}
    for tier, over in (((cfg.get("profiles") or {}).get(profile) or {}).get("tiers") or {}).items():
        if tier in tiers:
            tiers[tier].update(over or {})
    return tiers


def usage(cfg: dict, profile: str | None = None) -> list[dict]:
    """Miejsca, w których konfiguracja wskazuje model: tiery po nałożeniu każdego profilu i ustawienia sesji profili.
    `active` oznacza aktywny profil (podany albo `default_profile`)."""
    profiles = cfg.get("profiles") or {}
    current = profile if profile in profiles else cfg.get("default_profile")
    out = []
    for name in ([current] if current not in profiles else []) + list(profiles):
        is_active = name == current
        prefix = "" if is_active else f"profiles.{name}."
        for tier, t in effective_tiers(cfg, name).items():
            if t.get("model"):
                out.append({"where": f"{prefix}tiers.{tier}", "model": str(t["model"]), "profile": name, "active": is_active})
        for key in SESSION_SETTINGS:
            value = ((profiles.get(name) or {}).get("settings") or {}).get(key)
            if value:
                out.append({"where": f"profiles.{name}.settings.{key}", "model": str(value), "profile": name,
                            "active": is_active})
    return out


def _listed(ok: dict) -> str:
    return ", ".join(sorted(ok)) or "brak"


def check(cfg: dict, profile: str | None = None, targets=("claude",), today: dt.date | None = None
          ) -> tuple[list[str], list[str]]:
    """Błędy i ostrzeżenia listy zatwierdzonych modeli dla konfiguracji `cfg` (przed nałożeniem profilu)."""
    ok, expired, errors = approved(cfg, today)
    if errors:
        return errors, []
    if ok is None:
        return [], []
    warnings: list[str] = []
    targets = list(targets or ["claude"])
    managed_ids = {**MANAGED_IDS, **(((cfg.get("managed_agents") or {}).get("models")) or {})}
    seen_warn: set[str] = set()

    def why(model: str) -> str:
        if model in expired:
            return f"zatwierdzenie wygasło {expired[model]} ({KEY}.models.{model}.until)"
        return f"nie ma go na liście {KEY} (zatwierdzone: {_listed(ok)})"

    for u in usage(cfg, profile):
        model, where = u["model"], u["where"]
        if model == "inherit":
            if u["active"]:
                warnings.append(f"{where}: `inherit` bierze model sesji, którego lista {KEY} nie kontroluje — "
                                f"wpisz model w tierze albo pilnuj modelu sesji")
            continue
        problems = []
        is_tier = ".settings." not in where
        if "claude" in targets or not is_tier:
            if model not in ok:
                problems.append(f"model '{model}' — {why(model)}")
        if is_tier and "managed-agents" in targets and model not in ok:
            resolved = model if model.startswith("claude-") else str(managed_ids.get(model, model))
            if resolved not in ok and "claude" not in targets:
                problems.append(f"model '{resolved}' (target managed-agents, z '{model}' przez managed_agents.models) — "
                                f"{why(resolved)}")
        for p in problems:
            if u["active"]:
                errors.append(f"{where}: {p}")
            elif (msg := f"{where}: {p} — nie włączaj tego profilu") not in seen_warn:
                seen_warn.add(msg)
                warnings.append(msg)
    return errors, warnings


def _packs(root: Path):
    spec = importlib.util.spec_from_file_location("tf_packs_models", root / ".tf" / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project_state(root: Path) -> tuple[dict, str | None, list[str]]:
    """Konfiguracja projektu (bez nałożonego profilu), aktywny profil i targety — tak jak widzi je build.py."""
    packs = _packs(root)
    cfg = packs.load_config(root)
    profile = cfg.get("default_profile")
    state = root / ".claude" / "factory-profile.json"
    if state.is_file():
        try:
            profile = json.loads(state.read_text(encoding="utf-8")).get("profile") or profile
        except (json.JSONDecodeError, OSError):
            pass
    if profile not in (cfg.get("profiles") or {}):
        profile = cfg.get("default_profile")
    try:
        targets = packs.load_settings(root, cfg)["targets"]
    except Exception:  # noqa: BLE001 — ustawienia projektu nie mogą wywrócić kontroli modeli
        targets = list(cfg.get("default_targets") or ["claude"])
    return cfg, profile, targets


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    root = Path(argv[argv.index("--root") + 1]).resolve() if "--root" in argv else ROOT
    cfg, profile, targets = project_state(root)
    ok, expired, cfg_errors = approved(cfg)
    errors, warnings = check(cfg, profile, targets)
    uses = usage(cfg, profile)
    if "--json" in argv:
        raw = cfg.get(KEY) if isinstance(cfg.get(KEY), dict) else {}
        print(json.dumps({"source": raw.get("source"), "approved": ok, "expired": expired, "profile": profile,
                          "targets": targets, "usage": uses, "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2, default=str))
        return 1 if errors else 0
    if ok is None and not cfg_errors:
        print(f"Lista {KEY} nie jest ustawiona — bez ograniczeń modeli. Ustaw ją w .tf/config/config.yaml "
              f"(opis: python3 .tf/factory/models_policy.py --help).")
    else:
        print(f"Zatwierdzone modele ({KEY}): {_listed(ok or {})}"
              + (f" · wygasłe: {', '.join(f'{m} ({d})' for m, d in sorted(expired.items()))}" if expired else ""))
    print(f"Profil: {profile} · targety: {', '.join(targets)}")
    for u in uses:
        if u["active"]:
            print(f"  {u['where']:<40} {u['model']}")
    for w in warnings:
        print(f"⚠ {w}")
    for e in errors:
        print(f"✗ {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
