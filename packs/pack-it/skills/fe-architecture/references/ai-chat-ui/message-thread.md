# Message Thread

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/message-thread ("Structuring an AI Conversation Transcript").

## Metadata

- **Category:** AI chat UI (at the source: Components)
- **Level:** Intermediate
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** June 30, 2026
- **Author:** Den Odell

## TLDR

"Represent a conversation as an ordered array of messages, each with a stable id, a role, content, and its own status."

## Notes (state in 2026, corrections to the source)

- **Content from the model is untrusted** (prompt injection can smuggle in HTML/JS). Render it as text
  (framework interpolation, `textContent`) or through a markdown parser + a sanitizer (DOMPurify / the Sanitizer API) —
  never through raw `innerHTML`. The Web Components example below has been corrected from `innerHTML` to the DOM API.
- Do not nest live regions: `role="log"` on the thread already announces appended nodes (polite). While streaming,
  set `aria-busy="true"` on the assistant's message and remove it when done — otherwise the screen reader announces every token.
  Use the "announce once" example below instead of `aria-live` on the container, not together with it.
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`, `createEventDispatcher`). In Svelte 5
  respectively: `let { … } = $props()`, `$derived`/`$effect`, `onclick` attributes, callback props instead of the dispatcher.
- Angular (fw-angular): the thread state in a `signal<Message[]>` + `computed`, the stream through `HttpClient` with
  `observe: 'events', reportProgress: true` or `fetch` in a service; `@for (m of messages(); track m.id)`.

## Problem

A common mistake: storing the conversation as two separate strings (the last user prompt + the last assistant response) or putting flags like `isStreaming`/`error` at the top of the whole component. This causes state to leak between messages — the error of one response affects the whole thread. A quote from the site: "A conversation is a list of turns, each authored by someone, each in some state of completion."

## Solution

Store the conversation as an ordered array of message objects, each with:
- a stable `id`,
- a `role` (`user`, `assistant`, `system`),
- `content`,
- a `status` (`streaming`, `complete`, `stopped`, `error`).

## Code examples

### The conversation model (reducer)

```javascript
function conversationReducer(messages, action) {
  switch (action.type) {
    case 'send':
      return [
        ...messages,
        { id: crypto.randomUUID(), role: 'user', content: action.text, status: 'complete' },
        { id: action.replyId, role: 'assistant', content: '', status: 'streaming' },
      ];

    case 'token': // append a streamed chunk to one assistant message
      return messages.map(m =>
        m.id === action.id ? { ...m, content: m.content + action.chunk } : m
      );

    case 'finish': // 'complete' | 'stopped' | 'error'
      return messages.map(m =>
        m.id === action.id ? { ...m, status: action.status } : m
      );

    default:
      return messages;
  }
}
```

### Rendering the transcript — React

```jsx
function MessageThread({ messages }) {
  return (
    <div className="thread" role="log" aria-live="polite" aria-label="Conversation">
      {messages.map(m => (
        <article key={m.id} className={`message message--${m.role}`} data-status={m.status}>
          <span className="role">{m.role === 'user' ? 'You' : 'Assistant'}</span>
          <div className="content">
            {m.content || (m.status === 'streaming' && <ThinkingIndicator />)}
          </div>
          {m.status === 'error' && <RetryButton id={m.id} />}
        </article>
      ))}
    </div>
  );
}
```

### Vue

```vue
<template>
  <div class="thread" role="log" aria-live="polite" aria-label="Conversation">
    <article
      v-for="m in messages"
      :key="m.id"
      :class="`message message--${m.role}`"
      :data-status="m.status"
    >
      <span class="role">{{ m.role === 'user' ? 'You' : 'Assistant' }}</span>
      <div class="content">
        <template v-if="m.content">{{ m.content }}</template>
        <ThinkingIndicator v-else-if="m.status === 'streaming'" />
      </div>
      <RetryButton v-if="m.status === 'error'" :id="m.id" />
    </article>
  </div>
</template>

