"""From candidates to decisions: merge duplicates, set strength and status by the rules of the plan (section 4.3).

- one decision per normalised text; its evidence and source kinds are merged;
- strength: hard when any source states it as hard (must, never, lint restriction…), otherwise soft;
- status `auto-accepted` when a source settles it (a standards skill, an accepted ADR, a lint rule) or when two
  independent sources (different files or pages) state it; otherwise `candidate` — listed, not applied;
- rank: the best (lowest) position in the hierarchy among its sources: standards 1, adr 2, lint 3, doc/tool-rules 4.
The rule "≥ 70% of code changed after `since` follows it" needs a per-decision code check and is not applied yet.
"""
from __future__ import annotations

from .sources import RANK, candidate_id, norm


def decide(candidates: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for c in candidates:
        groups.setdefault(norm(c["text"]), []).append(c)
    out = []
    for _key, cs in groups.items():
        kinds = sorted({c["kind"] for c in cs}, key=lambda k: RANK.get(k, 9))
        origins = {c["evidence"].rsplit(":", 1)[0] if not c["evidence"].startswith(("https://", "http://"))
                   else c["evidence"].split(" (")[0] for c in cs}
        settled = [k for k in kinds if k in ("standards", "lint")] or \
            (["adr"] if any(c["kind"] == "adr" and c.get("adr_accepted") for c in cs) else [])
        if settled:
            status, acceptance = "auto-accepted", f"source: {settled[0]}"
        elif len(origins) >= 2:
            status, acceptance = "auto-accepted", f"{len(origins)} independent sources"
        else:
            status, acceptance = "candidate", "one source"
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
                     "skills": sorted({c["skill"] for c in cs if c.get("skill")})},
            "evidence": list(dict.fromkeys(c["evidence"] for c in cs))[:6],
        })
    return sorted(out, key=lambda d: (d["data"]["rank"], d["strength"] != "hard", d["id"]))
