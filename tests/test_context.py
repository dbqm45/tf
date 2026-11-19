#!/usr/bin/env python3
"""Tests of the factory tool `tools/context.py` (a local index of library documentation for a specific version) without an
external network: resolve from node_modules, fetch local and from a local server (registry, llms.txt, tarball), query (BM25),
stale version, no index, rejection of a private address, limits. python3 tests/test_context.py"""
import http.server
import importlib.util
import io
import json
import tarfile
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPT = ROOT / "tools" / "context.py"
CACHE = None   # the index directory in the test's temporary directory

README = """# demo-lib

Klient HTTP do usługi Demo.

## Instalacja
npm install demo-lib

## createClient(options)
Tworzy klienta. Opcja `retries` (domyślnie 3) ustala liczbę ponowień, `timeoutMs` — limit czasu żądania.

## Migracja z 1.x
Funkcja `connect()` została usunięta w 2.0 — użyj `createClient()`.
"""

DTS = """export interface ClientOptions {
  retries?: number;
  timeoutMs?: number;
}
export declare function createClient(options?: ClientOptions): Client;
export declare class Client {
  get(path: string): Promise<Response>;
}
"""

LLMS = """# demo-lib 2.1

## Streaming
Metoda `client.stream(path)` zwraca AsyncIterable fragmentów odpowiedzi. Dodana w 2.1.0.
"""


def load():
    spec = importlib.util.spec_from_file_location("context", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def project(tmp: Path, version="2.1.0") -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "package.json").write_text(json.dumps({"dependencies": {"demo-lib": "^2.0.0"}}), encoding="utf-8")
    pkg = tmp / "node_modules" / "demo-lib"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "package.json").write_text(json.dumps({"name": "demo-lib", "version": version, "types": "index.d.ts"}),
                                      encoding="utf-8")
    (pkg / "README.md").write_text(README, encoding="utf-8")
    (pkg / "index.d.ts").write_text(DTS, encoding="utf-8")
    return tmp


def tgz(files: dict) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), "--cache", str(CACHE), *args], cwd=cwd, capture_output=True,
                          text=True, timeout=60)


def jl(r):
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


