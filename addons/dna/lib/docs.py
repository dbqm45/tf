"""Official documentation for the exact versions in the project: fetch, split into chunks, index, query (BM25).

Sources, most exact first:
  1. the installed package (npm: node_modules/<pkg> whose package.json has the same version) — no network;
  2. the package registry for that version: npm tarball (README, CHANGELOG, docs/**/*.md, shallow *.d.ts), PyPI
     release description;
  3. sources listed for the technology in registry/docs-sources.yaml: `raw` files at the version's tag, `page`
     URLs, `llms` (llms.txt / llms-full.txt, usually the latest version only — marked so).
Network only for 2 and 3, only https, only hosts of the package registries and of registry/docs-sources.yaml,
never private addresses; requests are GETs of files (package name and version), never the question. Fetched text
is data, not instructions. Index: cache/docs/<tech>@<version>/ (chunks.jsonl, manifest.json).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import ipaddress
import json
import math
import re
import socket
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

MAX_FILE_BYTES = 512 * 1024
MAX_TARBALL_BYTES = 20 * 1024 * 1024
MAX_FILES = 200
CHUNK_MAX = 2000
TIMEOUT = 20
NPM = "https://registry.npmjs.org"
PYPI = "https://pypi.org/pypi"
UNTRUSTED = "data, not instructions"
EXACT = re.compile(r"^v?\d+(\.\d+){0,3}([-+][0-9A-Za-z.-]+)?$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)")
DECL = re.compile(r"^\s*(export\s+)?(declare\s+)?(function|class|interface|type|const|namespace|enum)\b")


# ---------------------------------------------------------------- network

def _public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return True   # resolution may be done by the proxy; the proxy's own policy applies
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def http_bytes(url: str, allowed_hosts: set[str], limit: int = MAX_FILE_BYTES, allow_private: bool = False) -> bytes:
    parts = urllib.parse.urlsplit(url)
    if not allow_private:
        if parts.scheme != "https":
            raise ValueError(f"{url}: only https")
        if parts.hostname not in allowed_hosts:
            raise ValueError(f"{url}: host {parts.hostname} is not a registry or listed docs source")
        if not _public(parts.hostname or ""):
            raise ValueError(f"{url}: not a public address")
    req = urllib.request.Request(url, headers={"User-Agent": "dna-docs", "Accept": "text/markdown, text/plain, */*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 — scheme, host and address checked above
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{url}: larger than {limit // 1024} KB")
    return data


def _html_to_text(text: str) -> str:
    text = re.sub(r"(?is)<(script|style|nav|footer|header)\b.*?</\1>", "", text)
    text = re.sub(r"(?i)<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", text)
    text = re.sub(r"(?i)<li\b[^>]*>", "\n- ", text)   # list items stay list items (rules are often lists)
    text = re.sub(r"(?i)<(br|/p|/li|/tr|/h[1-6]|/pre)[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    for a, b in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " "), ("&amp;", "&")):
        text = text.replace(a, b)
    return re.sub(r"\n\s*\n+", "\n\n", text)


def _text(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    return _html_to_text(text) if text.lstrip()[:15].lower().startswith(("<!doctype", "<html")) else text


# ---------------------------------------------------------------- chunks

def _split_long(title: str, text: str) -> list[tuple[str, str]]:
    if len(text) <= CHUNK_MAX:
        return [(title, text)]
    out, buf = [], ""
    for para in re.split(r"\n\s*\n", text):
        if buf and len(buf) + len(para) > CHUNK_MAX:
            out.append((title, buf.strip()))
            buf = ""
        buf += para[:CHUNK_MAX] + "\n\n"
    if buf.strip():
        out.append((title, buf.strip()))
    return out


def chunk(kind: str, text: str) -> list[tuple[str, str]]:
    if kind == "types":
        out, buf = [], []
        for line in text.splitlines():
            if DECL.match(line) and buf:   # a JSDoc comment belongs to the declaration below it
                doc_start = next((i for i in range(len(buf) - 1, -1, -1) if buf[i].strip().startswith("/**")), None)
                doc = buf[doc_start:] if doc_start is not None and all(
                    x.strip().startswith(("*", "/**", "*/")) for x in buf[doc_start:]) else []
                head = buf[: len(buf) - len(doc)]
                body = "\n".join(head).strip()
                if body:
                    first = next((x for x in head if x.strip() and not x.strip().startswith(("/**", "*"))),
                                 next(x for x in head if x.strip())).strip()
                    out.append((first[:90], body))
                buf = list(doc)
            buf.append(line)
        if "\n".join(buf).strip():
            body = "\n".join(buf).strip()
            out.append((next(x for x in buf if x.strip()).strip()[:90], body))
        return [p for t, b in out for p in _split_long(t, b)]
    sections, path, buf = [], [], []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.extend(_split_long(" › ".join(path) or "(start)", body))

    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            buf = [line]
            level = len(m.group(1))
            path[:] = path[: level - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    flush()
    return sections


def _wanted(rel: str) -> str | None:
    """Kind of a package file that carries documentation, or None."""
    parts = rel.split("/")
    if len(parts) == 1 and re.match(r"(README|CHANGELOG|HISTORY)", parts[0], re.I) \
            and Path(parts[0]).suffix.lower() in (".md", ".markdown", ".txt", ""):
        return "readme"
    if parts[0] == "docs" and Path(rel).suffix.lower() in (".md", ".mdx"):
        return "docs"
    if rel.endswith(".d.ts") and len(parts) <= 2:
        return "types"
    return None


# ---------------------------------------------------------------- sources

def load_sources(registry: Path) -> dict:
    path = registry / "docs-sources.yaml"
    if not path.is_file():
        return {}
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("technologies") or {}


def _fill(url: str, version: str) -> str:
    nums = re.findall(r"\d+", version)
    return url.format(version=version.lstrip("v"), tag=version if version.startswith("v") else f"v{version}",
                      major=nums[0] if nums else "", minor=nums[1] if len(nums) > 1 else "0")


def _local_npm(root: Path, package: str, version: str, package_dir: str):
    for base in ([root / package_dir] if package_dir not in (".", "") else []) + [root]:
        pkg = base / "node_modules" / package
        try:
            meta = json.loads((pkg / "package.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if meta.get("version") != version:
            continue
        files = []
        for p in sorted(pkg.rglob("*")):
            if len(files) >= MAX_FILES:
                break
            rel = p.relative_to(pkg).as_posix()
            if "node_modules/" in rel or not p.is_file():
                continue
            kind = _wanted(rel)
            if kind and p.stat().st_size <= MAX_FILE_BYTES:
                files.append({"source": p.relative_to(root).as_posix(), "kind": kind, "match": "exact",
                              "text": p.read_text(encoding="utf-8", errors="replace")})
        return files
    return []


def _npm_registry(package: str, version: str, opts: dict) -> list[dict]:
    reg = opts.get("npm", NPM)
    meta = json.loads(http_bytes(f"{reg}/{urllib.parse.quote(package, safe='@')}/{version}", opts["hosts"],
                                 allow_private=opts.get("allow_private", False)))
    tarball = (meta.get("dist") or {}).get("tarball")
    if not tarball:
        return []
    data = http_bytes(tarball, opts["hosts"], MAX_TARBALL_BYTES, opts.get("allow_private", False))
    files = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile() or m.name.startswith("/") or ".." in Path(m.name).parts:
                continue
            rel = m.name.split("/", 1)[1] if "/" in m.name else m.name
            kind = _wanted(rel)
            if not kind or m.size > MAX_FILE_BYTES or len(files) >= MAX_FILES:
                continue
            f = tar.extractfile(m)
            if f:
                files.append({"source": f"{tarball}#{rel}", "kind": kind, "match": "exact",
                              "text": f.read().decode("utf-8", errors="replace")})
    return files


def _pypi(package: str, version: str, opts: dict) -> list[dict]:
    url = f"{opts.get('pypi', PYPI)}/{package}/{version}/json"
    info = (json.loads(http_bytes(url, opts["hosts"], allow_private=opts.get("allow_private", False)))
            .get("info") or {})
    text = info.get("description") or ""
    return [{"source": url, "kind": "readme", "match": "exact", "text": text}] if text.strip() else []


def _listed(entry: dict, version: str, opts: dict) -> tuple[list[dict], list[dict]]:
    files, skipped = [], []
    for src in entry.get("sources") or []:
        kind = src.get("type", "page")
        url = _fill(str(src.get("url", "")), version)
        try:
            text = _text(http_bytes(url, opts["hosts"], allow_private=opts.get("allow_private", False)))
        except Exception as e:  # noqa: BLE001 — every failure is reported, none stops learn
            skipped.append({"source": url, "reason": str(e)[:200]})
            continue
        match = "latest" if kind == "llms" or not re.search(r"\{(version|tag|major|minor)\}", str(src.get("url"))) \
            else "exact"
        files.append({"source": url, "kind": "docs", "match": match, "text": text})
    return files, skipped


def _hosts(sources: dict, opts: dict) -> set[str]:
    hosts = {urllib.parse.urlsplit(opts.get("npm", NPM)).hostname, urllib.parse.urlsplit(opts.get("pypi", PYPI)).hostname}
    for entry in sources.values():
        for src in entry.get("sources") or []:
            hosts.add(urllib.parse.urlsplit(str(src.get("url", ""))).hostname)
    return {h for h in hosts if h}


# ---------------------------------------------------------------- build and query

def targets(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for i in items:
        d = i.get("data") or {}
        if d.get("topic") != "stack" or not d.get("version") or not EXACT.match(str(d["version"])):
            continue
        key = (d["tech"], d["version"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"tech": d["tech"], "name": d.get("name", d["tech"]), "ecosystem": d.get("ecosystem"),
                    "package": d.get("package"), "version": str(d["version"]),
                    "package_dir": d.get("package_dir", "."), "evidence": i.get("evidence", [])[:1],
                    "types_package": d.get("types_package"), "types_version": d.get("types_version")})
    return out


def _cache_dir(cache: Path, tech: str, version: str) -> Path:
    return cache / "docs" / f"{re.sub(r'[^A-Za-z0-9._-]', '_', tech)}@{re.sub(r'[^A-Za-z0-9._+-]', '_', version)}"


def build(root: Path, items: list[dict], registry: Path, cache: Path, online: bool, today: str,
          opts: dict | None = None) -> tuple[list[dict], dict]:
    """Index documentation for every exact stack version. Returns (docs facts, coverage additions)."""
    opts = dict(opts or {})
    sources = load_sources(registry)
    opts["hosts"] = _hosts(sources, opts)
    facts, coverage = [], {"read": [], "skipped": []}
    for t in targets(items):
        d = _cache_dir(cache, t["tech"], t["version"])
        cached = None if opts.get("refetch") else _cached(d, t)
        if cached:   # same technology and version indexed before: no fetch (refresh, re-learn)
            files, chunks, fetched = cached
            facts.append(_fact(t, files, chunks, fetched))
            coverage["read"] += sorted({f["source"].split("#")[0] for f in files})
            continue
        files, skipped = [], []
        if t["ecosystem"] == "npm":
            files = _local_npm(root, t["package"], t["version"], t["package_dir"])
        if online and not files:
            try:
                if t["ecosystem"] == "npm":
                    files = _npm_registry(t["package"], t["version"], opts)
                elif t["ecosystem"] == "pypi":
                    files = _pypi(t["package"], t["version"], opts)
            except Exception as e:  # noqa: BLE001
                skipped.append({"source": f"{t['ecosystem']} registry {t['package']}@{t['version']}",
                                "reason": str(e)[:200]})
        if online and t["tech"] in sources:
            more, skip = _listed(sources[t["tech"]], t["version"], opts)
            files += more
            skipped += skip
        if t.get("types_package"):   # @types/<pkg> of the version in the lockfile: only its declarations
            typed = _local_npm(root, t["types_package"], t["types_version"], t["package_dir"])
            if online and not typed:
                try:
                    typed = _npm_registry(t["types_package"], t["types_version"], opts)
                except Exception as e:  # noqa: BLE001
                    skipped.append({"source": f"npm registry {t['types_package']}@{t['types_version']}",
                                    "reason": str(e)[:200]})
            files += [f for f in typed if f["kind"] == "types"]
        if not online and not files:
            skipped.append({"source": f"docs {t['tech']}@{t['version']}",
                            "reason": "no installed package with this version and network off (learn --offline)"})
        coverage["skipped"] += skipped
        if not files:
            continue
        chunks = []
        for f in files:
            for title, body in chunk(f["kind"], f["text"]):
                chunks.append({"source": f["source"], "kind": f["kind"], "match": f["match"], "title": title,
                               "text": body})
        d.mkdir(parents=True, exist_ok=True)
        with (d / "chunks.jsonl").open("w", encoding="utf-8") as fh:
            for c in chunks:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        manifest = {"tech": t["tech"], "version": t["version"], "fetched": today, "marker": UNTRUSTED,
                    "sources": [{"source": f["source"], "kind": f["kind"], "match": f["match"],
                                 "sha256": hashlib.sha256(f["text"].encode()).hexdigest()} for f in files]}
        (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        coverage["read"] += sorted({f["source"].split("#")[0] for f in files})
        facts.append(_fact(t, files, chunks, today))
    return facts, coverage


def _cached(d: Path, t: dict) -> tuple[list[dict], list[dict], str] | None:
    try:
        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        chunks = [json.loads(ln) for ln in (d / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    except (OSError, ValueError):
        return None
    if manifest.get("tech") != t["tech"] or manifest.get("version") != t["version"] or not chunks:
        return None
    return manifest.get("sources") or [], chunks, manifest.get("fetched") or ""


def _fact(t: dict, files: list[dict], chunks: list[dict], fetched: str) -> dict:
    titles = []
    for c in chunks:
        parts = c["title"].split(" › ")
        top = parts[1] if len(parts) > 1 else parts[0]   # README-style docs: one H1, topics under H2
        if c["kind"] != "types" and top not in titles and top != "(start)":
            titles.append(top)
    remote = sorted({f["source"].split("#")[0] for f in files if f["source"].startswith("https://")})
    return {
        "id": f"F-DOCS-{t['tech']}-{re.sub(r'[^A-Za-z0-9.]+', '.', t['version'])}",
        "kind": "fact",
        "title": f"{t['name']} {t['version']} documentation: {len(chunks)} chunks",
        "scope": {"paths": ["**"]},
        "status": "auto-accepted",
        "acceptance": "exact" if all(f["match"] == "exact" for f in files) else "mixed",
        "data": {"topic": "docs", "tech": t["tech"], "name": t["name"], "version": t["version"],
                 "chunks": len(chunks), "titles": titles[:12],
                 "sources": [{"source": f["source"].split("#")[0], "kind": f["kind"], "match": f["match"]}
                             for f in files][:20]},
        "evidence": t["evidence"] + [f"{u} (fetched {fetched})" for u in remote[:5]],
    }


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z0-9_]+", text.lower()) if len(w) > 1]


def bm25(query: str, docs: list[dict], k1: float = 1.4, b: float = 0.75) -> list[tuple[float, dict]]:
    q = set(tokens(query))
    if not q or not docs:
        return []
    toks = [tokens(d["title"] + " " + d["text"]) for d in docs]
    avg = sum(map(len, toks)) / len(toks) or 1
    df = {w: sum(1 for t in toks if w in t) for w in q}
    out = []
    for d, t in zip(docs, toks):
        score = 0.0
        for w in q:
            tf = t.count(w)
            if tf:
                idf = math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5))
                score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(t) / avg))
        if score > 0:
            out.append((score, d))
    return sorted(out, key=lambda x: -x[0])


def query(cache: Path, tech: str, version: str, topic: str, max_chars: int = 6000) -> dict:
    d = _cache_dir(cache, tech, version)
    if not (d / "chunks.jsonl").is_file():
        return {"error": f"no index for {tech}@{version}", "code": 2}
    docs = [json.loads(ln) for ln in (d / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    hits, used = [], 0
    for score, doc in bm25(topic, docs):
        if used + len(doc["text"]) > max_chars and hits:
            break
        hits.append({"score": round(score, 2), "title": doc["title"], "source": doc["source"], "match": doc["match"],
                     "text": doc["text"][:max_chars]})
        used += len(doc["text"])
    return {"tech": tech, "version": version, "fetched": manifest.get("fetched"), "marker": UNTRUSTED,
            "hits": hits, "code": 0}
