#!/usr/bin/env python3
"""A REST API client for scripts the agent writes ("code mode"): Jira, Confluence and any API with a token.

The agent does not call dozens of MCP tools one by one; it writes one script that queries, paginates, filters and
prints only what the task needs. Large answers (a Jira issue is tens of kilobytes of JSON) never reach the context.

    import sys; sys.path.insert(0, ".claude/skills/core-api-scripts/scripts")
    from api_client import jira, confluence, api, pick, text
    j = jira()
    for issue in j.search("project = EBO AND statusCategory != Done", fields=["summary", "status"], limit=200):
        print(issue["key"], pick(issue, "fields.status.name"), pick(issue, "fields.summary"))

Addresses and credentials come only from environment variables (never from files in the repository, which a pull
request can change):
  Jira        JIRA_BASE_URL + JIRA_EMAIL and JIRA_API_TOKEN (Cloud) or JIRA_TOKEN (Data Center, Bearer)
  Confluence  CONFLUENCE_BASE_URL (Cloud: https://<site>.atlassian.net/wiki; when absent and JIRA_BASE_URL is an
              *.atlassian.net site, <JIRA_BASE_URL>/wiki) + CONFLUENCE_EMAIL/CONFLUENCE_API_TOKEN/CONFLUENCE_TOKEN,
              falling back to the JIRA_* credentials (one Atlassian Cloud token works for both)
  other API   API_<NAME>_BASE_URL + API_<NAME>_TOKEN (Bearer), e.g. API_BACKEND_BASE_URL → api("backend")
Safety: https only (http only for localhost), requests only to the configured host, no redirects (the credentials
never go to another address), answers up to 20 MB, a 30-second timeout. Writes (POST/PUT/PATCH/DELETE other than the
read-only searches) are a dry run unless TF_API_WRITE=1 is set: the call is printed as "[dry-run] …" to stderr and
returns {"dry_run": True}, so a script run without the variable lists every change for the human to approve first.
Standard library only.
"""
from __future__ import annotations

import base64
import html.parser
import http.client
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlencode, urljoin, urlparse

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

MAX_BYTES = 20_000_000
TIMEOUT = 30
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# POST endpoints that only read (searches with a body); they are not writes
READ_POSTS = {
    "jira": ("/rest/api/3/search/jql", "/rest/api/3/search/approximate-count", "/rest/api/3/issue/bulkfetch",
             "/rest/api/3/jql/parse", "/rest/api/3/search", "/rest/api/2/search", "/rest/api/2/jql/parse"),
}


