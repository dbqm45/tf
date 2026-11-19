#!/usr/bin/env python3
"""Tests of the dna add-on (0.1.0: skeleton, contract, stack detection). python3 addons/dna/tests/test_dna.py

Repositories are built in temporary directories by the tests themselves, one per ecosystem.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
REPO = ADDON.parents[1]
sys.path.insert(0, str(ADDON))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import detect, emit, verify  # noqa: E402

REGISTRY = ADDON / "registry"


def repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="dna-test-"))
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return root


def stack(root: Path) -> dict[tuple[str, str], dict]:
    items = detect.detect(root, REGISTRY)["items"]
    return {(i["data"]["tech"], i["data"]["package_dir"]): i for i in items if i["data"].get("topic") == "stack"}


def by_id(root: Path) -> dict[str, dict]:
    return {i["id"]: i for i in detect.detect(root, REGISTRY)["items"]}


def evidence_ok(root: Path, item: dict):
    for ev in item["evidence"]:
        path, line = ev.rsplit(":", 1)
        lines = (root / path).read_text(encoding="utf-8").splitlines()
        assert 1 <= int(line) <= len(lines), ev


# ---------------------------------------------------------------- detection

def test_npm_workspaces_take_version_from_lockfile_per_package():
    root = repo({
        "package.json": '{"name": "mono", "workspaces": ["apps/*"], "scripts": {"test": "vitest", "lint": "eslint ."},'
                        ' "devDependencies": {"typescript": "^5.4.0", "vitest": "^1.6.0"}}',
        "apps/web/package.json": '{"name": "web", "dependencies": {"react": "^18.2.0", "@mui/material": "^5.15.0"}}',
        "apps/legacy/package.json": '{"name": "legacy", "dependencies": {"react": "^17.0.0"}}',
        "package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {
            "": {"name": "mono"},
            "node_modules/typescript": {"version": "5.4.5"},
            "node_modules/vitest": {"version": "1.6.0"},
            "node_modules/react": {"version": "18.3.1"},
            "node_modules/@mui/material": {"version": "5.15.20"},
            "apps/legacy/node_modules/react": {"version": "17.0.2"}}}, indent=2),
    })
    s = stack(root)
    assert s[("react", "apps/web")]["data"]["version"] == "18.3.1"
    assert s[("react", "apps/legacy")]["data"]["version"] == "17.0.2"
    assert s[("react", "apps/web")]["data"]["declared"] == "^18.2.0"
    assert s[("mui", "apps/web")]["data"]["version"] == "5.15.20"
    assert s[("typescript", ".")]["data"]["version"] == "5.4.5"
    assert s[("react", "apps/legacy")]["scope"]["paths"] == ["apps/legacy/**"]
    assert s[("react", "apps/web")]["evidence"][0].startswith("package-lock.json:")
    for item in s.values():
        evidence_ok(root, item)
    ids = by_id(root)
    assert ids["F-CMD-test"]["data"]["command"] == "npm test"
    assert ids["F-CMD-lint"]["data"]["command"] == "npm run lint"
    assert ids["F-REPO-packages"]["data"]["packages"] == ["apps/legacy", "apps/web"]
    notes = detect.detect(root, REGISTRY)["coverage"]["notes"]
    assert any("react" in n and "17.0.2" in n and "18.3.1" in n for n in notes)


def test_pnpm_importers_and_peer_suffix():
    root = repo({
        "package.json": '{"name": "root", "scripts": {"build": "turbo build"}}',
        "packages/ui/package.json": '{"name": "ui", "dependencies": {"react": "^18.2.0", "tailwindcss": "^3.4.0"}}',
        "pnpm-lock.yaml": """
            lockfileVersion: '9.0'
            importers:
              .: {}
              packages/ui:
                dependencies:
                  react:
                    specifier: ^18.2.0
                    version: 18.3.1
                  tailwindcss:
                    specifier: ^3.4.0
                    version: 3.4.4(ts-node@10.9.2)
            packages:
              react@18.3.1:
                resolution: {integrity: sha512-x}
              tailwindcss@3.4.4:
                resolution: {integrity: sha512-y}
        """,
    })
    s = stack(root)
    assert s[("react", "packages/ui")]["data"]["version"] == "18.3.1"
    assert s[("tailwindcss", "packages/ui")]["data"]["version"] == "3.4.4"
    assert by_id(root)["F-CMD-build"]["data"]["command"] == "pnpm run build"
    evidence_ok(root, s[("react", "packages/ui")])


def test_yarn_v1_and_range_without_lockfile_is_reported():
    root = repo({
        "package.json": '{"dependencies": {"vue": "^3.4.0"}}',
        "yarn.lock": """
            # yarn lockfile v1


            vue@^3.4.0:
              version "3.4.27"
              resolved "https://registry.yarnpkg.com/vue/-/vue-3.4.27.tgz"
        """,
        "tools/package.json": '{"dependencies": {"express": "^4.19.0"}}',
    })
    s = stack(root)
    assert s[("vue", ".")]["data"]["version"] == "3.4.27"
    # tools/ has no lockfile of its own but the root yarn.lock does not list express: range only
    assert s[("express", "tools")]["data"]["version"] is None
    assert s[("express", "tools")]["acceptance"] == "manifest-range"
    k = dna.build(root, today="2026-11-19")
    assert "Express in tools: declared ^4.19.0" in emit.render_coverage(k)


def test_python_uv_lock_and_requires_python():
    root = repo({
        "pyproject.toml": """
            [project]
            name = "svc"
            requires-python = ">=3.11"
            dependencies = [
              "fastapi>=0.110",
              "SQLAlchemy[asyncio]>=2.0",
              "httpx",
            ]

            [tool.pytest.ini_options]
            testpaths = ["tests"]

            [tool.ruff]
            line-length = 100
        """,
        "uv.lock": """
            version = 1

            [[package]]
            name = "fastapi"
            version = "0.111.0"

            [[package]]
            name = "sqlalchemy"
            version = "2.0.30"
        """,
    })
    s = stack(root)
    assert s[("fastapi", ".")]["data"]["version"] == "0.111.0"
    assert s[("sqlalchemy", ".")]["data"]["version"] == "2.0.30"
    ids = by_id(root)
    assert ids["F-RUNTIME-python-root"]["data"]["declared"] == ">=3.11"
    assert ids["F-CMD-test"]["data"]["command"] == "pytest"
    assert ids["F-CMD-lint"]["data"]["command"] == "ruff check ."
    for item in s.values():
        evidence_ok(root, item)


def test_requirements_pin():
    root = repo({"requirements.txt": "Django==5.0.6\nrequests>=2\n"})
    assert stack(root)[("django", ".")]["data"]["version"] == "5.0.6"


def test_go_mod_skips_indirect():
    root = repo({"go.mod": """
        module example.com/svc

        go 1.22

        require (
            github.com/gin-gonic/gin v1.10.0
            github.com/labstack/echo/v4 v4.12.0 // indirect
        )
    """})
    s = stack(root)
    assert s[("gin", ".")]["data"]["version"] == "1.10.0"
    assert ("echo", ".") not in s
    assert by_id(root)["F-RUNTIME-go-root"]["data"]["version"] == "1.22"


def test_cargo_lock():
    root = repo({
        "Cargo.toml": '[package]\nname = "svc"\n\n[dependencies]\ntokio = { version = "1", features = ["full"] }\n'
                      'axum = "0.7"\n',
        "Cargo.lock": '[[package]]\nname = "axum"\nversion = "0.7.5"\n\n[[package]]\nname = "tokio"\nversion = "1.38.0"\n',
    })
    s = stack(root)
    assert s[("tokio", ".")]["data"]["version"] == "1.38.0"
    assert s[("axum", ".")]["data"]["version"] == "0.7.5"


def test_maven_parent_and_property():
    root = repo({"pom.xml": """
        <project>
          <parent>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-parent</artifactId>
            <version>3.3.1</version>
          </parent>
          <properties>
            <java.version>21</java.version>
            <junit.version>5.10.2</junit.version>
          </properties>
          <dependencies>
            <dependency>
              <groupId>org.junit.jupiter</groupId>
              <artifactId>junit-jupiter</artifactId>
              <version>${junit.version}</version>
            </dependency>
          </dependencies>
        </project>
    """})
    s = stack(root)
    assert s[("spring-boot", ".")]["data"]["version"] == "3.3.1"
    assert s[("junit", ".")]["data"]["version"] == "5.10.2"
    assert by_id(root)["F-RUNTIME-java-root"]["data"]["version"] == "21"
    evidence_ok(root, s[("spring-boot", ".")])


def test_gradle_catalog_and_plugin():
    root = repo({
        "gradle/libs.versions.toml": '[versions]\njunit = "5.10.1"\n\n[libraries]\n'
                                     'junit-jupiter = { module = "org.junit.jupiter:junit-jupiter", version.ref = "junit" }\n',
        "build.gradle.kts": 'plugins {\n    id("org.springframework.boot") version "3.2.5"\n}\n',
    })
    s = stack(root)
    assert s[("junit", ".")]["data"]["version"] == "5.10.1"
    assert s[("spring-boot", ".")]["data"]["version"] == "3.2.5"


def test_dotnet_project():
    root = repo({"src/Api/Api.csproj": """
        <Project Sdk="Microsoft.NET.Sdk.Web">
          <PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.6" />
          </ItemGroup>
        </Project>
    """})
    s = stack(root)
    assert s[("efcore", "src/Api")]["data"]["version"] == "8.0.6"
    assert by_id(root)["F-RUNTIME-dotnet-src-api"]["data"]["version"] == "net8.0"


def test_tooling_and_makefile_fallback():
    root = repo({".prettierrc": "{}", "eslint.config.js": "export default []\n",
                 "Makefile": "build:\n\tgo build ./...\n\nlint:\n\tgolangci-lint run\n"})
    ids = by_id(root)
    assert ids["F-TOOL-prettier"]["data"]["role"] == "format"
    assert ids["F-TOOL-eslint"]["data"]["role"] == "lint"
    assert ids["F-CMD-lint"]["data"]["command"] == "make lint"


def test_not_listed_package_is_not_stack_and_node_modules_skipped():
    root = repo({
        "package.json": '{"dependencies": {"left-pad": "^1.3.0"}}',
        "node_modules/react/package.json": '{"name": "react", "dependencies": {"react": "18.0.0"}}',
    })
    assert stack(root) == {}


# ---------------------------------------------------------------- contract, emit, verify

def _learned(files=None) -> tuple[Path, Path]:
    root = repo(files or {"package.json": '{"dependencies": {"react": "^18.2.0"}}',
                          "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}'})
    out = root / ".tf" / "addons" / "dna" / "out"
    assert dna.cmd_learn(root, out) == 0
    return root, out


def test_learn_writes_valid_output():
    root, out = _learned()
    assert verify.check_out(out, root) == []
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    assert k["contract"] == 1 and k["generator"].startswith("dna ")
    index = (out / "INDEX.md").read_text(encoding="utf-8")
    assert "React 18.3.1" in index
    assert len(index.splitlines()) <= verify.INDEX_MAX_LINES
    assert "package.json" in (out / "coverage.md").read_text(encoding="utf-8")


def test_verify_rejects_bad_evidence_and_edited_markdown():
    root, out = _learned()
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    k["items"][0]["evidence"] = ["package.json:999"]
    k["items"].append(dict(k["items"][0], id="F-X-missing", evidence=["nope.txt:1"]))
    k["items"].append(dict(k["items"][0], id="F-X-url", evidence=["https://example.com/doc"]))
    k["items"].append(dict(k["items"][0], id="D-X-1", kind="decision"))
    problems = verify.check_knowledge(k, root)
    assert any("out of range" in p for p in problems)
    assert any("does not exist" in p for p in problems)
    assert any("fetched" in p for p in problems)
    assert any("strength" in p for p in problems)
    (out / "INDEX.md").write_text("edited by hand\n", encoding="utf-8")
    assert any("differs from knowledge.json" in p for p in verify.check_out(out, root))


def test_verify_rejects_evidence_outside_repo():
    root, out = _learned()
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    k["items"][0]["evidence"] = ["../../etc/passwd:1"]
    assert any("outside the repository" in p for p in verify.check_knowledge(k, root))


def test_failed_check_keeps_previous_output(monkeypatch=None):
    root, out = _learned()
    before = (out / "knowledge.json").read_text(encoding="utf-8")
    original = verify.check_out
    verify.check_out = lambda o, r: ["forced failure"]
    try:
        assert dna.cmd_learn(root, out) == 1
    finally:
        verify.check_out = original
    assert (out / "knowledge.json").read_text(encoding="utf-8") == before
    assert not [p for p in out.parent.iterdir() if p.name.startswith(".dna-new-")]


def test_index_stays_within_limit_for_large_stack():
    deps = {name: "^1.0.0" for t in detect.load_detectors(REGISTRY) for name in t["match"].get("npm", [])}
    root, out = _learned({"package.json": json.dumps({"dependencies": deps})})
    assert len((out / "INDEX.md").read_text(encoding="utf-8").splitlines()) <= verify.INDEX_MAX_LINES


def test_cli_learn_verify_status():
    root = repo({"go.mod": "module x\n\ngo 1.22\n"})
    out = root / "out-dir"
    run = lambda *a: subprocess.run([sys.executable, str(ADDON / "dna.py"), *a, "--root", str(root), "--out",
                                     str(out)], capture_output=True, text=True)
    assert run("learn").returncode == 0
    assert run("verify").returncode == 0
    st = run("status")
    assert st.returncode == 0 and "items" in st.stdout
    assert run("bogus").returncode == 2


# ---------------------------------------------------------------- independence from the factory

def test_addon_imports_nothing_from_the_factory():
    forbidden = {"core", "packs", "modes", "tools", "org", "scripts"}
    for f in ADDON.rglob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for n in names:
                assert n.split(".")[0] not in forbidden, f"{f}: imports {n}"
        assert "parents[2]" not in f.read_text(encoding="utf-8") or f.name == "test_dna.py", f


def test_core_does_not_name_the_addon():
    for f in (REPO / "core").rglob("*"):
        if f.is_file() and f.suffix in (".py", ".md", ".yaml", ".json"):
            assert "addons/dna" not in f.read_text(encoding="utf-8", errors="replace"), f


def test_addon_yaml_contract():
    import yaml
    meta = yaml.safe_load((ADDON / "addon.yaml").read_text(encoding="utf-8"))
    assert meta["name"] == "dna" and meta["contract"] == 1
    assert (ADDON / meta["provides"]["context"].replace("out/", "out/")).name == "INDEX.md"
    schema = json.loads((ADDON / "schema" / "knowledge.schema.json").read_text(encoding="utf-8"))
    assert set(schema["properties"]["items"]["items"]["properties"]["kind"]["enum"]) == verify.KINDS
    assert set(schema["properties"]["items"]["items"]["properties"]["status"]["enum"]) == verify.STATUSES


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
