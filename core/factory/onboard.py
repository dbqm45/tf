#!/usr/bin/env python3
"""
tf onboard — przygotowanie repozytorium do pracy z fabryką: wykrywa polecenia projektu z plików, pisze raport
gotowości w zwykłym języku i włącza bramkę jakości.

  tf onboard                 # propozycja i pytanie o zgodę (bez terminala: sama propozycja)
  tf onboard --yes           # zapis bez pytania: .claude/quality-gate.json i .tf/reports/readiness.md
  tf onboard --dry-run       # tylko propozycja, niczego nie zapisuje
  tf onboard --json          # wynik wykrywania dla skryptów, niczego nie zapisuje

Wykrywa z manifestów w katalogu głównym (Node, Python, Go, Rust, Java, .NET; Makefile jako zapas): polecenie testów,
lintu, typów i buildu, plik blokady wersji, CI, plik instrukcji agenta, .gitignore. Niczego w projekcie nie uruchamia.
Istniejącej konfiguracji bramki nie nadpisuje. Blokujących kontroli jest najwyżej pięć — reszta to ostrzeżenia.

Werdykt: gotowe / gotowe-z-brakami / brak-testow. Kod wyjścia: 0 — są testy; 1 — brak polecenia testów (fabryka nie
sprawdzi zmian); 2 — błąd wywołania. Tylko biblioteka standardowa, bez sieci.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne też piszą i czytają UTF-8

KINDS = ("test", "lint", "typecheck", "build")
NAMES = {"test": "testy", "lint": "lint", "typecheck": "typy", "build": "build"}
LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "uv.lock", "poetry.lock",
             "Pipfile.lock", "pylock.toml", "go.sum", "Cargo.lock", "gradle.lockfile", "packages.lock.json")
CI_FILES = (".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", ".circleci/config.yml", "bitbucket-pipelines.yml")
NO_TEST = re.compile(r"no test specified", re.I)
MAX_BLOCKING = 5


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _json(path: Path) -> dict:
    try:
        data = json.loads(_read(path))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _node(root: Path) -> dict:
    scripts = _json(root / "package.json").get("scripts")
    if not isinstance(scripts, dict):
        return {}
    pm = next((name for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"),
                                       ("bun.lockb", "bun")) if (root / lock).is_file()), "npm")
    out = {}
    if isinstance(scripts.get("test"), str) and not NO_TEST.search(scripts["test"]):
        out["test"] = f"{pm} test"
    for kind, names in (("lint", ("lint",)), ("typecheck", ("typecheck", "type-check", "types", "tsc")),
                        ("build", ("build",))):
        name = next((n for n in names if isinstance(scripts.get(n), str)), None)
        if name:
            out[kind] = f"{pm} run {name}"
    return out


def _python(root: Path) -> dict:
    pyproject = _read(root / "pyproject.toml")
    reqs = "".join(_read(p) for p in sorted(root.glob("requirements*.txt")))
    has_tests = any((root / d).is_dir() for d in ("tests", "test"))
    if not pyproject and not reqs and not (root / "setup.py").is_file() and not (root / "pytest.ini").is_file():
        return {}
    known = pyproject + reqs
    run = "uv run " if (root / "uv.lock").is_file() else ("poetry run " if (root / "poetry.lock").is_file() else "")
    out = {}
    if "pytest" in known or (root / "pytest.ini").is_file():
        out["test"] = f"{run}pytest" if run else "python3 -m pytest"
    elif has_tests:
        out["test"] = f"{run}python -m unittest" if run else "python3 -m unittest"
    if "ruff" in known or (root / "ruff.toml").is_file():
        out["lint"] = f"{run}ruff check ."
    elif "flake8" in known or (root / ".flake8").is_file():
        out["lint"] = f"{run}flake8"
    if "mypy" in known or (root / "mypy.ini").is_file():
        out["typecheck"] = f"{run}mypy ."
    elif "pyright" in known or (root / "pyrightconfig.json").is_file():
        out["typecheck"] = f"{run}pyright"
    return out


def _go(root: Path) -> dict:
    if not (root / "go.mod").is_file():
        return {}
    return {"test": "go test ./...", "lint": "go vet ./...", "build": "go build ./..."}


def _rust(root: Path) -> dict:
    if not (root / "Cargo.toml").is_file():
        return {}
    return {"test": "cargo test", "lint": "cargo clippy", "build": "cargo build"}


def _java(root: Path) -> dict:
    if (root / "pom.xml").is_file():
        mvn = "./mvnw" if (root / "mvnw").is_file() else "mvn"
        return {"test": f"{mvn} -q test", "build": f"{mvn} -q -DskipTests package"}
    if any((root / f).is_file() for f in ("build.gradle", "build.gradle.kts")):
        gradle = "./gradlew" if (root / "gradlew").is_file() else "gradle"
        return {"test": f"{gradle} test", "build": f"{gradle} build -x test"}
    return {}


def _dotnet(root: Path) -> dict:
    if not any(root.glob("*.sln")) and not any(root.glob("*.csproj")):
        return {}
    return {"test": "dotnet test", "build": "dotnet build"}


def _make(root: Path) -> dict:
    targets = set(re.findall(r"^([A-Za-z][\w-]*)\s*:(?!=)", _read(root / "Makefile"), re.M))
    return {k: f"make {k}" for k in KINDS if k in targets}


FAMILIES = (("Node", "package.json", _node), ("Python", "pyproject.toml", _python), ("Go", "go.mod", _go),
            ("Rust", "Cargo.toml", _rust), ("Java", "pom.xml / build.gradle", _java), (".NET", "*.sln / *.csproj", _dotnet),
            ("Makefile", "Makefile", _make))


def detect(root: Path) -> dict:
    """Fakty z plików: polecenia (pierwsze wykryte dla każdego rodzaju), pliki i werdykt. Niczego nie uruchamia."""
    commands, families = {}, []
    for name, source, fn in FAMILIES:
        found = fn(root)
        if found:
            families.append(name)
        for kind in KINDS:
            if kind in found and kind not in commands:
                commands[kind] = {"command": found[kind], "source": source}
    workflows = root / ".github" / "workflows"
    ci = sorted(str(p.relative_to(root)) for p in workflows.glob("*.y*ml")) if workflows.is_dir() else []
    ci += [f for f in CI_FILES if (root / f).is_file()]
    facts = {"lockfile": [f for f in LOCKFILES if (root / f).is_file()], "ci": ci,
             "instructions": [f for f in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md") if (root / f).is_file()],
             "gitignore": (root / ".gitignore").is_file()}
    missing = [k for k in ("lint",) if k not in commands] + [k for k in ("lockfile", "ci", "gitignore") if not facts[k]]
    verdict = "brak-testow" if "test" not in commands else ("gotowe-z-brakami" if missing else "gotowe")
    return {"families": families, "commands": commands, "facts": facts, "missing": missing, "verdict": verdict}


GAPS = {   # kolejność = kolejność naprawy: najpierw to, bez czego fabryka nie sprawdzi zmian
    "test": "Brak polecenia testów. Bez testów fabryka nie potrafi sprawdzić, czy zmiana działa — to pierwsza rzecz "
            "do naprawy (można ją zlecić jako pierwsze zadanie).",
    "lockfile": "Brak pliku blokady wersji zależności. Każda instalacja może pobrać inne wersje, więc ten sam test "
                "raz przejdzie, a raz nie.",
    "lint": "Brak polecenia lintu. Błędy stylu i proste pomyłki wyjdą dopiero w przeglądzie.",
    "ci": "Brak CI. Kontrole działają tylko na komputerze autora; nikt nie sprawdza ich po wypchnięciu zmian.",
    "gitignore": "Brak .gitignore. Do repozytorium mogą trafić pliki tymczasowe i sekrety.",
}
VERDICTS = {"gotowe": "Repozytorium jest gotowe do pracy z fabryką.",
            "gotowe-z-brakami": "Repozytorium nadaje się do pracy z fabryką, ale ma braki opisane niżej.",
            "brak-testow": "Repozytorium nie jest gotowe: fabryka nie ma czym sprawdzić zmian."}


def blocking(det: dict) -> list[str]:
    """Kontrole, które zatrzymują pracę (najwyżej MAX_BLOCKING). Reszta to ostrzeżenia."""
    out = []
    if "test" in det["commands"]:
        out.append(f"Testy: `{det['commands']['test']['command']}` — praca nie kończy się, dopóki nie przejdą.")
    out.append("Sekrety: zapis kluczy i haseł do plików jest zatrzymywany.")
    out.append("Test przed kodem: kod produkcyjny bez wcześniejszego testu, który nie przechodzi, jest zatrzymywany.")
    return out[:MAX_BLOCKING]


def report(det: dict) -> str:
    cmds, facts = det["commands"], det["facts"]
    lines = ["# Gotowość repozytorium do pracy z fabryką", "", VERDICTS[det["verdict"]], "", "## Co jest"]
    for kind in KINDS:
        if kind in cmds:
            lines.append(f"- {NAMES[kind]}: `{cmds[kind]['command']}` (z: {cmds[kind]['source']})")
    if facts["lockfile"]:
        lines.append(f"- plik blokady wersji: {', '.join(facts['lockfile'])}")
    if facts["ci"]:
        lines.append(f"- CI: {', '.join(facts['ci'])}")
    if facts["instructions"]:
        lines.append(f"- plik instrukcji dla agenta: {', '.join(facts['instructions'])}")
    if facts["gitignore"]:
        lines.append("- .gitignore")
    if lines[-1] == "## Co jest":
        lines.append("- nie wykryto poleceń projektu ani plików konfiguracji")
    lines += ["", "## Czego brakuje (w kolejności naprawy)"]
    gaps = [GAPS[k] for k in GAPS if (k == "test" and "test" not in cmds) or k in det["missing"]]
    lines += [f"{i}. {g}" for i, g in enumerate(gaps, 1)] or ["Niczego istotnego."]
    lines += ["", "## Co fabryka blokuje"] + [f"- {b}" for b in blocking(det)]
    warn = [f"{NAMES[k]} (`{cmds[k]['command']}`)" for k in ("lint", "typecheck", "build") if k in cmds]
    if warn:
        lines += ["", "Tylko ostrzega (nie zatrzymuje pracy): " + ", ".join(warn) + "."]
    lines += ["", "## Kiedy ma spojrzeć człowiek",
              "- gdy testy nie przechodzą po trzech próbach poprawki — fabryka przestaje próbować i pyta;",
              "- przed scaleniem zmiany — scala człowiek, nie agent;",
              "- gdy ten raport mówi, że czegoś brakuje — braki naprawia się raz, najlepiej przed pierwszym zadaniem.", ""]
    return "\n".join(lines)


def proposal(root: Path, det: dict) -> tuple[list[str], dict]:
    """Co zostanie zapisane: opis dla człowieka i treść plików (ścieżka → tekst)."""
    say, files = [], {}
    gate = root / ".claude" / "quality-gate.json"
    if gate.is_file():
        say.append("• .claude/quality-gate.json już istnieje — zostaje bez zmian.")
    elif "test" in det["commands"]:
        files[gate] = json.dumps({"command": det["commands"]["test"]["command"]}, ensure_ascii=False, indent=2) + "\n"
        say.append(f"• .claude/quality-gate.json — bramka jakości z poleceniem `{det['commands']['test']['command']}`.")
    else:
        say.append("• bramka jakości zostaje wyłączona: nie wykryto polecenia testów.")
    files[root / ".tf" / "reports" / "readiness.md"] = report(det)
    say.append("• .tf/reports/readiness.md — raport gotowości.")
    return say, files


def main(argv: list[str]) -> int:
    flags = set(argv[1:])
    unknown = flags - {"--yes", "--dry-run", "--json", "-h", "--help"}
    if unknown or flags & {"-h", "--help"}:
        print(__doc__)
        return 2 if unknown else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    det = detect(root)
    code = 1 if det["verdict"] == "brak-testow" else 0
    if "--json" in flags:
        print(json.dumps(det, ensure_ascii=False, indent=2))
        return code
    print(report(det))
    say, files = proposal(root, det)
    print("Do zapisania:\n" + "\n".join(say))
    if "--dry-run" in flags:
        print("\n--dry-run: niczego nie zapisano.")
        return code
    if "--yes" not in flags:
        if not sys.stdin.isatty():
            print("\nNiczego nie zapisano. Zapis bez pytania: tf onboard --yes")
            return code
        if input("\nZapisać? [T/n] ").strip().lower() in ("n", "nie", "no"):
            print("Niczego nie zapisano.")
            return code
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("\n✓ Zapisano. Sprawdź stan: tf doctor")
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
