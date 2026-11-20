#!/usr/bin/env python3
"""Hook SessionStart: refresh the project's add-ons (.tf/addons/) in the background, so their guidelines follow the
repository without a manual `tf learn`.

Runs `.tf/factory/addons.py refresh` detached: the session does not wait; the output goes to
.tf/logs/addons-refresh.log. An add-on whose inputs did not change does nothing (its own fingerprint). Without
add-ons the hook does nothing. Off switch: TF_ADDON_REFRESH=0. TF_ADDON_REFRESH_SYNC=1 runs it in the foreground
(tests). The hook never blocks the start of a session (exit 0, silent).
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # błąd hooka do .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:
    def record_error(hook: str, exc: BaseException) -> None:
        return None

os.environ.setdefault("PYTHONUTF8", "1")


def main() -> int:
    if os.environ.get("TF_ADDON_REFRESH") == "0":
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    engine = root / ".tf" / "factory" / "addons.py"
    if not engine.is_file() or not (root / ".tf" / "addons").is_dir():
        return 0
    logs = root / ".tf" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(engine), "refresh"]
    with (logs / "addons-refresh.log").open("a", encoding="utf-8") as log:
        if os.environ.get("TF_ADDON_REFRESH_SYNC") == "1":
            subprocess.run(cmd, cwd=root, stdout=log, stderr=log, stdin=subprocess.DEVNULL, timeout=600)
        else:
            kwargs = {"start_new_session": True} if os.name != "nt" else \
                {"creationflags": getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
            subprocess.Popen(cmd, cwd=root, stdout=log, stderr=log, stdin=subprocess.DEVNULL, **kwargs)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 — a hook never blocks the session
        record_error("addons_refresh", e)
        sys.exit(0)
