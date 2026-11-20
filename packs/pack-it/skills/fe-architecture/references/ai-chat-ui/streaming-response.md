# Streaming Response

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/streaming-response.

## Metadata

- **Category:** AI chat UI (at the source: Resilience)
- **Level:** Advanced
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 28 June 2026
- **Author:** Den Odell

## TLDR

Read the model's response as a stream and append each chunk to the interface as it
arrives, so that the user watches the answer take shape, instead of looking at a loading
indicator for ten seconds.

## Notes (state in 2026, corrections to the source)

- Before reading the stream check `response.ok` (4xx/5xx have a body too) and set `Content-Type: application/json`.
  After the loop call `decoder.decode()` without arguments to flush the decoder's buffer. Corrected in the React example.
- SSE parser: a frame can have **several** `data:` lines (join them with `\n`), and the separator can be `\r\n\r\n`. The delta format
  (`choices[0].delta.content`) is provider-specific — map it in one adapter, not in the component.
  When the server is yours and it is a plain GET, consider the native `EventSource` (but it supports neither POST nor headers).
- **Render markdown from the model through a sanitizer** (DOMPurify / the Sanitizer API) or a parser that does not let
  raw HTML through — the model's response is untrusted data (security/input-sanitization.md, security/output-encoding.md).
- Updating state on every chunk can burden rendering with fast streams — buffer the tokens and flush them
  once per frame (`requestAnimationFrame`) — see fe-web-platform (`.claude/skills/fe-web-platform/references/core-web-vitals.md`, INP).
- Framework-agnostically: keep the stream-reading logic in a plain function/async generator (like `parseSSE`),
  and the component (a React hook, a Vue composable, an Angular service with a `signal`) only appends tokens to the state.
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`). In Svelte 5: `$props()`, `$state`,
  `$derived`, `onclick` attributes.

## Problem

The user asks the assistant a question and waits. The application does `await response.json()`, so nothing
appears on the screen until the last token has been generated — ten seconds of empty space,
then a wall of text all at once. The interface seems broken, even if the backend is fast, because
the user has no evidence that anything is happening.

## Solution

Request a streamed response and read the content as it arrives, without waiting for the whole
payload. Most APIs return a raw text stream or Server-Sent Events, where each chunk
contains a small delta of the response. Get a reader from `response.body`, decode each chunk,
extract the deltas and append them to the displayed message — the same view state mutation updates
the UI on every chunk, without any extra mechanism.

Two details that are easy to miss: decode through a streaming `TextDecoder` (`{ stream: true }`),
so that a character whose bytes fell on the boundary of two chunks does not come out garbled; pass
an `AbortController` signal through `fetch`, so that the stream can be cancelled (see `stop-generation.md`).

## Code examples

### Reading the Stream — React

```javascript
function useStreamingReply() {
  const [text, setText] = useState('');
  const [streaming, setStreaming] = useState(false);

  const send = async (prompt, signal) => {
    setText('');
    setStreaming(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
        signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        // stream: true keeps multi-byte characters intact across chunks
        const chunk = decoder.decode(value, { stream: true });
        setText(prev => prev + chunk);
      }
      const tail = decoder.decode(); // flush
      if (tail) setText(prev => prev + tail);
    } finally {
      setStreaming(false);
    }
  };

  return { text, streaming, send };
}
```

### Reading the Stream — Vue

```vue
<script setup>
import { ref } from 'vue';

const text = ref('');
const streaming = ref(false);

async function send(prompt, signal) {
  text.value = '';
  streaming.value = true;

  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
    signal,
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      text.value += decoder.decode(value, { stream: true });
    }
  } finally {
    streaming.value = false;
  }
}

defineExpose({ text, streaming, send });
</script>

<template>
  <div class="reply">{{ text }}</div>
</template>
```

### Reading the Stream — Svelte

```svelte
<script>
  let text = '';
  let streaming = false;

  export async function send(prompt, signal) {
    text = '';
    streaming = true;

    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
      signal,
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
      }
    } finally {
      streaming = false;
    }
  }
</script>

