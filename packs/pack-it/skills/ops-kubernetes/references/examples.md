# Kubernetes examples

> **Contents:** 1. A production Deployment with a PDB · 2. NetworkPolicy and RBAC for a new service · 3. A "successful" deployment, the application fails — a…

The names, numbers and registry are illustrative. Take requests values from real usage (metrics from recent weeks),
not from these examples.

## 1. A production Deployment with a PDB
**Situation:** "Write a manifest for `orders-api` for production. It starts in approx. 40 s, usually uses 300m CPU and 380 MiB
of memory, and does not talk to the Kubernetes API."

**How:**
1. requests from real usage, a memory limit with headroom, no CPU limit (you avoid throttling).
2. readiness and liveness on different endpoints; liveness without dependencies; `startupProbe` for the slow start.
3. 3 replicas, `RollingUpdate` with `maxUnavailable: 0`, a separate `PodDisruptionBudget`.
4. The image pinned to a digest; `securityContext` compliant with the `restricted` profile; `automountServiceAccountToken: false`.
5. `terminationGracePeriodSeconds` longer than the longest request (here 30 s).

**Result:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orders
  labels:
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: orders
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: orders-api
  template:
    metadata:
      labels:
        app: orders-api
    spec:
      serviceAccountName: orders-api
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 45
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: app
          image: registry.acme.example/orders-api@sha256:<digest>
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 300m
              memory: 400Mi
            limits:
              memory: 512Mi
          startupProbe:
            httpGet:
              path: /health/live
              port: 8080
            periodSeconds: 5
            failureThreshold: 12
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            periodSeconds: 10
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: orders-api
  namespace: orders
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app: orders-api
```
`startupProbe` gives up to 60 s (12 × 5 s) for startup before liveness starts working. Validation: `kubeconform`, then the change
through GitOps — the agent does not do `kubectl apply` on a shared cluster.

## 2. NetworkPolicy and RBAC for a new service
**Situation:** The `orders-admin` service is to accept traffic only from the ingress controller, connect to the `orders-db` database
on 5432 and read one ConfigMap through the Kubernetes API (which is why, unlike in example 1, it mounts the token).

**How:**
1. First a policy denying traffic in both directions in the namespace by default (check whether the CNI enforces NetworkPolicy).
2. Explicit allows: ingress from the ingress namespace, egress to the database and DNS — nothing more, so the cloud metadata is cut off too.
3. One service account, a Role in the namespace with a specific resource and verbs, no `*`.

**Result:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: orders
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orders-admin
  namespace: orders
spec:
  podSelector:
    matchLabels:
      app: orders-admin
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: orders-db
      ports:
        - port: 5432
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-admin
  namespace: orders
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: orders-admin-config-reader
  namespace: orders
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["orders-feature-flags"]
    verbs: ["get", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: orders-admin-config-reader
  namespace: orders
subjects:
  - kind: ServiceAccount
    name: orders-admin
    namespace: orders
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: orders-admin-config-reader
```
Traffic to the Kubernetes API needs a separate egress rule (the API server address depends on the cluster) — add it deliberately,
after checking the address.

## 3. A "successful" deployment, the application fails — a stale ConfigMap
**Situation:** After deploying `orders-api` version 2.4 all pods are `Running`, but the first payments end with
error 500. Log: `PAYMENTS_API_URL is not set`.

**How:**
1. Compare the variables expected by the new version with the ConfigMap in the GitOps repository — the new value is not there.
2. Cause: the code was changed in one PR, someone was to add the configuration "later"; an unchanged ConfigMap does not force a rollout.
3. Fix: a ConfigMap generated by Kustomize (a name with a hash suffix) in the same PR as the code.
4. Safeguard: the application validates its configuration at startup and does not report readiness when a value is missing —
   next time the rolling update stops at the first pod.

**Result:** `kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: orders
resources:
  - deployment.yaml
configMapGenerator:
  - name: orders-api-config
    literals:
      - PAYMENTS_API_URL=https://payments.internal.acme.example
      - ORDERS_TIMEOUT_MS=3000
```
In the Deployment: `envFrom: [{configMapRef: {name: orders-api-config}}]` — Kustomize replaces the name with
`orders-api-config-<hash>`, so every value change changes the pod template and triggers a new rollout.
