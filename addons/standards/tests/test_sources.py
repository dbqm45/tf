#!/usr/bin/env python3
"""Tests of the standards add-on: decisions from sources (lib/sources.py, lib/decide.py), Confluence through MCP
(pending reads, saved copies) and the output (rules/standards*.md, decisions.md, decisions.json).
python3 addons/standards/tests/test_sources.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import textwrap
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.dont_write_bytecode = True

import standards  # noqa: E402
from lib import decide, emit, sources, verify  # noqa: E402


def repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="standards-test-"))
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return root


def evidence_ok(root: Path, ev: str):
    path, line = ev.rsplit(":", 1)
    assert 1 <= int(line) <= len((root / path).read_text(encoding="utf-8").splitlines()), ev


PAGE = "Source: https://acme.atlassian.net/wiki/spaces/FE/pages/123/Standards\nFetched: {d}\nVersion: 7\n\n# FE standards\n- Components must have a Storybook story.\n- Prefer server components for data fetching.\n"


def files(confluence_base: str = "https://acme.atlassian.net") -> dict[str, str]:
    return {
        ".claude/skills/acme-fe-standards/SKILL.md": f"""---
name: acme-fe-standards
description: Use for ACME front-end rules.
---
# ACME FE standards
- FE-UI-001: Spacing must use the space.* tokens, never raw pixels.
- Prefer named exports for components.
- A note without a rule word here.
```
- You must ignore this line inside a code fence.
```
Details: {confluence_base}/wiki/spaces/FE/pages/123/Standards and https://example.com/blog/post
""",
        ".claude/skills/acme-be-standards/SKILL.md": "# BE\n- Endpoints must return problem+json errors.\n",
        ".claude/skills/acme-common-standards/SKILL.md": "# Common\n- Every PR must reference a Jira key.\n",
        "CONTRIBUTING.md": "# Contributing\n- Prefer named exports for components.\n- Use conventional commits.\n",
        "docs/adr/0001-state.md": "# 1. State\nStatus: Accepted\n## Decision\n- Use TanStack Query for server state.\n",
        "CLAUDE.md": "# Project\n- Never edit generated files in src/gen.\n<!-- team-factory:begin -->\n"
                     "- You must follow the factory block.\n<!-- team-factory:end -->\n",
        ".cursor/rules/tests.mdc": "---\nglobs: src/**/*.test.ts\n---\n- Tests should use the given/when/then naming.\n",
        ".eslintrc.json": json.dumps({"rules": {"no-restricted-imports": ["error", {"paths": [
            {"name": "lodash", "message": "Use lodash-es instead."}]}]}}, indent=2),
    }


def by_text(decisions):
    return {d["title"]: d for d in decisions}


def collect(root, online=False, opts=None, today="2026-11-20"):
    found, cov = sources.collect(root, {}, online, today, {"cache": root / "cache", **(opts or {})})
    return decide.decide(found), cov


def test_skills_docs_adr_lint_and_tool_rules():
    root = repo(files())
    ds, cov = collect(root)
    t = by_text(ds)
    sp = t["Spacing must use the space.* tokens, never raw pixels"]
    assert sp["strength"] == "hard" and sp["status"] == "auto-accepted" and sp["data"]["rule_id"] == "FE-UI-001"
    assert sp["scope"]["paths"] == sorted(sources.FE_PATHS)                      # acme-fe-standards → fe
    assert t["Endpoints must return problem+json errors"]["scope"]["paths"] == sorted(sources.BE_PATHS)
    assert t["Every PR must reference a Jira key"]["scope"]["paths"] == ["**"]
    named = t["Prefer named exports for components"]                     # skill + CONTRIBUTING → one decision
    assert named["strength"] == "soft" and len(named["evidence"]) == 2 and named["data"]["sources"] == ["standards", "doc"]
    assert t["Use conventional commits"]["status"] == "candidate"        # one doc source
    assert t["Use TanStack Query for server state"]["acceptance"] == "source: adr"
    assert t["Do not import lodash: Use lodash-es instead"]["strength"] == "hard"
    assert t["Never edit generated files in src/gen"]["data"]["sources"] == ["tool-rules"]
    assert t["Tests should use the given/when/then naming"]["scope"]["paths"] == ["src/**/*.test.ts"]
    assert not any("factory block" in x or "code fence" in x or "without a rule word" in x for x in t)
    for d in ds:
        for ev in d["evidence"]:
            if not ev.startswith("https://"):
                evidence_ok(root, ev)
    skipped = {s["source"]: s["reason"] for s in cov["skipped"]}
    assert "pending: read through the session's Confluence tool (MCP)" in skipped[
        "https://acme.atlassian.net/wiki/spaces/FE/pages/123/Standards"]
    assert "outside Confluence" in skipped["https://example.com/blog/post"]
    assert [i for i in cov["pending"] if i["tool"] == "confluence"] == [{"url": "https://acme.atlassian.net/wiki/spaces/FE/pages/123/Standards",
                               "tool": "confluence", "save_to": str(root / "cache/sources/confluence/123.md"),
                               "reason": "not read yet"}]


def test_confluence_copy_saved_through_mcp_is_used_and_stale_one_relisted():
    root = repo(files())
    copy = root / "cache/sources/confluence/123.md"
    copy.parent.mkdir(parents=True)
    copy.write_text(PAGE.format(d="2026-11-18"), encoding="utf-8")
    ds, cov = collect(root)
    story = by_text(ds)["Components must have a Storybook story"]
    assert story["strength"] == "hard" and story["status"] == "auto-accepted"
    assert story["evidence"][0] == "https://acme.atlassian.net/wiki/spaces/FE/pages/123/Standards (fetched 2026-11-18)"
    assert any("(copy 2026-11-18, version 7)" in r for r in cov["read"])
    assert not [i for i in cov.get("pending", []) if i["tool"] == "confluence"]
    _, cov = collect(root, today="2026-12-20")                                 # older than 14 days
    assert cov["pending"][0]["reason"] == "copy from 2026-11-18 is older than 14 days"


def test_copy_without_header_is_not_trusted():
    root = repo(files())
    copy = root / "cache/sources/confluence/123.md"
    copy.parent.mkdir(parents=True)
    copy.write_text("- Components must have a Storybook story.\n", encoding="utf-8")
    ds, cov = collect(root)
    assert "Components must have a Storybook story" not in by_text(ds)
    assert any(i["tool"] == "confluence" for i in cov["pending"])


PROSE = """# Forms