class ApiError(Exception):
    """A request failed — a message for the human, never with credentials."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):   # the Authorization header never follows a redirect
        raise ApiError(f"the server answered with a redirect ({code}) — check the base address variable")


def _clean(*values: str) -> None:
    if any(ord(ch) < 32 or ord(ch) == 127 for v in values for ch in v):
        raise ApiError("the credentials contain a newline or another control character — set the variables again")


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _auth(prefix: str, fallback: str | None = None) -> str | None:
    """The Authorization header from <PREFIX>_EMAIL + <PREFIX>_API_TOKEN (Basic) or <PREFIX>_TOKEN (Bearer)."""
    for p in (prefix, fallback):
        if not p:
            continue
        email, api_token, token = _env(f"{p}_EMAIL"), _env(f"{p}_API_TOKEN"), _env(f"{p}_TOKEN")
        _clean(email, api_token, token)
        if email and api_token:
            return "Basic " + base64.b64encode(f"{email}:{api_token}".encode()).decode()
        if token:
            return f"Bearer {token}"
    return None


def writes_allowed() -> bool:
    return _env("TF_API_WRITE") == "1"


class Client:
    """Requests to one API. `get/post/put/patch/delete` return parsed JSON (or text); `pages` iterates all results."""

    def __init__(self, name: str, base: str, auth: str | None, base_var: str = "", auth_vars: str = ""):
        if not base:
            raise ApiError(f"no address for {name} — set {base_var or 'the base address variable'}")
        parsed = urlparse(base)
        self.host = (parsed.hostname or "").lower()
        self.local = self.host in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and self.local):
            raise ApiError(f"the {name} address must start with https:// — credentials do not go over an unencrypted connection")
        if not auth:
            raise ApiError(f"no credentials for {name} — set {auth_vars or 'the token variables'}; the factory does not store them")
        self.name, self.base, self.origin = name, base.rstrip("/"), f"{parsed.scheme}://{parsed.netloc}"
        self.headers = {"Authorization": auth, "Accept": "application/json"}
        self.requests = 0

    # -- low level ------------------------------------------------------------------------------------------------
    def url(self, path: str, params: dict | None = None) -> str:
        if re.match(r"^[a-z][a-z0-9+.-]*://", path, re.I):          # an absolute "next" link: only on the same host
            if urlparse(path).netloc.lower() != urlparse(self.origin).netloc.lower():
                raise ApiError(f"refused a link to another host: {urlparse(path).netloc}")
            full = path
        elif path.startswith("/") and self.base != self.origin and path.startswith(urlparse(self.base).path + "/"):
            full = self.origin + path                                  # a link that already has the base path (/wiki/…)
        else:
            full = self.base + "/" + path.lstrip("/")
        clean = {k: (",".join(map(str, v)) if isinstance(v, (list, tuple)) else v) for k, v in (params or {}).items()
                 if v is not None}
        return full + (("&" if "?" in full else "?") + urlencode(clean, doseq=True) if clean else "")

    def is_write(self, method: str, path: str) -> bool:
        if method not in WRITE_METHODS:
            return False
        bare = urlparse(path).path if "://" in path else path.split("?")[0]
        return not (method == "POST" and bare.rstrip("/").endswith(READ_POSTS.get(self.name, ())))

    def request(self, method: str, path: str, params: dict | None = None, json_body=None, data: bytes | None = None,
                headers: dict | None = None):
        method = method.upper()
        url = self.url(path, params)
        if self.is_write(method, path) and not writes_allowed():
            shown = json.dumps(json_body, ensure_ascii=False)[:300] if json_body is not None else ""
            print(f"[dry-run] {method} {urlparse(url).path} {shown}".rstrip(), file=sys.stderr)
            return {"dry_run": True}
        body = json.dumps(json_body).encode("utf-8") if json_body is not None else data
        hdrs = {**self.headers, **(headers or {})}
        if json_body is not None:
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
        handlers = [_NoRedirect] + ([urllib.request.ProxyHandler({})] if self.local else [])
        self.requests += 1
        try:
            with urllib.request.build_opener(*handlers).open(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_BYTES + 1)
                ctype = resp.headers.get("Content-Type") or ""
        except ApiError:
            raise
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read(2000).decode("utf-8", "replace")
            except OSError:
                pass
            why = {400: "the request is invalid", 401: "the credentials were rejected", 403: "the account has no access",
                   404: "not found or the account cannot see it", 429: "too many requests — wait and retry"}.get(e.code, "error")
            raise ApiError(f"{self.name}: {method} {urlparse(url).path} → {e.code} ({why}) {detail[:500]}".rstrip()) from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLError):
                raise ApiError(f"the certificate of {self.host} could not be verified — the connection was stopped") from None
            raise ApiError(f"could not connect to {self.name} ({self.host}) within {TIMEOUT} seconds") from None
        except (http.client.HTTPException, TimeoutError, OSError, ValueError):
            raise ApiError(f"the connection to {self.name} ({self.host}) was interrupted or the answer was invalid") from None
        if len(raw) > MAX_BYTES:
            raise ApiError(f"the answer from {self.name} is larger than 20 MB — narrow the query (fields, limit)")
        if not raw:
            return None
        if "json" in ctype or raw[:1] in (b"{", b"["):
            try:
                return json.loads(raw.decode("utf-8"))
            except ValueError:
                pass
        return raw.decode("utf-8", "replace")

    def get(self, path: str, **params):
        return self.request("GET", path, params)

    def post(self, path: str, json=None, **params):  # noqa: A002 — the familiar name of the argument
        return self.request("POST", path, params, json)

    def put(self, path: str, json=None, **params):  # noqa: A002
        return self.request("PUT", path, params, json)

    def patch(self, path: str, json=None, **params):  # noqa: A002
        return self.request("PATCH", path, params, json)

    def delete(self, path: str, **params):
        return self.request("DELETE", path, params)

    def pages(self, path: str, params: dict | None = None, items: str | None = None, method: str = "GET",
              body: dict | None = None, limit: int | None = None):
        """Every item of a paginated list, across pages. Recognizes the styles in use: `nextPageToken` (Jira search),
        `startAt`/`maxResults`/`total`/`isLast` (Jira), `_links.next` (Confluence, cursor) and `start`/`limit`/`size`.
        `items`: the key with the list (detected: values, issues, results, comments, worklogs); `limit`: the most items."""
        params, body = dict(params or {}), (dict(body) if body is not None else None)
        seen, next_path = 0, path
        for _ in range(10_000):
            page = self.request(method, next_path, params, body)
            if not isinstance(page, (dict, list)) or (isinstance(page, dict) and page.get("dry_run")):
                return
            key = items or next((k for k in ("values", "issues", "results", "comments", "worklogs", "histories")
                                 if isinstance(page, dict) and isinstance(page.get(k), list)), None)
            batch = page if isinstance(page, list) else (page.get(key) or [] if key else [])
            for it in batch:
                yield it
                seen += 1
                if limit is not None and seen >= limit:
                    return
            if isinstance(page, list) or not batch:
                return
            if page.get("nextPageToken"):
                target = body if body is not None else params
                target["nextPageToken"] = page["nextPageToken"]
                continue
            nxt = (page.get("_links") or {}).get("next")
            if nxt:   # the link carries the cursor and the parameters; url() keeps it on the same host
                next_path, params = nxt, {}
                continue
            if page.get("isLast") is True:
                return
            if "startAt" in page:
                start = int(page.get("startAt") or 0) + len(batch)
                total = page.get("total")
                if isinstance(total, int) and start >= total:
                    return
                if page.get("isLast") is None and total is None and len(batch) < int(page.get("maxResults") or 0):
                    return
                (body if body is not None else params)["startAt"] = start
                continue
            if "start" in page and "size" in page:
                if page.get("size", 0) < page.get("limit", 0):
                    return
                params["start"] = int(page.get("start") or 0) + len(batch)
                continue
            return


class Jira(Client):
    """Jira Cloud (API v3, *.atlassian.net or JIRA_CLOUD=1) or Data Center (API v2)."""

    def __init__(self):
        base = _env("JIRA_BASE_URL")
        super().__init__("jira", base, _auth("JIRA"), "JIRA_BASE_URL (e.g. https://company.atlassian.net)",
                         "JIRA_EMAIL and JIRA_API_TOKEN (Cloud) or JIRA_TOKEN (Data Center)")
        flag = _env("JIRA_CLOUD")
        self.cloud = flag == "1" if flag in ("0", "1") else self.host.endswith(".atlassian.net")
        self.v = "3" if self.cloud else "2"

    def search(self, jql: str, fields=("summary", "status", "assignee"), limit: int | None = None, expand: str | None = None):
        """Issues matching JQL; only the given fields (each extra field is more JSON)."""
        fields = list(fields) if fields else None
        if self.cloud:
            body = {"jql": jql, "maxResults": 100, **({"fields": fields} if fields else {}),
                    **({"expand": expand} if expand else {})}
            yield from self.pages("/rest/api/3/search/jql", method="POST", body=body, items="issues", limit=limit)
        else:
            params = {"jql": jql, "maxResults": 100, "fields": fields, "expand": expand}
            yield from self.pages("/rest/api/2/search", params, items="issues", limit=limit)

    def count(self, jql: str) -> int | None:
        if self.cloud:
            r = self.post("/rest/api/3/search/approximate-count", json={"jql": jql})
            return r.get("count") if isinstance(r, dict) else None
        r = self.get("/rest/api/2/search", jql=jql, maxResults=0)
        return r.get("total") if isinstance(r, dict) else None

    def issue(self, key: str, fields=("summary", "status", "description"), expand: str | None = None):
        return self.get(f"/rest/api/{self.v}/issue/{key}", fields=list(fields) if fields else None, expand=expand)

    def comments(self, key: str, limit: int | None = None):
        yield from self.pages(f"/rest/api/{self.v}/issue/{key}/comment", items="comments", limit=limit)

    def transitions(self, key: str) -> list[dict]:
        r = self.get(f"/rest/api/{self.v}/issue/{key}/transitions")
        return r.get("transitions") or [] if isinstance(r, dict) else []

    def transition(self, key: str, name: str):
        """Moves the issue through the transition with this name (case-insensitive); a write — dry run without TF_API_WRITE=1."""
        match = [t for t in self.transitions(key) if str(t.get("name", "")).lower() == name.lower()
                 or str((t.get("to") or {}).get("name", "")).lower() == name.lower()]
        if not match:
            raise ApiError(f"{key}: no transition \"{name}\" — available: "
                           + ", ".join(str(t.get("name")) for t in self.transitions(key)))
        return self.post(f"/rest/api/{self.v}/issue/{key}/transitions", json={"transition": {"id": match[0]["id"]}})

    def comment(self, key: str, body: str):
        """Adds a plain-text comment (ADF in Cloud); a write — dry run without TF_API_WRITE=1."""
        payload = {"body": adf(body)} if self.cloud else {"body": body}
        return self.post(f"/rest/api/{self.v}/issue/{key}/comment", json=payload)


class Confluence(Client):
    """Confluence Cloud (base …/wiki, API v2 for pages, v1 for CQL search) or Data Center (API v1)."""

    def __init__(self):
        base = _env("CONFLUENCE_BASE_URL")
        jira_base = _env("JIRA_BASE_URL").rstrip("/")
        if not base and (urlparse(jira_base).hostname or "").endswith(".atlassian.net"):
            base = jira_base + "/wiki"
        super().__init__("confluence", base, _auth("CONFLUENCE", "JIRA"),
                         "CONFLUENCE_BASE_URL (e.g. https://company.atlassian.net/wiki) or a Cloud JIRA_BASE_URL",
                         "CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN (or the JIRA_* ones), or CONFLUENCE_TOKEN")
        flag = _env("CONFLUENCE_CLOUD")
        self.cloud = flag == "1" if flag in ("0", "1") else self.host.endswith(".atlassian.net")

    def search(self, cql: str, limit: int | None = 50):
        """Content matching CQL (title, excerpt, type, id) — without bodies."""
        yield from self.pages("/rest/api/search", {"cql": cql, "limit": 50}, items="results", limit=limit)

    def page(self, page_id: str, body_format: str = "storage") -> dict | None:
        """One page with its body (storage = XHTML); text(page) gives plain text."""
        if self.cloud:
            return self.get(f"/api/v2/pages/{page_id}", **{"body-format": body_format})
        return self.get(f"/rest/api/content/{page_id}", expand="body.storage,version,space")


def jira() -> Jira:
    return Jira()


def confluence() -> Confluence:
    return Confluence()


def api(name: str) -> Client:
    """Any REST API with a Bearer token: API_<NAME>_BASE_URL and API_<NAME>_TOKEN."""
    up = re.sub(r"[^A-Z0-9]", "_", name.upper())
    token = _env(f"API_{up}_TOKEN")
    _clean(token)
    return Client(name.lower(), _env(f"API_{up}_BASE_URL"), f"Bearer {token}" if token else None,
                  f"API_{up}_BASE_URL", f"API_{up}_TOKEN")


def pick(obj, path: str, default=None):
    """A value by a dotted path: pick(issue, "fields.status.name"), pick(x, "items.0.id")."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.lstrip("-").isdigit() and -len(cur) <= int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return default
        if cur is None:
            return default
    return cur


