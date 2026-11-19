---
name: {{PREFIX}}standards
description: Use for {{TITLE}} company rules — who approves, thresholds, bans and exceptions that apply at {{TITLE}}.
metadata:
  review: "{{REVIEW}}"
  catalog: "Use when the answer depends on {{TITLE}} rules rather than general practice — who at {{TITLE}} approves a change, thresholds and bans, exceptions, release windows, where {{TITLE}} keeps its decisions. Not for general practice (factory skills)."
  keywords: "TODO: the words people at the company use for these matters, e.g. names of systems, teams, processes"
---

# {{TITLE}} standards

This file is an index. The rules of each area are in a separate file: **load only the file of the area the task is
about** (a change to the page look alone → only `ui.md`; a new endpoint → `api.md`, and if it changes the schema, also
`data.md`). Rules a pattern can check (banned import, required header) are in `rules.yaml` of the
`{{COMPANY}}-standards` module and `tf analyze` checks them — do not repeat them in these files.

## Common to every change
- TODO: at most a few rules that always apply (e.g. the issue number in the PR description, who approves).

## Areas
| Area | When to read | File |
|---|---|---|
| UI | look, layout, components, screen texts and accessibility | `references/ui.md` |
| API | endpoints, contracts, errors, versions, call authorization | `references/api.md` |
| Data | database schema, migrations, personal data, retention | `references/data.md` |
| Releases | deployments, windows, release approval, rollback | `references/releases.md` |

TODO: remove an area the company does not have, together with its file; a new area is a new row and a file in
`references/`. Use a separate skill instead of a file only for a large area that people ask about in different words —
several similar skills compete for the same question.

## Where to look
- TODO: where the decisions and documentation are (e.g. a Confluence space) — a path or name, no passwords or tokens.
  Confluence is not read automatically; move the content that must take effect into the area files.

## Example
TODO: one real situation from the company and the correct outcome, e.g. "a PR adds a column to the orders table →
`data.md`: backward-compatible migration, approval by the data team".

## Sources
- TODO: the company document the rules come from and the date it was checked (YYYY-MM-DD).
