---
name: core-stack-sync
description: Use at the start of work and on a version mismatch — the project stack and matching skills to it, without upgrading.
metadata:
  review: "2027-10-17"
  catalog: "Use at the start of work in an existing project and when a hook reports a version mismatch — reading the stack (package.json, lockfile, pom.xml, build.gradle), comparing it with the versions the skills are based on, and updating the skills (not the project) to the project's versions. Not for upgrading the project's dependencies (a separate task, only on the user's request)."
  keywords: "podnieść wersję, kompatybilność wersji, na jakich wersjach polegać, zakres obsługiwanych wersji, peerDependencies, jakie wersje mamy w projekcie, niezgodność wersji, prawdziwy stack projektu, ustalić wersje w projekcie, starsza wersja frameworka w projekcie, moja wiedza dotyczy nowszych wersji, API niedostępne w wersji projektu, version mismatch, which versions to rely on, supported version range, project stack, older framework version"
---

# Syncing skills with the project stack

Technology skills (`lang-*`, `fw-*`, `tool-*`) describe a specific version range recorded in `skill.meta.json`
(`min_supported` … `based_on`). The project can be newer or older — then the skill has to be updated or applied with
care.

## 1. Read the stack
```bash
python3 .claude/hooks/detect_stack.py            # text report
python3 .claude/hooks/detect_stack.py --json     # for further processing
python3 .claude/hooks/detect_stack.py --latest   # + latest versions from the npm registry
```
Order of version sources: installed (`node_modules`) → lockfile → range in `package.json`; Java: `pom.xml`,
`build.gradle(.kts)`, `.java-version`. The `SessionStart` hook does this automatically and speaks only when there is
something to do. Monorepo (Nx, workspaces): versions from the root `package.json`; when projects have their own
`package.json`, run the script for each.

## 2. Decide by status
| Status | Meaning | What you do |
|---|---|---|
| `OK` | the project version is within the skill's range | you work; from the "Version-dependent" section you take only what the project's version has |
| `SKILL_OUTDATED` | the project is newer than `based_on` | **you update the skill** (step 3) before basing decisions on it |
| `PROJECT_OLDER` | the project is older than `min_supported` | **you do not roll the skill back**; you add rows to "Version-dependent" for the project's version (what is unavailable and what replaces it) and use only those features |
| `MISSING_SKILL` | a technology without a skill | you propose creating it: `python3 .tf/factory/build.py new-skill fw-<technology> "…"` (it gets the vocabulary table) and filling it per step 3 |
| constraint ✗ | e.g. Angular 22 requires TypeScript 6.0.x | you do not recommend versions outside the range (e.g. TS 7 in a project with Angular 22); you report the mismatch to the user |

## 3. Updating a skill (for each `SKILL_OUTDATED`)
1. **Primary sources** from `skill.meta.json → sources` + release information for every major version between
   `based_on` and the project's version (release notes, the official blog, the upgrade guide). Third-party blogs only
   as support.
2. **Collect the changes that matter to the skill:** new stable APIs, changed defaults, deprecated and removed elements,
   new requirements (language, Node, JDK versions), changed idioms. Skip experimental things or mark them explicitly.
3. **Edit SKILL.md:**
   - "Conventions / Rules" — the new default approach (e.g. a new way to build forms, the default change-detection
     strategy);
   - "Domain concepts in …" — only when the idiom for a vocabulary concept changed;
   - "Version-dependent" — add rows for the new versions (what from which version, what is deprecated, what replaces it).
     The general content must stay true for the whole `min_supported … based_on` range.
4. **Update the examples in `references/`** and — where possible — verify them with that version's compiler/tests in a
   temporary directory (e.g. `npm i` of specific versions in a scratchpad, not in the user's project).
5. **Update `skill.meta.json`:** `based_on`, possibly `min_supported`, `verified` (date), `verified_with`, `constraints`
   (e.g. in pack-it `"22": {"lang-typescript": ">=6.0 <6.1"}`), `sources`.
6. **Check related skills** — constraints (`constraints`) and dependencies (`skill_requires` in `.tf/config/config.yaml`),
   e.g. a new framework version may require updating the language skill.
7. `python3 .tf/factory/build.py check` → show the user the diff → commit per core-conventional-commits,
   e.g. `docs(skills): update fw-angular to Angular 22` (a skill from pack-it).

## Rules
- Skills are shared between projects: an update widens the range (`based_on` up) rather than "switching" the skill to
  one project. Information for older versions stays in "Version-dependent".
- **Never upgrade the project's dependencies** as part of this procedure. Upgrading the project (`ng update`,
  `nx migrate`, a JDK change) is a separate task, done only on the user's request.
- When you have no access to sources (no network), state in the report that the skill was not verified for that
  version, and work carefully, sticking to features shared by both versions.
- Technology registry for detection: the core registry `references/technologies.json` and the pack registries
  `.tf/factory/packs/<id>/technologies.json` (the same format); `detect_stack.py` reads all of them. Add your project's
  own technology to the core registry so it is reported.
