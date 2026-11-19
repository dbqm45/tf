# A fork, a new session, a subagent or agent teams

First the rule from SKILL.md §0: by default the main session works, you delegate only when the handover pays off.
When it pays off, choose the cheapest form that gives the isolation you need:

| Form | When | Cost and limitations |
|---|---|---|
| **A fork** (`subagent_type: fork`; `/subtask` from v2.1.212) | a side task that needs the whole conversation so far (e.g. checking a hypothesis without cluttering the main thread) | it inherits the whole context, so each of its turns reads that history; only the result comes back to the session |
| **A new session with a worktree** (`claude -w <nazwa>`, `git worktree add`) | a separate change with its own branch and review, parallel work (core-git-workflow) | a clean start: it reads the files again, but does not pay for someone else's history; you isolate the environment (ports, database) yourself |
| **A subagent** (`Agent`, optionally `isolation: worktree`) | a lot of reading and a short result, a fresh look, a mechanical change with a test | it starts from zero, gets only the brief; a cheaper model through the `model` parameter; a 5-minute cache |
| **Agent teams** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | exceptionally: several roles that must talk to each other along the way | **experimental**; 3–5 members, many more tokens than subagents; you do not turn it on without the human's consent |

- **The nesting limit:** a subagent can launch further ones up to the depth `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
  (3 by default; 1 = no nesting). Each level is a separate start from zero — in the brief forbid further
  delegation when it is not needed.
- [unverified] whether a fork shares the cache with the main session and whether it can work in a worktree — do not assume it
  when estimating the cost.

Source: Anthropic, Claude Code documentation (code.claude.com/docs: "Subagents", "Agent teams", "Common workflows"
— worktree), accessed 2026-10-18. Described in our own words.
