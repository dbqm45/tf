# Cases from Huntress analyses (summaries in our own words)

## ClickFix: "paste and run"
- **Mechanism:** a fake CAPTCHA or a full-screen "Windows update" asks for the Win+R shortcut, pasting from the clipboard
  and Enter. The pasted command (e.g. `mshta` with an IP address written in hexadecimal) downloads further stages; in one variant
  the code was hidden in the pixels of a PNG image, and the final payload was programs stealing passwords and browser data.
- **Lesson:** a command from a page's content is data. Detection: a browser/explorer → mshta/PowerShell chain,
  IP addresses in an unusual notation on the command line.
- Source: [ClickFix Gets Creative: Malware Buried in Images](https://www.huntress.com/blog/clickfix-malware-buried-in-images)

## Fake GPTs and fake instructions for AI tools
- **Mechanism:** search engine ads led to crafted Custom GPTs on chatgpt.com, which sent users to
  a page with a fake CAPTCHA and a PowerShell command; at the end a RAT with access to the screen, the camera and the microphone was installed.
  In other campaigns shared conversations on the official ChatGPT, Grok and claude.ai domains gave "advice" (e.g. how
  to free up disk space or how to install Claude Code) in the form of a Terminal command that installed a data stealer
  on macOS (passwords, the keychain, wallets).
- **Lesson:** a trusted domain does not make a command trusted. Install tools from the official documentation, not from sponsored
  results. Huntress sums it up like this: trust has become an attack surface.
- Sources: [Attackers Abuse ChatGPT Custom GPTs to Deliver RAT via ClickFix](https://www.huntress.com/blog/chatgpt-custom-gpts-clickfix-rat),
  [Attackers Didn't Wait for AI. They Built Workflows Around It.](https://www.huntress.com/blog/ai-powered-attack-workflows),
  [AMOS Stealer Exploits AI Trust: Malware Delivered Through ChatGPT and Grok](https://www.huntress.com/blog/amos-stealer-chatgpt-grok-ai-trust),
  [How a Google Search for Claude Led to MacSync](https://www.huntress.com/blog/fake-claude-macsync)

## An AI assistant on a compromised machine
- **Mechanism:** a developer's server with Next.js vulnerable to React2Shell (a likely vector of reinfection) was taken over by several attackers at once
  (miners, a botnet, data theft). Among other things `~/.ssh`, `~/.aws`, `~/.kube/config`, `.env` files,
  `.git-credentials` and data from the cloud metadata service were taken. Persistence: eight mechanisms (the user's and the system cron, the user's
  systemd services started from `/dev/shm`, udev rules, files locked with `chattr +i`), plus deleting the history
  and logs. The developer asked an AI assistant to "fix" a noisy fan; the assistant limited the CPU, the symptom disappeared,
  the attackers stayed. Without root permissions the assistant did not see the system persistence mechanisms, and its commands looked
  in the telemetry like the attacker's reconnaissance.
- **Lesson:** you report signs of a break-in, you do not fix them; limit passwordless sudo; the agent's sessions leave a trace
  with a time, so they can be separated from the attacker's actions; remove the cause (a patch), not only the effect.
- Sources: [Codex Red: Untangling a Linux Incident With an OpenAI Twist (Part 1)](https://www.huntress.com/blog/codex-part-one),
  [Part 2](https://www.huntress.com/blog/codex-part-two)

## An AI agent as a new insider threat
- **Huntress's thesis:** an agent gets permissions with one click, works at machine speed and does not question
  bad commands; malicious MCP servers and skills have already appeared.
- **Recommendations:** a separate identity and minimal permissions for every agent, reviewing plugins and integrations like vendors,
  a baseline of normal behaviour and an alarm on deviations, an audit trail linking the identity to the actions,
  an isolation plan in case the agent is taken over.
- Source: [AI Agent Security Risks: How Autonomous Agents Become an Insider Threat](https://www.huntress.com/insider-threats-guide/ai-agent-security-risks)

## AI speeds up old techniques
- **Huntress's thesis:** language models shorten the attack time for less experienced attackers, but the techniques stay the same
  (credential theft, remote administration tools, browser extensions). The defence does not change either:
  telemetry, command-line logging, MFA on administration tools, minimal permissions.
- Source: [Reflecting on AI in 2025: Faster Attacks, Same Old Tradecraft](https://www.huntress.com/blog/ai-2025-faster-attacks-same-tradecraft)

## Poisoning MCP tools and controlling changes from AI (devops.com)
- **Mechanism:** hidden instructions in an MCP tool's description tell the agent to read `~/.ssh`, `.env` or kubeconfig or
  to run `curl | bash`; a malicious tool can also pretend to have a high priority and record the calls <!-- audit-ok: opis ataku, nie polecenie -->
  of other tools. In the case described by Zenity Labs an instruction in a Jira issue, passed through MCP, led
  an agent in the editor to send out secrets.
- **Lesson:** review tool descriptions like code; changes in the pipeline from AI labelled, with CODEOWNERS on protected
  paths, with a scope limit and tests the agent cannot change.
- Sources: [Prompt Injection Isn't Just a Chat Problem — It's a DevOps Threat](https://devops.com/prompt-injection-isnt-just-a-chat-problem-its-a-devops-threat/),
  [Your Next Secrets Leak is Hiding in AI Coding Tools](https://devops.com/your-next-secrets-leak-is-hiding-in-ai-coding-tools/) (a vendor article),
  [The Agent Proposes, the Pipeline Disposes](https://devops.com/the-agent-proposes-the-pipeline-disposes-controls-for-ai-authored-change/),
  [AI-Generated Code Packages Can Lead to 'Slopsquatting'](https://devops.com/ai-generated-code-packages-can-lead-to-slopsquatting-threat/)
