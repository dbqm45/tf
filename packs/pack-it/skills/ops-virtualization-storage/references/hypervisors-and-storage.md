# Hypervisors and storage — facts to check before deciding

Contents: Versions and licences · When to use what · Questions for vendors

## Versions and licences (status according to a search on 2026-10-17)
- Proxmox VE 9.1: Debian 13 "Trixie", kernel 6.17, QEMU 10.1, Ceph Squid 19.2.3, ZFS 2.3.4. Whether a newer release exists: [unverified].
  Upgrading from 8.x first requires Ceph Reef → Squid.
- Ceph: Tentacle (20.x) the newest series, Squid (19.x) in the final phase of support; in Tentacle 20.2.0 a bug was reported
  when enabling `allow_ec_optimizations` on an EC pool — check the report (Tracker 74813) before enabling it
  [unverified].
- VMware (Broadcom): subscription instead of perpetual licences, per-core billing, a minimum of 16 cores per processor;
  reports of a minimum of 72 cores per purchase from 2025-04 (does not apply to all renewals — sources differ)
  [unverified]. Always verify in the partner's offer and the contract; package names (VCF, VVF) change.

## When to use what
- A small company, 2–10 nodes, Linux skills: Proxmox VE or KVM.
- A large environment with VMware tooling and application certifications: put the subscription cost and the migration cost side by side.
- Container workloads: Kubernetes nodes can also run on bare metal — the decision is in ops-kubernetes.

## Questions for vendors
Purchase minimums per site, renewal policy, hardware support period, firmware compatibility matrix, part replacement
time at an edge site, VM export to open formats.
