#!/usr/bin/env python3
"""Prepares a factory release on the current branch: computes the next SemVer version from Conventional Commits since the last
tag vX.Y.Z, writes it to core/factory/VERSION and adds an entry at the top of core/factory/CHANGELOG.md; on a MAJOR release
raises the upper bound of `requires.core` of overlays and modes that would exclude the new core. It does not commit, tag
or push: on main the Release workflow does that after every merge (`--ci`), committing "chore(release): X.Y.Z"
(docs/RELEASING.md). Run from the repository root.

  python3 scripts/release.py                  # version from commits
  python3 scripts/release.py minor            # force: major | minor | patch | X.Y.Z (1.0.0 always explicitly)
  python3 scripts/release.py --dry-run        # only show what would happen
  python3 scripts/release.py --ci             # Release workflow: having no changes to release is not an error
"""
from __future__ import annotations

import datetime as dt
import subprocess
import re
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


def widen_pack_requirements(version: str) -> list[str]:
    """On a MAJOR release: overlays and modes whose upper `requires.core` bound equals `<{new major}.0.0` (i.e.
    excluding the new core) get `<{new major + 1}.0.0`. Without this `build.py check` after the version bump reports
    every overlay and the release fails (6.0.0 and 7.0.0, tf#179, tf#181). Other bounds stay unchanged."""
    major = int(version.split(".")[0])
    if version != f"{major}.0.0":
        return []
    rx = re.compile(r'^(\s*core:\s*"[^"]*<)' + str(major) + r'(\.0\.0")', re.M)
    changed = []
    for p in sorted([*Path("packs").glob("*/pack.yaml"), *Path("modes").glob("*/pack.yaml")]):
        text = p.read_text(encoding="utf-8")
        new = rx.sub(lambda m: f"{m.group(1)}{major + 1}{m.group(2)}", text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed.append(p.parent.name)
    return changed


def main(argv: list[str]) -> int:
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__)
        return 0
    dry_run, ci = "--dry-run" in argv, "--ci" in argv
    wanted = next((a for a in argv if not a.startswith("--")), None)

    if not dry_run and git("status", "--porcelain"):
        return fail("the working tree has uncommitted changes — commit them or set them aside (git stash)")
    current = VERSION_FILE.read_text(encoding="utf-8").strip()
    tags = sorted((t[1:] for t in git("tag", "--list", "v*").split() if cc.is_release(t[1:])),
                  key=cmp_to_key(cc.compare))
    if not tags:
        return fail(f"no vX.Y.Z tag yet — the first one (v{current}) is created by the Release workflow on main after the merge")
    last = tags[-1]
    if last != current:
        return fail(f"core/factory/VERSION is {current}, the last tag is v{last} — release v{current} first (merge its PR)")

    messages = [m.strip() for m in git("log", "--format=%B%x00", f"v{last}..HEAD").split("\0") if m.strip()]
    kind = cc.bump_kind(messages)
    if wanted is None:
        if not kind:
            msg = f"since v{last} there is no feat/fix/perf or breaking change — nothing to release"
            if ci:
                print(msg)
                return 0
            return fail(f"{msg} (give a version to force a release)")
        version = cc.next_version(current, kind)
    elif wanted in ("major", "minor", "patch"):
        version = cc.bump(current, wanted)
    elif cc.is_release(wanted):
        version = wanted
    else:
        return fail(f"“{wanted}” is neither major/minor/patch nor X.Y.Z")
    if cc.compare(version, current) <= 0:
        return fail(f"{version} is not newer than {current}")

    entry = cc.changelog_entry(version, dt.date.today().isoformat(), messages)
    print(f"{len(messages)} commit(s) since v{last}{f' require a {kind} bump' if kind else ''} → {version}\n\n{entry}")
    if dry_run:
        return 0
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    CHANGELOG.write_text(cc.insert_entry(CHANGELOG.read_text(encoding="utf-8"), entry), encoding="utf-8")
    widened = widen_pack_requirements(version)
    if widened:
        print(f"✓ requires.core allows {version}: {', '.join(widened)}")
    if ci:
        print(f"✓ Version {version} saved")
        return 0
    print(f"""✓ Version {version} saved. Next:
  1. Review core/factory/CHANGELOG.md (reword the entries for users, add Changed/Deprecated if needed).
  2. python3 tools/workspace.py check
  3. git switch -c release/v{version} && git commit -am "chore(release): {version}"
  4. Push and open a PR “chore(release): {version}”. After the merge the Release workflow tags v{version}.""")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
