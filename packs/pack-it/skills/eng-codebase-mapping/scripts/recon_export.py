#!/usr/bin/env python3
"""
Export of a code reconstruction to JSON (for tools, e.g. ci_for_sdlc as the "current state"): the same content as `rules.md`,
`requirements.md` and `domain.md`, with `file:line` evidence split into fields, plus modules from the cards and the commit from the manifest.

  python3 recon_export.py docs/project/00-reconstruction [--repo DIR] [--out FILE]

An item = a bullet or a table row: `id` (kind + a digest of the content without evidence — stable when lines shift),
`text`, `section`, `module` (rules from a module section), `evidence` [{path, line, line_end[, verified]}], `quote`,
`confidence` (from "(confidence: …)"), `status` (evidence | assumption | unverified | question), `cells` (a table row:
header → value), `source` (file:line in the reconstruction directory). With `--repo` each evidence has `verified`: the file and lines
exist and the item's quote matches the code ±2 lines (like `recon_check.py`). Format: reconstruction-export.schema.json.

By default it writes `reconstruction.json` in the reconstruction directory. Exit code: 0 — written, 2 — no directory.
No network and no model; only the Python 3.9+ standard library.
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recon_check import MARK, QUOTE, REF, norm  # noqa: E402  (the same evidence format as the check)

SOURCES = (("rules", "rules.md"), ("requirements", "requirements.md"), ("domain", "domain.md"))
CONFIDENCE = re.compile(r"\(\s*confidence:?\s*([^)]+?)\s*\)", re.I)
STATUS = {"assumption": "assumption", "unverified": "unverified", "question": "question"}
MODULE_HEAD = re.compile(r"^(.+?)\s+\(details: modules/[^)]+\)$")


def refs(text: str) -> list:
    return [m for m in REF.finditer(text) if not re.match(r"https?$", m.group(1).split("/")[0])]


def clean(text: str) -> str:
    """Content without evidence, quotes, confidence and marks — what is left to read."""
    t = CONFIDENCE.sub("", text)
    for m in reversed(refs(t)):
        t = t[:m.start()] + t[m.end():]
    t = QUOTE.sub("", t)
    t = MARK.sub("", t)
    t = re.sub(r"\s*[—–-]\s*([,;]\s*)*$", "", t.strip())
    t = re.sub(r"(\s*,\s*)+$", "", t)
    return re.sub(r"\s{2,}", " ", t).strip(" —–;,")


class Verifier:
    def __init__(self, repo: str | None):
        self.repo, self.cache = repo, {}

    def __call__(self, path: str, a: int, b: int, quote: str | None) -> bool:
        if path not in self.cache:
            try:
                with open(os.path.join(self.repo, path), encoding="utf-8", errors="replace") as fh:
                    self.cache[path] = fh.read().splitlines()
            except OSError:
                self.cache[path] = None
        src = self.cache[path]
        if src is None or not (1 <= a <= b <= len(src)):
            return False
        if not quote:
            return True
        lo, hi = max(1, a - 2), min(len(src), b + 2)
        return norm(quote) in norm(" ".join(src[lo - 1:hi]))


def item(name: str, n: int, text: str, section: str, module: str | None, verify, cells=None) -> dict:
    found = refs(text)
    q = QUOTE.search(text[found[-1].end():] if found else text)
    quote = (q.group(1) or q.group(2)) if q and found else None
    evidence = []
    for m in found:
        a = int(m.group(2))
        e = {"path": m.group(1), "line": a, "line_end": int(m.group(3) or a)}
        if verify:
            e["verified"] = verify(e["path"], a, e["line_end"], quote)
        evidence.append(e)
    mark = MARK.search(text)
    status = STATUS.get(mark.group(1).lower(), "evidence") if mark else ("evidence" if evidence else "unverified")
    conf = CONFIDENCE.search(text)
    out = {"text": clean(text) if cells is None else " · ".join(v for k, v in cells.items() if v and not refs(v)),
           "section": section or None, "module": module, "evidence": evidence, "status": status,
           "source": f"{name}:{n}"}
    if quote:
        out["quote"] = quote
    if conf:
        out["confidence"] = conf.group(1)
    if cells is not None:
        out["cells"] = {k: clean(v) if refs(v) else v for k, v in cells.items()}
    return out


def parse(kind: str, name: str, lines: list[str], verify) -> list[dict]:
    out, section, module, head = [], "", None, None
    for n, line in enumerate(lines, 1):
        h = re.match(r"^#{2,6}\s+(.*)", line)
        if h:
            section = h.group(1).strip()
            mh = MODULE_HEAD.match(section)
            module = mh.group(1).strip() if mh and kind == "rules" else None
            section = mh.group(1).strip() if mh else section
            head = None
            continue
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            if head is None:
                head = cells
                continue
            row = {head[i] if i < len(head) else f"kolumna {i + 1}": c for i, c in enumerate(cells)}
            out.append(item(name, n, line, section, module, verify, cells=row))
            continue
        head = None
        b = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)", line)
        if b:
            out.append(item(name, n, b.group(1), section, module, verify))
    seen: dict[str, int] = {}
    for i in out:   # an identifier from the content and cells, without line numbers — stable under shifts
        basis = f"{name}\n{i['section']}\n{i['text']}\n{json.dumps(i.get('cells'), sort_keys=True, ensure_ascii=False)}"
        base = f"{kind}-{hashlib.sha1(basis.encode('utf-8')).hexdigest()[:10]}"
        seen[base] = seen.get(base, 0) + 1
        i["id"] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return out


def export(rec: str, repo: str | None) -> dict:
    verify = Verifier(repo) if repo else None
    data = {"format": "tf-reconstruction", "format_version": 1, "generated_at": datetime.date.today().isoformat(),
            "commit": None, "modules": []}
    try:
        with open(os.path.join(rec, "manifest.json"), encoding="utf-8") as fh:
            data["commit"] = json.load(fh).get("commit")   # as in the manifest (empty when the repo has no commits)
    except (OSError, ValueError):
        pass
    for card in sorted(glob.glob(os.path.join(rec, "modules", "*.json"))):
        try:
            with open(card, encoding="utf-8") as fh:
                c = json.load(fh)
        except (OSError, ValueError):
            continue
        stem = os.path.splitext(os.path.basename(card))[0]
        data["modules"].append({"module": c.get("module") or stem, "purpose": c.get("purpose") or None,
                                "card": f"modules/{stem}.json"})
    for kind, name in SOURCES:
        path = os.path.join(rec, name)
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError:
            lines = []
        data[kind] = parse(kind, name, lines, verify)
    return data


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    opts = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i] in ("--repo", "--out")}
    if not args or not os.path.isdir(args[0]):
        print(__doc__.strip() if not args else f"✗ no reconstruction directory: {args[0]}", file=sys.stderr)
        return 2
    rec = args[0]
    data = export(rec, opts.get("--repo"))
    out = opts.get("--out") or os.path.join(rec, "reconstruction.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    unv = sum(1 for k, _ in SOURCES for i in data[k] for e in i["evidence"] if e.get("verified") is False)
    print(f"✓ {out}: rules {len(data['rules'])}, requirements {len(data['requirements'])}, domain {len(data['domain'])}, "
          f"modules {len(data['modules'])}" + (f"; evidence that does not match the code: {unv} (recon_check.py)" if unv else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
