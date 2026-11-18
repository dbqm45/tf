# Network, cloud and identity at scale — infrastructure security

## Basic principles
- **The CIA triad**: confidentiality, integrity, availability. Every control protects one of them; DDoS and ransomware attack
  availability, a leak — confidentiality, tampering — integrity.
- **Defense in depth**: several independent layers (identity, network, host, application, data, detection), so that a failure of one
  does not mean a breach.
- **Least privilege** and **default deny** everywhere: IAM, network rules, Kubernetes RBAC, databases.

## Segmentation and zones
- Zones with a clear traffic policy between them: public (CDN, load balancer) → application → data; separately management
  (a bastion or identity-based access) and CI/CD. Traffic between zones denied by default, allowed by a rule with a description.
- East–west traffic (between services) filtered too — this is how an attacker moves after a breach: security groups
  per service, NetworkPolicy in Kubernetes (ops-kubernetes), VLANs or subnets in data centers.
- Databases and queues without public addresses; outbound traffic with an allowlist (it makes data exfiltration and contact
  with the attacker's server harder).

## Zero trust (NIST SP 800-207)
Location in the network does not grant trust. Every request: authenticated (the user **and** the device or service),
authorized according to a policy (context: device state, risk, time), encrypted. In practice: access to internal
tools through an identity-aware proxy instead of a VPN to the whole network, mTLS or workload identity between services,
short-lived credentials.

## DDoS
- Layers 3/4 (packet floods): protection from the cloud provider or a CDN with anycast and traffic scrubbing — the application alone
  will not stop it.
- Layer 7 (expensive HTTP requests): a CDN and cache, a WAF with bot protection, rate limits (be-api-design), queues for
  heavy operations, a challenge for suspicious clients.
- Autoscaling with **an upper limit and a cost alert** — an attack may target the bill (ops-finops).
- A plan: the contact at the protection provider, switching DNS or an "under attack" mode, communication with customers.

## Cloud: posture and identity
- **CSPM**: continuous checking of configuration (public buckets, open ports, missing encryption, overly broad roles)
  against CIS benchmarks — the provider's tools (AWS Security Hub, Microsoft Defender for Cloud, Google Security Command
  Center) or open ones (e.g. Prowler). Findings as tasks with an owner; new violations blocked earlier in the IaC
  (policies as code).
- **IAM**: people sign in through SSO with phishing-resistant MFA, no long-lived user keys; administrative
  permissions granted just in time; permission boundaries at the organization level (e.g. SCP) blocking the disabling of audit
  logs and the use of unused regions; service accounts — ops-secrets-identities.
- **Identity in a large organization** (IGA): joining, role change, leaving (joiner–mover–leaver) automated
  from the HR system; provisioning through SCIM; periodic access reviews with the manager's approval; detection of orphaned
  accounts and excessive permissions.

## Identity and network in the company (on-premises and hybrid)
- **Directory and protocols**: Active Directory or another LDAP directory — connections only over LDAPS or StartTLS,
  service accounts with long random passwords or managed identities (gMSA), separate administrative accounts;
  Kerberos with modern encryption (no RC4), restricting NTLM; Group Policy as code and with a review of
  changes. Sign-in to applications through SSO (SAML or OIDC) instead of separate passwords.
- **Network access**: 802.1X with RADIUS (EAP-TLS with device certificates instead of passwords), network access control
  (NAC) checking the device state, a VPN (IPsec or WireGuard) or better identity-based access (zero trust).
  Wi-Fi: WPA3 (Enterprise for the company), detection of rogue access points, a separate guest network.
- **Switches and VLANs**: automatic trunk negotiation disabled on access ports (protection against
  VLAN hopping), unused ports disabled, protection against ARP and DHCP spoofing (DHCP snooping, dynamic
  ARP inspection) where the hardware allows it.
- **DNS**: DNSSEC for your own zones, a DNS filter with lists of malicious domains, query logs in the SIEM.
- **Data loss prevention (DLP)**: data classification, rules for mail, the cloud and workstations;
  start in monitoring mode, because blocking rules without tuning stop work.
- **Developer workstations**: disk encryption, EDR, automatic updates, an account without permanent administrator
  rights, a password manager, secrets outside files in the home directory (core-agent-security, ops-secrets-identities).

## Multiple regions
- Data residency requirements (GDPR/RODO, contracts, the sector) decide which data may leave a region — recorded in an ADR.
- The same policies in all regions from one codebase (IaC, policies); unused regions blocked.
- KMS keys per region (data encrypted with a key from the region where it resides); backups in another region only
  in line with the residency requirements.
- Central collection of security logs and CSPM findings from all regions — an attack often starts where
  nobody is looking.

## Sources
- NIST SP 800-207 *Zero Trust Architecture* (2020); CIS Benchmarks; [Cloudflare: how to prevent DDoS attacks](https://www.cloudflare.com/en-gb/learning/ddos/how-to-prevent-ddos-attacks/)
- [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops) (CIA, defense in depth, segmentation, zoning, zero trust,
  DDoS, CSPM, IAM, large-scale identity, multi-region)
Described in our own words.
