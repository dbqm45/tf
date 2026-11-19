#!/usr/bin/env python3
"""
Standards signals from code (project reconstruction, team standards): tools from config files and
conventions counted in the code — each with a share, file:line examples and exceptions. This is DATA for a standard, not a
standard: you write the rule after reviewing the examples and exceptions. Standard library only; it does not run the code.

  python3 standards_scan.py <repo>          # text
  python3 standards_scan.py <repo> --json   # full result

Areas: file names, package layout (by function or by layer), tests (framework, location), test idioms (test kind per layer, doubles, case
structure, builders), code idioms (e.g. ctx as the 1st argument, read-only collections, Post/Redirect/Get), errors
(broad catching), logging, debt (TODO/FIXME).
`share` values are in percent (rounded); `total` = files of the given language the signal applies to.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

SKIP = {"node_modules", "vendor", "dist", "build", "target", "out", "bin", "obj", "coverage", "__pycache__",
        ".venv", "venv", ".next"}
LANG = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
        ".java": "Java", ".cs": "C#", ".go": "Go"}
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                  r"\.Tests?/|(Test|Tests|IT)\.java$|Tests?\.cs$")
TOOLS = [  # (tool, file or name pattern, content condition)
    ("editorconfig", re.compile(r"^\.editorconfig$"), None),
    ("eslint", re.compile(r"^(eslint\.config\.\w+|\.eslintrc(\.\w+)?)$"), None),
    ("prettier", re.compile(r"^(\.prettierrc(\.\w+)?|prettier\.config\.\w+)$"), None),
    ("typescript-strict", re.compile(r"^tsconfig(\.\w+)?\.json$"), re.compile(r'"strict"\s*:\s*true')),
    ("ruff", re.compile(r"^(ruff\.toml|\.ruff\.toml|pyproject\.toml)$"), re.compile(r"^\[tool\.ruff", re.M)),
    ("black", re.compile(r"^pyproject\.toml$"), re.compile(r"^\[tool\.black", re.M)),
    ("mypy", re.compile(r"^(mypy\.ini|pyproject\.toml|setup\.cfg)$"), re.compile(r"^\[(tool\.)?mypy", re.M)),
    ("pytest", re.compile(r"^(pytest\.ini|pyproject\.toml|setup\.cfg)$"), re.compile(r"^\[(tool:pytest|tool\.pytest)", re.M)),
    ("flake8", re.compile(r"^(\.flake8|setup\.cfg|tox\.ini)$"), re.compile(r"^\[flake8", re.M)),
    ("checkstyle", re.compile(r"^checkstyle.*\.xml$"), None),
    ("spotless", re.compile(r"^(build\.gradle(\.kts)?|pom\.xml)$"), re.compile(r"spotless")),
    ("golangci-lint", re.compile(r"^\.golangci\.ya?ml$"), None),
    ("stylecop", re.compile(r"^stylecop\.json$"), None),
    ("dotnet-analyzers", re.compile(r"^Directory\.Build\.props$"), re.compile(r"AnalysisLevel|TreatWarningsAsErrors")),
    ("pre-commit", re.compile(r"^\.pre-commit-config\.ya?ml$"), None),
]
NAMING = {"snake_case": re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$"), "kebab-case": re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$"),
          "PascalCase": re.compile(r"^[A-Z][a-zA-Z0-9]*$"), "camelCase": re.compile(r"^[a-z]+[A-Z][a-zA-Z0-9]*$"),
          "lowercase": re.compile(r"^[a-z0-9]+$")}
TEST_FW = {"Python": [("pytest", r"^\s*import pytest|^\s*from pytest"), ("unittest", r"^\s*import unittest|unittest\.TestCase")],
           "TypeScript": [("vitest", r"from ['\"]vitest['\"]"), ("jest", r"from ['\"]@jest/|jest\.fn\(|jest\.mock\("),
                          ("playwright", r"from ['\"]@playwright/test['\"]")],
           "JavaScript": [("vitest", r"from ['\"]vitest['\"]"), ("jest", r"jest\.fn\(|jest\.mock\(")],
           "Java": [("junit5", r"import org\.junit\.jupiter"), ("junit4", r"import org\.junit\.Test;"),
                    ("testng", r"import org\.testng")],
           "C#": [("xunit", r"using Xunit;"), ("nunit", r"using NUnit\.Framework;"), ("mstest", r"using Microsoft\.VisualStudio\.TestTools")],
           "Go": [("testing", r"\"testing\""), ("testify", r"github\.com/stretchr/testify")]}
BROAD = {"Python": [("bare except", r"^\s*except\s*:"), ("except Exception", r"^\s*except\s+(Base)?Exception\b")],
         "Java": [("catch Exception/Throwable", r"catch\s*\(\s*(final\s+)?(Exception|Throwable|RuntimeException)\s+\w+\s*\)")],
         "C#": [("catch Exception", r"catch\s*(\(\s*Exception\b[^)]*\))?\s*\{")],
         "TypeScript": [("empty catch", r"catch\s*(\([^)]*\))?\s*\{\s*\}")], "JavaScript": [("empty catch", r"catch\s*(\([^)]*\))?\s*\{\s*\}")],
         "Go": [("ignored error (_ =)", r"^\s*_\s*(,\s*_\s*)?=\s*\w")]}
LOGS = {"Python": [("logging", r"^\s*import logging|getLogger\("), ("structlog", r"import structlog"), ("print", r"^\s*print\(")],
        "TypeScript": [("console", r"\bconsole\.(log|warn|error|info)\("), ("pino", r"from ['\"]pino['\"]"), ("winston", r"from ['\"]winston['\"]")],
        "JavaScript": [("console", r"\bconsole\.(log|warn|error|info)\(")],
        "Java": [("slf4j", r"import org\.slf4j"), ("System.out", r"System\.(out|err)\.print")],
        "C#": [("ILogger", r"\bILogger(<\w+>)?\b"), ("Console", r"\bConsole\.Write(Line)?\(")],
        "Go": [("log/slog", r"\"log/slog\""), ("log", r"\"log\""), ("zap", r"go\.uber\.org/zap")]}
TEST_IDIOMS = {  # in test files: how the team tests (patterns for the test standard)
    "Java": [("@WebMvcTest (web layer test)", r"@WebMvcTest\b"), ("@DataJpaTest (repository test)", r"@DataJpaTest\b"),
             ("@SpringBootTest (integration test)", r"@SpringBootTest\b"), ("@MockitoBean/@MockBean", r"@Mock(ito)?Bean\b"),
             ("Mockito (mock/when)", r"\bMockito\.|\bwhen\(|@Mock\b"), ("Testcontainers", r"@Testcontainers\b|\bTestcontainers\b|Container<"),
             ("MockMvc", r"\bMockMvc\b"), ("@ParameterizedTest", r"@ParameterizedTest\b"), ("AssertJ (assertThat)", r"\bassertThat\(")],
    "C#": [("[Fact]", r"\[Fact\]"), ("[Theory] with data", r"\[Theory\]"), ("NSubstitute (Substitute.For)", r"\bSubstitute\.For<"),
           ("Moq (new Mock<>)", r"\bnew Mock<"), ("WebApplicationFactory (integration tests)", r"\bWebApplicationFactory<"),
           ("test data builder", r"\bclass \w+Builder\b|\bnew \w+Builder\("), ("FluentAssertions (.Should())", r"\.Should\(\)")],
    "Go": [("t.Run (subtests)", r"\bt\.Run\("), ("table of cases ([]struct)", r"\[\]struct\s*\{"),
           ("external package *_test", r"^package \w+_test\b"), ("sqlmock", r"go-sqlmock|sqlmock\."),
           ("mockery (mocks.)", r"\bmocks\.\w+|mock\.Anything"), ("testify assert/require", r"\b(assert|require)\.\w+\("),
           ("httptest", r"\bhttptest\.")],
    "Python": [("@pytest.mark.parametrize", r"@pytest\.mark\.parametrize"), ("pytest fixture", r"@pytest\.fixture"),
               ("unittest.mock", r"unittest\.mock|\bMagicMock\b|\bpatch\("), ("factory_boy", r"\bfactory\.\w+Factory\b")],
    "TypeScript": [("describe/it", r"\bdescribe\(|\bit\("), ("test.each/it.each", r"\b(test|it)\.each\b"),
                   ("vi.mock/jest.mock", r"\b(vi|jest)\.mock\("), ("Testing Library", r"@testing-library/"), ("msw", r"from ['\"]msw")],
    "JavaScript": [("describe/it", r"\bdescribe\(|\bit\("), ("vi.mock/jest.mock", r"\b(vi|jest)\.mock\(")]}
CODE_IDIOMS = {  # in production code: idioms worth recording in the standard
    "Go": [("context.Context as first argument", r"^func (\([^)]*\) )?\w+\(\s*\w+ context\.Context\b"),
           ("sentinel errors (errors.New in var)", r"^\s*Err\w+\s*=\s*errors\.New\("), ("error wrapping (%w)", r"%w")],
    "Java": [("constructor injection (final fields)", r"^\s*private final \w+"), ("@Autowired on field", r"@Autowired\s*\n?\s*private"),
             ("@InitBinder", r"@InitBinder\b"), ("@ModelAttribute", r"@ModelAttribute\b"),
             ("redirect: (Post/Redirect/Get)", r"\"redirect:"), ("@Transactional", r"@Transactional\b"), ("record", r"\brecord \w+\(")],
    "C#": [("AsReadOnly (read-only collections)", r"\.AsReadOnly\(\)"), ("private setter", r"\{\s*get;\s*private set;"),
           ("Guard.Against", r"\bGuard\.Against\."), ("DI registration in extension methods", r"this IServiceCollection\b"),
           ("DI: AddScoped", r"\.AddScoped\b"), ("DI: AddSingleton", r"\.AddSingleton\b"), ("DI: AddTransient", r"\.AddTransient\b"),
           ("domain exception (: Exception)", r"class \w+Exception\s*:\s*\w*Exception\b")],
    "Python": [("dataclass", r"@dataclass\b"), ("pydantic BaseModel", r"\(BaseModel\)"), ("type annotations in def", r"def \w+\([^)]*:\s*\w")],
    "TypeScript": [("zod (validation at the boundary)", r"from ['\"]zod['\"]"), ("readonly", r"\breadonly\b")]}
ROLES = ("Controller", "Service", "Repository", "Validator", "Handler", "Endpoint", "Entity", "Dto", "Mapper",
         "Factory", "Formatter", "Configuration", "Config", "Exception", "Specification", "Middleware")
LAYERS = {"controller", "controllers", "service", "services", "repository", "repositories", "repo", "model", "models",
          "entity", "entities", "dto", "dtos", "handler", "handlers", "dao", "mapper", "mappers", "view", "views",
          "domain", "infrastructure", "application", "persistence", "adapters", "usecase", "usecases", "interfaces",
          "contracts", "abstractions"}


def role(stem: str) -> str | None:
    return next((r for r in ROLES if stem.endswith(r) and stem != r), None)


TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")


def walk(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP and not d.startswith("."))
        for f in sorted(fn):
            yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")


def read(root: str, p: str) -> str:
    try:
        with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def lines_matching(text: str, rx: str) -> list[int]:
    r = re.compile(rx, re.M)
    return [text.count("\n", 0, m.start()) + 1 for m in r.finditer(text)]


def signal(area, lang, rule, files_hit, total, examples, exceptions=()):
    return {"area": area, "language": lang, "rule": rule, "count": len(files_hit), "total": total,
            "share": round(100 * len(files_hit) / total) if total else 0, "examples": list(examples)[:5],
            "exceptions": list(exceptions)[:5]}


def scan(root: str) -> dict:
    paths = list(walk(root))
    tools = []
    for p in paths:
        name = os.path.basename(p)
        for tool, rx, cond in TOOLS:
            if rx.search(name) and (cond is None or cond.search(read(root, p))):
                tools.append({"tool": tool, "file": p})
    code = [(p, LANG[os.path.splitext(p)[1]]) for p in paths if os.path.splitext(p)[1] in LANG]
    by_lang = collections.defaultdict(list)
    for p, lang in code:
        by_lang[lang].append(p)
    sigs = []
    for lang, files in sorted(by_lang.items()):
        prod = [p for p in files if not TEST.search(p)]
        tests = [p for p in files if TEST.search(p)]
        texts = {p: read(root, p) for p in files}
        # (production) file names: the dominant style + exceptions
        stems = {p: os.path.basename(p).split(".")[0] for p in prod}
        styles = {p: next((k for k, rx in NAMING.items() if rx.match(s)), "other") for p, s in stems.items()}
        cnt = collections.Counter(v for v in styles.values() if v != "lowercase")
        if cnt:
            top = cnt.most_common(1)[0][0]
            ok = [p for p, v in styles.items() if v in (top, "lowercase")]
            sigs.append(signal("file names", lang, top, ok, len(prod), ok,
                               [f"{p} ({styles[p]})" for p in prod if p not in ok]))
        # package layout: a directory with files of different roles (by function) or a directory named like a layer
        dirs = collections.defaultdict(list)
        for p in prod:
            dirs[os.path.dirname(p)].append(os.path.basename(p).split(".")[0])
        feature = [d for d, st in dirs.items() if os.path.basename(d).lower() not in LAYERS
                   and len({role(x) for x in st} - {None}) >= 2]
        layered = [d for d in dirs if os.path.basename(d).lower() in LAYERS]
        if feature:
            sigs.append(signal("layout", lang, "packages by feature (different roles in one directory)", feature,
                               len(dirs), [f"{d}/ ({', '.join(sorted({role(x) for x in dirs[d]} - {None}))})" for d in feature],
                               layered))
        if layered:
            sigs.append(signal("layout", lang, "packages by layer (directory = layer)", layered, len(dirs),
                               [f"{d}/" for d in layered], feature))
        # tests: framework and location
        for fw, rx in TEST_FW.get(lang, []):
            hit = {p: lines_matching(texts[p], rx) for p in tests}
            hit = {p: l for p, l in hit.items() if l}
            if hit:
                sigs.append(signal("tests", lang, fw, list(hit), len(tests), [f"{p}:{l[0]}" for p, l in hit.items()]))
        if tests:
            sep = [p for p in tests if re.search(r"(^|/)(tests?|__tests__|spec)/|\.Tests?/", p)]
            if sep:
                sigs.append(signal("tests", lang, "separate tests/ directory", sep, len(tests), sep,
                                   [p for p in tests if p not in sep]))
            col = [p for p in tests if p not in sep]
            if col:
                sigs.append(signal("tests", lang, "test next to code", col, len(tests), col, sep))
        # idioms: of tests (in tests) and of code (in production code)
        for area, table, pool in (("test idioms", TEST_IDIOMS, tests), ("code idioms", CODE_IDIOMS, prod)):
            for rule, rx in table.get(lang, []):
                hit = {p: lines_matching(texts[p], rx) for p in pool}
                hit = {p: l for p, l in hit.items() if l}
                if hit:
                    sigs.append(signal(area, lang, rule, list(hit), len(pool), [f"{p}:{l[0]}" for p, l in hit.items()]))
        # errors, logging, debt — in production code
        for area, table in (("errors", BROAD), ("logging", LOGS)):
            for rule, rx in table.get(lang, []):
                hit = {p: lines_matching(texts[p], rx) for p in prod}
                hit = {p: l for p, l in hit.items() if l}
                if hit:
                    sigs.append(signal(area, lang, rule, list(hit), len(prod),
                                       [f"{p}:{n}" for p, l in hit.items() for n in l]))
        hit = {p: lines_matching(texts[p], TODO.pattern) for p in prod}
        hit = {p: l for p, l in hit.items() if l}
        if hit:
            sigs.append(signal("debt", lang, "TODO/FIXME", list(hit), len(prod),
                               [f"{p}:{n}" for p, l in hit.items() for n in l]))
    return {"root": os.path.abspath(root), "tools": tools, "signals": sigs,
            "files": {lang: len(f) for lang, f in sorted(by_lang.items())}}


def render(r: dict) -> str:
    L = ["Tools from config: " + (", ".join(f"{t['tool']} ({t['file']})" for t in r["tools"]) or "none"),
         "Signals (area · language · rule: files/total = share; examples; exceptions):"]
    for s in r["signals"]:
        L.append(f"  - {s['area']} · {s['language']} · {s['rule']}: {s['count']}/{s['total']} = {s['share']}%; "
                 f"e.g. {', '.join(s['examples'][:3])}" + (f"; exceptions: {', '.join(s['exceptions'][:3])}" if s["exceptions"] else ""))
    L.append("This is data, not a standard: write the rule after you look at the examples and exceptions.")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if args[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(args) != 1 or not os.path.isdir(args[0]):
        print(f"✗ give a repository directory (got: {args})", file=sys.stderr)
        return 2
    r = scan(args[0])
    print(json.dumps(r, ensure_ascii=False, indent=2) if as_json else render(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
