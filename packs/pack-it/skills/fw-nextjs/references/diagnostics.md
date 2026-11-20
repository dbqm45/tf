# Diagnosing common Next.js errors (App Router)

## 1. The server–client boundary
- **An asynchronous client component** (`'use client'` and `async function`) is not allowed. Fetch the data
  in the server parent and pass it through props, or use `use(promise)` in the client.
- **Non-serializable props** from the server to the client: plain functions, class instances, `Map`, `Set`, cycles,
  symbols. Convert `Date` to ISO text (e.g. `toISOString()`), and collections to arrays or objects. You pass functions
  only as Server Actions (`'use server'`).
- **A domain object** (a class with methods) crosses as a DTO and is rebuilt by a factory on the client side
  (the "Domain concepts" table in SKILL.md).

## 2. Hydration errors
Typical causes: browser APIs in render, date and time (a different time zone and moment), random identifiers (`useId()`),
invalid HTML nesting. Format the date in the client after mounting, or pass from the server text for one explicit
time zone. `suppressHydrationWarning` only for a single element with intentionally different content, not as a general silencer.

## 3. Losing server rendering without `<Suspense>`
`useSearchParams()` in a static route without `<Suspense>` above the component moves the rendering of the whole route to
the browser. The same applies to `usePathname()` in a dynamic route without `generateStaticParams`. Wrap the smallest
component that uses them in `<Suspense>` with fallback content. `useParams()` and `useRouter()` do not require it.

## 4. Packages incompatible with the server
- **Packages using `window` or `document`** (charts, editors, maps): a dynamic import without SSR in a client
  component.
- **Packages with native modules or that bundle badly** (e.g. `sharp`, `bcrypt`, some ORMs): an entry in
  `serverExternalPackages` in `next.config`.
- **ESM/CommonJS errors** in a package from `node_modules`: `transpilePackages`.
- You import CSS in a module (`import './x.css'`), not with a `<link>` tag; you do not add common polyfills, because
  Next.js includes them.
- You check bundle size with the bundle analyzer for Turbopack or webpack [unverified: the command name
  depends on the version — check in the version's documentation].

## 5. Navigation in `try/catch`
`redirect()`, `permanentRedirect()`, `notFound()`, `forbidden()` and `unauthorized()` work by throwing a
special exception. Do not call them inside a `try` whose `catch` swallows errors: move the call after the block or
rethrow the exception in `catch` (`unstable_rethrow`). `forbidden()` and `unauthorized()` require enabling in the
configuration and the `forbidden.tsx` / `unauthorized.tsx` files [unverified: the experimental status depends on the version].
`error.tsx` is a client component; `global-error.tsx` contains its own `<html>` and `<body>`.

## 6. Development server tools
- **The development server's MCP endpoint** (`/_next/mcp`, in 16 by default, in 15 behind the `experimental.mcpServer` flag):
  it returns current build and runtime errors with source mapping, the list of routes and the log path. Check the port of the running
  server instead of assuming 3000. Connecting a new MCP server to the agent is the human's decision (core-agent-security).
- **Rebuilding selected routes:** `next build --debug-build-paths "<path or pattern>"` (16+) shortens checking
  a build error fix in a large application.
