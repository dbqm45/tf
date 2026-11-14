#!/usr/bin/env python3
"""
tf onboard — przygotowanie repozytorium do pracy z fabryką: wykrywa polecenia projektu z plików, pisze raport
gotowości w zwykłym języku i włącza bramkę jakości.

  tf onboard                 # propozycja i pytanie o zgodę (bez terminala: sama propozycja)
  tf onboard --yes           # zapis bez pytania: verify.sh, .claude/quality-gate.json, .tf/reports/readiness.md
                             # i polecenia w sekcji „Komendy” pliku instrukcji (CLAUDE.md / CLAUDE.local.md)
  tf onboard --yes --verify  # po zapisie uruchamia weryfikację raz i mówi, czy przechodzi
  tf onboard --dry-run       # tylko propozycja, niczego nie zapisuje
  tf onboard --json          # wynik wykrywania dla skryptów, niczego nie zapisuje

Wykrywa z manifestów w katalogu głównym (Node, Python, Go, Rust, Java, .NET; Makefile jako zapas): polecenie testów,
lintu, typów i buildu, plik blokady wersji, CI, plik instrukcji agenta, .gitignore. Bez --verify niczego w projekcie
nie uruchamia. `verify.sh` to jedno polecenie weryfikacji (lint → typy → testy) dla bramki jakości, pętli `/tf` i CI;
w Windows bramka dostaje samo polecenie testów. Istniejącego verify.sh ani konfiguracji bramki nie nadpisuje.
Blokujących kontroli jest najwyżej pięć — reszta to ostrzeżenia.

Werdykt: gotowe / gotowe-z-brakami / brak-testow. Kod wyjścia: 0 — są testy; 1 — brak polecenia testów (fabryka nie
sprawdzi zmian) albo --verify czerwone; 2 — błąd wywołania. Tylko biblioteka standardowa, bez sieci.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
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
VERIFY = "./verify.sh"
VERIFY_KINDS = ("lint", "typecheck", "test")   # kolejność w verify.sh: od najszybszej kontroli
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"   # jak w install.py
COMMANDS = re.compile(r"(### Komendy\n)(.*?)(?=\n### |\n" + re.escape(MARK_END) + ")", re.S)
LABELS = {"test": "Test", "lint": "Lint", "typecheck": "Typecheck", "build": "Build"}


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


FLAG_FILES = ("config/flags.json", "flags.json", "feature-flags.json", "config/feature-flags.json",
              "config/feature_flags.json", "config/flags.yaml", "config/flags.yml", "flags.yaml", "flags.yml")
TEST_ENVS = ("test", "testing", "dev", "development", "local", "staging", "stage", "qa")
ENV_NAMES = (*TEST_ENVS, "uat", "preprod", "prod", "production", "live")


def detect_flags(root: Path) -> dict:
    """Plik flag funkcji i środowiska (z kluczy pliku JSON); puste pola, gdy niczego nie wykryto."""
    for rel in FLAG_FILES:
        if not (root / rel).is_file():
            continue
        data = _json(root / rel) if rel.endswith(".json") else {}
        top = [k for k in data if isinstance(data[k], dict)]
        envs = [k for k in top if k.lower() in ENV_NAMES]
        if not envs:                        # układ flaga → środowisko → stan
            envs = sorted({e for k in top for e in data[k] if str(e).lower() in ENV_NAMES})
        test = next((e for name in TEST_ENVS for e in envs if e.lower() == name), None)
        return {"file": rel, "envs": envs, "test_env": test}
    return {"file": None, "envs": [], "test_env": None}


def uses_verify(root: Path, det: dict) -> bool:
    """Czy bramka uruchamia verify.sh: jest już w repozytorium albo da się go wygenerować (nie w Windows)."""
    return os.name != "nt" and ((root / "verify.sh").is_file() or "test" in det["commands"])


def verify_script(det: dict) -> str:
    lines = ["#!/usr/bin/env bash",
             "# Jedno polecenie weryfikacji projektu: lint, typy, testy. Wygenerowane przez `tf onboard`.",
             "# Uruchamia je bramka jakości fabryki (.claude/quality-gate.json); to samo polecenie nadaje się do CI.",
             "# Gdy polecenia projektu się zmienią, popraw je tutaj.",
             "set -euo pipefail", 'cd "$(dirname "$0")"', ""]
    for kind in VERIFY_KINDS:
        if kind in det["commands"]:
            lines += [f'echo "== {NAMES[kind]}"', det["commands"][kind]["command"]]
    return "\n".join(lines) + "\n"


def blocking(det: dict, verify: bool = False) -> list[str]:
    """Kontrole, które zatrzymują pracę (najwyżej MAX_BLOCKING). Reszta to ostrzeżenia."""
    out = []
    for kind in (VERIFY_KINDS if verify else ("test",)):
        if kind in det["commands"]:
            out.append(f"{NAMES[kind].capitalize()}: `{det['commands'][kind]['command']}` — praca nie kończy się, "
                       "dopóki nie przejdą.")
    out.append("Sekrety: zapis kluczy i haseł do plików jest zatrzymywany.")
    out.append("Test przed kodem: kod produkcyjny bez wcześniejszego testu, który nie przechodzi, jest zatrzymywany.")
    return out[:MAX_BLOCKING]


def report(det: dict, verify: bool = False) -> str:
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
    lines += ["", "## Co fabryka blokuje"] + [f"- {b}" for b in blocking(det, verify)]
    warn = [f"{NAMES[k]} (`{cmds[k]['command']}`)" for k in (("build",) if verify else ("lint", "typecheck", "build"))
            if k in cmds]
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
    verify = uses_verify(root, det)
    if verify and (root / "verify.sh").is_file():
        say.append("• verify.sh już istnieje — zostaje bez zmian.")
    elif verify:
        files[root / "verify.sh"] = verify_script(det)
        say.append("• verify.sh — jedno polecenie weryfikacji: "
                   + " → ".join(NAMES[k] for k in VERIFY_KINDS if k in det["commands"]) + ".")
    command = VERIFY if verify else (det["commands"].get("test") or {}).get("command")
    gate = root / ".claude" / "quality-gate.json"
    if gate.is_file():
        say.append("• .claude/quality-gate.json już istnieje — zostaje bez zmian.")
    elif command:
        files[gate] = json.dumps({"command": command}, ensure_ascii=False, indent=2) + "\n"
        say.append(f"• .claude/quality-gate.json — bramka jakości z poleceniem `{command}`.")
    else:
        say.append("• bramka jakości zostaje wyłączona: nie wykryto polecenia testów.")
    line = commands_line(det, verify)
    for name in ("CLAUDE.local.md", "CLAUDE.md"):
        old = _read(root / name)
        new = with_commands(old, line) if line else old
        if new != old:
            files[root / name] = new
            say.append(f"• {name} — polecenia projektu w sekcji „Komendy”.")
    card = root / ".tf" / "config" / "operations.json"
    try:                                  # karta mogła powstać wcześniej bez flag (np. zapis trackera przez pętlę /tf)
        known = json.loads(card.read_text(encoding="utf-8")) if card.exists() else {}
    except (OSError, ValueError):
        known = None                      # nieczytelna karta zostaje nietknięta
    if isinstance(known, dict) and "flags" not in known:   # skąd fabryka wie, jak w projekcie działają flagi
        flags = detect_flags(root)
        files[card] = json.dumps({**known, "flags": flags}, ensure_ascii=False, indent=1) + "\n"
        say.append(f"• .tf/config/operations.json — karta operacyjna: plik flag {flags['file']}, środowiska "
                   f"{', '.join(flags['envs'])}, testowe: {flags['test_env']}." if flags["file"] else
                   "• .tf/config/operations.json — karta operacyjna: pliku flag funkcji nie wykryto; uzupełnij "
                   "`file`, `envs` i `test_env`, jeśli projekt używa flag (bez tego fabryka każe sprawdzać je ręcznie).")
    files[root / ".tf" / "reports" / "readiness.md"] = report(det, verify)
    say.append("• .tf/reports/readiness.md — raport gotowości.")
    return say, files


def commands_line(det: dict, verify: bool) -> str:
    parts = ([f"Weryfikacja: `{VERIFY}`"] if verify else []) + [
        f"{LABELS[k]}: `{det['commands'][k]['command']}`" for k in KINDS if k in det["commands"]]
    return "- " + " · ".join(parts) if parts else ""


def with_commands(text: str, line: str) -> str:
    """Podmienia treść podsekcji „Komendy” w bloku fabryki; plik bez bloku albo bez podsekcji zostaje bez zmian."""
    start = text.find(MARK_BEGIN)
    end = text.find(MARK_END, start)
    if start < 0 or end < 0:
        return text
    block = text[start:end + len(MARK_END)]
    return text[:start] + COMMANDS.sub(lambda m: m.group(1) + line + "\n", block, count=1) + text[end + len(MARK_END):]


def run_verify(root: Path, command: str, timeout: float = 900) -> tuple[bool, str]:
    """Uruchamia weryfikację raz (tylko z --verify): (zielona?, wyjście przycięte do początku i końca)."""
    try:
        r = subprocess.run(shlex.split(command), cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"przekroczony limit czasu {timeout:g} s"
    except OSError as e:
        return False, str(e)
    out = r.stdout + r.stderr
    saved = ".tf/logs/verify-output.txt"
    try:   # pełne wyjście do pliku; na ekran początek i koniec (pierwszy błąd bywa na początku logu)
        (root / ".tf" / "logs").mkdir(parents=True, exist_ok=True)
        (root / saved).write_text(out, encoding="utf-8")
    except OSError:
        pass
    if len(out) > 3000:
        out = out[:1000] + f"\n… [pominięto {len(out) - 3000} znaków; całość: {saved}] …\n" + out[-2000:]
    return r.returncode == 0, out


LOCAL_FILES = ("verify.sh", ".claude/quality-gate.json")   # pliki z tf onboard, które należą do repozytorium projektu


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return r.returncode, r.stdout.strip()


def settle_files(root: Path) -> str:
    """Co zrobić z plikami onboardingu w git. Instalacja prywatna niczego nie commituje, więc pliki zostają lokalne
    (wpis w .git/info/exclude) i drzewo robocze jest czyste; w zespołowej trafiają do commita. Zwraca zdanie dla człowieka."""
    code, exclude = _git(root, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude")
    if code != 0 or not exclude:
        return ""
    mine = [f for f in LOCAL_FILES if (root / f).is_file() and _git(root, "ls-files", "--error-unmatch", f)[0] != 0]
    if not mine:
        return ""
    if _json(root / ".claude" / "factory-manifest.json").get("mode") != "private":
        return "Do commita: " + ", ".join(mine) + " — wtedy kontrole działają u każdego po `git pull`."
    path = Path(exclude)
    have = _read(path).splitlines()
    new = [f for f in mine if f not in have]
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(("" if not have or have[-1] == "" else "\n") + "\n".join(new) + "\n")
    return ("Instalacja prywatna: " + ", ".join(mine) + " zostają lokalne (wpis w .git/info/exclude), "
            "więc drzewo robocze jest czyste. Żeby kontrole działały u całego zespołu: tf install --shared.")


def main(argv: list[str]) -> int:
    flags = set(argv[1:])
    unknown = flags - {"--yes", "--dry-run", "--json", "--verify", "-h", "--help"}
    if unknown or flags & {"-h", "--help"}:
        print(__doc__)
        return 2 if unknown else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    det = detect(root)
    code = 1 if det["verdict"] == "brak-testow" else 0
    if "--json" in flags:
        print(json.dumps(det, ensure_ascii=False, indent=2))
        return code
    print(report(det, uses_verify(root, det)))
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
        if path.name == "verify.sh":
            path.chmod(0o755)
    print("\n✓ Zapisano. Sprawdź stan: tf doctor")
    note = settle_files(root)
    if note:
        print(note)
    if "--verify" in flags:
        command = _json(root / ".claude" / "quality-gate.json").get("command")
        if not command:
            print("⚠ Nie ma czego uruchomić: bramka jakości nie ma polecenia.")
            return 1
        command = command if isinstance(command, str) else " ".join(map(str, command))
        ok, tail = run_verify(root, command)
        print(f"✓ Weryfikacja przechodzi: `{command}`." if ok
              else f"✗ Weryfikacja nie przechodzi: `{command}`. Napraw to przed pierwszym zadaniem.\n"
                   f"--- wyjście ---\n{tail}")
        return code if ok else 1
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
