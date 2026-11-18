# Service Workers, cache and offline

Moved from the frontend-developer import (`senior.md`, "Service Workers"), supplemented.

## What it is

A script running in the background, outside the page thread, as a **proxy between the application and the network** — the basis of PWA and offline.
It works only in a secure context (HTTPS; `localhost` for testing), because it has power over all the page's traffic within its
scope (`scope`).

## Lifecycle

1. `install` — the first installation: pre-caching static assets (the app shell).
2. `activate` — the new version takes control: cleaning up old caches.
3. `fetch` — intercepting requests and responding from the cache, the network or both.

Update pitfalls: a new SW waits until all tabs with the old one are closed (`waiting`); `skipWaiting()` +
`clients.claim()` speed up the takeover, but can mix old HTML with new chunks — show the user
"A new version is available — refresh" instead of switching silently. Serve the SW file with `Cache-Control: no-cache`.

## Cache strategies (customary names)

| Strategy | Behaviour | For |
|---|---|---|
| Cache-first | the cache, the network only when missing | assets with a hash in the name, fonts |
| Network-first | the network, the cache on error/offline | HTML, data that should be fresh |
| Stale-while-revalidate | immediately from the cache, refresh in the background | moderately changing content (avatars, lists) |
| Network-only / cache-only | no fallback / the cache only | mutating requests / offline resources |

Do not cache personalized responses or ones with sensitive data without a per-user key and clearing on
logout. Usually do not write the strategies by hand — Workbox or the framework module (`@angular/service-worker`,
`vite-plugin-pwa`).

## Additional capabilities

- **Push notifications** (Push API + Notification; on iOS only for PWAs added to the home screen).
- **Background Sync** — finishing a send after the network comes back (Chromium; in other engines — a queue in IndexedDB
  and a retry on `online`).
- **Navigation preload** — fetching the navigation in parallel while the SW starts up (lower network-first latency).

## When not to

An application without offline/installation requirements rarely needs a SW — it adds update complexity and cache bugs that are hard to
reproduce. For speed alone a correct HTTP cache (`Cache-Control`, `immutable` for
assets with a hash) and a CDN are often enough.
