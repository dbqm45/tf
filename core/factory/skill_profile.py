#!/usr/bin/env python3
"""
Dopasowuje widoczność opisów skilli fabryki do projektu (ustawienie Claude Code `skillOverrides`).

  python3 factory/skill_profile.py              # zastosuj w bieżącym projekcie
  python3 factory/skill_profile.py --dry-run    # pokaż plan, nic nie zapisuj
  python3 factory/skill_profile.py <projekt>
  python3 factory/skill_profile.py --describe ux-,sec-   # w tym projekcie te wymiary z opisem (zapamiętane w manifeście)

Po co: Claude Code trzyma listę skilli w budżecie ~1% okna kontekstu; po przepełnieniu usuwa opisy najrzadziej
używanych skilli, więc każdy nowy skill wypychałby opisy innych. Tu opis na liście dostają skille potrzebne w tym
projekcie, a reszta jest widoczna jako sama nazwa (`name-only`) — model nadal może je wywołać, a hook `skill_hint`
podpowiada je z opisem, gdy polecenie ich dotyczy. Reguły:
  - technologie (`fw-`, `lang-`, `tool-`): opis tylko dla wykrytych przez `.claude/hooks/detect_stack.py`
    (gdy wykrywanie nie zadziała — wszystkie z opisem, jak dotąd);
  - wiedza branżowa (`dom-`), wymiary specjalistyczne (`sec-`, `ai-`, `ux-` — persony znają je ze swojego promptu)
    i skille oznaczone przez autora `metadata.widocznosc: nazwa`: sama nazwa, chyba że projekt włączy wymiar
    przez `--describe` (np. zespół UX pracuje nimi na co dzień);
  - pozostałe skille fabryki: opis.
Zmieniane są tylko wpisy, które zapisała fabryka (pamięta je manifest, klucz `skill_overrides`). Twoje ustawienia
w `skillOverrides` — także usunięcie wpisu fabryki — mają pierwszeństwo. Własnych skilli ani skilli uruchamianych
tylko ręcznie (`disable-model-invocation: true`) skrypt nie dotyka. Zapis: `.claude/settings.local.json`.
Uruchamiają go instalacja i aktualizacja; ręcznie — po zmianie stacku. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

STACK_PREFIXES = ("fw-", "lang-", "tool-")
NAME_ONLY_PREFIXES = ("dom-", "sec-", "ai-", "ux-")
MANIFEST = Path(".claude") / "factory-manifest.json"
SETTINGS = Path(".claude") / "settings.local.json"


def desired(name: str, stack: set[str] | None, marked: bool = False, describe: tuple[str, ...] = ()) -> str:
    """Widoczność skilla: "on" (nazwa i opis) albo "name-only". `stack=None` — stack nieznany;
    `marked` — autor oznaczył skill `metadata.widocznosc: nazwa` (rzadko potrzebny, znajduje go skill_hint);
    `describe` — prefiksy wymiarów, które projekt chce mieć z opisem."""
    if describe and name.startswith(tuple(describe)):
        return "on"
    if marked or name.startswith(NAME_ONLY_PREFIXES):
        return "name-only"
    if name.startswith(STACK_PREFIXES) and stack is not None and name not in stack:
        return "name-only"
    return "on"


def plan(settings: dict, want: dict[str, str], managed: dict[str, str]) -> tuple[dict, dict[str, str], list[str]]:
    """Nowe ustawienia, nowy zapis fabryki (tylko wartości ≠ "on") i lista skilli z ręcznym ustawieniem użytkownika."""
    out = dict(settings)
    ov = dict(settings.get("skillOverrides") or {})
    new_managed, kept = {}, []
    for name in sorted(set(want) | set(managed)):
        cur, ours = ov.get(name, "on"), managed.get(name, "on")
        if cur != ours:                                   # ktoś zmienił wpis fabryki albo ustawił własny
            kept.append(name)
            if ours != "on":
                new_managed[name] = ours
            continue
        target = want.get(name, "on")                     # skill usunięty z fabryki → wpis fabryki znika
        if target == "on":
            ov.pop(name, None)
        else:
            ov[name] = target
            new_managed[name] = target
    if ov:
        out["skillOverrides"] = ov
    else:
        out.pop("skillOverrides", None)
    return out, new_managed, [k for k in kept if k in want]


def _front(skill_md: Path) -> str:
    return skill_md.read_text(encoding="utf-8", errors="replace").split("\n---", 1)[0]


def manual_only(skill_md: Path) -> bool:
    return bool(re.search(r"^disable-model-invocation:\s*true\s*$", _front(skill_md), re.M))


def marked_name_only(skill_md: Path) -> bool:
    return bool(re.search(r"^\s+widocznosc:\s*[\"']?nazwa[\"']?\s*$", _front(skill_md), re.M))


def factory_skills(root: Path, manifest: dict) -> list[str]:
    """Skille fabryki w projekcie (z manifestu); bez manifestu — wszystkie skille w .claude/skills (repo fabryki)."""
    files = manifest.get("files")
    if files:
        names = {m.group(1) for f in files if (m := re.match(r"\.claude/skills/([^/]+)/SKILL\.md$", f))}
    else:
        names = {p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md")}
    return sorted(n for n in names if (root / ".claude" / "skills" / n / "SKILL.md").is_file()
                  and not manual_only(root / ".claude" / "skills" / n / "SKILL.md"))


def detect_stack(root: Path) -> set[str] | None:
    """Skille technologii wykryte w projekcie; None, gdy wykrywania nie da się uruchomić."""
    path = root / ".claude" / "hooks" / "detect_stack.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("ctf_detect_stack", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return set(mod.analyze(root).get("suggested_stack") or [])
    except Exception:                                    # błąd wykrywania nie może zepsuć instalacji
        return None


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError:
        return {}


def apply(root: Path, dry: bool = False, describe: list[str] | None = None) -> dict:
    """`describe=None` — wymiary z opisem z manifestu (`skill_describe`); lista — nowa wartość do zapamiętania."""
    root = root.resolve()
    man_p, set_p = root / MANIFEST, root / SETTINGS
    manifest, settings = read_json(man_p), read_json(set_p)
    if describe is None:
        describe = manifest.get("skill_describe") or []
    stack = detect_stack(root)
    skills_dir = root / ".claude" / "skills"
    want = {n: desired(n, stack, marked_name_only(skills_dir / n / "SKILL.md"), tuple(describe))
            for n in factory_skills(root, manifest)}
    new_settings, managed, kept = plan(settings, want, manifest.get("skill_overrides") or {})
    hidden = sorted(n for n, v in want.items() if v == "name-only")
    if not dry:
        if new_settings != settings:
            set_p.parent.mkdir(parents=True, exist_ok=True)
            set_p.write_text(json.dumps(new_settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if man_p.exists() and (manifest.get("skill_overrides", {}) != managed
                               or (manifest.get("skill_describe") or []) != describe):
            manifest["skill_overrides"] = managed
            if describe:
                manifest["skill_describe"] = describe
            else:
                manifest.pop("skill_describe", None)
            man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"skills": len(want), "with_description": len(want) - len(hidden), "name_only": hidden, "user_kept": kept,
            "stack": sorted(stack) if stack is not None else None}


def summary(res: dict, dry: bool) -> str:
    stack = ", ".join(res["stack"]) if res["stack"] else ("nic nie wykryto" if res["stack"] is not None
                                                          else "nieznany — technologie zostają z opisem")
    lines = [f"{'Plan' if dry else 'ℹ'} widoczności skilli: z opisem {res['with_description']}, sama nazwa "
             f"{len(res['name_only'])} (stack: {stack})."]
    if dry and res["name_only"]:
        lines.append("  sama nazwa: " + ", ".join(res["name_only"]))
    if res["user_kept"]:
        lines.append("  Twoje ustawienia zostały: " + ", ".join(res["user_kept"]))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    args, describe, it = [], None, iter(argv[1:])
    for a in it:
        if a == "--describe":
            describe = [p.strip() for p in next(it, "").split(",") if p.strip()]
        elif not a.startswith("-"):
            args.append(a)
    dry = "--dry-run" in argv
    res = apply(Path(args[0]) if args else Path.cwd(), dry, describe)
    print(summary(res, dry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
