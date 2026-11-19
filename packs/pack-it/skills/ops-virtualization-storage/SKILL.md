---
name: ops-virtualization-storage
description: Use for on-premises and edge infrastructure — hypervisor, cluster, SAN/NAS/Ceph, RAID, backups, hardware lifecycle, edge.
metadata:
  review: "2027-04-17"
  catalog: "Use for designing infrastructure in a server room or at the edge — choosing a hypervisor (KVM with libvirt and QEMU, Proxmox VE, VMware vSphere taking into account the licensing changes after the Broadcom acquisition), cluster size (CPU and memory overcommit, N+1, HA, live migration, quorum), storage architecture (SAN FC and iSCSI, NAS NFS and SMB, Ceph), RAID and erasure coding, IOPS, throughput, latency and queue depth, snapshots vs backups, the 3-2-1 rule, immutability, hardware lifecycle (refresh, spare parts, firmware), capacity planning, edge constraints, migration between hypervisors. The output is a design with a sizing table. Not for recovery after a region failure and DR strategy (ops-multi-region-resilience), backups in the context of incidents and SLOs (ops-sre-incidents), I/O tuning in the operating system (ops-linux-performance) or container orchestration (ops-kubernetes)."
  keywords: "hiperwizor, wirtualizacja, KVM, libvirt, QEMU, Proxmox, VMware, vSphere, ESXi, Broadcom, licencje VMware, migracja z VMware, klaster, overcommit, nadsubskrypcja, HA, live migration, vMotion, SAN, iSCSI, Fibre Channel, NAS, NFS, SMB, Ceph, storage, macierz, RAID, RAID 6, erasure coding, IOPS, przepustowość, opóźnienie dysku, głębokość kolejki, migawka, snapshot, backup, 3-2-1, niezmienialna kopia, serwerownia, on-premise, odświeżanie sprzętu, części zapasowe, firmware, pojemność, edge, sklep, oddział, zdalne zarządzanie, iDRAC, iLO, wymiarowanie klastra, hypervisor, virtualization, VMware licences, migration from VMware, cluster, oversubscription, storage array, throughput, disk latency, queue depth, immutable backup, server room, hardware refresh, spare parts, capacity, store, branch, remote management, cluster sizing"
  visibility: name
---

# Virtualization, storage and hardware (server room and edge)

Output: **an infrastructure design with a sizing table** (template below). For changes to running infrastructure
the agent only proposes a plan (change window, order, rollback, dry-run where the tool has one);
a human executes them, or the agent with the human's explicit consent. Recovery after a site failure: **ops-multi-region-resilience**;
the role of backups in incidents and RPO/RTO: **ops-sre-incidents**; I/O in the kernel and the file system: **ops-linux-performance**;
containers: **ops-kubernetes** (you count Kubernetes nodes on virtual machines here like any other workload).

## Procedure
1. **Workloads and requirements.** An inventory of VMs/services: vCPU, RAM, disk, I/O profile (random or sequential, read/write,
   block size), RPO/RTO, dependencies, core-based licences (databases, Windows Server). Without a measurement from the current
   environment (p95 over 30 days, not the average) the numbers below are guesswork.
2. **Hypervisor** — chosen by criteria, not by brand:
   - **KVM + libvirt/QEMU**: the Linux kernel, the most freedom, you build management and HA yourself (Pacemaker, Ansible).
   - **Proxmox VE**: KVM and LXC with web management, clustering, HA, Ceph and ZFS in the package; AGPL licence, the support
     is paid (subscription). Versions: `references/hypervisors-and-storage.md`.
   - **VMware vSphere**: a mature ecosystem (DRS, vSAN, NSX), but after the Broadcom acquisition the licensing changed
     (subscription instead of perpetual, per-core billing, purchase minimums) — **check the terms in the current offer
     and contract, not from memory** [unverified: details of minimums and renewals, reseller reports from 2025-04].
   - Decision: the team's skills, support from the application vendor (certification for the hypervisor), 5-year cost (licences
     + support + people), lock-in risk. For small sites, count the purchase minimums per site.
