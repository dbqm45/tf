#!/usr/bin/env python3
"""Tests of the stack filter in the skill_hint hook: in a project with a detected stack the hook does not suggest framework
and language skills (`fw-`, `lang-`) from the technology registry that the project does not have — unless the command names them.
Measurement 2026-11-16 (docs/todo.md): in a Spring Boot repo the hook suggested fw-nestjs and the agent loaded it.
python3 core/tests/test_skill_hint_stack.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".claude" / "hooks" / "skill_hint.py").is_file()
            or (p / "core" / "hooks" / "skill_hint.py").is_file())
HOOKS = ROOT / ".claude" / "hooks" if (ROOT / ".claude" / "hooks" / "skill_hint.py").is_file() else ROOT / "core" / "hooks"
# Our own technology registry (the core-stack-sync/references/technologies.json format): the test does not depend on packs.
REGISTRY = {"technologies": [
    {"id": "spring-boot", "name": "Spring Boot", "skill": "fw-spring-boot", "versionless": True,
     "detect": {"spring_boot": True}},
    {"id": "nestjs", "name": "NestJS", "skill": "fw-nestjs", "versionless": True, "detect": {"npm": ["@nestjs/core"]}},
    {"id": "playwright", "name": "Playwright", "skill": "tool-playwright", "versionless": True,
     "detect": {"npm": ["@playwright/test"]}}]}
DESC = "Walidacja DTO kontrolera, obsługa żądań HTTP i mapowanie odpowiedzi w {fw}."
SKILLS = {"fw-spring-boot": "Spring Boot", "fw-nestjs": "NestJS", "tool-playwright": "Playwright"}
POM = ("<project><parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId>"
       "<version>3.3.4</version></parent></project>")


def project(base: Path, stack: bool) -> Path:
    app = base / ("spring" if stack else "empty")
    shutil.copytree(HOOKS, app / ".claude" / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
    reg = app / ".claude" / "skills" / "core-stack-sync" / "references"
    reg.mkdir(parents=True)
    (reg / "technologies.json").write_text(json.dumps(REGISTRY), encoding="utf-8")
    for name, fw in SKILLS.items():
        d = app / ".claude" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {DESC.format(fw=fw)}\n---\n# {fw}\n",
                                    encoding="utf-8")
    if stack:
        (app / "pom.xml").write_text(POM, encoding="utf-8")
    return app


def hint(app: Path, prompt: str, **env) -> str:
    r = subprocess.run([sys.executable, str(app / ".claude" / "hooks" / "skill_hint.py")],
                       input=json.dumps({"prompt": prompt, "session_id": "t"}), capture_output=True, text=True,
                       timeout=60, cwd=app, env={**os.environ, "CLAUDE_PROJECT_DIR": str(app), **env})
    return r.stdout + r.stderr


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    q = "Dodaj walidację DTO kontrolera dla żądań HTTP i mapowanie odpowiedzi"
    with tempfile.TemporaryDirectory() as t:
        spring, empty = project(Path(t), True), project(Path(t), False)
        out = hint(spring, q)
        check("fw-spring-boot" in out and "fw-nestjs" not in out,
              f"SH-1: w repo Spring Boot bez podpowiedzi fw-nestjs: {out}")
        out = hint(spring, q + " — przenosimy to do NestJS")
        check("fw-nestjs" in out, f"SH-2: the command names NestJS, so the skill stays: {out}")
        out = hint(empty, q)
        check("fw-nestjs" in out and "fw-spring-boot" in out,
              f"SH-3: without a detected stack (a new project) nothing is filtered out: {out}")
        out = hint(spring, q, CLAUDE_SKILL_HINT_STACK="0")
        check("fw-nestjs" in out, f"SH-4: CLAUDE_SKILL_HINT_STACK=0 disables the filter: {out}")
        out = hint(spring, q)
        check("tool-playwright" in out,
              f"SH-5: tool skills (tool-) are not filtered — a command may add a new tool: {out}")
        r = subprocess.run([sys.executable, str(spring / ".claude" / "hooks" / "skill_hint.py"), "--explain", q],
                           capture_output=True, text=True, timeout=60, cwd=spring,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(spring)})
        check("outside the project's stack" in r.stdout and "fw-nestjs" in r.stdout,
              f"SH-6: --explain pokazuje skille odfiltrowane jako poza stackiem: {r.stdout}")
        # SH-7: empty, invalid or non-object input (logged on Windows as JSONDecodeError in decoder.py:363) → code 0,
        # no hint, no traceback, nothing in .tf/logs/hook-errors.jsonl
        for raw in ("", "  \n", "{this is not json", "\ufeff{\"prompt\": 1", "[1, 2]", "\"text\"", "null"):
            r = subprocess.run([sys.executable, str(spring / ".claude" / "hooks" / "skill_hint.py")], input=raw,
                               capture_output=True, text=True, timeout=60, cwd=spring,
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(spring)})
            log = spring / ".tf" / "logs" / "hook-errors.jsonl"
            check(r.returncode == 0 and not r.stdout.strip() and "Traceback" not in r.stderr and not log.is_file(),
                  f"SH-7: stdin {raw!r} → code 0, no hint, no error: {r.returncode} {r.stdout!r} {r.stderr[-300:]!r}")
        # SH-8: a corrupt data file (the technology registry) counts as missing: the hint still works, no error logged
        reg = spring / ".claude" / "skills" / "core-stack-sync" / "references" / "technologies.json"
        reg.write_text("{corrupt", encoding="utf-8")
        out = hint(spring, q)
        check("fw-spring-boot" in out and "Traceback" not in out
              and not (spring / ".tf" / "logs" / "hook-errors.jsonl").is_file(),
              f"SH-8: a corrupt technologies.json is treated as missing: {out}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} skill_hint stack filter tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
