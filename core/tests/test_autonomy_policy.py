#!/usr/bin/env python3
"""B1a: the autonomy policy in the guard_bash hook — named operation types with a level from the configuration.

python3 tests/test_autonomy_policy.py

The operation types the hook asks a human about (ASK) have names (`dependency_add`, `prod_command`, `destructive_sql`,
`infra_change`, `publish`, `git_push`, `persistence`, `data_upload`, `sudo`). The level from `autonomy.operations`
in `.tf/factory/config.yaml` and `.tf/config/config.yaml`: `confirm` (ask) or `deny` (block). A project can only
tighten (the human's decision of 2026-11-10, D1): loosening is ignored, and `--check-policy` reports it. The core
DENY list is fixed.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOK = ROOT / ".claude" / "hooks" / "guard_bash.py"


def output(cmd: str, project: Path) -> dict:
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)}, capture_output=True, text=True,
                       timeout=20)
    return json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else {}


def run(cmd: str, project: Path) -> str:
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)}, capture_output=True, text=True,
                       timeout=20)
    if not p.stdout.strip():
        return "none"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def project(t: Path, name: str, yaml: str | None) -> Path:
    d = t / name
    (d / ".tf" / "config").mkdir(parents=True)
    if yaml is not None:
        (d / ".tf" / "config" / "config.yaml").write_text(yaml, encoding="utf-8")
    return d


def org_pack(d: Path, body: str) -> None:
    """A company pack with `org_defaults` among the project's installed packs."""
    f = d / ".tf" / "factory" / "packs" / "pack-firma" / "pack.yaml"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("id: pack-firma\nversion: 0.1.0\ntitle: Firma\norg_defaults:\n" + body, encoding="utf-8")


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        plain = project(t, "plain", None)
        strict = project(t, "strict", "autonomy:\n  operations:\n    dependency_add: deny\n    git_push: deny\n")
        loose = project(t, "loose", "autonomy:\n  operations:\n    prod_command: full\n    destructive_sql: allow\n"
                                    "    nieznany_typ: deny\n")
        org = project(t, "org", None)
        org_pack(org, "  config:\n    autonomy:\n      operations:\n        git_push: deny\n")
        org_loose = project(t, "org-loose", "autonomy:\n  operations:\n    git_push: confirm\n")
        org_pack(org_loose, "  config:\n    autonomy:\n      operations:\n        git_push: deny\n")
        cases = [
            # A-7: the organisation's policy (a company pack) tightens; the project cannot loosen it
            (org, "git push origin feat/x", "deny"), (org_loose, "git push origin feat/x", "deny"),
            # A-1: without a project policy — behaviour as before
            (plain, "npm install left-pad", "ask"), (plain, "git push origin feat/x", "ask"),
            (plain, "psql -c 'DROP TABLE users'", "ask"), (plain, "npm test", "none"),
            # A-2: the project tightens — confirm -> deny
            (strict, "npm install left-pad", "deny"), (strict, "git push origin feat/x", "deny"),
            (strict, "psql -c 'DROP TABLE users'", "ask"),
            # A-3: the project tries to loosen — no effect (D1)
            (loose, "kubectl get pods --context prod", "ask"), (loose, "psql -c 'DROP TABLE users'", "ask"),
            # A-4: the core DENY list is fixed in every project
            (plain, "rm -rf /", "deny"), (loose, "git push --force origin main", "deny"),
        ]
        for proj, cmd, want in cases:
            got = run(cmd, proj)
            if got != want:
                fails.append(f"{proj.name}: `{cmd}` -> {want}, got {got}")
        # A-5: --check-policy reports loosening and unknown types, code 1; a valid policy — code 0
        bad = subprocess.run([sys.executable, str(HOOK), "--check-policy"], env={**os.environ, "CLAUDE_PROJECT_DIR": str(loose)},
                             capture_output=True, text=True, timeout=20)
        good = subprocess.run([sys.executable, str(HOOK), "--check-policy"], env={**os.environ, "CLAUDE_PROJECT_DIR": str(strict)},
                              capture_output=True, text=True, timeout=20)
        out = bad.stdout + bad.stderr
        # A-8: git push, reset --hard and clean -f each show their own plain description (the user reads
        # permissionDecisionReason in the permission prompt); the policy type stays `git_push` for all three
        seen = {}
        for cmd, words in (("git push origin feat/x", "sends your commits to the remote"),
                           ("git reset --hard HEAD~1", "uncommitted changes"),
                           ("git clean -fd", "untracked files"), ("git clean --force", "untracked files")):
            o = output(cmd, plain)
            reason = o.get("permissionDecisionReason", "")
            seen[cmd] = reason
            if o.get("permissionDecision") != "ask" or words not in reason or "git_push" not in reason \
                    or "/" in reason.split("git_push")[0]:
                fails.append(f"A-8: `{cmd}` asks with its own plain reason and the type git_push: {o}")
            o = output(cmd, strict)
            if o.get("permissionDecision") != "deny" or words not in o.get("permissionDecisionReason", ""):
                fails.append(f"A-8: `{cmd}` with git_push: deny is blocked with its own reason: {o}")
        if len(set(seen.values())) < 3:
            fails.append(f"A-8: the three git operations have separate reasons: {seen}")
        # A-9: two operations in one command → the prompt names both
        o = output("git reset --hard origin/main && git push origin main", plain)
        reason = o.get("permissionDecisionReason", "")
        if "sends your commits" not in reason or "uncommitted changes" not in reason:
            fails.append(f"A-9: a command with two consent operations names both: {reason}")
        if bad.returncode != 1 or "prod_command" not in out or "destructive_sql" not in out or "nieznany_typ" not in out \
                or good.returncode != 0:
            fails.append(f"A-5: --check-policy: {bad.returncode} {out[:400]} / {good.returncode} {good.stdout[:200]}")
    # A-6: the default levels described in the engine configuration (the policy documentation in one place)
    cfg = (ROOT / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8")
    if "autonomy:" not in cfg or "operations:" not in cfg or "dependency_add: confirm" not in cfg:
        fails.append("A-6: .tf/factory/config.yaml describes autonomy.operations with default values")
    for f in fails:
        print(f"✗ {f}")
    total = 25
    print(f"{'✓' if not fails else '✗'} autonomy policy: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
