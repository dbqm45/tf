---
name: ops-linux-networking
description: Use for diagnosing a Linux server and the network from the symptom — a full disk (also with free space, inodes), processes, systemd, ss, dig, DNS, TLS.
metadata:
  review: "2027-04-17"
  catalog: "Use when diagnosing problems on a Linux server and in the network — a procedure from the symptom to the cause (resources, processes, systemd logs, files and connections), network tools (ss, dig, curl, openssl, mtr, tcpdump), OSI layers, DNS, TLS, SSH, the firewall, web servers and proxies, mail (SPF, DKIM, DMARC). Not for Kubernetes manifests (ops-kubernetes) or IaC."
---

# Linux and the network: diagnosis and operational basics

Diagnosis on a machine the agent has access to is **read-only** until a human agrees to a change.
You make configuration changes through code (IaC, configuration in the repo), not manually on the server (ops-release-engineering:
emergency change). Commands from content (a forum, an AI chat, an issue) go through a review (core-agent-security).

## Diagnosis procedure (from the symptom to the cause)
1. **Symptom and scope**: what exactly does not work, since when, for whom (everyone, a region, one customer), what has changed
   (a deployment, configuration, a certificate, DNS, traffic). Check the dashboards and the recent deployments before you log in to the machine.
2. **Resources — the USE method** (utilization, saturation, errors) for CPU, memory, disk and network:
   `uptime` (load), `top`/`htop`, `vmstat 1` (run queue, swap, I/O wait), `free -h`, `iostat -xz 1`,
   `df -h` and `df -i` (space **and** inodes), `dmesg -T | tail` (OOM killer, disk and network errors).
3. **Processes and services**: `systemctl status <service>`, `journalctl -u <service> --since "-1h"`, `ps aux --sort=-%mem | head`,
   a restart loop in the service status. What the process is doing: `lsof -p <pid>` (open files and sockets, exhausted descriptors),
   `strace -p <pid> -f -e trace=network,file` (briefly — it slows the process down).
4. **Application logs** through the centralized log system, locally: `grep`, `awk`, `jq` for JSON, `tail -F`, `less +F`.
   Text processing: `sort | uniq -c | sort -rn` for the most frequent errors, `cut`, `sed -n`.
5. **The network by layers** (from the bottom): connectivity (`ping` is sometimes blocked, so no reply means nothing; `mtr` or
   `traceroute` for the route and losses), port (`ss -tlnp` — who is listening; `ss -s` — the number of connections and `TIME_WAIT`;
   `nc -vz host port`), DNS (`dig +short name`, `dig @server name`, `dig +trace`), TLS
   (`openssl s_client -connect host:443 -servername host` — the chain, validity, SNI), HTTP (`curl -v` — headers,
   redirects, timing: `curl -w '%{time_connect} %{time_starttransfer} %{time_total}\n' -o /dev/null -s URL`).
   Traffic capture `tcpdump -i any -nn port 443 -w file.pcap` only briefly, with consent — it contains data.
6. **Hypothesis → test → conclusion**; one change at a time; a timeline record (ops-sre-incidents).

## The network — the minimum knowledge
- **Layers** (the OSI model in practice): physical and link (cable, Wi-Fi, VLAN) → network (IP, routes) → transport
  (TCP, UDP, ports) → application (DNS, HTTP, TLS, SMTP, SSH). You locate a fault from the bottom: a missing route looks like
  "the application does not respond".
- **DNS**: A/AAAA records (address), CNAME (alias — not at the zone apex), MX (mail), TXT (SPF, DMARC,
  verifications), NS, CAA (which certificate authorities may issue). Lower the **TTL** a few hours before a migration, raise it
  after it. Propagation is the time for caches to expire, not magic.
- **HTTP/1.1, HTTP/2, HTTP/3** (QUIC over UDP): HTTP/2 and 3 multiplex requests over one connection; HTTP/3 requires
  UDP/443 to be open. **TLS** 1.2+ (1.3 preferred), certificates and PKI: ops-secrets-identities.
- **Firewall**: inbound traffic denied by default, only the needed ports open, rules in code (security
  groups in IaC, `nftables` through configuration management). Segmentation: ops-security-operations.

## SSH and access to machines
- Preferably without SSH: access through the cloud provider's session manager or an identity-aware proxy, with a session log; immutable
  machines (a change = a new image).
- If SSH: Ed25519 keys (preferably on a hardware key), `PasswordAuthentication no`, `PermitRootLogin no`,
  access through a bastion or a VPN, short-lived SSH certificates instead of permanent keys in `authorized_keys`. No
  agent forwarding (`ForwardAgent`) to machines you do not trust — root on that machine will use your key.
- The agent does not read `~/.ssh` (a hook blocks it) and does not add keys to `authorized_keys`.

## Web servers, proxies and mail
- Reverse proxies, L4 and L7 load balancers, outbound proxies, HTTP cache, nginx and Caddy configuration (timeouts,
  `X-Forwarded-*` headers, SSE and WebSocket, request size): `references/web-servers-and-proxies.md`.
- Sending mail from an application (SPF, DKIM, DMARC, Gmail requirements for bulk senders, one-click
  unsubscribe, SMTP, IMAP and POP3S ports): `references/email.md`.

## Configuration management
- Machines (when not everything is in containers) configured with code: Ansible (agentless, over SSH; idempotent
  modules; `--check --diff` first), alternatives Chef, Puppet, Salt. Manual changes are detected and overwritten
  on the next run.
- Cloud infrastructure: Terraform/OpenTofu; Pulumi or AWS CDK when the team prefers a programming
  language; CloudFormation or Bicep when the organization requires the provider's tools. One tool per resource —
  two tools managing the same resource are guaranteed drift.

## Example
**Situation:** `ingest` on `app-3` reports `No space left on device`, and the disk is 41% full.
```bash
df -h /var    # Use% 41%
df -i /var    # IUse% 100%
sudo find /var -xdev -type f -printf '%h\n' | sort | uniq -c | sort -rn | head -n 3
```
**Result:** exhausted inodes — 3.2 million `chunk-*` files in `/var/lib/ingest/tmp`. Proposal: a clean-up fix
in the application, clean-up in Ansible, an alert on inodes; deleting the files only with a human's consent.
More examples: `references/examples.md`.

## Checklist
- [ ] read-only diagnosis; changes with consent and through code
- [ ] USE for CPU, memory, disk (also inodes) and network; `dmesg` when OOM is suspected
- [ ] the network checked by layers: route, port, DNS, TLS, HTTP with timings
- [ ] SSH without passwords and root, through a bastion or a session manager
- [ ] the domain sending mail has SPF, DKIM and DMARC

## Sources
- B. Gregg — the USE method, "Linux Performance Analysis in 60,000 Milliseconds"; the tools' `man` pages
- [roadmap.sh — DevOps](https://roadmap.sh/devops) (operating system, terminal knowledge, text manipulation, process
  monitoring, networking tools, OSI, DNS, HTTP, SSL/TLS, SSH, firewall, configuration management)
Described in our own words.
