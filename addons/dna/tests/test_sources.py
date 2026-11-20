#!/usr/bin/env python3
"""Tests of decisions from sources (lib/sources.py, lib/decide.py) and their output (rules/standards*.md,
decisions.md). Confluence is a local HTTP server. python3 addons/dna/tests/test_sources.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import decide, emit, sources, verify  # noqa: E402
from test_dna import evidence_ok, repo  # noqa: E402
from test_docs import serve  # noqa: E402

PAGE = "<h1>FE standards</h1><ul><li>Components must have a Storybook story.</li><li>Prefer server components for data fetching.</li></ul>"


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


def collect(root, online=False, opts=None):
    found, cov = sources.collect(root, {}, online, "2026-11-20", opts)
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
                evidence_ok(root, {"evidence": [ev]})
    skipped = {s["source"]: s["reason"] for s in cov["skipped"]}
    assert "network off" in skipped["https://acme.atlassian.net/wiki/spaces/FE/pages/123/Standards"]
    assert "outside Confluence" in skipped["https://example.com/blog/post"]


def test_confluence_page_followed_with_credentials():
    routes = {"/wiki/rest/api/content/123?expand=body.storage,version":
              json.dumps({"body": {"storage": {"value": PAGE}}, "version": {"number": 7}}).encode()}
    base, srv = serve(routes)
    try:
        root = repo(files(base))
        ds, cov = collect(root, online=True, opts={"allow_private": True, "confluence_auth": ("a@b.c", "tok")})
        t = by_text(ds)
        story = t["Components must have a Storybook story"]
        assert story["strength"] == "hard" and story["evidence"][0] == f"{base}/wiki/spaces/FE/pages/123/Standards (fetched 2026-11-20)"
        assert any("(version 7)" in r for r in cov["read"])
    finally:
        srv.shutdown()


def test_credentials_never_go_to_another_host():
    for url, word in (("https://evil.example/wiki/pages/1", "not the Atlassian site"),
                      ("http://acme.atlassian.net/wiki/pages/1", "only https")):
        try:
            sources.confluence_page(url, {"confluence_host": "acme.atlassian.net", "confluence_auth": ("a", "b")})
            raise AssertionError(f"{url} accepted")
        except ValueError as e:
            assert word in str(e), e


def test_output_rules_and_index():
    root = repo(files())
    out = root / "out"
    assert dna.cmd_learn(root, out, online=False, cache=root / "cache") == 0
    assert verify.check_out(out, root) == []
    fe = (out / "rules" / "standards-fe.md").read_text(encoding="utf-8")
    assert fe.startswith("---\npaths:\n") and "[hard] Spacing must use the space.* tokens" in fe and "(FE-UI-001)" in fe
    assert (out / "rules" / "standards-be.md").is_file()
    common = (out / "rules" / "standards.md").read_text(encoding="utf-8")
    assert "Every PR must reference a Jira key" in common and "Use conventional commits" not in common
    dec = (out / "decisions.md").read_text(encoding="utf-8")
    assert "## Candidates (one source, not applied)" in dec and "Use conventional commits" in dec
    index = (out / "INDEX.md").read_text(encoding="utf-8")
    assert "Standards:" in index and "[hard] Every PR must reference a Jira key" in index
    for f in (out / "rules").glob("*.md"):
        assert len(f.read_text(encoding="utf-8").splitlines()) <= emit.RULES_MAX_LINES


def test_long_rule_list_is_cut_with_a_pointer():
    many = "# S\n" + "".join(f"- Rule {i} must hold for module number {i}.\n" for i in range(80))
    root = repo({".claude/skills/acme-common-standards/SKILL.md": many})
    out = root / "out"
    assert dna.cmd_learn(root, out, online=False, cache=root / "cache") == 0
    text = (out / "rules" / "standards.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= emit.RULES_MAX_LINES and "more in `.tf/addons/dna/out/decisions.md`" in text


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
