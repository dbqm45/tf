#!/usr/bin/env python3
"""Testy phase_progress.py: zamiana zdarzeń stream-JSON Claude Code na linie `run.progress`."""
import json
import sys
from pathlib import Path

REL_WORK = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "phase_progress.py"
REL_SRC = Path("modes") / "mode-pdi" / "skills" / "pdi-decisions" / "scripts" / "phase_progress.py"
ROOT = next((p for p in Path(__file__).resolve().parents
             if (p / REL_WORK).is_file() or (p / REL_SRC).is_file()), None)
SCRIPT = (ROOT / REL_WORK) if ROOT and (ROOT / REL_WORK).is_file() else ((ROOT / REL_SRC) if ROOT else None)

if SCRIPT is None:
    raise SystemExit("nie znaleziono phase_progress.py")
sys.path.insert(0, str(SCRIPT.parent))
import phase_progress as pp  # noqa: E402


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    def events(*ev: dict) -> list[dict]:
        return list(ev)

    # P-1: sukces — persona startuje, czyta plik, pisze plik, uruchamia polecenie, kończy wynikiem
    stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "claude-opus-4-7"},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "id": "u1",
             "input": {"file_path": "/Users/kamil/WebstormProjects/sklep/docs/project/changes/CHG-12/intent.md"}},
        ]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "u1", "content": [{"type": "text", "text": "..."}]},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Write", "id": "u2",
             "input": {"file_path": "/x/sklep/docs/project/changes/CHG-12/requirements.md"}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "id": "u3",
             "input": {"command": "python3 .claude/skills/pdi-decisions/scripts/decision_record.py check"}},
        ]}},
        {"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": 0.42,
         "result": {"type": "text", "text": "gotowe, czekam na bramkę B2"},
         "usage": {"input_tokens": 100, "output_tokens": 50},
         "duration_ms": 1234, "duration_api_ms": 1000, "num_turns": 5,
         "permission_denials": [], "session_id": "s"},
    )
    rows, final = pp.events_to_progress(stream, phase="requirements", change="CHG-12", budget_usd=3)
    check(len(rows) == 4,
          f"P-1: 4 linie postępu (init, Read, Write, Bash) — ma {len(rows)}")
    check(rows[0]["status"] == "started" and rows[0]["phase"] == "requirements"
          and rows[0]["change"] == "CHG-12" and rows[0]["budget_usd"] == 3,
          f"P-1: pierwsza linia started z phase/change/budget: {rows[0]}")
    check(rows[1]["status"] == "in_progress"
          and rows[1]["message"] == "czyta plik docs/project/changes/CHG-12/intent.md",
          f"P-1: Read → ścieżka względna od docs/project/changes/: {rows[1]}")
    check(rows[2]["message"] == "pisze plik docs/project/changes/CHG-12/requirements.md",
          f"P-1: Write → pisze plik z względną ścieżką: {rows[2]}")
    check(rows[3]["message"] == "uruchamia polecenie",
          f"P-1: Bash nigdy nie zdradza polecenia: {rows[3]}")
    check(isinstance(final, dict) and final.get("total_cost_usd") == 0.42,
          f"P-1: final result zachowany: {final}")

    # P-2: waiting_gate — emit_final po `result` ok dla fazy niebędącej delivery
    rel = pp.ProgressRelay(phase="requirements", change="CHG-12")
    for e in stream:
        rel.handle(e)
    waiting = rel.emit_final(status="waiting_gate", message="B2")
    check(waiting["status"] == "waiting_gate" and waiting["message"] == "B2"
          and waiting["cost_usd"] == 0.42,
          f"P-2: waiting_gate z kosztem z last_result: {waiting}")

    # P-3: failed — is_error=True → emit_final(status=failed)
    failed_stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "result", "subtype": "error_max_turns", "is_error": True, "total_cost_usd": 1.01,
         "result": {"type": "text", "text": "limit tur"}, "usage": {},
         "duration_ms": 1, "duration_api_ms": 1, "num_turns": 0,
         "permission_denials": [], "session_id": "s"},
    )
    rows, final = pp.events_to_progress(failed_stream, phase="delivery", change="CHG-12")
    check(len(rows) == 1 and rows[0]["status"] == "started",
          f"P-3: tylko linia started (żaden tool_use); ma {rows}")
    check(final and final["is_error"] and final["subtype"] == "error_max_turns",
          f"P-3: final result z is_error=True: {final}")

    # P-4: permission_denied w strumieniu → linia in_progress z „odmowa narzędzia …”
    denied_stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "system", "subtype": "permission_denied", "tool_use_id": "u1", "tool_name": "Write",
         "reason": "zapis poza zakresem fazy"},
        {"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": 0.1,
         "result": {"type": "text", "text": "ok"}, "usage": {},
         "duration_ms": 1, "duration_api_ms": 1, "num_turns": 0,
         "permission_denials": [{"tool_name": "Write", "tool_use_id": "u1", "reason": "zapis poza zakresem fazy"}],
         "session_id": "s"},
    )
    rows, final = pp.events_to_progress(denied_stream, phase="design", change="CHG-12")
    check(any(r.get("message", "").startswith("odmowa narzędzia Write") for r in rows),
          f"P-4: linia z odmową narzędzia: {rows}")

    # P-5: message nigdy nie wrzuca pełnego wejścia narzędzia
    secret_stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "id": "u1",
             "input": {"command": "export SECRET=abcDEF123; rm -rf /tmp/x\nprintf $SECRET"}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "id": "u2",
             "input": {"file_path": "/tmp/decoy", "old_string": "stary", "new_string": "nowy\n\x1b[31mSEKRET\x1b[0m"}},
        ]}},
    )
    rows, _ = pp.events_to_progress(secret_stream, phase="delivery")
    bash = next((r for r in rows if "polecenie" in r.get("message", "")), None)
    edit = next((r for r in rows if "pisze plik" in r.get("message", "")), None)
    check(bash and "SECRET" not in bash["message"] and "abcDEF123" not in bash["message"]
          and "rm -rf" not in bash["message"],
          f"P-5a: Bash nie zdradza polecenia ani sekretu: {bash}")
    check(edit and "stary" not in edit["message"] and "SEKRET" not in edit["message"]
          and "\x1b" not in edit["message"] and "\n" not in edit["message"]
          and len(edit["message"]) <= pp.MESSAGE_MAX,
          f"P-5b: Edit tylko ścieżka pliku, bez treści, bez znaków sterujących: {edit}")

    # P-6: nieznane wiersze są pomijane — krtuli ani wyjątku
    bad_stream = events(
        "nie-JSON",
        {"type": "foo"},
        {"type": "assistant"},
        {"type": "assistant", "message": None},
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": 0.0,
         "result": {"type": "text", "text": ""}, "usage": {},
         "duration_ms": 1, "duration_api_ms": 1, "num_turns": 0,
         "permission_denials": [], "session_id": "s"},
    )
    rows, final = pp.events_to_progress(bad_stream, phase="intent")
    check([r["status"] for r in rows] == ["started"],
          f"P-6: tylko started; ma {rows}")
    check(final is not None and not final["is_error"],
          f"P-6: result zachowany mimo szumu: {final}")

    # P-7: kształt linii (is_valid_progress)
    good = {"phase": "requirements", "status": "in_progress", "message": "czyta plik …", "cost_usd": 0.1}
    bad_status = {"phase": "requirements", "status": "oops"}
    bad_phase = {"phase": "", "status": "started"}
    bad_cost = {"phase": "requirements", "status": "started", "cost_usd": -0.1}
    bad_type = {"phase": "requirements", "status": "started", "message": 123}
    check(pp.is_valid_progress(good), "P-7a: dobra linia jest ok")
    check(not pp.is_valid_progress(bad_status), "P-7b: nieznany status odrzucony")
    check(not pp.is_valid_progress(bad_phase), "P-7c: pusta phase odrzucona")
    check(not pp.is_valid_progress(bad_cost), "P-7d: ujemny cost_usd odrzucony")
    check(not pp.is_valid_progress(bad_type), "P-7e: message złego typu odrzucony")

    # P-8: format_line — jeden wiersz z prefiksem
    row = {"phase": "design", "status": "in_progress", "message": "pisze plik x", "cost_usd": 0.2}
    line = pp.format_line(row)
    check(line.startswith(pp.PREFIX) and "\n" not in line,
          f"P-8: format_line ma prefiks i brak \\n: {line}")
    check(json.loads(line[len(pp.PREFIX):]) == row,
          f"P-8: JSON po prefiksie to ten sam słownik: {line}")

    # P-9: tylko pierwszy `system init` emituje started (duplikaty pomijane)
    double_init = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "system", "subtype": "init", "session_id": "s2", "model": "m"},
    )
    rows, _ = pp.events_to_progress(double_init, phase="intent")
    check(len(rows) == 1 and rows[0]["status"] == "started",
          f"P-9: drugi init pominięty: {rows}")

    # P-10: MCP → serwer/narzędzie
    mcp_stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "mcp__pdi__list_inbox", "id": "u1", "input": {}},
        ]}},
    )
    rows, _ = pp.events_to_progress(mcp_stream, phase="requirements")
    check(any(r.get("message") == "używa narzędzia pdi/list_inbox" for r in rows),
          f"P-10: MCP ładnie nazwane: {rows}")

    # P-11: tool_result z is_error=True → linia „błąd wyniku narzędzia”
    err_stream = events(
        {"type": "system", "subtype": "init", "session_id": "s", "model": "m"},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "u1", "content": [{"type": "text", "text": "fail"}],
             "is_error": True},
        ]}},
    )
    rows, _ = pp.events_to_progress(err_stream, phase="delivery")
    check(any(r.get("message") == "błąd wyniku narzędzia" for r in rows),
          f"P-11: błąd wyniku narzędzia: {rows}")

    # Podsumowanie
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów phase_progress")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