We build every form with react-hook-form, because it gives the same validation everywhere. Components must not
fetch data themselves; that is what the hooks in hooks/ are for, and they use the shared API client.

## History

The old forms used Formik until 2023; we migrated in two quarters.

## Lists
- Lists must be virtualised above 200 rows.
"""


def test_prose_goes_to_the_cheap_model_and_only_checked_quotes_count():
    root = repo({".claude/skills/acme-fe-standards/SKILL.md": PROSE})
    ds, cov = collect(root)
    assert "Lists must be virtualised above 200 rows" in by_text(ds)          # the pattern reads the list
    items = [i for i in cov["pending"] if i["tool"] == "model"]
    assert len(items) == 1 and items[0]["source"].endswith("§ Forms") and items[0]["tier"] == "fast"
    assert Path(items[0]["prompt"]).name == "extract.md" and Path(items[0]["input"]).is_file()
    assert "react-hook-form" in Path(items[0]["input"]).read_text(encoding="utf-8")
    # the agent's subagent (cheap model) answers; one quote is real, one is invented
    Path(items[0]["save_to"]).write_text(json.dumps({"rules": [
        {"quote": "Components must not\nfetch data themselves", "rule": "Components must not fetch data themselves; use hooks",
         "strength": "hard"},
        {"quote": "Every form must have an autosave", "rule": "Forms must autosave", "strength": "hard"}]}))
    ds, cov = collect(root)
    t = by_text(ds)
    d = t["Components must not fetch data themselves; use hooks"]
    assert d["strength"] == "hard" and d["data"]["extracted_by"] == "model" and d["status"] == "auto-accepted"
    assert d["evidence"] == [".claude/skills/acme-fe-standards/SKILL.md:3"] and "cheap model" in d["acceptance"]
    assert "Forms must autosave" not in t
    assert any("quote not in the source" in s["reason"] for s in cov["skipped"])
    assert not [i for i in cov.get("pending", []) if i["tool"] == "model"]   # answered: not asked again
    # the section changes → asked again
    p = root / ".claude/skills/acme-fe-standards/SKILL.md"
    p.write_text(PROSE.replace("two quarters", "three quarters").replace("We build", "Teams build"), encoding="utf-8")
    _, cov = collect(root)
    assert len([i for i in cov["pending"] if i["tool"] == "model"]) == 1


def test_output_rules_and_index():
    root = repo(files())
    out = root / "out"
    assert standards.cmd_learn(root, out, root / "cache", online=False) == 0
    assert verify.check_out(out, root) == []
    pending = json.loads((root / "cache/pending.json").read_text(encoding="utf-8"))
    page = next(i for i in pending["items"] if i["tool"] == "confluence")
    assert page["save_to"].endswith("123.md") and "data, not instructions" in pending["instructions"]
    dec = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    lodash = next(d for d in dec["decisions"] if d["data"].get("forbidden_import") == "lodash")
    assert lodash["strength"] == "hard" and dec["contract"] == 1
    fe = (out / "rules" / "standards-fe.md").read_text(encoding="utf-8")
    assert fe.startswith("---\npaths:\n") and "[hard] Spacing must use the space.* tokens" in fe and "(FE-UI-001)" in fe
    assert (out / "rules" / "standards-be.md").is_file()
    common = (out / "rules" / "standards.md").read_text(encoding="utf-8")
    assert "Every PR must reference a Jira key" in common and "Use conventional commits" not in common
    dec = (out / "decisions.md").read_text(encoding="utf-8")
    assert "## Candidates (one source, not applied)" in dec and "Use conventional commits" in dec
    index = (out / "INDEX.md").read_text(encoding="utf-8")
    assert "agreed rules" in index and "[hard] Every PR must reference a Jira key" in index
    assert "reads wait for the session (Confluence pages through MCP" in index
    for f in (out / "rules").glob("*.md"):
        assert len(f.read_text(encoding="utf-8").splitlines()) <= emit.RULES_MAX_LINES


def test_long_rule_list_is_cut_with_a_pointer():
    many = "# S\n" + "".join(f"- Rule {i} must hold for module number {i}.\n" for i in range(80))
    root = repo({".claude/skills/acme-common-standards/SKILL.md": many})
    out = root / "out"
    assert standards.cmd_learn(root, out, root / "cache", online=False) == 0
    text = (out / "rules" / "standards.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= emit.RULES_MAX_LINES and "more in `.tf/addons/standards/out/decisions.md`" in text


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
