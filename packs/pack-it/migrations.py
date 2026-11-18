"""Project data migrations of the pack-it overlay (called by the core `migrations.migrate_values` on update).

14.x: legacy dossier (`eng-legacy-dossier`) in English syntax — sections, finding and recommendation fields, `State:`,
the rules table. The name and value maps come from the skill (`dossier_check.ALIASES`, `VALUE_ALIASES`)."""
from __future__ import annotations

import re
from pathlib import Path


def _dossier_maps(root: Path) -> tuple[dict, dict] | None:
    """Dossier name and value maps from the installed eng-legacy-dossier skill (pack-it); without the skill — None."""
    f = root / ".claude" / "skills" / "eng-legacy-dossier" / "scripts" / "dossier_check.py"
    if not f.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_dossier_check", f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return dict(mod.ALIASES), dict(mod.VALUE_ALIASES)
    except Exception:   # noqa: BLE001 — a broken skill does not stop the update
        return None


def _dossier_text(text: str, names: dict, values: dict) -> str:
    """Dossier 14.x syntax: `##` headings, `Key: value` fields of ARCH/REC blocks, `State:`, the rules table."""
    out, section = [], ""
    for line in text.split("\n"):
        h = re.match(r"^## (.+?)\s*$", line)
        if h:
            section = names.get(h.group(1), h.group(1))
            out.append(f"## {section}")
            continue
        s = re.match(r"^Stan: (\S+)( — .*)$", line)
        if s:
            out.append(f"State: {values.get(s.group(1), s.group(1))}{s.group(2)}")
            continue
        f = re.match(r"^([^:|#\n][^:\n]*?):\s(.*)$", line)
        if f and f.group(1) in names and section in ("Findings", "Recommendations"):
            v = f.group(2).strip()
            v = values.get(v, v) if names[f.group(1)] in ("Category", "Decision") else f.group(2)
            out.append(f"{names[f.group(1)]}: {v}")
            continue
        if section == "Business rules" and line.strip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            if [c.strip() for c in cells[:4]] == ["ID", "Reguła", "Dowód", "Pewność"]:
                out.append("| ID | Rule | Evidence | Confidence |" + "|".join(cells[4:]) + ("|" if len(cells) > 4 else ""))
                continue
            if len(cells) >= 4 and cells[3].strip() in values:
                cells[3] = f" {values[cells[3].strip()]} "
                out.append("|" + "|".join(cells) + "|")
                continue
        out.append(line)
    return "\n".join(out)


def _dossiers(root: Path, dry: bool) -> list[str]:
    """Existing legacy dossiers (files with the `<!-- legacy-dossier` marker) in 14.x syntax."""
    maps = _dossier_maps(root)
    if maps is None:
        return []
    out = []
    for f in sorted((root / "docs" / "project").rglob("*.md")) if (root / "docs" / "project").is_dir() else []:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.startswith("<!-- legacy-dossier"):
            continue
        new = _dossier_text(text, *maps)
        if new != text:
            out.append(f.relative_to(root).as_posix())
            if not dry:
                f.write_text(new, encoding="utf-8")
    return out


def migrate_values(root: Path, dry: bool = True) -> list[str]:
    return _dossiers(root, dry)
