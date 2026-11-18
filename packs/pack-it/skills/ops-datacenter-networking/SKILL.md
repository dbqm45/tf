---
name: ops-datacenter-networking
description: Use for data center networking — leaf-spine fabric, BGP, VXLAN and EVPN, network automation and changes.
metadata:
  review: "2027-04-17"
  visibility: name
  catalog: "Use for the design of and changes to a data center or campus network — the leaf-spine (Clos) fabric and oversubscription, underlay (eBGP, OSPF, IS-IS), VXLAN overlay with EVPN, BGP for operators (route selection, communities, filters, prefix limits, RPKI), ECMP and failure domains, automation (source of truth, configuration generation, CI, change windows), edge firewalls, telemetry, capacity planning, a diagnosis method. The result is a fabric design and a change plan. Not for diagnosing a Linux host (ops-linux-networking), segmentation and trust policy (sec-zero-trust-identity) or cloud networking as code."
  keywords: "leaf spine, fabryka sieciowa, centrum danych, datacenter, bgp, vxlan, evpn, underlay, overlay, ecmp, oversubscription, przełączniki, switch, router, netbox, automatyzacja sieci, okno zmian, rpki, prefix list, telemetria sieciowa, pojemność łączy, firewall brzegowy, sieć kampusowa, network fabric, data center, switches, network automation, change window, network telemetry, link capacity, edge firewall, campus network"
---

# Data center networking: the fabric design and the change plan

Result: **a fabric design** (topology, addressing, routing, overlay, failure domains) and **a change plan** (steps, verification,
rollback). The agent only proposes changes on real devices: a configuration diff, a dry-run and a change window,
deployment after a human's consent. Diagnosing a single host (ss, dig, curl, TLS): ops-linux-networking.
Segmentation policy (who talks to whom): sec-zero-trust-identity.

## Design procedure
1. **Requirements**: the number of racks and servers, port speed (e.g. 2x25G), east-west vs north-south traffic,
   the target scale in 3 years, availability targets (ops-sre-incidents), L2 requirements (VM migration, legacy).
2. **Leaf-spine (Clos) topology**: every leaf connects to every spine; servers only to leaves. You compute
   **oversubscription** = the sum of the leaf's server port bandwidth ÷ the sum of uplink bandwidth [example: 48x25G down,
   6x100G up → 1200:600 = 2:1]. You choose the target value for the workload (storage and AI: 1:1; general: 2:1–3:1
   [assumption]). The number of spines = the number of leaf uplinks; scaling: adding a spine or a tier (pod/super-spine).
3. **Underlay**: routed L3 to the rack, no stretching of L2 between leaves. By default **eBGP** with a unique ASN
   per leaf (or per pair) and a shared spine ASN, per RFC 7938 (Informational, 2016) — it has a simpler model
   than IGP+iBGP and good filtering. Alternative: OSPF or IS-IS (smaller scales, the team knows IGP), then BGP
   only for the overlay. Sessions on link addresses (point-to-point /31 or unnumbered), BFD for fast failure detection.
4. **Overlay**: VXLAN (RFC 7348, Informational) as the encapsulation, **EVPN** (RFC 7432, the extension for overlays:
   RFC 8365) as the control plane instead of flood-and-learn. Decisions: the L2VNI/L3VNI model, anycast gateway,
   symmetric IRB, multihoming (ESI/EVPN-LAG instead of MLAG, if the hardware supports it), BUM handling, MTU
   (+50 B of VXLAN headers [unverified] — jumbo along the whole path). You do not invent VNI, RD and RT numbers by hand:
   the scheme comes from the source of truth.
5. **ECMP and failure domains**: several equal paths, hashing on the 5-tuple; uneven hashing and elephant flows are
   typical causes of unbalanced uplinks. Failure domain = what loses traffic on a failure of a leaf, a spine, a leaf
   pair, a tier, power, a configuration change. Principle: losing one spine does not exceed the bandwidth budget
   (compute N-1). Check the maximum number of paths and prefixes in the hardware specification.
6. **Edge and firewalls**: the internet/WAN link on separate border leaves, a stateful firewall between zones,
   east-west traffic in the overlay filtered by policies defined in sec-zero-trust-identity; here only the mechanics
   (VRF, route leaking with filters, service chaining).
