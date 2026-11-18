# Cluster sizing — formulas

Contents: Capacity after a failure · Storage · Table template

## Capacity after a failure (N+1)
- Usable cores = (N − 1) × cores per node; usable memory = (N − 1) × node RAM × (1 − host reserve ~10–15%) [example].
- vCPU:core ratio = total vCPU / usable cores. The limit depends on the workload; verify CPU ready/steal.
- Hyperthreading does not double the cores; licences usually count physical cores.

## Storage
- Usable capacity: replication ×3 → raw/3; RAID 6 with n disks → (n−2)/n; EC k+m → k/(k+m).
- Headroom for rebuilds and the performance drop after a disk/node failure; in Ceph a pool should not exceed ~80% [example],
  so that the rebuild after a node failure fits.
- Throughput (MB/s) = IOPS × block size; concurrency = throughput × latency.

## Table template
| resource | requirement (p95) | calculation | with N+1 and headroom | notes |
|---|---|---|---|---|
| vCPU | | | | |
| RAM | | | | |
| IOPS / p99 latency | | | | |
| usable capacity | | | | |
| network (storage, migration, VM) | | | | |
