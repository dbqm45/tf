# Stop Generation

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/stop-generation.

## Metadata

- **Category:** AI chat UI (at the source: Resilience)
- **Level:** Intermediate
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 2 July 2026
- **Author:** Den Odell

## TLDR

"Give users a stop button that aborts the fetch with an AbortController, keeps whatever text
already streamed in, and lets the server know to stop generating."

**A context note:** this pattern applies specifically to AI/chat interfaces with streamed
responses — it is built directly on `streaming-response.md`.

## Notes (state in 2026, corrections to the source)

- **On a Node server react to `res.on('close')`, not `req.on('close')`** — since Node 16 the `close` event on
  `req` fires after the request body has been read, not when the client disconnects, so generation would be interrupted at once
  (or never). Corrected in the Express example.
- Guard against a "stale" controller: after finishing, check whether `controllerRef.current === controller` before
  you change the status — otherwise the abort of the previous generation overwrites the state of the new one. Corrected in the React example.
- Check `res.ok` before reading the stream; recognize `AbortError` by `err.name === 'AbortError'`
  (with `AbortSignal.timeout()` a `TimeoutError` arrives — that is an error, not "stopped").
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`). In Svelte 5: `$props()`, `$state`,
  `$derived`, `onclick` attributes.

## Problem

The model misinterprets the question and generates an answer that goes in the wrong direction. The user
watches this process in real time, but has no way to stop it. Even when
a "Stop" button exists, it can be a facade — the network request stays open, tokens keep being generated
and billed, even though the user thinks the process has been stopped.

## Solution

Create an `AbortController` at the start of generation and pass its `signal` to `fetch`. Keep
the controller in a ref while streaming. When "Stop" is clicked call `controller.abort()`, which
rejects the active fetch and breaks the stream-reading loop. Catch the resulting `AbortError` and
treat it as a **normal outcome** (`status: 'stopped'`), not an error.

Critical: **keep the tokens that have already arrived** — an abort should mark the message as
"stopped" and leave its partial content visible, not erase it. Swap the "Send" button for
"Stop" while streaming and back again when finished.

## Code examples

### Wiring the Abort — React

```javascript
function useGeneration() {
  const [text, setText] = useState('');
  const [status, setStatus] = useState('idle'); // idle | streaming | stopped | error
  const controllerRef = useRef(null);

  const start = async (prompt) => {
    controllerRef.current?.abort(); // one generation at a time
    const controller = new AbortController();
    controllerRef.current = controller;
    const isCurrent = () => controllerRef.current === controller;
    setText('');
    setStatus('streaming');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (isCurrent()) setText(prev => prev + decoder.decode(value, { stream: true }));
      }
      if (isCurrent()) setStatus('complete');
    } catch (err) {
      // Abort is an expected outcome, not an error
      if (isCurrent()) setStatus(err.name === 'AbortError' ? 'stopped' : 'error');
    }
  };

  const stop = () => controllerRef.current?.abort();

  return { text, status, start, stop };
}
```

### Wiring the Abort — Vue

```vue
<script setup>
import { ref } from 'vue';

const text = ref('');
const status = ref('idle');
let controller = null;

async function start(prompt) {
  controller = new AbortController();
  text.value = '';
  status.value = 'streaming';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      text.value += decoder.decode(value, { stream: true });
    }
    status.value = 'complete';
  } catch (err) {
    status.value = err.name === 'AbortError' ? 'stopped' : 'error';
  }
}

function stop() { controller?.abort(); }
defineExpose({ text, status, start, stop });
</script>
```

### Wiring the Abort — Svelte

```svelte
<script>
  let text = '';
  let status = 'idle';
  let controller = null;

  export async function start(prompt) {
    controller = new AbortController();
    text = '';
    status = 'streaming';

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ prompt }),
        signal: controller.signal,
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
      }
      status = 'complete';
    } catch (err) {
      status = err.name === 'AbortError' ? 'stopped' : 'error';
    }
  }

  export const stop = () => controller?.abort();
</script>
```

### Wiring the Abort — Web Components

```javascript
class Generation extends HTMLElement {
  #controller = null;

  async start(prompt) {
    this.#controller = new AbortController();
    this.textContent = '';

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ prompt }),
        signal: this.#controller.signal,
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        this.textContent += decoder.decode(value, { stream: true });
      }
      this.dataset.status = 'complete';
    } catch (err) {
      this.dataset.status = err.name === 'AbortError' ? 'stopped' : 'error';
    }
  }

  stop() { this.#controller?.abort(); }
}
customElements.define('ai-generation', Generation);
```

### The Stop Control

```javascript
function GenerationControls({ status, onStop }) {
  if (status !== 'streaming') return null;
  return (
    <button type="button" className="stop" onClick={onStop} aria-label="Stop generating">
      <StopIcon aria-hidden="true" /> Stop generating
    </button>
  );
}
```

### Keeping the Partial Answer

```javascript
function AssistantMessage({ text, status, onRegenerate }) {
  return (
    <article data-status={status}>
      <div className="content">{text}</div>
      {status === 'stopped' && (
        <footer className="stopped-note">
          <span>Stopped.</span>
          <button onClick={onRegenerate}>Regenerate</button>
        </footer>
      )}
    </article>
  );
}
```

### Stopping the Work on the Server

```javascript
// Express handler proxying a streaming model API
app.post('/api/chat', async (req, res) => {
  const upstream = new AbortController();

  // When the browser aborts, the response socket closes — stop generating too.
  // (Not req.on('close'): since Node 16 it fires once the request body is read.)
  res.on('close', () => { if (!res.writableEnded) upstream.abort(); });

  const modelStream = await model.chat({ messages: req.body.messages, signal: upstream.signal });
  for await (const chunk of modelStream) {
    res.write(chunk);
  }
  res.end();
});
```

## Advantages

- The user can get out of an answer going in the wrong direction, instead of waiting for it to end.
- Implementing the abort on the server side too really stops token generation — you do not pay for
  tokens that nobody will read any more.
- Keeping the partial text makes stopping **non-destructive** for the answer so far.
- It builds directly on the `Streaming Response` infrastructure — it is not a separate system.
- A clear "Stop" control gives the user a real sense of control over the interface.

## Disadvantages / tradeoffs

- **Aborting the fetch on the client does not by itself stop generation on the server** —
  handling the connection close (`res.on('close', ...)`) is an easy-to-forget but critical
  detail; without it the server (and billing) keeps running despite the "stopped" answer in the UI.
- `AbortError` arrives as a rejected Promise — without recognizing it as an expected outcome,
  a normal stop looks like an application error.
- A race condition at the boundary: the user clicks stop exactly when the
  last token arrives.
- Partial answers can be confusing if they are cut off in the middle of a sentence/thought.
- Clearing the controller ref matters — a stale, "old" controller can abort
  the wrong, already outdated request.

## Related patterns

- [Streaming Response](streaming-response.md) — ai-chat-ui
- [Response Regeneration](response-regeneration.md) — ai-chat-ui
- [Prompt Input](prompt-input.md)
- [Message Thread](message-thread.md)
- [AbortController (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [AbortSignal (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [Aborting a fetch (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#aborting_a_fetch)

## When to use / when NOT to use

Required in every UI that streams language model responses — the per-token cost and the length of
generation justify giving the user real control to interrupt. It **makes no sense** outside this
context: for an ordinary, short `fetch()` for data (non-streamed, fast) an ordinary
`AbortController` on component unmount (cleanup) is enough, without a dedicated "Stop" button in the UI —
this pattern as a *visible UI feature* makes sense where the operation is long and visible to
the user in real time.