class _Text(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "table"}

    def __init__(self):
        super().__init__()
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("li",):
            self.out.append("\n- ")
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)


def text(value, limit: int | None = 20_000) -> str:
    """Plain text from an ADF document (Jira Cloud), Confluence storage XHTML, a page dict or a string; truncated to `limit`."""
    if isinstance(value, dict) and "body" in value and not value.get("type"):
        body = value["body"]
        value = pick(body, "storage.value") or pick(body, "atlas_doc_format.value") or body
        if isinstance(value, str) and value.startswith("{"):
            try:
                value = json.loads(value)
            except ValueError:
                pass
    if isinstance(value, (dict, list)):
        out = _adf(value)
    elif isinstance(value, str) and "<" in value and ">" in value:
        p = _Text()
        p.feed(value)
        out = "".join(p.out)
    else:
        out = str(value or "")
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out if limit is None or len(out) <= limit else out[:limit] + " …[truncated]"


def _adf(node) -> str:
    if isinstance(node, list):
        return "".join(_adf(n) for n in node)
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return str(node.get("text") or "")
    if node.get("type") == "hardBreak":
        return "\n"
    inner = "".join(_adf(c) for c in node.get("content") or [])
    if node.get("type") == "listItem":
        return "- " + inner.strip() + "\n"
    return inner + ("\n" if node.get("type") in ("paragraph", "heading", "codeBlock", "blockquote", "tableRow") else "")


def adf(plain: str) -> dict:
    """A plain text (paragraphs separated by blank lines) as an ADF document for Jira Cloud fields and comments."""
    paras = [p for p in re.split(r"\n\s*\n", plain.strip()) if p.strip()] or [""]
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": p}] if p else []} for p in paras]}
