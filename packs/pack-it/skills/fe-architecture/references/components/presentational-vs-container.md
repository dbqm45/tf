# Presentational vs. Container

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/presentational-vs-container.

## Metadata

- **Category:** Components
- **Level:** Beginner
- **Examples:** React, Vue, Svelte
- **Last updated:** September 26, 2025
- **Author:** Den Odell

## TLDR

"Separate dumb components that just render props from smart components that manage data, making UI reusable and trivial to test."

## Notes (state in 2026, corrections to the source)

- The "container" role is today more often played by a **hook / composable / service** (a React custom hook, a Vue composable, an Angular service
  with `signal`/`httpResource`) or a route loader / Server Component, and the presentational component receives data through
  inputs. The principle remains: the UI renders from inputs, the data logic lives elsewhere.
- The manual `useEffect` + `fetch` in the examples does not handle cancellation or races — in production use a data layer
  (resilience/loading-state.md, TanStack Query etc.).
- `<li onClick>` is not keyboard accessible — in real code use a `<button>`/`<a>` inside the `<li>`
  (fe-web-platform, `.claude/skills/fe-web-platform/references/accessibility/semantic-html.md`).
- Tests: `screen.getByRole(...)` instead of destructuring from `render` (testing/component-testing.md).
- The Vue examples are in the Options API (`data`, `mounted`) — in new code the Composition API (`<script setup>`).
- The Svelte examples are Svelte 4 syntax (`export let`, `$:`, `on:click`, `<slot>`); in Svelte 5: `$props()`, `$state`,
  `$derived`, `$effect`, `onclick` attributes, snippets instead of slots.

## Problem

An 800-line component mixing: API calls, error handling, data transformation and JSX. The effect: hard testing, no way to reuse the component with a different data source, no clear boundary between styling and business logic.

## Solution

A split into two types of components: **presentational** (they render the UI solely on the basis of props, without side effects) and **container** (they manage state, fetch data, handle errors and pass the result to the presentational component as props).

## Code examples

### React

```javascript
// Presentational - only renders UI
function UserList({ users, onUserClick, loading, error }) {
  if (loading) return <div className="spinner">Loading...</div>;
  if (error) return <div className="error">{error.message}</div>;
  if (users.length === 0) return <div className="empty">No users</div>;

  return (
    <ul className="user-list">
      {users.map(user => (
        <li key={user.id} onClick={() => onUserClick(user.id)}>
          <img src={user.avatar} alt="" />
          <h3>{user.name}</h3>
        </li>
      ))}
    </ul>
  );
}

// Container - handles data fetching and state
function UserListContainer() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  const handleUserClick = async (userId) => {
    await trackUserClick(userId);
    navigate(`/user/${userId}`);
  };

  return (
    <UserList
      users={users}
      onUserClick={handleUserClick}
      loading={loading}
      error={error}
    />
  );
}
```

### Vue

```vue
<!-- UserList.vue - Presentational -->
<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">{{ error.message }}</div>
  <ul v-else class="user-list">
    <li v-for="user in users" :key="user.id" @click="$emit('user-click', user.id)">
      <h3>{{ user.name }}</h3>
    </li>
  </ul>
</template>

<script>
export default {
  props: ['users', 'loading', 'error'],
  emits: ['user-click']
};
</script>

<!-- UserListContainer.vue - Container -->
<template>
  <UserList :users="users" :loading="loading" :error="error" @user-click="handleUserClick" />
</template>

<script>
import UserList from './UserList.vue';

export default {
  components: { UserList },
  data: () => ({ users: [], loading: true, error: null }),
  async mounted() {
    try {
      this.users = await fetchUsers();
    } catch (err) {
      this.error = err;
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async handleUserClick(userId) {
      await trackUserClick(userId);
      this.$router.push(`/user/${userId}`);
    }
  }
};
</script>
```

### Svelte