3. **Cluster sizing** (table and formulas in `references/sizing.md`):
   - **Capacity after a failure**: design for **N+1** (loss of one node, with HA without exceeding limits);
     for large clusters N+2. Do not count nodes "to the limit" — HA starts VMs only where there is free memory.
   - **CPU**: the ratio of vCPU to physical cores depends on the workload; the starting point is the values [example]
     2:1–4:1 for general services, 1:1 for latency-sensitive workloads and databases, and **you verify it by measuring CPU
     ready time (CPU ready/steal)**, not by a rule of thumb.
   - **Memory**: no overcommit for databases and critical workloads; ballooning and host swap are an exception, not a plan.
   - **Live migration** needs shared storage or disk copying, a consistent CPU family (a common CPU model
     in the cluster) and a migration network separate from VM traffic.
   - **Quorum**: a cluster needs a majority of votes; 2 nodes need a third vote (QDevice, witness), otherwise
     the failure of one node stops the cluster. The recommended start is 3 nodes.
   - Network: separate VLANs or interfaces for management, migration, storage and VM traffic; 25 GbE for distributed
     storage [example], redundant paths (LACP/MLAG, MPIO for iSCSI/FC).
4. **Storage** — choosing the architecture:

   | Requirement | Choice | Note |
   |---|---|---|
   | low-latency shared blocks | SAN (FC or iSCSI) | FC: a dedicated network, expensive, predictable; iSCSI over Ethernet: cheaper, needs isolation and MPIO |
   | files for many clients | NAS (NFS for Linux/VMs, SMB for Windows) | watch out for locks, permissions and a single head |
   | horizontal scaling without an array | software-defined storage (Ceph, vSAN) | minimum 3 nodes, network and disks with consistent sizing |
   | a single host or edge | local ZFS/LVM, asynchronous replication | simplicity over HA |

   Ceph: by default replication ×3 with `min_size` 2; an erasure coding k+m pool saves space at the cost of latency and
   rebuild overhead, needs at least k+m failure domains [unverified: version requirements — check
   the documentation of the release in use].
5. **RAID and erasure coding** — for large disks (≥ 10 TB) a rebuild takes hours to days, and during that time the cluster is
   vulnerable to a second failure and a read error (URE):
   - RAID 5 on large disks: avoid it for data whose loss hurts; **RAID 6 or RAID 10** (10: faster writes and
     rebuild, 50% capacity); RAID 0 only for temporary data.
   - Writes in RAID 5/6 have a penalty (read-modify-write: approx. 4 and 6 operations per write [example, a controller with cache reduces it]).
   - Erasure coding: lower capacity overhead (e.g. k=4, m=2 → 1.5× instead of 3×), but more expensive reads/writes of small
     blocks and rebuilds — for archival and object workloads, less often for databases.
   - RAID is not a backup: it protects against a disk failure, not against deletion, an application bug or ransomware.
