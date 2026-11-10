#!/usr/bin/env python3
"""
Moduł `observability` tf analyze, piętro 0 (bez modelu): podstawy obserwowalności usług HTTP (ops-observability).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Reguły:
- `no-health-endpoint` — w repozytorium jest punkt startowy usługi (Express, Fastify, Koa, NestJS, Hono, FastAPI,
  Flask, Spring Boot), ale nigdzie nie ma trasy `health`/`healthz`/`livez`/`readyz`/`ready`/`ping`, Actuatora ani
  `@nestjs/terminus` — orkiestrator nie odróżni usługi żywej od zawieszonej; zgłaszane przy punkcie startowym;
- `no-correlation-id` — usługa loguje, ale nigdzie nie ma identyfikatora żądania ani śledzenia (`x-request-id`,
  `correlation id`, `traceparent`, OpenTelemetry, `pino-http`, MDC) — logów jednego żądania nie da się połączyć;
- `print-instead-of-logger` — `console.*` albo `print` w pliku usługi (importuje framework HTTP albo jest route
  handlerem Next.js) zamiast loggera z poziomem i polami;
- `swallowed-error` — pusta obsługa błędu bez komentarza: w JS/TS każdy pusty `catch {}` i `.catch(() => {})`,
  w Pythonie, Javie i Kotlinie tylko szeroki wyjątek (gołe `except`, `Exception`, `BaseException`, `Throwable`) —
  błąd znika bez logu i bez ponowienia (pusty blok z komentarzem i wąski, nazwany wyjątek to świadoma decyzja).
Sprawdzenie na poziomie repozytorium (trasa health, identyfikator) obejmuje wszystkie usługi naraz. Testy, skrypty
w `scripts/`, dokumentacja i fixtures są pomijane. Znalezienie = „sprawdź”. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".venv", "venv", "__pycache__", ".tf", ".next",
             "target", "_vendor", "vendor"}
FACTORY_OWNED = (".tf/factory/", ".claude/")
TEST_OR_DOC = re.compile(r"(^|/)(tests?|__tests__|e2e|fixtures|spec|examples?|docs?|scripts?|tools|bin|cli)/|"
                         r"\.(test|spec)\.|(^|/)test_[^/]*$|(^|/)conftest\.py$|\.(md|rst|txt|adoc)$")
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
CODE_EXT = JS_EXT | {".py", ".java", ".kt"}
CONFIG_FILES = re.compile(r"(^|/)(pom\.xml|build\.gradle(\.kts)?|package\.json|requirements[^/]*\.txt|"
                          r"pyproject\.toml|application[^/]*\.(ya?ml|properties))$")

ENTRY = re.compile(r"\bexpress\s*\(\s*\)|\bfastify\s*\(|\bnew\s+Koa\s*\(|\bNestFactory\.create\s*\(|"
                   r"\bnew\s+Hono\s*\(|\bFastAPI\s*\(|\bFlask\s*\(\s*__name__|@SpringBootApplication\b")
SERVICE = re.compile(r"""(?:from|require\s*\()\s*["'](?:express|fastify|koa|@koa/router|@nestjs/\w+|hono)["']|"""
                     r"^\s*(?:from|import)\s+(?:fastapi|flask|django|starlette)\b|"
                     r"@(?:RestController|Controller|SpringBootApplication)\b", re.M)
NEXT_ROUTE = re.compile(r"(^|/)app/(.+/)?route\.[cm]?[jt]sx?$")
HEALTH = re.compile(r"""["'`]/?(?:api/)?(?:v\d+/)?_?(?:health|healthz|healthcheck|livez|readyz|ready|readiness|"""
                    r"""liveness|ping)\b|spring-boot-starter-actuator|management\.endpoints|@nestjs/terminus|"""
                    r"""(^|/)(health|healthz)/route\.""", re.I | re.M)
CORRELATION = re.compile(r"x-request-id|x-correlation-id|correlation[_-]?id|request[_-]?id|\btraceparent\b|"
                         r"opentelemetry|\btrace_?id\b|MDC\.put|pino-http|express-request-id|cls-rtracer|"
                         r"asgi[_-]correlation[_-]id|genReqId|sentry", re.I)
LOGGING = re.compile(r"""\b(?:winston|pino|bunyan|log4js|structlog|loguru|slf4j|LoggerFactory|getLogger)\b|"""
                     r"""^\s*import\s+logging\b|new\s+Logger\s*\(|from\s+["']@nestjs/common["'].*\bLogger\b|"""
                     r"""\blogger\.(?:info|warn|error|debug)\s*\(""", re.M)
PRINT = re.compile(r"^\s*(?:console\.(?:log|info|debug|warn|error|trace)|print)\s*\(", re.M)
EMPTY_CATCH = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*\{\s*\}|\.catch\s*\(\s*(?:\(\s*\w*\s*\)|\w+)\s*=>\s*\{\s*\}\s*\)")
# Java/Kotlin i Python: tylko szeroki wyjątek — pusta obsługa wąskiego, nazwanego wyjątku to zwykle świadomy idiom.
JAVA_EMPTY_CATCH = re.compile(r"\bcatch\s*\(\s*(?:final\s+)?(?:java\.lang\.)?(?:Exception|Throwable|RuntimeException)"
                              r"\s+\w+\s*\)\s*\{\s*\}|\bcatch\s*\(\s*\w+\s*:\s*(?:Exception|Throwable)\s*\)\s*\{\s*\}")
PY_EXCEPT_PASS = re.compile(r"^(\s*)except(?:\s*\(?\s*(?:Exception|BaseException)\s*\)?(?:\s+as\s+\w+)?)?[ \t]*:[ \t]*"
                            r"(#.*)?\n\s*(?:pass|\.\.\.)[ \t]*(#.*)?$", re.M)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def emit(rule: str, rel: str, line: int, snippet: str, title: str, severity: str, evidence: str,
         suggestion: str, confidence: float = 0.6) -> None:
    print(json.dumps({"rule": rule, "title": title, "file": rel, "line": line, "snippet": snippet.strip()[:160],
                      "severity": severity, "confidence": confidence, "evidence": evidence,
                      "basis": "ops-observability (logi strukturalne, korelacja), ops-sre-incidents (sondy, SLO)",
                      "suggestion": suggestion}, ensure_ascii=False))


def list_files(root: Path) -> list[str]:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve():
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        return [f for f in r.stdout.splitlines() if f and not set(Path(f).parts) & SKIP_DIRS
                and not f.startswith(FACTORY_OWNED)]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        out += [str((Path(dp) / f).relative_to(root)) for f in fns]
    return sorted(out)


def read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8") if p.stat().st_size <= 1_000_000 else None
    except (OSError, UnicodeDecodeError):
        return None


def scan(root: Path, files: list[str]) -> None:
    code: dict[str, str] = {}
    config_text = ""
    for rel in files:
        rel = rel.replace(os.sep, "/")
        p = root / rel
        if not p.is_file():
            continue
        if CONFIG_FILES.search(rel):
            config_text += (read(p) or "") + "\n"
        if TEST_OR_DOC.search(rel) or p.suffix.lower() not in CODE_EXT:
            continue
        text = read(p)
        if text is not None:
            code[rel] = text
    corpus = "\n".join(code.values()) + "\n" + config_text + "\n".join(code)
    entries = [(rel, m) for rel, t in code.items() for m in [ENTRY.search(t)] if m]
    if entries:
        has_health = bool(HEALTH.search(corpus))
        has_corr = bool(CORRELATION.search(corpus))
        logs = any(LOGGING.search(t) for t in code.values())
        for rel, m in entries:
            text = code[rel]
            if not has_health:
                emit("no-health-endpoint", rel, line_of(text, m.start()), text.splitlines()[line_of(text, m.start()) - 1],
                     "usługa bez endpointu health", "średnia",
                     "punkt startowy usługi; w repozytorium brak trasy health/livez/readyz, Actuatora i terminus",
                     "dodaj `/livez` (proces żyje) i `/readyz` (zależności gotowe) i podepnij je pod sondy "
                     "orkiestratora")
            if logs and not has_corr:
                emit("no-correlation-id", rel, line_of(text, m.start()), text.splitlines()[line_of(text, m.start()) - 1],
                     "logi bez identyfikatora żądania", "średnia",
                     "usługa loguje, ale w repozytorium brak x-request-id, traceparent, OpenTelemetry i podobnych",
                     "nadaj identyfikator żądania w middleware (przyjmij `traceparent`/`x-request-id` albo "
                     "wygeneruj), dołączaj go do każdego logu i przekazuj dalej")
    for rel, text in code.items():
        ext = Path(rel).suffix.lower()
        if SERVICE.search(text) or (ext in JS_EXT and NEXT_ROUTE.search(rel)):
            for m in PRINT.finditer(text):
                if m.group(0).lstrip().startswith("print") and ext != ".py":
                    continue
                ln = line_of(text, m.start())
                emit("print-instead-of-logger", rel, ln, text.splitlines()[ln - 1],
                     "console/print zamiast loggera w kodzie usługi", "niska",
                     "wyjście bez poziomu, pól i identyfikatora żądania; trudne do filtrowania i alertów",
                     "użyj loggera strukturalnego (pino, winston, logging/structlog, SLF4J) z polami zamiast "
                     "sklejania tekstu")
        pats = [PY_EXCEPT_PASS] if ext == ".py" else [JAVA_EMPTY_CATCH] if ext in (".java", ".kt") else [EMPTY_CATCH]
        for pat in pats:
            for m in pat.finditer(text):
                if ext == ".py" and (m.group(2) or m.group(3)):
                    continue
                ln = line_of(text, m.start(1) if ext == ".py" else m.start())
                emit("swallowed-error", rel, ln, text.splitlines()[ln - 1], "połknięty błąd", "średnia",
                     "pusta obsługa wyjątku bez komentarza — błąd znika bez logu, metryki i ponowienia",
                     "zaloguj błąd z kontekstem i przekaż dalej albo obsłuż; jeśli pominięcie jest zamierzone, "
                     "opisz dlaczego w komentarzu", confidence=0.8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--files", default="")
    a = ap.parse_args()
    root = Path(a.root)
    files = [f for f in a.files.split(",") if f] or list_files(root)
    scan(root, files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
