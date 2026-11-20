#!/usr/bin/env python3
"""
UserPromptSubmit hook: warns when the session context gets long — one cause of mistakes and fabrications.

It takes the context size from the last model response in the transcript (input + cache read and write). After
a threshold is crossed it appends a short instruction to the context: save a checkpoint and propose to the human
`/compact` with instructions, or a new session. Each threshold is reported once per session; when the context drops (e.g. after
compaction), the counter resets.

Thresholds in thousands of tokens: CLAUDE_CONTEXT_WARN_K (default 100) and 1.5 × the threshold (strong warning).
Disable: CLAUDE_CONTEXT_WARN_K=0. Standard library only; an error never blocks the command.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

TAIL_BYTES = 400_000   # the last model response is at the end of the transcript; we do not read the whole file


def context_tokens(transcript: Path) -> int:
    if not transcript.is_file():
        return 0
    size = transcript.stat().st_size
    with transcript.open("rb") as f:
        f.seek(max(0, size - TAIL_BYTES))
        lines = f.read().decode("utf-8", errors="ignore").splitlines()
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = (e.get("message") or {}).get("usage") if e.get("type") == "assistant" else None
        if u:
            return int((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                       + (u.get("cache_creation_input_tokens") or 0))
    return 0


def message(level: int, k: int) -> str:
    if level == 2:
        return (f"WARNING (context_guard): this session's context is about {k}k tokens — a lot. The risk of mistakes, "
                "forgetting earlier agreements and fabrication grows. Before doing anything else: write a checkpoint "
                "(core-project-record: steps, next action, agreements from the conversation) and propose to the user a new "
                "session from the checkpoint or `/compact` with an instruction on what to keep. State only facts checked "
                "right now (core-grounding), not from memory of the earlier part of the conversation.")
    return (f"context_guard: this session's context is about {k}k tokens. For longer work write a checkpoint "
            "and consider with the user `/compact` with an instruction or a new session; delegate exploring many files "
            "to subagents. Re-check important facts instead of relying on the earlier part of the conversation.")


def main() -> int:
    try:
        warn_k = int(os.environ.get("CLAUDE_CONTEXT_WARN_K", "100"))
    except ValueError:
        warn_k = 100
    if warn_k <= 0:
        return 0
    try:
        data = json.load(sys.stdin)
        tokens = context_tokens(Path(str(data.get("transcript_path") or "")).expanduser())
        if not tokens:
            return 0
        level = 2 if tokens >= warn_k * 1500 else 1 if tokens >= warn_k * 1000 else 0
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
        state_p = root / ".tf" / "logs" / "context-guard.json"
        state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
        session = str(data.get("session_id") or "?")
        last = int(state.get(session, 0))
        if level > last:
            print(message(level, tokens // 1000))
        if level != last:
            state[session] = level
            state = dict(list(state.items())[-200:])   # only the latest sessions
            state_p.parent.mkdir(parents=True, exist_ok=True)
            state_p.write_text(json.dumps(state), encoding="utf-8")
    except Exception as e:  # the hook does not interrupt the session; the error goes to the log
        record_error("context_guard", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
