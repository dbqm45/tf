#!/usr/bin/env python3
"""Windows portability of the engine and the core tests.

1. The engine (`core/factory/*.py`) compares and stores paths in the POSIX form: a path built with
   `str(x.relative_to(...))` has `\\` on Windows and differs from the same path written with `/` (that made
   `build.py check` report ".claude/agents/_generated are stale" with identical files).
2. Core tests do not require the right to create symbolic links: a plain Windows account without the developer mode
   gets WinError 1314 from `symlink_to`, so tests link through `link_or_copy`, which copies when linking fails.
python3 tests/test_windows_paths.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STR_RELATIVE = re.compile(r"\bstr\(\s*[\w.()\[\]]*\.relative_to\(")
SYMLINK = re.compile(r"\.symlink_to\(|\bos\.symlink\(")


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
    for msg in fails:
        print(f"✗ {msg}")
    print(f"{'✓' if not fails else '✗'} Windows paths and links: {len(fails)} problem(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
