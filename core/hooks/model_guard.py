#!/usr/bin/env python3
"""
PreToolUse (Agent|Task): a delegation may name only an approved model.

Works only when the project, its team pack or its company pack sets `models_approved` (see
`.tf/factory/model_check.py`); without a list the hook ends at once. With a list, the `model` parameter of a delegation
that is not approved (by alias or by the identifier the alias points to in `models_current`, with `until` not past)
→ deny, with the approved models in the message. A delegation without `model` uses the agent's own tier, which
`model_check.py` checks (`tf doctor`, CI). The model of the session itself (`/model`) is outside this hook.

A configuration that cannot be read never blocks: the error goes to `.tf/logs/hook-errors.jsonl` and the delegation
passes — that is why this hook has no `onFailure: block`.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record, record_block
except ImportError:  # an install without the hook logs — the hook works as before
    def record(hook: str, exc: BaseException) -> None:
        return None

    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: the code page (cp1250) ≠ Claude Code's UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ENGINE = Path(".tf") / "factory" / "model_check.py"


def verdict(project: Path, model: str) -> tuple[bool, str, dict]:
    """(approved?, reason, the list) by the project's engine; (True, "", {}) when there is no engine."""
    path = next((c for c in (project / ENGINE, Path(__file__).resolve().parents[2] / ENGINE) if c.is_file()), None)
    if path is None:
        return True, "", {}
    spec = importlib.util.spec_from_file_location("tf_model_check_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    policy = mod.load_policy(project)
    ok, why = mod.approval(model, policy)
    return ok, why, policy


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    ti = data.get("tool_input") if isinstance(data, dict) else None
    model = ti.get("model") if isinstance(ti, dict) else None
    if not isinstance(model, str) or not model.strip() or model.strip() == "inherit":
        sys.exit(0)
    model = model.strip()
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) else None
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd())
    try:
        ok, why, policy = verdict(project, model)
    except Exception as e:  # noqa: BLE001 — a broken configuration does not block delegations
        record("model_guard", e)
        sys.exit(0)
    if ok:
        sys.exit(0)
    record_block("model_guard", "deny")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"[model_guard] Model {model} is not approved in this project ({why}). Approved "
                                    f"(models_approved, source: {policy.get('source')}): "
                                    f"{', '.join(policy.get('valid') or []) or 'nothing'}. Delegate with one of them or "
                                    "without the `model` parameter; the list is changed by its owner, not in the session.",
    }}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
