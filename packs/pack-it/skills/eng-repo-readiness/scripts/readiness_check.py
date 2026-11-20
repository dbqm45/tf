#!/usr/bin/env python3
"""
Repository readiness for agent work — facts from files, without running anything.

  python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py            # current directory, a table
  python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py ../repo --json

Detects (manifests to depth 2, skipping node_modules, .git, dist, build, vendor, target, .venv):
- language families and lockfiles (requirements.txt is a weak substitute), the dependency audit command for the family
  (Java and Dart without a built-in audit → "skipped", never "0 findings");
- the test runner and a "dry" command (a list of tests without executing them);
- CI stages: lint, test, build, types, security (GitHub Actions, GitLab CI, Azure, CircleCI, Bitbucket, Jenkins);
- configuration: .gitignore, TypeScript strict, linter, formatter, .editorconfig, .env.example;
- agent instruction files (CLAUDE.md, AGENTS.md, .claude/);
- the developer loop: the start command (make/just/Taskfile, dev/setup scripts, a README section), the services
  the code needs (Postgres, Redis…) and their compose with a healthcheck, devcontainer, seed data, values
  in .env.example that look like real secrets (only variable names in the output), the related-tests command.
It does NOT run the audit, tests or build — the agent does that with the human's consent, using the commands given in the output.

Project verdict: critical (no test runner or ≥3 high findings) / needs-attention / healthy.
Vulnerabilities are not known here — critical vulnerabilities from the audit raise the verdict manually.

Exit code: 0 — no high-severity findings; 1 — there are high-severity findings; 2 — invocation error (bad path).
Standard library only, no network.
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
           None, "a non-zero exit code on findings is information, not a failure"),
    "python": (["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
               ["uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock"],
               "pip-audit --format json", "no native severity — default medium unless the description says otherwise"),
    "rust": (["Cargo.toml"], ["Cargo.lock"], "cargo audit --json", ""),
    "go": (["go.mod"], ["go.sum"], "govulncheck -json ./...", "reports only vulnerabilities reachable from the code"),
    "ruby": (["Gemfile"], ["Gemfile.lock"], "bundle audit check --update", "text output"),
    "php": (["composer.json"], ["composer.lock"], "composer audit --format json", "requires Composer ≥ 2.4"),
    "dotnet": ([], ["packages.lock.json"], "dotnet list package --vulnerable --include-transitive",
               "newer SDKs also have `dotnet package list --vulnerable`"),
    "java": (["pom.xml", "build.gradle", "build.gradle.kts"], ["gradle.lockfile"], None,
             "no built-in audit — use an external tool (e.g. OWASP Dependency-Check)"),
    "dart": (["pubspec.yaml"], ["pubspec.lock"], None, "no built-in audit — use an external tool"),
}
JS_AUDIT = {"pnpm-lock.yaml": "pnpm audit --json", "yarn.lock": "yarn npm audit --json (Yarn Berry) / yarn audit --json",
            "bun.lock": "npm audit --json (bun has no audit — check the version)", "bun.lockb": "npm audit --json (bun has no audit — check the version)"}

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
SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def walk(root: Path, depth: int = 2):
    """Files up to the given depth (0 = the root directory only), without generated and dependency directories."""
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
    """(runner, dry-run command) for the family in the manifest directory."""
    if family == "js":
        deps, scripts = js_deps(manifest)
        test_script = scripts.get("test", "")
        for name, cmd in (("vitest", "npx vitest list"), ("jest", "npx jest --listTests"),
                          ("mocha", "npx mocha --dry-run"), ("@playwright/test", "npx playwright test --list")):
            if name in deps or name.lstrip("@").split("/")[0] in test_script:
                return name, cmd
        if "node --test" in test_script:
            return "node:test", "no dry-run mode — run `node --test` with consent"
        return None, None
    if family == "python":
        text = " ".join(read(mdir / f) for f in ("pyproject.toml", "requirements.txt", "requirements-dev.txt",
                                                  "setup.cfg", "tox.ini", "Pipfile"))
        if "pytest" in text or (mdir / "pytest.ini").exists() or (mdir / "conftest.py").exists():
            return "pytest", "pytest --collect-only -q"
        if any(p.name.startswith("test_") and p.suffix == ".py" for p in walk(mdir, 2)):
            return "unittest", "python -m unittest discover -v (runs the tests — with consent)"
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
        return "dart test", "dart test (no dry-run mode — with consent)"
    return None, None


# Developer loop (DX): services the code needs locally — by dependencies and images in compose.
SERVICE_DEPS = {
    "postgres": r"\b(pg|postgres|postgresql|psycopg2?(-binary)?|asyncpg|pgx|lib/pq|org\.postgresql|npgsql|pg-promise)\b",
    "mysql": r"\b(mysql2?|pymysql|mysqlclient|mysql-connector[\w-]*|go-sql-driver/mysql|mysql-connector-j)\b",
    "redis": r"\b(redis|ioredis|bullmq|go-redis|spring-boot-starter-data-redis|valkey)\b",
    "mongodb": r"\b(mongodb|mongoose|pymongo|motor|mongo-driver|spring-boot-starter-data-mongodb)\b",
    "rabbitmq": r"\b(amqplib|pika|aio-pika|spring-boot-starter-amqp)\b",
    "kafka": r"\b(kafkajs|confluent-kafka|kafka-python|spring-kafka|segmentio/kafka-go)\b",
    "elasticsearch": r"(@elastic/elasticsearch|\belasticsearch\b|\bopensearch(-py)?\b)",
}
SERVICE_IMAGES = {"postgres": r"postgres|postgis|timescale", "mysql": r"mysql|mariadb", "redis": r"redis|valkey",
                  "mongodb": r"mongo", "rabbitmq": r"rabbitmq", "kafka": r"kafka|redpanda",
                  "elasticsearch": r"elasticsearch|opensearch"}
COMPOSE_FILES = ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml", "compose.dev.yaml",
                 "compose.dev.yml", "docker-compose.dev.yml", "docker-compose.override.yml"]
SETUP_TARGETS = {"setup", "bootstrap", "init", "install", "dev", "up", "start", "run", "serve"}
README_START = re.compile(r"^#{1,4}\s*(quick ?start|getting started|szybki start|uruchomienie|jak uruchomić|"
                          r"local development|development setup|praca lokalna|setup)\b", re.I | re.M)
SECRET_VALUE = re.compile(r"sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|"
                          r"xox[abprs]-[\w-]{10,}|AIza[0-9A-Za-z_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
                          r"sk_live_[A-Za-z0-9]{16,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}")
PLACEHOLDER = re.compile(r"example|changeme|change-me|your|xxx|dummy|fake|placeholder|dev|test|local|<|\$\{", re.I)


def dev_loop(root: Path, files: list[Path], families: list[dict]) -> tuple[dict, list[tuple]]:
    """Facts about the developer loop and findings of the `dx` area (without running anything)."""
    findings, setup = [], []
    for name in ("Makefile", "makefile", "GNUmakefile"):
        text = read(root / name)
        setup += [f"make {t}" for t in re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", text, re.M) if t in SETUP_TARGETS]
    for name in ("justfile", "Justfile", ".justfile"):
        text = read(root / name)
        setup += [f"just {t}" for t in re.findall(r"^([A-Za-z][\w-]*)[^:=\n]*:(?!=)", text, re.M) if t in SETUP_TARGETS]
    for name in ("Taskfile.yml", "Taskfile.yaml"):
        text = read(root / name)
        setup += [f"task {t}" for t in re.findall(r"^  ([A-Za-z][\w-]*):\s*$", text, re.M) if t in SETUP_TARGETS]
    pkgs = [f for f in files if f.name == "package.json"]
    all_deps: dict = {}
    for pkg in pkgs:
        deps, scripts = js_deps(pkg)
        all_deps.update(deps)
        if pkg.parent == root:
            setup += [("npm start" if k == "start" else f"npm run {k}") for k in scripts if k in SETUP_TARGETS]
    readme = next((read(root / n) for n in ("README.md", "readme.md", "README.rst", "README") if (root / n).exists()), "")
    m = README_START.search(readme)
    if m:
        setup.append(f"README: {m.group(0).lstrip('#').strip()}")
    if families and not setup:
        findings.append(("dx", "medium", "no single start command (make/just/Taskfile, dev/setup script) "
                         "and no run instructions in the README", "—",
                         "add `make setup` or `just dev` (dependencies, services, seed data) and document it in the README "
                         "and CLAUDE.md — the agent and a newcomer start with one command"))
    # service dependencies
    dep_text = " ".join(all_deps) + " " + " ".join(
        read(f) for f in files if f.name in ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile",
                                             "Gemfile", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts"))
    needed = sorted(k for k, rx in SERVICE_DEPS.items() if re.search(rx, dep_text, re.I))
    compose = next((root / n for n in COMPOSE_FILES if (root / n).is_file()), None)
    services, no_health, covered = [], [], set()
    if compose:
        text = read(compose)
        parts = ("\n" + text).split("\nservices:", 1)
        body = parts[1] if len(parts) == 2 else ""
        blocks = re.split(r"^  ([\w.-]+):\s*$", body, flags=re.M)
        for i in range(1, len(blocks), 2):
            name, block = blocks[i], blocks[i + 1]
            services.append(name)
            kinds = {kind for kind, rx in SERVICE_IMAGES.items()
                     if re.search(rx, name + " " + " ".join(re.findall(r"image:\s*(\S+)", block)), re.I)}
            covered |= kinds
            if kinds and "healthcheck:" not in block:   # a healthcheck counts for services the application waits for
                no_health.append(name)
    devcontainer = (root / ".devcontainer" / "devcontainer.json").is_file() or (root / ".devcontainer.json").is_file()
    if devcontainer and "dockerComposeFile" in read(root / ".devcontainer" / "devcontainer.json"):
        covered |= set(needed) if compose else set()
    testcontainers = bool(re.search(r"testcontainers", dep_text, re.I))
    missing = [k for k in needed if k not in covered]
    if missing and not testcontainers:
        findings.append(("dx", "medium", f"service dependencies ({', '.join(missing)}) without a local environment "
                         "(compose, devcontainer, Testcontainers)", "—",
                         "add `compose.yaml` with these services and healthchecks — the agent can then run tests without "
                         "manual setup"))
    if no_health:
        findings.append(("dx", "low", f"compose services without a healthcheck: {', '.join(no_health)}",
                         compose.name if compose else "—",
                         "add a healthcheck and `depends_on: condition: service_healthy` — tests do not start before the database"))
    # dane startowe
    seed = any(re.search(r"seed", f.name, re.I) for f in walk(root, 3)) or any(
        "seed" in k for pkg in pkgs for k in js_deps(pkg)[1]) or "loaddata" in read(root / "Makefile")
    if any(k in needed for k in ("postgres", "mysql", "mongodb")) and not seed:
        findings.append(("dx", "low", "no seed data for the local database", "—",
                         "add an idempotent seed script with synthetic data (no production copy)"))
    # secrets in .env.example — variable names only, never values
    leaked = []
    for line in read(root / ".env.example").splitlines():
        mm = re.match(r"^\s*(?:export\s+)?([A-Za-z_][\w]*)\s*=\s*(.*)$", line)
        if not mm or not mm.group(2).strip():
            continue
        name, value = mm.group(1), mm.group(2).strip().strip("\"'")
        if SECRET_VALUE.search(value) or (re.search(r"KEY|SECRET|TOKEN|PASSWORD|PRIVATE", name, re.I)
                                          and len(value) >= 20 and not PLACEHOLDER.search(value)):
            leaked.append(name)
    if leaked:
        findings.append(("dx", "high", f".env.example contains values that look like real secrets: "
                         f"{', '.join(leaked)}", ".env.example",
                         "leave values empty or use obvious dummies; if the key was real, revoke it "
                         "(ops-secrets-identities)"))
    # tests related to the change
    runners = [f.get("runner") or "" for f in families]
    related = None
    if (root / "nx.json").is_file():
        related = "npx nx affected -t test"
    elif "vitest" in runners:
        related = "npx vitest related <changed files> --run"
    elif "jest" in runners:
        related = "npx jest --findRelatedTests <changed files>"
    elif "pytest" in runners:
        related = "pytest --lf (last failed) or pytest-testmon (tests touched by the change)"
    elif "go test" in runners:
        related = "go test ./<changed package>/..."
    dx = {"setup": setup, "services": services, "services_without_healthcheck": no_health,
          "services_needed": needed, "devcontainer": devcontainer, "related_tests": related}
    return dx, findings


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
                lock_note = "requirements.txt is a weak lockfile substitute (no hashes, no transitive dependencies)"
            entry = {"family": family, "manifest": rel, "lockfile": lock, "lockfile_note": lock_note}
            cmd = audit
            if family == "js":
                cmd = JS_AUDIT.get(Path(lock).name, "npm audit --json") if lock else "npm audit --json"
            entry["audit"] = cmd or "skipped (no built-in audit)"
            entry["audit_note"] = note
            entry["runner"], entry["dry_run"] = runner_for(family, m.parent, m)
            families.append(entry)
            if not lock and family != "java":
                findings.append(("foundation", "high", f"{family}: no lockfile for {rel}"
                                 + (" (requirements.txt is a weak substitute)" if lock_note else ""),
                                 rel, f"generate a lockfile with the project's package manager ({', '.join(locks[:2])})"))
            if not entry["runner"]:
                findings.append(("environment", "high", f"{family}: no test runner detected ({rel})", rel,
                                 "add a test runner that fits the stack — fix #1 for the agent"))
            if cmd is None:
                findings.append(("foundation", "low", f"{family}: dependency audit skipped — no built-in tool",
                                 rel, note))

    # CI
    ci_files = [p for p in (root / ".github" / "workflows").glob("*.y*ml")] if (root / ".github" / "workflows").is_dir() else []
    ci_files += [root / f for f in CI_FILES if (root / f).exists()]
    ci_text = "\n".join(read(p) for p in ci_files)
    stages = {name: bool(re.search(rx, ci_text, re.I)) for name, rx in STAGES.items()} if ci_files else {}
    ci = {"files": [str(p.relative_to(root)) for p in ci_files], "stages": stages}
    if not ci_files:
        findings.append(("environment", "medium", "no CI configuration", "—",
                         "a pipeline with lint / test / build / types / security stages (ops-ci-cd)"))
    else:
        missing = [s for s, ok in stages.items() if not ok]
        if missing:
            findings.append(("environment", "medium", f"CI is missing stages: {', '.join(missing)}", ci["files"][0],
                             "add the missing stages (ops-ci-cd)"))

    # konfiguracja
    names = {p.name for p in root.iterdir()} if root.is_dir() else set()
    config = {}
    config[".gitignore"] = ".gitignore" in names
    if not config[".gitignore"]:
        findings.append(("configuration", "high", "no .gitignore (risk of committing secrets and artifacts)", "—",
                         "add a .gitignore for the stack"))
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
        config["typescript_strict"] = bool(strict) if strict is not None else ("unknown (extends)" if extends else False)
        if strict is not True and not extends:
            findings.append(("configuration", "high", "TypeScript without \"strict\": true", str(ts.relative_to(root)),
                             "enable strict (gradually, per directory, if there are many errors)"))
    pyproject = read(root / "pyproject.toml")
    linter = [n for n in LINTERS if n in names] + (["ruff (pyproject)"] if "[tool.ruff" in pyproject else [])
    pkg_deps = js_deps(root / "package.json")[0] if (root / "package.json").exists() else {}
    linter += [d for d in ("eslint", "@biomejs/biome", "oxlint") if d in pkg_deps and d not in linter]
    formatter = [n for n in FORMATTERS if n in names] + (["black/ruff format (pyproject)"]
                                                         if re.search(r"\[tool\.(black|ruff\.format)", pyproject) else [])
    formatter += [d for d in ("prettier", "@biomejs/biome") if d in pkg_deps]
    if any(f["family"] in ("go", "rust") for f in families):
        formatter.append("gofmt/rustfmt (built-in)")
    config["linter"], config["formatter"] = sorted(set(linter)), sorted(set(formatter))
    if families and not linter:
        findings.append(("configuration", "medium", "no linter detected", "—", "add a linter that fits the stack"))
    if families and not formatter:
        findings.append(("configuration", "medium", "no formatter detected", "—", "add a formatter that fits the stack"))
    for name, msg in ((".editorconfig", "no .editorconfig"), (".env.example", "no .env.example (list of variables without values)")):
        config[name] = name in names
        if not config[name]:
            findings.append(("configuration", "low", msg, "—", f"add {name}"))

    instructions = [n for n in ("CLAUDE.md", "AGENTS.md", ".claude") if (root / n).exists()]
    dx, dx_findings = dev_loop(root, files, families)
    findings += dx_findings

    high = [f for f in findings if f[1] == "high"]
    no_runner = any("no test runner" in f[2] for f in findings)
    verdict = "critical" if (no_runner or len(high) >= 3) else ("needs-attention" if findings and any(
        f[1] in ("high", "medium") for f in findings) else "healthy")
    findings.sort(key=lambda f: SEV_ORDER[f[1]])
    return {
        "root": str(root),
        "families": families,
        "ci": ci,
        "config": config,
        "instructions": instructions,
        "dx": dx,
        "findings": [{"area": a, "severity": s, "message": m, "evidence": e, "fix": fx} for a, s, m, e, fx in findings],
        "verdict": verdict,
        "note": "audit, tests and build were not run; critical vulnerabilities from the audit raise the verdict",
    }


def to_text(r: dict) -> str:
    out = [f"# Repo readiness: {r['root']}", "", f"Project verdict: **{r['verdict']}** ({r['note']})", "",
           "| Family | Manifest | Lockfile | Audit | Test runner | Dry run |", "|---|---|---|---|---|---|"]
    for f in r["families"]:
        lock = f["lockfile"] or ("MISSING — " + f["lockfile_note"] if f["lockfile_note"] else "MISSING")
        out.append(f"| {f['family']} | `{f['manifest']}` | {lock} | `{f['audit']}` | {f['runner'] or 'MISSING'} | "
                   f"{('`' + f['dry_run'] + '`') if f['dry_run'] else '—'} |")
    if not r["families"]:
        out.append("| — | no manifests detected | | | | |")
    st = r["ci"]["stages"]
    out += ["", f"CI: {', '.join(r['ci']['files']) or 'MISSING'}"
            + (" — " + " · ".join(f"{k} {'✓' if v else '✗'}" for k, v in st.items()) if st else ""),
            f"Agent instructions: {', '.join(r['instructions']) or 'MISSING'}",
            f"Developer loop: start {', '.join(r['dx']['setup']) or 'MISSING'} · services "
            f"{', '.join(r['dx']['services']) or '—'} (needed: {', '.join(r['dx']['services_needed']) or '—'}) · "
            f"devcontainer {'✓' if r['dx']['devcontainer'] else '✗'} · related tests: "
            f"{r['dx']['related_tests'] or '—'}", "",
            "| Severity | Area | Finding | Evidence | Fix |", "|---|---|---|---|---|"]
    for x in r["findings"]:
        out.append(f"| {x['severity']} | {x['area']} | {x['message']} | {x['evidence']} | {x['fix']} |")
    if not r["findings"]:
        out.append("| — | — | no findings | — | — |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Repo readiness for agent work (reads files only). "
                                             "Exit code: 0 no high findings, 1 high findings, 2 usage error.")
    ap.add_argument("path", nargs="?", default=".", help="repository directory (default: current)")
    ap.add_argument("--json", action="store_true", help="output as JSON")
    a = ap.parse_args(argv)
    root = Path(a.path).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    r = detect(root)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else to_text(r))
    return 1 if any(x["severity"] == "high" for x in r["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
