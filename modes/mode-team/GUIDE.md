# Agent teams (`mode-team`) — a team of agents on demand

A persona leads a team of 3–5 teammates (the factory's executors) who write to each other directly and take tasks from a
shared list. It is an experimental Claude Code feature and it is much more expensive than ordinary delegation to subagents,
so the mode is not installed by default, and you turn the flag on yourself.

## When
- **Fits:** roles must exchange findings and argue along the way — a review from several sides, debugging
  with competing hypotheses, a change across several layers with agreeing on a contract.
- **Does not fit:** tasks one after another, editing the same files, unattended work (`claude -p` does not create a team).
  Then the persona's subagents are enough.

## How
1. `tf add mode-team` — installs the mode.
2. `python3 .claude/skills/team-session/scripts/team_switch.py on` — the flag in `.claude/settings.local.json`
   (only for you); it works from the next session.
3. A new interactive session with a persona, e.g. `claude --agent kuba`, then `/team-session <task>`.
   The persona checks whether a team makes sense and asks about the composition and the cost limit.
4. After the session: `team_switch.py off`. With the flag on, a subagent named by Claude starts as a teammate
   even when nobody asked for a team.

## What to watch out for
- The cost grows with the number of teammates; you measure it with `python3 .tf/factory/cost_report.py --days 1`.
- Every file should have one owner — two teammates overwrite each other's changes.
- One team per session; `/resume` does not restore teammates.
- Teammates' permission questions appear in your session; add frequent commands to `allow` before the start.

Details of the run: `.claude/skills/team-session/SKILL.md`.
