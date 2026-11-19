# Dependency audit — commands and reading the results

You run the audit in CI and at the start of work in a repo (eng-repo-readiness). The audit **reports**, it does not fix:
`npm audit fix` and its equivalents only with a human's consent, with a review of the lockfile diff.

| Family | Command (machine-readable output) | Notes |
|---|---|---|
| JS/TS (npm) | `npm audit --json` | an exit code ≠ 0 when there are findings is information, not a step failure; threshold: `--audit-level=high` |
| JS/TS (pnpm) | `pnpm audit --json` | |
| Python | `pip-audit --format json` (checked on 2.10.1) | no native severity → medium by default, unless the description says otherwise; for a project with a lockfile: `pip-audit --locked` |
| Rust | `cargo audit --json` | requires `cargo install cargo-audit` |
| Go | `govulncheck -json ./...` | reports only vulnerabilities reachable from the code — less noise |
| Ruby | `bundle audit check --update` | text output |
| PHP | `composer audit --format json` | since Composer 2.4 — check the version |
| .NET | `dotnet list package --vulnerable --include-transitive` | in a newer SDK also `dotnet package list --vulnerable` |
| Java, Dart | none built in — an external tool (e.g. OWASP Dependency-Check, OSV-Scanner) | without a tool record "skipped", **never "0 findings"** |

## Reading the results
- **Severity from CVSS:** ≥ 9.0 critical · 7.0–8.9 high · 4.0–6.9 medium · < 4.0 low. You show critical and high ones
  at once, the rest in the report.
- **Direct separately from transitive:** you fix direct ones at once (an update, a replacement); transitive ones
  wait for the maintainer's fix or a version override (`overrides` / `resolutions`) after a review. Mixing them
  at the start of a project leads to alert fatigue.
- Priority: reachability and known exploitation (SKILL.md, §5 — the KEV catalog), not the severity alone.
- You record the result with the date and the tool version; no tool or a network error = "not checked", not "clean".
