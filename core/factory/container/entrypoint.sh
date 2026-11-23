#!/bin/sh
# Root only long enough to set the firewall; then the session runs as `node` with no capabilities left
# (setpriv clears them on the user change), so the agent cannot change the firewall.
set -eu
/usr/local/bin/init_firewall.sh
exec setpriv --reuid=node --regid=node --init-groups --inh-caps=-all --bounding-set=-all -- "$@"
