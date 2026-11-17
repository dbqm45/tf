**Token-frugal**
- You search with Grep/Glob before opening a file; you read fragments (offset/limit), not whole large files.
- You do not read node_modules, builds, lockfiles or generated files.
- You trim long command output (`| tail -50`, `--quiet`, `--reporter=dot`).
- Reports and answers are short: the result, the verification, the risks.
