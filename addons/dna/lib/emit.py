"""Markdown in out/ generated from knowledge.json. One source of truth: the Markdown never carries anything the JSON
does not, so the two cannot disagree (verify.check_out compares them byte for byte).
"""
from __future__ import annotations

import json
from pathlib import Path

INDEX_MAX_LINES = 15
CATEGORY_ORDER = ["language", "framework", "ui-framework", "design-system", "styling", "state", "data", "testing",
                  "tooling"]


def _stack(items: list[dict]) -> list[dict]:
    return [i for i in items if i.get("kind") == "fact" and i.get("data", {}).get("topic") == "stack"
            and i.get("status") != "abandoned"]


def _version(d: dict) -> str:
    return d.get("version") or f"{d.get('declared') or '?'} (range)"


def render_index(k: dict) -> str:
    items = k["items"]
    lines = ["# Project knowledge (dna)", ""]
    by_tech: dict[str, list[dict]] = {}
    for f in _stack(items):
        by_tech.setdefault(f["data"]["tech"], []).append(f)
    entries = []
    for tech, fs in sorted(by_tech.items(), key=lambda kv: (
            CATEGORY_ORDER.index(kv[1][0]["data"].get("category")) if kv[1][0]["data"].get("category")
            in CATEGORY_ORDER else 99, kv[0])):
        versions = sorted({_version(f["data"]) for f in fs})
        entries.append(f"{fs[0]['data']['name']} {' / '.join(versions)}")
    if entries:
        lines.append("- Stack: " + ", ".join(entries))
    runtimes = sorted({i["title"] for i in items if i.get("data", {}).get("topic") == "runtime"})
    if runtimes:
        lines.append("- Runtime: " + ", ".join(runtimes))
    cmds = [i["data"] for i in items if i.get("data", {}).get("topic") == "command"]
    if cmds:
        lines.append("- Commands: " + "; ".join(f"{c['command_kind']} `{c['command']}`" for c in cmds))
    tools = [i["data"] for i in items if i.get("data", {}).get("topic") == "tooling"]
    if tools:
        lines.append("- Formatting and lint are done by the tools, not by hand: "
                     + ", ".join(sorted({t["tool"] for t in tools})))
    hard = [i for i in items if i.get("kind") == "decision" and i.get("strength") == "hard"
            and i.get("status") in ("accepted", "auto-accepted") and i["scope"]["paths"] == ["**"]]
    for d in hard[: max(0, INDEX_MAX_LINES - len(lines) - 3)]:
        lines.append(f"- [hard] {d['title']} ({d['id']})")
    lines.append("- Use the versions above; for anything else see `knowledge.json` and `coverage.md` in this directory.")
    return "\n".join(lines[:INDEX_MAX_LINES]) + "\n"


def render_coverage(k: dict) -> str:
    cov = k["coverage"]
    lines = ["# Coverage", "", f"Generated {k['generated']} by {k['generator']}.", "", "## Read", ""]
    lines += [f"- {s}" for s in cov["read"]] or ["- (nothing)"]
    lines += ["", "## Not read", ""]
    lines += [f"- {s['source']}: {s['reason']}" for s in cov["skipped"]] or ["- (nothing)"]
    if cov.get("notes"):
        lines += ["", "## Notes", ""] + [f"- {n}" for n in cov["notes"]]
    stack = _stack(k["items"])
    ranged = [f for f in stack if not f["data"].get("version")]
    if ranged:
        lines += ["", "## Versions without a lockfile", ""]
        lines += [f"- {f['data']['name']} in {f['data']['package_dir']}: declared {f['data']['declared']}"
                  for f in ranged]
    return "\n".join(lines) + "\n"


def render(k: dict) -> dict[str, str]:
    """File name in out/ -> content."""
    return {"INDEX.md": render_index(k), "coverage.md": render_coverage(k)}


def write(k: dict, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "knowledge.json").write_text(json.dumps(k, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, text in render(k).items():
        (out / name).write_text(text, encoding="utf-8")
