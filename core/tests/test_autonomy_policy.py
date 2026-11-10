#!/usr/bin/env python3
"""B1a: polityka autonomii w hooku guard_bash — nazwane typy operacji z poziomem z konfiguracji.

python3 tests/test_autonomy_policy.py

Typy operacji, o które hook pyta człowieka (ASK), mają nazwy (`dependency_add`, `prod_command`, `destructive_sql`,
`infra_change`, `publish`, `git_push`, `persistence`, `data_upload`, `sudo`). Poziom z `autonomy.operations`
w `.tf/factory/config.yaml` i `.tf/config/config.yaml`: `confirm` (pytaj) albo `deny` (blokuj). Projekt może tylko
zaostrzać (decyzja człowieka 2026-11-10, D1): rozluźnienie jest ignorowane, a `--check-policy` je zgłasza. Lista
DENY rdzenia jest stała.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
HOOK = ROOT / ".claude" / "hooks" / "guard_bash.py"


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


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        plain = project(t, "plain", None)
        strict = project(t, "strict", "autonomy:\n  operations:\n    dependency_add: deny\n    git_push: deny\n")
        loose = project(t, "loose", "autonomy:\n  operations:\n    prod_command: full\n    destructive_sql: allow\n"
                                    "    nieznany_typ: deny\n")
        cases = [
            # A-1: bez polityki projektu — zachowanie jak dotąd
            (plain, "npm install left-pad", "ask"), (plain, "git push origin feat/x", "ask"),
            (plain, "psql -c 'DROP TABLE users'", "ask"), (plain, "npm test", "none"),
            # A-2: projekt zaostrza — confirm → deny
            (strict, "npm install left-pad", "deny"), (strict, "git push origin feat/x", "deny"),
            (strict, "psql -c 'DROP TABLE users'", "ask"),
            # A-3: projekt próbuje rozluźnić — bez skutku (D1)
            (loose, "kubectl get pods --context prod", "ask"), (loose, "psql -c 'DROP TABLE users'", "ask"),
            # A-4: lista DENY rdzenia stała w każdym projekcie
            (plain, "rm -rf /", "deny"), (loose, "git push --force origin main", "deny"),
        ]
        for proj, cmd, want in cases:
            got = run(cmd, proj)
            if got != want:
                fails.append(f"{proj.name}: `{cmd}` → {want}, jest {got}")
        # A-5: --check-policy zgłasza rozluźnienia i nieznane typy, kod 1; poprawna polityka — kod 0
        bad = subprocess.run([sys.executable, str(HOOK), "--check-policy"], env={**os.environ, "CLAUDE_PROJECT_DIR": str(loose)},
                             capture_output=True, text=True, timeout=20)
        good = subprocess.run([sys.executable, str(HOOK), "--check-policy"], env={**os.environ, "CLAUDE_PROJECT_DIR": str(strict)},
                              capture_output=True, text=True, timeout=20)
        out = bad.stdout + bad.stderr
        if bad.returncode != 1 or "prod_command" not in out or "destructive_sql" not in out or "nieznany_typ" not in out \
                or good.returncode != 0:
            fails.append(f"A-5: --check-policy: {bad.returncode} {out[:400]} / {good.returncode} {good.stdout[:200]}")
    # A-6: domyślne poziomy opisane w konfiguracji silnika (dokumentacja polityki w jednym miejscu)
    cfg = (ROOT / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8")
    if "autonomy:" not in cfg or "operations:" not in cfg or "dependency_add: confirm" not in cfg:
        fails.append("A-6: .tf/factory/config.yaml opisuje autonomy.operations z wartościami domyślnymi")
    for f in fails:
        print(f"✗ {f}")
    total = 13
    print(f"{'✓' if not fails else '✗'} polityka autonomii: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
