# Client-Side Routing

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/client-side-routing.

## Metadata

- **Category:** Routing
- **Level:** Intermediate
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 14 December 2025
- **Author:** Den Odell

## TLDR

"Intercept navigation to swap views without full page reloads, managing browser history and scroll
position for a seamless single-page experience."

## Notes (state in 2026, corrections to the source)

- **A bug in the React example corrected:** `useNavigate()` called outside `<BrowserRouter>` throws an exception — the hook
  works only in a component under the router. In React Router 7 import from `react-router` (the `react-router-dom` package
  is only a re-export); "framework mode" gives loaders/actions per route.
- Vanilla: `e.target.matches('a')` does not catch clicks on elements inside a link — use `e.target.closest('a')` and
  skip clicks with modifiers (Ctrl/Cmd/Shift, the middle button), `target="_blank"`, `download` and links
  to other origins. Corrected.
- **Navigation API** (`navigation.addEventListener('navigate', e => e.intercept({ handler }))`) — the modern
  successor of manual `pushState` + `popstate` + click interception; in 2026 available in all major
  engines (check Baseline for your audience), with the History API as a fallback.
- After a route change move focus to the heading and update `document.title` (fe-web-platform,
  `.claude/skills/fe-web-platform/references/accessibility/focus-management.md`); transition animations — the View Transitions API.
- An alternative to an SPA for content: MPA + cross-document View Transitions + Speculation Rules (prerender) gives
  smoothness without a client router (rendering-models.md).
- Svelte: `svelte-routing` is a niche library — the standard is SvelteKit's file-based routing. Angular: `provideRouter`,
  functional guards, `withComponentInputBinding()`, `loadComponent` (fw-angular).

## Problem

Every link click triggers a full page reload: a white flash, the scroll jumping to the top, loss of
form data, a playing video stopping, expanded accordions collapsing. Users
lose work by clicking a link before saving changes. Every navigation also requires its own whole-page
loading indicator.

## Solution

Stop full page loads — use the History API to change the URL without real browser
navigation, swapping only the fragment of content that actually changes. Intercept link
clicks, call `pushState` to update the URL and render the new route component; for the "back" button
listen to `popstate` and render the previous route. This preserves form state, the scroll position,
expanded menus and ongoing media.

## Code examples

### React

```javascript
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router'; // RR7

// useNavigate() works only in components rendered INSIDE the router
function LoginForm() {
  const navigate = useNavigate();
  const handleLogin = async (credentials) => {
    await login(credentials);
    navigate('/dashboard'); // Programmatic navigation
  };
  return <CredentialsForm onSubmit={handleLogin} />;
}

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
        <Link to="/products">Products</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/products" element={<Products />} />
        <Route path="/login" element={<LoginForm />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Vue

```javascript
<template>
  <div>
    <nav>
      <router-link to="/">Home</router-link>
      <router-link to="/about">About</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script>
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/about', component: About },
    {
      path: '/dashboard',
      component: Dashboard,
      beforeEnter: (to, from) => {
        if (!isAuthenticated()) return '/login';
      }
    }
  ]
});

export default { router };
</script>
```

### Svelte

```javascript
<script>
  import { Router, Route, Link, navigate } from 'svelte-routing';
  import Home from './Home.svelte';
  import About from './About.svelte';

  function handleLogin() {
    navigate('/dashboard', { replace: true });
  }
</script>

<Router>
  <nav>
    <Link to="/">Home</Link>
    <Link to="/about">About</Link>
  </nav>
  <Route path="/" component={Home} />
  <Route path="/about" component={About} />
</Router>
```

### Vanilla JavaScript

```javascript
class Router {
  constructor(routes) {
    this.routes = routes;

    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (!link || link.origin !== location.origin) return;
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if (link.target === '_blank' || link.hasAttribute('download')) return;
      e.preventDefault();
      this.navigate(link.pathname + link.search + link.hash);
    });

    window.addEventListener('popstate', () => this.render(location.pathname));
    this.render(location.pathname);
  }

  navigate(path) {
    history.pushState({}, '', path);
    this.render(path);
  }

  render(path) {
    const route = this.routes.find(r => r.path === path)
      || this.routes.find(r => r.path === '*');
    if (!route) return;

    const container = document.querySelector('#app');
    container.innerHTML = '';
    container.appendChild(new route.component().render());
  }
}

const router = new Router([
  { path: '/', component: HomePage },
  { path: '/about', component: AboutPage },
  { path: '*', component: NotFoundPage }
]);
```

### Scroll Position Management

```javascript
// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  return null;
}

// Or preserve scroll per route
const scrollPositions = new Map();

function preserveScroll() {
  scrollPositions.set(location.pathname, window.scrollY);
}

function restoreScroll(pathname) {
  window.scrollTo(0, scrollPositions.get(pathname) || 0);
}
```

### Hash-Based Routing

```javascript
// For environments without server config (URLs: example.com/#/about)
window.addEventListener('hashchange', () => {
  render(location.hash.slice(1) || '/');
});
```

## Advantages

- Instant navigation, without a white flash and whole-page loading indicators.
- UI state survives navigation — form data, scroll, ongoing media.
- The possibility of animated transitions between views.
- A smaller server load (fetching data, not full HTML pages).
- Precise control over guards, navigation and transition hooks (e.g. `beforeEnter`).

## Disadvantages / tradeoffs

- Requires JavaScript — without it nothing moves.
- Requires server configuration (a direct visit to a URL must return the application, not a 404).
- SEO complications — crawlers may not execute JS.
- Manual memory management — you have to make sure listeners are cleaned up on unmount.
- Manual handling of scroll and focus (the browser does this automatically on a full load).
- "History quirks if you mix up `pushState` and `replaceState`, creating confusing back-button
  behavior."

## Related patterns

- History API — MDN.
- React Router — documentation.
- Vue Router — documentation.
- SvelteKit Routing — the Svelte documentation.

## When to use / when NOT to use

Client-side routing is the foundation of every SPA — use it whenever you build a component
application with many views. Do **not** treat it as the obvious choice for mostly
static/documentation content, where SEO and the first render count more than smooth
transitions between subpages — there full reloads (or SSR/SSG, see
`../rendering-models.md`, the "Rendering models" section) are often the better
choice. Also remember the server configuration (a fallback to `index.html` for every path) — without
it a direct visit to a deep URL simply will not work.
