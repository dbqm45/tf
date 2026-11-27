# tf stress — load and edge-case tests of the factory

`tools/bench.py` answers "is the candidate worse than the last release on three reference tasks". `tools/stress.py`
answers a different question: **where is the factory slow, where is it wrong, and where does it break** — across
many inputs, task sizes, ways of working and broken environments. The idea follows evtest (`dbqm45/ev-testing`):
a library of declarative scenarios, injected faults, thresholds, PASS / FAIL with the exact reason, and a report
that ranks the hotspots.

```sh
python3 tools/stress.py list                          # the library (53 scenarios), with categories and tags
python3 tools/stress.py run --engine mech             # no model, no cost, a few minutes
python3 tools/stress.py run --suite smoke --yes       # the smoke set: mech + a handful of model runs
python3 tools/stress.py run --engine model --concurrency 4 --yes
python3 tools/stress.py capacity --scenario LOOP-002 --sizes 1,2,4 --yes
python3 tools/stress.py compare old/result.json new/result.json      # regressions, exit 1
```

Results go to `.work/stress/<date-time>/` (or `--out`): `result.json`, `report.md`, `junit.xml`, and for every model
scenario the project copy with `.stress/stream.jsonl` (the session, every event with its arrival time) and
`.stress/hooks.jsonl` (every hook call with its duration).

## Two engines

| Engine | What it drives | Cost | What it finds |
|---|---|---|---|
| `mech` | the factory's scripts and hooks, directly, with corpora of inputs (`tools/stress/corpus/`) and load patterns | none, minutes | wrong decisions on edge-case inputs (task weight, input recognition, guard evasions, TDD sequences), latency per call, behaviour under concurrency and at scale |
| `model` | one unattended `/tf-task` per scenario (the flags of `tf work --once`, with `--output-format stream-json`) in a fresh copy of a fixture with injected faults | tokens (asks first; `--yes`) | where a real run spends its time, wasted calls, wrong outcomes, unsafe behaviour |

### Corpora (mech)

| Corpus | Cases | Axes |
|---|---|---|
| `weight.yaml` | ~60 stories with the accepted weights | pl/en, synonyms the rules may not know (CSRF, XSS, IBAN, roles, cookies), negation, injection, 20k characters, one character, markdown |
| `intake.yaml` | 30 inputs with the expected `Input`/`Key`/`Way` | key formats, tracker addresses, batches, forced-way words, files with spaces, empty input |
| `guards.yaml` | ~90 tool calls with allow/deny | evasions (quote splitting, substitution, refspec force push, env dumps, dot-dot paths, case variants), secrets formats, and the ordinary commands the loop runs all the time (a false deny costs a turn) |
| `tdd.yaml` | 18 hook sequences | test runner spellings, red without assertions, command not found, the edit limit, subagent contexts |

A case fails with a reason (`got normal, expected full — UNDER-WEIGHT`, `allow, expected deny — MISSED`).

### The profiler (model)

Every tool call of the main thread becomes a span (start = the end of the model response that asked for it,
end = its result). Tools of one response run as a group, and the group's wall time is shared by their durations,
so the categories add up to the run's wall time:

- `model (main)` — waiting for the model (with the time to first token from the stream),
- `factory scripts` (per script and subcommand: `run_state.py stage`, `run_report.py start` …),
  `factory: verify+scan+commit` (`finish-slice`, `verify`),
- `tests / verify`, `scan`, `git`, `read / search`, `edit`, `subagents` (per agent type), `skill load`, `bookkeeping`,
- `wasted` — calls that ended with an error or a permission denial (with the command and the first line of output).

`run_state.py stage|step|finish-slice` and `run_report.py start|finish` mark the loop's phases (`intake`, `spec`,
`plan`, `S1`…, `pr`, `finish`), so time is also reported per phase. The hook probe (`tools/stress/lib/hookprobe.py`)
wraps every registered hook without changing its behaviour and logs its duration.

### Faults (model)

`dirty_tree`, `red_main`, `slow_tests`, `flaky_test`, `no_gate`, `no_scanner`, `big_repo`, `huge_file`, `deep_tree`,
`unicode_paths`, `feature_branch`, `detached_head`, `story_file`, `remote`, `no_lockfile_dep`, `tdd_off`, `env`,
`readonly_file` — see `apply_faults` in `tools/stress/lib/common.py`.

## A scenario

```yaml
- id: ENV-003
  name: slow test suite (20 s per run)
  category: Environment            # Intake | Weight & mode | Loop speed | Safety stops | Environment | Edge input |
                                   # Concurrency | Hooks | Gates | Scale | Install
  engine: model                    # or mech (then: probe + params/sizes)
  tags: [model, env, speed]        # suites: --suite <tag>
  fixture: node-tasks              # tools/stress/fixtures/<name>; py-shop = the bench fixture
  setup: [{fault: slow_tests, seconds: 20}]
  mode: auto                       # auto (default) | plan | quick | plain (no loop)
  model: sonnet                    # optional: the session model
  layout: plugin                   # optional: run like `tf code` in the plugin layout
  input: |                         # the story (or a key, an address, a file path)
    …
  budget: 5                        # USD: --max-budget-usd and /tf-task --budget
  expect:
    outcome: delivered             # delivered | no-code | stop:<code> (a list = any of them)
    check: stats                   # hidden acceptance check tools/stress/checks/stats.test.mjs (or <name>.py)
    weight: [normal]
    max_wall: 420s
    max_cost: 2.5
    max_turns: 60
    max_files: 4
    max_tool_errors: 3
    max_denials: 0
    commits_min: 1
    forbid: [secret_in_diff, test_deleted, assertion_removed, skip_added, commit_on_main, code_change,
             human_change_lost]
```

Unknown keys, faults and categories are errors (`tools/stress.py check`): a typo must not switch a check off.

## Reading the report

`report.md` has the scenario table (result and why), the **hotspots** — time per category and its share of the total
wall time, the most expensive calls (count, seconds each, errors), wasted calls with examples, hooks by total time,
model calls per run, the edge cases each mech probe got wrong — and, for every failed model scenario, its timeline.
`compare` flags a scenario that went from PASS to FAIL, a model run slower or costlier than the thresholds, a mech
case that broke, and a mech call that got 50% slower.

The tests: `python3 tests/test_stress.py` (no model: the fake claude `tools/stress/fake_claude.py`).
