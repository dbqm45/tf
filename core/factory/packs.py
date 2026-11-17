#!/usr/bin/env python3
"""
Nakładki (pack-*) zainstalowane w projekcie i konfiguracja złożona z rdzenia i nakładek.

  python3 .tf/factory/packs.py              # zainstalowane nakładki i ustawienia projektu
  python3 .tf/factory/packs.py --json       # konfiguracja po złożeniu (do diagnostyki)

Układ w projekcie:
  .tf/factory/config.yaml                 domyślna konfiguracja rdzenia (silnik — nadpisuje go aktualizacja)
  .tf/factory/traits/*.md                 cechy rdzenia
  .tf/factory/packs/<id>/pack.yaml        nakładka: wymiary, agenci, konsultanci, wkład do rdzenia i innych nakładek
  .tf/factory/packs/<id>/{roles,personas,traits}/
  .tf/factory/packs/<id>/pack.yaml → org_defaults   domyślne organizacji (nakładka firmowa, najwyżej jedna)
  .tf/factory/packs/<id>/pack.yaml → team_defaults  domyślne zespołu (nakładka zespołu, najwyżej jedna, po firmowej)
  .tf/config/config.yaml                  nadpisania projektu (nakładane rekurencyjnie na domyślną konfigurację)
  .tf/config/{roles,personas,traits}/     własne role, persony i cechy projektu (nadpisują te z rdzenia i nakładek)
  ~/.tf/preferences.yaml, .tf/config/me.yaml   preferencje osoby: styl pracy (`tf style`), ostatnia warstwa
  .claude/skills/                         skille rdzenia i nakładek (Claude Code czyta je tylko stąd)
  .claude/factory-settings.json           ustawienia projektu: targets (język rozmowy i commitów nie jest ustawieniem)

Zasady składania:
  - listy (wymiary, słownik, skille samodzielne, wiersze routingu) — rdzeń, potem nakładki w kolejności nazw;
  - wymiary sortowane po `order`; ten sam prefiks w dwóch miejscach to błąd;
  - `always_skills` nakładki trafiają tylko do jej person i wykonawców;
  - `contributes` (wkład do person, ról i agentów spoza nakładki) oraz agenci wspólni, konsultanci i wiersze routingu
    nakładki działają tylko wtedy, gdy spełniony jest `contributes_when` (np. `{targets: [claude, managed-agents]}`);
  - odwołania do elementów nakładek z `optional_packs`, których nie zainstalowano, są pomijane bez błędu.
Biblioteka standardowa + PyYAML (systemowy albo dołączony w .tf/factory/_vendor).
"""
from __future__ import annotations

import json
import re
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

try:
    import yaml
except ImportError:  # dołączona kopia PyYAML (licencja MIT, .tf/factory/_vendor/yaml/LICENSE)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

SETTINGS_REL = Path(".claude") / "factory-settings.json"
ENGINE_REL = Path(".tf") / "factory"     # silnik fabryki (tylko do odczytu — nadpisuje go aktualizacja)
CONFIG_REL = Path(".tf") / "config"      # konfiguracja projektu: nadpisania config.yaml, własne persony, role, cechy
PACKS_REL = ENGINE_REL / "packs"
LIST_KEYS = ("traits", "core_skills", "skills")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base: dict, over: dict) -> dict:
    """`over` nałożone na `base`: słowniki łączone rekurencyjnie, inne wartości (listy, napisy, liczby) zastępowane."""
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


# Nakładka firmowa (`org_defaults` w pack.yaml): domyślne organizacji między silnikiem a projektem. Tylko te klucze
# konfiguracji — reszta to składanie fabryki (wymiary, agenci), którego nakładka firmowa nie przestawia.
ORG_CONFIG_KEYS = ("autonomy", "tiers", "profiles", "default_profile", "work", "loop", "steps", "task",
                   "commit_language")
ORG_OPERATIONS_KEYS = ("tracker",)


def org_defaults(root: Path, key: str = "org_defaults") -> tuple[str | None, dict]:
    """Pierwsza (po id) zainstalowana nakładka z `org_defaults` (albo `team_defaults`, key) i jej wartości; (None, {})
    bez takiej nakładki. Więcej niż jedna to błąd zgłaszany przez `compose` (build.py check)."""
    for pid, p in installed_packs(root).items():
        if isinstance(p.get(key), dict):
            return pid, p[key]
    return None, {}


