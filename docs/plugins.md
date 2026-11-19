# Overlays and modes as Claude Code plugins: analysis

Status: 2026-10-21. Facts about plugins come from the code.claude.com documentation (read on 2026-10-21, pages
`/en/plugins/*`, `/en/sub-agents`, `/en/skills`, `/en/hooks`, `/en/plugin-evals`). What the documentation does not say
I mark [unverified]. This document supports a human decision; there is no code yet.

**Human decision (2026-10-21): we are not building a plugin export.** The factory is installed by `tf` as before. The
analysis stays as the rationale for the decision.

## Conclusion
- **Overlays: not as a whole, for now.** Personas and roles are built in the project from the core and all overlays at
  once (`build.py`). A plugin is static files, so that assembly would fall apart. What is feasible is exporting just an
  overlay's skills (a "skill library"), with the limitations described below.
- **The core: no.** A plugin does not ship `CLAUDE.md`, rules or permissions, and the core is largely made of them.
- **There stays one source.** A plugin would be an artifact built from `modes/` and `packs/` by a tool in `tools/`, not a
  second copy to maintain. The `tf` installer remains the primary way to install.

## What a plugin can and cannot do (facts)
| Area | Plugin | Source |
|---|---|---|
| Components | `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `bin/` (on the Bash `PATH`), `settings.json`, `output-styles/`, `workflows/`, manifest `.claude-plugin/plugin.json` (only `name` is required) | `/en/plugins/manifest-reference` |
| Agents | ignored fields: `permissionMode`, `hooks`, `mcpServers`, `initialPrompt`; these work, among others: `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `omitClaudeMd`, `isolation` | `/en/plugins/components#agents` |
| Main session agent | `claude --agent <name>` finds the agent from the plugin by name alone (`<plugin>:<name>` on a collision); the plugin's `settings.json` can set `agent` | `/en/sub-agents`, `/en/plugins/components#default-settings` |
| Settings | only `agent` and `subagentStatusLine` work, the rest (including `permissions`) is rejected | `/en/plugins/components#default-settings` |
| Permission for a script | a skill can approve its own script: `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/… *)` | `/en/skills` |
| `CLAUDE.md` | `CLAUDE.md` in a plugin is not loaded; instructions only through a skill | `/en/plugins/manifest-reference` |
| Hooks | `hooks/hooks.json` in the shape of `hooks` from `settings.json`; registered when the plugin loads, they block like any other (exit 2, `onFailure: "block"`); they get `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` | `/en/plugins/components#hooks`, `/en/hooks` |
| Files | installation copies the plugin to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`; files outside the plugin directory (`../shared`) are not copied; persistent state in `${CLAUDE_PLUGIN_DATA}` | `/en/plugins/loading` |
| Names | everything under the `<plugin>:` namespace; a skill also as `/<name>` if there is no collision; names starting with `claude-`, `anthropic-`, `cc-plugin-` are a validation error | `/en/plugins/manifest-reference`, `/en/skills` |
| Dependencies and versions | `dependencies` with a SemVer range (`^2.0`, `>=1.4`), resolved by git tags `<plugin>--v<version>` (`claude plugin tag --push`) | `/en/plugins/dependencies` |
| Team | `extraKnownMarketplaces` and `enabledPlugins` in the repository's `.claude/settings.json`; works only in a trusted folder; a plugin from an external source is installed by each person (`claude plugin install … --scope project`) | `/en/plugins/org` |
| Cloud sessions | do not load plugins installed locally or enabled in the repository's `.claude/settings.json` | `/en/plugins/install` |
| Validation | `claude plugin validate <directory> --strict` (no model); `claude plugin eval`: paid model calls | `/en/plugins/cli-reference`, `/en/plugin-evals` |

## What we lose, element by element
### Overlays (`pack-*`)
- **Personas and roles:** in a project they are built from the roles, facets, working agreement, report contract,
  consultant table and routing of all installed overlays, in the project's working language. A plugin could carry only
  one frozen assembly (e.g. core + this overlay, language `pl`). That is exactly what `build.py` avoids.
- **Skills:** they transfer well (a plain `SKILL.md` with `references/`, `scripts/`). We lose:
  - skill visibility by the project's stack (`skillOverrides`, `detect_stack.py`);
  - `skill_hint` hook suggestions;
  - the quality gate and the versioned registry;
  - references to skills of other overlays, checked today by `workspace.py refs`.
- **Context cost:** the description of every skill from a plugin is in context on every turn, and `pack-it` has 142
  skills. The factory limits this with visibility by stack; a plugin does not.

### The core
- The section in `CLAUDE.md`, permissions, `onFailure` on hooks in the project settings, `factory/` (build,
  installation, update, migrations), the `docs/project/` journal: a plugin has no place for them.
- The hooks alone could be moved, but some read the project's configuration (`cleanroom.json`, settings), and a plugin
  enabled for a user works in every repository.

## Risks and questions for the decision
1. **Public repository.** A marketplace is a `.claude-plugin/marketplace.json` file with plugin names and descriptions.
   In a public repo `tf` reveals what the project is, much like the README, which you do not want for now. Options: a
   separate private repo for the marketplace, or a local-only export (`--plugin-dir`), with no publication.
2. **Plugin name:** e.g. `tf-skills` (it cannot start with `claude-`).
3. **Cloud sessions do not load plugins from repository settings**: installing `tf` is still needed there.

## Proposed steps (after the decision)
1. **`tools/plugin_export.py`:** builds `dist/plugins/<id>/` (manifest, skills) from an overlay, checks the export with
   `claude plugin validate --strict` and adds a test to CI. The `claude plugin eval` evaluations are paid, so only with
   consent.
2. **Publication** according to the decision on risk 1.
3. **Exporting just an overlay's skills** comes with a warning about context cost for large overlays.
