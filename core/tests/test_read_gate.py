#!/usr/bin/env python3
"""Tests of the read_gate hook (PreToolUse Read|Bash): reading a large file whole costs context, so the hook says so.
`read_gate.mode` (warn by default, deny, off) and `read_gate.max_lines` (350) in the factory configuration; a read with
offset/limit, a small file, a binary file and a configuration error always pass.
python3 .claude/tests/test_read_gate.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
HOOK = ROOT / ".claude" / "hooks" / "read_gate.py"


def project(base: Path, name: str, override: str | None = None) -> Path:
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    if override is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(override, encoding="utf-8")
    (p / "big.py").write_text("".join(f"x{i} = {i}\n" for i in range(400)), encoding="utf-8")
    (p / "small.py").write_text("".join(f"x{i} = {i}\n" for i in range(50)), encoding="utf-8")
    (p / "logo.png").write_bytes(b"\x89PNG\r\n" + b"\n" * 1000)
    return p


def hook(proj: Path, tool: str, tool_input) -> tuple[str, str]:
    """(decision, text): allow+context → ("warn", context), deny → ("deny", reason), nothing printed → ("none", "")."""
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": tool, "tool_input": tool_input,
                                                                       "cwd": str(proj)}),
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(proj)})
    if r.returncode != 0:
        return f"exit {r.returncode}", r.stderr[-300:]
    if not r.stdout.strip():
        return "none", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    if out.get("permissionDecision") == "deny":
        return "deny", out.get("permissionDecisionReason", "")
    return ("warn", out.get("additionalContext", "")) if out.get("additionalContext") else ("none", "")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    check(HOOK.is_file(), f"RG-0: the hook {HOOK.relative_to(ROOT)} is installed")
    if not HOOK.is_file():
        print(f"✗ {fails[0]}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "default")
        got, text = hook(p, "Read", {"file_path": str(p / "big.py")})
        check(got == "warn" and "400" in text and "offset" in text and "scout" in text,
              f"RG-1: a whole read of a 400-line file → allowed with a hint (lines, offset/limit, scout): {got} {text}")
        for why, ti in (("RG-2: a read with offset/limit passes", {"file_path": str(p / "big.py"), "offset": 100, "limit": 50}),
                        ("RG-3: a small file passes", {"file_path": str(p / "small.py")}),
                        ("RG-4: a binary file (an image) passes", {"file_path": str(p / "logo.png")}),
                        ("RG-5: a missing file passes (Read reports it)", {"file_path": str(p / "nope.py")})):
            got, _ = hook(p, "Read", ti)
            check(got == "none", f"{why}: {got}")
        got, text = hook(p, "Bash", {"command": "cat big.py"})
        check(got == "warn" and "big.py" in text, f"RG-6: `cat` of a large file in Bash → the same hint: {got} {text}")
        for cmd in ("head -n 40 big.py", "cat small.py", "cat big.py | grep x1", "git status"):
            got, _ = hook(p, "Bash", {"command": cmd})
            check(got == "none", f"RG-7: `{cmd}` passes: {got}")
        got, _ = hook(p, "Read", "not a mapping")
        check(got == "none", f"RG-8: input outside the format does not crash: {got}")

        p = project(base, "deny", "read_gate:\n  mode: deny\n")
        got, text = hook(p, "Read", {"file_path": str(p / "big.py")})
        check(got == "deny" and "offset" in text, f"RG-9: mode deny → a whole read of a large file is refused: {got} {text}")
        got, _ = hook(p, "Read", {"file_path": str(p / "big.py"), "limit": 100})
        check(got == "none", f"RG-10: mode deny still lets a read with a range through: {got}")

        p = project(base, "off", "read_gate:\n  mode: off\n")
        got, _ = hook(p, "Read", {"file_path": str(p / "big.py")})
        check(got == "none", f"RG-11: mode off → silence: {got}")

        p = project(base, "limit", "read_gate:\n  max_lines: 1000\n")
        got, _ = hook(p, "Read", {"file_path": str(p / "big.py")})
        check(got == "none", f"RG-12: max_lines from the project configuration: {got}")

        p = project(base, "broken", "read_gate: [not: a mapping\n")
        got, _ = hook(p, "Read", {"file_path": str(p / "big.py")})
        check(got in ("none", "warn"), f"RG-13: a broken configuration never blocks: {got}")

    sfile = next((f for f in (ROOT / ".claude" / "settings.json", ROOT / ".claude" / "settings.local.json") if f.is_file()), None)
    settings = json.loads(sfile.read_text(encoding="utf-8")) if sfile else {}
    pre = settings.get("hooks", {}).get("PreToolUse", [])
    check(any("read_gate.py" in json.dumps(e) and "Read" in e.get("matcher", "") and "Bash" in e.get("matcher", "")
              for e in pre), "RG-14: the hook is registered in settings.json for Read and Bash")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} read_gate tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
