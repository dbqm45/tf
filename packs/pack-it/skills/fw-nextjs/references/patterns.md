# Next.js 16 patterns (App Router) — examples

> **Contents:** 1. The data access layer (DAL) · 2. Server Action · 3. A cached read (Cache Components) · 4. A page with `await params` and `<Suspense>` · 5. `proxy.ts` · 6. Equivalents for 14 and 15

Checked with the TypeScript compiler (`tsc --noEmit`, `strict`) with the `next` 16.3.8 and `react` 19.3 types. The
`@/lib/*` modules in the examples are stand-in declarations (session, database) — in the project substitute your own.

## 1. The data access layer (DAL)
```ts
// features/orders/server/dal.ts
import 'server-only';
import { cache } from 'react';
import { getSession } from '@/lib/auth';
import { db } from '@/lib/db';

export type OrderDTO = { id: string; total: string; status: 'open' | 'paid' };

export const currentUser = cache(async () => {
  const s = await getSession();
  if (!s) throw new Error('UNAUTHENTICATED');
  return s.user;
});

export async function ordersOfCurrentUser(): Promise<OrderDTO[]> {
  const user = await currentUser();
  const rows = await db.order.findMany({ where: { ownerId: user.id } });
  return rows.map(r => ({ id: r.id, total: r.total.toFixed(2), status: r.status }));   // minimal DTO
}
```
React's `cache` deduplicates the session check within one request. The DTO contains no fields the UI does not need.

## 2. Server Action
```ts
// features/orders/server/actions.ts
'use server';
import { updateTag } from 'next/cache';
import { currentUser } from './dal';
import { db } from '@/lib/db';

export type DeleteResult = { ok: true } | { ok: false; reason: string };

export async function deleteOrder(_prev: DeleteResult | null, form: FormData): Promise<DeleteResult> {
  const user = await currentUser();                       // 1. session — in EVERY action
  const id = form.get('id');
  if (typeof id !== 'string' || id.length === 0) return { ok: false, reason: 'Missing identifier' };   // 2. input
  const order = await db.order.findUnique({ where: { id } });
  if (!order || order.ownerId !== user.id) return { ok: false, reason: 'Order not found' };   // 3. owner (IDOR)
  if (order.status === 'paid') return { ok: false, reason: 'A paid order cannot be deleted' };    // 4. rule
  await db.order.delete({ where: { id } });
  updateTag(`orders:${user.id}`);                         // 5. list refreshed immediately (read-your-writes)
  return { ok: true };
}
```
The same message for "does not exist" and "someone else's" does not reveal the existence of other users' resources. Action tests: no session,
someone else's order, an empty `id`, a paid order, the valid case.

## 3. A cached read (Cache Components)
```ts
// features/products/server/queries.ts — requires cacheComponents: true in next.config.ts
import { cacheLife, cacheTag } from 'next/cache';
import { db } from '@/lib/db';

export async function productList() {
  'use cache';
  cacheLife('hours');
  cacheTag('products');
  const rows = await db.product.findMany();
  return rows.map(p => ({ id: p.id, name: p.name }));
}
```
Editing in the admin panel: the action saves the product and calls `updateTag('products')` — the user sees the change immediately.
A background refresh (e.g. from a webhook in a Route Handler): `revalidateTag('products', 'max')`. A function with `'use cache'`
cannot read `cookies()` or `headers()` — pass the needed value as an argument (it becomes part of the key).

## 4. A page with `await params` and `<Suspense>`
```tsx
// app/products/[id]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';

declare function product(id: string): Promise<{ id: string; name: string } | null>;
declare function Reviews(props: { id: string }): Promise<React.ReactElement>;

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const p = await product(id);
  if (!p) notFound();
  return (
    <main>
      <h1>{p.name}</h1>
      <Suspense fallback={<p>Loading reviews…</p>}>
        <Reviews id={id} />
      </Suspense>
    </main>
  );
}
```
After `next typegen`, instead of a manual type: `PageProps<'/products/[id]'>`.

## 5. `proxy.ts`
```ts
// proxy.ts (root directory or src/) — Next.js 16, Node.js runtime
import { NextResponse, type NextRequest } from 'next/server';

export function proxy(req: NextRequest) {
  if (!req.cookies.get('session')) return NextResponse.redirect(new URL('/login', req.url));
  return NextResponse.next();
}

export const config = { matcher: ['/orders/:path*'] };
```
This is only a quick redirect for convenience. The real authorization is in the DAL and in every action (points 1–2).

## 6. Equivalents for 14 and 15
| Next.js 16 | 15 | 14 |
|---|---|---|
| `proxy.ts`, `export function proxy` | `middleware.ts`, `export function middleware` (Node.js since 15.5) | `middleware.ts` (Edge) |
| `await params` (mandatory) | `await params` (synchronous access with a warning) | `params` synchronously |
| `'use cache'` + `cacheTag` | `fetch(url, { next: { tags: ['products'] } })` or `unstable_cache` | the same; `fetch` cached by default |
| `updateTag(tag)` in an action | `revalidateTag(tag)` | `revalidateTag(tag)` |
| `revalidateTag(tag, 'max')` | `revalidateTag(tag)` | `revalidateTag(tag)` |
| `refresh()` | `router.refresh()` in the client | `router.refresh()` in the client |
| `useActionState` | `useActionState` (React 19) | `useFormState` from `react-dom` |
