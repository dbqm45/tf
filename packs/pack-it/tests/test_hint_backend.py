#!/usr/bin/env python3
"""A regression test of skill hints (the skill_hint hook) on typical backend commands in a Spring Boot repo — without a model.
A set from the 2026-11-16 measurement (docs/todo.md, "Team and personal preference layers"): the expected skill in the hint
and no skills of other stacks (the stack filter). A skill description change that breaks these hints shows up here, not in
a paid evaluation. python3 .claude/tests/test_hint_backend.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks" / "skill_hint.py").is_file())
HINT = ROOT / ".claude" / "hooks" / "skill_hint.py"
POM = ("<project><parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId>"
       "<version>3.3.4</version></parent></project>")
# command → skills, at least one of which must be in the hint (the commands are Polish test data)
EXPECT = {
    "Dodaj endpoint GET /orders z paginacją": {"be-api-design"},
    "Napisz migrację bazy dodającą kolumnę status do tabeli orders": {"be-database"},
    "Dodaj autoryzację JWT do API zamówień": {"be-auth-security"},
    "Zoptymalizuj zapytanie N+1 przy pobieraniu zamówień z pozycjami": {"be-database"},
    "Zrefaktoryzuj OrderService, jest za duży": {"eng-refactor-planning"},
    "Dodaj healthcheck i metryki do aplikacji": {"ops-observability"},
    "Zaktualizuj Spring Boot do nowszej wersji": {"fw-spring-boot", "ops-dependency-upgrades"},
    "Napisz Dockerfile dla aplikacji": {"ops-docker"},
    "Dodaj walidację DTO w kontrolerze zamówień": {"fw-spring-boot"},
    "Obsłuż błędy w API zgodnie z RFC 7807": {"be-api-design"},
}
UNWANTED = {"Obsłuż błędy w API zgodnie z RFC 7807": {"ai-mcp-server"}}
REST = ["Popraw transakcję przy zapisie zamówienia, czasem gubi pozycje", "Zrób outbox dla zdarzenia OrderPlaced do Kafki",
        "Napisz test integracyjny repozytorium JPA zamówień", "Dodaj cache dla listy produktów",
        "Dodaj obsługę idempotencji przy płatności", "Dodaj limit zapytań na API", "Dodaj audyt zmian zamówień",
        "Popraw wyciek połączeń do bazy", "Zaprojektuj agregat Order z pozycjami", "Dodaj eksport zamówień do CSV"]
OTHER_STACK = re.compile(r"\b(fw-(angular|react|nextjs|nestjs|aspnet-core|vue|svelte)|lang-(typescript|javascript|csharp|go|python|kotlin))\b")


def hinted(project: Path, prompt: str) -> set[str]:
    r = subprocess.run([sys.executable, str(HINT)], input=json.dumps({"prompt": prompt, "session_id": "t"}),
                       capture_output=True, text=True, timeout=60, cwd=project,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_SKILL_HINT_JEV": "0"})
    return set(re.findall(r"^- ([a-z]+-[a-z0-9-]+) —", r.stdout, re.M))


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not (ROOT / ".claude" / "skills" / "fw-spring-boot").is_dir():
        print("• skipped: no IT pack (fw-spring-boot)")
        return 0
    with tempfile.TemporaryDirectory() as t:
        app = Path(t) / "app"
        (app / ".claude").mkdir(parents=True)
        os.symlink(ROOT / ".claude" / "skills", app / ".claude" / "skills")
        (app / "pom.xml").write_text(POM, encoding="utf-8")
        for prompt, want in EXPECT.items():
            got = hinted(app, prompt)
            check(got & want, f"HB: {prompt!r} → expected {' or '.join(sorted(want))}, hint: {sorted(got) or 'none'}")
            bad = got & UNWANTED.get(prompt, set())
            check(not bad, f"HB: „{prompt}” → skill spoza tematu w podpowiedzi: {sorted(bad)}")
        other = {p: sorted(s for s in hinted(app, p) if OTHER_STACK.search(s)) for p in [*EXPECT, *REST]}
        check(not any(other.values()), f"HB: hints of skills of other stacks in a Spring Boot repo: "
                                       f"{ {p: s for p, s in other.items() if s} }")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the backend hints")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
