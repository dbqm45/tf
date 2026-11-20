# Forms of delegation and what each costs

Read section 0 of SKILL.md first: the default is to do the work in the main session. This file compares the forms once
delegation is justified.

| Form | Starts with | Cache | Fits | Cost notes |
|---|---|---|---|---|
| Fork (`subagent_type: fork`, `/subtask`) | The whole current conversation | Shares the history's content, so every fork turn re-reads it | Checking a side hypothesis that needs everything you know | Cheap to brief, expensive per turn in a long session; whether it reuses the main session's cache entry is not established [unverified] - do not count on it when costing |
| New session in a worktree (`claude -w <name>`) | A clean context and its own branch | Its own | An independent change that gets its own review and PR | You isolate ports, databases and caches yourself; the brief must carry every agreement |
| Subagent (Agent tool) | Only your brief | Its own, 5-minute lifetime | Reading-heavy search, a mechanical change with a test, a fresh-eyes review | Can run a cheaper model via `model`; launch independent briefs together so each warms its cache once; optional worktree isolation |
| Agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | Several teammates, each with its own context | One per teammate | Large research, review or feature work with independent parts | Experimental, off by default, token use grows with each active teammate; keep teams small (3-5) and start one only with the human's consent - never a default |

## Rules that apply to all forms
- One coherent change stays with one executor.
- The brief starts with the `Class:` line, names the files, the check that decides done and what not to touch.
- Nesting: subagents may spawn their own up to `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` layers (default 3; 1 means no nesting).
  When further delegation is not needed, say so in the brief.
- The main session verifies the result (tests, diff) before accepting it; the executor's report is a claim.

## Example
Two independent changes and a security review of the auth module:
- change A and change B touch different modules with their own tests -> two subagents launched in one turn
  (`Class: parallel`), or two worktree sessions if each should become its own PR;
- the security review -> a subagent on a strong model with only the diff and the threat list (`Class: review`), so it does not
  inherit the author's reasoning;
- agent teams would add coordination cost for no gain here.

## Sources
- Claude Code docs, "Subagents", code.claude.com/docs/en/sub-agents - accessed 2026-11-20 (fork, depth limit, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`).
- Claude Code docs, "Agent teams", code.claude.com/docs/en/agent-teams - accessed 2026-11-20 (experimental, more tokens per teammate).
- Claude Code docs, "Prompt caching", code.claude.com/docs/en/prompt-caching - accessed 2026-11-20 (subagent cache lifetime).
