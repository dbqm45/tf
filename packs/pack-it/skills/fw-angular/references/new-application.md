# A new Angular application and working with the CLI

Contents: 1. Creating the application · 2. Generating code and packages · 3. File names · 4. Environment configuration
· 5. The Angular CLI MCP server · Sources

## 1. Creating the application
1. **Version.** Without the human's request you do not specify a version: you take the latest stable one. When the human asks for a specific one,
   you use `npx @angular/cli@<version> new …`, bypassing the local installation.
2. **CLI.** Check whether `ng` is available (`ng version`). It is → `ng new`; it is not → `npx @angular/cli@latest new`.
   You propose a global installation (`npm install -g @angular/cli`) to the human; you do not run it yourself.
3. **A command without questions:** `ng new <name> --interactive=false` and flags chosen for the application description:
   - `--style=scss|css|less`, `--routing`, `--ssr` (server-side rendering, `rendering-and-ssr.md`),
     `--prefix=<prefix>` (the selector prefix);
   - `--ai-config=<tool>` writes rules for the agent into the project (e.g. `claude`, `agents`); after creation read
     the generated file and apply it together with this skill;
   - `--skip-tests` only on an explicit request.
4. **Application name:** propose one from the description or ask.
5. **Default decisions in a new project:** forms in Signal Forms (stable since v22), zoneless and `OnPush` (the default
   in new versions), Vitest, standalone, the new control flow.
6. **Do not start the development server right away.** First build the first features, then ask the human whether
   to run `ng serve`.
7. **Verification after every code change:** `ng build`. You read and fix compilation errors before handing over the work.

## 2. Generating code and packages
- You generate code through the CLI, then fill it in: `ng g c <path>` (component), `ng g s` (service), `ng g d`
  (directive), `ng g p` (pipe), `ng g g` (functional guard), `ng g interceptor`, `ng g resolver`, `ng g interface`,
  `ng g enum`, `ng g class`. Note the path returned by the generator so that you edit the right file.
- Routes have no generator: generate a component and add it to the `Routes` array (usually `app.routes.ts`).
- You add Angular libraries through `ng add <package>` instead of `npm install`: the command installs the package and runs its
  configuration schematics (e.g. `ng add @angular/material`, `ng add tailwindcss`).
- **Tailwind CSS v4:** after `ng add tailwindcss` the global stylesheet has `@import 'tailwindcss';`. Do not create
  `tailwind.config.js` or the `@tailwind base/components/utilities` directives from version 3. For manual configuration
  a `.postcssrc.json` file with the `@tailwindcss/postcss` plugin is enough.
- A proxy to a local API during development: the `proxy.conf.json` file and the `proxyConfig` option of the `serve` target in `angular.json`.
- E2e tests: `ng add` of the chosen tool (e.g. Playwright, Cypress), then `ng e2e`.

## 3. File names (the style guide since v20)
- In projects created in the new style files have no role suffix: `product-list.ts` with the `ProductList` class instead of
  `product-list.component.ts`; the template and styles have the same base name, the test `.spec.ts`.
- The name says the purpose, not the role: services `auth-data.ts`, `orders-store.ts`, `user-data-client.ts`; the directory gives the context
  (`core/`, `features/<feature>/`, `shared/`). Data types keep the `.model.ts` suffix.
- Name collisions: the `UserProfile` component in `user-profile.ts` next to the `User` interface in `user.model.ts`.
- **Check the project first:** neighbouring files, schematic settings in `angular.json`, ESLint rules. A project
  with suffixes stays with suffixes. Do not mix both styles in one feature directory; when in doubt use
  suffixes.

## 4. Environment configuration
- **At build time:** `ng g environments` creates `src/environments/` and the file replacement in `angular.json`. Checking
  development mode: `isDevMode()` instead of a manual `production` flag.
- **At run time:** the same artifact for many environments; configuration from a JSON file loaded before the application
  starts (`provideAppInitializer`) and provided with a token. You do not put secrets in any of these files: they end up
  in the browser.

## 5. The Angular CLI MCP server
- The Angular CLI has a built-in MCP server: `npx @angular/cli mcp` (in the MCP client configuration as `command: npx`,
  `args: ["-y", "@angular/cli", "mcp"]`). Options: `--read-only` (only tools without changes to the project), `--local-only`
  (no network).
- Tools include: `get_best_practices` (the best-practices guide for the project's version), `search_documentation`
  (angular.dev), `list_projects`, `onpush_zoneless_migration` (a plan for moving to `OnPush` and zoneless), `run_target`,
  `devserver_start`, `devserver_stop`, `devserver_wait_for_build`.
- Adding an MCP server to the agent configuration is a permission change: only with the human's consent (core-agent-security).
  Choose `--read-only` when the agent only needs to read.

## Sources
- angular/skills, the `angular-new-app` and `angular-developer` skills (angular-developer/references files: cli, naming-conventions,
  environment-configuration, tailwind-css, mcp, e2e-testing), commit
  43ec6adc2b35049734d0d114e3948e022f1cd1e7 of 2026-10-21 (generated from angular/angular), MIT licence, author Google LLC.
  Described in our own words; accessed 2026-10-21.