7. **Capacity and telemetry**: uplink utilization (p95 and peak), port drops and errors, the number of routes/MACs in the tables
   vs the ASIC limit, the growth rate → the expansion date (alert at 60–70% [example]). Streaming telemetry
   (gNMI/OpenConfig, push every few seconds to tens of seconds) instead of SNMP polling where the hardware allows;
   flow logs (IPFIX/sFlow) for traffic analysis; the metrics stack: ops-observability.

## BGP for operators — the minimum
- **Route selection** (RFC 4271, in short): highest weight/local-pref → shortest AS-path → origin → lowest MED →
   eBGP before iBGP → lowest IGP cost → router-id. Check the exact order in the vendor's documentation.
- **Communities** mark origin and intent (e.g. "from the DC", "do not export"); their meaning is in the source of truth.
- **Filters always**: import and export through a prefix-list/policy; without a policy an eBGP session exchanges nothing (RFC 8212
  [unverified]). **A prefix limit** (`maximum-prefix`) on every session with a warning and a cut-off.
- **RPKI route origin validation** (RFC 6811): states Valid / Invalid / NotFound; reject Invalid on transit
  sessions, keep the ROAs for your own prefixes up to date. This concerns the internet edge, not the fabric.
- A change of BGP policy at the edge = high risk: first a before/after route comparison (`show` + diff), then a change window.

## Automation and changes
- **Source of truth** (e.g. NetBox, per the NetBox Labs documentation a system for modelling devices, connections and IPs):
  the intent in data, the configuration **generated** from templates (Jinja, Ansible, Nornir), not written by hand on the device.
- **CI for network changes**: a PR to the repo → lint of data and templates → generated configuration and diff → a test
  in emulation/a lab (Containerlab, Batfish for configuration analysis [unverified]) → review → deployment
  in waves (one leaf → a pair → a rack → the rest) with automatic state verification (BGP sessions, routes, ping between VTEPs).
- **Change window**: goal, scope, timed steps, "stop" criteria, a tested **rollback** (rollback to the last
  configuration or `commit confirmed`), the on-call contact, a freeze of other changes. An emergency change: ops-release-engineering.
- Drift: the configuration from the devices compared periodically with the source of truth; manual changes are a process incident.

## Diagnosis method
From the symptom to the layer: physical (optics, CRC errors) → link/LAG → underlay sessions → routes → overlay (VTEP, EVPN route
type 2/3/5) → policies/firewall → application. Compare with a second, healthy path; one change at a time; a timeline.
The host at the end of the path: ops-linux-networking.

## Example
**Input:** 40 racks, 2x25G per server, 20 servers per rack, mostly east-west traffic, a 3:1 target.
**Result** [example]: a leaf per rack (2 leaves in a pair), downstream 20x2x25G = 1000G per rack → 500G per leaf; uplinks
4x100G = 400G → oversubscription 1.25:1 — better than the target, so 4 spines are enough; N-1 (3 spines) → 300G = 1.67:1,
still ≤ 3:1. Underlay eBGP (RFC 7938), overlay EVPN-VXLAN, jumbo MTU 9216 [assumption]. Change plan: deployment
in waves, rollback through `commit confirmed`, verification of BGP sessions and routes after every wave.

## Checklist
- [ ] oversubscription computed and compared with the target, also in the N-1 state
- [ ] underlay justified (eBGP per RFC 7938 or IGP), BFD, no L2 between leaves
- [ ] overlay: EVPN as the control plane, MTU, multihoming, numbering from the source of truth
- [ ] BGP: import/export filters, prefix limits, RPKI at the edge
- [ ] configuration generated from the source of truth, diff and test in CI before the change window
- [ ] a change plan with waves, stop criteria and a tested rollback; deployment with a human's consent
- [ ] telemetry and capacity alerts; boundaries with neighbouring skills kept

## Sources
- IETF RFC 7938, "Use of BGP for Routing in Large-Scale Data Centers", Informational, August 2016 (datatracker.ietf.org, accessed 2026-10-17)
- IETF RFC 7348 (VXLAN, Informational, 2014; work on a successor draft-ietf-nvo3-rfc7348bis ongoing, as of 2025-12), RFC 7432 and RFC 8365 (EVPN), RFC 4271 (BGP-4), RFC 6811 (RPKI origin validation), RFC 8212 — numbers and dates without rechecking the content [unverified]
- NetBox Labs — NetBox documentation as a network source of truth (netboxlabs.com/docs, accessed 2026-10-17)
Described in our own words.
