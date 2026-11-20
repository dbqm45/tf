"""Checks of out/ of the standards add-on: decisions with evidence that exists, Markdown in sync, size limits."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import emit

STATUSES = {"candidate", "auto-accepted", "accepted", "abandoned"}
ID = re.compile(r"^[A-Z]+(-[A-Za-z0-9.]+)+$")
URL_EVIDENCE = re.compile(r"^(https|file)://\S+ \(fetched \d{4}-\d{2}-\d{2}\)$")
PATH_EVIDENCE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+)$")


def check_knowledge(k: dict, root: Path) -> list[str]:
    problems = []
    if k.get("contract") != 1:
        problems.append("contract must be 1")
    seen, cache = set(), {}
    for i, item in enumerate(k.get("items") or []):
        where = f"items[{i}] {item.get('id', '?')}"
        if item.get("kind") != "decision" or not ID.match(str(item.get("id", ""))):
            problems.append(f"{where}: not a decision with a valid id")
        if item.get("id") in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(item.get("id"))
        if item.get("status") not in STATUSES or item.get("strength") not in ("hard", "soft"):
            problems.append(f"{where}: bad status or strength")
        if not (item.get("scope") or {}).get("paths"):
            problems.append(f"{where}: no scope.paths")
        if not item.get("evidence"):
            problems.append(f"{where}: no evidence")
        for ev in item.get("evidence") or []:
            if ev.startswith(("https://", "file://", "http://")):
                if not URL_EVIDENCE.match(ev) and not ev.startswith("http://"):
                    problems.append(f"{where}: URL evidence needs '(fetched YYYY-MM-DD)': {ev}")
                continue
            m = PATH_EVIDENCE.match(ev)
            if not m:
                problems.append(f"{where}: evidence is not path:line or URL: {ev}")
                continue
            target = (root / m.group("path")).resolve()
            if root.resolve() not in target.parents:
                problems.append(f"{where}: evidence outside the repository: {ev}")
                continue
            if m.group("path") not in cache:
                try:
                    cache[m.group("path")] = target.read_text(encoding="utf-8", errors="replace").count("\n") + 1
                except OSError:
                    cache[m.group("path")] = -1
            if not 1 <= int(m.group("line")) <= cache[m.group("path")]:
                problems.append(f"{where}: evidence missing or out of range: {ev}")
    return problems


def check_out(out: Path, root: Path) -> list[str]:
    try:
        k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"knowledge.json: {e}"]
    problems = check_knowledge(k, root)
    for name, text in emit.render(k).items():
        f = out / name
        if not f.is_file() or f.read_text(encoding="utf-8") != text:
            problems.append(f"{name}: missing or differs from knowledge.json")
    if len((out / "INDEX.md").read_text(encoding="utf-8").splitlines()) > emit.INDEX_MAX_LINES:
        problems.append("INDEX.md: too long")
    return problems
