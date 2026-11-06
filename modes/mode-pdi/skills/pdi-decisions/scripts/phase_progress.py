"""Postęp fazy — zamiana zdarzeń stream-JSON Claude Code na linie `run.progress` (kontrakt pdi 0.11.0).

phase_run.py wywołuje `claude --print --output-format stream-json --verbose` i strumieniuje zdarzenia tego
strumienia na stdout jako linie z prefiksem `PDI-PROGRESS: {json}` (jedna linia = jeden słownik). pdi po
stronie hosta łapie te linie (dispatch_local) i zapisuje obok logu jako `.progress.jsonl`.

Każda linia postępu ma `phase` i `status` (jak w `run_progress`); opcjonalnie `change`, `cost_usd`,
`budget_usd`, `message`, `url`. Do `message` **nigdy** nie trafia pełny wejściowy ładunek narzędzia
(prompt, treść pliku, polecenie powłoki, decyzje, sekrety) — tylko krótki opis typu „czyta plik <ścieżka>”,
„uruchamia polecenie”, „używa narzędzia <nazwa>”. Znaki sterujące poza tabulatorem są zamieniane na
spację; linia dłuższa niż 200 znaków jest obcinana.

Źródło zachowania `stream-json` i kształtu zdarzeń: code.claude.com/docs/en/cli-reference,
code.claude.com/docs/en/headless, code.claude.com/docs/en/agent-sdk/typescript (odczyt 2026-11-06).
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

STATUSES = ("started", "in_progress", "waiting_gate", "done", "failed")
MESSAGE_MAX = 200
PREFIX = "PDI-PROGRESS: "

_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize(text: Any) -> str:
    """Jeden wiersz z `text`: bez znaków sterujących i wielokrotnych spacji, przycięty do MESSAGE_MAX."""
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
    """Ścieżka pliku do wiadomości: względna od klonu produktu, bez ścieżek absolutnych hosta."""
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
    """mcp__serwer__narzędzie → serwer/narzędzie; inaczej name."""
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}"
    return name


def tool_use_message(name: str, tool_input: Any) -> str:
    """Krótki opis wywołania narzędzia bez wrzucania wejścia (poza krótką ścieżką pliku)."""
    if not isinstance(tool_input, dict):
        tool_input = {}
    if name == "Read":
        return sanitize(f"czyta plik {rel_path(tool_input.get('file_path', ''))}")
    if name in ("Edit", "Write", "NotebookEdit"):
        return sanitize(f"pisze plik {rel_path(tool_input.get('file_path', ''))}")
    if name == "Bash":
        return "uruchamia polecenie"
    if name == "Grep":
        path = tool_input.get("path") or ""
        return sanitize(f"szuka wzorca w {rel_path(path)}" if path else "szuka wzorca")
    if name == "Glob":
        return "szuka plików"
    if name in ("WebFetch", "WebSearch"):
        return "pobiera dane z sieci"
    if name == "Task":
        kind = tool_input.get("subagent_type") or ""
        return sanitize(f"uruchamia agenta {kind}" if kind else "uruchamia agenta")
    if name == "TodoWrite":
        return "aktualizuje listę zadań"
    pretty = _mcp_pretty(name) if name else "nieznane"
    return sanitize(f"używa narzędzia {pretty}")


def result_text(result: Any) -> str:
    """Tekst odpowiedzi persony z końcowego zdarzenia stream-JSON — obsługuje {type, text} i str."""
    if isinstance(result, dict):
        text = result.get("text")
        return text if isinstance(text, str) else ""
    if isinstance(result, str):
        return result
    return ""


class ProgressRelay:
    """Zamiana strumienia zdarzeń stream-JSON na linie `run.progress`.

    - `handle(event)` zwraca listę linii postępu dla jednego zdarzenia (0, 1 albo 2).
    - Po końcu strumienia `last_result` ma końcowe zdarzenie `result` (albo None).
    - `emit_final(status=…)` daje linię `done`/`failed`/`waiting_gate` na koniec, z `cost_usd` z `last_result`.
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
                return [self._row(status="started", message="persona startuje")]
            if subtype == "permission_denied":
                tool = event.get("tool_name") or "?"
                reason = event.get("reason") or ""
                msg = f"odmowa narzędzia {tool}" + (f": {reason}" if reason else "")
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
                    return [self._row(status="in_progress", message="błąd wyniku narzędzia")]
            return []
        if etype == "result":
            self.last_result = event
            return []
        return []

    def emit_final(self, *, status: str, message: Optional[str] = None) -> dict:
        """Końcowa linia postępu (z kosztem z `last_result`, gdy jest)."""
        if status not in STATUSES:
            raise ValueError(f"status {status!r} spoza {', '.join(STATUSES)}")
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
    """Cały strumień → (lista linii postępu, końcowy event `result` albo None). Pomocniczo w testach."""
    relay = ProgressRelay(phase=phase, change=change, budget_usd=budget_usd)
    out: list[dict] = []
    for event in events:
        out.extend(relay.handle(event))
    return out, relay.last_result


def is_valid_progress(row: Any) -> bool:
    """Sprawdza, czy słownik ma kształt linii `run.progress` (bez wymagania pól opcjonalnych)."""
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
    """Linia postępu do wypisania na stdout fazy: `PDI-PROGRESS: {json}` w jednej linii."""
    import json as _json

    return PREFIX + _json.dumps(row, ensure_ascii=False, separators=(",", ":"))
