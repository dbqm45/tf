#!/usr/bin/env python3
"""
Packs (pack-*) installed in a project and the configuration assembled from the core and packs.

  python3 .tf/factory/packs.py              # installed packs and project settings
  python3 .tf/factory/packs.py --json       # configuration after assembly (for diagnostics)

Layout in a project:
  .tf/factory/config.yaml                 default core configuration (the engine — overwritten by an update)
  .tf/factory/traits/*.md                 core traits
  .tf/factory/packs/<id>/pack.yaml        pack: dimensions, agents, consultants, contributions to the core and other packs
  .tf/factory/packs/<id>/{roles,personas,traits}/
  .tf/factory/packs/<id>/pack.yaml → org_defaults   organization defaults (company pack, at most one)
  .tf/factory/packs/<id>/pack.yaml → team_defaults  team defaults (team pack, at most one, after the company one)
  .tf/config/config.yaml                  project overrides (applied recursively over the default configuration)
  .tf/config/{roles,personas,traits}/     the project's own roles, personas and traits (override those from the core and packs)
  ~/.tf/preferences.yaml, .tf/config/me.yaml   personal preferences: work style (`tf style`), the last layer
  .claude/skills/                         skills of the core and packs (Claude Code reads them only from here)
  .claude/factory-settings.json           project settings: targets (the conversation and commit language is not a setting)

Assembly rules:
  - lists (dimensions, dictionary, standalone skills, routing rows) — the core, then packs in name order;
  - dimensions sorted by `order`; the same prefix in two places is an error;
  - a pack's `always_skills` go only to its personas and executors;
  - `contributes` (contributions to personas, roles and agents outside the pack) as well as shared agents, consultants and routing rows
    of a pack apply only when `contributes_when` is satisfied (e.g. `{targets: [claude, managed-agents]}`);
  - references to elements of `optional_packs` that are not installed are skipped without error.
Standard library + PyYAML (the system one or the bundled copy in .tf/factory/_vendor).
"""
from __future__ import annotations

import json
import re
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

try:
    import yaml
except ImportError:  # bundled copy of PyYAML (MIT license, .tf/factory/_vendor/yaml/LICENSE)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

SETTINGS_REL = Path(".claude") / "factory-settings.json"
ENGINE_REL = Path(".tf") / "factory"     # the factory engine (read-only — overwritten by an update)
CONFIG_REL = Path(".tf") / "config"      # project configuration: config.yaml overrides, own personas, roles, traits
PACKS_REL = ENGINE_REL / "packs"
LIST_KEYS = ("traits", "core_skills", "skills")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base: dict, over: dict) -> dict:
    """`over` applied on top of `base`: dicts merged recursively, other values (lists, strings, numbers) replaced."""
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


# Company pack (`org_defaults` in pack.yaml): organization defaults between the engine and the project. Only these configuration
# keys — the rest is factory assembly (dimensions, agents), which the company pack does not rearrange.
ORG_CONFIG_KEYS = ("autonomy", "tiers", "profiles", "default_profile", "work", "loop", "steps", "task",
                   "commit_language", "models_approved", "isolation", "isolation_min", "isolation_allow_domains",
                   "addons")   # addons.<name>: settings the core passes to that add-on
ORG_OPERATIONS_KEYS = ("tracker",)


def org_defaults(root: Path, key: str = "org_defaults") -> tuple[str | None, dict]:
    """The first (by id) installed pack with `org_defaults` (or `team_defaults`, key) and its values; (None, {})
    without such a pack. More than one is an error reported by `compose` (build.py check)."""
    for pid, p in installed_packs(root).items():
        if isinstance(p.get(key), dict):
            return pid, p[key]
    return None, {}


def team_defaults(root: Path) -> tuple[str | None, dict]:
    """Team pack (`team_defaults`): the same keys as the company one, a layer between the company and the project."""
    return org_defaults(root, "team_defaults")


def narrowed_modes(layers: list[tuple[str, dict]]) -> list[str]:
    """`task.allowed_modes` after all layers: an intersection — a lower layer (team, project) only narrows the list
    of the higher one (company), never restores a mode the higher one took away."""
    allowed = list(TASK_MODES)
    for _label, layer in layers:
        modes = ((layer or {}).get("task") or {}).get("allowed_modes")
        if isinstance(modes, list):
            allowed = [m for m in allowed if m in modes]
    return allowed


