---
name: ops-setup-wizard
description: Use when a human must set up keys in dashboards or CI secrets by hand — an interactive bash script.
metadata:
  review: "2027-04-17"
  catalog: "Use when a human must go through a procedure by hand that the agent cannot or should not perform — keys and accounts in the dashboards of external services, CI secrets, a one-time migration or switchover. The agent writes an interactive bash script (a wizard), the human runs it, the secrets bypass the model's context. Not for steps the agent will do itself, nor for architectural decisions."
---

# Setup wizard (a script for a human)

A wizard is a bash script that leads a human step by step: it opens the right page, says what to click and copy,
takes the value, saves it where needed (`.env`, a GitHub Actions secret or variable), asks for confirmation before
an irreversible step and shows progress. **The agent writes it, but never runs it** — the human types the keys, without echo,
so they do not reach the model's context (unless someone pastes them into the conversation — warn against that).

Template: `scripts/wizard.template.sh` (progress with a time estimate, confirmations, opening a URL also in WSL, hidden input of
secrets, an idempotent write to `.env` with permissions 600, `gh secret`/`gh variable` through stdin, a summary with a list of things
to do by hand). You leave the library above the `### ETAPY ###` marker unchanged — you write only the stages.

## Procedure
1. **The scope from the repository, not from questions.** Read `.env.example`, the key names in `.env*` (without values — a standing
   rule), `docker-compose*`, the framework configuration, `.github/workflows/*` (every `secrets.X` and `vars.X` is a value the
   wizard must produce). For a migration: the current state, the target state and the irreversible steps between them.
2. **A list of stages for approval** — in dependency order. For each value: where the human will get it, where it will go,
   whether it is secret:
   | Who needs it | Target |
   |---|---|
   | local development only | `.env` |
   | CI, a secret value | a GitHub secret |
   | CI, a public value | a GitHub variable |
   | development and CI | `.env` + a secret |
   | nothing (just an action: a toggle, a plan change) | nowhere |
   The human may add, remove or reorder stages.
3. **The path in every stage**: the URL and the exact route ("Dashboard → Developers → API keys → Reveal → copy"). You do not know
   the current look of the dashboard or the command → check the documentation (`researcher`) or ask; **do not invent steps**.
4. **Write the wizard**: copy the template to `scripts/` (one-time) or to the place the human indicates. One stage =
   one action that fits on the screen. First `open_url`, then `ask`/`ask_secret`; `ask_secret` for everything
   secret; `write_env` for every saved value; `set_secret` only for what CI really uses; `confirm`
   before every irreversible step. Set `TOTAL_STAGES`.
5. **Check statically**: `bash -n`, `shellcheck` (if available), `chmod +x`. Trace: every value from step 2 is
   collected and goes where it should; every name in `set_secret` matches `secrets.*` in the workflow. You do not run it
   (it opens a browser and waits for the human).
6. **Hand over**: how to run it; `.env` is in `.gitignore`. A one-time wizard is deleted after use; a repeatable one (onboarding
   a new person) — a commit and a link in the README, instead of instructions to copy and paste.

## Security rules
- A hook blocks the agent from reading `.env*` anyway; the wizard does not print secrets to the screen or to logs.
- Values for `gh` go through stdin, not in arguments (arguments are visible in the process list).
- No `curl | sh` and no downloading of scripts in the wizard; you describe installing tools as a manual step. <!-- audit-ok: describes an attack, not a command -->
- The wizard knows only the state of the repository, not the state of the external service: a stage that may already be done (an account, a key)
  asks "do you already have it?" and allows skipping; the summary lists the skipped things and those to do by hand.
- A rerun fills in the saved values as defaults; there is no "undo" — interrupt (Ctrl-C) and run it again.

## Source
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT), the `wizard` skill; description:
[aihero.dev](https://www.aihero.dev/skills-wizard). The procedure described in our own words, the template written from scratch.
