#!/usr/bin/env python3
"""Model names in the factory configuration (step H20): whether the configuration and engine refer to models that do not exist.

  python3 .tf/factory/model_check.py            # human-readable result (also in `tf doctor`)
  python3 .tf/factory/model_check.py --json     # result for scripts
  python3 .tf/factory/model_check.py --today YYYY-MM-DD   # reference date (tests)

The single source of truth is three keys of `.tf/factory/config.yaml`: `models_current` (alias → current identifier),
`models_legacy` (older identifiers, still allowed when someone pins them deliberately) and `models_checked` (the date
of the check, source: the `claude-api` skill). Checked are:
- every `claude-…` identifier in the core configuration, in the company and team packs (`org_defaults`, `team_defaults`),
  in project overrides (`.tf/config/config.yaml`) and in the engine code (`.tf/factory/*.py`) — an unknown one is an error (a typo or a model that no longer exists);
- aliases in `managed_agents.models` — they must point to a model from `models_current`, not an older one;
- the price list `prices_usd_per_mtok` — every current alias has a price (missing is a warning: the cost report will show only tokens);
- the `models_checked` date — older than 90 days is a warning (not an error: CI does not turn red from the passage of time).

Approved models (`models_approved`, optional; without it nothing below applies). An organization lists the models it
allows — by alias or by full identifier, linked through `models_current` — in the company pack, the team pack or the
project; a lower layer only narrows the list of a higher one. With a list: a tier model after the active profile and
the active profile's session settings (`model`, `advisorModel`) outside the list are errors, other profiles and
`inherit` are warnings, `until` in the past ends an approval, and with the `managed-agents` target the identifier
a tier alias maps to must be approved too. The same list is used by `profile.py` and by the `model_guard` hook.

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
from datetime import date, datetime
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
APPROVED = "models_approved"
PROFILE_STATE = Path(".claude") / "factory-profile.json"
SESSION_KEYS = ("model", "advisorModel")      # profile settings that name a model


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


def policy_layers(mod, root: Path) -> list[tuple[str, dict]]:
    """Layers that can set `models_approved`, from the weakest: engine, company pack, team pack, project. A layer that
    cannot be read counts as empty (the unreadable file is reported elsewhere); the person layer never sets the list."""
    layers: list[tuple[str, dict]] = []

    def read(rel: Path) -> None:
        try:
            data = mod.load_yaml(root / rel) if (root / rel).is_file() else {}
        except Exception:  # noqa: BLE001
            data = {}
        layers.append((rel.as_posix(), data if isinstance(data, dict) else {}))

    read(ENGINE / "config.yaml")
    for key in ("org_defaults", "team_defaults"):
        try:
            pid, od = mod.org_defaults(root, key)
        except Exception:  # noqa: BLE001 — a broken pack.yaml is reported by build.py check
            pid, od = None, {}
        conf = od.get("config") if pid and isinstance(od.get("config"), dict) else {}
        if pid:
            layers.append((f"{(ENGINE / 'packs' / pid / 'pack.yaml').as_posix()} ({key})",
                           {k: v for k, v in conf.items() if k in mod.ORG_CONFIG_KEYS}))
    read(OWN)
    return layers


def covering(model: str, names, current: dict) -> str | None:
    """The name on `names` that covers `model`: the model itself, the identifier its alias points to in
    `models_current`, or an alias that points to this identifier. None when nothing covers it."""
    if model in names:
        return model
    if current.get(model) in names:
        return current[model]
    return next((alias for alias, mid in current.items() if mid == model and alias in names), None)


def approved_policy(layers: list[tuple[str, dict]], current: dict, today: date) -> dict:
    """The list of approved models after all layers. `set` is False when no layer gives a list (no restriction)."""
    errors, warnings = [], []
    entries: dict[str, dict] | None = None
    source = None
    for label, layer in layers:
        raw = layer.get(APPROVED)
        if raw is None or raw == {}:
            continue
        where = f"{APPROVED} in {label}"
        if not isinstance(raw, dict) or not isinstance(raw.get("models") or {}, dict):
            errors.append(f"{where}: expected `models:` with a mapping model → details (e.g. `sonnet: {{}}`) — the layer was skipped")
            continue
        found, bad = {}, False
        for name, meta in (raw.get("models") or {}).items():
            if not isinstance(name, str) or not (meta is None or isinstance(meta, dict)):
                errors.append(f"{where}: the entry `{name}` must be a mapping of details (may be empty: `{name}: {{}}`) — the layer was skipped")
                bad = True
                continue
            entry = dict(meta or {})
            until = entry.get("until")
            try:   # YAML gives a date for an unquoted value and a date with a time when someone adds the hour
                entry["until"] = (until.date() if isinstance(until, datetime) else until if isinstance(until, date)
                                  or until is None else date.fromisoformat(str(until)))
            except ValueError:
                errors.append(f"{where}: `until` of {name} is `{until}` — expected a date YYYY-MM-DD — the layer was skipped")
                bad = True
                continue
            found[name] = entry
        if bad or not found:
            continue
        if entries is None:
            entries, source = found, raw.get("source") if isinstance(raw.get("source"), str) else label
            continue
        kept = {}
        for name, entry in found.items():
            parent = covering(name, entries, current)
            if parent is None:
                warnings.append(f"{where}: {name} is not on the list of a higher layer — ignored (a lower layer can only narrow the list)")
                continue
            dates = [d for d in (entries[parent].get("until"), entry.get("until")) if d]
            kept[name] = {**entries[parent], **entry, "until": min(dates) if dates else None}
        entries = kept
    entries = entries if entries is not None else {}
    expired = {n: e["until"].isoformat() for n, e in entries.items() if e.get("until") and e["until"] < today}
    return {"set": source is not None, "source": source, "valid": sorted(n for n in entries if n not in expired),
            "expired": expired, "current": current, "errors": errors, "warnings": warnings}


def approval(model: str, policy: dict) -> tuple[bool, str]:
    """(approved?, reason when not). Without a list every model is approved."""
    if not policy["set"] or covering(model, policy["valid"], policy["current"]):
        return True, ""
    late = covering(model, policy["expired"], policy["current"])
    if late:
        return False, f"the approval of {late} ended on {policy['expired'][late]}"
    return False, "it is not on the list"


def model_usage(cfg: dict, active: str | None, managed: bool) -> list[dict]:
    """Where the configuration names a model: tiers after each profile, the profiles' session settings and, with the
    `managed-agents` target, the identifiers the active tiers map to. `active` marks what works now."""
    tiers = cfg.get("tiers") if isinstance(cfg.get("tiers"), dict) else {}
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}

    def part(name, key) -> dict:
        prof = profiles.get(name) if isinstance(profiles.get(name), dict) else {}
        return prof.get(key) if isinstance(prof.get(key), dict) else {}

    def tier_models(name) -> dict:
        out = {}
        for tier, t in tiers.items():
            over = part(name, "tiers").get(tier)
            m = (over.get("model") if isinstance(over, dict) else None) or (t.get("model") if isinstance(t, dict) else None)
            if isinstance(m, str) and m:
                out[tier] = m
        return out

    def session(name) -> dict:
        return {k: v for k, v in part(name, "settings").items() if k in SESSION_KEYS and isinstance(v, str) and v}

    items = [{"where": f"tiers.{t}", "model": m, "active": True, "profile": active} for t, m in tier_models(active).items()]
    items += [{"where": f"profiles.{active}.settings.{k}", "model": m, "active": True, "profile": active}
              for k, m in session(active).items()]
    if managed:
        ids = (cfg.get("managed_agents") or {}).get("models") if isinstance(cfg.get("managed_agents"), dict) else {}
        for alias in sorted({m for m in tier_models(active).values() if not m.startswith("claude-")}):
            mid = (ids or {}).get(alias)
            if isinstance(mid, str) and mid:
                items.append({"where": f"managed_agents.models.{alias}", "model": mid, "active": True, "profile": active})
    for name in profiles:
        if name != active:
            items += [{"where": f"profiles.{name}.tiers.{t}", "model": m, "active": False, "profile": name}
                      for t, m in tier_models(name).items()]
            items += [{"where": f"profiles.{name}.settings.{k}", "model": m, "active": False, "profile": name}
                      for k, m in session(name).items()]
    return items


def load_policy(root: Path, today: date | None = None) -> dict:
    """The approved list of a project with what it applies to — for `check`, `profile.py` and the `model_guard` hook."""
    mod = packs_module(root)
    layers = policy_layers(mod, root)
    cfg: dict = {}
    for _label, layer in layers:
        cfg = mod.deep_merge(cfg, layer)
    current = {k: v for k, v in (cfg.get("models_current") if isinstance(cfg.get("models_current"), dict) else {}).items()
               if isinstance(k, str) and isinstance(v, str)}
    policy = approved_policy(layers, current, today or date.today())
    try:
        state = json.loads((root / PROFILE_STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    active = state.get("profile") if isinstance(state, dict) and isinstance(state.get("profile"), str) else cfg.get("default_profile")
    try:
        managed = "managed-agents" in mod.load_settings(root, cfg)["targets"]
    except Exception:  # noqa: BLE001
        managed = False
    return {**policy, "config": cfg, "active": active if isinstance(active, str) else None, "managed": managed}


def judge(policy: dict, usage: list[dict]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the places that use a model outside the approved list."""
    errors, warnings = [], []
    if not policy["set"]:
        return errors, warnings
    allows = f"{APPROVED} allows: {', '.join(policy['valid']) or 'nothing'} (source: {policy['source']})"
    later: dict[str, list[str]] = {}
    for u in usage:
        if u["model"] == "inherit":
            if u["active"]:
                warnings.append(f"{u['where']}: `inherit` takes the session's model, which {APPROVED} does not control")
            continue
        ok, why = approval(u["model"], policy)
        if ok:
            continue
        if u["active"]:
            errors.append(f"{u['where']}: model {u['model']} is not approved ({why}; active profile: {u['profile']}) — {allows}")
        else:
            later.setdefault(u["profile"], []).append(f"{u['model']} in {u['where']} ({why})")
    for name, found in later.items():
        warnings.append(f"profiles.{name} would use models that are not approved: {'; '.join(found)} — "
                        f"`profile.py {name}` will refuse to switch ({APPROVED})")
    return errors, warnings