class Site(http.server.BaseHTTPRequestHandler):
    files: dict = {}

    def do_GET(self):  # noqa: N802
        body = Site.files.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        ctype = "application/json" if self.path.startswith("/npm/") else (
            "application/octet-stream" if self.path.endswith(".tgz") else "text/plain")
        self.send_header("content-type", ctype)
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def log_message(self, *a):
        pass


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    if not SCRIPT.is_file():
        print(f"✗ missing {SCRIPT}")
        return 1
    global CACHE
    di = load()
    with tempfile.TemporaryDirectory() as t:
        CACHE = Path(t) / "cache"
        di.CACHE = CACHE
        repo = project(Path(t) / "proj")
        r = run(["resolve", "demo-lib"], repo)
        res = jl(r) or {}
        check(r.returncode == 0 and res.get("id") == "npm:demo-lib@2.1.0" and "node_modules" in res.get("version_source", ""),
              f"D-1: resolve takes the version from node_modules: {r.stdout}{r.stderr}")

        r = run(["query", "demo-lib", "retries"], repo)
        check(r.returncode == 2 and "fetch" in r.stdout + r.stderr, f"D-2: query without an index → code 2 and a fetch hint: {r.stdout}")

        r = run(["fetch", "demo-lib"], repo)
        cache = CACHE / "npm" / "demo-lib@2.1.0"
        manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8")) if (cache / "manifest.json").is_file() else {}
        chunks = [json.loads(x) for x in (cache / "chunks.jsonl").read_text(encoding="utf-8").splitlines()] \
            if (cache / "chunks.jsonl").is_file() else []
        check(r.returncode == 0 and manifest.get("version") == "2.1.0" and manifest.get("id") == "npm:demo-lib@2.1.0",
              f"D-3: local fetch writes a manifest with the version: {r.stdout}{r.stderr} {manifest}")
        srcs = {s.get("path") for s in manifest.get("sources", [])}
        check(any(p and p.endswith("README.md") for p in srcs) and any(p and p.endswith("index.d.ts") for p in srcs)
              and all(s.get("sha256") and s.get("fetched_at") for s in manifest.get("sources", [])),
              f"D-4: the manifest lists README and .d.ts with sha256 and a date: {manifest.get('sources')}")
        titles = [c.get("title", "") for c in chunks]
        check(any("createClient(options)" in x for x in titles) and any("Migracja" in x for x in titles)
              and any("ClientOptions" in c.get("text", "") for c in chunks),
              f"D-5: chunks by README headings and the .d.ts declaration: {titles}")

        r = run(["query", "demo-lib", "jak ustawić liczbę ponowień retries"], repo)
        out = r.stdout
        check(r.returncode == 0 and "retries" in out and "demo-lib@2.1.0" in out and "data, not instructions" in out
              and "README.md" in out,
              f"D-6: query returns the relevant chunk with the source, version and the data marker: {out[:600]}")
        first = out.find("createClient(options)")
        check(first != -1 and (out.find("Instalacja") == -1 or first < out.find("Instalacja")),
              f"D-7: the most relevant chunk first (BM25): {out[:600]}")
        r = run(["query", "demo-lib", "connect usunięta migracja", "--json"], repo)
        res = jl(r) or {}
        hits = res.get("results") or []
        check(r.returncode == 0 and hits and "Migracja" in hits[0].get("title", "") and hits[0].get("version") == "2.1.0"
              and hits[0].get("source"),
              f"D-8: --json with the fields title, version, source: {r.stdout[:500]}")
        r = run(["query", "demo-lib", "retries", "--max-chars", "120"], repo)
        body = r.stdout.split("\n", 2)[-1] if r.stdout.count("\n") >= 2 else r.stdout
        check(r.returncode == 0 and len(r.stdout) < 1200, f"D-9: --max-chars limits the result: {len(r.stdout)}")

        project(repo, version="2.2.0")
        r = run(["query", "demo-lib", "retries"], repo)
        check(r.returncode == 3 and "2.2.0" in r.stdout + r.stderr and "fetch" in r.stdout + r.stderr,
              f"D-10: an index of a different version than the project → code 3 and a refresh command: {r.stdout}{r.stderr}")
        r = run(["list"], repo)
        check(r.returncode == 0 and "demo-lib@2.1.0" in r.stdout and "2.2.0" in r.stdout,
              f"D-11: list shows the index and the project version: {r.stdout}")
        project(repo, version="2.1.0")

        r = run(["fetch", "demo-lib", "--online", "--url", "http://127.0.0.1:9/docs.md"], repo)
        check(r.returncode != 0 and ("non-public" in r.stdout + r.stderr or "niepubliczny" in r.stdout + r.stderr or "localhost" in r.stdout + r.stderr
                                     or "https" in r.stdout + r.stderr),
              f"D-12: --url to a private address rejected: {r.stdout}{r.stderr}")

        # online fetch from a local server: registry → home page → llms.txt
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Site)
        port = srv.server_address[1]
        base = f"http://127.0.0.1:{port}"
        Site.files = {"/npm/demo-lib/2.1.0": json.dumps({"name": "demo-lib", "version": "2.1.0",
                                                          "homepage": f"{base}/site"}),
                      "/site/llms.txt": LLMS}
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            info = di.fetch("demo-lib", repo, online=True, npm_registry=f"{base}/npm", allow_private=True)
        except Exception as e:  # noqa: BLE001
            info = {"error": repr(e)}
        finally:
            srv.shutdown()
        man = json.loads((cache / "manifest.json").read_text(encoding="utf-8")) if (cache / "manifest.json").is_file() else {}
        check(any(s.get("url", "").endswith("/site/llms.txt") for s in man.get("sources", [])),
              f"D-13: --online adds llms.txt from the registry's home page: {info} {man.get('sources')}")
        r = run(["query", "demo-lib", "stream AsyncIterable"], repo)
        check(r.returncode == 0 and "client.stream" in r.stdout and "llms.txt" in r.stdout,
              f"D-14: a chunk from llms.txt found by query: {r.stdout[:500]}")

        big = repo / "node_modules" / "demo-lib" / "docs"
        big.mkdir(exist_ok=True)
        (big / "huge.md").write_text("# Duży\n" + "x " * (di.MAX_FILE_BYTES), encoding="utf-8")
        r = run(["fetch", "demo-lib"], repo)
        man = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and not any((s.get("path") or "").endswith("huge.md") for s in man.get("sources", []))
              and "huge.md" in r.stdout + r.stderr,
              f"D-15: a file over the limit skipped with a message: {r.stdout}{r.stderr}")

    # factory mode: a given version without a project, documentation from a package in the registry (tarball)
    with tempfile.TemporaryDirectory() as t2:
        empty = Path(t2)
        CACHE = empty / "cache"
        di.CACHE = CACHE
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Site)
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        Site.files = {
            "/npm/demo-lib/3.0.0": json.dumps({"name": "demo-lib", "version": "3.0.0",
                                               "dist": {"tarball": f"{base}/tgz/demo-lib-3.0.0.tgz"}}),
            "/tgz/demo-lib-3.0.0.tgz": tgz({"package/README.md": "# demo-lib 3\n\n## defineConfig()\nNowe API konfiguracji w 3.0.\n",
                                            "package/index.d.ts": "export declare function defineConfig(c: object): object;\n",
                                            "package/CHANGELOG.md": "# Zmiany\n\n## 3.0.0\nUsunięto createClient().\n"}),
            "/npm/evil-lib/1.0.0": json.dumps({"name": "evil-lib", "version": "1.0.0",
                                               "dist": {"tarball": f"{base}/tgz/evil-lib-1.0.0.tgz"}}),
            "/tgz/evil-lib-1.0.0.tgz": tgz({"package/../../poza.md": "# zły\n", "package/README.md": "# ok\n"}),
        }
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            try:
                man = di.fetch("demo-lib", empty, online=True, version="3.0.0", npm_registry=f"{base}/npm",
                               allow_private=True)
            except Exception as e:  # noqa: BLE001
                man = {"error": repr(e)}
            paths = [s.get("path") or s.get("url") or "" for s in man.get("sources", [])]
            check(man.get("id") == "npm:demo-lib@3.0.0" and any(p.endswith("index.d.ts") for p in paths)
                  and any(p.endswith("CHANGELOG.md") for p in paths),
                  f"D-16: --version without a project: README, .d.ts and CHANGELOG from the package in the registry: {man}")
            r = subprocess.run([sys.executable, str(SCRIPT), "--cache", str(CACHE), "--root", str(empty), "query",
                                "demo-lib", "defineConfig",
                                "--version", "3.0.0"], capture_output=True, text=True, timeout=60)
            check(r.returncode == 0 and "defineConfig" in r.stdout and "demo-lib@3.0.0" in r.stdout,
                  f"D-17: query --version uses the index of that version: {r.stdout}{r.stderr}")
            try:
                bad = di.fetch("evil-lib", empty, online=True, version="1.0.0", npm_registry=f"{base}/npm",
                               allow_private=True)
            except Exception as e:  # noqa: BLE001
                bad = {"error": repr(e)}
            check(not (empty / "poza.md").exists() and not (empty.parent / "poza.md").exists()
                  and not any("poza.md" in (s.get("path") or "") for s in bad.get("sources", []))
                  and any("poza.md" in s for s in bad.get("skipped", [])),
                  f"D-18: a tarball entry escaping the package rejected: {bad}")
        finally:
            srv.shutdown()

    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the local documentation index")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
