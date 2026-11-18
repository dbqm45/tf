"""Phase progress — converting Claude Code stream-JSON events into `run.progress` lines (pdi contract 0.11.0).

phase_run.py calls `claude --print --output-format stream-json --verbose` and streams the events of that
stream to stdout as lines with the prefix `PDI-PROGRESS: {json}` (one line = one dict). pdi on the
host side picks up these lines (dispatch_local) and saves them next to the log as `.progress.jsonl`.

Each progress line has `phase` and `status` (as in `run_progress`); optionally `change`, `cost_usd`,
`budget_usd`, `message`, `url`. The full tool input payload **never** goes into `message`
(prompt, file content, shell command, decisions, secrets) — only a short description such as "reads file <path>",
"runs a command", "uses tool <name>". Control characters other than tab are replaced with a
space; a line longer than 200 characters is truncated.

Source of the `stream-json` behavior and event shapes: code.claude.com/docs/en/cli-reference,
code.claude.com/docs/en/headless, code.claude.com/docs/en/agent-sdk/typescript (read 2026-11-06).
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

STATUSES = ("started", "in_progress", "waiting_gate", "done", "failed")
MESSAGE_MAX = 200
PREFIX = "PDI-PROGRESS: "

_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize(text: Any) -> str:
    """One row from `text`: without control characters and repeated spaces, trimmed to MESSAGE_MAX."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    cleaned = _CTRL.sub(" ", text)
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > MESSAGE_MAX:
        cleaned = cleaned[: MESSAGE_MAX - 1] + "…"
    return cleaned


def rel_path(path: Any) -> str:
    """File path for a message: relative to the product clone, without the host's absolute paths."""
    if not isinstance(path, str) or not path:
        return ""
    normalized = path.replace("\\", "/")
    marker = "docs/project/changes/"
    i = normalized.find(marker)
    if i >= 0:
        return normalized[i:]
    parts = [p for p in normalized.split("/") if p]
    if len(parts) > 2:
        return "…/" + "/".join(parts[-2:])
    return "/".join(parts)


def _mcp_pretty(name: str) -> str:
    """mcp__server__tool → server/tool; otherwise name."""
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}"
    return name


def tool_use_message(name: str, tool_input: Any) -> str:
    """A short description of a tool call without dumping the input (except a short file path)."""
    if not isinstance(tool_input, dict):
        tool_input = {}
    if name == "Read":
        return sanitize(f"reads file {rel_path(tool_input.get('file_path', ''))}")
    if name in ("Edit", "Write", "NotebookEdit"):
        return sanitize(f"writes file {rel_path(tool_input.get('file_path', ''))}")
    if name == "Bash":
        return "runs a command"
    if name == "Grep":
        path = tool_input.get("path") or ""
        return sanitize(f"searches for a pattern in {rel_path(path)}" if path else "searches for a pattern")
    if name == "Glob":
        return "searches for files"
    if name in ("WebFetch", "WebSearch"):
        return "fetches data from the web"
    if name == "Task":
        kind = tool_input.get("subagent_type") or ""
        return sanitize(f"starts agent {kind}" if kind else "starts an agent")
    if name == "TodoWrite":
        return "updates the task list"
    pretty = _mcp_pretty(name) if name else "unknown"
    return sanitize(f"uses tool {pretty}")


def result_text(result: Any) -> str:
    """The persona's response text from the final stream-JSON event — handles {type, text} and str."""
    if isinstance(result, dict):
        text = result.get("text")
        return text if isinstance(text, str) else ""
    if isinstance(result, str):
        return result
    return ""


class ProgressRelay:
    """Converting a stream of stream-JSON events into `run.progress` lines.

    - `handle(event)` returns the list of progress lines for one event (0, 1 or 2).
    - After the stream ends `last_result` holds the final `result` event (or None).
    - `emit_final(status=…)` gives a `done`/`failed`/`waiting_gate` line at the end, with `cost_usd` from `last_result`.
    """

    def __init__(
        self,
        *,
        phase: str,
        change: Optional[str] = None,
        budget_usd: Optional[float] = None,
    ) -> None:
        self.phase = phase
        self.change = change
        self.budget_usd = budget_usd
        self.last_result: Optional[dict] = None
        self._started = False

    def _base(self) -> dict:
        row: dict = {"phase": self.phase}
        if self.change:
            row["change"] = self.change
        if self.budget_usd is not None:
            row["budget_usd"] = self.budget_usd
        return row

    def _row(
        self,
        *,
        status: str,
        message: Optional[str] = None,
        cost_usd: Optional[float] = None,
    ) -> dict:
        row = self._base()
        row["status"] = status
        if message:
            row["message"] = sanitize(message)
        if cost_usd is not None:
            row["cost_usd"] = cost_usd
        return row

    def handle(self, event: Any) -> list[dict]:
        if not isinstance(event, dict):
            return []
        etype = event.get("type")
        if etype == "system":
            subtype = event.get("subtype")
            if subtype == "init" and not self._started:
                self._started = True
                return [self._row(status="started", message="persona starting")]
            if subtype == "permission_denied":
                tool = event.get("tool_name") or "?"
                reason = event.get("reason") or ""
                msg = f"tool denied {tool}" + (f": {reason}" if reason else "")
                return [self._row(status="in_progress", message=msg)]
            return []
        if etype == "assistant":
            message = event.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                return []
            rows: list[dict] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    rows.append(
                        self._row(
                            status="in_progress",
                            message=tool_use_message(block.get("name") or "", block.get("input")),
                        )
                    )
            return rows
        if etype == "user":
            message = event.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                return []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                    return [self._row(status="in_progress", message="tool result error")]
            return []
        if etype == "result":
            self.last_result = event
            return []
        return []

    def emit_final(self, *, status: str, message: Optional[str] = None) -> dict:
        """The final progress line (with the cost from `last_result`, when present)."""
        if status not in STATUSES:
            raise ValueError(f"status {status!r} is not one of {', '.join(STATUSES)}")
        cost: Optional[float] = None
        if isinstance(self.last_result, dict):
            raw = self.last_result.get("total_cost_usd")
            if isinstance(raw, (int, float)):
                cost = float(raw)
        return self._row(status=status, message=message, cost_usd=cost)


def events_to_progress(
    events: Iterable[Any],
    *,
    phase: str,
    change: Optional[str] = None,
    budget_usd: Optional[float] = None,
) -> tuple[list[dict], Optional[dict]]:
    """The whole stream → (list of progress lines, the final `result` event or None). A helper for tests."""
    relay = ProgressRelay(phase=phase, change=change, budget_usd=budget_usd)
    out: list[dict] = []
    for event in events:
        out.extend(relay.handle(event))
    return out, relay.last_result


def is_valid_progress(row: Any) -> bool:
    """Checks whether a dict has the shape of a `run.progress` line (without requiring the optional fields)."""
    if not isinstance(row, dict):
        return False
    if not isinstance(row.get("phase"), str) or not row["phase"]:
        return False
    if row.get("status") not in STATUSES:
        return False
    for key in ("cost_usd", "budget_usd"):
        value = row.get(key)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            return False
    for key in ("change", "task", "slice", "message", "url"):
        value = row.get(key)
        if value is not None and not isinstance(value, str):
            return False
    return True


def format_line(row: dict) -> str:
    """A progress line to print to the phase's stdout: `PDI-PROGRESS: {json}` on one line."""
    import json as _json

    return PREFIX + _json.dumps(row, ensure_ascii=False, separators=(",", ":"))
