#!/usr/bin/env python3
"""Factory release tests (docs/RELEASING.md): Conventional Commits 1.0.0 → SemVer 2.0.0 → a CHANGELOG entry, release notes
and a full run of `scripts/release.py` in a temporary git repository. python3 tests/test_release.py

The release tool belongs only to the factory repository (`scripts/` does not reach projects), so in an installed
copy of the tests (`.claude/tests/`) the test is skipped."""
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPTS = ROOT / "scripts"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(cwd: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env).stdout


def run(cwd: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=cwd, capture_output=True, text=True,
                          timeout=60)


def main() -> int:
    if not (SCRIPTS / "conventional.py").exists():
        print("— test_release: skipped (no scripts/ — this is a copy of the tests in a project, not the factory repository)")
        return 0
    cc = load(SCRIPTS / "conventional.py", "conventional")
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # CC: linting a commit message and a PR title
    for ok in ["feat(web): zoom the context graph",
               "fix: odrzuć pustą odpowiedź",
               "feat(server)!: drop the legacy settings format",
               "build(deps-dev): Bump vitest from 5.0.3 to 5.1.0",
               "ci(deps): bump the actions group with 6 updates (#13)",
               "chore(release): 2.7.0",
               "fix(server): handle IAM roles\n\nThe SDK resolves them lazily.\n\nRefs: #20",
               "refactor(core): rename blockade state\n\nBREAKING CHANGE: ResourceDto.isReserved removed",
               "Merge branch 'main' into feature",
               'Revert "feat: x"',
               "fixup! feat(web): zoom",
               "# Please enter the commit message\nfeat(web): zoom the graph\n# Lines starting with # are ignored"]:
        check(cc.lint_message(ok) == [], f"CC-OK {ok.splitlines()[0]!r}: {cc.lint_message(ok)}")

    for bad, why in [("Czytelniejszy graf kontekstu", "<type>"),
                     ("feature(web): zoom", "unknown type “feature”"),
                     ("Feat(web): zoom", "<type>"),
                     ("feat(Web): zoom", "scope “Web”"),
                     ("feat(web):zoom", "<type>"),
                     ("feat(web): ", "empty"),
                     ("fix: dodaj rzecz.", "period"),
                     (f"feat: {'x' * 73}", "73 characters"),
                     ("fix: a\nbody without a blank line", "blank line"),
                     ("fix: a\n\nbreaking change: lowercase footer", "capital letters"),
                     ("", "empty")]:
        problems = "\n".join(cc.lint_message(bad))
        check(why in problems, f"CC-BAD {bad!r}: expected “{why}”, got: {problems!r}")
    check(cc.lint_message(f"feat: {'x' * 72} (#123)") == [], "CC-LEN: 72 characters is the limit, GitHub's “(#NN)” does not count")

    # SV: the bump kind and the next version
    check(cc.bump_kind(["docs: readme", "test: more"]) is None, "SV-01: docs/test do not release")
    check(cc.bump_kind(["fix: a", "perf: b"]) == "patch", "SV-01: fix/perf → patch")
    check(cc.bump_kind(["fix: a", "feat: b", "chore: c"]) == "minor", "SV-01: feat → minor")
    check(cc.bump_kind(["feat: b", "fix(x)!: a"]) == "major", "SV-01: ! → major")
    check(cc.bump_kind(["refactor: a\n\nBREAKING CHANGE: gone"]) == "major", "SV-01: the BREAKING CHANGE footer → major")
    check(cc.bump_kind(["refactor: a\n\nBREAKING-CHANGE: gone"]) == "major", "SV-01: the BREAKING-CHANGE footer → major")
    check(cc.next_version("1.4.2", "major") == "2.0.0", "SV-03: major from 1.0.0")
    check(cc.next_version("1.4.2", "minor") == "1.5.0", "SV-03: minor")
    check(cc.next_version("1.4.2", "patch") == "1.4.3", "SV-03: patch")
    check(cc.next_version("0.1.0", "major") == "0.2.0", "SV-04: in 0.y.z a breaking change → minor")
    check(cc.next_version("0.1.0", "minor") == "0.1.1", "SV-04: in 0.y.z feat → patch")
    check(cc.next_version("0.9.3", "major") == "0.10.0", "SV-04: 1.0.0 is never counted")

    # CL: a CHANGELOG entry in the factory/CHANGELOG.md format
    entry = cc.changelog_entry("2.7.0", "2026-10-17", ["feat(web): zoom the context graph (#21)",
                                                      "fix(server): recognise IAM roles (#20)",
                                                      "feat(server)!: drop the legacy settings format",
                                                      "docs: readme", "Czytelniejszy graf"])
    check(entry == "\n".join(["## [2.7.0] — 2026-10-17",
                              "### Breaking", "- **server:** drop the legacy settings format",
                              "### Added", "- **web:** zoom the context graph (#21)",
                              "### Fixed", "- **server:** recognise IAM roles (#20)", ""]),
          f"CL-01: Breaking/Added/Fixed sections (in English, like the commit descriptions), every commit once:\n{entry}")
    check("No user-visible changes" in cc.changelog_entry("2.6.1", "2026-10-17", ["ci: x"]), "CL-02: an entry without user-visible changes")

    # REL: release notes = the body of one version's entry
    log = "\n".join(["# Zmiany", "", "Wstęp.", "", "## [2.7.0] — 2026-10-17", "### Nowe", "- **web:** zoom", "",
                     "## [2.6.0] — 2026-10-10", "Pierwsza.", "### Nowe", "- MVP", "", "[2.6.0]: https://example.test/v2.6.0"])
    check(cc.release_notes(log, "2.7.0") == "### Nowe\n- **web:** zoom", "REL-1: the newest entry ends before the next one")
    check(cc.release_notes(log, "2.6.0") == "Pierwsza.\n### Nowe\n- MVP", "REL-2: the last entry without link definitions")
    check(cc.release_notes(log, "2.8.0") is None, "REL-3: no version → None")
    check(cc.release_notes(log, "2.7") is None, "REL-4: the prefix of another version does not match")
    check(cc.release_notes(log.replace("\n", "\r\n"), "2.7.0") == "### Nowe\n- **web:** zoom", "REL-5: CRLF")

    # consistency with the factory check: a generated entry passes semver.py check-changelog with the bump kind
    sv = load(ROOT / "core" / "skills" / "core-semver" / "scripts" / "semver.py", "semver")
    base = "# Zmiany\n\n## [2.6.0] — 2026-10-10\n### Nowe\n- x\n"
    for kind, msgs in [("major", ["feat!: a"]), ("minor", ["feat: a", "fix: b"]), ("patch", ["fix: a"])]:
        v = cc.next_version("2.6.0", kind)
        text = cc.insert_entry(base, cc.changelog_entry(v, "2026-10-17", msgs))
        check(sv.check_changelog(text, v, "1.35.0") == [], f"CL-03 {kind}: {sv.check_changelog(text, v, '1.35.0')}")
    check(cc.insert_entry(base, "## [2.6.1] — d\nX\n").index("[2.6.1]") < base.index("[2.6.0]") + 20,
          "CL-04: the new entry on top, below the intro")

    # E2E: scripts/release.py in a temporary repo
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "core" / "factory").mkdir(parents=True)
        (repo / "core" / "factory" / "VERSION").write_text("2.6.0\n", encoding="utf-8")
        (repo / "core" / "factory" / "CHANGELOG.md").write_text(base, encoding="utf-8")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "chore(release): 2.6.0")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 1 and "v2.6.0" in r.stderr, f"E2E-1: no tag — an error naming the first tag: {r.stderr}")
        git(repo, "tag", "-a", "v2.6.0", "-m", "Release 2.6.0")
        git(repo, "commit", "-q", "--allow-empty", "-m", "docs: readme")
        r = run(repo, "release.py", "--ci")
        check(r.returncode == 0 and "nothing to release" in r.stdout
              and (repo / "core" / "factory" / "VERSION").read_text().strip() == "2.6.0", f"E2E-2: --ci without feat/fix: {r.stdout}{r.stderr}")
        r = run(repo, "release.py")
        check(r.returncode == 1, "E2E-3: without --ci, nothing to release is an error")
        git(repo, "commit", "-q", "--allow-empty", "-m", "feat(build): nowa flaga --x (#5)")
        git(repo, "commit", "-q", "--allow-empty", "-m", "fix: popraw y")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 0 and "2.7.0" in r.stdout and not git(repo, "status", "--porcelain"),
              f"E2E-4: --dry-run writes nothing: {r.stdout}{r.stderr}")
        (repo / "brudny.txt").write_text("x")
        r = run(repo, "release.py", "--ci")
        check(r.returncode == 1 and "uncommitted" in r.stderr, f"E2E-5: a dirty tree: {r.stderr}")
        (repo / "brudny.txt").unlink()
        r = run(repo, "release.py", "--ci")
        log_text = (repo / "core" / "factory" / "CHANGELOG.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and (repo / "core" / "factory" / "VERSION").read_text() == "2.7.0\n"
              and log_text.startswith("# Zmiany\n\n## [2.7.0] — ") and "- **build:** nowa flaga --x (#5)" in log_text
              and "### Fixed\n- popraw y" in log_text, f"E2E-6: release 2.7.0: {r.stdout}{r.stderr}\n{log_text}")
        r = run(repo, "release_notes.py", "2.7.0")
        check(r.returncode == 0 and r.stdout.startswith("### Added"), f"E2E-7: release notes: {r.stdout}{r.stderr}")
        r = run(repo, "release_notes.py", "9.9.9")
        check(r.returncode == 1, "E2E-8: no entry → code 1")
        git(repo, "commit", "-qam", "chore(release): 2.7.0")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 1 and "v2.6.0" in r.stderr and "2.7.0" in r.stderr, f"E2E-9: VERSION without a tag: {r.stderr}")
        git(repo, "tag", "-a", "v2.7.0", "-m", "Release 2.7.0")
        git(repo, "commit", "-q", "--allow-empty", "-m", "fix: z")
        r = run(repo, "release.py", "--dry-run", "major")
        check(r.returncode == 0 and "3.0.0" in r.stdout, f"E2E-10: forcing major: {r.stdout}{r.stderr}")
        r = run(repo, "release.py", "--dry-run", "2.7.0")
        check(r.returncode == 1 and "is not newer" in r.stderr, f"E2E-11: a version that is not newer: {r.stderr}")

        # E2E-12: a MAJOR release raises the upper bound of `requires.core` of overlays and modes that would exclude the new core
        for rel, line in (("packs/pack-a/pack.yaml", '  core: ">=2.0.0 <3.0.0"   # komentarz zostaje'),
                          ("modes/mode-b/pack.yaml", '  core: ">=2.5.0 <3.0.0"'),
                          ("packs/pack-c/pack.yaml", '  core: ">=2.0.0 <9.0.0"')):
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(f"id: x\nrequires:\n{line}\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "feat!: zmiana niezgodna\n\nBREAKING CHANGE: x")
        r = run(repo, "release.py", "--ci")
        packs = {rel: (repo / rel).read_text(encoding="utf-8") for rel in
                 ("packs/pack-a/pack.yaml", "modes/mode-b/pack.yaml", "packs/pack-c/pack.yaml")}
        check(r.returncode == 0 and (repo / "core" / "factory" / "VERSION").read_text() == "3.0.0\n"
              and '">=2.0.0 <4.0.0"   # komentarz zostaje' in packs["packs/pack-a/pack.yaml"]
              and '">=2.5.0 <4.0.0"' in packs["modes/mode-b/pack.yaml"]
              and '">=2.0.0 <9.0.0"' in packs["packs/pack-c/pack.yaml"] and "pack-a" in r.stdout,
              f"E2E-12: MAJOR raises the overlays' requires.core (<3.0.0 → <4.0.0), other bounds unchanged: "
              f"{r.stdout}{r.stderr} {packs}")

        # checking the commit message (the commit-msg hook and the PR title)
        r = run(repo, "check_commit_message.py", "feat(web): zoom")
        check(r.returncode == 0 and "✓" in r.stdout, "MSG-1: a correct title")
        r = run(repo, "check_commit_message.py", "Zmiany")
        check(r.returncode == 1 and "Example" in r.stderr, f"MSG-2: a bad title with an example: {r.stderr}")
        (repo / "MSG").write_text("# komentarz\nfix: a\n", encoding="utf-8")
        r = run(repo, "check_commit_message.py", "--file", str(repo / "MSG"))
        check(r.returncode == 0, f"MSG-3: a message file with git comments: {r.stderr}")

    hook = ROOT / ".githooks" / "commit-msg"
    check(hook.exists() and os.access(hook, os.X_OK), "HOOK: .githooks/commit-msg exists and is executable")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} test_release: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
