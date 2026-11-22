---
name: ops-docker
description: Use for Dockerfile, docker-compose, images and running containers — size, build time, image and runtime security (non-root, read-only, capabilities).
metadata:
  review: "2027-04-17"
  catalog: "Use when creating and optimizing a Dockerfile, docker-compose, container images and their security. Not for CI pipelines (ops-ci-cd) or cloud infrastructure."
---

# Docker

## Dockerfile — the pattern
```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3000
HEALTHCHECK CMD node dist/healthcheck.js || exit 1
CMD ["node", "dist/server.js"]
```

## Rules
1. Multi-stage: the build tools do not end up in the final image.
2. A base image with a specific tag (preferably with a digest), never `latest`. Prefer `-slim`/distroless.
3. Dependency layers before `COPY . .`, a `.dockerignore` with `.env*` and `.git`, a non-root user (`USER`).
4. Zero secrets in the image and in `ARG`/`ENV`. Build secrets: `RUN --mount=type=secret`.
5. `CMD` in the exec (JSON) form, so that signals reach the process.
6. `HEALTHCHECK` or a healthcheck in the orchestrator.
7. Running: a read-only file system (`--read-only` + `tmpfs` for the temporary directory), `--cap-drop=ALL`,
   `no-new-privileges`, an image without a shell and a package manager (distroless). After a break-in through an application vulnerability
   (e.g. React2Shell) the attacker then cannot easily download and run a miner or a backdoor.
8. The container's outbound traffic limited to the needed services; no access to the cloud metadata (`169.254.169.254`),
   give cloud permissions through a workload identity (e.g. IRSA, Workload Identity), and enforce IMDSv2 on the machines.

## docker-compose (dev)
Secrets from an uncommitted `.env`, only `.env.example` in the repo.

## Verification
- `hadolint Dockerfile` (if available), `docker build` passes, the image size checked (`docker images`).
- A vulnerability scan (`docker scout cves` / `trivy image`), if available.
