#!/usr/bin/env python3
"""
Hook commit-msg: Conventional Commits 1.0.0 i ślad zmiany w stopkach (skill core-conventional-commits).

  python3 .claude/skills/core-conventional-commits/scripts/commit_msg.py check <plik-wiadomości>
  python3 .claude/skills/core-conventional-commits/scripts/commit_msg.py install

`check` sprawdza:
  - nagłówek `<typ>(<zakres>)!: <opis>` — typ małymi literami, opis niepusty, ≤ 72 znaki, bez kropki na końcu;
    pusta linia po nagłówku; `BREAKING CHANGE` wielkimi literami. Zakres dowolny (konwencja projektu).
    Wiadomości gita (`Merge …`, `Revert "…"`, `fixup!`, `squash!`, `amend!`) przechodzą bez sprawdzania.
  - stopkę `Change: TSK-57` (klucz zmiany albo cięcia, kilka po przecinku) — klucz w kształcie `[A-Z][A-Z0-9]+-[0-9]+`;
  - stopkę `Flag: payment-retry` — jeden klucz flagi, bez spacji;
  - gałąź z kluczem w nazwie (np. `story/tsk-57-ponowienie`) — wymagany `Change:` z tym kluczem.
`install` zapisuje hook `commit-msg` w katalogu hooków gita (szanuje `core.hooksPath`); cudzego hooka nie nadpisuje.

Kod wyjścia: 0 — w porządku, 1 — wiadomość odrzucona albo hook nie zainstalowany, 2 — złe wywołanie.
Tylko biblioteka standardowa Pythona 3.9+.
"""
from __future__ import annotations

import re
import stat
import subprocess
import sys
from pathlib import Path

MAX_SUBJECT = 72
KEY = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
BRANCH_KEY = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*-[0-9]+)(?![0-9])")
HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()]+)\))?(?P<bang>!)?: (?P<subject>.*)$")
GENERATED = re.compile(r"^(Merge |Revert \"|(fixup|squash|amend)! )")
FLAG = re.compile(r"^[A-Za-z0-9._-]+$")
MARK = "core-conventional-commits/scripts/commit_msg.py"   # rozpoznanie własnego hooka przy ponownym install
HOOK = f"""#!/bin/sh
# Factory commit-msg hook: Conventional Commits and Change:/Flag: footers ({MARK})
exec python3 "$(git rev-parse --show-toplevel)/.claude/skills/{MARK}" check "$1"
"""


def clean(message: str) -> str:
    """Bez linii komentarza i bez części pod linią nożyczek, które git wstawia do szablonu wiadomości."""
    lines = []
    for ln in message.replace("\r\n", "\n").split("\n"):
        if ln.startswith("# ------------------------ >8 ------------------------"):
            break
        if not ln.startswith("#"):
            lines.append(ln)
    return "\n".join(lines).strip("\n").rstrip()


def trailers(message: str, token: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(rf"^{token}:[ \t]*(.*)$", message, re.M)]


def branch() -> str:
    r = subprocess.run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def lint(raw: str, branch_name: str = "") -> list[str]:
    message = clean(raw)
    if not message:
        return ["the message is empty"]
    header = message.split("\n", 1)[0]
    if GENERATED.match(header):
        return []
    problems = []
    h = HEADER.match(header.strip())
    if not h:
        problems.append(f"\"{header}\" does not have the form \"<type>(<scope>)!: <subject>\" — type in lowercase, e.g. "
                        "\"feat(payments): retry failed payment\"")
    else:
        subject = re.sub(r" \(#\d+\)$", "", h["subject"])   # numer PR, który GitHub dopisuje przy squash merge
        if not subject.strip():
            problems.append("the subject after \": \" is empty")
        if len(subject) > MAX_SUBJECT:
            problems.append(f"the subject has {len(subject)} characters (maximum {MAX_SUBJECT})")
        if subject.endswith("."):
            problems.append("the subject must not end with a period")
    lines = message.split("\n")
    if len(lines) > 1 and lines[1].strip():
        problems.append("leave a blank line between the header and the body")
    if re.search(r"^breaking[ -]change:", message, re.M | re.I) and not re.search(r"^BREAKING[ -]CHANGE: \S", message, re.M):
        problems.append("write the footer in uppercase: \"BREAKING CHANGE: <what changed and how to migrate>\"")
    keys = []
    for value in trailers(message, "Change"):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        if not parts:
            problems.append("the \"Change:\" footer has no key — e.g. \"Change: TSK-57\"")
        for p in parts:
            if KEY.match(p):
                keys.append(p)
            else:
                problems.append(f"\"Change: {p}\" — the key must match [A-Z][A-Z0-9]+-[0-9]+, e.g. TSK-57 or CHG-12")
    for value in trailers(message, "Flag"):
        if not FLAG.match(value):
            problems.append(f"\"Flag: {value}\" — one flag key without spaces, e.g. \"Flag: payment-retry\"")
    for m in BRANCH_KEY.finditer(branch_name):
        want = m.group(1).upper()
        if KEY.match(want) and want not in keys:
            problems.append(f"branch \"{branch_name}\" belongs to {want} — add the footer (after a blank line): \"Change: {want}\"")
    return problems


def check(path: str) -> int:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ cannot read the message: {e}", file=sys.stderr)
        return 2
    problems = lint(raw, branch())
    if problems:
        print("✗ commit rejected (commit-msg hook, core-conventional-commits):\n"
              + "\n".join(f"  - {p}" for p in problems))
        return 1
    return 0


def install() -> int:
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], capture_output=True, text=True)
    if r.returncode:
        print("✗ this is not a git repository")
        return 1
    hooks = Path(r.stdout.strip())
    hook = hooks / "commit-msg"
    if hook.exists() and MARK not in hook.read_text(encoding="utf-8", errors="ignore"):
        print(f"✗ {hook} already exists (another hook) — not overwriting it. Add this line at its end:\n"
              f'  python3 "$(git rev-parse --show-toplevel)/.claude/skills/{MARK}" check "$1" || exit 1')
        return 1
    hooks.mkdir(parents=True, exist_ok=True)
    hook.write_text(HOOK, encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"✓ hook commit-msg: {hook}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"] and len(argv) == 2:
        return check(argv[1])
    if argv == ["install"]:
        return install()
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
