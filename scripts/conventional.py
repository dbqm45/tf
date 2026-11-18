"""Conventional Commits 1.0.0 and SemVer 2.0.0 for factory releases (docs/RELEASING.md): message lint, bump kind,
CHANGELOG entry and release notes. Shared by release.py, release_notes.py and check_commit_message.py.
Version arithmetic (with the 0.y.z phase) is computed by semver.py from the core-semver skill — a single source of rules."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "ctf_semver", ROOT / "core" / "skills" / "core-semver" / "scripts" / "semver.py")
semver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(semver)

# Typy przyjmowane w repozytorium (zestaw @commitlint/config-conventional).
TYPES = ["feat", "fix", "perf", "refactor", "test", "docs", "style", "build", "ci", "chore", "revert"]
MAX_SUBJECT = 72

HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()]*)\))?(?P<bang>!)?: (?P<subject>.*)$")
SCOPE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: \S", re.M)
# Messages written by git or GitHub; they do not reach main in this form (squash merge), so we do not lint them.
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
    """Removes the comment lines that git inserts into the message template."""
    text = "\n".join(ln for ln in message.replace("\r\n", "\n").split("\n") if not ln.startswith("#"))
    return re.sub(r"^\s*\n", "", text).rstrip()


def lint_message(raw: str) -> list[str]:
    """Problems with a commit message or PR title; an empty list = conforms to Conventional Commits."""
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
    subject = re.sub(r" \(#\d+\)$", "", h["subject"])   # the PR number that GitHub appends on squash merge
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
    """The bump the commits require: breaking → major, feat → minor, fix/perf → patch, the rest → none."""
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
    """A regular X.Y.Z bump (rules 6–8); an explicit `major` on 0.y.z gives 1.0.0."""
    return semver.bump(_release(current), kind)


def next_version(current: str, kind: str) -> str:
    """The next version from commits; in the 0.y.z phase breaking → minor, the rest → patch. 1.0.0 is never computed."""
    return semver.next_version(_release(current), kind)


def compare(a: str, b: str) -> int:
    return semver.compare(a, b)


# Section names in English (Keep a Changelog), like commit descriptions; older entries have Polish names.
SECTIONS = [("Breaking", lambda c: is_breaking(c["message"])),
            ("Added", lambda c: c["type"] == "feat"),
            ("Fixed", lambda c: c["type"] in ("fix", "perf"))]


def changelog_entry(version: str, date: str, messages: list[str]) -> str:
    """A CHANGELOG entry (the core/factory/CHANGELOG.md format) from commits since the last tag; each commit appears once."""
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
    """Inserts an entry above the newest one (under the file header and intro)."""
    i = changelog.find("\n## [")
    if i < 0:
        return f"{changelog.rstrip()}\n\n{entry}"
    return f"{changelog[:i + 1]}{entry}\n{changelog[i + 1:]}"


def release_notes(changelog: str, version: str) -> str | None:
    """The body of the `version` entry without the "## [X.Y.Z]" heading, or None when there is no entry."""
    lines = changelog.replace("\r\n", "\n").split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"## [{version}]")), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    # Link definitions ("[2.6.0]: https://…") at the end of the file do not belong to the entry.
    body = [ln for ln in lines[start + 1:end] if not re.match(r"^\[[^\]]+\]:\s", ln)]
    return "\n".join(body).strip() or None
