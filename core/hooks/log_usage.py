#!/usr/bin/env python3
"""
SubagentStop / SessionEnd: zapisuje zużycie tokenów per agent i model oraz użyte skille do .claude/logs/usage.jsonl.
PostToolUse narzędzia Agent (dawniej Task): wpis delegowania do .claude/logs/delegation.jsonl — wykonawca, model,
klasa zadania z linii „Klasa: …” briefu, długość briefu i raportu; agent_id łączy go z wpisem w usage.jsonl.
Raport: python3 factory/cost_report.py [--delegation]
"""
from __future__ import annotations

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

TIER_RE = re.compile(r"Tier:\**\s*za\s+(niski|wysoki)", re.I)
KLASA_RE = re.compile(r"^[\s*_`>#-]*Klasa\s*:[\s*_`]*([^\s—–,.;:*_`-]+)", re.I | re.M)
CLASSES = ("czytanie", "rownolegle", "przeglad", "mechaniczna", "decyzja", "inne")   # core-cost-control §0


def task_class(brief: str) -> str | None:
    """Klasa z linii „Klasa: …” briefu (bez diakrytyków, małymi literami); spoza listy → „inne”, brak linii → None."""
    m = KLASA_RE.search(brief[:2000])
    if not m:
        return None
    word = unicodedata.normalize("NFKD", m.group(1).lower().replace("ł", "l"))
    word = "".join(c for c in word if not unicodedata.combining(c))
    return word if word in CLASSES else "inne"


def text_len(value) -> int:
    """Długość tekstu raportu: string, lista bloków {type: text} albo słownik z `content`/`result`
    (w tle — status async_launched — raportu jeszcze nie ma: 0)."""
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
        "usage": resp_d.get("usage"),        # tylko pierwszy plan; w tle zużycie daje SubagentStop (agent_id)
        "duration_ms": resp_d.get("totalDurationMs"),
    }


def log_dir_for(data: dict) -> Path:
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR", data.get("cwd", "."))) / ".claude" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def usage_from_transcript(path: Path) -> dict:
    """Sumuje usage z transkryptu. Ta sama odpowiedź (message.id) bywa zapisana w kilku liniach
    podczas streamingu — bierzemy OSTATNI (pełny) zapis dla każdego id."""
    per_msg: dict[str, tuple[str, dict]] = {}
    skills: list[str] = []
    last_text = ""
    if path.is_file():
        with path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
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
                        m = re.search(r"\.claude/skills/([^/]+)/SKILL\.md$", str(inp.get("file_path", "")))
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
    m = TIER_RE.search(last_text[-2000:])     # samoocena wykonawcy z raportu: „Tier: za niski/za wysoki — powód”
    return {**totals, "models": models, "skills": list(dict.fromkeys(skills)),
            "tier_feedback": m.group(1).lower() if m else None}


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
    else:  # SessionEnd — główny wątek (persona uruchomiona przez --agent albo zwykła sesja)
        agent = data.get("agent_type") or "main"
        path = transcript
    if not path:
        sys.exit(0)

    usage = usage_from_transcript(Path(path).expanduser())
    if usage["requests"] == 0:
        sys.exit(0)
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
