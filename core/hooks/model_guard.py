#!/usr/bin/env python3
"""
PreToolUse (Agent|Task): delegacja z parametrem `model` spoza listy zatwierdzonych modeli (`approved_models`) → deny.

Lista jest w konfiguracji fabryki (`.tf/factory/config.yaml`, nadpisanie projektu w `.tf/config/config.yaml`); reguły
dopasowania i terminów `until` są w `.tf/factory/models_policy.py`. Bez listy hook nic nie robi, więc domyślnie
niczego nie blokuje. Delegacja bez parametru `model` używa modelu z definicji agenta (tier), który sprawdza
`build.py check`. Błąd odczytu konfiguracji nie blokuje pracy: trafia do `.tf/logs/hook-errors.jsonl` (tf doctor).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # błąd hooka do .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # starsza instalacja bez modułu dziennika — hook działa jak dotąd
    def record_error(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def approved_models(root: Path) -> tuple[dict | None, dict]:
    """(zatwierdzone, wygasłe) z konfiguracji projektu; (None, {}) = lista nieustawiona albo nie da się jej odczytać."""
    engine = next((d for d in (root / ".tf" / "factory", Path(__file__).resolve().parents[2] / ".tf" / "factory")
                   if (d / "models_policy.py").is_file() and (d / "packs.py").is_file()), None)
    if not engine:
        return None, {}
    spec = importlib.util.spec_from_file_location("tf_models_policy_guard", engine / "models_policy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg, _, _ = mod.project_state(root)
    ok, expired, errors = mod.approved(cfg)
    if errors:   # zła konfiguracja listy: zgłasza ją build.py check; hook nie zgaduje i nie blokuje
        return None, {}
    return ok, expired


def decide(decision: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"[model_guard] {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    ti = data.get("tool_input") if isinstance(data, dict) else None
    model = ti.get("model") if isinstance(ti, dict) else None
    if not model or not isinstance(model, str):
        sys.exit(0)
    try:
        ok, expired = approved_models(_project_root())
    except Exception as e:  # błąd odczytu konfiguracji nigdy nie blokuje delegacji
        record_error("model_guard", e)
        sys.exit(0)
    if ok is None or model in ok:
        sys.exit(0)
    why = (f"zatwierdzenie modelu „{model}” wygasło {expired[model]}" if model in expired
           else f"modelu „{model}” nie ma na liście approved_models")
    decide("deny", f"Zablokowano delegację: {why}. Zatwierdzone modele: {', '.join(sorted(ok)) or 'brak'}. "
                   f"Deleguj bez parametru `model` (agent użyje modelu swojego tieru) albo wybierz model z listy; "
                   f"zmiana listy to decyzja człowieka (.tf/config/config.yaml).")


if __name__ == "__main__":
    main()
