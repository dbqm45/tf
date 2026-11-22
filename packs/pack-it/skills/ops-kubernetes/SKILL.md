---
name: ops-kubernetes
description: Use for Kubernetes manifests and operations — resources, probes, replicas and PDB, autoscaling, RBAC, NetworkPolicy, ConfigMap changes in a rollout.
metadata:
  review: "2027-04-17"
  catalog: "Use for Kubernetes manifests and operations — resources (requests/limits), probes, replica count and PodDisruptionBudget, autoscaling, pod security (Pod Security Standards, securityContext), RBAC and service accounts, NetworkPolicy, secrets, manifest validation in CI, cluster upgrades. Not for images (ops-docker), releases and GitOps (ops-release-engineering) or the cloud."
---

# Kubernetes

## 1. Every Deployment has
- CPU and memory **requests** from real usage (without them the scheduler guesses, and an HPA on CPU/memory percentage does not work);
  a **memory limit** always; a CPU limit with care — one that is too low chokes the application (throttling).
- **readinessProbe** (whether to accept traffic) and **livenessProbe** (whether to restart) — different endpoints, liveness does not
  check external dependencies, because a database failure would restart all pods. Slow start: `startupProbe`.
- At least 2 replicas for production services, a `PodDisruptionBudget` (e.g. `maxUnavailable: 1`) and a
  `RollingUpdate` strategy with a `maxUnavailable` that does not shut down all pods at once.
- The image pinned to a version or digest, never `latest` — when a pod restarts or moves, the node pulls whatever the
  tag points to **now**, and the behaviour changes without any deployment.
- Graceful shutdown: SIGTERM handling, `terminationGracePeriodSeconds` longer than the longest request.

## 2. Autoscaling
- HPA on a metric that really grows with load (CPU, requests per second, queue length — KEDA for queues
  and events). Minimum and maximum replicas set deliberately; the maximum protects against cost and database overload.
- Node autoscaling (Cluster Autoscaler, Karpenter) needs correct requests — otherwise the nodes are badly sized.

## 3. Pod security
- A namespace with the label `pod-security.kubernetes.io/enforce: restricted` (Pod Security Standards); exceptions explicit.
- `securityContext`: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`,
  `seccompProfile.type: RuntimeDefault` (required by the `restricted` profile) and `readOnlyRootFilesystem: true` (outside
  the profile — enforce it with a Kyverno or Gatekeeper policy).
- `automountServiceAccountToken: false`, if the pod does not talk to the Kubernetes API.
- **NetworkPolicy** (works only with a CNI network plugin that enforces it) denying traffic in the namespace by default, then explicit allows; egress restricted
  (also to the cloud metadata).
- RBAC: one service account per application, Role in the namespace instead of ClusterRole, no `*` in resources and verbs.
  Cloud access through workload identity (IRSA, EKS Pod Identity, Workload Identity), not through keys in secrets.
- Policies enforced at admission: Kyverno or OPA Gatekeeper — e.g. a ban on `latest`, required requests,
  only images from a trusted registry and signed (cosign).

## 4. Secrets and configuration
- Secrets through `secretKeyRef`/volumes from an external manager (External Secrets, Vault, Sealed Secrets, SOPS),
  never in plain text in the manifest or in the pipeline file. Secret encryption in etcd enabled.
- Variable names in the manifest and the application match — a mismatch ends in pods failing at startup; the application
  validates its configuration at startup (lang-typescript, the section on `process.env`).
- **Configuration is deployed together with the code.** A common "minor" mistake: the new version of the application expects a new value
  (e.g. an API address), but the ConfigMap or Secret stayed old — the pods run, the deployment looks successful, the application fails
  only on the first call. Therefore:
  - the ConfigMap and secret references go in the same PR and GitOps repository as the code change that needs them;
  - a configuration change forces a new rollout: Kustomize `configMapGenerator`/`secretGenerator` (a name with a hash
    suffix) or, in Helm, an annotation with a configuration checksum in the pod template. Environment variables from a ConfigMap do not
    refresh in a running pod;
  - the application checks the required values at startup and does not report readiness when they are missing — then
    the rolling update stops at the first pod instead of replacing all of them.

## 5. Validation in CI
`yamllint`, schema validation (`kubeconform`), `kubectl apply --dry-run=server` on a test cluster, Helm/Kustomize
lint, policy scan (Kyverno CLI, Conftest). The agent does not run `kubectl apply` on a shared cluster —
the change goes through GitOps (ops-release-engineering); the `guard_bash.py` hook asks for consent on `kubectl apply/delete`.

## 6. Cluster upgrades
Before an upgrade: the list of removed API versions (e.g. `kubent`, `pluto`), compatibility of controllers and operators, the upgrade
first in a test environment, nodes one by one while respecting PDBs.

## Example
**Situation:** `orders-api` to production; startup approx. 40 s, usage approx. 300m CPU and 380 MiB.
**Result** (key Deployment fields, nesting shortened; next to it a PDB `maxUnavailable: 1`):
```yaml
replicas: 3
image: registry.acme.example/orders-api@sha256:<digest>
resources: { requests: { cpu: 300m, memory: 400Mi }, limits: { memory: 512Mi } }
startupProbe: { httpGet: { path: /health/live, port: 8080 }, periodSeconds: 5, failureThreshold: 12 }
readinessProbe: { httpGet: { path: /health/ready, port: 8080 } }
livenessProbe: { httpGet: { path: /health/live, port: 8080 } }
securityContext: { runAsNonRoot: true, allowPrivilegeEscalation: false, capabilities: { drop: [ALL] } }
```
More examples: `references/examples.md`.

## Checklist
- [ ] requests, memory limit, readiness/liveness probes, ≥ 2 replicas and a PDB
- [ ] Pod Security `restricted`, securityContext, a default-deny NetworkPolicy
- [ ] a service account per application, minimal RBAC, workload identity instead of keys
- [ ] secrets from a manager, validation of manifests and policies in CI
- [ ] a configuration change in the same PR as the code and forcing a rollout; configuration validation at startup
- [ ] removed APIs checked before a cluster upgrade

## Sources
- [10 Minor DevOps Mistakes That Can Cause Major Production Issues](https://medium.com/coinmonks/10-minor-devops-mistakes-that-can-cause-major-production-issues-191d141e7686) — Pawan Natekar, 2026 (stale ConfigMap/Secret, `latest`, no limits)
- [Why Your Deployments Fail: A Deep Dive Into Misconfigured Pipelines](https://devops.com/why-your-deployments-fail-a-deep-dive-into-misconfigured-pipelines/) (devops.com)
- Kubernetes documentation: [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/),
  [Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/),
  [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/),
  [Specifying a Disruption Budget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)
devops.com has few practical articles on Kubernetes operations, so the skill relies mainly on the project documentation.
