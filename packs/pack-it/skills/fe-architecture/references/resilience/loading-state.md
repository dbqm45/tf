# Loading State

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/loading-state.

## Metadata

- **Category:** Resilience
- **Level:** Advanced
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 15 November 2025
- **Author:** Den Odell

## TLDR

Show spinners, skeletons or progress bars during asynchronous operations, so that
the user knows the application is working and does not abandon or retry the action prematurely.

## Notes (state in 2026, corrections to the source)

- Model the state as a union (`idle | loading | error | empty | success`) — not three independent flags. Every data
  view handles four states: loading, error (with a "try again" action), empty, data.
- In the React example reset `error` before a new request (otherwise an old error covers the new data) — corrected.
- Optimistic updates: only for operations with a high probability of success, always with a rollback;
  React 19 has `useOptimistic`, TanStack Query — `onMutate`/rollback. A rollback to `todos` from the closure can overwrite
  later changes — revert the specific change, not the whole state.
- The "inline" search in the example has no debounce or cancellation — see performance/debounce.md.
- The skeleton colours in CSS are tokens (fe-css), and the shimmer animation respects `prefers-reduced-motion`.
- `role="progressbar"` requires `aria-valuemin`/`aria-valuemax` (or a native `<progress>`) — corrected.
- Angular: `resource`/`httpResource` provide `isLoading()`, `error()`, `value()`, `reload()` (fw-angular).
- The Svelte examples are Svelte 4 syntax (`export let`); in Svelte 5 `$props()`/`$state`.

## Problem

The user clicks "Save", but nothing changes visually — the button looks the same, the form
looks the same. The lack of feedback makes the user click again, accidentally
submitting the form twice, or refresh/leave the page, losing their work, thinking that the application
has frozen, although in reality it is working in the background.

## Solution

"Always show users what is happening — too many applications forget this basic UX
rule." Show a spinner/skeleton/progress bar while loading; disable buttons and change their
label to "Saving…"; for long operations show **real** progress ("Uploading: 47%"), not
an indeterminate spinner; separate the loading state from the data state and from the error state (three different states,
not one boolean).

Skeleton screens work particularly well — they show the **shape** of the upcoming
content, which makes loading subjectively "feel" faster than an empty spinner, even with
an identical real waiting time.

## Code examples

### Basic Loading State — React

```javascript
function UserProfile({ userId }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchUser(userId);
        if (!cancelled) setUser(data);
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadUser();
    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <div className="spinner" role="status">Loading...</div>;
  if (error) return <div className="error">Failed to load user</div>;
  return <div>{user.name}</div>;
}
```

### Basic Loading State — Vue

```vue
<template>
  <div v-if="loading" class="spinner" role="status">Loading...</div>
  <div v-else-if="error" class="error">{{ error.message }}</div>
  <div v-else>{{ user.name }}</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps(['userId']);
const loading = ref(true);
const error = ref(null);
const user = ref(null);

onMounted(async () => {
  try {
    user.value = await fetchUser(props.userId);
  } catch (err) {
    error.value = err;
  } finally {
    loading.value = false;
  }
});
</script>
```

### Basic Loading State — Svelte

```svelte
<script>
  export let userId;
  let userPromise = fetchUser(userId);
</script>

{#await userPromise}
  <div class="spinner">Loading...</div>
{:then user}
  <div>{user.name}</div>
{:catch error}
  <div class="error">Failed to load user</div>
{/await}
```

### Basic Loading State — Web Components

```javascript
class UserProfile extends HTMLElement {
  loading = true;
  user = null;
  error = null;

  async connectedCallback() {
    this.render();
    try {
      this.user = await fetchUser(this.getAttribute('user-id'));
    } catch (err) {
      this.error = err;
    } finally {
      this.loading = false;
      this.render();
    }
  }

  render() {
    if (this.loading) this.innerHTML = '<div class="spinner">Loading...</div>';
    else if (this.error) this.innerHTML = '<div class="error">Failed</div>';
    else this.innerHTML = `<div>${this.user.name}</div>`;
  }
}
customElements.define('user-profile', UserProfile);
```

### Button Loading State

```javascript
function SaveButton({ onSave }) {
  const [saving, setSaving] = useState(false);

  const handleClick = async () => {
    setSaving(true);
    try {
      await onSave();
    } finally {
      setSaving(false);
    }
  };

  return (
    <button onClick={handleClick} disabled={saving} aria-busy={saving}>
      {saving ? 'Saving...' : 'Save'}
    </button>
  );
}
```

### Skeleton Screen

```javascript
function UserList({ users, loading }) {
  if (loading) {
    return (
      <div className="user-list">
        {[1, 2, 3].map(i => (
          <div key={i} className="user-skeleton">
            <div className="skeleton-avatar" />
            <div className="skeleton-text" />
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="user-list">
      {users.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}
```

