#!/usr/bin/env python3
"""Tests of dna documentation (lib/docs.py, `dna.py docs`). python3 addons/dna/tests/test_docs.py

The registries are a local HTTP server (allow_private in the options); nothing goes to the internet.
"""
from __future__ import annotations

import gzip
import http.server
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import threading
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

import dna  # noqa: E402
from lib import docs, verify  # noqa: E402
from test_dna import repo  # noqa: E402

README = """# React

## useTransition
`useTransition` lets you update the state without blocking the UI.

## useState
Returns a stateful value.
"""


def serve(routes: dict[str, bytes]) -> tuple[str, http.server.ThreadingHTTPServer]:
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = routes.get(self.path)
            self.send_response(200 if body is not None else 404)
            self.end_headers()
            self.wfile.write(body or b"")

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}", srv


def tarball(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def react_project(installed: str | None = "18.3.1") -> Path:
    files = {"package.json": '{"dependencies": {"react": "^18.2.0"}}',
             "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"}}}'}
    if installed:
        files.update({"node_modules/react/package.json": json.dumps({"name": "react", "version": installed}),
                      "node_modules/react/README.md": README,
                      "node_modules/react/index.d.ts": "export function useTransition(): [boolean, Function];\n"})
    return repo(files)


def learn(root: Path, online=False, opts=None) -> tuple[dict, Path, Path]:
    out, cache = root / "out", root / "cache"
    k = dna.build(root, today="2026-11-20", online=online, cache=cache, docs_opts=opts)
    from lib import emit
    emit.write(k, out)
    return k, out, cache


# ----------------------------------------------------------------

def test_installed_package_is_indexed_offline():
    root = react_project()
    k, out, cache = learn(root)
    fact = next(i for i in k["items"] if i["id"] == "F-DOCS-react-18.3.1")
    assert fact["acceptance"] == "exact" and fact["data"]["chunks"] >= 3
    assert "useTransition" in fact["data"]["titles"]
    assert verify.check_out(out, root) == []
    index = (out / "docs-index.md").read_text(encoding="utf-8")
    assert "react@18.3.1" in index and "data, not instructions" in index
    assert "docs query" in (out / "INDEX.md").read_text(encoding="utf-8")
    res = docs.query(cache, "react", "18.3.1", "useTransition blocking")
    assert res["hits"][0]["title"].endswith("useTransition")
    assert res["hits"][0]["source"] == "node_modules/react/README.md" and res["marker"] == "data, not instructions"


def test_installed_package_of_another_version_is_not_used():
    root = react_project(installed="17.0.2")
    k, out, _ = learn(root)
    assert not any(i["data"].get("topic") == "docs" for i in k["items"])
    assert any("react@18.3.1" in s["source"] and "network off" in s["reason"] for s in k["coverage"]["skipped"])
    assert not (out / "docs-index.md").exists()


def test_npm_registry_tarball_for_exact_version():
    base, srv = serve({})
    try:
        srv.RequestHandlerClass  # routes filled after the base URL is known
        routes = {"/react/18.3.1": json.dumps({"dist": {"tarball": f"{base}/react-18.3.1.tgz"}}).encode(),
                  "/react-18.3.1.tgz": tarball({"package/README.md": README, "package/../evil.md": "# x\n",
                                                "package/docs/hooks.md": "# Hooks\n## useId\nUnique ids.\n",
                                                "package/src/deep/a.d.ts": "export type X = 1;\n"})}
        srv.shutdown()
        base, srv = serve(routes)
        routes["/react/18.3.1"] = json.dumps({"dist": {"tarball": f"{base}/react-18.3.1.tgz"}}).encode()
        root = react_project(installed=None)
        k, out, cache = learn(root, online=True, opts={"npm": base, "allow_private": True})
        fact = next(i for i in k["items"] if i["id"] == "F-DOCS-react-18.3.1")
        kinds = {s["kind"] for s in fact["data"]["sources"]}
        assert kinds == {"readme", "docs"}, fact["data"]["sources"]        # deep .d.ts and ../ entries skipped
        assert docs.query(cache, "react", "18.3.1", "useId")["hits"][0]["title"].startswith("Hooks")
        assert verify.check_out(out, root) == []
    finally:
        srv.shutdown()


