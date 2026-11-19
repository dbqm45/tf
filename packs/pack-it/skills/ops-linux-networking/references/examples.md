# Linux and network diagnosis examples

All commands are read-only. Host names, addresses (from the documentation range) and results are illustrative.

## 1. "No space left on device" with free space
**Situation:** Since the morning the `ingest` service on `app-3` has not been writing files: the log shows `No space left on device`, and the dashboard
shows the disk 41% full.

**How:**
1. Scope: one host, since 6:10, no deployment — so something grew rather than changed.
2. USE for the disk: `df -h` **and** `df -i` — space is not the only file system resource.
3. Find the directory with millions of small files and the process that creates them.
4. A conclusion and a proposed change through code; deleting files only after a human's consent.

**Result:**
```bash
journalctl -u ingest --since "-2h" | tail -n 5
df -h /var
df -i /var
sudo find /var -xdev -type f -printf '%h\n' | sort | uniq -c | sort -rn | head -n 3
```
```text
Oct 05 06:10:02 app-3 ingest[2211]: write /var/lib/ingest/tmp/chunk-8812: no space left on device
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme1n1     50G   21G   30G  41% /var
Filesystem      Inodes   IUsed IFree IUse% Mounted on
/dev/nvme1n1   3276800 3276800     0  100% /var
3194022 /var/lib/ingest/tmp
   8121 /var/log/journal/4f2c
   2210 /var/lib/apt/lists
```
Conclusion: exhausted inodes, not space. `ingest` does not clean up the `chunk-*` files (3.2 million). Proposal: a clean-up
fix in the application, a clean-up task in the machine configuration (Ansible) and an alert on `node_filesystem_files_free`
(ops-observability). Deleting the old files — after a human's approval.

## 2. After a migration some clients see a certificate error
**Situation:** Yesterday `shop.acme.example` was moved to a new server. Some clients report "certificate expired",
the rest works.

**How:**
1. "Some clients" after a DNS change suggests a cache: compare the answer of the authoritative server and of a public resolver.
2. Check the record's TTL — whether it was lowered before the migration.
3. Check the certificate on **both** addresses with the correct SNI.

**Result:**
```bash
dig +short NS acme.example
dig @ns1.acme.example shop.acme.example A +noall +answer
dig @1.1.1.1 shop.acme.example A +noall +answer
for ip in 203.0.113.20 198.51.100.7; do
  echo | openssl s_client -connect "$ip:443" -servername shop.acme.example 2>/dev/null \
    | openssl x509 -noout -enddate
done
```
```text
ns1.acme.example.
ns2.acme.example.
shop.acme.example.  86400 IN A 198.51.100.7     # authoritative: the new server
shop.acme.example.  61200 IN A 203.0.113.20     # resolver: the old address still in the cache
notAfter=Oct  4 23:59:59 2026 GMT               # 203.0.113.20 (old)
notAfter=Jan  2 23:59:59 2027 GMT               # 198.51.100.7 (new)
```
Conclusion: the TTL of 86,400 s was not lowered before the migration, resolvers keep the old address for up to a day, and on the old server
the certificate has expired. As a stopgap (with consent): renew the certificate on the old server or redirect traffic from it to the new one
until the cache expires. For the future: the TTL lowered a few hours before the migration, raised after it.

## 3. Reports end with a 504 error after 60 s
**Situation:** Generating the monthly report in `reports.acme.example` returns 504 Gateway Timeout, always after about
a minute. Smaller reports work.

**How:**
1. Measure the request timings with `curl -w` — a constant time of the drop points to a limit, not to overload.
2. Check the proxy and application logs from the same minute — whether the application finishes its work after the drop.
3. Compare the timeouts in the chain: load balancer → nginx → application (`references/web-servers-and-proxies.md`).

**Result:**
```bash
curl -s -o /dev/null -w '%{http_code} %{time_connect} %{time_starttransfer} %{time_total}\n' \
  "https://reports.acme.example/api/reports/monthly?month=2026-09"
sudo grep 'upstream timed out' /var/log/nginx/error.log | tail -n 1
journalctl -u reports-api --since "-10min" | grep monthly
sudo nginx -T 2>/dev/null | grep -E 'proxy_(read|connect)_timeout'
```
```text
504 0.012 60.031 60.031
upstream timed out (110: Connection timed out) while reading response header from upstream, request: "GET /api/reports/monthly?month=2026-09"
Oct 05 10:14:52 web-1 reports-api[901]: report monthly 2026-09 done in 83.4s
    proxy_read_timeout 60s;
```
Conclusion: nginx drops the connection after 60 s, while the application finishes the report after 83 s and works in vain. The timeout of the higher level must be
longer than that of the lower one, but it is better not to lengthen a synchronous request: the report as a background job with polling
for the status. As a stopgap (a change in the configuration repository, with consent): `proxy_read_timeout 120s` only for this path.
