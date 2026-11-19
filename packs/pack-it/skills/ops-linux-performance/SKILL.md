---
name: ops-linux-performance
description: Use for Linux performance — the USE method, perf, flame graphs, eBPF, memory, disk, kernel tuning and cgroups.
metadata:
  review: "2027-04-17"
  visibility: name
  catalog: "Use when investigating the performance of a Linux system and tuning it — methodology (USE, RED), the first-minute checklist, CPU profiling (perf, flame graphs), eBPF (bcc, bpftrace), memory (page cache, swap, OOM, NUMA, huge pages), disk (schedulers, latency, fio), the basics of the network stack and sysctl, cgroups v2, the process of changing kernel parameters, the safety of tracing tools. The result is a performance investigation report. Not for diagnosing service failures, DNS and TLS (ops-linux-networking), metrics and alerts (ops-observability), bugs in code (eng-debugging) or requests and limits in Kubernetes (ops-kubernetes)."
  keywords: "wolny serwer, serwer zwalnia, serwer muli, pierwsza diagnoza wydajności, obciążenie serwera, wolny serwer, wysokie obciążenie, load average, cpu 100%, flame graph, perf, ebpf, bpftrace, oom killer, swap, page cache, numa, huge pages, iowait, fio, scheduler dyskowy, sysctl, tuning jądra, cgroups, opóźnienia dysku, wąskie gardło, profilowanie, slow server, server slowing down, server is sluggish, first performance diagnosis, server load, high load, disk scheduler, kernel tuning, disk latency, bottleneck, profiling"
---

# Linux performance: investigation and tuning

The result: **a performance investigation report** (the symptom, the method, the measurements, the bottleneck, the recommendation, the result after the change).
Measurement is read-only; a change of a kernel parameter or a limit in production only as a plan (the state before, the change,
a test, a rollback) and with a human's consent. Service failures, DNS, TLS and host tools (ss, dig, curl): ops-linux-networking.
Metrics and alerts over time: ops-observability. A bug in the code's logic: eng-debugging. Pod requests/limits: ops-kubernetes.

## Methodology first
- **USE** (B. Gregg): for every resource (CPU, memory, disk, network, also queues and locks) check
  **utilization**, **saturation** (a queue, waiting) and **errors**. Start with errors
  and saturation — they are easier to interpret. Record which resources you ruled out.
- **RED** for services: the request rate (Rate), errors (Errors), duration (Duration, percentiles, not the average).
  RED tells you **that** the service is suffering; USE tells you **which resource** is the cause.
- Do not guess and do not start with the tool you know ("street light"). First the question: what is slow, since when,
  what changed, what is the goal (SLO).

## The first minute (the Netflix/Gregg list, 10 commands)
`uptime` (load: the 1/5/15 min trend) → `dmesg -T | tail` (OOM, disk errors, throttling) → `vmstat 1` (the `r` queue,
swap `si/so`, `wa`) → `mpstat -P ALL 1` (one hot core = a single-threaded thread) → `pidstat 1` (who eats the CPU)
→ `iostat -xz 1` (`await`/`aqu-sz`, `%util` reliable mainly for a single disk) → `free -m` (cache vs
available) → `sar -n DEV 1` (throughput) → `sar -n TCP,ETCP 1` (retransmits) → `top`. Requires the
`sysstat` package. Additionally `cat /proc/pressure/{cpu,memory,io}` (PSI: time spent waiting for a resource, also per cgroup).

## CPU profiling
1. `perf top` / `perf record -F 99 -g -p <pid> -- sleep 30` (sampling at ~99 Hz, usually low overhead), then
   `perf report`. Symbols require debug information or frames (Java, Node: frame pointer options/symbol maps).
