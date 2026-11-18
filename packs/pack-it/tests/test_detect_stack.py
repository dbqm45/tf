#!/usr/bin/env python3
"""Tests of stack detection and the comparison with skill versions: python3 tests/test_detect_stack.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude" / "hooks" / "detect_stack.py"


def run(files: dict[str, str], *flags: str, stdin: str = "") -> str:
    with tempfile.TemporaryDirectory() as d:
        for name, content in files.items():
            (Path(d) / name).parent.mkdir(parents=True, exist_ok=True)
            (Path(d) / name).write_text(content)
        args = [sys.executable, str(SCRIPT), *flags] + ([] if "--hook" in flags else [d])
        env = {"CLAUDE_PROJECT_DIR": d, "PATH": "/usr/bin:/bin"}
        return subprocess.run(args, input=stdin, capture_output=True, text=True, timeout=30, env=env).stdout


def statuses(files: dict[str, str]) -> dict[str, str]:
    report = json.loads(run(files, "--json"))
    return {t["skill"]: t["status"] for t in report["technologies"]} | {
        f"constraint:{c['skill']}": ("ok" if c["ok"] else "violation") for c in report["constraints"]}


def pkg(deps: dict, dev: dict | None = None) -> str:
    return json.dumps({"dependencies": deps, "devDependencies": dev or {}})


WEB = '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>{tfm}</PropertyGroup></Project>'
LIB = '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>{tfm}</PropertyGroup></Project>'

CASES = [
    ("Angular 22 + TS 6.0 + Nx 23 → compatible",
     {"package.json": pkg({"@angular/core": "^22.2.0"}, {"typescript": "~6.0.2", "nx": "23.2.1"})},
     {"fw-angular": "OK", "lang-typescript": "OK", "tool-nx": "OK", "constraint:lang-typescript": "ok"}),
    ("Angular 22 + TS 7 → constraint violation",
     {"package.json": pkg({"@angular/core": "22.2.0"}, {"typescript": "7.0.2"})},
     {"fw-angular": "OK", "constraint:lang-typescript": "violation"}),
    ("Angular 16 → project older than the skill",
     {"package.json": pkg({"@angular/core": "^16.2.0"}, {"typescript": "~5.1.6"})},
     {"fw-angular": "PROJECT_OLDER", "lang-typescript": "OK"}),
    ("Angular 23 (future) → skill to update",
     {"package.json": pkg({"@angular/core": "^23.0.0"}, {"typescript": "~6.1.0"})},
     {"fw-angular": "SKILL_OUTDATED"}),
    ("Vue → no skill",
     {"package.json": pkg({"vue": "^3.5.0"})},
     {"fw-vue": "MISSING_SKILL"}),
    ("Next.js 16.3 + React 19.3 → compatible",
     {"package.json": pkg({"next": "16.3.8", "react": "19.3.0"})},
     {"fw-nextjs": "OK", "fw-react": "OK", "constraint:fw-react": "ok"}),
    ("Next.js 16 + React 19.1 → constraint violation",
     {"package.json": pkg({"next": "^16.0.0", "react": "19.1.4"})},
     {"fw-nextjs": "OK", "constraint:fw-react": "violation"}),
    ("React 17 → project older than the skill",
     {"package.json": pkg({"react": "^17.0.2"})},
     {"fw-react": "PROJECT_OLDER"}),
    ("Python with requires-python + pytest in uv.lock → compatible",
     {"pyproject.toml": '[project]\nname = "x"\nrequires-python = ">=3.12"\n',
      "uv.lock": 'version = 1\n\n[[package]]\nname = "pytest"\nversion = "9.1.1"\n'},
     {"lang-python": "OK", "tool-pytest": "OK", "constraint:lang-python": "ok"}),
    ("Python 3.9 + pytest 7 from requirements.txt → both older than the skills",
     {".python-version": "3.9.18\n", "requirements.txt": "requests==2.32.3\npytest==7.4.4\n"},
     {"lang-python": "PROJECT_OLDER", "tool-pytest": "PROJECT_OLDER"}),
    ("Python 3.16 (future) → skill to update",
     {".python-version": "3.16\n"},
     {"lang-python": "SKILL_OUTDATED"}),
    ("pytest in the pyproject dependency group → detected",
     {"pyproject.toml": '[project]\nname = "x"\nrequires-python = "~=3.13"\n\n[dependency-groups]\ndev = ["pytest>=9.0", "ruff"]\n'},
     {"lang-python": "OK", "tool-pytest": "OK"}),
    ("Maven Java 25 + Spring Boot → the Java skill to update, the Spring skill compatible",
     {"pom.xml": "<project><parent><artifactId>spring-boot-starter-parent</artifactId><version>3.5.4</version></parent>"
                 "<properties><java.version>25</java.version></properties></project>"},
     {"lang-java": "SKILL_OUTDATED", "fw-spring-boot": "OK"}),
    ("NestJS 12 → compatible",
     {"package.json": pkg({"@nestjs/core": "^12.2.0", "@nestjs/common": "^12.2.0"})},
     {"fw-nestjs": "OK"}),
    ("NestJS 10 → project older than the skill",
     {"package.json": pkg({"@nestjs/core": "^10.4.19"})},
     {"fw-nestjs": "PROJECT_OLDER"}),
    ("Go 1.27 with a toolchain directive → compatible (version from the go directive)",
     {"go.mod": "module example.com/x\n\ngo 1.27.0\n\ntoolchain go1.28.1\n"},
     {"lang-go": "OK"}),
    ("Go 1.21 → project older than the skill",
     {"go.mod": "module example.com/x\n\ngo 1.21\n"},
     {"lang-go": "PROJECT_OLDER"}),
    ("Go 1.28 (future) → skill to update",
     {"go.mod": "module example.com/x\n\ngo 1.28\n"},
     {"lang-go": "SKILL_OUTDATED"}),
    ("ASP.NET Core on .NET 10 in src/ → C# and ASP.NET Core compatible",
     {"Shop.sln": "", "src/Api/Api.csproj": WEB.format(tfm="<TargetFramework>net10.0</TargetFramework>")},
     {"lang-csharp": "OK", "fw-aspnet-core": "OK"}),
    ("a .NET 8 library → C# compatible, without ASP.NET Core",
     {"src/Core/Core.csproj": LIB.format(tfm="<TargetFramework>net8.0</TargetFramework>")},
     {"lang-csharp": "OK", "fw-aspnet-core": None}),
    ("ASP.NET Core on .NET 6 → project older than the skills",
     {"Api.csproj": WEB.format(tfm="<TargetFramework>net6.0</TargetFramework>")},
     {"lang-csharp": "PROJECT_OLDER", "fw-aspnet-core": "PROJECT_OLDER"}),
    ("multiple platforms with .NET 11 → the highest decides, skill to update",
     {"src/Lib/Lib.csproj": LIB.format(tfm="<TargetFrameworks>net10.0;net11.0</TargetFrameworks>")},
     {"lang-csharp": "SKILL_OUTDATED"}),
    ("Gradle Java 21 → compatible",
     {"build.gradle.kts": "java { toolchain { languageVersion.set(JavaLanguageVersion.of(21)) } }"},
     {"lang-java": "OK"}),
]


def main() -> int:
    fails = 0
    for title, files, expected in CASES:
        got = statuses(files)
        wrong = {k: (v, got.get(k)) for k, v in expected.items() if got.get(k) != v}
        if wrong:
            fails += 1
            print(f"✗ {title}: {wrong}")
    silent = run({"package.json": pkg({"@angular/core": "22.0.0"}, {"typescript": "6.0.1"})}, "--hook", stdin="{}")
    if silent.strip():
        fails += 1
        print(f"✗ the hook should stay silent for a compatible project, but printed: {silent!r}")
    loud = run({"package.json": pkg({"@angular/core": "22.0.0"}, {"typescript": "7.0.0"})}, "--hook", stdin="{}")
    if "Mismatch" not in loud:
        fails += 1
        print(f"✗ the hook should report a TS mismatch, but printed: {loud!r}")
    total = len(CASES) + 2
    print(f"{'✓' if not fails else '✗'} {total - fails}/{total} tests of stack detection")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
