#!/usr/bin/env python3
"""Testy SemVer 2.0.0: skrypt core-semver (walidacja, precedencja, podbicia, następna wersja z commitów, kontrola
CHANGELOG), porównanie wersji w update.py i zgodność wersji samej fabryki."""
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SV_PATH = ROOT / ".claude" / "skills" / "core-semver" / "scripts" / "semver.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    sv = load(SV_PATH, "semver")
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # reguła 11: przykład kolejności ze specyfikacji (podany w losowej kolejności)
    spec_order = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11",
                  "1.0.0-rc.1", "1.0.0"]
    check(sv.sort_versions(list(reversed(spec_order))) == spec_order, "precedencja: przykład z reguły 11")
    check(sv.compare("1.9.0", "1.10.0") < 0 and sv.compare("1.10.0", "1.11.0") < 0, "liczby porównywane liczbowo (reguła 2)")
    check(sv.compare("1.0.0+20130313144700", "1.0.0+exp.sha.5114f85") == 0, "metadane budowania pomijane (reguła 10)")
    check(sv.compare("2.0.0", "2.1.0") < 0 and sv.compare("2.1.0", "2.1.1") < 0, "major.minor.patch od lewej")

    # reguły 2, 9, 10: poprawne i niepoprawne wersje
    good = ["0.0.4", "1.2.3", "10.20.30", "1.1.2-prerelease+meta", "1.0.0-alpha.beta.1", "1.0.0-0A.is.legal",
            "1.0.0-rc.1+build.123", "2.0.0+build.1848", "1.2.3----RC-SNAPSHOT.12.9.1--.12+788"]
    bad = ["1", "1.2", "1.2.3-0123", "1.2.3-0123.0123", "1.1.2+.123", "+invalid", "-invalid", "alpha", "1.2.3.DEV",
           "01.1.1", "1.01.1", "1.1.01", "1.2.3-rc..1", "v1.2.3", "1.2.3-", "1.2.3+"]
    for v in good:
        try:
            sv.Version(v)
        except ValueError:
            check(False, f"poprawna wersja odrzucona: {v}")
    for v in bad:
        try:
            sv.Version(v)
            check(False, f"niepoprawna wersja przyjęta: {v}")
        except ValueError as e:
            if v == "v1.2.3":
                check("nazwa tagu" in str(e), "v1.2.3: komunikat o prefiksie tagu")

    # podbicia (reguły 6–8: zerowanie niższych składników; wersje przedpremierowe)
    cases = [("2.4.1", "major", "3.0.0"), ("2.4.1", "minor", "2.5.0"), ("2.4.1", "patch", "2.4.2"),
             ("1.2.3", "pre", "1.2.4-rc.1"), ("1.2.4-rc.1", "pre", "1.2.4-rc.2"), ("1.2.4-rc.9", "pre", "1.2.4-rc.10"),
             ("1.2.4-rc.2", "release", "1.2.4"), ("2.0.0-rc.1", "major", "2.0.0"), ("1.3.0-beta.1", "minor", "1.3.0"),
             ("1.2.4-rc.1", "patch", "1.2.4")]
    for v, part, want in cases:
        got = sv.bump(v, part)
        check(got == want, f"bump {v} {part}: {got} ≠ {want}")
    check(sv.compare("1.2.4-rc.10", "1.2.4-rc.9") > 0, "rc.10 > rc.9 (identyfikatory liczbowe)")

    # następna wersja z Conventional Commits; faza 0.y.z
    k, _ = sv.classify(["feat(api)!: remove v1", "fix: x"])
    k2, _ = sv.classify(["feat: add y", "fix: x", "docs: z"])
    k3, _ = sv.classify(["fix: x", "perf: y"])
    k4, _ = sv.classify(["docs: a", "chore: b"])
    k5, _ = sv.classify(["refactor: z\n\nBREAKING CHANGE: config key renamed"])
    check((k, k2, k3, k4, k5) == ("major", "minor", "patch", None, "major"), f"classify: {k, k2, k3, k4, k5}")
    check(sv.next_version("1.4.2", "major") == "2.0.0" and sv.next_version("0.3.1", "major") == "0.4.0"
          and sv.next_version("0.3.1", "minor") == "0.3.2" and sv.next_version("1.0.0", None) is None,
          "next_version: faza 0.y.z i brak zmian")

    with tempfile.TemporaryDirectory() as d:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t"}
        g = lambda *a: subprocess.run(["git", *a], cwd=d, env=env, capture_output=True, text=True)
        g("init", "-q")
        g("commit", "--allow-empty", "-q", "-m", "feat: start")
        g("tag", "v1.4.0")
        g("tag", "v1.10.0-rc.1")
        g("commit", "--allow-empty", "-q", "-m", "fix: bug")
        g("commit", "--allow-empty", "-q", "-m", "feat(ui): new filter")
        r = subprocess.run([sys.executable, str(SV_PATH), "next", "--since", "v1.4.0"], cwd=d, env=env,
                           capture_output=True, text=True)
        check("następna wersja: 1.5.0 (minor" in r.stdout, f"next z historii git: {r.stdout}")
        r2 = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(SV_PATH.parent)!r}); "
                             "import semver; print(semver.last_tag())"], cwd=d, env=env, capture_output=True, text=True)
        check(r2.stdout.strip() == "v1.10.0-rc.1", f"last_tag wg precedencji SemVer: {r2.stdout.strip()}")

    # kontrola CHANGELOG
    log = "# Zmiany\n\n## [1.3.0] — d\n### Nowe\n- a\n\n## [1.2.1] — d\n### Poprawione\n- b\n\n## [1.2.0] — d\n### Nowe\n- c\n"
    check(sv.check_changelog(log, "1.3.0", "1.0.0") == [], "changelog poprawny")
    check(any("≠ wersja" in p for p in sv.check_changelog(log, "1.3.1")), "changelog: VERSION ≠ najnowszy wpis")
    check(any("kolejność" in p for p in sv.check_changelog(log.replace("[1.2.1]", "[1.4.0]"))), "changelog: kolejność")
    check(any("dwa razy" in p for p in sv.check_changelog(log.replace("[1.2.1]", "[1.2.0]"))), "changelog: duplikat")
    bad_minor = log.replace("## [1.3.0] — d\n### Nowe", "## [1.2.2] — d\n### Nowe")
    check(any("tylko patch" in p for p in sv.check_changelog(bad_minor, None, "1.0.0")), "changelog: Nowe w patch")
    bad_major = log.replace("### Nowe\n- a", "### Niezgodne\n- usunięto x")
    check(any("wymagany major" in p for p in sv.check_changelog(bad_major, None, "1.0.0")), "changelog: Niezgodne w minor")
    check(sv.check_changelog(bad_minor, None, "1.3.0") == [], "changelog: kontrola rodzaju dopiero od strict_from")

    # update.py: precedencja SemVer
    up = load(ROOT / "factory" / "update.py", "ctf_update")
    check(up.newer_than("1.36.0", "1.36.0-rc.1") > 0 and up.newer_than("1.10.0", "1.9.3") > 0
          and up.newer_than("v1.2.3", "1.2.3") == 0, "update.py: porównanie wersji wg SemVer")

    # sama fabryka: VERSION i CHANGELOG zgodne z SemVer
    sys.path.insert(0, str(ROOT / "factory" / "_vendor"))   # PyYAML systemowy albo dołączony do fabryki
    import yaml
    cfg = yaml.safe_load((ROOT / "factory" / "config.yaml").read_text(encoding="utf-8"))
    version = (ROOT / "factory" / "VERSION").read_text(encoding="utf-8").strip()
    probs = sv.check_changelog((ROOT / "factory" / "CHANGELOG.md").read_text(encoding="utf-8"), version,
                               cfg.get("semver_strict_from"))
    check(not probs, f"wersja fabryki: {probs}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów SemVer")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
