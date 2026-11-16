#!/usr/bin/env python3
"""
Nakładka firmowa z szablonu `org/template/` — standardy i domyślne ustawienia jednej organizacji dla wszystkich jej
projektów. Uruchamiasz raz na firmę, w klonie repozytorium fabryki; wynik ląduje poza nim, w repozytorium firmy.

  python3 org/new_org_pack.py <firma> --out <katalog> [--prefix p-] [--title "Nazwa firmy"]
  python3 org/new_org_pack.py <firma> --team <zespół> --out <katalog> [--prefix p-] [--title "Nazwa zespołu"]

  <firma>    id nakładki pack-<firma>: małe litery, cyfry i „-” (np. acme)
  --out      katalog wyniku, poza repozytorium fabryki; nie może istnieć
  --prefix   prefiks skilli firmy (domyślnie <firma>-); nie może być zajęty przez rdzeń ani nakładkę fabryki
  --title    nazwa firmy w tekstach (domyślnie z <firma>)
  --team     nakładka zespołu pack-<firma>-<zespół> (szablon `org/template-team/` dla pack.yaml i README.md, reszta
             z `org/template/`): standardy zespołu ponad nakładką firmy pack-<firma>, którą wymaga; prefiks skilli
             domyślnie <zespół>-

Pola do uzupełnienia mają znacznik TODO; opis każdego pola i dalsze kroki: org/README.md i README.md w wyniku.
Tylko biblioteka standardowa.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "template"
TEAM_TEMPLATE = Path(__file__).resolve().parent / "template-team"     # pack.yaml i README.md nakładki zespołu


def taken_prefixes() -> dict[str, str]:
    """Prefiksy wymiarów rdzenia, nakładek i trybów fabryki → właściciel (dopasowanie `prefix: x-`)."""
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
    subst = {"{{FIRMA_UP}}": name.replace("-", "").upper()[:8], "{{FIRMA}}": name, "{{ORG}}": org, "{{PREFIX}}": prefix,
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
            src = TEAM_TEMPLATE / rel_src          # pack.yaml i README.md zespołu
        rel = fill(rel_src.as_posix())
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = fill(src.read_text(encoding="utf-8"))
        if team and rel_src.name == "SKILL.md":   # opis skilla: ustalenia zespołu ponad standardami firmy
            text = re.sub(r"^description: .*$", f"description: Użyj przy ustaleniach zespołu {title} ponad standardami "
                          f"firmy ({org}-standardy) — kto zatwierdza, progi, zakazy i wyjątki obowiązujące w zespole.",
                          text, count=1, flags=re.M)
        dst.write_text(text, encoding="utf-8")
        written.append(rel)
    print(f"✓ {out}: {len(written)} plików")
    if team:
        print(f"""Dalej (README.md w nakładce zespołu, org/README.md):
  1. Uzupełnij pola TODO: grep -rn TODO {out}
  2. Sprawdź: python3 tools/workspace.py check --packs pack-it,pack-{org},pack-{name} --pack-dir <repo firmy> --pack-dir {out}
  3. Opublikuj {out} jako repozytorium git zespołu (tagi vX.Y.Z)
  4. Projekt zespołu: tf install --pack-dir <repo firmy> --pack-dir <repo zespołu> --add pack-{name}""")
        return 0
    print(f"""Dalej (org/README.md, README.md w nakładce):
  1. Uzupełnij pola TODO: grep -rn TODO {out}
  2. Sprawdź: python3 tools/workspace.py check --packs pack-it,pack-{name} --pack-dir {out}
  3. Opublikuj {out} jako repozytorium git firmy (tagi vX.Y.Z)
  4. Projekt: tf install --pack-dir <repozytorium firmy> --add pack-{name}""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
