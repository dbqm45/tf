# Security in the /tf loop: the version cooldown and the slice scan

You read this when `security_scan.py` returns FAIL or STOP and you need to understand the result. The script:
`python3 .claude/skills/tf/scripts/security_scan.py` (below `security_scan.py`).

## The version cooldown at the start (N10)
`security_scan.py cooldown` — FAIL when the package manager has no cooldown set: `min-release-age=7` (npm),
`minimumReleaseAge: 10080` (pnpm), `npmMinimalAgeGate` (Yarn), `exclude-newer` (uv), or the lockfile is outside git.
FAIL → STOP with the line to add from the output; you do not change the settings yourself. A new dependency younger than 7 days (the package
manager refuses to install it) → STOP with an explanation, not a workaround.

## The slice scan (after green tests)
`security_scan.py scan --slice S<n> --attempt <k> --out <katalog-przebiegu>/security/S<n>`:
- semgrep (OWASP Top 10 and the product's `.semgrep.yml`) on the slice's files; the dependency audit only when the manifest
  or the lockfile changes;
- SARIF, the verdict and the `summary.md` of each attempt in `security/S<n>/attempt-<k>/` — attempts do not overwrite each other, the report shows
  all of them;
- **blocking** (an error or a warning with a CWE from the OWASP Top 10, the rule SEC-001 from ci_for_sdlc) → the attempt FAILS: the findings
  (the rule, file:line) from `security/S<n>/feedback.md` (always from the last attempt) are the input of the next attempt;
- after 2 attempts the script prints a STOP block — you do not commit the slice, just as with a red test;
- a missing scanner is a FAIL with an installation command, not a silent PASS;
- findings below the threshold go to the run report (the "Security" section).

Variables: `TF_SCAN_PATH` (where to look for scanners instead of `PATH`), `TF_SEMGREP_CONFIG` (your own rule set). The semgrep state
(`SEMGREP_SETTINGS_FILE`, `SEMGREP_LOG_FILE`, `SEMGREP_VERSION_CACHE_PATH`) the script directs to `.tf/cache/semgrep/`,
because without a writable HOME semgrep ends with an error (PRB-32, reproduced 2026-11-05) — you do not add the variables
before the command.

## Sources
- OWASP Top 10 2021 and 2025, "List of Mapped CWEs" (github.com/OWASP/Top10, read 2026-11-02): the CWE list of the blocking
  threshold; a rule like SEC-001 in ci_for_sdlc (`--sarif`).
- semgrep 1.183.0 (the package code, read 2026-11-02): `--sarif --output`, `--metrics=off`, the rule registry from semgrep.dev
  (a host on the container's allowlist).
- npm 11.10.0 `min-release-age` (days), pnpm 10.17.0 `minimumReleaseAge` (minutes), uv `exclude-newer` (relative time)
  — details and gaps: the plan `docs/plans/2026-11-02-z8c-2-…`.
