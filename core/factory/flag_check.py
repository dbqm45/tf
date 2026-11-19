#!/usr/bin/env python3
"""
Task feature-flag check (step D of the run axis): only a human changes a flag's state outside the test environment.

  tf flag check <KEY> [--base <branch>] [--json]

The task flag is recorded by `tf task flag <KEY> set <key> [--remove-by YYYY-MM-DD]`, its absence —
`tf task flag <KEY> none --reason "bez flagi, bo …"`, and a human's consent for another environment —
`tf task flag <KEY> allow <environment> --by human:<id>`.

How the script knows how flags work in the project: from the operations card `.tf/config/operations.json` (created by
`tf onboard`): {"flags": {"file": "config/flags.json", "envs": ["test", "prod"], "test_env": "test"}}.
A JSON file is supported (and YAML, when PyYAML is available) in the layout `environment → flag → state` or
`flag → environment → state`; the state is a boolean or an object with an `enabled` field. Comparison: the file in the base (git)
against the working file.

Rule FLAG-001: a task flag enabled on an environment other than the test one, which was not enabled in the base and for
which the task has no recorded human consent. With this error `tf task stage <KEY> pr` (and later stages) is refused.

When there is no card, it does not point to a file, the file has another format or the flags are controlled by another mechanism (environment variables,
a service), the script says plainly „sprawdź ręcznie” (check manually) and exits with code 0 — it does not pretend to run a check it cannot do.

Switch: `feature_flags.auto` in the configuration (`.tf/config/config.yaml`, default `true`). With `auto: false` a human
adds flags themselves — a task without a flag passes without an error, and a flag recorded in the task is checked as usual.

Exit code: 0 — compliant with the rule (or the check could not be run); 1 — FLAG-001 or a task with a specification
without a flag and without a reason; 2 — invocation error. Standard library only (PyYAML optional).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")

CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
BASES = ("main", "origin/main", "master", "origin/master")


def load_task(root: Path, key: str) -> dict | None:
    try:
        task = json.loads((root / CHANGES / key / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return task if isinstance(task, dict) else None


def card(root: Path) -> dict:
    try:
        data = json.loads((root / CARD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    flags = data.get("flags") if isinstance(data, dict) else None
    return flags if isinstance(flags, dict) else {}


def auto_flags(root: Path) -> bool:
    """`feature_flags.auto` from the configuration: the engine default (config.yaml next to the script) with the project override
    (.tf/config/config.yaml). When the configuration cannot be read — enabled, as by default."""
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_cfg", Path(__file__).resolve().with_name("packs.py"))
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        cfg = packs.load_yaml(Path(__file__).resolve().with_name("config.yaml"))
        own = root / ".tf" / "config" / "config.yaml"
        if own.is_file():
            cfg = packs.deep_merge(cfg, packs.load_yaml(own))
        return (cfg.get("feature_flags") or {}).get("auto", True) is not False
    except Exception:  # noqa: BLE001 — no configuration means the default setting, not a failure
        return True


def parse(text: str, name: str):
    """File content of the flags as a dict; None when the format cannot be read."""
    try:
        if name.lower().endswith((".yaml", ".yml")):
            try:
                import yaml
            except ImportError:
                vendor = Path(__file__).resolve().parent / "_vendor"
                if not vendor.is_dir():
                    return None
                sys.path.insert(0, str(vendor))
                import yaml
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception:  # noqa: BLE001 — an unreadable file means „sprawdź ręcznie” (check manually), not a failure
        return None
    return data if isinstance(data, dict) else None


def on(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
        return value["enabled"]
    return None


def states(data: dict | None, flag: str, envs: list[str]) -> dict[str, bool]:
    """Flag state on the card's environments, in both supported file layouts."""
    out: dict[str, bool] = {}
    if not data:
        return out
    for env in envs:
        by_env = data.get(env) if isinstance(data.get(env), dict) else {}
        by_flag = data.get(flag) if isinstance(data.get(flag), dict) else {}
        value = on(by_env.get(flag)) if flag in by_env else on(by_flag.get(env))
        if value is not None:
            out[env] = value
    return out