<script setup>
defineProps({ messages: Array });
</script>
```

### Svelte

```svelte
<script>
  export let messages = [];
</script>

<div class="thread" role="log" aria-live="polite" aria-label="Conversation">
  {#each messages as m (m.id)}
    <article class="message message--{m.role}" data-status={m.status}>
      <span class="role">{m.role === 'user' ? 'You' : 'Assistant'}</span>
      <div class="content">
        {#if m.content}{m.content}
        {:else if m.status === 'streaming'}<ThinkingIndicator />{/if}
      </div>
      {#if m.status === 'error'}<RetryButton id={m.id} />{/if}
    </article>
  {/each}
</div>
```

### Web Components

```javascript
class MessageThread extends HTMLElement {
  set messages(list) {
    this.setAttribute('role', 'log');
    // DOM API instead of innerHTML: model/user content is never parsed as HTML
    this.replaceChildren(...list.map(m => {
      const article = document.createElement('article');
      article.className = `message message--${m.role}`;
      article.dataset.status = m.status;
      article.setAttribute('aria-busy', String(m.status === 'streaming'));
      const role = document.createElement('span');
      role.className = 'role';
      role.textContent = m.role === 'user' ? 'You' : 'Assistant';
      const content = document.createElement('div');
      content.className = 'content';
      content.textContent = m.content || (m.status === 'streaming' ? '…' : '');
      article.append(role, content);
      return article;
    }));
  }
}
customElements.define('message-thread', MessageThread);
```

### Styling turns visually and semantically

```css
.message { display: grid; gap: 0.25rem; padding: 0.75rem 1rem; }
.message--user { justify-items: end; }
.message--user .content { background: var(--accent); color: var(--on-accent); border-radius: 1rem 1rem 0 1rem; }
.message--assistant .content { background: var(--surface); border-radius: 1rem 1rem 1rem 0; }
.message[data-status="error"] { outline: 1px solid var(--danger); }
.message[data-status="stopped"] .content::after { content: " (stopped)"; opacity: 0.6; }
```

### Announcing a new turn only once (not per token)

```jsx
function AssistantMessage({ message }) {
  const done = message.status !== 'streaming';
  return (
    <div
      className="content"
      // Only announce once the turn is complete, not on every token
      aria-live={done ? 'polite' : 'off'}
    >
      {message.content}
    </div>
  );
}
```

## Advantages

- "Streaming, stopping, and errors scope to a single turn" — the error/streaming of one message does not affect the rest of the thread.
- Stable `id`s enable reuse of DOM nodes (list keying).
- History, editing, branching and regeneration become simple array operations (map/filter), not operations on two separate strings.
- The `log` role + `aria-live` make the conversation accessible to assistive technologies.
- A normalized array is easy to serialize and test.

## Disadvantages / tradeoffs

- Requires discipline so that state does not "leak" back to the level of a single component (top-level flags).
- Per-message live regions require careful handling of announcements (see the "announce once, not per token" example).
- Long threads eventually require list virtualization, which complicates the scrolling logic.
- Rich content inside messages (markdown, code, images) is a separate rendering problem, not solved by the data model itself.
- Generating stable `id`s (`crypto.randomUUID()`) adds a small but extra ceremony.

## Related patterns

- [Streaming Response](streaming-response.md) — ai-chat-ui.
- [Prompt Input](prompt-input.md) — ai-chat-ui.
- [Response Regeneration](response-regeneration.md) — ai-chat-ui.
- [Thinking Indicator](thinking-indicator.md) — ai-chat-ui.
- The `log` role — MDN.
- Normalizing State Shape — Redux docs.
- List rendering keys — React docs.

## When to use / when NOT to use

Use this model whenever you build a conversational/chat UI (with AI or between people) — even a simple MVP benefits from it, because adding streaming/retry/regeneration later to "two strings" requires rewriting the whole state, while for an array of messages — only adding a `status` field.

Do not introduce it for a simple, one-off message (e.g. a single toast/alert) — this is a pattern for a **thread** of many turns, not for a single message without history.
