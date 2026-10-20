#!/usr/bin/env python3
"""
Gotowość repozytorium do pracy agentów — fakty z plików, bez uruchamiania czegokolwiek.

  python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py            # bieżący katalog, tabela
  python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py ../repo --json

Wykrywa (manifesty do głębokości 2, z pominięciem node_modules, .git, dist, build, vendor, target, .venv):
- rodziny języków i lockfile (requirements.txt to słaby zamiennik), komendę audytu zależności dla rodziny
  (Java i Dart bez wbudowanego audytu → „pominięto”, nigdy „0 znalezisk”);
- runner testów i komendę „na sucho” (lista testów bez wykonania);
- etapy CI: lint, test, build, typy, bezpieczeństwo (GitHub Actions, GitLab CI, Azure, CircleCI, Bitbucket, Jenkins);
- konfigurację: .gitignore, TypeScript strict, linter, formatter, .editorconfig, .env.example;
- pliki instrukcji agenta (CLAUDE.md, AGENTS.md, .claude/).
Audytu, testów ani builda NIE uruchamia — robi to agent za zgodą człowieka, z komendami podanymi w wyniku.

Werdykt projektu: krytyczne (brak runnera testów albo ≥3 ustalenia wysokie) / wymaga-uwagi / zdrowe.
Podatności nie są tu znane — krytyczne podatności z audytu podnoszą werdykt ręcznie.

Kod wyjścia: 0 — brak ustaleń wysokiej wagi; 1 — są ustalenia wysokiej wagi; 2 — błąd wywołania (zła ścieżka).
Tylko biblioteka standardowa, bez sieci.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "vendor", "target", ".venv", "venv", "__pycache__", ".next",
             "coverage", ".bootstrap-scaffold"}

# rodzina: (manifesty, lockfile'e, komenda audytu lub None, uwaga do audytu)
FAMILIES = {
    "js": (["package.json"], ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"],
           None, "kod wyjścia ≠ 0 przy znaleziskach to informacja, nie awaria"),
    "python": (["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
               ["uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock"],
               "pip-audit --format json", "bez natywnej wagi — domyślnie średnia, chyba że opis mówi inaczej"),
    "rust": (["Cargo.toml"], ["Cargo.lock"], "cargo audit --json", ""),
    "go": (["go.mod"], ["go.sum"], "govulncheck -json ./...", "zgłasza tylko podatności osiągalne z kodu"),
    "ruby": (["Gemfile"], ["Gemfile.lock"], "bundle audit check --update", "wynik tekstowy"),
    "php": (["composer.json"], ["composer.lock"], "composer audit --format json", "wymaga Composera ≥ 2.4"),
    "dotnet": ([], ["packages.lock.json"], "dotnet list package --vulnerable --include-transitive",
               "w nowszym SDK także `dotnet package list --vulnerable`"),
    "java": (["pom.xml", "build.gradle", "build.gradle.kts"], ["gradle.lockfile"], None,
             "brak wbudowanego audytu — narzędzie zewnętrzne (np. OWASP Dependency-Check)"),
    "dart": (["pubspec.yaml"], ["pubspec.lock"], None, "brak wbudowanego audytu — narzędzie zewnętrzne"),
}
JS_AUDIT = {"pnpm-lock.yaml": "pnpm audit --json", "yarn.lock": "yarn npm audit --json (Yarn Berry) / yarn audit --json",
            "bun.lock": "npm audit --json (bun bez audytu — sprawdź wersję)", "bun.lockb": "npm audit --json (bun bez audytu — sprawdź wersję)"}

CI_FILES = [".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", ".circleci/config.yml", "bitbucket-pipelines.yml"]
STAGES = {
    "lint": r"\blint\b|eslint|biome (check|lint)|ruff check|flake8|golangci|clippy|rubocop|phpstan|ktlint|checkstyle",
    "test": r"\btests?\b|test_\w+\.py|unittest|pytest|vitest|jest|mocha|go test|cargo test|dotnet test|rspec|phpunit|mvn .*verify|gradlew? .*check",
    "build": r"\bbuild\b|compile|package\b|assemble",
    "types": r"\btsc\b|typecheck|type-check|mypy|pyright|vue-tsc|svelte-check",
    "security": r"\baudit\b|codeql|trivy|snyk|osv-scanner|govulncheck|pip-audit|dependency-check|gitleaks|semgrep",
}
LINTERS = ["eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts", ".eslintrc", ".eslintrc.js",
           ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml", "biome.json", "biome.jsonc", "ruff.toml", ".ruff.toml",
           ".golangci.yml", ".golangci.yaml", ".rubocop.yml", "phpstan.neon", "checkstyle.xml", "detekt.yml",
           "analysis_options.yaml", ".flake8", "oxlint.json", ".oxlintrc.json"]
FORMATTERS = [".prettierrc", ".prettierrc.json", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.mjs", ".prettierrc.yml",
              ".prettierrc.yaml", "prettier.config.js", "prettier.config.mjs", "biome.json", "biome.jsonc",
              "rustfmt.toml", ".rustfmt.toml", ".php-cs-fixer.php", ".php-cs-fixer.dist.php", ".clang-format", "dprint.json"]
SEV_ORDER = {"wysoka": 0, "średnia": 1, "niska": 2}


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def walk(root: Path, depth: int = 2):
    """Pliki do zadanej głębokości (0 = sam katalog główny), bez katalogów generowanych i zależności."""
    stack = [(root, 0)]
    while stack:
        d, lvl = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir():
                if lvl < depth and e.name not in SKIP_DIRS and not e.name.startswith("."):
                    stack.append((e, lvl + 1))
            else:
                yield e


def strip_jsonc(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r'(^|[^:"\\])//.*$', r"\1", text, flags=re.M)
    return re.sub(r",(\s*[}\]])", r"\1", text)


def js_deps(pkg: Path) -> tuple[dict, dict]:
    try:
        data = json.loads(read(pkg) or "{}")
    except ValueError:
        return {}, {}
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return deps, data.get("scripts", {}) or {}


def find_lock(manifest_dir: Path, root: Path, locks: list[str]) -> str | None:
    d = manifest_dir
    while True:
        for name in locks:
            if (d / name).exists():
                return str((d / name).relative_to(root))
        if d == root or root not in d.parents:
            return None
        d = d.parent


def runner_for(family: str, mdir: Path, manifest: Path) -> tuple[str | None, str | None]:
    """(runner, komenda na sucho) dla rodziny w katalogu manifestu."""
    if family == "js":
        deps, scripts = js_deps(manifest)
        test_script = scripts.get("test", "")
        for name, cmd in (("vitest", "npx vitest list"), ("jest", "npx jest --listTests"),
                          ("mocha", "npx mocha --dry-run"), ("@playwright/test", "npx playwright test --list")):
            if name in deps or name.lstrip("@").split("/")[0] in test_script:
                return name, cmd
        if "node --test" in test_script:
            return "node:test", "brak trybu na sucho — uruchom `node --test` za zgodą"
        return None, None
    if family == "python":
        text = " ".join(read(mdir / f) for f in ("pyproject.toml", "requirements.txt", "requirements-dev.txt",
                                                  "setup.cfg", "tox.ini", "Pipfile"))
        if "pytest" in text or (mdir / "pytest.ini").exists() or (mdir / "conftest.py").exists():
            return "pytest", "pytest --collect-only -q"
        if any(p.name.startswith("test_") and p.suffix == ".py" for p in walk(mdir, 2)):
            return "unittest", "python -m unittest discover -v (uruchamia testy — za zgodą)"
        return None, None
    if family == "rust":
        return "cargo test", "cargo test --no-run"
    if family == "go":
        return "go test", "go test -list . ./..."
    if family == "ruby":
        text = read(mdir / "Gemfile")
        return ("rspec", "bundle exec rspec --dry-run") if "rspec" in text else (None, None)
    if family == "php":
        text = read(manifest)
        return ("phpunit", "vendor/bin/phpunit --list-tests") if "phpunit" in text else (None, None)
    if family == "dotnet":
        return "dotnet test", "dotnet test --list-tests"
    if family == "java":
        text = read(manifest)
        if re.search(r"junit|testng|spock", text, re.I):
            return ("junit/testng", "mvn -q test-compile" if manifest.name == "pom.xml" else "./gradlew testClasses")
        return None, None
    if family == "dart":
        return "dart test", "dart test (bez trybu na sucho — za zgodą)"
    return None, None


def detect(root: Path) -> dict:
    families, findings = [], []
    seen = set()
    files = list(walk(root, 2))
    for family, (manifests, locks, audit, note) in FAMILIES.items():
        cands = [f for f in files if f.name in manifests]
        if family == "dotnet":
            cands = [f for f in files if f.suffix in (".csproj", ".fsproj", ".sln")]
        # jedna pozycja na katalog manifestu (pyproject + requirements w tym samym katalogu = jedna)
        for m in sorted(cands, key=lambda p: (len(p.parts), str(p))):
            key = (family, m.parent)
            if key in seen:
                continue
            seen.add(key)
            rel = str(m.relative_to(root))
            lock = find_lock(m.parent, root, locks)
            lock_note = None
            if not lock and family == "python" and (m.parent / "requirements.txt").exists():
                lock_note = "requirements.txt to słaby zamiennik lockfile (brak sum i zależności przechodnich)"
            entry = {"family": family, "manifest": rel, "lockfile": lock, "lockfile_note": lock_note}
            cmd = audit
            if family == "js":
                cmd = JS_AUDIT.get(Path(lock).name, "npm audit --json") if lock else "npm audit --json"
            entry["audit"] = cmd or "pominięto (brak wbudowanego audytu)"
            entry["audit_note"] = note
            entry["runner"], entry["dry_run"] = runner_for(family, m.parent, m)
            families.append(entry)
            if not lock and family != "java":
                findings.append(("fundament", "wysoka", f"{family}: brak lockfile przy {rel}"
                                 + (" (requirements.txt to słaby zamiennik)" if lock_note else ""),
                                 rel, f"wygeneruj lockfile menedżerem projektu ({', '.join(locks[:2])})"))
            if not entry["runner"]:
                findings.append(("środowisko", "wysoka", f"{family}: nie wykryto runnera testów ({rel})", rel,
                                 "dodaj runner testów zgodny ze stackiem — poprawka nr 1 dla agenta"))
            if cmd is None:
                findings.append(("fundament", "niska", f"{family}: audyt zależności pominięto — brak wbudowanego narzędzia",
                                 rel, note))

    # CI
    ci_files = [p for p in (root / ".github" / "workflows").glob("*.y*ml")] if (root / ".github" / "workflows").is_dir() else []
    ci_files += [root / f for f in CI_FILES if (root / f).exists()]
    ci_text = "\n".join(read(p) for p in ci_files)
    stages = {name: bool(re.search(rx, ci_text, re.I)) for name, rx in STAGES.items()} if ci_files else {}
    ci = {"files": [str(p.relative_to(root)) for p in ci_files], "stages": stages}
    if not ci_files:
        findings.append(("środowisko", "średnia", "brak konfiguracji CI", "—",
                         "pipeline z etapami lint / test / build / typy / bezpieczeństwo (ops-ci-cd)"))
    else:
        missing = [s for s, ok in stages.items() if not ok]
        if missing:
            findings.append(("środowisko", "średnia", f"CI bez etapów: {', '.join(missing)}", ci["files"][0],
                             "dopisz brakujące etapy (ops-ci-cd)"))

    # konfiguracja
    names = {p.name for p in root.iterdir()} if root.is_dir() else set()
    config = {}
    config[".gitignore"] = ".gitignore" in names
    if not config[".gitignore"]:
        findings.append(("konfiguracja", "wysoka", "brak .gitignore (ryzyko commitu sekretów i artefaktów)", "—",
                         "dodaj .gitignore dla stacku"))
    tsconfigs = [f for f in files if f.name == "tsconfig.json"]
    if tsconfigs:
        ts = tsconfigs[0]
        text = strip_jsonc(read(ts))
        try:
            opts = json.loads(text).get("compilerOptions", {})
            strict = opts.get("strict")
            extends = json.loads(text).get("extends")
        except ValueError:
            strict, extends = None, None
        config["typescript_strict"] = bool(strict) if strict is not None else ("nieznane (extends)" if extends else False)
        if strict is not True and not extends:
            findings.append(("konfiguracja", "wysoka", "TypeScript bez \"strict\": true", str(ts.relative_to(root)),
                             "włącz strict (stopniowo, per katalog, jeśli błędów dużo)"))
    pyproject = read(root / "pyproject.toml")
    linter = [n for n in LINTERS if n in names] + (["ruff (pyproject)"] if "[tool.ruff" in pyproject else [])
    pkg_deps = js_deps(root / "package.json")[0] if (root / "package.json").exists() else {}
    linter += [d for d in ("eslint", "@biomejs/biome", "oxlint") if d in pkg_deps and d not in linter]
    formatter = [n for n in FORMATTERS if n in names] + (["black/ruff format (pyproject)"]
                                                         if re.search(r"\[tool\.(black|ruff\.format)", pyproject) else [])
    formatter += [d for d in ("prettier", "@biomejs/biome") if d in pkg_deps]
    if any(f["family"] in ("go", "rust") for f in families):
        formatter.append("gofmt/rustfmt (wbudowany)")
    config["linter"], config["formatter"] = sorted(set(linter)), sorted(set(formatter))
    if families and not linter:
        findings.append(("konfiguracja", "średnia", "nie wykryto lintera", "—", "dodaj linter zgodny ze stackiem"))
    if families and not formatter:
        findings.append(("konfiguracja", "średnia", "nie wykryto formatera", "—", "dodaj formater zgodny ze stackiem"))
    for name, msg in ((".editorconfig", "brak .editorconfig"), (".env.example", "brak .env.example (lista zmiennych bez wartości)")):
        config[name] = name in names
        if not config[name]:
            findings.append(("konfiguracja", "niska", msg, "—", f"dodaj {name}"))

    instructions = [n for n in ("CLAUDE.md", "AGENTS.md", ".claude") if (root / n).exists()]

    high = [f for f in findings if f[1] == "wysoka"]
    no_runner = any("runnera testów" in f[2] for f in findings)
    verdict = "krytyczne" if (no_runner or len(high) >= 3) else ("wymaga-uwagi" if findings and any(
        f[1] in ("wysoka", "średnia") for f in findings) else "zdrowe")
    findings.sort(key=lambda f: SEV_ORDER[f[1]])
    return {
        "root": str(root),
        "families": families,
        "ci": ci,
        "config": config,
        "instructions": instructions,
        "findings": [{"area": a, "severity": s, "message": m, "evidence": e, "fix": fx} for a, s, m, e, fx in findings],
        "verdict": verdict,
        "note": "audyt, testy i build nie były uruchamiane; krytyczne podatności z audytu podnoszą werdykt",
    }


def to_text(r: dict) -> str:
    out = [f"# Gotowość repo: {r['root']}", "", f"Werdykt projektu: **{r['verdict']}** ({r['note']})", "",
           "| Rodzina | Manifest | Lockfile | Audyt | Runner testów | Na sucho |", "|---|---|---|---|---|---|"]
    for f in r["families"]:
        lock = f["lockfile"] or ("BRAK — " + f["lockfile_note"] if f["lockfile_note"] else "BRAK")
        out.append(f"| {f['family']} | `{f['manifest']}` | {lock} | `{f['audit']}` | {f['runner'] or 'BRAK'} | "
                   f"{('`' + f['dry_run'] + '`') if f['dry_run'] else '—'} |")
    if not r["families"]:
        out.append("| — | nie wykryto manifestów | | | | |")
    st = r["ci"]["stages"]
    out += ["", f"CI: {', '.join(r['ci']['files']) or 'BRAK'}"
            + (" — " + " · ".join(f"{k} {'✓' if v else '✗'}" for k, v in st.items()) if st else ""),
            f"Instrukcje agenta: {', '.join(r['instructions']) or 'BRAK'}", "",
            "| Waga | Obszar | Ustalenie | Dowód | Poprawka |", "|---|---|---|---|---|"]
    for x in r["findings"]:
        out.append(f"| {x['severity']} | {x['area']} | {x['message']} | {x['evidence']} | {x['fix']} |")
    if not r["findings"]:
        out.append("| — | — | brak ustaleń | — | — |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Gotowość repo do pracy agentów (tylko odczyt plików). "
                                             "Kod wyjścia: 0 brak ustaleń wysokich, 1 są ustalenia wysokie, 2 błąd wywołania.")
    ap.add_argument("path", nargs="?", default=".", help="katalog repozytorium (domyślnie bieżący)")
    ap.add_argument("--json", action="store_true", help="wynik w JSON")
    a = ap.parse_args(argv)
    root = Path(a.path).resolve()
    if not root.is_dir():
        print(f"błąd: {root} nie jest katalogiem", file=sys.stderr)
        return 2
    r = detect(root)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else to_text(r))
    return 1 if any(x["severity"] == "wysoka" for x in r["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