2. **A flame graph** from perf data (`stackcollapse-perf.pl | flamegraph.pl`, B. Gregg's tools): width = share
   of time, you look for wide "plateaus". Compare two graphs (before/after, healthy/sick — a differential flame graph).
3. Time off the CPU (locks, I/O, sleep): an off-CPU flame graph (eBPF), not perf CPU.

## eBPF (bcc, bpftrace)
One-liners instead of guessing: `biolatency` (a histogram of disk latency), `biosnoop`, `execsnoop` (short-lived processes),
`opensnoop`, `tcpretrans`, `tcplife`, `runqlat` (latency in the CPU run queue), `cachestat`, `offcputime`, `profile`;
`bpftrace -e` for your own probes. Tool names and availability depend on the package (`bcc-tools`, `bpftrace`) and the kernel
[check `ls /usr/share/bcc/tools`]. They require root/CAP_BPF privileges.

## Memory, disk, network, cgroups
- **Memory**: `available` in `free` matters more than "free"; the page cache is reclaimable. Swapping
  (`si/so` persistently > 0) and `dmesg | grep -i oom` (the OOM killer: who, why, a cgroup limit or the system). NUMA:
  `numactl -H`, `numastat` (remote memory, unbalanced nodes). Huge pages: Transparent Huge Pages is sometimes the source
  of latency spikes in databases — change it only according to the database vendor's recommendations and with a measurement.
- **Disk**: look at latency and the queue (`await`, `aqu-sz`, `biolatency` — percentiles), not just MB/s. Choose the scheduler
  (`none`, `mq-deadline`, `kyber`, `bfq`) for the device: NVMe usually `none`; a change only after a test.
  A `fio` benchmark on **a copy/ a test environment**, never on a production volume under traffic; the result depends
  on `direct=1`, `bs`, `iodepth`, `rw`, a profile close to the application's.
- **Network (the host stack)**: `ss -ti` (rtt, cwnd, retrans), `nstat`, `ethtool -S` (drops on the NICs), `sar -n`. You change sysctl
  (`net.core.somaxconn`, `tcp_rmem/wmem`, `tcp_congestion_control`) when a measurement shows a specific symptom
  (e.g. an overflowing accept queue), not according to a list from the internet. The network fabric: ops-datacenter-networking.
- **cgroups v2**: limits and metrics in `/sys/fs/cgroup/<group>/` (`cpu.max`, `cpu.stat` → `nr_throttled`,
  `memory.max`, `memory.events` → `oom_kill`, `io.max`, `*.pressure`). A common symptom: CPU throttling despite free
  host cores, or a container OOM below the host's memory. The values in Kubernetes: ops-kubernetes.

## The process of changing a parameter (without cargo cult)
1. **Measure** the baseline (the same metrics and load, repeated ≥3 times, values recorded).
2. **A hypothesis**: "parameter X will reduce Y, because of mechanism Z".
3. **One change at a time**, temporarily (`sysctl -w`), with a rollback ready.
4. **Measure again** under the same conditions; an improvement smaller than the noise = no effect.
5. **Document** (the value, the reason, the measurement before/after, the kernel version) and persist it in code (IaC, `/etc/sysctl.d/`),
   not by hand on the server. Revert changes with no effect. Kernel parameters from the security baseline (CIS) stay —
   host hardening is described by ops-security-operations.

## The safety of tracing tools
Overhead: `perf record` by sampling — low; `strace` — high (it slows the process down many times over), `tcpdump`/`bpftrace`
with a probe on every event — potentially high. Rules: sampling tools first, briefly (10–30 s), one
machine or a canary instance, output to a file in `/tmp` with clean-up, the data may contain sensitive arguments
and content. With a human's consent in production; core-agent-security for commands from the internet.

## Example
**Input:** the `/search` API p99 2.4 s (RED), p50 stable; `app-2`.
**Investigation:** `uptime` load 14 on 8 cores; `vmstat 1` `r`=16, `wa`=0 → CPU saturation; `mpstat` even;
`pidstat` → `search-worker` 780%; `perf record -F 99 -g` + a flame graph → 41% in `regex_compile` [example].
**The report's result:** the cause — compiling the expression on every request; the recommendation: a cache of the compiled
pattern (a code change, a test, a deployment through ops-ci-cd); the measurement after the change p99 < 300 ms [example]. No sysctl changes.

## Checklist
- [ ] the symptom, the scope and the goal (SLO) recorded; RED for the service, USE for the resources
- [ ] the first-minute list done, the ruled-out resources noted
- [ ] the conclusion based on a measurement (perf/flame graph/eBPF), not on a hunch
- [ ] a parameter change: measurement → hypothesis → one change → measurement → documentation
- [ ] low-overhead tracing tools, briefly, with consent in production
- [ ] the report: the cause, the evidence, the recommendation, the result after the change

## Sources
- B. Gregg — The USE Method (brendangregg.com/usemethod.html) and the Netflix TechBlog, "Linux Performance Analysis in 60,000 Milliseconds" (2015; the 10 commands confirmed by a search on 2026-10-17)
- Linux kernel documentation — PSI, Pressure Stall Information (docs.kernel.org/accounting/psi, accessed 2026-10-17); cgroup v2 (docs.kernel.org/admin-guide/cgroup-v2) — files and fields [unverified]
- The names of the bcc/bpftrace tools, the default schedulers and the THP recommendations — own knowledge, not rechecked [unverified]
Described in our own words.
