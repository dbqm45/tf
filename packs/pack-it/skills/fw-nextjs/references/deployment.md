# Deployment outside Vercel and version updates
> runtime · 5. Version update step by step

## 1. The container image
- `output: 'standalone'` in `next.config` creates a directory with the server (`server.js`) and only the production dependencies.
  You copy the `.next/static` and `public` directories into the image separately; without them the page has no CSS or static files.
- A multi-stage image (dependencies, build, run), the process as a user without root privileges, a healthcheck on
  a lightweight route. Image rules: ops-docker.

## 2. Many instances
The default cache (ISR, `'use cache'` entries, the result of `revalidatePath` and `revalidateTag`) lives on the disk or in the memory
of **one** instance. Behind a load balancer each replica has its own cache, so after invalidation some users
see stale data. Solutions:
- a shared store through a custom cache handler (`cacheHandler` / `cacheHandlers` in `next.config`, e.g. on Redis)
  [unverified: the option names depend on the version — check in the version's documentation];
- for Cache Components the `'use cache: remote'` variant with the platform's store;
- the platform's deployment adapter (stable since 16.2) or the OpenNext project for serverless environments.

SSR, static pages from the build, `next/font` and Draft Mode work with many instances without additional configuration.

## 3. Images and environment variables
- `next/image` optimization loads the server's CPU. Limit the variants (`deviceSizes`, `imageSizes`), extend
  `minimumCacheTTL` or use an external loader (an image CDN). You list remote sources in `images.remotePatterns`.
- `NEXT_PUBLIC_*` are inlined at build time, so one image will not change them between environments. Configuration
  that must differ between environments you read on the server from `process.env` at request time and pass to
  the client through props.

## 4. The runtime environment
By default and for new code: Node.js (the full API, the database, most packages). The Edge Runtime only with an explicit
latency requirement from edge locations and after checking that all dependencies work in it. In 16
`proxy.ts` runs on Node.js, and Cache Components do not work in Edge.

## 5. Version update step by step
1. Read the versions of `next`, `react`, `react-dom` and the types from `package.json` and the lockfile (grep, without reading the whole
   file). You do the upgrade only at the human's request (ops-dependency-upgrades, core-stack-sync).
2. Read the upgrade guide for every major version on the way (nextjs.org/docs/app/guides/upgrading)
   or the documentation from the new version's package. When jumping several major versions you go one at a time (14 → 15 → 16).
3. Codemods first: `npx @next/codemod@latest upgrade` (it bumps the dependencies and runs the needed transformations),
   if needed individual transformations, e.g. `next-async-request-api` (15), `middleware-to-proxy` (16).
4. Bump together `next`, `react`, `react-dom`, `@types/react`, `@types/react-dom` and `eslint-config-next`.
5. Review the manual changes from the guide: the configuration in `next.config`, removed options, the default cache behaviour.
6. Verification: `next build`, unit and e2e tests, a manual review of the key paths in `next dev`.
