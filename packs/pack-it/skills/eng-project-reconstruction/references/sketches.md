# CLAUDE.md and REVIEW.md drafts from the standards

Both files are proposals for a human to approve (`CLAUDE.draft.md`, `REVIEW.draft.md` in the report directory).
You take only standards with a share ≥ 70% and evidence; you leave the rest in the report as "mixed".

## CLAUDE.draft.md (under a page)
Only what the agent will not infer from the code, the README and the configuration (core-agent-instructions):
- build and test commands from the build files (`file:line`);
- 3–7 conventions that the tools do not enforce (e.g. domain exceptions instead of error codes);
- traps: legacy modules with a different style, places without tests, things invisible in the graph.

## REVIEW.draft.md
PR review rules (core-git-workflow, a reference to `REVIEW.md`):
- **Important** (blocks): a violation of a standard with a share ≥ 90% or of a business rule with a test;
- **Minor** (at most 5 per review): the other standards;
- **Exclusions:** generated code and the exclusions from `repo_inventory`, legacy directories indicated as exceptions.
Every rule with a link to `standards/<area>.md`.
