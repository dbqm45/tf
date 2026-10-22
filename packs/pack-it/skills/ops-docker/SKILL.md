---
name: ops-docker
description: Użyj przy Dockerfile, docker-compose i obrazach — tworzenie, rozmiar i czas budowy, bezpieczeństwo obrazów.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj przy tworzeniu i optymalizacji Dockerfile, docker-compose, obrazów kontenerów i ich bezpieczeństwa. Nie do pipeline'ów CI (ops-ci-cd) ani infrastruktury chmurowej (ops-iac-terraform)."
---

# Docker

## Dockerfile — wzorzec
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

## Zasady
1. Multi-stage: narzędzia buildu nie trafiają do obrazu końcowego.
2. Obraz bazowy z konkretnym tagiem (najlepiej z digestem), nigdy `latest`. Preferuj `-slim`/distroless.
3. Warstwy zależności przed `COPY . .`, `.dockerignore` z `.env*` i `.git`, użytkownik nie-root (`USER`).
4. Zero sekretów w obrazie i w `ARG`/`ENV`. Sekrety buildu: `RUN --mount=type=secret`.
5. `CMD` w formie exec (JSON), aby sygnały docierały do procesu.
6. `HEALTHCHECK` lub healthcheck w orkiestratorze.
7. Uruchomienie: system plików tylko do odczytu (`--read-only` + `tmpfs` na katalog tymczasowy), `--cap-drop=ALL`,
   `no-new-privileges`, obraz bez powłoki i menedżera pakietów (distroless). Po włamaniu przez podatność aplikacji
   (np. React2Shell) napastnik nie pobierze i nie uruchomi wtedy łatwo koparki ani backdoora.
8. Ruch wychodzący kontenera ograniczony do potrzebnych usług; brak dostępu do metadanych chmury (`169.254.169.254`),
   uprawnienia chmurowe daj przez tożsamość obciążenia (np. IRSA, Workload Identity), a na maszynach wymuszaj IMDSv2.

## docker-compose (dev)
Sekrety z niecommitowanego `.env`, w repo tylko `.env.example`.

## Weryfikacja
- `hadolint Dockerfile` (jeśli dostępny), `docker build` przechodzi, rozmiar obrazu sprawdzony (`docker images`).
- Skan podatności (`docker scout cves` / `trivy image`), jeśli dostępny.