```css
.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--skeleton-base) 25%, var(--skeleton-highlight) 50%, var(--skeleton-base) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-avatar { animation: none; }
}
```

### Progress Bar

```javascript
function FileUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async (file) => {
    setUploading(true);
    setProgress(0);

    try {
      await uploadFile(file, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress(percent);
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />

      {uploading && (
        <div className="progress-bar" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label="Upload progress">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span>{progress}%</span>
        </div>
      )}
    </div>
  );
}
```

### Optimistic Updates

```javascript
function TodoList({ todos }) {
  const [optimisticTodos, setOptimisticTodos] = useState(todos);
  const [loading, setLoading] = useState({});

  const handleToggle = async (id) => {
    setOptimisticTodos(prev =>
      prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t)
    );
    setLoading(prev => ({ ...prev, [id]: true }));

    try {
      await toggleTodo(id);
    } catch {
      setOptimisticTodos(todos);
    } finally {
      setLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  return (
    <ul>
      {optimisticTodos.map(todo => (
        <li key={todo.id}>
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() => handleToggle(todo.id)}
            disabled={loading[todo.id]}
          />
          {todo.text}
        </li>
      ))}
    </ul>
  );
}
```

### Delayed Loading Indicator

```javascript
function DataDisplay() {
  const [showSpinner, setShowSpinner] = useState(false);
  const [data, setData] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => setShowSpinner(true), 200);

    fetchData().then(result => {
      clearTimeout(timer);
      setShowSpinner(false);
      setData(result);
    });

    return () => clearTimeout(timer);
  }, []);

  if (showSpinner) return <Spinner />;
  return data ? <Content data={data} /> : null;
}
```

### Inline Loading State

```javascript
function SearchBox() {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState([]);

  const handleSearch = async (q) => {
    setSearching(true);
    const data = await search(q);
    setResults(data);
    setSearching(false);
  };

  return (
    <div>
      <div className="search-input-wrapper">
        <input
          type="search"
          value={query}
          onChange={(e) => { setQuery(e.target.value); handleSearch(e.target.value); }}
        />
        {searching && <span className="spinner-inline" />}
      </div>
      <ul>
        {results.map(r => <li key={r.id}>{r.title}</li>)}
      </ul>
    </div>
  );
}
```

## Advantages

- The user stops "clicking furiously" — the feedback confirms that the action has been
  registered.
- Page abandonment drops — the user does not refresh/run away, seeing that the application is working.
- Perceived performance improves — skeletons "feel" faster than an empty spinner even with
  an identical waiting time.
- A clear distinction between "loading" / "loaded but empty" / "failure" — no need to guess.
- Duplicate form submissions disappear, because a disabled button prevents an accidental
  double click.
- A progress bar sets expectations — "Uploading: 47%" says how much longer to wait.
- The page layout is stable — the skeleton reserves space, so there are no sudden content jumps.

## Disadvantages / tradeoffs

- The risk of "spinner spam" — too many indicators at once create visual clutter.
- Very fast operations can flash an indicator for 50ms — that is worse than none; add a short
  delay (see "Delayed Loading Indicator" above).
- More state to manage per component (`loading`, `data`, `error` instead of just the data).
- Skeletons require maintenance — a layout change requires updating the corresponding skeleton.
- Optimistic updates are hard — they require solid rollback logic on error.
- Progress bars require backend support — without progress data you cannot show a meaningful %.
- A sophisticated loading state is **not** a fix for a real performance problem — the real fix
  is speeding up the operation itself, not a nicer spinner on a slow operation.
- Accessibility is easily overlooked — `role="status"`, `aria-busy` are often forgotten.

## Related patterns

- [Error Handling](./error-handling.md) — Resilience
- [Async Boundary](./async-boundary.md) — Resilience
- [Progress Indicators (NN Group)](https://www.nngroup.com/articles/progress-indicators/)
- [Suspense (React)](https://react.dev/reference/react/Suspense)
- [Suspense (Vue)](https://vuejs.org/guide/built-ins/suspense.html)
- [Await Blocks (Svelte)](https://svelte.dev/docs/logic-blocks#await)

## When to use / when NOT to use

Use it **always** when an operation takes long/unpredictably (network, upload) — this is a foundation of
Resilience, not an option. Do **not** add an indicator for operations that finish in <100–200ms — an empty
screen for a fraction of a second is better than a flashing spinner that flickers and disappears before the user
manages to notice it (see the "Delayed Loading Indicator" pattern). Match the type of indicator to the nature of the
operation: a spinner on the button for short actions, a skeleton for page content, a progress bar only
when the backend actually gives you progress data.