```svelte
<!-- UserList.svelte - Presentational -->
<script>
  export let users;
  export let onUserClick;
</script>

<ul>
  {#each users as user (user.id)}
    <li on:click={() => onUserClick(user.id)}>{user.name}</li>
  {/each}
</ul>

<!-- UsersPage.svelte - Container -->
<script>
  import { onMount } from 'svelte';
  import UserList from './UserList.svelte';

  let users = [], loading = true, error = null;

  onMount(async () => {
    try {
      users = await fetchUsers();
    } catch (err) {
      error = err;
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div>Loading...</div>
{:else if error}
  <div>{error.message}</div>
{:else}
  <UserList {users} onUserClick={(id) => navigate(`/user/${id}`)} />
{/if}
```

### Alternative: a custom hook instead of a container

```javascript
// Custom hook extracts data logic - replaces container component
function useUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { users, loading, error };
}

// Component uses hook instead of container wrapper
function UsersPage() {
  const { users, loading, error } = useUsers();
  if (loading) return <Spinner />;
  if (error) return <Error error={error} />;
  return <UserList users={users} onUserClick={(id) => navigate(`/user/${id}`)} />;
}
```

### The same presentational component, different data sources

```javascript
// Same presentational component, different data sources
function ProductList({ items, onItemClick }) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id} onClick={() => onItemClick(item.id)}>{item.name}</li>
      ))}
    </ul>
  );
}

// From API
function APIProducts() {
  const [items, setItems] = useState([]);
  useEffect(() => { fetchProducts().then(setItems); }, []);
  return <ProductList items={items} onItemClick={trackClick} />;
}

// From WebSocket
function LiveProducts() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    const ws = new WebSocket('/products');
    ws.onmessage = (e) => setItems(JSON.parse(e.data));
    return () => ws.close();
  }, []);
  return <ProductList items={items} onItemClick={trackClick} />;
}
```

### Testing a presentational component (without mocking data)

```javascript
test('renders user list', () => {
  const users = [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }];
  const { getByText } = render(<UserList users={users} />);
  expect(getByText('Alice')).toBeInTheDocument();
  expect(getByText('Bob')).toBeInTheDocument();
});

test('calls onClick handler', () => {
  const handleClick = jest.fn();
  const { getByText } = render(
    <UserList users={[{ id: 1, name: 'Alice' }]} onUserClick={handleClick} />
  );
  fireEvent.click(getByText('Alice'));
  expect(handleClick).toHaveBeenCalledWith(1);
});
```

## Advantages

- The presentational component works with any data source (API, WebSocket, static props) without code changes.
- Testing is simple — no mocking of services, only props and assertions.
- Designers/other teams can iterate on the UI without understanding the data-fetching logic.
- Presentational components are portable between projects.

## Disadvantages / tradeoffs

- More files and indirection (two components where one could do).
- It is overkill for simple components without real complexity in the data logic.
- In modern React custom hooks (`useUsers()`) often replace this pattern — less boilerplate.
- Prop drilling and blurred boundaries can appear if the split is not consistent.
- The modern approach (hooks + colocation) favours keeping the logic closer to the component, not a separate container file.

## Related patterns

- [Separation of Concerns](../fundamentals/separation-of-concerns.md) — Fundamentals.
- [Single Responsibility](../fundamentals/single-responsibility.md) — Fundamentals.
- [Component Testing](../testing/component-testing.md) — Testing.
- "Smart and Dumb Components" — Dan Abramov.
- "Thinking in React" — React docs.

## When to use / when NOT to use

Use this separation when you really need **reuse** of the same UI with different data sources (example: a `ProductList` fed once from REST, once from WebSocket) or when a component mixing data and UI is already hard to test/maintain.

Do not introduce this split mechanically for every component with one `useEffect` — in modern React (hooks) a simpler, single-file component with the logic extracted into a custom hook often gives the same gain (testability, reusability) without doubling the number of files. This is exactly the case from eng-design-principles (YAGNI, the critique of pattern overuse): apply a pattern when it solves a named problem, not "because it is in the textbook".
