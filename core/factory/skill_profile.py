#!/usr/bin/env python3
"""
Adjusts the visibility of factory skill descriptions to the project (the Claude Code `skillOverrides` setting).

  python3 .tf/factory/skill_profile.py              # apply in the current project
  python3 .tf/factory/skill_profile.py --dry-run    # show the plan, write nothing
  python3 .tf/factory/skill_profile.py <project>
  python3 .tf/factory/skill_profile.py --describe ux-,sec-   # in this project these dimensions with a description (remembered in the manifest)

Why: Claude Code keeps the skill list in a budget of ~1% of the context window; on overflow it removes the descriptions of the least
used skills, so every new skill would push out the descriptions of others. Here the skills needed in this
project get a description in the list, and the rest is visible as the name only (`name-only`) — the model can still call them, and the `skill_hint` hook
suggests them with a description when the command concerns them. Rules:
  - technologies (`fw-`, `lang-`, `tool-`): description only for those detected by `.claude/hooks/detect_stack.py`
    (when detection fails — all with a description, as before);
  - specialist dimensions indicated by overlays (`skill_visibility.name_only_prefixes` in pack.yaml, e.g. `sec-`,
    `ai-`, `ux-` — personas know them from their prompt) and skills marked by the author `metadata.visibility: name`:
    the name only, unless the project enables a dimension via `--describe` (e.g. a UX team works with them daily);
  - the remaining factory skills: description.
Only the entries the factory wrote are changed (the manifest remembers them, key `skill_overrides`). Your settings
in `skillOverrides` — including removal of a factory entry — take precedence. The script does not touch your own skills or skills run
manually only (`disable-model-invocation: true`). Written to: `.claude/settings.local.json`.
The installer and update run it; manually — after a stack change. Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

STACK_PREFIXES = ("fw-", "lang-", "tool-")
NAME_ONLY_PREFIXES: tuple[str, ...] = ()   # core: none; overlays add their own (name_only_prefixes)


def pack_name_only(root: Path) -> tuple[str, ...]:
    """“Name only” prefixes from installed overlays (.tf/factory/packs.py)."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_sp", root / ".tf" / "factory" / "packs.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cfg = mod.compose(root, mod.load_config(root))
        return tuple(cfg["skill_visibility"]["name_only_prefixes"])
    except Exception:  # no factory in the project or a broken pack.yaml — no overlay prefixes
        return ()
MANIFEST = Path(".claude") / "factory-manifest.json"
SETTINGS = Path(".claude") / "settings.local.json"


def desired(name: str, stack: set[str] | None, marked: bool = False, describe: tuple[str, ...] = (),
            name_only: tuple[str, ...] = NAME_ONLY_PREFIXES) -> str:
    """Skill visibility: "on" (name and description) or "name-only". `stack=None` — stack unknown;
    `marked` — the author marked the skill `metadata.visibility: name` (rarely needed, skill_hint finds it);
    `describe` — dimension prefixes the project wants with a description."""
    if describe and name.startswith(tuple(describe)):
        return "on"
    if marked or (name_only and name.startswith(name_only)):
        return "name-only"
    if name.startswith(STACK_PREFIXES) and stack is not None and name not in stack:
        return "name-only"
    return "on"


def plan(settings: dict, want: dict[str, str], managed: dict[str, str]) -> tuple[dict, dict[str, str], list[str]]:
    """New settings, the new factory record (only values ≠ "on") and the list of skills with a manual user setting."""
    out = dict(settings)
    ov = dict(settings.get("skillOverrides") or {})
    new_managed, kept = {}, []
    for name in sorted(set(want) | set(managed)):
        cur, ours = ov.get(name, "on"), managed.get(name, "on")
        if cur != ours:                                   # someone changed the factory entry or set their own
            kept.append(name)
            if ours != "on":
                new_managed[name] = ours
            continue
        target = want.get(name, "on")                     # skill removed from the factory → the factory entry disappears
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
    return bool(re.search(r"^\s+visibility:\s*[\"']?name[\"']?\s*$", _front(skill_md), re.M))


def factory_skills(root: Path, manifest: dict) -> list[str]:
    """Factory skills in the project (from the manifest); without a manifest — all skills in .claude/skills (the factory repo)."""
    files = manifest.get("files")
    if files:
        names = {m.group(1) for f in files if (m := re.match(r"\.claude/skills/([^/]+)/SKILL\.md$", f))}
    else:
        names = {p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md")}
    return sorted(n for n in names if (root / ".claude" / "skills" / n / "SKILL.md").is_file()
                  and not manual_only(root / ".claude" / "skills" / n / "SKILL.md"))


def detect_stack(root: Path) -> set[str] | None:
    """Technology skills detected in the project; None when detection cannot be run."""
    path = root / ".claude" / "hooks" / "detect_stack.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("ctf_detect_stack", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return set(mod.analyze(root).get("suggested_stack") or [])
    except Exception:                                    # a detection error must not break the installation
        return None


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except ValueError:
        return {}


def apply(root: Path, dry: bool = False, describe: list[str] | None = None) -> dict:
    """`describe=None` — dimensions with a description from the manifest (`skill_describe`); a list — the new value to remember."""
    root = root.resolve()
    man_p, set_p = root / MANIFEST, root / SETTINGS
    manifest, settings = read_json(man_p), read_json(set_p)
    if describe is None:
        describe = manifest.get("skill_describe") or []
    stack = detect_stack(root)
    skills_dir = root / ".claude" / "skills"
    name_only = NAME_ONLY_PREFIXES + pack_name_only(root)
    want = {n: desired(n, stack, marked_name_only(skills_dir / n / "SKILL.md"), tuple(describe), name_only)
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
    stack = ", ".join(res["stack"]) if res["stack"] else ("nothing detected" if res["stack"] is not None
                                                          else "unknown — technology skills keep their description")
    lines = [f"{'Plan for' if dry else 'ℹ'} skill visibility: described {res['with_description']}, name only "
             f"{len(res['name_only'])} (stack: {stack})."]
    if dry and res["name_only"]:
        lines.append("  name only: " + ", ".join(res["name_only"]))
    if res["user_kept"]:
        lines.append("  your settings kept: " + ", ".join(res["user_kept"]))
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