def config_layers(root: Path) -> list[tuple[str, dict]]:
    """Configuration layers from the weakest: engine, organization (company pack), team (team pack), project,
    person. Every configuration
    reader (build, hooks, tf risk, tf work) assembles them in this order."""
    engine, own = root / ENGINE_REL / "config.yaml", root / CONFIG_REL / "config.yaml"
    layers = [((ENGINE_REL / "config.yaml").as_posix(), load_yaml(engine) if engine.is_file() else {})]
    for key in ("org_defaults", "team_defaults"):          # company, then team
        pid, od = org_defaults(root, key)
        if pid:
            part = {k: v for k, v in (od.get("config") or {}).items() if k in ORG_CONFIG_KEYS}
            layers.append((f"{(PACKS_REL / pid / 'pack.yaml').as_posix()} ({key})", part))
    if own.is_file():
        layers.append(((CONFIG_REL / "config.yaml").as_posix(), load_yaml(own)))
    below: dict = {}
    for _label, layer in layers:
        below = deep_merge(below, layer)
    below.setdefault("task", {})["allowed_modes"] = narrowed_modes(layers)
    person, _warns, sources = person_layer(root, below)
    if person:
        layers.append((f"{' + '.join(sources)} (person)", person))
    return layers


# Person layer (docs/todo.md, "Warstwy zespołu i preferencji osoby"): the last, the narrowest. A person sets only style
# and work-mode switches — without `work` limits, `autonomy.triage` rules and factory assembly. Autonomy operations
# can only be tightened (guard_bash checks this when assembling layers), and the default task mode must be in
# `task.allowed_modes` of the higher layers (company, team, project).
PERSON_REL = CONFIG_REL / "me.yaml"
PERSON_KEYS = {"task": ("default_mode",), "loop": ("blocked_slices", "confirm_each_slice"), "autonomy": ("operations",)}
TASK_MODES = ("plan", "normal", "auto")


def preferences_path() -> Path:
    """Personal preferences shared by all of a person's projects; `TF_PREFERENCES` overrides the path (tests)."""
    return Path(os.environ.get("TF_PREFERENCES") or Path.home() / ".tf" / "preferences.yaml")


def _person_part(data: dict, warns: list[str], src: str) -> dict:
    out: dict = {}
    for k, v in (data or {}).items():
        if k == "style":
            continue
        if k not in PERSON_KEYS or not isinstance(v, dict):
            warns.append(f"{src}: `{k}` — a person does not set this (allowed: style, "
                         f"{', '.join(f'{s}.{x}' for s, xs in PERSON_KEYS.items() for x in xs)}). Skipped")
            continue
        part = {x: v[x] for x in PERSON_KEYS[k] if x in v}
        for x in sorted(set(v) - set(PERSON_KEYS[k])):
            warns.append(f"{src}: `{k}.{x}` — a person does not set this. Skipped")
        if part:
            out[k] = part
    return out


def person_layer(root: Path, below: dict) -> tuple[dict, list[str], list[str]]:
    """Person layer: `~/.tf/preferences.yaml` ← `.tf/config/me.yaml`, the style expanded into switch values
    (`styles` in the engine configuration), then explicitly given values. Returns (layer, warnings, sources)."""
    warns: list[str] = []
    raw, sources = {}, []
    for path, label in ((preferences_path(), "~/.tf/preferences.yaml"), (root / PERSON_REL, PERSON_REL.as_posix())):
        try:
            data = load_yaml(path) if path.is_file() else None
        except Exception as e:  # noqa: BLE001 — a bad person file does not break the configuration; a warning remains
            warns.append(f"{label}: cannot read ({e})")
            continue
        if isinstance(data, dict) and data:
            raw, sources = deep_merge(raw, {**_person_part(data, warns, label),
                                            **({"style": data["style"]} if data.get("style") else {})}), [*sources, label]
    if not raw:
        return {}, warns, sources
    out: dict = {}
    style = raw.pop("style", None)
    if style:
        styles = below.get("styles") or {}
        if style in styles:
            preset = {k: v for k, v in (styles[style] or {}).items() if k != "claude"}   # claude: tf style, not configuration
            out = deep_merge(_person_part(preset, warns, f"styles.{style}"), {})
            out["style"] = style
        else:
            warns.append(f"unknown style \"{style}\" (available: {', '.join(styles) or 'none'}). Skipped")
    out = deep_merge(out, raw)
    allowed = (below.get("task") or {}).get("allowed_modes") or list(TASK_MODES)
    mode = (out.get("task") or {}).get("default_mode")
    if mode is not None and (mode not in TASK_MODES or mode not in allowed):
        warns.append(f"task.default_mode: {mode} — not in task.allowed_modes ({', '.join(allowed)}) set at a higher layer. "
                     "The company, team or project value stays")
        out["task"].pop("default_mode")
        if not out["task"]:
            out.pop("task")
    return out, warns, sources


