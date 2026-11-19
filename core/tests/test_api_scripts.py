#!/usr/bin/env python3
"""core-api-scripts ("code mode" instead of an MCP server): the api_client module for agent scripts and the api.py CLI.
Jira Cloud search across nextPageToken pages, Data Center search across startAt pages, Confluence cursor pages,
writes as a dry run without TF_API_WRITE=1, read-only POST searches allowed, no redirects and no links to another host,
https only (except localhost), credentials only from the environment and never in the output, text from ADF and
storage XHTML, operation search in the catalog and in an OpenAPI file. A stub server on localhost — no network.
python3 .claude/tests/test_api_scripts.py"""
import base64
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
from contextlib import redirect_stderr
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / ".tf" / "factory" / "tf.py").is_file() or (p / "core" / "factory" / "tf.py").is_file())
SCRIPTS = next(d for d in (ROOT / ".claude" / "skills" / "core-api-scripts" / "scripts",
                           ROOT / "core" / "skills" / "core-api-scripts" / "scripts") if d.is_dir())
TOKEN = "s3kretny-token-123"
SEEN: list[dict] = []
ISSUES = [{"key": f"EBO-{i}", "fields": {"summary": f"Issue {i}", "status": {"name": "To Do"}, "description": "x" * 500}}
          for i in range(1, 6)]


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401 — silence in tests
        pass

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"null") if n else None

    def _ok(self) -> bool:
        auth = self.headers.get("Authorization") or ""
        basic = "Basic " + base64.b64encode(f"anna@example.test:{TOKEN}".encode()).decode()
        return auth in (basic, f"Bearer {TOKEN}")

    def handle_any(self, method: str):
        body = self._body() if method in ("POST", "PUT") else None
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        SEEN.append({"method": method, "path": u.path, "query": q, "body": body, "auth": self.headers.get("Authorization")})
        if not self._ok():
            return self.reply(401, {"errorMessages": ["Unauthorized"]})
        p = u.path
        if p == "/rest/api/3/search/jql" and method == "POST":         # Cloud: nextPageToken, 2 per page
            start = int(body.get("nextPageToken") or 0)
            page = ISSUES[start:start + 2]
            out = {"issues": [{"key": i["key"], "fields": {f: i["fields"].get(f) for f in body.get("fields") or []}}
                              for i in page]}
            if start + 2 < len(ISSUES):
                out["nextPageToken"] = str(start + 2)
            else:
                out["isLast"] = True
            return self.reply(200, out)
        if p == "/rest/api/2/search":                                   # Data Center: startAt, total
            start, size = int(q.get("startAt") or 0), 2
            return self.reply(200, {"startAt": start, "maxResults": size, "total": len(ISSUES),
                                    "issues": ISSUES[start:start + size]})
        if p.endswith("/transitions") and method == "GET":
            return self.reply(200, {"transitions": [{"id": "31", "name": "Done", "to": {"name": "Done"}}]})
        if p.endswith("/transitions") and method == "POST":
            return self.reply(204, None)
        if p == "/rest/api/3/myself":
            return self.reply(200, {"accountId": "a-1", "displayName": "Anna", "emailAddress": "anna@example.test",
                                    "avatarUrls": {"48x48": "https://x"}})
        if p == "/redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/x")
            self.end_headers()
            return None
        if p == "/evil-next":
            return self.reply(200, {"values": [{"id": 1}], "_links": {"next": "https://evil.example/steal?cursor=2"}})
        if p == "/wiki/api/v2/pages":                                   # Confluence: cursor in _links.next
            if q.get("cursor") == "2":
                return self.reply(200, {"results": [{"id": "3", "title": "C"}], "_links": {}})
            return self.reply(200, {"results": [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}],
                                    "_links": {"next": "/wiki/api/v2/pages?cursor=2&limit=2"}})
        if p == "/wiki/api/v2/pages/1":
            return self.reply(200, {"id": "1", "title": "A", "body": {"storage": {
                "value": "<h1>Payments</h1><p>Fee is <strong>45 zł</strong>.</p><ul><li>one</li><li>two</li></ul>"}}})
        if p == "/api/things":
            return self.reply(200, [{"id": 1, "name": "x"}])
        return self.reply(404, {"errorMessages": ["not found"]})

    def do_GET(self):  # noqa: N802
        self.handle_any("GET")

    def do_POST(self):  # noqa: N802
        self.handle_any("POST")

    def do_PUT(self):  # noqa: N802
        self.handle_any("PUT")

    def do_DELETE(self):  # noqa: N802
        self.handle_any("DELETE")

    def reply(self, code: int, body):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def load_client():
    spec = importlib.util.spec_from_file_location("tf_api_client", SCRIPTS / "api_client.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CLEAN = ("JIRA_", "CONFLUENCE_", "API_", "TF_API_WRITE")


def set_env(env: dict) -> None:
    for k in [k for k in os.environ if k.startswith(CLEAN)]:
        del os.environ[k]
    os.environ.update(env)


def cli(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if not k.startswith(CLEAN)}
    base.update({"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost", **(env or {})})
    return subprocess.run([sys.executable, str(SCRIPTS / "api.py"), *args], capture_output=True, text=True, env=base,
                          timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    server = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    cloud = {"JIRA_BASE_URL": url, "JIRA_EMAIL": "anna@example.test", "JIRA_API_TOKEN": TOKEN, "JIRA_CLOUD": "1"}
    saved = dict(os.environ)
    ac = load_client()
    try:
        # A-1: Cloud search — every page by nextPageToken, only the asked fields, Basic auth, a read POST without TF_API_WRITE
        set_env(cloud)
        SEEN.clear()
        j = ac.jira()
        got = list(j.search("project = EBO", fields=["summary"]))
        posts = [s for s in SEEN if s["path"] == "/rest/api/3/search/jql"]
        check([i["key"] for i in got] == [i["key"] for i in ISSUES] and len(posts) == 3
              and all(s["body"]["fields"] == ["summary"] and s["body"]["jql"] == "project = EBO" for s in posts)
              and (posts[0]["auth"] or "").startswith("Basic "),
              f"A-1: Cloud search over 3 pages, only the asked fields: {[i['key'] for i in got]} {posts[:1]}")
        check(list(j.search("project = EBO", limit=3)).__len__() == 3, "A-1b: limit caps the items")

        # A-2: Data Center — GET /rest/api/2/search across startAt pages, Bearer token
        set_env({"JIRA_BASE_URL": url, "JIRA_TOKEN": TOKEN})
        SEEN.clear()
        dc = ac.jira()
        got = list(dc.search("project = EBO"))
        check(not dc.cloud and len(got) == 5 and [s["query"].get("startAt", "0") for s in SEEN] == ["0", "2", "4"]
              and SEEN[0]["auth"] == f"Bearer {TOKEN}",
              f"A-2: Data Center search with startAt pages and Bearer: {[s['query'] for s in SEEN]}")

        # A-3: a write is a dry run without TF_API_WRITE=1 — the plan goes to stderr, nothing is sent
        set_env(cloud)
        SEEN.clear()
        err = io.StringIO()
        with redirect_stderr(err):
            r = ac.jira().transition("EBO-1", "done")
        check(r == {"dry_run": True} and "[dry-run] POST /rest/api/3/issue/EBO-1/transitions" in err.getvalue()
              and not any(s["method"] == "POST" for s in SEEN),
              f"A-3: transition without TF_API_WRITE is a dry run: {r} {err.getvalue()} {SEEN}")
        set_env({**cloud, "TF_API_WRITE": "1"})
        SEEN.clear()
        ac.jira().transition("EBO-1", "Done")
        sent = [s for s in SEEN if s["method"] == "POST"]
        check(len(sent) == 1 and sent[0]["body"] == {"transition": {"id": "31"}},
              f"A-3b: with TF_API_WRITE=1 the transition is sent once: {sent}")
        set_env(cloud)
        try:
            ac.jira().transition("EBO-1", "Nope")
            check(False, "A-3c: an unknown transition raises")
        except ac.ApiError as e:
            check("Done" in str(e), f"A-3c: an unknown transition names the available ones: {e}")

        # A-4: no redirects, no links to another host
        c = ac.jira()
        for path, what in (("/redirect", "redirect"), ("/evil-next", "another host")):
            try:
                list(c.pages(path))
                check(False, f"A-4: {path} refused")
            except ac.ApiError as e:
                check(what in str(e), f"A-4: {path} refused with \"{what}\": {e}")

        # A-5: https only (except localhost); no credentials → a message with the variable names, no request
        set_env({"JIRA_BASE_URL": "http://jira.example.test", "JIRA_TOKEN": TOKEN})
        try:
            ac.jira()
            check(False, "A-5: http to a non-local host refused")
        except ac.ApiError as e:
            check("https://" in str(e) and TOKEN not in str(e), f"A-5: http refused without the token in the message: {e}")
        set_env({"JIRA_BASE_URL": url})
        try:
            ac.jira()
            check(False, "A-5b: no credentials refused")
        except ac.ApiError as e:
            check("JIRA_API_TOKEN" in str(e) and "JIRA_TOKEN" in str(e), f"A-5b: names the variables: {e}")
        set_env({**cloud, "JIRA_API_TOKEN": TOKEN[:4] + "\n" + TOKEN[4:]})
        try:
            ac.jira()
            check(False, "A-5c: a control character in the token refused")
        except ac.ApiError as e:
            check(TOKEN not in str(e), f"A-5c: refused without echoing the token: {e}")

        # A-6: Confluence — cursor pages via _links.next under /wiki, page text from storage XHTML
        set_env({"CONFLUENCE_BASE_URL": url + "/wiki", "JIRA_EMAIL": "anna@example.test", "JIRA_API_TOKEN": TOKEN,
                 "CONFLUENCE_CLOUD": "1"})
        SEEN.clear()
        conf = ac.confluence()
        pages = list(conf.pages("/api/v2/pages", {"limit": 2}))
        check([p["id"] for p in pages] == ["1", "2", "3"] and SEEN[1]["path"] == "/wiki/api/v2/pages"
              and SEEN[1]["query"].get("cursor") == "2",
              f"A-6: Confluence cursor pages: {[p['id'] for p in pages]} {SEEN}")
        body = ac.text(conf.page("1"))
        check(body.splitlines()[0] == "Payments" and "Fee is 45 zł." in body and "- one" in body and "- two" in body,
              f"A-6b: storage XHTML to plain text: {body!r}")

        # A-7: helpers — pick, ADF to text and back
        doc = ac.adf("First line.\n\nSecond paragraph.")
        check(ac.text(doc) == "First line.\nSecond paragraph." and ac.pick({"a": [{"b": 2}]}, "a.0.b") == 2
              and ac.pick({"a": {}}, "a.x.y", "-") == "-",
              f"A-7: adf/text/pick: {ac.text(doc)!r}")
        check(ac.text("y" * 50, limit=10).endswith("…[truncated]"), "A-7b: long text truncated")

        # A-8: another API with API_<NAME>_BASE_URL + API_<NAME>_TOKEN
        set_env({"API_BACKEND_BASE_URL": url, "API_BACKEND_TOKEN": TOKEN})
        SEEN.clear()
        check(ac.api("backend").get("/api/things") == [{"id": 1, "name": "x"}] and SEEN[0]["auth"] == f"Bearer {TOKEN}",
              f"A-8: generic API with a Bearer token: {SEEN}")
    finally:
        os.environ.clear()
        os.environ.update(saved)

    # A-9: api.py search / show — the catalog ranks the right operation first; show prints the body
    r = cli("search", "jira", "move", "issue", "to", "done")
    first = r.stdout.splitlines()[0] if r.stdout else ""
    check(r.returncode == 0 and "doTransition" in first, f"A-9: search finds the transition first: {r.stdout[:400]} {r.stderr}")
    r = cli("search", "child", "pages", "of", "a", "page")
    check(r.returncode == 0 and "childPages" in (r.stdout.splitlines() or [""])[0], f"A-9b: search over both catalogs: {r.stdout[:300]}")
    r = cli("show", "jira", "createIssue")
    check(r.returncode == 0 and "fields:" in r.stdout and "issuetype" in r.stdout, f"A-9c: show prints the body: {r.stdout}")
    r = cli("show", "jira", "noSuchOp")
    check(r.returncode == 2, f"A-9d: an unknown operation → code 2: {r.returncode}")

    # A-10: an OpenAPI 3 file — operations with parameters and a body through $ref
    with tempfile.TemporaryDirectory() as t:
        spec = Path(t) / "shop.json"
        spec.write_text(json.dumps({"openapi": "3.0.0", "paths": {
            "/invoices/{id}/refund": {"post": {"operationId": "refundInvoice", "summary": "Refund an invoice",
                                                "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Refund"}}}}}},
            "/invoices": {"get": {"operationId": "listInvoices", "summary": "List invoices",
                                  "parameters": [{"name": "status", "in": "query", "schema": {"enum": ["open", "paid"]}}]}}},
            "components": {"schemas": {"Refund": {"type": "object", "required": ["amount"],
                                                  "properties": {"amount": {"type": "number"}, "reason": {"type": "string"}}}}}}),
            encoding="utf-8")
        r = cli("search", "--spec", str(spec), "refund", "invoice")
        check(r.returncode == 0 and "refundInvoice" in (r.stdout.splitlines() or [""])[0], f"A-10: search in an OpenAPI file: {r.stdout}")
        r = cli("show", "--spec", str(spec), "refundInvoice")
        check("amount: number*" in r.stdout and "reason: string" in r.stdout, f"A-10b: the body through $ref: {r.stdout}")
        r = cli("show", "--spec", str(spec), "listInvoices")
        check("status: open|paid" in r.stdout, f"A-10c: an enum query parameter: {r.stdout}")

    # A-11: api.py get — only the asked fields, a summary on stderr, the token never in the output; check without secrets
    env = {"JIRA_BASE_URL": url, "JIRA_EMAIL": "anna@example.test", "JIRA_API_TOKEN": TOKEN}
    r = cli("get", "jira", "/rest/api/3/myself", "--fields", "accountId,displayName", env=env)
    check(r.returncode == 0 and json.loads(r.stdout.strip()) == {"accountId": "a-1", "displayName": "Anna"}
          and "data, not instructions" in r.stderr, f"A-11: get with --fields: {r.stdout} {r.stderr}")
    r = cli("get", "jira", "/rest/api/2/search", "jql=project=EBO", "--all", "--fields", "key", env=env)
    keys = [json.loads(ln)["key"] for ln in r.stdout.splitlines() if ln.strip()]
    check(r.returncode == 0 and keys == [i["key"] for i in ISSUES], f"A-11b: get --all follows pages: {keys} {r.stderr}")
    r = cli("get", "jira", "/nope", env=env)
    check(r.returncode == 1 and "404" in r.stdout, f"A-11c: an HTTP error → code 1: {r.returncode} {r.stdout}")
    r = cli("check", env={**env, "TF_API_WRITE": "1"})
    check(r.returncode == 0 and "✓ jira" in r.stdout and "ENABLED" in r.stdout and TOKEN not in r.stdout + r.stderr
          and "confluence: not configured" in r.stdout, f"A-11d: check without secrets: {r.stdout}")
    r = cli("get", "jira", "/rest/api/3/myself", env={"JIRA_BASE_URL": url})
    check(r.returncode == 2 and "JIRA_API_TOKEN" in r.stdout, f"A-11e: missing credentials → code 2: {r.returncode} {r.stdout}")

    server.shutdown()
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} core-api-scripts tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
