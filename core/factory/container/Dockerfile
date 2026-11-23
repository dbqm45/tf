# The factory's session image (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I4): `tf code --container` runs
# Claude Code here with only the project mounted at /workspace. Built by `tf code --container` on first use
# (tag tf-sandbox:<factory version>). The base image is pinned by digest, Claude Code by version.
FROM node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee

ARG CLAUDE_CODE_VERSION=2.1.330

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git iptables python3 \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
 && npm cache clean --force \
 && mkdir -p /workspace /home/node/.claude \
 && chown node:node /workspace /home/node/.claude

COPY --chmod=0755 init_firewall.sh entrypoint.sh /usr/local/bin/

# TF_CONTAINER=1 tells the factory (tf isolation, the status line, the session-start hook) that the session is here
ENV TF_CONTAINER=1 \
    CLAUDE_CONFIG_DIR=/home/node/.claude \
    HOME=/home/node

WORKDIR /workspace
# The entrypoint runs as root only to set the firewall, then drops to the `node` user without capabilities.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["claude"]
