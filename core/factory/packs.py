#!/usr/bin/env python3
"""
Nakładki (pack-*) zainstalowane w projekcie i konfiguracja złożona z rdzenia i nakładek.

  python3 factory/packs.py              # zainstalowane nakładki i ustawienia projektu
  python3 factory/packs.py --json       # konfiguracja po złożeniu (do diagnostyki)

Układ w projekcie:
  factory/config.yaml                     konfiguracja rdzenia
  factory/traits/*.md                     cechy rdzenia (i własne cechy projektu)
  factory/roles/, factory/personas/       własne role i persony projektu (nadpisują te z nakładek o tej samej nazwie)
  factory/packs/<id>/pack.yaml            nakładka: wymiary, agenci, konsultanci, wkład do rdzenia i innych nakładek
  factory/packs/<id>/{roles,personas,traits}/
  .claude/skills/                         skille rdzenia i nakładek (Claude Code czyta je tylko stąd)
  .claude/factory-settings.json           ustawienia projektu: language, commit_language, targets

Zasady składania:
  - listy (wymiary, słownik, skille samodzielne, wiersze routingu) — rdzeń, potem nakładki w kolejności nazw;
  - wymiary sortowane po `order`; ten sam prefiks w dwóch miejscach to błąd;
  - `always_skills` nakładki trafiają tylko do jej person i wykonawców;
  - `contributes` (wkład do person, ról i agentów spoza nakładki) oraz agenci wspólni, konsultanci i wiersze routingu
    nakładki działają tylko wtedy, gdy spełniony jest `contributes_when` (np. `{language: pl}`);
  - odwołania do elementów nakładek z `optional_packs`, których nie zainstalowano, są pomijane bez błędu.
Biblioteka standardowa + PyYAML (systemowy albo dołączony w factory/_vendor).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # dołączona kopia PyYAML (licencja MIT, factory/_vendor/yaml/LICENSE)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

SETTINGS_REL = Path(".claude") / "factory-settings.json"
PACKS_REL = Path("factory") / "packs"
LIST_KEYS = ("traits", "core_skills", "skills")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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
    langs = cfg.get("languages") or {}
    lang = data.get("language") if data.get("language") in langs else cfg.get("default_language", "pl")
    commit = data.get("commit_language") if data.get("commit_language") in langs else cfg.get("default_commit_language", "en")
    targets = [t for t in (data.get("targets") or cfg.get("default_targets") or ["claude"]) if isinstance(t, str)]
    return {"language": lang, "commit_language": commit, "targets": targets}


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
    for f in sorted((root / "factory" / sub).glob("*.yaml")):
        data = load_yaml(f)
        data["_src"] = f"factory/{sub}/{f.name}"
        data["_pack"] = "project"
        if data.get("name") in items:
            notes.append(f"{sub} {data['name']}: własna wersja projektu zastępuje wersję z {items[data['name']]['_pack']}")
        items[data["name"]] = data
    return items, notes


def load_traits(root: Path) -> dict[str, str]:
    out = {p.stem: p.read_text(encoding="utf-8").strip() for p in sorted((root / "factory" / "traits").glob("*.md"))}
    for p in installed_packs(root).values():
        out.update({t.stem: t.read_text(encoding="utf-8").strip() for t in sorted((p["_dir"] / "traits").glob("*.md"))})
    return out


MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"


def language_lines(cfg: dict, settings: dict) -> list[str]:
    langs = cfg.get("languages") or {}
    lines = [(langs.get(settings.get("language")) or {}).get("work"),
             (langs.get(settings.get("commit_language")) or {}).get("commits"), cfg.get("code_language_note")]
    return [f"- {x.strip()}" for x in lines if x]


def write_language_lines(path: Path, cfg: dict, settings: dict) -> bool:
    """Podmienia podsekcję „### Język” w bloku fabryki w CLAUDE.md / CLAUDE.local.md. Zwraca True, gdy zmieniono."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if MARK_BEGIN not in text or MARK_END not in text:
        return False
    a, b = text.index(MARK_BEGIN), text.index(MARK_END)
    block = text[a:b]
    body = "### Język\n" + "\n".join(language_lines(cfg, settings)) + "\n"
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
    root = Path(__file__).resolve().parent.parent
    cfg = compose(root, load_yaml(root / "factory" / "config.yaml"))
    if "--json" in argv:
        print(json.dumps({k: v for k, v in cfg.items() if k != "_packs"}, ensure_ascii=False, indent=1, default=str))
        return 0
    s = cfg["_settings"]
    print(f"Language: {s['language']} · commit language: {s['commit_language']} · targets: {', '.join(s['targets'])}")
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
