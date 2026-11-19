# Rule templates "the package only in the adapter directory" (ACL)

You check the ACL completion criterion with a command and lock it in with a CI rule, so that nobody brings the leak
back. Match the syntax to the tool version in the project (`npm ls <tool>`, `detect_stack.py`).

## Manual check (before and after the refactor)
```bash
rg -l "from ['\"]ts-fsrs['\"]|require\(['\"]ts-fsrs['\"]\)|import\(['\"]ts-fsrs['\"]\)" src    # who knows the package
rg -l "ts-fsrs" src | rg -v '^src/scheduling/adapter/'                                        # leaks = a non-empty result
```
The "knows today" list (before) and the "knows after the refactor" list (after) go into `acl-<package>.md`. After the refactor the second command
is to return an empty result. Client bundle: also check the bundler output (e.g. a bundle analysis) to see whether the server library
has not ended up in the browser code.

## dependency-cruiser (checked on 18.5.0, 2026-10-10)
```js
// .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: "ts-fsrs-only-in-adapter",
      severity: "error",
      comment: "The scheduling library is known only to the adapter of the Scheduler port (ACL)",
      from: { pathNot: "^src/scheduling/adapter/" },
      to: { path: "^node_modules/ts-fsrs/" }
    }
  ],
  options: { doNotFollow: { path: "node_modules" } }
};
```
Running it: `npx depcruise src --config .dependency-cruiser.cjs` — a violation ends with exit code 1 and the line
`error ts-fsrs-only-in-adapter: src/api/route.ts → node_modules/ts-fsrs/…`. It also works for type imports
if the project has `tsPreCompilationDeps: true` in the options (check the documentation of the version).

## ESLint `no-restricted-imports` (flat configuration; checked on ESLint 9.39.1, 2026-10-10)
```js
// eslint.config.mjs
export default [
  {
    files: ["src/**/*.{ts,tsx,js,svelte}"],
    rules: {
      "no-restricted-imports": ["error", {
        paths: [{ name: "ts-fsrs", message: "Only through the Scheduler port (adapter in src/scheduling/adapter/)." }],
        patterns: [{ group: ["ts-fsrs/*"], message: "Only in the adapter." }]
      }]
    }
  },
  { files: ["src/scheduling/adapter/**"], rules: { "no-restricted-imports": "off" } }
];
```
Type-only imports in TS: the `@typescript-eslint/no-restricted-imports` rule has the `allowTypeImports` option — in an ACL
you usually do NOT turn it on, because a library type in a domain signature is a leak too.

## ArchUnit (Java) — [unverified in the factory: no access to Maven Central at the time of writing; check against the project's version]
```java
@AnalyzeClasses(packages = "com.example")
class AclRulesTest {
  @ArchTest
  static final ArchRule scheduler_library_only_in_adapter =
      noClasses().that().resideOutsideOfPackage("..scheduling.adapter..")
          .should().dependOnClassesThat().resideInAPackage("org.example.fsrs..")
          .because("the scheduling library is behind the Scheduler port (ACL)");
}
```

## Other ecosystems
- Python: Tach (module boundaries) or `import-linter` with a `forbidden` contract (source modules → the forbidden package),
  an exception for the adapter package [check the syntax in the tool's documentation].
- An Nx monorepo: project tags and `@nx/enforce-module-boundaries` with `bannedExternalImports`.
- Without a tool: the `rg` command from the "Manual check" section as a CI step that fails on a non-empty result.