def team_defaults(root: Path) -> tuple[str | None, dict]:
    """Nakładka zespołu (`team_defaults`): te same klucze co firmowa, warstwa między firmą a projektem."""
    return org_defaults(root, "team_defaults")


def narrowed_modes(layers: list[tuple[str, dict]]) -> list[str]:
    """`task.allowed_modes` po wszystkich warstwach: przecięcie — niższa warstwa (zespół, projekt) tylko zawęża listę
    wyższej (firma), nigdy nie przywraca trybu, który wyższa zabrała."""
    allowed = list(TASK_MODES)
    for _label, layer in layers:
        modes = ((layer or {}).get("task") or {}).get("allowed_modes")
        if isinstance(modes, list):
            allowed = [m for m in allowed if m in modes]
    return allowed


def config_layers(root: Path) -> list[tuple[str, dict]]:
    """Warstwy konfiguracji od najsłabszej: silnik, organizacja (nakładka firmowa), zespół (nakładka zespołu), projekt,
    osoba. Każdy czytelnik
    konfiguracji (build, hooki, tf risk, tf work) składa je w tej kolejności."""
    engine, own = root / ENGINE_REL / "config.yaml", root / CONFIG_REL / "config.yaml"
    layers = [((ENGINE_REL / "config.yaml").as_posix(), load_yaml(engine) if engine.is_file() else {})]
    for key in ("org_defaults", "team_defaults"):          # firma, potem zespół
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
        layers.append((f"{' + '.join(sources)} (osoba)", person))
    return layers


# Warstwa osoby (docs/todo.md, „Warstwy zespołu i preferencji osoby”): ostatnia, najwęższa. Osoba ustawia tylko styl
# i przełączniki sposobu pracy — bez limitów `work`, reguł `autonomy.triage` i składania fabryki. Operacje autonomii
# może tylko zaostrzyć (sprawdza guard_bash przy składaniu warstw), a domyślny tryb zadania musi być w
# `task.allowed_modes` wyższych warstw (firma, zespół, projekt).
PERSON_REL = CONFIG_REL / "me.yaml"
PERSON_KEYS = {"task": ("default_mode",), "loop": ("blocked_slices", "confirm_each_slice"), "autonomy": ("operations",)}
TASK_MODES = ("plan", "normal", "auto")


def preferences_path() -> Path:
    """Preferencje osoby wspólne dla wszystkich jej projektów; `TF_PREFERENCES` podmienia ścieżkę (testy)."""
    return Path(os.environ.get("TF_PREFERENCES") or Path.home() / ".tf" / "preferences.yaml")


def _person_part(data: dict, warns: list[str], src: str) -> dict:
    out: dict = {}
    for k, v in (data or {}).items():
        if k == "style":
            continue
        if k not in PERSON_KEYS or not isinstance(v, dict):
            warns.append(f"{src}: `{k}` — tego osoba nie ustawia (dozwolone: style, "
                         f"{', '.join(f'{s}.{x}' for s, xs in PERSON_KEYS.items() for x in xs)}); pominięte")
            continue
        part = {x: v[x] for x in PERSON_KEYS[k] if x in v}
        for x in sorted(set(v) - set(PERSON_KEYS[k])):
            warns.append(f"{src}: `{k}.{x}` — tego osoba nie ustawia; pominięte")
        if part:
            out[k] = part
    return out


def person_layer(root: Path, below: dict) -> tuple[dict, list[str], list[str]]:
    """Warstwa osoby: `~/.tf/preferences.yaml` ← `.tf/config/me.yaml`, styl rozwinięty do wartości przełączników
    (`styles` w konfiguracji silnika), potem wartości podane wprost. Zwraca (warstwa, ostrzeżenia, źródła)."""
    warns: list[str] = []
    raw, sources = {}, []
    for path, label in ((preferences_path(), "~/.tf/preferences.yaml"), (root / PERSON_REL, PERSON_REL.as_posix())):
        try:
            data = load_yaml(path) if path.is_file() else None
        except Exception as e:  # noqa: BLE001 — zły plik osoby nie psuje konfiguracji; zostaje ostrzeżenie
            warns.append(f"{label}: nie da się odczytać ({e})")
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
            preset = {k: v for k, v in (styles[style] or {}).items() if k != "claude"}   # claude: tf style, nie konfiguracja
            out = deep_merge(_person_part(preset, warns, f"styles.{style}"), {})
            out["style"] = style
        else:
            warns.append(f"nieznany styl „{style}” (są: {', '.join(styles) or 'brak'}); pominięty")
    out = deep_merge(out, raw)
    allowed = (below.get("task") or {}).get("allowed_modes") or list(TASK_MODES)
    mode = (out.get("task") or {}).get("default_mode")
    if mode is not None and (mode not in TASK_MODES or mode not in allowed):
        warns.append(f"task.default_mode: {mode} — poza task.allowed_modes ({', '.join(allowed)}) ustawionym wyżej; "
                     "zostaje wartość firmy, zespołu albo projektu")
        out["task"].pop("default_mode")
        if not out["task"]:
            out.pop("task")
    return out, warns, sources


