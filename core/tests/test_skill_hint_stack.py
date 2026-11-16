#!/usr/bin/env python3
"""Testy filtra stacku w hooku skill_hint: w projekcie z wykrytym stackiem hook nie podpowiada skilli frameworków
i języków (`fw-`, `lang-`) z rejestru technologii, których w projekcie nie ma — chyba że polecenie je wymienia.
Pomiar 2026-11-16 (docs/todo.md): w repo Spring Boot hook podsuwał fw-nestjs i agent go wczytywał.
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
# Własny rejestr technologii (format core-stack-sync/references/technologies.json): test nie zależy od nakładek.
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
        check("fw-nestjs" in out, f"SH-2: polecenie wymienia NestJS, więc skill zostaje: {out}")
        out = hint(empty, q)
        check("fw-nestjs" in out and "fw-spring-boot" in out,
              f"SH-3: bez wykrytego stacku (nowy projekt) nic nie jest odfiltrowane: {out}")
        out = hint(spring, q, CLAUDE_SKILL_HINT_STACK="0")
        check("fw-nestjs" in out, f"SH-4: CLAUDE_SKILL_HINT_STACK=0 wyłącza filtr: {out}")
        out = hint(spring, q)
        check("tool-playwright" in out,
              f"SH-5: skille narzędzi (tool-) nie są filtrowane — polecenie może dodawać nowe narzędzie: {out}")
        r = subprocess.run([sys.executable, str(spring / ".claude" / "hooks" / "skill_hint.py"), "--explain", q],
                           capture_output=True, text=True, timeout=60, cwd=spring,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(spring)})
        check("poza stackiem" in r.stdout and "fw-nestjs" in r.stdout,
              f"SH-6: --explain pokazuje skille odfiltrowane jako poza stackiem: {r.stdout}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów filtra stacku skill_hint")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
