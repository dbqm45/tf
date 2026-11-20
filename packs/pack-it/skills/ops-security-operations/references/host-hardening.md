# Host hardening (the server's operating system)

Applies to a virtual or physical machine with a full operating system (Linux, briefly Windows Server). Containers and images:
`ops-docker`; the cloud account and services, CSPM: `sec-cloud-security`; secrets and machine keys: `ops-secrets-identities`.
The goal: a smaller attack surface and a configuration that does not drift.

## Procedure
1. **A baseline instead of a list from memory.** Choose the CIS Benchmark for the distribution and version (level 1 to start;
   level 2 for systems with a high data classification) or a SCAP/STIG profile if a regulation requires it. Record deviations
   with a reason and an owner (an ADR or an exceptions file next to the IaC). General principles: NIST SP 800-123.
2. **A minimal system.** The distribution's minimal image; remove or disable services and packages the machine's role does not
   need (`systemctl list-unit-files --state=enabled`, `ss -tulpn` — every listening port has an owner).
   No compilers or diagnostic tools in production, if they are not needed.
3. **SSH.** Keys only (`PasswordAuthentication no`, `KbdInteractiveAuthentication no`), no root login
   (`PermitRootLogin no`), restricted users or groups (`AllowGroups`), access only from a bastion, a VPN or
   conditional access (sec-zero-trust-identity) — port 22 is not open to the internet. Better: access through
   the cloud provider's session manager or short-lived SSH certificates instead of long-lived keys.
4. **Accounts and permissions.** Named accounts, no shared ones; `sudo` with a list of commands per role, not `ALL`;
   service accounts without a shell; expiry of unused accounts. Least privilege also for processes: a service
   as a separate user, systemd restrictions (`NoNewPrivileges`, `ProtectSystem`, `PrivateTmp`).
5. **The host firewall** rejects inbound traffic by default (nftables, ufw, firewalld; in the cloud additionally security
   groups). Outbound traffic restricted where possible — it makes data exfiltration and downloading tools harder for
   an attacker.
6. **Kernel and file system.** `sysctl` parameters from the baseline (e.g. packet forwarding disabled when the machine
   is not a router; protection against address spoofing); `/tmp` and data partitions with `noexec`, `nosuid`, `nodev`,
   where the role allows it; Secure Boot; SELinux or AppArmor in enforcing mode, not disabled.
7. **Audit and logs.** `auditd` (account changes, sudo, configuration files, module loading) and system logs
   sent off the host (section 1 of the skill: telemetry). Time synchronization (NTP/chrony) — without it correlation does not work.
8. **Patches.** Automatic security patches (`unattended-upgrades`, `dnf-automatic`) or an image rebuild
   in rings (section 5 of the skill); a reboot after a kernel patch planned, not postponed forever.
9. **Endpoint protection.** EDR or a detection agent on production hosts (section 3 of the skill), file integrity
   monitoring for critical paths.
10. **Checking and drift.** A compliance scan against the baseline (OpenSCAP with a CIS profile, Lynis as a quick review) after
    building the image and periodically; the result in the image CI or in a report. The machine built from IaC (Packer, Ansible,
    cloud-init), manual changes detected and reverted — logging in to the machine to "fix" something is drift.

## Windows Server — a summary
CIS Benchmark or Microsoft Security Baselines; Server Core where possible; SMBv1 and unneeded roles disabled;
LAPS for local administrator passwords; the Windows firewall enabled for all profiles; Defender (or another EDR)
and PowerShell logging (Script Block Logging) sent to the SIEM.

## Example
**Input:** "Three Ubuntu machines with an API, SSH open from the internet, password login, updates by hand once a
quarter."
**Result:** an image from Packer + Ansible per CIS Ubuntu level 1, exceptions in an exceptions file next to the IaC; SSH only from
the bastion and only with keys, no root; firewall: 443 from the load balancer, 22 from the bastion; `unattended-upgrades` for
security patches with a reboot window; auditd and journald to the SIEM; OpenSCAP in the image pipeline, a report every week;
configuration changes only through a PR to the IaC.

## Checklist
- [ ] a baseline (CIS/SCAP) chosen, deviations recorded
- [ ] only the needed services and ports; every port has an owner
- [ ] SSH: keys or certificates, no root, no access from the internet
- [ ] named accounts, restricted sudo, services under separate users
- [ ] the host firewall rejects by default; outbound traffic restricted where possible
- [ ] SELinux/AppArmor enforcing; kernel and mount parameters from the baseline
- [ ] auditd and logs off the host, time synchronized
- [ ] automatic patches or an image rebuild; reboots planned
- [ ] a compliance scan after the build and periodically; drift detected, changes only through IaC

## Sources
- NIST SP 800-123 *Guide to General Server Security* (final, 07.2008; the nist.gov page checked 2026-10-27, the status on
  csrc.nist.gov [unverified] — the host is unreachable from the sandbox): https://csrc.nist.gov/pubs/sp/800/123/final
- CIS Benchmarks (a list per system): https://www.cisecurity.org/cis-benchmarks [unverified: the page was not fetched];
  CIS Controls v8.1 (06.2024, per a search on 2026-10-27)
Described in our own words.
