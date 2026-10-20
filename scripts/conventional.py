"""Conventional Commits 1.0.0 i SemVer 2.0.0 dla wydań fabryki (docs/RELEASING.md): lint wiadomości, rodzaj podbicia,
wpis CHANGELOG i notatki wydania. Wspólne dla release.py, release_notes.py i check_commit_message.py.
Arytmetykę wersji (z fazą 0.y.z) liczy semver.py ze skilla core-semver — jedno źródło reguł."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "ctf_semver", ROOT / ".claude" / "skills" / "core-semver" / "scripts" / "semver.py")
semver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(semver)

# Typy przyjmowane w repozytorium (zestaw @commitlint/config-conventional).
TYPES = ["feat", "fix", "perf", "refactor", "test", "docs", "style", "build", "ci", "chore", "revert"]
MAX_SUBJECT = 72

HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()]*)\))?(?P<bang>!)?: (?P<subject>.*)$")
SCOPE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: \S", re.M)
# Wiadomości, które piszą git lub GitHub; na main nie trafiają w tej postaci (squash merge), więc ich nie lintujemy.
GENERATED = re.compile(r"^(Merge |Revert \"|(fixup|squash|amend)! )")
RELEASE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def first_line(message: str) -> str:
    return message.split("\n", 1)[0]


def parse_header(header: str) -> dict | None:
    m = HEADER.match(header.strip())
    if not m:
        return None
    return {"type": m["type"], "scope": m["scope"], "breaking": bool(m["bang"]), "subject": m["subject"]}


def is_breaking(message: str) -> bool:
    h = parse_header(first_line(message))
    return bool(h and h["breaking"]) or bool(BREAKING_FOOTER.search(message))


def clean(message: str) -> str:
    """Usuwa linie komentarza, które git wstawia do szablonu wiadomości."""
    text = "\n".join(ln for ln in message.replace("\r\n", "\n").split("\n") if not ln.startswith("#"))
    return re.sub(r"^\s*\n", "", text).rstrip()


def lint_message(raw: str) -> list[str]:
    """Problemy wiadomości commita lub tytułu PR; pusta lista = zgodna z Conventional Commits."""
    message = clean(raw)
    if not message:
        return ["wiadomość jest pusta"]
    header = first_line(message)
    if GENERATED.match(header):
        return []
    h = parse_header(header)
    if not h:
        return [f"„{header}” nie ma postaci „<typ>(<zakres>)!: <opis>” — np. „fix(build): odrzuć pusty opis persony”"]
    problems = []
    if h["type"] not in TYPES:
        problems.append(f"nieznany typ „{h['type']}” — użyj jednego z: {', '.join(TYPES)}")
    if h["scope"] is not None and not SCOPE.match(h["scope"]):
        problems.append(f"zakres „{h['scope']}” pisz małymi literami, np. build, install, hooks, core-semver, deps")
    subject = re.sub(r" \(#\d+\)$", "", h["subject"])   # numer PR, który GitHub dopisuje przy squash merge
    if not subject.strip():
        problems.append("opis po „: ” jest pusty")
    if len(subject) > MAX_SUBJECT:
        problems.append(f"opis ma {len(subject)} znaki (maksymalnie {MAX_SUBJECT})")
    if subject.endswith("."):
        problems.append("opis nie kończy się kropką")
    lines = message.split("\n")
    if len(lines) > 1 and lines[1].strip():
        problems.append("zostaw pustą linię między nagłówkiem a treścią")
    if re.search(r"^breaking[ -]change:", message, re.M | re.I) and not BREAKING_FOOTER.search(message):
        problems.append("stopkę pisz wielkimi literami: „BREAKING CHANGE: <co i jak migrować>”")
    return problems


def bump_kind(messages: list[str]) -> str | None:
    """Podbicie, którego wymagają commity: niezgodne → major, feat → minor, fix/perf → patch, reszta → brak."""
    kind = None
    for message in messages:
        if is_breaking(message):
            return "major"
        h = parse_header(first_line(message))
        t = h["type"] if h else None
        if t == "feat":
            kind = "minor"
        elif t in ("fix", "perf") and not kind:
            kind = "patch"
    return kind


def is_release(version: str) -> bool:
    return bool(RELEASE.match(version))


def _release(version: str) -> str:
    if not is_release(version):
        raise ValueError(f"„{version}” nie jest wersją wydania X.Y.Z")
    return version


def bump(current: str, kind: str) -> str:
    """Zwykłe podbicie X.Y.Z (reguły 6–8); jawne `major` na 0.y.z daje 1.0.0."""
    return semver.bump(_release(current), kind)


def next_version(current: str, kind: str) -> str:
    """Następna wersja z commitów; w fazie 0.y.z niezgodne → minor, reszta → patch. 1.0.0 nigdy nie jest liczone."""
    return semver.next_version(_release(current), kind)


def compare(a: str, b: str) -> int:
    return semver.compare(a, b)


# Nazwy sekcji po angielsku (Keep a Changelog), jak opisy commitów; starsze wpisy mają nazwy polskie.
SECTIONS = [("Breaking", lambda c: is_breaking(c["message"])),
            ("Added", lambda c: c["type"] == "feat"),
            ("Fixed", lambda c: c["type"] in ("fix", "perf"))]


def changelog_entry(version: str, date: str, messages: list[str]) -> str:
    """Wpis CHANGELOG (format factory/CHANGELOG.md) z commitów od ostatniego tagu; każdy commit trafia raz."""
    commits = [{"message": m, **h} for m in messages if (h := parse_header(first_line(m)))]
    out = [f"## [{version}] — {date}"]
    left = commits
    for title, match in SECTIONS:
        items = [c for c in left if match(c)]
        left = [c for c in left if not match(c)]
        if items:
            out.append(f"### {title}")
            out += [f"- **{c['scope']}:** {c['subject']}" if c["scope"] else f"- {c['subject']}" for c in items]
    if len(out) == 1:
        out.append("No user-visible changes (docs, tests, CI).")
    return "\n".join(out) + "\n"


def insert_entry(changelog: str, entry: str) -> str:
    """Wstawia wpis nad najnowszym (pod nagłówkiem i wstępem pliku)."""
    i = changelog.find("\n## [")
    if i < 0:
        return f"{changelog.rstrip()}\n\n{entry}"
    return f"{changelog[:i + 1]}{entry}\n{changelog[i + 1:]}"


def release_notes(changelog: str, version: str) -> str | None:
    """Treść wpisu `version` bez nagłówka „## [X.Y.Z]” albo None, gdy wpisu nie ma."""
    lines = changelog.replace("\r\n", "\n").split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"## [{version}]")), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    # Definicje linków („[2.6.0]: https://…”) na końcu pliku nie należą do wpisu.
    body = [ln for ln in lines[start + 1:end] if not re.match(r"^\[[^\]]+\]:\s", ln)]
    return "\n".join(body).strip() or None
