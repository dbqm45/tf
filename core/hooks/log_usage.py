#!/usr/bin/env python3
"""
SubagentStop / SessionEnd: records token usage per agent and model, and the skills used, to .tf/logs/usage.jsonl.
Each entry has a harness fingerprint (`harness`): the Claude Code version from the transcript, the factory and overlay versions
from `.claude/factory-manifest.json`, and a digest of the checksums of installed files — results and costs can be
compared across versions (step H20).
PostToolUse of the Agent tool (formerly Task): a delegation entry to .tf/logs/delegation.jsonl — executor, model,
task class from the „Klasa: …” line of the brief, brief and report length; agent_id links it to the entry in usage.jsonl.
Report: python3 .tf/factory/cost_report.py [--delegation]
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

TIER_RE = re.compile(r"Tier:\**\s*(?:za\s+)?(niski|wysoki|too\s+low|too\s+high)", re.I)
TIER_EN = {"too low": "too low", "too high": "too high", "niski": "too low", "wysoki": "too high"}   # recorded in English; the former Polish signal too
KLASA_RE = re.compile(r"^[\s*_`>#-]*(?:Klasa|Class)\s*:[\s*_`]*([^\s—–,.;:*_`-]+)", re.I | re.M)
CLASSES = ("reading", "parallel", "review", "mechanical", "decision", "other",   # core-cost-control §0
           "addon")   # work an add-on left for the session (tf addon report counts it)
# A brief in Polish („Klasa: Przegląd”) — the same class; the log entry is always in English.
PL_CLASSES = {"czytanie": "reading", "rownolegle": "parallel", "przeglad": "review", "mechaniczna": "mechanical",
              "decyzja": "decision", "inne": "other"}


SKILL_READ_RE = re.compile(r"(?:\.claude|\.tf/plugin)/skills/([^/]+)/SKILL\.md$")   # also the factory plugin (factory mode)

def task_class(brief: str) -> str | None:
    """Class from the „Klasa: …” line of the brief (without diacritics, lowercase); outside the list → "other", no line → None."""
    m = KLASA_RE.search(brief[:2000])
    if not m:
        return None
    word = unicodedata.normalize("NFKD", m.group(1).lower().replace("ł", "l"))
    word = "".join(c for c in word if not unicodedata.combining(c))
    word = PL_CLASSES.get(word, word)
    return word if word in CLASSES else "other"


def text_len(value) -> int:
    """Length of the report text: a string, a list of {type: text} blocks, or a dict with `content`/`result`
    (in the background — status async_launched — there is no report yet: 0)."""
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(text_len(v.get("text", "")) if isinstance(v, dict) else text_len(v) for v in value)
    if isinstance(value, dict):
        return next((text_len(value[k]) for k in ("content", "result") if k in value), 0)
    return 0


def delegation_record(data: dict) -> dict:
    inp = data.get("tool_input") or {}
    resp = data.get("tool_response")
    resp_d = resp if isinstance(resp, dict) else {}
    brief = str(inp.get("prompt") or "")
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": data.get("session_id"),
        "tool": data.get("tool_name"),
        "agent": inp.get("subagent_type") or "general-purpose",
        "model": inp.get("model"),
        "resolved_model": resp_d.get("resolvedModel"),
        "klass": task_class(brief),
        "brief_chars": len(brief),
        "result_chars": text_len(resp),
        "agent_id": resp_d.get("agentId") or resp_d.get("agent_id"),
        "background": bool(inp.get("run_in_background")) or resp_d.get("status") == "async_launched",
        "usage": resp_d.get("usage"),        # foreground only; in the background usage comes from SubagentStop (agent_id)
        "duration_ms": resp_d.get("totalDurationMs"),
    }


def log_dir_for(data: dict) -> Path:
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR", data.get("cwd", "."))) / ".tf" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def usage_from_transcript(path: Path) -> dict:
    """Sums usage from the transcript. The same response (message.id) may be written on several lines
    during streaming — we take the LAST (complete) entry for each id."""
    per_msg: dict[str, tuple[str, dict]] = {}
    skills: list[str] = []
    last_text = ""
    version = None
    if path.is_file():
        with path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry.get("version"), str) and entry["version"].strip():
                    version = entry["version"].strip()[:40]
                msg = entry.get("message") or {}
                for c in (msg.get("content") or []) if entry.get("type") == "assistant" else []:
                    if isinstance(c, dict) and c.get("type") == "text" and c.get("text"):
                        last_text = c["text"]
                    if not isinstance(c, dict) or c.get("type") != "tool_use":
                        continue
                    inp = c.get("input") or {}
                    if c.get("name") == "Skill" and inp.get("skill"):
                        skills.append(str(inp["skill"]).split(":")[-1])
                    elif c.get("name") == "Read":
                        m = SKILL_READ_RE.search(str(inp.get("file_path", "")).replace("\\", "/"))
                        if m:
                            skills.append(m.group(1))
                usage = msg.get("usage")
                if entry.get("type") != "assistant" or not usage:
                    continue
                mid = msg.get("id") or entry.get("uuid")
                prev = per_msg.get(mid)
                if prev is None or (usage.get("output_tokens") or 0) >= (prev[1].get("output_tokens") or 0):
                    per_msg[mid] = (msg.get("model", "unknown"), usage)
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "requests": len(per_msg)}
    models: dict[str, int] = {}
    for model, u in per_msg.values():
        totals["input"] += u.get("input_tokens") or 0
        totals["output"] += u.get("output_tokens") or 0
        totals["cache_read"] += u.get("cache_read_input_tokens") or 0
        totals["cache_write"] += u.get("cache_creation_input_tokens") or 0
        models[model] = models.get(model, 0) + (u.get("output_tokens") or 0)
    m = TIER_RE.search(last_text[-2000:])     # the executor's self-assessment from the report: „Tier: too low/too high — reason”
    return {**totals, "models": models, "skills": list(dict.fromkeys(skills)),
            "tier_feedback": TIER_EN.get(" ".join(m.group(1).lower().split()), m.group(1).lower()) if m else None, "claude_code": version}


def harness(root: Path, claude_code: str | None) -> dict:
    """Harness fingerprint: the Claude Code, factory and overlay versions, and 12 characters of a SHA-256 over the file checksums
    from the install manifest. Without a manifest — only what can be determined."""
    out = {"claude_code": claude_code} if claude_code else {}
    try:
        man = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    if not isinstance(man, dict):
        return out
    if isinstance(man.get("version"), str):
        out["factory"] = man["version"][:40]
    if isinstance(man.get("packs"), dict):
        out["packs"] = {str(k)[:60]: str(v)[:40] for k, v in sorted(man["packs"].items())}
    if isinstance(man.get("files"), dict) and man["files"]:
        digest = hashlib.sha256(json.dumps(man["files"], sort_keys=True, ensure_ascii=False).encode("utf-8"))
        out["files"] = digest.hexdigest()[:12]
    return out


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    event = data.get("hook_event_name", "")
    transcript = data.get("transcript_path") or ""

    if event == "PostToolUse":
        if data.get("tool_name") in ("Agent", "Task"):
            with (log_dir_for(data) / "delegation.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(delegation_record(data), ensure_ascii=False) + "\n")
        sys.exit(0)
    if event == "SubagentStop":
        agent = data.get("agent_type") or "subagent"
        path = data.get("agent_transcript_path")
        if not path and transcript and data.get("agent_id"):
            path = str(Path(transcript).with_suffix("") / "subagents" / f"agent-{data['agent_id']}.jsonl")
    else:  # SessionEnd — the main thread (a persona started with --agent, or a regular session)
        agent = data.get("agent_type") or "main"
        path = transcript
    if not path:
        sys.exit(0)

    usage = usage_from_transcript(Path(path).expanduser())
    if usage["requests"] == 0:
        sys.exit(0)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", data.get("cwd", ".")))
    usage["harness"] = harness(root, usage.pop("claude_code", None))
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": data.get("session_id"),
        "event": event,
        "agent": agent,
        "effort": (data.get("effort") or {}).get("level"),
        **usage,
    }
    if event == "SubagentStop" and data.get("agent_id"):
        record["agent_id"] = data["agent_id"]
    with (log_dir_for(data) / "usage.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
