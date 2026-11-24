"""From candidates to decisions: merge duplicates, set strength and status by the rules of the plan (section 4.3).

- one decision per normalised text; its evidence and source kinds are merged;
- strength: hard when any source states it as hard (must, never, lint restriction…), otherwise soft;
- status `auto-accepted` when a source settles it (a standards skill, an accepted ADR, a lint rule) or when two
  independent sources (different files or pages) state it and at least one of them is written (not inferred: PR
  review comments and code conventions are inferred by a model, so two pull requests or two example files alone stay
  a candidate); `accepted` when a human lists its id under `accept` in the configuration; otherwise `candidate` —
  listed, not applied;
- rank: the best (lowest) position in the hierarchy among its sources: standards 1, adr 2, lint 3, doc/tool-rules 4.
The rule "≥ 70% of code changed after `since` follows it" needs a per-decision code check and is not applied yet.
"""
from __future__ import annotations

from .sources import INFERRED, RANK, candidate_id, norm


def decide(candidates: list[dict], accept: set[str] | None = None) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for c in candidates:
        groups.setdefault(norm(c["text"]), []).append(c)
    out = []
    for _key, cs in groups.items():
        cs = sorted(cs, key=lambda c: c["kind"] in INFERRED)   # the written source's wording first
        kinds = sorted({c["kind"] for c in cs}, key=lambda k: RANK.get(k, 9))
        origins = {c["evidence"].rsplit(":", 1)[0] if not c["evidence"].startswith(("https://", "http://"))
                   else c["evidence"].split(" (")[0] for c in cs}
        settled = [k for k in kinds if k in ("standards", "lint")] or \
            (["adr"] if any(c["kind"] == "adr" and c.get("adr_accepted") for c in cs) else [])
        if settled:
            status, acceptance = "auto-accepted", f"source: {settled[0]}" + (
                " (cheap model, quote checked)" if all(c.get("extracted_by") == "model" for c in cs) else "")
        elif len(origins) >= 2 and any(c["kind"] not in INFERRED for c in cs):
            status, acceptance = "auto-accepted", f"{len(origins)} independent sources"
        elif candidate_id(cs[0]) in (accept or set()):
            status, acceptance = "accepted", "confirmed by a human (accept in the configuration)"
        else:
            status, acceptance = "candidate", "one source" if not all(c["kind"] in INFERRED for c in cs) else \
                "inferred only (" + ", ".join(sorted({c["kind"] for c in cs})) + "): needs a written source or accept"
        paths = sorted({p for c in cs for p in c["paths"]})
        if "**" in paths:
            paths = ["**"]
        best = cs[0]
        out.append({
            "id": candidate_id(best), "kind": "decision", "title": best["text"][:240],
            "scope": {"paths": paths}, "status": status, "acceptance": acceptance,
            "strength": "hard" if any(c["strength"] == "hard" for c in cs) else "soft",
            "data": {"topic": "decision", "sources": kinds, "rank": RANK.get(kinds[0], 9),
                     "rule_id": next((c["rule_id"] for c in cs if c.get("rule_id")), None),
                     "forbidden_import": next((c["forbidden_import"] for c in cs if c.get("forbidden_import")), None),
                     "quote": next((c["quote"] for c in cs if c.get("quote")), None),
                     "quotes": [{"text": c["quote"], "reviewer": c["reviewer"], "evidence": c["evidence"]}
                                for c in cs if c["kind"] == "review"][:4],
                     "extracted_by": "model" if all(c.get("extracted_by") == "model" for c in cs) else "pattern",
                     "skills": sorted({c["skill"] for c in cs if c.get("skill")})},
            "evidence": list(dict.fromkeys(c["evidence"] for c in cs))[:6],
        })
    return sorted(out, key=lambda d: (d["data"]["rank"], d["strength"] != "hard", d["id"]))
