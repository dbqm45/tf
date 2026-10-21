#!/usr/bin/env python3
"""
Migracje rdzenia — autokorekta plików projektu po zmianach w publicznym API fabryki (factory/PUBLIC_API.md).

  python3 factory/migrations.py            # pokaż, co trzeba poprawić (nic nie zmienia)
  python3 factory/migrations.py --apply    # popraw

Uruchamiają je instalator (po każdej aktualizacji) i `tf doctor --fix`. Poprawiane są tylko pliki projektu, których
fabryka nie instalowała: własne persony i role (`factory/personas/`, `factory/roles/`), własne nakładki
(`factory/packs/<id>/` spoza manifestu) i własne skille (`.claude/skills/<skill>/SKILL.md` spoza manifestu).
Pliki fabryki aktualizuje instalator. Tylko biblioteka standardowa.

Nowa zmiana nazwy w rdzeniu lub nakładce = nowy wpis w RENAMES (z wersją rdzenia, od której obowiązuje).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# wersja rdzenia → stara nazwa → nowa nazwa (skille, cechy, role)
RENAMES: dict[str, dict[str, str]] = {
    "3.0.0": {
        "core-tech-docs": "docs-tech-writing",          # pack-docs
        "fe-ux-design": "ux-feature-design",            # pack-ux
        "core-knowledge-base": "dom-ev-knowledge-base",  # pack-ev
    },
    "5.0.0": {
        "core-story-run": "talos-story-run",            # mode-talos
    },
}


def factory_files(root: Path) -> set[str]:
    try:
        return set(json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("files") or {})
    except (OSError, ValueError):
        return set()


def own_files(root: Path) -> list[Path]:
    """Pliki projektu, które mogą odwoływać się do nazw fabryki, a których fabryka nie instaluje."""
    installed = factory_files(root)
    cands = [*(root / "factory" / "personas").glob("*.yaml"), *(root / "factory" / "roles").glob("*.yaml"),
             *(root / "factory" / "packs").glob("*/**/*.yaml"), *(root / ".claude" / "skills").glob("*/SKILL.md")]
    return [p for p in cands if p.is_file() and p.relative_to(root).as_posix() not in installed]


def apply(root: Path = ROOT, dry: bool = True) -> list[str]:
    """Zmiany nazw w plikach projektu. Zwraca opis zmian (przy dry=True — zmian do zrobienia)."""
    mapping = {old: new for table in RENAMES.values() for old, new in table.items()}
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, mapping)) + r")\b")
    out = []
    for p in own_files(root):
        text = p.read_text(encoding="utf-8")
        hits = sorted(set(pattern.findall(text)))
        if not hits:
            continue
        out.append(f"{p.relative_to(root).as_posix()}: " + ", ".join(f"{h} → {mapping[h]}" for h in hits))
        if not dry:
            p.write_text(pattern.sub(lambda m: mapping[m.group(1)], text), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    changes = apply(ROOT, dry="--apply" not in argv)
    for c in changes:
        print(("✓ " if "--apply" in argv else "⚠ ") + c)
    if not changes:
        print("✓ Nothing to migrate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
