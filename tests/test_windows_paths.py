#!/usr/bin/env python3
"""Windows portability of the engine and the core tests.

1. The engine (`core/factory/*.py`) compares and stores paths in the POSIX form: a path built with
   `str(x.relative_to(...))` has `\\` on Windows and differs from the same path written with `/` (that made
   `build.py check` report ".claude/agents/_generated are stale" with identical files).
2. Core tests do not require the right to create symbolic links: a plain Windows account without the developer mode
   gets WinError 1314 from `symlink_to`, so tests link through `link_or_copy`, which copies when linking fails.
3. No POSIX-only signal is read when a module loads (a default argument or a top-level line): Windows has no
   `signal.SIGKILL`, and `def kill_tree(…, sig=signal.SIGKILL)` in ui_snap.py made `import ui_snap` (and run_state.py) fail.
4. The scripts that write the task's and the project record's files (committed, checked by the project's lint) write
   LF: a text-mode `write_text` writes CRLF on Windows. Edits of the project's own files keep their line ending.
python3 tests/test_windows_paths.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STR_RELATIVE = re.compile(r"\bstr\(\s*[\w.()\[\]]*\.relative_to\(")
SYMLINK = re.compile(r"\.symlink_to\(|\bos\.symlink\(")
LF_WRITERS = ("core/skills/tf/scripts/run_report.py", "core/skills/tf/scripts/run_state.py", "core/factory/spec_check.py",
              "core/factory/task_state.py", "core/hooks/project_record.py", "core/factory/onboard.py")
POSIX_SIGNAL = re.compile(r"\bsignal\.SIG(?:KILL|HUP|PIPE|ALRM|USR1|USR2|CHLD|QUIT|STOP|CONT|TSTP)\b")


def main() -> int:
    fails = []
    for f in sorted((ROOT / "core" / "factory").glob("*.py")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if STR_RELATIVE.search(line):
                fails.append(f"{f.relative_to(ROOT).as_posix()}:{i}: str(….relative_to(…)) — use .as_posix()")
    for f in sorted((ROOT / "core" / "tests").glob("test_*.py")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if SYMLINK.search(line) and "def link_or_copy" not in line and "link-ok" not in line:
                fails.append(f"{f.relative_to(ROOT).as_posix()}:{i}: a symbolic link without a fallback — use link_or_copy "
                             "(or mark a test that needs a real link with `# link-ok` and skip it when linking fails)")
    for base in ("core", "packs", "modes", "addons"):
        for f in sorted((ROOT / base).rglob("*.py")):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                at_load = not line[:1].isspace() or re.match(r"\s*(async\s+)?def\s", line)
                if at_load and POSIX_SIGNAL.search(line):
                    fails.append(f"{f.relative_to(ROOT).as_posix()}:{i}: a POSIX-only signal read when the module loads "
                                 "(Windows has none) — read it inside the function, e.g. `sig or signal.SIGKILL`")
    for rel in LF_WRITERS:
        for i, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            if ".write_text(" in line:
                fails.append(f"{rel}:{i}: write_text writes CRLF on Windows — write_bytes(text.encode('utf-8'))")
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("tf_install_eol", ROOT / "core" / "factory" / "install.py")
    inst = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inst)
    with tempfile.TemporaryDirectory() as t:
        for name, before, after in (("lf.md", b"a\nb\n", b"a\nb\nc\n"), ("crlf.md", b"a\r\nb\r\n", b"a\r\nb\r\nc\r\n"),
                                    ("new.md", None, b"a\nb\nc\n")):
            p = Path(t) / name
            if before is not None:
                p.write_bytes(before)
            inst.write_keeping_eol(p, "a\nb\nc\n")
            if p.read_bytes() != after:
                fails.append(f"install.write_keeping_eol({name}): {p.read_bytes()!r}, expected {after!r}")
    for msg in fails:
        print(f"✗ {msg}")
    print(f"{'✓' if not fails else '✗'} Windows paths, links, signals and line endings: {len(fails)} problem(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
