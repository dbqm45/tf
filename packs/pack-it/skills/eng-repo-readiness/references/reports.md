# Readiness report templates

## A new project skeleton — `docs/project/06-delivery/bootstrap-verification.md`

```markdown
# Skeleton verification — <date>
**TL;DR:** <status: ok / failed / ok-with-remarks> · generator `<command>` (<version>, freshness: <fresh / ageing / outdated>)

| Step | Result |
|---|---|
| Stack decision | `docs/project/04-architecture/stack-decision.md` (accepted, <date>) |
| Generator command | `<full command>` — exit code <n> |
| Moved files | <count>; list in the appendix |
| Conflicts | `CLAUDE.md.scaffold`, `package.json.scaffold` — differences: <briefly> |
| `.gitignore` | merged: +<n> lines |
| Dependency audit | `<command>` — direct: <c/h/m/l>, transitive: <c/h/m/l> |
| Skeleton tests | `<command>` — <result> |
| Build | `<command>` — <result> |

## Next steps (the human's decisions)
- [ ] merge or reject the `.scaffold` files
- [ ] `git init` / first commit
- [ ] direct vulnerabilities: <action>; transitive: <we wait for the maintainer / overrides after a review>
```

Status `failed`: instead of the table of moved files — the command, the exit code, the last 20 lines of output, the path
`.bootstrap-scaffold/` left for inspection. No files added by hand.

## An audit of an existing repo — `docs/project/07-review/<date>-repo-readiness.md`

```markdown
# Repo readiness for agent work — <date>, commit <sha>
**TL;DR:** project <healthy / needs-attention / critical>, stack <ready / ready-with-compensation / high-friction>; fix no. 1: <…>

## Facts (readiness_check.py, detect_stack.py, commands run with consent)
| Area | Finding | Evidence |
|---|---|---|
| lockfile | … | `package-lock.json` |
| audit | direct 0, transitive 2 high | `npm audit --json` (<date>) |
| tests | runner: NONE | `package.json` without a `test` script |
| CI | lint ✓ test ✗ build ✓ types ✗ security ✗ | `.github/workflows/ci.yml` |
| configuration | `.gitignore` ✓, strict —, linter ✓, formatter ✗ | … |

## The four stack gates
| Component | Types | Conventions | Popularity in the family | Documentation | Evidence |
|---|---|---|---|---|---|
| API (Express 5) | ✗ | ✗ | ✓ | ✓ | no TS, routes in 3 different places |

### Compensations — rules for CLAUDE.md (ready to paste)
- Routes only in `src/routes/<resource>.js`, each exports `router`; registration in `src/app.js`.
- Errors: `next(err)`, one handler in `src/middleware/errors.js`; do not send a response from `catch`.

## Fixes (order of impact on the agent)
| # | What | Why for the agent | Command | Effort |
|---|---|---|---|---|
| 1 | test runner + smoke test | the agent has no way to check changes | `<command from the runner's documentation>` | medium |

## What was not checked
<e.g. the Java audit skipped — no built-in tool; the tests were not run, only listed>
```

Common rule: every number and assessment has evidence (a file or a command with a date); no evidence = "not checked".
