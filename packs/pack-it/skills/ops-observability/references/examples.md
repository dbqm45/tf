# Observability examples

> **Contents:** 1. SLO alerts for a new service · 2. Disk and certificates — an alert from the trend · 3. A log you can search and link to a trace

The application metric names (`http_requests_total`, `http_request_duration_seconds`) are examples — use the ones
your library exports. The thresholds are values from an example SLO.

## 1. SLO alerts for a new service
**Situation:** "Add alerts for `checkout-api`. SLO: 99.5% of requests without a 5xx error and p95 below 500 ms."

**How:**
1. Alert on symptoms from the SLO (error rate, p95), not on CPU or pod restarts.
2. RED metrics per endpoint, low-cardinality labels (`route`, not the full URL).
3. Every alert: a threshold, a duration (`for`), an owner, a link to the runbook.
4. Check that someone will handle the alert — otherwise do not add it.

**Result:** `alerts/checkout-api.yml`
```yaml
groups:
  - name: checkout-api-slo
    rules:
      - alert: CheckoutApiHighErrorRate
        expr: |
          sum(rate(http_requests_total{service="checkout-api", status=~"5.."}[5m]))
            /
          sum(rate(http_requests_total{service="checkout-api"}[5m]))
            > 0.005
        for: 10m
        labels:
          severity: page
          team: checkout
        annotations:
          summary: "checkout-api: over 0.5% of responses 5xx for 10 min"
          runbook_url: https://wiki.acme.example/runbooks/checkout-api#5xx-errors
      - alert: CheckoutApiSlowP95
        expr: |
          histogram_quantile(0.95,
            sum by (le, route) (rate(http_request_duration_seconds_bucket{service="checkout-api"}[5m]))
          ) > 0.5
        for: 15m
        labels:
          severity: ticket
          team: checkout
        annotations:
          summary: "checkout-api {{ $labels.route }}: p95 above 500 ms for 15 min"
          runbook_url: https://wiki.acme.example/runbooks/checkout-api#latency
```
On the dashboard the same queries plus deployment annotations — a "before / after" comparison in the first minutes of a release.

## 2. Disk and certificates — an alert from the trend
**Situation:** Last month the database stopped because a volume filled up, and a week later the certificate of an
internal webhook expired. Both problems grew for weeks.

**How:**
1. Disk: an 80% threshold as a warning and a `predict_linear` forecast for one day as an alert; inodes separately.
2. Certificates: an independent measurement from outside (blackbox_exporter), thresholds of 21 and 7 days — also for internal certificates.
3. A runbook and an owner on every rule.

**Result:** `alerts/slow-growth.yml`
```yaml
groups:
  - name: slow-growth
    rules:
      - alert: FilesystemFullIn24h
        expr: predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[6h], 24*3600) < 0
        for: 30m
        labels:
          severity: page
          team: platform
        annotations:
          summary: "{{ $labels.instance }} {{ $labels.mountpoint }}: the disk will fill up within a day"
          runbook_url: https://wiki.acme.example/runbooks/disk-full
      - alert: FilesystemInodesLow
        expr: node_filesystem_files_free{fstype!~"tmpfs|overlay"} / node_filesystem_files < 0.10
        for: 30m
        labels:
          severity: ticket
          team: platform
        annotations:
          summary: "{{ $labels.instance }} {{ $labels.mountpoint }}: less than 10% free inodes"
          runbook_url: https://wiki.acme.example/runbooks/disk-full#inodes
      - alert: CertExpiresIn21Days
        expr: probe_ssl_earliest_cert_expiry - time() < 21*86400
        for: 1h
        labels:
          severity: ticket
          team: platform
        annotations:
          summary: "{{ $labels.instance }}: the certificate expires in less than 21 days"
          runbook_url: https://wiki.acme.example/runbooks/tls-renewal
      - alert: CertExpiresIn7Days
        expr: probe_ssl_earliest_cert_expiry - time() < 7*86400
        for: 1h
        labels:
          severity: page
          team: platform
        annotations:
          summary: "{{ $labels.instance }}: the certificate expires in less than 7 days — the renewal automation failed"
          runbook_url: https://wiki.acme.example/runbooks/tls-renewal
```
The blackbox_exporter target list also covers Kubernetes webhooks, the database and the queue with mTLS, not just public domains.

## 3. A log you can search and link to a trace
**Situation:** During an incident it was impossible to find the failed payments: the logs were sentences of text, the same error was written
three times at different levels of the stack, and one of them contained a full token.

**How:**
1. One JSON object per event with `timestamp`, `level`, `message`, `service`, `trace_id` and context.
2. An error logged once — where it is handled, not in the repository, the service and the controller.
3. The token and personal data masked; `user_id` in the log yes, but not as a metric label.
4. `trace_id` from the OpenTelemetry context, to go from the log to the trace.

**Result:** before (three lines, one with a secret):
```text
ERROR PaymentRepository: payment failed
ERROR PaymentService: payment failed for user john.smith@example.com token=tok_live_8f3a…
ERROR PaymentController: Error: payment failed
```
after (one line):
```json
{"timestamp": "2026-10-05T10:14:52.120Z", "level": "error", "message": "payment authorization declined", "service": "checkout-api", "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736", "route": "POST /payments", "user_id": "u_18842", "provider": "acquirer-a", "reason": "insufficient_funds", "card": "**** 4242", "duration_ms": 812}
```
The query during an incident: `level="error" AND service="checkout-api" AND reason="insufficient_funds"`, and from `trace_id`
straight to the trace, which will show in which external call the 812 ms were spent.
