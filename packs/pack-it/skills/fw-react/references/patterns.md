# React 19 patterns — examples

> **Contents:** 1. A computed value instead of state and an effect · 2. Resetting state through `key` · 3. `useEffectEvent` — the effect does not react to a value… · 4. A form with `useActionState` and a business rejection · 5. Fetching in an effect without a race · 6. A state machine in `useReducer` · 7. Equivalents for React 18

Examples checked with the TypeScript compiler (`tsc --noEmit`, `strict`) with the `react` 19.3 types. Each shows
the mistake first, then the fix.

## 1. A computed value instead of state and an effect
Mistake: an extra render and a moment in which `total` does not match `items`.
```tsx
const [total, setTotal] = useState(0);
useEffect(() => { setTotal(items.reduce((s, i) => s + i.price * i.qty, 0)); }, [items]);
```
Fix: compute during render. When the computation is expensive and the compiler is not enabled — `useMemo`.
```tsx
type Item = { price: number; qty: number };

export function CartTotal({ items }: { items: Item[] }) {
  const total = items.reduce((s, i) => s + i.price * i.qty, 0);
  return <p>{total}</p>;
}
```

## 2. Resetting state through `key`
Mistake: an effect clearing the state after `userId` changes — for one render the old data is visible.
Fix: the parent sets `key`; a new `key` value is a new component with clean state.
```tsx
import { useState } from 'react';

function NoteForm() {
  const [note, setNote] = useState('');
  return <input value={note} onChange={e => setNote(e.target.value)} />;
}

export function Profile({ userId }: { userId: string }) {
  return <NoteForm key={userId} />;
}
```
Resetting only part of the state: compare the previous value during render (the `prevUserId` pattern from react.dev), not in an effect.

## 3. `useEffectEvent` — the effect does not react to a value it only reads
Mistake: `theme` in the dependencies — a theme change drops and re-establishes the connection.
Fix (19.2+): the logic "on the event connect, show a notification in the current theme" goes into an Effect Event.
```tsx
import { useEffect, useEffectEvent } from 'react';

type Conn = { on(ev: 'connected', cb: () => void): void; disconnect(): void };
declare function connect(roomId: string): Conn;
declare function notify(msg: string, theme: 'light' | 'dark'): void;

export function ChatRoom({ roomId, theme }: { roomId: string; theme: 'light' | 'dark' }) {
  const onConnected = useEffectEvent(() => notify('Connected', theme));
  useEffect(() => {
    const c = connect(roomId);
    c.on('connected', () => onConnected());
    return () => c.disconnect();
  }, [roomId]);   // onConnected does not go into the dependencies
  return null;
}
```
Rules: you call an Effect Event only from effects; you do not pass it to other components or hooks.

## 4. A form with `useActionState` and a business rejection
```tsx
import { useActionState } from 'react';

type State = { status: 'idle' } | { status: 'ok'; id: string } | { status: 'rejected'; reason: string };
declare function reserveRoom(roomId: string, slot: string): Promise<{ ok: true; id: string } | { ok: false; reason: string }>;

async function reserve(_prev: State, form: FormData): Promise<State> {
  const r = await reserveRoom(String(form.get('room')), String(form.get('slot')));
  return r.ok ? { status: 'ok', id: r.id } : { status: 'rejected', reason: r.reason };
}

export function ReserveForm() {
  const [state, action, pending] = useActionState(reserve, { status: 'idle' } as State);
  return (
    <form action={action}>
      <input name="room" required />
      <input name="slot" required />
      <button disabled={pending}>Reserve</button>
      {state.status === 'rejected' && <p role="alert">{state.reason}</p>}
    </form>
  );
}
```
In Next.js the `reserve` function can be a Server Action — then authorization and input validation go inside it (fw-nextjs).

## 5. Fetching in an effect without a race
Only when there is no framework or query library. A late response for an old filter is ignored,
and the request aborted.
```tsx
import { useEffect, useState } from 'react';

export function Results({ query }: { query: string }) {
  const [rows, setRows] = useState<string[]>([]);
  useEffect(() => {
    const ctrl = new AbortController();
    fetch(`/api/search?q=${encodeURIComponent(query)}`, { signal: ctrl.signal })
      .then(r => r.json() as Promise<string[]>)
      .then(setRows)
      .catch(e => { if ((e as Error).name !== 'AbortError') throw e; });
    return () => ctrl.abort();
  }, [query]);
  return <ul>{rows.map(r => <li key={r}>{r}</li>)}</ul>;
}
```

## 6. A state machine in `useReducer`
```tsx
import { useReducer } from 'react';

type S = { kind: 'free' } | { kind: 'held'; by: string } | { kind: 'booked'; by: string };
type E = { type: 'hold'; by: string } | { type: 'confirm' } | { type: 'release' };

export function slot(s: S, e: E): S {
  switch (e.type) {
    case 'hold': return s.kind === 'free' ? { kind: 'held', by: e.by } : s;
    case 'confirm': return s.kind === 'held' ? { kind: 'booked', by: s.by } : s;
    case 'release': return s.kind === 'held' ? { kind: 'free' } : s;
  }
}

export function Slot() {
  const [s, dispatch] = useReducer(slot, { kind: 'free' });
  return <button onClick={() => dispatch({ type: 'hold', by: 'me' })}>{s.kind}</button>;
}
```
You test the reducer as a pure function: `expect(slot({ kind: 'free' }, { type: 'confirm' })).toEqual({ kind: 'free' })`.

## 7. Equivalents for React 18
| React 19 | React 18 |
|---|---|
| `ref` as a prop | `forwardRef((props, ref) => …)` |
| `useActionState` / `<form action>` | `onSubmit` + `useState` for the result and `useTransition` for pending |
| `useOptimistic` | local state changed before the request and rolled back after an error |
| `useEffectEvent` (19.2) | `useRef` with the latest value updated in an effect (the "latest ref" pattern) |
| `use(promise)` | a query library or an effect with a cleanup (point 5) |
| `act` from `react` | `act` from `react-dom/test-utils` |
| React Compiler | also works with 17 and 18 (the `react-compiler-runtime` package) |