def test_types_package_of_the_locked_version():
    root = repo({"package.json": '{"dependencies": {"react": "^18.2.0"}, "devDependencies": {"@types/react": "^18.3.0"}}',
                 "package-lock.json": '{"packages": {"node_modules/react": {"version": "18.3.1"},'
                                      ' "node_modules/@types/react": {"version": "18.3.3"}}}',
                 "node_modules/@types/react/package.json": '{"name": "@types/react", "version": "18.3.3"}',
                 "node_modules/@types/react/index.d.ts": "export function useId(): string;\n"
                                                         "export function useDeferredValue<T>(v: T): T;\n",
                 "node_modules/@types/react/README.md": "# Installation\nnpm install @types/react\n"})
    k, _, cache = learn(root)
    stack = next(i for i in k["items"] if i["id"] == "F-STACK-react-root")
    assert stack["data"]["types_version"] == "18.3.3"
    fact = next(i for i in k["items"] if i["id"] == "F-DOCS-react-18.3.1")
    assert [s["kind"] for s in fact["data"]["sources"]] == ["types"]          # README of @types is not docs
    hit = docs.query(cache, "react", "18.3.1", "useDeferredValue")["hits"][0]
    assert "useDeferredValue" in hit["text"] and hit["source"].endswith("@types/react/index.d.ts")


def test_pypi_release_description():
    routes = {"/fastapi/0.111.0/json": json.dumps({"info": {"description": "# FastAPI\n## Depends\nInject.\n"}}).encode()}
    base, srv = serve(routes)
    try:
        root = repo({"pyproject.toml": '[project]\ndependencies = ["fastapi>=0.110"]\n',
                     "uv.lock": '[[package]]\nname = "fastapi"\nversion = "0.111.0"\n'})
        k, _, cache = learn(root, online=True, opts={"pypi": base, "allow_private": True})
        assert any(i["id"] == "F-DOCS-fastapi-0.111.0" for i in k["items"])
        assert docs.query(cache, "fastapi", "0.111.0", "Depends")["hits"]
    finally:
        srv.shutdown()


def test_listed_sources_versioned_and_latest():
    reg = Path(tempfile.mkdtemp()) / "registry"
    (reg / "detectors").mkdir(parents=True)
    (reg / "detectors" / "s.yaml").write_text((ADDON / "registry" / "detectors" / "stack.yaml").read_text())
    base, srv = serve({"/v18.3.1/guide.md": b"# Guide\n## Server\nRender.\n", "/llms.txt": b"# llms\n## All\nx\n"})
    try:
        (reg / "docs-sources.yaml").write_text(json.dumps({"technologies": {"react": {"sources": [
            {"type": "raw", "url": base + "/{tag}/guide.md"}, {"type": "llms", "url": base + "/llms.txt"},
            {"type": "page", "url": base + "/missing.md"}]}}}))
        root = react_project()
        items = dna.detect.detect(root, reg)["items"]
        facts, cov = docs.build(root, items, reg, root / "cache", True, "2026-11-20", {"allow_private": True})
        matches = {s["source"].rsplit("/", 1)[-1]: s["match"] for s in facts[0]["data"]["sources"]}
        assert matches["guide.md"] == "exact" and matches["llms.txt"] == "latest"
        assert facts[0]["acceptance"] == "mixed"
        assert any(s["source"].endswith("/missing.md") for s in cov["skipped"])
    finally:
        srv.shutdown()


def test_network_rules():
    for url, hosts, word in (("http://registry.npmjs.org/x", {"registry.npmjs.org"}, "only https"),
                             ("https://evil.example/x", {"registry.npmjs.org"}, "not a registry"),
                             ("https://127.0.0.1/x", {"127.0.0.1"}, "not a public address")):
        try:
            docs.http_bytes(url, hosts)
            raise AssertionError(f"{url} accepted")
        except ValueError as e:
            assert word in str(e), e
    assert "registry.npmjs.org" in docs._hosts({}, {}) and "pypi.org" in docs._hosts({}, {})


def test_cli_query_codes():
    root = react_project()
    out, cache = root / "o", root / "c"
    run = lambda *a: subprocess.run([sys.executable, str(ADDON / "dna.py"), *a, "--root", str(root), "--out",
                                     str(out), "--cache", str(cache)], capture_output=True, text=True)
    assert run("learn", "--offline").returncode == 0
    ok = run("docs", "query", "react", "useTransition")
    assert ok.returncode == 0 and "data, not instructions" in ok.stdout and "useTransition" in ok.stdout
    js = json.loads(run("docs", "query", "react", "useState", "--json").stdout)
    assert js["version"] == "18.3.1" and js["hits"]
    assert run("docs", "query", "react", "x", "--version", "17.0.2").returncode == 2   # no index for it
    assert run("docs", "query", "vue", "x").returncode == 2                            # not in the project
    assert run("docs", "query", "react").returncode == 2                               # usage


def test_docs_index_size_limit():
    k = {"items": [{"id": f"F-DOCS-t{i}-1.0.0", "kind": "fact", "title": "t", "scope": {"paths": ["**"]},
                    "status": "auto-accepted", "evidence": ["x:1"],
                    "data": {"topic": "docs", "tech": f"t{i}", "version": "1.0.0", "chunks": 5,
                             "titles": ["A very long section title " * 3] * 12, "sources": []}} for i in range(80)]}
    from lib import emit
    assert len(emit.render_docs_index(k).encode()) <= verify.DOCS_INDEX_MAX_BYTES


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