6. **Performance.** Size on three axes: **IOPS**, **throughput** (IOPS × block size) and **latency**
   (p95/p99). Queue depth links them through Little's law (concurrency = throughput × latency): without
   parallelism an NVMe SSD will not reach its specification. Measure under a realistic load (fio with the application's profile),
   leave ~30% headroom for rebuilds and peaks. Tuning on the OS side: **ops-linux-performance**.
7. **Data protection.** **A snapshot is not a backup** — it sits on the same storage and disappears with it. A backup:
   the **3-2-1** rule (3 copies, 2 different media, 1 off-site; the 3-2-1-1-0 extension is a vendor
   convention: +1 immutable/offline, 0 errors after a restore test). At least one **immutable** copy
   (Object Lock/WORM, tape, offline) with credentials separate from production. A backup counts after a **restore test**
   with timing. RPO/RTO and incidents: **ops-sre-incidents**.
8. **Hardware lifecycle and capacity.** An asset register: model, purchase date, end of warranty and support, firmware
   version, required replacements. The refresh cycle is typically 4–6 years [example — depends on vendor support and
   depreciation]; spare parts on site (disks, power supplies, fans, optics) and an SLA contract for replacement. You update firmware
   in change windows, node by node, first in a test environment; you check BIOS/HBA/disk compatibility with the hypervisor
   in the vendor's compatibility matrix. A capacity forecast from the usage trend: an alert at ~70–80% pool utilization
   (hardware lead time is sometimes longer than the time until the pool fills up).
9. **Edge.** Assumptions: the link is sometimes unavailable, nobody is on site, space and power are scarce.
   - **Autonomous** operation without connectivity (local DNS, authentication, data queuing), synchronization when it comes back.
   - **Out-of-band remote management** (BMC: iDRAC, iLO, Redfish), zero-touch provisioning, centrally approved images.
   - Small clusters: 1 node + fast replacement, 2 nodes + a witness, 3 nodes for HA. A spare node sent by courier is sometimes
     cheaper than a third node at every site.
   - You manage the fleet as code, updates in waves (canaries), telemetry through a local buffer
     (**ops-observability**). Containers at the edge: **ops-kubernetes**.
10. **Migration between hypervisors.** An inventory of VMs and dependencies, a pilot on a non-critical VM, disk conversion
    (qcow2, VMDK, VHDX), virtual drivers (virtio), changes of network cards and MAC addresses, licences tied to
    hardware, backup and monitoring agents, a cutover window, **a rollback plan** (the old environment runs in parallel
    until acceptance). Waves from the least to the most critical.
11. **Output** — template:
    ```
    # Infrastructure design: <name>
    Assumptions: workloads, RPO/RTO, budget, horizon
    Sizing table: | resource | requirement | calculation | with N+1 headroom | notes |
    Decisions: hypervisor, storage, RAID/EC, network, backups (with justification and rejected options)
    Risks and pitfalls | Deployment and rollback plan | To be confirmed by a human
    ```

## Example
Input: 3 nodes, each with 2×16 cores and 512 GB RAM; 60 VMs (180 vCPU, 700 GB RAM in total) [example].
Output: after losing a node, 64 cores and 1024 GB remain. Memory: 700 GB < 1024 GB, and even with 15% headroom (805 GB) it
fits; CPU: 180/64 = 2.8:1 — acceptable for general services, not for databases. Decision: 3 nodes, Ceph ×3 on NVMe, a 25 GbE
network, databases pinned at 1:1; backups to a separate server with an immutable off-site copy and a restore test
every quarter.

## Checklist
- [ ] workloads measured (p95), not estimated
- [ ] capacity calculated after a node failure (N+1), quorum ensured
- [ ] CPU and memory: overcommit verified with a metric, not a rule of thumb
- [ ] licence terms checked in the current offer (VMware) and the 5-year cost
- [ ] RAID/EC matched to disk size and rebuild time
- [ ] IOPS, throughput and p99 latency calculated, headroom for rebuilds
- [ ] 3-2-1, an immutable copy, a timed restore test
- [ ] hardware register, firmware, spare parts, capacity forecast
- [ ] edge: offline operation, remote management, spare hardware
- [ ] migration with a rollback plan; changes only with a human's consent

## Sources
- Proxmox VE: [Release notes and roadmap](https://pve.proxmox.com/wiki/Roadmap) — a search in 2026-10 found release 9.1 (Debian 13, Ceph Squid 19.2.3); [unverified] whether there is a newer one.
- Ceph: [docs.ceph.com — releases](https://docs.ceph.com/en/latest/releases/) — Tentacle 20.2.x active, Squid 19.2.x with an estimated end of support in 2026-09 or 2026-10 (sources differ) [unverified].
- VMware/Broadcom: reports of a minimum of 72 cores per purchase and 16 cores per processor (from 2025-04, [Techzine](https://techzine.eu/news/infrastructure/130027/broadcom-raises-minimum-requirement-for-vmware-licenses-from-16-to-72-cores)) — secondary sources, [unverified] against Broadcom's terms.
- The 3-2-1 rule: CISA, [Data Backup Options](https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf) [unverified: current status].
