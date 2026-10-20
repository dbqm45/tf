#!/usr/bin/env python3
"""Testy wydań fabryki (docs/RELEASING.md): Conventional Commits 1.0.0 → SemVer 2.0.0 → wpis CHANGELOG, notatki
wydania i pełny przebieg `scripts/release.py` w tymczasowym repozytorium git. python3 tests/test_release.py

Narzędzie wydań należy tylko do repozytorium fabryki (`scripts/` nie trafia do projektów), więc w zainstalowanej
kopii testów (`.claude/tests/`) test się pomija."""
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
        print("— test_release: pominięty (brak scripts/ — to kopia testów w projekcie, nie repozytorium fabryki)")
        return 0
    cc = load(SCRIPTS / "conventional.py", "conventional")
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # CC: lint wiadomości commita i tytułu PR
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

    for bad, why in [("Czytelniejszy graf kontekstu", "<typ>"),
                     ("feature(web): zoom", "nieznany typ „feature”"),
                     ("Feat(web): zoom", "<typ>"),
                     ("feat(Web): zoom", "zakres „Web”"),
                     ("feat(web):zoom", "<typ>"),
                     ("feat(web): ", "pusty"),
                     ("fix: dodaj rzecz.", "kropk"),
                     (f"feat: {'x' * 73}", "73 znaki"),
                     ("fix: a\nbody without a blank line", "pustą linię"),
                     ("fix: a\n\nbreaking change: lowercase footer", "wielkimi literami"),
                     ("", "pusta")]:
        problems = "\n".join(cc.lint_message(bad))
        check(why in problems, f"CC-BAD {bad!r}: oczekiwano „{why}”, jest: {problems!r}")
    check(cc.lint_message(f"feat: {'x' * 72} (#123)") == [], "CC-LEN: 72 znaki to limit, „(#NN)” z GitHuba się nie liczy")

    # SV: rodzaj podbicia i następna wersja
    check(cc.bump_kind(["docs: readme", "test: more"]) is None, "SV-01: docs/test nie wydają")
    check(cc.bump_kind(["fix: a", "perf: b"]) == "patch", "SV-01: fix/perf → patch")
    check(cc.bump_kind(["fix: a", "feat: b", "chore: c"]) == "minor", "SV-01: feat → minor")
    check(cc.bump_kind(["feat: b", "fix(x)!: a"]) == "major", "SV-01: ! → major")
    check(cc.bump_kind(["refactor: a\n\nBREAKING CHANGE: gone"]) == "major", "SV-01: stopka BREAKING CHANGE → major")
    check(cc.bump_kind(["refactor: a\n\nBREAKING-CHANGE: gone"]) == "major", "SV-01: stopka BREAKING-CHANGE → major")
    check(cc.next_version("1.4.2", "major") == "2.0.0", "SV-03: major od 1.0.0")
    check(cc.next_version("1.4.2", "minor") == "1.5.0", "SV-03: minor")
    check(cc.next_version("1.4.2", "patch") == "1.4.3", "SV-03: patch")
    check(cc.next_version("0.1.0", "major") == "0.2.0", "SV-04: w 0.y.z zmiana niezgodna → minor")
    check(cc.next_version("0.1.0", "minor") == "0.1.1", "SV-04: w 0.y.z feat → patch")
    check(cc.next_version("0.9.3", "major") == "0.10.0", "SV-04: 1.0.0 nigdy nie jest liczone")

    # CL: wpis CHANGELOG w formacie factory/CHANGELOG.md
    entry = cc.changelog_entry("2.7.0", "2026-10-17", ["feat(web): zoom the context graph (#21)",
                                                      "fix(server): recognise IAM roles (#20)",
                                                      "feat(server)!: drop the legacy settings format",
                                                      "docs: readme", "Czytelniejszy graf"])
    check(entry == "\n".join(["## [2.7.0] — 2026-10-17",
                              "### Breaking", "- **server:** drop the legacy settings format",
                              "### Added", "- **web:** zoom the context graph (#21)",
                              "### Fixed", "- **server:** recognise IAM roles (#20)", ""]),
          f"CL-01: sekcje Breaking/Added/Fixed (po angielsku, jak opisy commitów), każdy commit raz:\n{entry}")
    check("No user-visible changes" in cc.changelog_entry("2.6.1", "2026-10-17", ["ci: x"]), "CL-02: wpis bez zmian dla użytkownika")

    # REL: notatki wydania = treść wpisu jednej wersji
    log = "\n".join(["# Zmiany", "", "Wstęp.", "", "## [2.7.0] — 2026-10-17", "### Nowe", "- **web:** zoom", "",
                     "## [2.6.0] — 2026-10-10", "Pierwsza.", "### Nowe", "- MVP", "", "[2.6.0]: https://example.test/v2.6.0"])
    check(cc.release_notes(log, "2.7.0") == "### Nowe\n- **web:** zoom", "REL-1: najnowszy wpis kończy się przed następnym")
    check(cc.release_notes(log, "2.6.0") == "Pierwsza.\n### Nowe\n- MVP", "REL-2: ostatni wpis bez definicji linków")
    check(cc.release_notes(log, "2.8.0") is None, "REL-3: brak wersji → None")
    check(cc.release_notes(log, "2.7") is None, "REL-4: prefiks innej wersji nie pasuje")
    check(cc.release_notes(log.replace("\n", "\r\n"), "2.7.0") == "### Nowe\n- **web:** zoom", "REL-5: CRLF")

    # zgodność z kontrolą fabryki: wygenerowany wpis przechodzi semver.py check-changelog z rodzajem podbicia
    sv = load(ROOT / "core" / "skills" / "core-semver" / "scripts" / "semver.py", "semver")
    base = "# Zmiany\n\n## [2.6.0] — 2026-10-10\n### Nowe\n- x\n"
    for kind, msgs in [("major", ["feat!: a"]), ("minor", ["feat: a", "fix: b"]), ("patch", ["fix: a"])]:
        v = cc.next_version("2.6.0", kind)
        text = cc.insert_entry(base, cc.changelog_entry(v, "2026-10-17", msgs))
        check(sv.check_changelog(text, v, "1.35.0") == [], f"CL-03 {kind}: {sv.check_changelog(text, v, '1.35.0')}")
    check(cc.insert_entry(base, "## [2.6.1] — d\nX\n").index("[2.6.1]") < base.index("[2.6.0]") + 20,
          "CL-04: nowy wpis na górze, pod wstępem")

    # E2E: scripts/release.py w tymczasowym repo
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "core" / "factory").mkdir(parents=True)
        (repo / "core" / "factory" / "VERSION").write_text("2.6.0\n", encoding="utf-8")
        (repo / "core" / "factory" / "CHANGELOG.md").write_text(base, encoding="utf-8")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "chore(release): 2.6.0")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 1 and "v2.6.0" in r.stderr, f"E2E-1: bez tagu — błąd z nazwą pierwszego tagu: {r.stderr}")
        git(repo, "tag", "-a", "v2.6.0", "-m", "Release 2.6.0")
        git(repo, "commit", "-q", "--allow-empty", "-m", "docs: readme")
        r = run(repo, "release.py", "--ci")
        check(r.returncode == 0 and "nic do wydania" in r.stdout
              and (repo / "core" / "factory" / "VERSION").read_text().strip() == "2.6.0", f"E2E-2: --ci bez feat/fix: {r.stdout}{r.stderr}")
        r = run(repo, "release.py")
        check(r.returncode == 1, "E2E-3: bez --ci brak zmian do wydania to błąd")
        git(repo, "commit", "-q", "--allow-empty", "-m", "feat(build): nowa flaga --x (#5)")
        git(repo, "commit", "-q", "--allow-empty", "-m", "fix: popraw y")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 0 and "2.7.0" in r.stdout and not git(repo, "status", "--porcelain"),
              f"E2E-4: --dry-run nic nie zapisuje: {r.stdout}{r.stderr}")
        (repo / "brudny.txt").write_text("x")
        r = run(repo, "release.py", "--ci")
        check(r.returncode == 1 and "niezacommitowane" in r.stderr, f"E2E-5: brudne drzewo: {r.stderr}")
        (repo / "brudny.txt").unlink()
        r = run(repo, "release.py", "--ci")
        log_text = (repo / "core" / "factory" / "CHANGELOG.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and (repo / "core" / "factory" / "VERSION").read_text() == "2.7.0\n"
              and log_text.startswith("# Zmiany\n\n## [2.7.0] — ") and "- **build:** nowa flaga --x (#5)" in log_text
              and "### Fixed\n- popraw y" in log_text, f"E2E-6: wydanie 2.7.0: {r.stdout}{r.stderr}\n{log_text}")
        r = run(repo, "release_notes.py", "2.7.0")
        check(r.returncode == 0 and r.stdout.startswith("### Added"), f"E2E-7: notatki wydania: {r.stdout}{r.stderr}")
        r = run(repo, "release_notes.py", "9.9.9")
        check(r.returncode == 1, "E2E-8: brak wpisu → kod 1")
        git(repo, "commit", "-qam", "chore(release): 2.7.0")
        r = run(repo, "release.py", "--dry-run")
        check(r.returncode == 1 and "v2.6.0" in r.stderr and "2.7.0" in r.stderr, f"E2E-9: VERSION bez tagu: {r.stderr}")
        git(repo, "tag", "-a", "v2.7.0", "-m", "Release 2.7.0")
        git(repo, "commit", "-q", "--allow-empty", "-m", "fix: z")
        r = run(repo, "release.py", "--dry-run", "major")
        check(r.returncode == 0 and "3.0.0" in r.stdout, f"E2E-10: wymuszenie major: {r.stdout}{r.stderr}")
        r = run(repo, "release.py", "--dry-run", "2.7.0")
        check(r.returncode == 1 and "nie jest nowsza" in r.stderr, f"E2E-11: wersja nie nowsza: {r.stderr}")

        # sprawdzanie wiadomości commita (hook commit-msg i tytuł PR)
        r = run(repo, "check_commit_message.py", "feat(web): zoom")
        check(r.returncode == 0 and "✓" in r.stdout, "MSG-1: poprawny tytuł")
        r = run(repo, "check_commit_message.py", "Zmiany")
        check(r.returncode == 1 and "Przykład" in r.stderr, f"MSG-2: zły tytuł z przykładem: {r.stderr}")
        (repo / "MSG").write_text("# komentarz\nfix: a\n", encoding="utf-8")
        r = run(repo, "check_commit_message.py", "--file", str(repo / "MSG"))
        check(r.returncode == 0, f"MSG-3: plik wiadomości z komentarzami gita: {r.stderr}")

    hook = ROOT / ".githooks" / "commit-msg"
    check(hook.exists() and os.access(hook, os.X_OK), "HOOK: .githooks/commit-msg istnieje i jest wykonywalny")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} test_release: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
