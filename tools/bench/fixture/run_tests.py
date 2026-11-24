#!/usr/bin/env python3
"""Build and tests of the shop: `python3 run_tests.py` runs every test; `python3 run_tests.py <files>` runs the tests
related to the changed files (a test file itself, or tests/test_<module>.py for app/**/<module>.py; anything else runs all)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def related(files: list[str]) -> list[str] | None:
    names = set()
    for f in files:
        p = Path(f)
        if p.parts and p.parts[0] == "tests" and p.name.startswith("test_") and p.suffix == ".py":
            names.add(p.stem)
        elif p.parts and p.parts[0] == "app" and p.suffix == ".py":
            test = "pages" if "pages" in p.parts else p.stem
            if not (ROOT / "tests" / f"test_{test}.py").is_file():
                return None
            names.add(f"test_{test}")
        else:
            return None
    return sorted(names)


def main(argv: list[str]) -> int:
    loader = unittest.TestLoader()
    names = related(argv) if argv else None
    suite = (loader.loadTestsFromNames([f"tests.{n}" for n in names]) if names
             else loader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT)))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
