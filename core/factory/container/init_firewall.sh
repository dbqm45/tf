#!/bin/sh
# The container's firewall: outgoing traffic is dropped by default; allowed are loopback, DNS, replies, and the
# addresses of the domains in TF_ALLOW_DOMAINS (comma-separated, resolved once at start — `tf code --container` passes
# the fixed list plus the project's `isolation_allow_domains`). Limits: DNS itself stays open (data can leave through
# lookups), and a domain whose addresses change during the session needs a new session.
set -eu
command -v iptables >/dev/null || { echo "init_firewall: iptables missing" >&2; exit 1; }
iptables -F OUTPUT
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
for d in $(printf '%s' "${TF_ALLOW_DOMAINS:-}" | tr ',' ' '); do
  case "$d" in *[!A-Za-z0-9.-]*|"") echo "init_firewall: skipped '$d'" >&2; continue ;; esac
  for ip in $(getent ahostsv4 "$d" | awk '{print $1}' | sort -u); do
    iptables -A OUTPUT -d "$ip" -p tcp -m multiport --dports 80,443 -j ACCEPT
  done
done
iptables -P OUTPUT DROP
if command -v ip6tables >/dev/null; then
  ip6tables -F OUTPUT 2>/dev/null || true
  ip6tables -A OUTPUT -o lo -j ACCEPT 2>/dev/null || true
  ip6tables -P OUTPUT DROP 2>/dev/null || true
fi
