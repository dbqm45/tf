# Live Regions

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/live-regions (Den Odell, updated 7 October 2025).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Examples:** React, Vue, Native web

## TLDR

"Announce dynamic content changes to screen readers using ARIA live regions, choosing politeness
levels based on urgency."

## Notes (state as of 2026, corrections to the source)

- `.sr-only`: `clip` is deprecated — use `clip-path: inset(50%)` (the CSS was corrected).
- `role="alert"` already implies `aria-live="assertive"` (and `aria-atomic="true"`), `role="status"` — `polite`; do not
  duplicate the attributes. The region must exist in the DOM before the content changes — always render it, change only the text.
- In the countdown example `setAnnouncement` was called inside the `setSeconds` updater function (a side
  effect in the updater — in StrictMode it runs twice). Corrected: the announcements are derived from the value in an effect.
- `useCallback(debounce(...), [])` — the lint does not see the dependencies; keep a stable debounce function in `useMemo`/`useRef`.
- Angular: `LiveAnnouncer` from the CDK (`announce(msg, 'polite')`) — fw-angular. Specification: WAI-ARIA 1.2.

## Problem

Dynamic changes on the page (toast notifications, validation messages, autosave indicators) are not
audible to screen reader users. When the page does not reload, the screen reader has no
built-in reason to announce newly injected content — it must be explicitly
instructed to do so.

## Solution

Mark regions of the page with the `aria-live` attribute to tell screen readers to automatically
announce content changes:
- `aria-live="polite"` — non-urgent updates (e.g. "Item added to cart"), it waits until the screen reader
  finishes the current utterance.
- `aria-live="assertive"` — urgent messages (e.g. errors), it interrupts immediately.
- `role="status"` — a shorthand equivalent to `aria-live="polite"`.
- `role="alert"` — a shorthand equivalent to `aria-live="assertive"`.

**The key requirement:** the live region container must exist in the DOM **before** content is injected into
it — adding the container and the content at the same moment may not be detected.

## Code examples

### Basic live regions — HTML

```html
<!-- Polite: waits for current announcement to finish -->
<div aria-live="polite" aria-atomic="true" class="status-message"></div>

<!-- Assertive: interrupts immediately -->
<div aria-live="assertive" aria-atomic="true" class="error-message"></div>
```

### Basic live regions — React

```javascript
function NotificationSystem() {
  const [message, setMessage] = useState('');

  const showSuccess = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <>
      <button onClick={() => showSuccess('Item added to cart')}>Add to Cart</button>
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {message}
      </div>
    </>
  );
}
```

### Basic live regions — Vue

```vue
<template>
  <button @click="addItem">Add to Cart</button>
  <div role="status" aria-live="polite" aria-atomic="true" class="sr-only">
    {{ statusMessage }}
  </div>
</template>

<script setup>
import { ref } from 'vue';
const statusMessage = ref('');

const addItem = () => {
  statusMessage.value = 'Item added to cart';
  setTimeout(() => statusMessage.value = '', 3000);
};
</script>
```

### Announcing form validation errors

```javascript
function SignupForm() {
  const [errors, setErrors] = useState({});
  const [errorMessage, setErrorMessage] = useState('');

  const validateForm = (formData) => {
    const newErrors = {};
    if (!formData.email) newErrors.email = 'Email is required';
    if (!formData.password) newErrors.password = 'Password is required';
    setErrors(newErrors);

    const count = Object.keys(newErrors).length;
    setErrorMessage(count > 0 ? `Form has ${count} error${count > 1 ? 's' : ''}` : '');
    return count === 0;
  };

  return (
    <form onSubmit={handleSubmit}>
      <div role="alert" className="sr-only">{errorMessage}</div>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" aria-invalid={!!errors.email} />
        {errors.email && <p>{errors.email}</p>}
      </div>
      <button type="submit">Sign Up</button>
    </form>
  );
}
```

### Announcing the loading state

```javascript
function DataLoader({ userId }) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('');

  const loadData = async () => {
    setStatus('Loading...');
    try {
      setData(await fetchUser(userId));
      setStatus('Data loaded');
    } catch {
      setStatus('Failed to load');
    }
  };

  return (
    <>
      <button onClick={loadData}>Load Data</button>
      <div role="status" aria-live="polite" className="sr-only">{status}</div>
      {data && <UserProfile user={data} />}
    </>
  );
}
```

### A progress indicator

