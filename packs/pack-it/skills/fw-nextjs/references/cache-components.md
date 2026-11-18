# Cache Components (Next.js 16+) — model, keys, limitations, migration

You enable it with the `cacheComponents: true` flag in `next.config.ts`; it replaces the experimental `experimental.ppr`.
Before the change check the documentation matched to the installed version (`.next-docs/`, SKILL.md), because the cache
API changed between releases 15 and 16.

## 1. Three kinds of content on one page
- **Static:** synchronous code, imports and pure computations go into the shell prerendered at build time.
- **Cached:** asynchronous data that does not have to be fresh on every request, you mark with `'use cache'`.
- **Dynamic:** data that must be fresh or depends on the request (cookies, headers, search parameters),
  you wrap in `<Suspense>`. It loads as a stream after the shell is sent.

An asynchronous component without `'use cache'` and without `<Suspense>` above it is a build error: Next.js does not know whether to
prerender it or to wait for the request. You resolve it explicitly in one of the two ways.

## 2. Where you put `'use cache'`
- **File:** the whole page or module is cached. Use it rarely, because it is hard to extract a dynamic part later.
- **Component:** a cached fragment of the tree, e.g. a product list on a page with the user's cart.
- **Function:** a data read in the DAL (`references/patterns.md`, section 3). The easiest to test and reuse.

## 3. Lifetime and variants
- `cacheLife('minutes' | 'hours' | 'days' | 'weeks' | 'max')` or an object with three times: how long to serve
  the stale value without asking the server, how often to refresh in the background and when the entry expires unconditionally.
  The default profile without `cacheLife` has short times on the order of minutes [unverified: check the exact values
  in the version's documentation].
- `'use cache: remote'` — entries in the platform's store (e.g. Redis, KV) shared by the instances.
- `'use cache: private'` — an exception for a specific user's data that allows reading `cookies()`; the result
  does not go into the shared cache. Use it when the value cannot be passed as an argument (section 6).

## 4. The cache key
The key is created automatically from the build identifier (a new deployment invalidates everything), the function's location,
the serializable arguments and the closure variables. Conclusions:
- everything the result depends on must be an argument or a closure variable;
- a non-serializable argument (a class, a function) breaks the key — pass identifiers and simple data;
- an argument with a large number of values (e.g. a full filter object) multiplies entries — pass only the needed fields.

## 5. Invalidation
- `cacheTag('products', 'product-' + id)` inside the function: a general tag for lists and a specific one for a single record.
- In a Server Action after the save `updateTag(tag)`: the same user sees their write immediately.
- From a webhook or a background job `revalidateTag(tag, 'max')`: subsequent requests will get fresh data, current ones may
  get the old version.

## 6. Request data
In a function with `'use cache'` you do not read `cookies()`, `headers()` or `searchParams`. You read them higher up, outside
the cached function, and pass the needed value as an argument; it becomes part of the key. The part of the page that
reads this data sits in `<Suspense>`.

## 7. Limitations
- It requires the Node.js environment: it does not work in the Edge Runtime or with a static export (`output: 'export'`).
- Non-deterministic values (`Math.random()`, `Date.now()`, `crypto.randomUUID()`) in `'use cache'` are computed
  once and stay in the cache. When they must be different on every request, call `await connection()`
  from `next/server` first, outside the cache.
- With several instances, entries in the memory of one instance are not visible in the others (`references/deployment.md`).

## 8. Migration from the old settings
| Before (15 and older) | With Cache Components |
|---|---|
| `experimental.ppr` | `cacheComponents: true` |
| `export const dynamic = 'force-dynamic'` | remove it; dynamic is the default |
| `export const dynamic = 'force-static'` | `'use cache'` + `cacheLife('max')` |
| `export const revalidate = N` | `cacheLife({ revalidate: N })` |
| `unstable_cache(fn, keyParts, { tags, revalidate })` | a function with `'use cache'`, `cacheTag(...)`, `cacheLife(...)`; no manual keys |

Order: enable the flag on a branch, run `next build` and remove the errors one by one (each points to a component without
a "cache or Suspense" decision). Then a review of all `revalidateTag` and `revalidatePath`.

When you migrate a larger application, the Next.js authors provide the process skills `next-cache-components-adoption`
and `next-cache-components-optimizer` in the `vercel/next.js` repository (the `skills` directory). The human installs them after
an audit (core-agent-security).
