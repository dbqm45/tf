#!/usr/bin/env python3
"""Przygotowuje wydanie fabryki na bieżącej gałęzi: liczy następną wersję SemVer z Conventional Commits od ostatniego
tagu vX.Y.Z, zapisuje ją w core/factory/VERSION i dopisuje wpis na górze core/factory/CHANGELOG.md. Nie commituje, nie taguje
i nie pushuje: na main robi to workflow Release po każdym merge (`--ci`), commitując „chore(release): X.Y.Z”
(docs/RELEASING.md). Wywołuj z katalogu głównego repozytorium.

  python3 scripts/release.py                  # wersja z commitów
  python3 scripts/release.py minor            # wymuszenie: major | minor | patch | X.Y.Z (1.0.0 zawsze jawnie)
  python3 scripts/release.py --dry-run        # tylko pokaż, co by się stało
  python3 scripts/release.py --ci             # workflow Release: brak zmian do wydania nie jest błędem
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from functools import cmp_to_key
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventional as cc  # noqa: E402

VERSION_FILE = Path("core/factory/VERSION")
CHANGELOG = Path("core/factory/CHANGELOG.md")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, timeout=30).stdout.strip()


def fail(msg: str) -> int:
    print(f"✗ {msg}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__)
        return 0
    dry_run, ci = "--dry-run" in argv, "--ci" in argv
    wanted = next((a for a in argv if not a.startswith("--")), None)

    if not dry_run and git("status", "--porcelain"):
        return fail("drzewo robocze ma niezacommitowane zmiany — zacommituj je lub odłóż (git stash)")
    current = VERSION_FILE.read_text(encoding="utf-8").strip()
    tags = sorted((t[1:] for t in git("tag", "--list", "v*").split() if cc.is_release(t[1:])),
                  key=cmp_to_key(cc.compare))
    if not tags:
        return fail(f"brak tagu vX.Y.Z — pierwszy (v{current}) tworzy workflow Release na main po merge")
    last = tags[-1]
    if last != current:
        return fail(f"core/factory/VERSION ma {current}, ostatni tag to v{last} — najpierw wydaj v{current} (merge jego PR)")

    messages = [m.strip() for m in git("log", "--format=%B%x00", f"v{last}..HEAD").split("\0") if m.strip()]
    kind = cc.bump_kind(messages)
    if wanted is None:
        if not kind:
            msg = f"od v{last} nie ma feat/fix/perf ani zmiany niezgodnej — nic do wydania"
            if ci:
                print(msg)
                return 0
            return fail(f"{msg} (podaj wersję, żeby wymusić wydanie)")
        version = cc.next_version(current, kind)
    elif wanted in ("major", "minor", "patch"):
        version = cc.bump(current, wanted)
    elif cc.is_release(wanted):
        version = wanted
    else:
        return fail(f"„{wanted}” to ani major/minor/patch, ani X.Y.Z")
    if cc.compare(version, current) <= 0:
        return fail(f"{version} nie jest nowsza od {current}")

    entry = cc.changelog_entry(version, dt.date.today().isoformat(), messages)
    print(f"{len(messages)} commit(ów) od v{last}{f' wymaga podbicia {kind}' if kind else ''} → {version}\n\n{entry}")
    if dry_run:
        return 0
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    CHANGELOG.write_text(cc.insert_entry(CHANGELOG.read_text(encoding="utf-8"), entry), encoding="utf-8")
    if ci:
        print(f"✓ Wersja {version} zapisana")
        return 0
    print(f"""✓ Wersja {version} zapisana. Dalej:
  1. Przejrzyj core/factory/CHANGELOG.md (przeredaguj wpisy dla użytkowników, dodaj Changed/Deprecated, jeśli trzeba).
  2. python3 tools/workspace.py check
  3. git switch -c release/v{version} && git commit -am "chore(release): {version}"
  4. Push i PR „chore(release): {version}”. Po merge workflow Release taguje v{version}.""")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