```javascript
function FileUpload() {
  const [progress, setProgress] = useState(0);
  const [announcement, setAnnouncement] = useState('');

  const updateProgress = (percent) => {
    setProgress(percent);
    if (percent % 25 === 0) setAnnouncement(`Upload ${percent}% complete`);
  };

  return (
    <>
      <div role="progressbar" aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100">
        <div style={{ width: `${progress}%` }} />
      </div>
      <div role="status" aria-live="polite" className="sr-only">{announcement}</div>
    </>
  );
}
```

### Announcing a timer/countdown

```javascript
function Countdown({ initialSeconds }) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    const timer = setInterval(() => setSeconds(prev => Math.max(prev - 1, 0)), 1000);
    return () => clearInterval(timer);
  }, []);

  // Side effects derived from state — not inside the state updater
  useEffect(() => {
    if (seconds === 60) setAnnouncement('1 minute remaining');
    else if (seconds === 10) setAnnouncement('10 seconds remaining');
    else if (seconds === 0) setAnnouncement('Time expired');
  }, [seconds]);

  return (
    <>
      <div>{seconds} seconds</div>
      <div role="status" aria-live="assertive" className="sr-only">{announcement}</div>
    </>
  );
}
```

### Announcing search results

```javascript
function SearchResults() {
  const [results, setResults] = useState([]);
  const [announcement, setAnnouncement] = useState('');

  const search = async (query) => {
    setAnnouncement('Searching...');
    const data = await fetchResults(query);
    setResults(data);
    setAnnouncement(`${data.length} result${data.length !== 1 ? 's' : ''} found`);
  };

  return (
    <>
      <input type="search" onChange={(e) => search(e.target.value)} />
      <div role="status" aria-live="polite" className="sr-only">{announcement}</div>
      <ul>
        {results.map(r => <li key={r.id}>{r.title}</li>)}
      </ul>
    </>
  );
}
```

### Autosave status

```javascript
function Editor() {
  const [content, setContent] = useState('');
  const [saveStatus, setSaveStatus] = useState('');

  const autoSave = useCallback(
    debounce(async (text) => {
      setSaveStatus('Saving...');
      try {
        await saveContent(text);
        setSaveStatus('Draft saved');
        setTimeout(() => setSaveStatus(''), 2000);
      } catch {
        setSaveStatus('Failed to save');
      }
    }, 1000),
    []
  );

  return (
    <>
      <textarea value={content} onChange={(e) => { setContent(e.target.value); autoSave(e.target.value); }} />
      <div role="status" aria-live="polite">{saveStatus}</div>
    </>
  );
}
```

### The "screen reader only" class

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
```

## Advantages

- Screen readers announce content changes they would otherwise have no reason to know about.
- Messages are announced automatically, without additional user interaction.
- It works with all the major screen readers (NVDA, JAWS, VoiceOver).
- Loading states, progress milestones and completion messages become audible.
- Screen reader users get the same feedback as sighted users.

## Disadvantages / trade-offs

- Too many announcements turn into audio noise — it tires and disorients.
- The choice of the politeness level (`polite` vs `assertive`) really matters — a wrong one spoils
  the experience.
- The live region container **must** exist in the DOM before the content changes.
- Fast, frequent updates can overwhelm a screen reader.
- Different screen readers have different timing behaviours for announcements.
- The content must stay visible/present long enough for the screen reader to read it.
- `aria-atomic="true"` announces the **whole** region on every change; `false` announces only the changed
  part — the choice affects what the user will hear.
- Automated tests cannot verify whether the announcements make sense to a human.

## Related patterns

- [ARIA Roles and Attributes](aria-roles-and-attributes.md)
- [Loading State](fe-architecture/references/resilience/loading-state.md)
- [Error Handling](fe-architecture/references/resilience/error-handling.md)
- [ARIA Live Regions — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions)
- [aria-live Attribute — W3C](https://www.w3.org/TR/wai-aria-1.2/#aria-live)
- [Dynamic Content Accessibility — W3C](https://www.w3.org/WAI/ARIA/apg/practices/updating-content/)

## When to use / when NOT to use

Use it for **every** dynamic content change that a screen reader user should
learn about without losing their current focus position (a toast, a validation result, a save/search
status). By default `polite` — reserve `assertive` **sparingly**, only for
really critical messages requiring an immediate reaction (an error blocking further
action); overusing `assertive` is worse than not using it, because it interrupts the user in the middle of
another activity. Do not use a live region for content the user will see anyway through a focus
move (see `focus-management.md`) — these two mechanisms sometimes exclude each other: do not combine both for the same
change without a specific reason.
