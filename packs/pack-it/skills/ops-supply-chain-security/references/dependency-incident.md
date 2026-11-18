# Procedure: a compromised package has been reported

Goal: within hours, answer whether we have been affected, and if so — cut off the attacker and revoke what they could
have taken. The order matters: first establishing the scope, then rotating secrets, then the clean-up.

## 1. Establish the facts from the advisory
- The package name, the malicious versions, the time window (from publication to removal), the mechanism (e.g. `postinstall`), the indicators:
  file names, domains, IP addresses, additional packages. Source: the advisory of the maintainers, the registry, a security vendor.
- Record them in the project log (core-project-record) — this will be the basis for decisions and the report.

## 2. Do we have this version
- The lockfiles of all repositories and release branches: `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`.
  Search with `grep` for the package name and the names of the packages added by the attack — do not read whole files (the token cost).
- The SBOM of the released artifacts and images (section 5 of the skill).
- The mere presence of the directory of the added malicious package in `node_modules` means that the script was executed — even if the files
  look clean (malicious scripts can clean up after themselves).

## 3. Which machines installed during the attack window
- CI runners: the logs of jobs with an installation in the time window; treat self-hosted runners like laptops.
- Developer laptops: who ran `npm install` / `update` at that time; the persistence traces described in the advisory
  (files, services, autostart entries); traffic to the indicated domains and IPs in the network logs.

## 4. An affected machine = a compromised machine
- Do not "clean" it — reinstall the operating system or destroy the runner and the image. The malware may have left more than one
  persistence mechanism.
- Before you shut it down, preserve what the security team needs (the list of processes, connections, logs).

## 5. Rotate everything that was reachable
From every affected machine and runner: npm/PyPI/registry tokens, GitHub tokens (personal and app ones; `GITHUB_TOKEN` itself
expires when the job ends), SSH keys, cloud credentials, the contents of `.env`, browser sessions and the OAuth tokens
of tools (cloud CLIs, `gh`, Docker). After the rotation, review the access logs of the registry, the repositories and the cloud from the attack window.

## 6. Fixing the dependencies
- Pin the last safe version and enforce it in the whole tree (`overrides` in npm, `pnpm.overrides`, `resolutions`).
- Clear the cache (`npm cache clean --force`), reinstall from scratch with `--ignore-scripts`, check the lockfile.

## 7. Conclusions
Which of the safeguards from the skill's checklist would have stopped the attack (a cooldown, blocking scripts, an alarm on a new dependency)?
Enter the decision into the decision register and plan the rollout.