LOCAL_SETTINGS_REL = Path(".claude") / "settings.local.json"
STYLE_MARK = "style_permission_mode"   # in .claude/factory-settings.json: what the style set and what was there before


def apply_style_permissions(root: Path) -> list[str]:
    """Claude Code permission mode from the work style (`styles.<style>.claude.permission_mode`) in the project's
    `.claude/settings.local.json`. Sets it only in place of the default (`default` or none) or one set earlier by the style —
    a mode chosen by a human is not overwritten. A style without a mode gives back what was there before it. Returns messages."""
    cfg = load_config(root)
    style = cfg.get("style")
    want = ((((cfg.get("styles") or {}).get(style) or {}) if style else {}).get("claude") or {}).get("permission_mode")
    local, mark_path = root / LOCAL_SETTINGS_REL, root / SETTINGS_REL

    def read(path: Path) -> dict:
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except (json.JSONDecodeError, OSError):
            data = None
        return data

    data, marks = read(local), read(mark_path)
    if data is None:
        return [f"{LOCAL_SETTINGS_REL.as_posix()}: invalid JSON. The style does not change the permission mode"]
    marks = marks if isinstance(marks, dict) else {}
    mark = marks.get(STYLE_MARK) if isinstance(marks.get(STYLE_MARK), dict) else None
    perms = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
    cur = perms.get("defaultMode")
    msgs: list[str] = []
    if mark and cur != mark.get("mode"):
        mark = None                      # a human changed the mode after the style — their choice, the style no longer gives it back
    if want:
        if cur == want:
            return msgs
        if mark is None and cur not in (None, "default"):
            msgs = [f"Claude Code permission mode stays `{cur}` (you chose it in {LOCAL_SETTINGS_REL.as_posix()}). "
                    f"Style {style} would set `{want}`. Change it yourself if you want"]
            if STYLE_MARK in marks:
                marks.pop(STYLE_MARK)
                mark_path.write_text(json.dumps(marks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            return msgs
        previous = mark.get("previous") if mark else cur
        perms["defaultMode"] = want
        mark = {"mode": want, "previous": previous}
        msgs.append(f"Claude Code permission mode: `{want}` in {LOCAL_SETTINGS_REL.as_posix()} (style {style}). It applies from "
                    "the next Claude Code session")
    elif mark or STYLE_MARK in marks:
        if mark:
            if mark.get("previous") is None:
                perms.pop("defaultMode", None)
            else:
                perms["defaultMode"] = mark["previous"]
            msgs.append(f"Claude Code permission mode restored: `{mark.get('previous') or 'default'}` "
                        f"(applies from the next session)")
        mark = None
    else:
        return msgs
    if msgs:                             # mode changed — write Claude Code settings (the rest of the file unchanged)
        if perms:
            data["permissions"] = perms
        else:
            data.pop("permissions", None)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if mark:
        marks[STYLE_MARK] = mark
    else:
        marks.pop(STYLE_MARK, None)
    mark_path.write_text(json.dumps(marks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return msgs


def work_style(root: Path) -> dict:
    """Work mode after assembling layers: style, default and allowed task modes, loop switches, warnings."""
    cfg = load_config(root)
    below: dict = {}
    lower = [lv for lv in config_layers(root) if not lv[0].endswith("(person)")]
    for _label, layer in lower:
        below = deep_merge(below, layer)
    below.setdefault("task", {})["allowed_modes"] = narrowed_modes(lower)
    warns = person_layer(root, below)[1]
    task, loop = cfg.get("task") or {}, cfg.get("loop") or {}
    allowed = [m for m in (task.get("allowed_modes") or TASK_MODES) if m in TASK_MODES]
    mode = task.get("default_mode") if task.get("default_mode") in allowed else ("normal" if "normal" in allowed else allowed[0])
    return {"style": cfg.get("style"), "default_mode": mode, "allowed_modes": allowed,
            "blocked_slices": loop.get("blocked_slices") is True,
            "confirm_each_slice": loop.get("confirm_each_slice") is True, "warnings": warns}


def org_operations(root: Path) -> dict:
    """Operational card defaults from the company pack, overridden by the team pack (today: `tracker`). The tracker
    address (`url`) is set by neither — where the token goes is determined only by the JIRA_BASE_URL variable (tf skill, intake.py)."""
    tracker: dict = {}
    for key in ("org_defaults", "team_defaults"):
        ops = org_defaults(root, key)[1].get("operations") or {}
        if isinstance(ops.get("tracker"), dict):
            # team prefixes replace company prefixes (the team's ticket keys), the other fields are merged
            tracker = {**deep_merge(tracker, ops["tracker"]),
                       **({"prefixes": ops["tracker"]["prefixes"]} if "prefixes" in ops["tracker"] else {})}
    return {"tracker": {k: v for k, v in tracker.items() if k != "url"}} if tracker else {}


def load_config(root: Path) -> dict:
    """Core configuration: engine (`.tf/factory/config.yaml`) ← organization defaults (company pack) ←
    project overrides (`.tf/config/config.yaml`) ← personal preferences (work style)."""
    cfg: dict = {}
    layers = config_layers(root)
    for _label, layer in layers:
        cfg = deep_merge(cfg, layer)
    if layers:
        cfg.setdefault("task", {})["allowed_modes"] = narrowed_modes([lv for lv in layers if not lv[0].endswith("(person)")])
    return cfg


# The project's decision to work without a security scanner (`tf config security.scanner off --by human:<id> --reason …`).
# Without it a missing scanner is a FAIL of the slice scan; with it the scan records the decision instead (who, when, why).
SCANNER_KEY = re.compile(r"(?m)^security:[ \t]*(#.*)?$")


def scanner_decision(root: Path) -> dict | None:
    """The recorded `security.scanner` decision when it is `off` ({"state", "by", "at", "reason"}); None otherwise."""
    try:
        sec = load_config(root).get("security")
    except Exception:  # noqa: BLE001 — an unreadable configuration is no decision: the scan stays strict
        return None
    dec = sec.get("scanner") if isinstance(sec, dict) else None
    if isinstance(dec, dict) and str(dec.get("state", "")).lower() == "off" and dec.get("by"):
        return dec
    return None


def write_scanner_decision(root: Path, state: str, by: str, reason: str, at: str) -> Path:
    """`security.scanner` in the project configuration, as one flow-mapping line; the rest of the file (comments too) stays.
    A `security:` block that already exists gets the line in place of its old `scanner:` entry."""
    f = root / CONFIG_REL / "config.yaml"
    text = f.read_text(encoding="utf-8") if f.is_file() else ""
    value = {"state": state, "by": by, "at": at, "reason": reason}
    line = "  scanner: " + json.dumps(value, ensure_ascii=False)
    lines = text.splitlines()
    head = next((i for i, ln in enumerate(lines) if SCANNER_KEY.fullmatch(ln)), None)
    if head is None:
        if re.search(r"(?m)^security:", text):
            raise ValueError("the `security` key in .tf/config/config.yaml is not a block — write it as `security:` with "
                             "indented entries")
        lines += ["security:", line]
    else:
        end = head + 1
        while end < len(lines) and (not lines[end].strip() or lines[end][:1] in " \t"):
            end += 1
        body, skip = [], None
        for ln in lines[head + 1:end]:
            indent = len(ln) - len(ln.lstrip())
            if skip is not None and (not ln.strip() or indent > skip):
                continue                         # the nested lines of the old `scanner:` entry
            skip = indent if re.match(r"\s+scanner:", ln) else None
            if skip is None:
                body.append(ln)
        lines[head + 1:end] = [line, *body]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f


def installed_packs(root: Path) -> dict[str, dict]:
    """Packs installed in the project: id → pack.yaml data (+ `_dir`)."""
    out: dict[str, dict] = {}
    base = root / PACKS_REL
    for p in sorted(base.glob("*/pack.yaml")) if base.is_dir() else []:
        data = load_yaml(p)
        data["_dir"] = p.parent
        out[data.get("id") or p.parent.name] = data
    return out


def load_settings(root: Path, cfg: dict) -> dict:
    """Project settings with the core's default values."""
    data: dict = {}
    p = root / SETTINGS_REL
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            data = {}
    targets = [t for t in (data.get("targets") or cfg.get("default_targets") or ["claude"]) if isinstance(t, str)]
    return {"targets": targets}


def save_settings(root: Path, **changes) -> dict:
    p = root / SETTINGS_REL
    data: dict = {}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            data = {}
    data.update({k: v for k, v in changes.items() if v is not None})
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return data


def drop_settings(root: Path, *keys: str) -> bool:
    """Removes keys from the project settings (e.g. the former `language`, `commit_language`). True when something was changed."""
    p = root / SETTINGS_REL
    try:
        data = json.loads(p.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict) or not any(k in data for k in keys):
        return False
    p.write_text(json.dumps({k: v for k, v in data.items() if k not in keys}, ensure_ascii=False, indent=1) + "\n",
                 encoding="utf-8")
    return True


def active(pack: dict, settings: dict) -> bool:
    """Whether a pack's contribution applies under these settings (`contributes_when`)."""
    cond = pack.get("contributes_when") or {}
    return all(settings.get(k) == v for k, v in cond.items())


def _union(a, b) -> list:
    return list(dict.fromkeys([*(a or []), *(b or [])]))


def compose(root: Path, cfg: dict) -> dict:
    """Core configuration (`cfg`) supplemented with installed packs and project settings. Assembly errors
    go to `_errors` (reported by `build.py check`)."""
    cfg = dict(cfg)
    packs = installed_packs(root)
    settings = load_settings(root, cfg)
    errors: list[str] = []
    cfg["_packs"], cfg["_settings"] = packs, settings
    for key, kind in (("org_defaults", "company"), ("team_defaults", "team")):
        owners = [pid for pid, p in packs.items() if p.get(key) is not None]
        if len(owners) > 1:
            errors.append(f"{key}: {' and '.join(owners)} — a project can have only one {kind} pack "
                          f"({owners[0]} is active)")
        if key == "team_defaults" and owners and not any(p.get("org_defaults") is not None for p in packs.values()):
            errors.append(f"{owners[0]}: team pack without a company pack. Install pack-<company> "
                          "(requires.packs in the team pack.yaml)")
        for pid in owners[:1]:
            od = packs[pid][key]
            if not isinstance(od, dict):
                errors.append(f"{pid}: {key} must be a mapping (config, operations)")
                continue
            for k in sorted(set(od) - {"config", "operations"}):
                errors.append(f"{pid}: {key}.{k} — unknown section (available: config, operations)")
            for k in sorted(set(od.get("config") or {}) - set(ORG_CONFIG_KEYS)):
                errors.append(f"{pid}: {key}.config.{k} — a {kind} pack does not set this key "
                              f"(allowed: {', '.join(ORG_CONFIG_KEYS)}). Value skipped")
            for k in sorted(set(od.get("operations") or {}) - set(ORG_OPERATIONS_KEYS)):
                errors.append(f"{pid}: {key}.operations.{k} — unknown section (available: tracker). Value skipped")
    cfg["_active"] = {pid for pid, p in packs.items() if active(p, settings)}

    facets = [dict(f, _pack="core") for f in cfg.get("facets") or []]
    for pid, p in packs.items():
        facets += [dict(f, _pack=pid) for f in p.get("facets") or []]
    seen: dict[str, str] = {}
    for f in facets:
        if f["prefix"] in seen:
            errors.append(f"facet {f['prefix']}: defined in {seen[f['prefix']]} and in {f['_pack']}")
        seen[f["prefix"]] = f["_pack"]
    cfg["facets"] = sorted(facets, key=lambda f: f.get("order", 500))

    cfg["vocabulary"] = _union(cfg.get("vocabulary"), [v for p in packs.values() for v in p.get("vocabulary") or []])
    cfg["skill_requires"] = dict(cfg.get("skill_requires") or {})
    cfg["standalone_skills"] = list(cfg.get("standalone_skills") or [])
    cfg["shared_agents"] = {n: dict(s, _pack="core") for n, s in (cfg.get("shared_agents") or {}).items()}
    cfg["consultants"] = {}
    rows, notes = [cfg.get("routing", "").rstrip()], [cfg.get("routing_notes", "").strip()]
    fresh = {"prefixes": {}, "skills": {}}
    name_only: list[str] = []
    persona_contrib: dict[str, list] = {k: [] for k in LIST_KEYS}
    role_contrib: dict[str, dict] = {}
    for pid, p in packs.items():
        for k, v in (p.get("skill_requires") or {}).items():
            cfg["skill_requires"][k] = _union(cfg["skill_requires"].get(k), v)
        cfg["standalone_skills"] = _union(cfg["standalone_skills"], p.get("standalone_skills"))
        cfg["unversioned_skills"] = _union(cfg.get("unversioned_skills"), p.get("unversioned_skills"))
        cfg.setdefault("reference_sections", {}).update(p.get("reference_sections") or {})
        for k in ("prefixes", "skills"):
            fresh[k].update((p.get("freshness") or {}).get(k) or {})
        name_only = _union(name_only, (p.get("skill_visibility") or {}).get("name_only_prefixes"))
        if pid not in cfg["_active"]:
            continue
        for n, s in (p.get("shared_agents") or {}).items():
            if n in cfg["shared_agents"]:
                errors.append(f"shared agent {n}: defined in {cfg['shared_agents'][n]['_pack']} and in {pid}")
            cfg["shared_agents"][n] = dict(s, _pack=pid)
        for n, s in (p.get("consultants") or {}).items():
            cfg["consultants"][n] = dict(s, _pack=pid)
        if p.get("routing"):
            rows.append(p["routing"].rstrip())
        if p.get("routing_notes"):
            notes.append(p["routing_notes"].strip())
        contrib = p.get("contributes") or {}
        for k in LIST_KEYS:
            persona_contrib[k] = _union(persona_contrib[k], (contrib.get("personas") or {}).get(k))
        for role, extra in (contrib.get("roles") or {}).items():
            role_contrib.setdefault(role, {"skills": []})["skills"] = _union(
                role_contrib.get(role, {}).get("skills"), (extra or {}).get("skills"))
    # contributions to agents (including those from packs): skills and a prompt paragraph
    for pid, p in packs.items():
        if pid not in cfg["_active"]:
            continue
        for n, extra in ((p.get("contributes") or {}).get("agents") or {}).items():
            if n not in cfg["shared_agents"]:
                continue
            a = dict(cfg["shared_agents"][n])
            a["skills"] = _union(a.get("skills"), (extra or {}).get("skills"))
            if (extra or {}).get("prompt"):
                a["prompt"] = a.get("prompt", "").rstrip() + "\n" + extra["prompt"].strip() + "\n"
            cfg["shared_agents"][n] = a
    cfg["routing"] = "\n".join(r for r in rows if r) + "\n"
    cfg["routing_notes"] = "\n".join(n for n in notes if n) + "\n"
    cfg["freshness"] = fresh
    cfg["skill_visibility"] = {"name_only_prefixes": name_only}
    cfg["_persona_contrib"], cfg["_role_contrib"] = persona_contrib, role_contrib
    cfg["_errors"] = errors
    return cfg


def missing_optional(pack: dict | None, packs: dict) -> list[str]:
    """Optional packs of this pack that are not installed."""
    return [o for o in (pack or {}).get("optional_packs") or [] if o not in packs]


def load_items(root: Path, sub: str) -> tuple[dict[str, dict], list[str]]:
    """Roles or personas: from packs and the project's own (the project's own override the pack). Returns (items, warnings)."""
    items: dict[str, dict] = {}
    notes: list[str] = []
    for pid, p in installed_packs(root).items():
        for f in sorted((p["_dir"] / sub).glob("*.yaml")):
            data = load_yaml(f)
            data["_src"] = f.relative_to(root).as_posix()
            data["_pack"] = pid
            if data.get("name") in items:
                notes.append(f"{sub} {data['name']}: in {items[data['name']]['_pack']} and in {pid}. Using {pid}")
            items[data["name"]] = data
    for f in sorted((root / CONFIG_REL / sub).glob("*.yaml")):
        data = load_yaml(f)
        data["_src"] = (CONFIG_REL / sub / f.name).as_posix()
        data["_pack"] = "project"
        if data.get("name") in items:
            notes.append(f"{sub} {data['name']}: the project's own version replaces the version from {items[data['name']]['_pack']}")
        items[data["name"]] = data
    return items, notes


def load_traits(root: Path) -> dict[str, str]:
    out = {p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((root / ENGINE_REL / "traits").glob("*.md"))}
    for p in installed_packs(root).values():
        out.update({t.stem: t.read_text(encoding="utf-8").strip() for t in sorted((p["_dir"] / "traits").glob("*.md"))})
    out.update({p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((root / CONFIG_REL / "traits").glob("*.md"))})
    return out


MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"


# Commit language of a repository without a model: subjects of recent commits (without the Conventional Commits prefix).
PL_CHARS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
PL_WORDS = {"i", "w", "na", "z", "dla", "nie", "oraz", "przez", "bez", "dodaj", "dodano", "popraw", "poprawka",
            "poprawki", "zmiana", "zmiany", "nowy", "nowa", "nowe", "aktualizacja", "przenieś", "usuń", "obsługa"}
EN_WORDS = {"the", "and", "for", "of", "in", "with", "from", "into", "add", "adds", "added", "fix", "fixes", "fixed",
            "update", "updates", "remove", "removes", "use", "when", "by", "new", "move", "handle", "support"}
CC_PREFIX = re.compile(r"^[a-z]+(\([^)]*\))?!?:\s*")


_COMMIT_LANG: dict = {}


def commit_language(root: Path, last: int = 50) -> str | None:
    """`pl`, `en`, `mixed` (no clear majority) or None (no git or commits — a new repository).
    Result memoized per process — build calls it once per agent."""
    key = (str(Path(root).resolve()), last)
    if key not in _COMMIT_LANG:
        _COMMIT_LANG[key] = _commit_language(Path(root), last)
    return _COMMIT_LANG[key]


def _commit_language(root: Path, last: int) -> str | None:
    if not root.is_dir():
        return None
    try:
        r = subprocess.run(["git", "log", f"-{last}", "--no-merges", "--format=%s"], cwd=root, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    subjects = [s for s in r.stdout.splitlines() if s.strip()] if r.returncode == 0 else []
    if not subjects:
        return None
    pl = en = 0
    for s in subjects:
        body = CC_PREFIX.sub("", s)
        words = set(re.findall(r"[^\W\d_]+", body.lower()))
        is_pl, is_en = bool(PL_CHARS & set(body)) or bool(words & PL_WORDS), bool(words & EN_WORDS)
        pl += is_pl and not is_en
        en += is_en and not is_pl
    if pl + en == 0 or min(pl, en) * 3 > max(pl, en):   # fewer than 3:1 — no verdict
        return "mixed"
    return "pl" if pl > en else "en"


def language_lines(cfg: dict, root: Path) -> list[str]:
    """The "Language" section: the conversation rule (fixed), commit language from `git log`, code language."""
    cl = cfg.get("commit_language") or {}
    found = commit_language(root)
    code = found or cl.get("new_repo", "en")
    commits = cl.get(code) or cl.get("mixed")
    if commits:   # where this language comes from — a human sees it is not a setting
        commits = commits.rstrip(".") + (" (like the existing commits, `git log`)." if found else
                                         " (new repository without commits; later the language of the history in `git log`).")
    lines = [cfg.get("language_note"), commits, cfg.get("code_language_note")]
    return [f"- {' '.join(str(x).split())}" for x in lines if x]


def write_language_lines(path: Path, cfg: dict, root: Path) -> bool:
    """Replaces the "### Language" subsection in the factory block in CLAUDE.md / CLAUDE.local.md. Returns True when changed."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if MARK_BEGIN not in text or MARK_END not in text:
        return False
    a, b = text.index(MARK_BEGIN), text.index(MARK_END)
    block = text[a:b]
    body = "### Language\n" + "\n".join(language_lines(cfg, root)) + "\n"
    head = "### Language\n"
    if head in block:
        i = block.index(head)
        j = block.find("\n### ", i + 1)
        new_block = block[:i] + body + (block[j + 1:] if j >= 0 else "")
    else:
        new_block = block.rstrip("\n") + "\n\n" + body
    new = text[:a] + new_block + text[b:]
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[2]
    cfg = compose(root, load_config(root))
    if "--json" in argv:
        print(json.dumps({k: v for k, v in cfg.items() if k != "_packs"}, ensure_ascii=False, indent=1, default=str))
        return 0
    s = cfg["_settings"]
    print(f"Commit language: {commit_language(root) or 'new repository'} (from git log) · targets: {', '.join(s['targets'])}")
    for pid, p in cfg["_packs"].items():
        state = "" if pid in cfg["_active"] else " (dormant: contributes_when not met)"
        print(f"  {pid} {p.get('version', '?')} — {p.get('title', '')}{state}")
    if not cfg["_packs"]:
        print("  (no packs installed — core only)")
    for e in cfg["_errors"]:
        print(f"✗ {e}")
    return 1 if cfg["_errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
