# The visual check: screenshots before and after a UI change

You read this only when `ui_snap.py worth <katalog> --base <gałąź domyślna>` printed `visual check: yes`. For a backend task
(no UI files, a trivial UI touch, `--no-visual`) it prints `no` and the visual check does not exist: no screenshots, no
section in the PR, nothing to write. `--visual` / `--no-visual` in the human's message win; record them with
`run_state.py stage <katalog> intake --visual` (or `--no-visual`). The thresholds are in `visual_check:` of
`.tf/config/config.yaml` (defaults in `.tf/factory/config.yaml`).

## Before the first code slice
`python3 .claude/skills/tf/scripts/ui_snap.py capture <katalog> --label before --start --route /login --route /`
- The routes are the screens the acceptance criteria concern (not the whole application). Without `--route` the card's
  `preview.routes` are used (`.tf/config/operations.json`), else `/`.
- `--viewport 1280x800,390x844` adds a phone width; add it when a criterion is about a responsive layout. The default is one
  desktop size (every screenshot costs reading time).
- `--start` starts the dev server (`preview.start` of the card, or the `dev`/`start`/`serve` script of package.json),
  waits until it answers and stops it after the shots; a server that already answers is left alone. Only `localhost`,
  `127.0.0.1` and `[::1]` are opened.
- Exit code 3 (no browser, or the server did not start): do not retry in a loop. Write `screens/check.md` with one line
  `Skipped: <reason>` (the script's message in one sentence) and go on; the PR says "skipped". Never a silent pass.
  The script installs nothing; without Chromium/Chrome/Edge the human can set `CTF_BROWSER`.

## After the last slice
1. `ui_snap.py capture <katalog> --label after --start` with the same routes and viewports.
2. `ui_snap.py compare <katalog>` writes `screens/compare.md`: per route and viewport `identical`, `changed`, `only before`
   or `only after`, with the file paths.
3. **Look.** Open with Read every `changed` pair (and every `only after`); `identical` ones need no look. Compare what
   you see with the acceptance criteria that have a visible effect. A pair that changed but no criterion explains is a
   finding: `park` it or revert it (scope).
4. Write `screens/check.md`, one line per criterion with a visible effect:
   `- AC-1 · /login @1280x800 — the error text is red under the field — **matches**`
   (`**does not match**` when it differs; always the route and the viewport, they link the line to the screenshot).
   Several pictures: look at them yourself; delegating to a cheaper subagent is for many screenshots only when you
   give it the criteria and ask for a verdict per screen, and then you still open every `does not match`.

## A mismatch
`**does not match**` is a red result: back to the slice that owns the criterion (the repair rules and the STOP block of
SKILL.md apply: at most 2 attempts), then capture `after` again and `compare`. The PR description never hides it.

## Where things are
The screenshots stay in `<katalog>/screens/` (outside git): `before/`, `after/` (`<route>@<W>x<H>.png`, `index.json` with
the sha256 and the PNG size), `compare.md`, `check.md`. `run_state.py pr-body` turns them into the `## Visual check`
section (counts, the path, mismatches) and the dashboard shows the pairs side by side.
