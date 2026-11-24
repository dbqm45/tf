# shop

A tiny sample shop for the factory benchmark (`tools/bench.py`): Python standard library only.

- `app/components/button.py` — the shared button component every page renders its buttons with;
- `app/pages/` — page templates (one `render` function each);
- `app/pricing.py` — order totals in cents;
- `app/auth/permissions.py` — roles and what they may do.

Build and tests: `python3 run_tests.py` (all tests) or `python3 run_tests.py <changed files>` (the related tests).
