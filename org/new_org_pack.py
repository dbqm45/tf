#!/usr/bin/env python3
"""
Company overlay from the `org/template/` template — one organization's standards and default settings for all its projects.
You run it once per company, in a clone of the factory repository; the output lands outside it, in the company repository.

  python3 org/new_org_pack.py <company> --out <dir> [--prefix p-] [--title "Company name"]
  python3 org/new_org_pack.py <company> --team <team> --out <dir> [--prefix p-] [--title "Team name"]

  <company>  id of the pack-<company> overlay: lowercase letters, digits and "-" (e.g. acme)
  --out      output directory, outside the factory repository; must not exist
  --prefix   prefix of the company's skills (default <company>-); must not be taken by the core or a factory overlay
  --title    company name in the texts (default derived from <company>)
  --team     team overlay pack-<company>-<team> (template `org/template-team/` for pack.yaml and README.md, the rest
             from `org/template/`): team standards on top of the company overlay pack-<company>, which it requires; skill prefix
             defaults to <team>-

Fields to fill in are marked TODO; description of each field and further steps: org/README.md and README.md in the output.
Standard library only.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "template"
TEAM_TEMPLATE = Path(__file__).resolve().parent / "template-team"     # pack.yaml and README.md of the team overlay


def taken_prefixes() -> dict[str, str]:
    """Prefixes of the factory's core, overlay and mode dimensions → owner (matching `prefix: x-`)."""
    out: dict[str, str] = {}
    files = [ROOT / "core" / "factory" / "config.yaml", *sorted(ROOT.glob("packs/*/pack.yaml")),
             *sorted(ROOT.glob("modes/*/pack.yaml"))]
    for f in files:
        if f.is_file():
            for p in re.findall(r"prefix:\s*([a-z0-9]+-)", f.read_text(encoding="utf-8")):
                out.setdefault(p, f.parent.name)
    return out


def main(argv: list[str]) -> int:
    args, opts = [], {"out": None, "prefix": None, "title": None, "team": None}
    it = iter(argv)
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a.startswith("--") and a[2:] in opts:
            opts[a[2:]] = next(it, "")
        else:
            args.append(a)
    org = args[0] if args else ""
    team = opts["team"]
    name = f"{org}-{team}" if team else org
    prefix = opts["prefix"] or f"{team or org}-"
    title = opts["title"] or name.replace("-", " ").title()
    out = Path(opts["out"]).expanduser().resolve() if opts["out"] else None
    problems = []
    if not re.fullmatch(r"[a-z][a-z0-9-]*[a-z0-9]", org):
        problems.append(f"name: lowercase letters, digits and '-' (got {org!r})")
    if team is not None and not re.fullmatch(r"[a-z][a-z0-9-]*[a-z0-9]", team):
        problems.append(f"team: lowercase letters, digits and '-' (got {team!r})")
    if not re.fullmatch(r"[a-z][a-z0-9]*-", prefix):
        problems.append(f"prefix must look like 'abc-' (got {prefix!r})")
    elif prefix in (taken := taken_prefixes()):
        problems.append(f"prefix {prefix} is already used by {taken[prefix]}")
    if any(c in title for c in '"\n\\'):
        problems.append("title must not contain quotes, backslashes or new lines")
    if (ROOT / "packs" / f"pack-{name}").exists():
        problems.append(f"pack-{name} is a factory pack id — choose another name")
    if out is None:
        problems.append("--out <directory> is required: the company pack lives in the company's repository")
    elif out == ROOT or ROOT in out.parents:
        problems.append(f"{out} is inside the factory repository — the company pack lives outside it")
    elif out.exists():
        problems.append(f"{out} already exists — nothing overwritten")
    if problems:
        print("✗ " + "\n✗ ".join(problems), file=sys.stderr)
        return 2
    version = (ROOT / "core" / "factory" / "VERSION").read_text(encoding="utf-8").strip()
    subst = {"{{COMPANY_UP}}": name.replace("-", "").upper()[:8], "{{COMPANY}}": name, "{{ORG}}": org, "{{PREFIX}}": prefix,
             "{{TITLE}}": title, "{{CORE_RANGE}}": f">={version} <{int(version.split('.')[0]) + 1}.0.0",
             "{{REVIEW}}": (datetime.date.today() + datetime.timedelta(days=365)).isoformat()}

    def fill(s: str) -> str:
        for k, v in subst.items():
            s = s.replace(k, v)
        return s

    written = []
    for src in sorted(f for f in TEMPLATE.rglob("*") if f.is_file()):
        rel_src = src.relative_to(TEMPLATE)
        if team and (TEAM_TEMPLATE / rel_src).is_file():
            src = TEAM_TEMPLATE / rel_src          # the team's pack.yaml and README.md
        rel = fill(rel_src.as_posix())
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = fill(src.read_text(encoding="utf-8"))
        if team and rel_src.name == "SKILL.md":   # skill description: team rules on top of the company standards
            text = re.sub(r"^description: .*$", f"description: Use for {title} team rules on top of the company "
                          f"standards ({org}-standards) — who approves, thresholds, bans and exceptions that apply in the team.",
                          text, count=1, flags=re.M)
        dst.write_text(text, encoding="utf-8")
        written.append(rel)
    print(f"✓ {out}: {len(written)} files")
    if team:
        print(f"""Next (README.md in the team pack, org/README.md):
  1. Fill in the TODO fields: grep -rn TODO {out}
  2. Check: python3 tools/workspace.py check --packs pack-it,pack-{org},pack-{name} --pack-dir <company repo> --pack-dir {out}
  3. Publish {out} as the team's git repository (tags vX.Y.Z)
  4. Team project: tf install --pack-dir <company repo> --pack-dir <team repo> --add pack-{name}""")
        return 0
    print(f"""Next (org/README.md, README.md in the pack):
  1. Fill in the TODO fields: grep -rn TODO {out}
  2. Check: python3 tools/workspace.py check --packs pack-it,pack-{name} --pack-dir {out}
  3. Publish {out} as the company's git repository (tags vX.Y.Z)
  4. Project: tf install --pack-dir <company repository> --add pack-{name}""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
