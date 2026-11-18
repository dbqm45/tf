# Web servers, proxies and load balancing

## Roles
| Element | What it does | Typical tools |
|---|---|---|
| **reverse proxy** | accepts traffic from clients and passes it to the application: TLS, compression, limits, routing by path or host | nginx, Caddy, Envoy, HAProxy, Traefik, Ingress / Gateway API in Kubernetes |
| **L4 load balancer** | distributes TCP/UDP connections, does not look into HTTP | NLB, HAProxy in TCP mode |
| **L7 load balancer** | distributes HTTP requests, knows paths, headers, cookies | ALB, Application Gateway, nginx, Envoy |
| **forward proxy** | **outbound** traffic from the network goes through the proxy: a domain allowlist, a log, a package cache | Squid, cloud proxies, NAT gateways with a filter |
| **cache server** | stores HTTP responses in front of the application | CDN, Varnish, `proxy_cache` in nginx |
| **application server** | runs the code | Node, Tomcat, Kestrel/IIS; behind a reverse proxy, not directly from the internet |

## Reverse proxy configuration — what to remember
- **TLS** terminated at the proxy or the load balancer, an HTTP→HTTPS redirect, HSTS (be-auth-security,
  `api-security-checklist.md`). Caddy issues and renews certificates automatically; in nginx — certbot or
  cert-manager.
- **Headers from the proxy**: `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host` (or the standard `Forwarded`).
  The application trusts them **only** from known proxies (e.g. `trust proxy` in Express, `server.forward-headers-strategy`
  in Spring Boot) — otherwise a client will spoof any IP address and bypass the rate limits.
- **Timeouts** consistent along the chain: client → load balancer → proxy → application → database. The timeout of the higher level
  longer than that of the lower one, otherwise the proxy drops the connection while the application keeps working (`proxy_read_timeout`,
  `proxy_connect_timeout` in nginx).
- **Request size** (`client_max_body_size` in nginx) consistent with the limit in the application; larger files through a signed URL
  to the object store.
- **SSE and streaming**: response buffering disabled for these routes (`proxy_buffering off` or the
  `X-Accel-Buffering: no` header) and a long read timeout. **WebSocket**: passing the `Upgrade` and `Connection` headers.
- **Compression** at the proxy (gzip or Brotli), if the application does not do it — in one place, not in two.
- Hide the server version (`server_tokens off`), no directory listing, separate access logs with a request identifier
  passed to the application (ops-observability).

## Load balancing
- Algorithms: round robin (simple, equal requests), least connections (requests of different cost), hash (affinity,
  e.g. a cache per key). Sticky sessions only when you must — they make scaling and deployments harder; better sessions outside the process.
- Health probes check readiness (`/health/ready`), not just whether the port is open; an instance is withdrawn
  gracefully (connection draining) during a deployment.
- A service mesh (Istio, Linkerd, including sidecarless modes): mTLS, retries, traffic splitting and telemetry between
  services without code changes — at the cost of operational complexity. Usually only with many services and teams;
  before that, libraries and the Gateway API are enough (ops-kubernetes).

## Outbound proxies
- Applications and CI go out to the internet through a proxy or a gateway with a domain allowlist (package registries, partner APIs).
  This makes data exfiltration and malicious code's contact with the attacker's server harder (ops-supply-chain-security).
- An artifact repository (Artifactory, Nexus, a cloud registry) as an intermediary for npm, Maven and images: a cache,
  one point of control, the option to quarantine new versions.

## Sources
- The nginx (`ngx_http_proxy_module`), Caddy, Envoy, Kubernetes Gateway API documentation
- [roadmap.sh — DevOps](https://roadmap.sh/devops) (web servers, reverse proxy, forward proxy, caching server,
  load balancer, service mesh, artifact management)
Described in our own words.
