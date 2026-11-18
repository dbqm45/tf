#!/usr/bin/env python3
"""
Claude Code status line: model and effort, context fill, cache, session cost, limits — with no model tokens.

  Opus · high │ kontekst 42% 84k │ cache 91% │ $0.42 │ 5h 23%

Warns (⚠) when the context exceeds the CLAUDE_CONTEXT_WARN_K threshold (default 100k — the same as the
context_guard hook), when the cache is cold (the next turn will read the whole history without a discount) and when a limit is near.
It takes data from the JSON that Claude Code passes on input; missing fields are skipped. An error never interrupts work.
"""
from __future__ import annotations

import json
import os
import sys

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def fmt_k(n: float) -> str:
    return f"{n / 1000:.0f}k" if n >= 1000 else str(int(n))


def line(d: dict) -> str:
    parts = []
    model = (d.get("model") or {}).get("display_name") or (d.get("model") or {}).get("id") or "?"
    effort = (d.get("effort") or {}).get("level")
    agent = (d.get("agent") or {}).get("name")
    parts.append(" · ".join(x for x in (agent, model, effort) if x))

    cw = d.get("context_window") or {}
    cu = cw.get("current_usage") or {}
    used = sum((cu.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    pct = cw.get("used_percentage")
    if used or pct is not None:
        try:
            warn_k = int(os.environ.get("CLAUDE_CONTEXT_WARN_K", "100"))
        except ValueError:
            warn_k = 100
        mark = "⚠ " if warn_k > 0 and used >= warn_k * 1000 else ""
        parts.append(f"{mark}kontekst {pct if pct is not None else '?'}% {fmt_k(used)}".rstrip())

    pc = d.get("prompt_cache") or {}
    if pc.get("hit_ratio") is not None:
        cold = " zimny" if pc.get("warm") is False and pc.get("requests") else ""
        parts.append(f"cache {round(100 * pc['hit_ratio'])}%{cold}")
    elif cu.get("cache_read_input_tokens") is not None and used:
        parts.append(f"cache {round(100 * (cu.get('cache_read_input_tokens') or 0) / used)}%")

    cost = (d.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        parts.append(f"${cost:.2f}")

    rl = d.get("rate_limits") or {}
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        p = (rl.get(key) or {}).get("used_percentage")
        if p is not None and p >= 50:
            parts.append(f"{'⚠ ' if p >= 80 else ''}{label} {p:.0f}%")
    sl = rl.get("spend_limit") or {}
    if sl.get("used_percentage") is not None and sl["used_percentage"] >= 50:
        parts.append(f"{'⚠ ' if sl['used_percentage'] >= 80 else ''}spend limit {sl['used_percentage']:.0f}%")
    return " │ ".join(p for p in parts if p)


def main() -> int:
    try:
        print(line(json.load(sys.stdin)))
    except Exception:
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