<div class="reply">{text}</div>
```

### Reading the Stream — Web Components

```javascript
class StreamingReply extends HTMLElement {
  async send(prompt, signal) {
    this.textContent = '';

    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
      signal,
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      this.textContent += decoder.decode(value, { stream: true });
    }
  }
}
customElements.define('streaming-reply', StreamingReply);
```

### Parsing Server-Sent Events

```javascript
async function* parseSSE(response, signal) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Frames are separated by a blank line; keep the trailing partial in the buffer
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop();

    for (const frame of frames) {
      // A frame may carry several data: lines — join them
      const data = frame.split(/\r?\n/)
        .filter(l => l.startsWith('data:'))
        .map(l => l.slice(5).trimStart())
        .join('\n');
      if (!data) continue;

      if (data === '[DONE]') return;

      const token = JSON.parse(data).choices?.[0]?.delta?.content;
      if (token) yield token;
    }
  }
}

// Usage: for await (const token of parseSSE(response, signal)) append(token);
```

### Rendering Streaming Markdown

```javascript
function StreamingMarkdown({ text, streaming }) {
  const { safe, pending } = useMemo(() => {
    if (!streaming) return { safe: text, pending: '' };

    // If we're inside an unclosed code fence, render up to it as markdown
    // and show the rest as plain text until the closing ``` arrives.
    const fenceCount = (text.match(/```/g) || []).length;
    if (fenceCount % 2 === 1) {
      const lastFence = text.lastIndexOf('```');
      return { safe: text.slice(0, lastFence), pending: text.slice(lastFence) };
    }
    return { safe: text, pending: '' };
  }, [text, streaming]);

  // <Markdown> must not pass raw HTML through (or must sanitize it) — model output is untrusted
  return (
    <div className="markdown">
      <Markdown>{safe}</Markdown>
      {pending && <pre className="pending">{pending}</pre>}
    </div>
  );
}
```

### Staying Anchored to the Latest Text

```javascript
function useStickToBottom(ref, dep) {
  const pinned = useRef(true);

  useEffect(() => {
    const el = ref.current;
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      pinned.current = distance < 40; // near the bottom = follow along
    };
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  }, [ref]);

  useEffect(() => {
    if (pinned.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [dep, ref]); // dep = the streaming text, so this runs on every chunk
}
```

## Advantages

- The interface feels responsive even on a slow model — text appears within a second and
  never stops for long.
- The subjective waiting time is shorter — reading the answer as it forms fills time that
  would otherwise be "dead".
- The user can start reacting to the beginning of a long answer before the end has even
  been generated.
- Interaction abandonment drops — there is constant evidence that the application is working, not silence read as
  "freezing".
- It combines naturally with `Stop Generation` — you already have the reader and the abort signal at hand.

## Disadvantages / tradeoffs

- Chunk boundaries do **not** coincide with characters/tokens/markdown syntax — naive
  decoding/rendering visibly breaks the output (see the handling of `{ stream: true }` and unclosed
  code fences in the examples above).
- Streamed markdown is genuinely tricky — unclosed code fences, tables, lists require
  special handling to avoid flicker.
- Error handling is harder — the request can fail **after** the user has already seen
  half of the answer.
- Auto-scroll fights the user if you do not detect that they deliberately scrolled up to
  read something earlier (see `useStickToBottom`).
- You lose the ability to validate/post-process the **whole** response before displaying
  anything at all.
- Some network infrastructure (certain proxies, compression layers) buffers the whole response before
  passing it on — this makes streaming completely impossible, regardless of the frontend code.

## Related patterns

- Thinking Indicator — ai-chat-ui (`thinking-indicator.md`)
- [Stop Generation](stop-generation.md) — ai-chat-ui
- [Message Thread](message-thread.md)
- [Loading State](../resilience/loading-state.md) — Resilience
- Streaming API Responses — OpenAI
- Streaming — Anthropic
- [Streams API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API)
- [Using Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)

## When to use / when NOT to use

Reach for streaming when an operation generates content **incrementally** and takes long enough (>1-2s) that
the lack of feedback really hurts the experience — AI model responses are the typical case.
Do **not** stream short, fast responses (a simple database query taking 100ms) —
the implementation overhead (SSE parsing, handling chunk boundaries, auto-scroll) brings no
perceptual gain there; a plain `await response.json()` + `loading-state.md` is simpler and sufficient.