def git_show(root: Path, base: str | None, rel: str) -> str | None:
    """The file in the comparison base; None when there is no repository, base or file in the base."""
    for ref in ([base] if base else BASES):
        try:
            r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=root, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if r.returncode == 0:
            return r.stdout
    return None


def check(root: Path, key: str, base: str | None = None) -> dict:
    """Check result: `checked` (whether it could be run), `errors`, `note` (why not, or what was checked)."""
    task = load_task(root, key) or {}
    flag = task.get("flag") if isinstance(task.get("flag"), dict) else None
    has_spec = (root / CHANGES / key / "spec.md").is_file()
    auto = auto_flags(root)
    result = _check(root, key, base, flag, has_spec, auto)
    result["auto"] = auto
    return result


def _check(root: Path, key: str, base: str | None, flag: dict | None, has_spec: bool, auto: bool) -> dict:
    if flag is None:
        if not auto:
            return {"checked": False, "flag": None, "errors": [],
                    "note": "automatic flags are off (feature_flags.auto: false) — you add a flag yourself; "
                            "the factory does not create or require one"}
        if has_spec:
            return {"checked": True, "flag": None, "errors": [{
                "rule": "FLAG-000", "env": None,
                "message": f"the task has no flag and no reason for having none — tf task flag {key} set <key> or "
                           f"tf task flag {key} none --reason \"no flag because …\""}], "note": ""}
        return {"checked": False, "flag": None, "errors": [], "note": "a task without a specification needs no flag"}
    if flag.get("none"):
        return {"checked": True, "flag": None, "errors": [], "note": f"no flag: {flag['none']}"}
    name = flag.get("key")
    cfg = card(root)
    rel, envs, test_env = cfg.get("file"), cfg.get("envs") or [], cfg.get("test_env")
    manual = (f"flag {name}: the script cannot check its state on the environments — check by hand that it is off "
              "outside the test environment. ")
    if not rel or not envs or not test_env:
        return {"checked": False, "flag": name, "errors": [],
                "note": manual + f"Fill in the card {CARD.as_posix()} (flag file, environments, test environment)."}
    try:
        now = parse((root / rel).read_text(encoding="utf-8", errors="replace"), rel)
    except OSError:
        now = None
    if now is None:
        return {"checked": False, "flag": name, "errors": [],
                "note": manual + f"The file {rel} does not exist or has a format the script cannot read."}
    before_text = git_show(root, base, rel)
    before = states(parse(before_text, rel) if before_text else None, name, envs)
    current = states(now, name, envs)
    allowed = flag.get("allowed") or {}
    errors = []
    for env in envs:
        if env != test_env and current.get(env) is True and before.get(env) is not True and env not in allowed:
            errors.append({"rule": "FLAG-001", "env": env,
                           "message": f"flag {name} is on in the environment \"{env}\" without a human decision — turn it off there "
                                      f"or record the approval: tf task flag {key} allow {env} --by human:<id>"})
    summary = ", ".join(f"{env}: {'on' if current.get(env) else 'off'}" for env in envs)
    return {"checked": True, "flag": name, "errors": errors, "note": f"flag {name} in {rel} — {summary}"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf flag check", description="Check the feature flag of a task.")
    ap.add_argument("key")
    ap.add_argument("--base", default=None)
    ap.add_argument("--json", action="store_true")
    args = [a for a in argv[1:] if a != "check"] if argv[1:2] == ["check"] else argv[1:]
    try:
        a = ap.parse_args(args)
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        print(f"✗ the key \"{a.key}\" does not match the pattern (e.g. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    if load_task(root, a.key) is None:
        print(f"✗ there is no task {a.key} — create it: tf task start {a.key} --title \"…\"")
        return 2
    result = check(root, a.key, a.base)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 1 if result["errors"] else 0
    if result["note"]:
        print(("✓ " if result["checked"] and not result["errors"] else "⚠ " if not result["checked"] else "") + result["note"])
    for e in result["errors"]:
        print(f"✗ {e['rule']}  {e['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