LOCAL_SETTINGS_REL = Path(".claude") / "settings.local.json"
STYLE_MARK = "style_permission_mode"   # w .claude/factory-settings.json: co ustawił styl i co było przedtem


def apply_style_permissions(root: Path) -> list[str]:
    """Tryb uprawnień Claude Code ze stylu pracy (`styles.<styl>.claude.permission_mode`) w `.claude/settings.local.json`
    projektu. Ustawia go tylko w miejsce domyślnego (`default` albo brak) albo wcześniej ustawionego przez styl — trybu
    wybranego przez człowieka nie nadpisuje. Styl bez trybu oddaje to, co było przed nim. Zwraca komunikaty."""
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
        return [f"{LOCAL_SETTINGS_REL.as_posix()}: niepoprawny JSON — trybu uprawnień stylu nie zmieniam"]
    marks = marks if isinstance(marks, dict) else {}
    mark = marks.get(STYLE_MARK) if isinstance(marks.get(STYLE_MARK), dict) else None
    perms = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
    cur = perms.get("defaultMode")
    msgs: list[str] = []
    if mark and cur != mark.get("mode"):
        mark = None                      # człowiek zmienił tryb po stylu — jego wybór, styl go już nie oddaje
    if want:
        if cur == want:
            return msgs
        if mark is None and cur not in (None, "default"):
            msgs = [f"tryb uprawnień Claude Code zostaje `{cur}` (wybrany przez Ciebie w {LOCAL_SETTINGS_REL.as_posix()}); "
                    f"styl {style} ustawiłby `{want}` — zmień go sam, jeśli chcesz"]
            if STYLE_MARK in marks:
                marks.pop(STYLE_MARK)
                mark_path.write_text(json.dumps(marks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            return msgs
        previous = mark.get("previous") if mark else cur
        perms["defaultMode"] = want
        mark = {"mode": want, "previous": previous}
        msgs.append(f"tryb uprawnień Claude Code: `{want}` w {LOCAL_SETTINGS_REL.as_posix()} (styl {style}); działa od "
                    "następnej sesji Claude Code")
    elif mark or STYLE_MARK in marks:
        if mark:
            if mark.get("previous") is None:
                perms.pop("defaultMode", None)
            else:
                perms["defaultMode"] = mark["previous"]
            msgs.append(f"tryb uprawnień Claude Code przywrócony: `{mark.get('previous') or 'domyślny'}` "
                        f"(działa od następnej sesji)")
        mark = None
    else:
        return msgs
    if msgs:                             # zmieniony tryb — zapis ustawień Claude Code (reszta pliku bez zmian)
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
    """Sposób pracy po złożeniu warstw: styl, domyślny i dozwolone tryby zadania, przełączniki pętli, ostrzeżenia."""
    cfg = load_config(root)
    below: dict = {}
    lower = [lv for lv in config_layers(root) if not lv[0].endswith("(osoba)")]
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
    """Domyślne karty operacyjnej z nakładki firmowej, nadpisane przez nakładkę zespołu (dziś: `tracker`). Adresu
    trackera (`url`) żadna nie ustawia — dokąd idzie token, mówi tylko zmienna JIRA_BASE_URL (skill tf, intake.py)."""
    tracker: dict = {}
    for key in ("org_defaults", "team_defaults"):
        ops = org_defaults(root, key)[1].get("operations") or {}
        if isinstance(ops.get("tracker"), dict):
            # prefiksy zespołu zastępują prefiksy firmy (klucze zgłoszeń zespołu), reszta pól się scala
            tracker = {**deep_merge(tracker, ops["tracker"]),
                       **({"prefixes": ops["tracker"]["prefixes"]} if "prefixes" in ops["tracker"] else {})}
    return {"tracker": {k: v for k, v in tracker.items() if k != "url"}} if tracker else {}


def load_config(root: Path) -> dict:
    """Konfiguracja rdzenia: silnik (`.tf/factory/config.yaml`) ← domyślne organizacji (nakładka firmowa) ←
    nadpisania projektu (`.tf/config/config.yaml`) ← preferencje osoby (styl pracy)."""
    cfg: dict = {}
    layers = config_layers(root)
    for _label, layer in layers:
        cfg = deep_merge(cfg, layer)
    if layers:
        cfg.setdefault("task", {})["allowed_modes"] = narrowed_modes([lv for lv in layers if not lv[0].endswith("(osoba)")])
    return cfg


def installed_packs(root: Path) -> dict[str, dict]:
    """Nakładki zainstalowane w projekcie: id → dane pack.yaml (+ `_dir`)."""
    out: dict[str, dict] = {}
    base = root / PACKS_REL
    for p in sorted(base.glob("*/pack.yaml")) if base.is_dir() else []:
        data = load_yaml(p)
        data["_dir"] = p.parent
        out[data.get("id") or p.parent.name] = data
    return out


def load_settings(root: Path, cfg: dict) -> dict:
    """Ustawienia projektu z domyślnymi wartościami rdzenia."""
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
    """Usuwa klucze z ustawień projektu (np. dawne `language`, `commit_language`). True, gdy coś zmieniono."""
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
    """Czy wkład nakładki działa przy tych ustawieniach (`contributes_when`)."""
    cond = pack.get("contributes_when") or {}
    return all(settings.get(k) == v for k, v in cond.items())


def _union(a, b) -> list:
    return list(dict.fromkeys([*(a or []), *(b or [])]))


def compose(root: Path, cfg: dict) -> dict:
    """Konfiguracja rdzenia (`cfg`) uzupełniona o zainstalowane nakładki i ustawienia projektu. Błędy składania
    trafiają do `_errors` (zgłasza je `build.py check`)."""
    cfg = dict(cfg)
    packs = installed_packs(root)
    settings = load_settings(root, cfg)
    errors: list[str] = []
    cfg["_packs"], cfg["_settings"] = packs, settings
    for key, kind in (("org_defaults", "firmowa"), ("team_defaults", "zespołu")):
        owners = [pid for pid, p in packs.items() if p.get(key) is not None]
        if len(owners) > 1:
            errors.append(f"{key}: {' i '.join(owners)} — w projekcie może być tylko jedna nakładka {kind} "
                          f"(działa {owners[0]})")
        if key == "team_defaults" and owners and not any(p.get("org_defaults") is not None for p in packs.values()):
            errors.append(f"{owners[0]}: nakładka zespołu bez nakładki firmowej — zainstaluj pack-<firma> "
                          "(requires.packs w pack.yaml zespołu)")
        for pid in owners[:1]:
            od = packs[pid][key]
            if not isinstance(od, dict):
                errors.append(f"{pid}: {key} musi być słownikiem (config, operations)")
                continue
            for k in sorted(set(od) - {"config", "operations"}):
                errors.append(f"{pid}: {key}.{k} — nieznana sekcja (są: config, operations)")
            for k in sorted(set(od.get("config") or {}) - set(ORG_CONFIG_KEYS)):
                errors.append(f"{pid}: {key}.config.{k} — tego klucza nakładka {kind} nie ustawia "
                              f"(dozwolone: {', '.join(ORG_CONFIG_KEYS)}); wartość pominięta")
            for k in sorted(set(od.get("operations") or {}) - set(ORG_OPERATIONS_KEYS)):
                errors.append(f"{pid}: {key}.operations.{k} — nieznana sekcja (jest: tracker); wartość pominięta")
    cfg["_active"] = {pid for pid, p in packs.items() if active(p, settings)}

    facets = [dict(f, _pack="core") for f in cfg.get("facets") or []]
    for pid, p in packs.items():
        facets += [dict(f, _pack=pid) for f in p.get("facets") or []]
    seen: dict[str, str] = {}
    for f in facets:
        if f["prefix"] in seen:
            errors.append(f"wymiar {f['prefix']}: zdefiniowany w {seen[f['prefix']]} i w {f['_pack']}")
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
                errors.append(f"agent wspólny {n}: zdefiniowany w {cfg['shared_agents'][n]['_pack']} i w {pid}")
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
    # wkład do agentów (także tych z nakładek): skille i akapit promptu
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
    """Nakładki opcjonalne tej nakładki, których nie zainstalowano."""
    return [o for o in (pack or {}).get("optional_packs") or [] if o not in packs]


def load_items(root: Path, sub: str) -> tuple[dict[str, dict], list[str]]:
    """Role albo persony: z nakładek i własne projektu (własne nadpisują nakładkę). Zwraca (elementy, ostrzeżenia)."""
    items: dict[str, dict] = {}
    notes: list[str] = []
    for pid, p in installed_packs(root).items():
        for f in sorted((p["_dir"] / sub).glob("*.yaml")):
            data = load_yaml(f)
            data["_src"] = f.relative_to(root).as_posix()
            data["_pack"] = pid
            if data.get("name") in items:
                notes.append(f"{sub} {data['name']}: w {items[data['name']]['_pack']} i w {pid} — używam {pid}")
            items[data["name"]] = data
    for f in sorted((root / CONFIG_REL / sub).glob("*.yaml")):
        data = load_yaml(f)
        data["_src"] = (CONFIG_REL / sub / f.name).as_posix()
        data["_pack"] = "project"
        if data.get("name") in items:
            notes.append(f"{sub} {data['name']}: własna wersja projektu zastępuje wersję z {items[data['name']]['_pack']}")
        items[data["name"]] = data
    return items, notes


def load_traits(root: Path) -> dict[str, str]:
    out = {p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((root / ENGINE_REL / "traits").glob("*.md"))}
    for p in installed_packs(root).values():
        out.update({t.stem: t.read_text(encoding="utf-8").strip() for t in sorted((p["_dir"] / "traits").glob("*.md"))})
    out.update({p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((root / CONFIG_REL / "traits").glob("*.md"))})
    return out


MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"


# Język commitów repozytorium bez modelu: tematy ostatnich commitów (bez przedrostka Conventional Commits).
PL_CHARS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
PL_WORDS = {"i", "w", "na", "z", "dla", "nie", "oraz", "przez", "bez", "dodaj", "dodano", "popraw", "poprawka",
            "poprawki", "zmiana", "zmiany", "nowy", "nowa", "nowe", "aktualizacja", "przenieś", "usuń", "obsługa"}
EN_WORDS = {"the", "and", "for", "of", "in", "with", "from", "into", "add", "adds", "added", "fix", "fixes", "fixed",
            "update", "updates", "remove", "removes", "use", "when", "by", "new", "move", "handle", "support"}
CC_PREFIX = re.compile(r"^[a-z]+(\([^)]*\))?!?:\s*")


_COMMIT_LANG: dict = {}


def commit_language(root: Path, last: int = 50) -> str | None:
    """`pl`, `en`, `mixed` (brak wyraźnej przewagi) albo None (brak gita lub commitów — nowe repozytorium).
    Wynik zapamiętany na proces — build wywołuje to raz na agenta."""
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
    if pl + en == 0 or min(pl, en) * 3 > max(pl, en):   # mniej niż 3:1 — bez rozstrzygnięcia
        return "mixed"
    return "pl" if pl > en else "en"


def language_lines(cfg: dict, root: Path) -> list[str]:
    """Sekcja „Język”: reguła rozmowy (stała), język commitów z `git log`, język kodu."""
    cl = cfg.get("commit_language") or {}
    found = commit_language(root)
    code = found or cl.get("new_repo", "en")
    commits = cl.get(code) or cl.get("mixed")
    if commits:   # skąd ten język — człowiek widzi, że to nie ustawienie
        commits = commits.rstrip(".") + (" (jak dotychczasowe commity, `git log`)." if found else
                                         " (nowe repozytorium bez commitów; potem język historii z `git log`).")
    lines = [cfg.get("language_note"), commits, cfg.get("code_language_note")]
    return [f"- {' '.join(str(x).split())}" for x in lines if x]


def write_language_lines(path: Path, cfg: dict, root: Path) -> bool:
    """Podmienia podsekcję „### Język” w bloku fabryki w CLAUDE.md / CLAUDE.local.md. Zwraca True, gdy zmieniono."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if MARK_BEGIN not in text or MARK_END not in text:
        return False
    a, b = text.index(MARK_BEGIN), text.index(MARK_END)
    block = text[a:b]
    body = "### Język\n" + "\n".join(language_lines(cfg, root)) + "\n"
    if "### Język\n" in block:
        i = block.index("### Język\n")
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
