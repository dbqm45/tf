# Thinking Indicator

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/thinking-indicator.

## Metadata

- **Category:** AI chat UI (at the source: Resilience)
- **Level:** Beginner
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 28 June 2026
- **Author:** Den Odell

## TLDR

"The one to three seconds between sending a prompt and the first token is the most anxious moment
of an AI interaction. Fill it with a thinking state that appears instantly, is announced to
assistive tech, respects reduced motion, and disappears the moment real text arrives."

## Notes (state in 2026, corrections to the source)

- `.sr-only`: the `clip` property is deprecated — use `clip-path: inset(50%)` + `white-space: nowrap`
  (corrected in the CSS below).
- If the indicator sits inside a thread with `role="log"` (message-thread.md), do not give it its own `role="status"`
  — nested live regions produce double announcements. Text for the screen reader in the message slot is enough.
- Take phase labels for agents from real server events (e.g. SSE events of type `status`), never from a timer.
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`). In Svelte 5: `$props()`, `$state`,
  `$derived`, `onclick` attributes.

## Problem

The user waits 1–3 seconds for the model's first response without any feedback, which
suggests that the request has failed — this leads to sending the same prompt again.
A generic spinner does not communicate precisely "the assistant is composing an answer". Indicators are often
purely visual, leaving screen reader users without any information.

## Solution

Place the thinking indicator immediately in the assistant's message slot (see Message Thread), without
waiting for any network response. Style it as a distinct element (animated dots,
a pulsing avatar) that communicates "the assistant is composing an answer", not generic loading. When
the first token arrives through `streaming-response.md`, the indicator turns into the real content.

Ensure accessibility: render it inside a `polite` live region with visually hidden text "Assistant is
thinking…". Under `prefers-reduced-motion` provide a static version without animation. For agents doing
work before answering — update the phase label ("Searching the docs…", "Writing…").

## Code examples

### The Indicator — React

```javascript
function ThinkingIndicator({ label = 'Assistant is thinking' }) {
  return (
    <div className="thinking" role="status" aria-live="polite">
      <span className="sr-only">{label}…</span>
      <span className="dots" aria-hidden="true">
        <span /><span /><span />
      </span>
    </div>
  );
}
```

### The Indicator — Vue

```vue
<template>
  <div class="thinking" role="status" aria-live="polite">
    <span class="sr-only">{{ label }}…</span>
    <span class="dots" aria-hidden="true"><span /><span /><span /></span>
  </div>
</template>

<script setup>
defineProps({ label: { type: String, default: 'Assistant is thinking' } });
</script>
```

### The Indicator — Svelte

```svelte
<script>
  export let label = 'Assistant is thinking';
</script>

<div class="thinking" role="status" aria-live="polite">
  <span class="sr-only">{label}…</span>
  <span class="dots" aria-hidden="true"><span></span><span></span><span></span></span>
</div>
```

### The Indicator — Web Components

```javascript
class ThinkingIndicator extends HTMLElement {
  connectedCallback() {
    const label = this.getAttribute('label') || 'Assistant is thinking';
    this.setAttribute('role', 'status');
    this.setAttribute('aria-live', 'polite');
    const sr = document.createElement('span');
    sr.className = 'sr-only';
    sr.textContent = `${label}…`; // textContent: the label is never parsed as HTML
    const dots = document.createElement('span');
    dots.className = 'dots';
    dots.setAttribute('aria-hidden', 'true');
    dots.append(...Array.from({ length: 3 }, () => document.createElement('span')));
    this.replaceChildren(sr, dots);
  }
}
customElements.define('thinking-indicator', ThinkingIndicator);
```

### Animated Dots, With a Reduced-Motion Fallback

```css
.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0;
}

.dots { display: inline-flex; gap: 0.25rem; }
.dots span {
  width: 0.5rem; height: 0.5rem; border-radius: 50%;
  background: currentColor; opacity: 0.4;
  animation: blink 1.4s infinite both;
}
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink { 0%, 80%, 100% { opacity: 0.4; } 40% { opacity: 1; } }

@media (prefers-reduced-motion: reduce) {
  .dots span { animation: none; opacity: 0.7; }
}
```

### Swapping Thinking for Streamed Text

```javascript
function AssistantMessage({ content, status }) {
  // Empty + streaming = still thinking; any content = show the text
  if (status === 'streaming' && content.length === 0) {
    return <ThinkingIndicator />;
  }
  return <div className="content" aria-busy={status === 'streaming'}>{content}</div>;
}
```

### Phase-Aware Status for Agents

```javascript
function AgentStatus({ phase }) {
  // phase updates arrive from the server: 'thinking' | 'searching' | 'writing'
  const label = {
    thinking: 'Thinking',
    searching: 'Searching the docs',
    writing: 'Writing the answer',
  }[phase] ?? 'Working';

  return (
    <div className="thinking" role="status" aria-live="polite">
      <span className="sr-only">{label}…</span>
      <span aria-hidden="true">{label}<Dots /></span>
    </div>
  );
}
```

## Advantages

- It eliminates the dead time before the first token, preventing a premature resend.
- A dedicated indicator communicates "the assistant is composing" much more clearly than a generic spinner.
- A live region gives screen reader users audio information instead of silence.
- It is the natural, empty state of a streaming message — almost no extra implementation cost.
- A phase-dependent status (for agents) turns a long wait into visible, concrete progress.

## Disadvantages / tradeoffs

- An animated indicator without real progress information can over time seem like a facade during
  a longer wait; phase labels help, but only if they are **true**.
- Live region announcements require restraint — a thinking indicator plus incoming tokens can cause
  double, redundant announcements without proper care.
- Fake phase labels ("Analyzing…" when nothing is really being analysed) destroy the user's trust
  in the interface.
- The animation requires a `prefers-reduced-motion` fallback — it is easy to forget.
- The transition from the indicator to the first token can flicker if you do not handle it in the same DOM
  slot (see `AssistantMessage` above — a condition in the same place, not separate elements).

## Related patterns

- [Streaming Response](streaming-response.md) — ai-chat-ui
- [Message Thread](message-thread.md)
- [Loading State](../resilience/loading-state.md) — Resilience
- Live Regions — fe-web-platform/references/accessibility/live-regions.md
- [ARIA live regions (MDN)](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions)
- [prefers-reduced-motion (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
- [Progress Indicators (NN Group)](https://www.nngroup.com/articles/progress-indicators/)

## When to use / when NOT to use

Use it **always** in chat/AI interfaces for the window between sending a prompt and the first token —
it is a minimal cost with a large impact on perceived reliability. Do **not** introduce phase labels
("Searching…", "Writing…") if the backend does not actually report such phases — a static,
honest "Thinking…" indicator is better than invented, untrue phases that sooner or later
will be exposed as a facade.