def profile_violations(root: Path, name: str, session: bool = True, today: date | None = None) -> list[str]:
    """What stops switching to the profile `name`: its models outside the approved list (empty = nothing)."""
    policy = load_policy(root, today)
    usage = [u for u in model_usage(policy["config"], name, policy["managed"])
             if u["active"] and (session or ".settings." not in u["where"])]
    return judge(policy, usage)[0]


def check(root: Path, today: date) -> dict:
    errors, warnings = [], []
    mod = packs_module(root)
    try:
        core = mod.load_yaml(root / ENGINE / "config.yaml") or {}
    except Exception as e:  # noqa: BLE001 — the core configuration is unreadable: there is nothing to check
        return {"errors": [f"cannot read {ENGINE / 'config.yaml'}: {e}"], "warnings": [], "current": {},
                "legacy": [], "checked": None, "ids": [], "approved": None, "approved_expired": {}, "usage": []}
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

    sources = [((ENGINE / "config.yaml").as_posix(), core), (OWN.as_posix(), own)]
    sources[1:1] = [(label, data) for label, data in policy_layers(mod, root)[1:-1]]   # company and team packs
    for label, data in sources:
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
    policy = load_policy(root, today)
    usage = model_usage(policy["config"], policy["active"], policy["managed"])
    found = judge(policy, usage)
    errors += policy["errors"] + found[0]
    warnings += policy["warnings"] + found[1]
    return {"errors": errors, "warnings": warnings, "current": current, "legacy": legacy, "checked": checked or None,
            "ids": sorted(seen), "approved": policy["valid"] if policy["set"] else None,
            "approved_expired": policy["expired"], "usage": usage, "profile": policy["active"]}


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
            if res["approved"] is not None:
                print(f"✓ models: the approved list ({', '.join(res['approved'])}) covers the tiers and the session "
                      f"settings of the active profile {res['profile'] or '—'}")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
