"""Checks of out/: the knowledge.json contract, evidence that exists, Markdown in sync, size limits.

Returns a list of problems; an empty list means the output may be used. `learn` writes into a temporary directory
and replaces out/ only when this check passes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import emit

KINDS = {"fact", "block", "decision", "convention", "exemplar"}
STATUSES = {"candidate", "auto-accepted", "accepted", "abandoned", "unknown"}
ID = re.compile(r"^[A-Z]+(-[A-Za-z0-9.]+)+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_EVIDENCE = re.compile(r"^(https|file)://\S+ \(fetched \d{4}-\d{2}-\d{2}\)$")   # file://: a local git source
PATH_EVIDENCE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+)$")
INDEX_MAX_LINES = 15
DOCS_INDEX_MAX_BYTES = 8 * 1024


def check_knowledge(k: dict, root: Path) -> list[str]:
    problems = []
    if k.get("contract") != 1:
        problems.append(f"contract must be 1, got {k.get('contract')!r}")
    if not str(k.get("generator", "")).startswith("dna "):
        problems.append("generator must start with 'dna '")
    if not DATE.match(str(k.get("generated", ""))):
        problems.append("generated must be YYYY-MM-DD")
    cov = k.get("coverage")
    if not isinstance(cov, dict) or not isinstance(cov.get("read"), list) or not isinstance(cov.get("skipped"), list):
        problems.append("coverage must have lists 'read' and 'skipped'")
    seen = set()
    lines_cache: dict[str, int] = {}
    for i, item in enumerate(k.get("items") or []):
        where = f"items[{i}] {item.get('id', '?')}"
        for field in ("id", "kind", "title", "scope", "evidence", "status"):
            if field not in item:
                problems.append(f"{where}: missing '{field}'")
        if "id" in item:
            if not ID.match(str(item["id"])):
                problems.append(f"{where}: bad id")
            if item["id"] in seen:
                problems.append(f"{where}: duplicate id")
            seen.add(item["id"])
        if item.get("kind") not in KINDS:
            problems.append(f"{where}: unknown kind {item.get('kind')!r}")
        if item.get("status") not in STATUSES:
            problems.append(f"{where}: unknown status {item.get('status')!r}")
        if item.get("kind") == "decision" and item.get("strength") not in ("hard", "soft"):
            problems.append(f"{where}: a decision needs strength hard|soft")
        paths = (item.get("scope") or {}).get("paths")
        if not isinstance(paths, list) or not paths:
            problems.append(f"{where}: scope.paths must be a non-empty list")
        if "since" in item and not DATE.match(str(item["since"])):
            problems.append(f"{where}: since must be YYYY-MM-DD")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            problems.append(f"{where}: no evidence")
            continue
        for ev in evidence:
            problems += _check_evidence(str(ev), root, where, lines_cache)
    return problems


def _check_evidence(ev: str, root: Path, where: str, cache: dict) -> list[str]:
    if ev.startswith(("https://", "file://")):
        return [] if URL_EVIDENCE.match(ev) else [f"{where}: URL evidence needs '(fetched YYYY-MM-DD)': {ev}"]
    m = PATH_EVIDENCE.match(ev)
    if not m:
        return [f"{where}: evidence is not path:line or URL: {ev}"]
    rel = m.group("path")
    target = (root / rel).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        return [f"{where}: evidence outside the repository: {ev}"]
    if rel not in cache:
        try:
            cache[rel] = target.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        except OSError:
            cache[rel] = -1
    if cache[rel] < 0:
        return [f"{where}: evidence file does not exist: {ev}"]
    if not 1 <= int(m.group("line")) <= cache[rel]:
        return [f"{where}: evidence line out of range ({cache[rel]} lines): {ev}"]
    return []


def check_out(out: Path, root: Path) -> list[str]:
    kf = out / "knowledge.json"
    try:
        k = json.loads(kf.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{kf}: {e}"]
    problems = check_knowledge(k, root)
    expected = emit.render(k)
    for name, text in expected.items():
        f = out / name
        if not f.is_file():
            problems.append(f"{name}: missing (generated from knowledge.json)")
        elif f.read_text(encoding="utf-8") != text:
            problems.append(f"{name}: differs from knowledge.json (edit knowledge.json, not the Markdown)")
    index = out / "INDEX.md"
    if index.is_file() and len(index.read_text(encoding="utf-8").splitlines()) > INDEX_MAX_LINES:
        problems.append(f"INDEX.md: more than {INDEX_MAX_LINES} lines")
    docs_index = out / "docs-index.md"
    if docs_index.is_file() and docs_index.stat().st_size > DOCS_INDEX_MAX_BYTES:
        problems.append(f"docs-index.md: larger than {DOCS_INDEX_MAX_BYTES} bytes")
    return problems
