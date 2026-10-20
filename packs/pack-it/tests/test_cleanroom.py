#!/usr/bin/env python3
"""Testy clean-room dla projektantów testów: python3 tests/test_cleanroom.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOK = ROOT / ".claude" / "hooks" / "cleanroom_guard.py"
QA = "kasia-qa-analyst"

CASES = [
    # (agent, tool, tool_input, oczekiwana decyzja)
    (QA, "Read", {"file_path": "src/app/pricing/pricing.ts"}, "deny"),
    (QA, "Read", {"file_path": f"{ROOT}/src/Order.java"}, "deny"),
    (QA, "Read", {"file_path": "src/app/order.component.html"}, "deny"),
    (QA, "Read", {"file_path": "./libs/cart/src/lib/cart.service.ts"}, "deny"),
    (QA, "Read", {"file_path": "docs/project/03-requirements/requirements.md"}, "none"),
    (QA, "Read", {"file_path": f"{ROOT}/docs/project/05-plan/test-plan.md"}, "none"),
    (QA, "Read", {"file_path": "src/app/pricing/pricing.spec.ts"}, "none"),
    (QA, "Read", {"file_path": "e2e/order.spec.ts"}, "none"),
    (QA, "Read", {"file_path": "src/test/java/OrderTest.java"}, "none"),
    (QA, "Read", {"file_path": "libs/api/src/index.d.ts"}, "none"),
    (QA, "Read", {"file_path": "api/openapi.yaml"}, "none"),
    (QA, "Read", {"file_path": "package.json"}, "none"),
    (QA, "Read", {"file_path": "vitest.config.ts"}, "none"),
    (QA, "Read", {"file_path": "README.md"}, "none"),
    (QA, "Grep", {"pattern": "discount"}, "deny"),
    (QA, "Grep", {"pattern": "discount", "path": "src"}, "deny"),
    (QA, "Grep", {"pattern": "discount", "glob": "*.ts"}, "deny"),
    (QA, "Grep", {"pattern": "discount", "path": "src/pricing.ts"}, "deny"),
    (QA, "Grep", {"pattern": "rabat", "path": "docs"}, "none"),
    (QA, "Grep", {"pattern": "rabat", "path": "docs/project"}, "none"),
    (QA, "Grep", {"pattern": "TC-0", "glob": "*.spec.ts"}, "none"),
    (QA, "Grep", {"pattern": "rabat", "glob": "*.md"}, "none"),
    (QA, "Grep", {"pattern": "rabat", "type": "md"}, "none"),
    (QA, "Glob", {"pattern": "src/**/*.ts"}, "none"),
    (QA, "Bash", {"command": "cat src/pricing.ts"}, "deny"),
    ("plugin:kasia-qa-analyst", "Read", {"file_path": "src/pricing.ts"}, "deny"),
    # profil blind (allowlist) — generator wymagań na ślepo
    ("blind-analyst", "Read", {"file_path": "docs/project/02-domain/_blind/brief.md"}, "none"),
    ("blind-analyst", "Read", {"file_path": f"{ROOT}/docs/project/02-domain/_blind/competitors.md"}, "none"),
    ("blind-analyst", "Read", {"file_path": "docs/project/02-domain/context-map.md"}, "deny"),
    ("blind-analyst", "Read", {"file_path": "docs/project/02-domain/_blind/../context-map.md"}, "deny"),
    ("blind-analyst", "Read", {"file_path": "README.md"}, "deny"),
    ("blind-analyst", "Read", {"file_path": "src/app.ts"}, "deny"),
    ("blind-analyst", "Glob", {"pattern": "**/*"}, "deny"),
    ("blind-analyst", "Grep", {"pattern": "x", "path": "docs/project/02-domain/_blind"}, "deny"),
    ("blind-analyst", "Bash", {"command": "cat docs/project/02-domain/context-map.md"}, "deny"),
    ("blind-analyst", "WebFetch", {"url": "https://example.com"}, "deny"),
    ("blind-analyst", "Write", {"file_path": "docs/project/02-domain/_blind/requirements.md"}, "none"),
    ("ewa-blind-analyst", "Read", {"file_path": "src/app.ts"}, "deny"),
    # profil es-sim — uczestnicy symulacji widzą tylko prompty rund
    ("es-participant", "Read", {"file_path": "docs/training/es-sim/2026-09-27-a/rounds/01/recepcja.prompt.md"}, "none"),
    ("es-room", "Read", {"file_path": "docs/training/es-sim/2026-09-27-a/rounds/03/room.prompt.md"}, "none"),
    ("es-participant", "Read", {"file_path": ".claude/skills/ddd-es-simulation/scenarios/weterynaria/brief.md"}, "deny"),
    ("es-participant", "Read", {"file_path": "docs/training/es-sim/2026-09-27-a/state.json"}, "deny"),
    ("es-room", "Read", {"file_path": "docs/project/02-domain/corpus.md"}, "deny"),
    ("es-room", "Grep", {"pattern": "sprzeczn"}, "deny"),
    ("es-coach", "Read", {"file_path": ".claude/skills/ddd-es-simulation/scenarios/weterynaria/brief.md"}, "none"),
    # inni agenci — bez zmian
    ("kasia-qa-automation", "Read", {"file_path": "src/pricing.ts"}, "none"),
    ("filip-frontend", "Grep", {"pattern": "x"}, "none"),
    ("", "Read", {"file_path": "src/pricing.ts"}, "none"),
]


def run(agent: str, tool: str, ti: dict) -> str:
    payload = {"tool_name": tool, "tool_input": ti, "cwd": str(ROOT)}
    if agent:
        payload["agent_type"] = agent
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                       timeout=10, env=env)
    if not p.stdout.strip():
        return "none"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def main() -> int:
    fails = 0
    for agent, tool, ti, want in CASES:
        got = run(agent, tool, ti)
        if got != want:
            fails += 1
            print(f"✗ {agent or '(główny)'} {tool} {ti}: oczekiwano {want}, jest {got}")
    print(f"{'✓' if not fails else '✗'} {len(CASES) - fails}/{len(CASES)} testów clean-room")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
