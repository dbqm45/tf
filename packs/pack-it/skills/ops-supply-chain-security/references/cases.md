# Cases from Huntress and devops.com analyses (summaries in our own words)

Every case: what happened → what would have stopped it. The technical details and indicators are in the sources.

## axios in npm (March 2026)
- **Course:** the attackers took over the main maintainer's computer during a fake meeting (a forged company Slack,
  a Teams call with several "participants", a request to install an "update"). From the taken-over account they published
  axios 1.14.1 and 0.30.4 with a new dependency `plain-crypto-js` 4.2.1, whose `postinstall` installed remote access (a RAT)
  on Windows, macOS and Linux. An attack window of about 3 hours; Huntress recorded at least 135 infected machines.
- **What would have stopped it:** a cooldown for new versions (1–3 days), blocking install scripts in CI, an alarm on a new transitive
  dependency, publishing only through OIDC with classic tokens revoked.
- Sources: [Supply Chain Compromise of axios npm Package](https://www.huntress.com/blog/supply-chain-compromise-axios-npm-package),
  [axios npm Compromise: The Ultimate Supply Chain Scaries](https://www.huntress.com/blog/axios-npm-compromise)

## A multi-ecosystem campaign (TeamPCP, March 2026)
- **Course:** simultaneous attacks on GitHub Actions, npm, PyPI and Docker Hub; a swapped Trivy scanner in actions,
  malicious versions of a PyPI package, a data-stealing payload hidden in an audio file. The target: secrets from CI and developer laptops.
- **What would have stopped it:** tool actions and images pinned to a SHA/digest, short-lived OIDC credentials in CI instead of
  permanent secrets, restricted outbound traffic from the runners.
- Source: [Threat View from the Lens of Huntress Adversary Tactics: March 2026](https://www.huntress.com/threat-library/adversary-tactics/march-2026)

## Trivy → Checkmarx KICS → LiteLLM (March 2026, devops.com)
- **Course:** the TeamPCP group returned to the Trivy project through a credential that had not been revoked after an earlier
  break-in. The malicious action read tokens and cloud keys from the runner process memory and then performed a normal scan.
  The stolen write tokens were used for further compromises (Checkmarx KICS, npm packages). The CI of the LiteLLM project
  installed the swapped Trivy, and the malicious LiteLLM releases were on PyPI for about 40 minutes.
- **What would have stopped it:** scanners in jobs without secrets, pinned versions of build tools, rotation of all
  credentials after an incident, an alarm on repositories and releases created by unexpected accounts.
- Sources: [Sophisticated Supply Chain Attack Targeting Trivy Expands to Checkmarx, LiteLLM](https://devops.com/sophisticated-supply-chain-attack-targeting-trivy-expands-to-checkmarx-litellm/),
  [LiteLLM Attack Affected 2,500 Companies, 434,000 CI/CD Pipelines](https://devops.com/litellm-attack-affected-2500-companies-434000-ci-cd-pipelines-cloudsek/) (the figures from the vendor CloudSEK)

## Mini Shai-Hulud (May 2026, devops.com)
- **Course:** the attackers published malicious versions using the victims' trusted publishing path (their GitHub Actions
  workflows and OIDC tokens), so the packages had valid provenance. The payload was in an optional dependency
  fetched from GitHub and run by Bun, which bypassed static scanners.
- **What would have stopped it:** a trusted publisher pinned to the workflow and a protected environment with a human's approval,
  a ban on publishing from commits outside protected branches, an alarm on `github:` dependencies.
- Source: [Widespread Mini Shai-Hulud Campaign Is a Matter of Trust](https://devops.com/widespread-mini-shai-hulud-campaign-is-a-matter-of-trust/)

## React2Shell, CVE-2025-55182 (December 2025)
- **Course:** unsafe deserialization in the React Server Components protocol allowed executing code
  on the server without logging in, with a single HTTP request. It affected `react-server-dom-webpack`, `-parcel` and `-turbopack` in versions 19.0,
  19.1.0, 19.1.1, 19.2.0 (fixes: 19.0.1, 19.1.2, 19.2.1), and therefore also Next.js applications. The attacks started the day after
  the disclosure; after a break-in, cryptocurrency miners, backdoors and tunnels were installed.
- **What would have stopped it:** deploying the patch within a day (the exception path from the cooldown), a Node server without root privileges,
  without a shell in the image and with restricted outbound traffic (ops-docker), an alarm on the server process launching a shell.
- Sources: [PeerBlight Linux Backdoor Exploits React2Shell](https://www.huntress.com/blog/peerblight-linux-backdoor-exploits-react2shell),
  [Codex Red: Untangling a Linux Incident With an OpenAI Twist (Part 2)](https://www.huntress.com/blog/codex-part-two)

## Legitimate tools as a backdoor (Komari, 2026)
- **Course:** after getting in through stolen VPN credentials, the attacker installed an open-source monitoring agent
  as a service with a misleading name, downloading the installation script straight from GitHub. The agent gave them a remote shell.
- **What would have stopped it:** no "download and run" installers from the internet, an alarm on new services and daemons, control
  of traffic to `raw.githubusercontent.com` from servers.
- Source: [Komari: The 'Monitoring' Tool That Didn't Need Weaponising](https://www.huntress.com/blog/komari-c2-agent-abuse)

## General conclusions
Supply chain attacks are detected much later than direct break-ins, because they come through a channel you trust
(a signed update, a known package). That is why what counts is: an inventory (SBOM), verification (signatures, provenance),
minimal permissions for vendors and segmentation.
Source: [What Rising Supply Chain Attacks Mean for Cybersecurity Ecosystems](https://www.huntress.com/blog/rising-supply-chain-attacks-cybersecurity-ecosystems)
