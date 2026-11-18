# Prompt Input

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/prompt-input.

## Metadata

- **Category:** AI chat UI (at the source: Components)
- **Level:** Intermediate
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** June 29, 2026
- **Author:** Den Odell

## TLDR

"A chat composer is a textarea, not a text field: it grows with its content, sends on Enter but adds a newline on Shift+Enter, respects IME composition, and turns into a stop button while the model is replying."

## Notes (state in 2026, corrections to the source)

- `field-sizing: content` — Chromium since 2024; in the other engines check support (Baseline) and keep a JS
  auto-grow as a fallback (`@supports not (field-sizing: content)`).
- IME checking: in React `e.nativeEvent.isComposing`; elsewhere — `e.isComposing` (the `e.keyCode === 229` fallback only
  for old Safari). Also add `compositionend` handling if you send at the end of composition.
- The field needs an accessible name (`<label>` or `aria-label`); a `placeholder` alone is not one — fe-web-platform
  (`.claude/skills/fe-web-platform/references/accessibility/accessible-forms.md`).
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`, `createEventDispatcher`). In Svelte 5
  respectively: `let { … } = $props()`, `$derived`/`$effect`, `onclick` attributes, callback props instead of the dispatcher.
- Angular (fw-angular): the thread state in a `signal<Message[]>` + `computed`, the stream through `HttpClient` with
  `observe: 'events', reportProgress: true` or `fetch` in a service; `@for (m of messages(); track m.id)`.

## Problem

A naive text input in a chat/AI interface has four typical problems:
1. The user cannot write multiple lines without scrolling invisible text.
2. Enter sends an unfinished message instead of adding a new line.
3. During IME composition (Japanese, Chinese, Korean) the Enter that confirms the characters sends the message prematurely.
4. The Send button stays active while the response is being generated, which allows prompts to collide (two requests at once).

## Solution

- Use a `<textarea>`, not an `<input>`.
- Auto-grow the element up to a maximum height, then scroll.
- Enter sends; Shift+Enter (or Ctrl/Cmd+Enter) adds a new line.
- Ignore Enter during an active IME composition (`event.isComposing` or `event.keyCode === 229`).
- The button changes from Send to Stop while the response is being generated.
- Trim (`trim`) whitespace before sending.
- Clear the field and reset its height after sending.

## Code examples

### React

```javascript
function PromptInput({ onSend, busy }) {
  const [value, setValue] = useState('');
  const ref = useRef(null);

  const grow = (el) => {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  };

  const submit = () => {
    const text = value.trim();
    if (!text || busy) return;
    onSend(text);
    setValue('');
    ref.current.style.height = 'auto';
  };

  const onKeyDown = (e) => {
    // Enter sends; Shift+Enter is a newline; ignore Enter mid-IME-composition
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <textarea
      ref={ref}
      rows={1}
      aria-label="Message the assistant"
      value={value}
      placeholder="Message the assistant…"
      onChange={(e) => { setValue(e.target.value); grow(e.target); }}
      onKeyDown={onKeyDown}
    />
  );
}
```

### Vue

```javascript
<script setup>
import { ref } from 'vue';

const props = defineProps({ busy: Boolean });
const emit = defineEmits(['send']);
const value = ref('');
const el = ref(null);

function grow() {
  el.value.style.height = 'auto';
  el.value.style.height = Math.min(el.value.scrollHeight, 200) + 'px';
}

function submit() {
  const text = value.value.trim();
  if (!text || props.busy) return;
  emit('send', text);
  value.value = '';
  el.value.style.height = 'auto';
}

function onKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    submit();
  }
}
</script>

<template>
  <textarea
    ref="el"
    rows="1"
    v-model="value"
    placeholder="Message the assistant…"
    @input="grow"
    @keydown="onKeyDown"
  />
</template>
```

### Svelte

```javascript
<script>
  export let busy = false;
  let value = '';
  let el;

  function grow() {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }

  function submit() {
    const text = value.trim();
    if (!text || busy) return;
    dispatch('send', text);
    value = '';
    el.style.height = 'auto';
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
</script>

<textarea
  bind:this={el}
  bind:value
  rows="1"
  placeholder="Message the assistant…"
  on:input={grow}
  on:keydown={onKeyDown}
/>
```

### Web Components

```javascript
class PromptInput extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `<textarea rows="1" placeholder="Message the assistant…"></textarea>`;
    const el = this.querySelector('textarea');

    el.addEventListener('input', () => {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 200) + 'px';
    });

    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        const text = el.value.trim();
        if (!text || this.hasAttribute('busy')) return;
        this.dispatchEvent(new CustomEvent('send', { detail: text }));
        el.value = '';
        el.style.height = 'auto';
      }
    });
  }
}
customElements.define('prompt-input', PromptInput);
```

### Send or Stop, never both at once

```javascript
function Composer({ busy, canSend, onSend, onStop }) {
  return (
    <form className="composer" onSubmit={(e) => { e.preventDefault(); onSend(); }}>
      <textarea /* …as above… */ />
      {busy ? (
        <button type="button" onClick={onStop} aria-label="Stop generating">
          <StopIcon /> Stop
        </button>
      ) : (
        <button type="submit" disabled={!canSend} aria-label="Send message">
          <SendIcon /> Send
        </button>
      )}
    </form>
  );
}
```

### Auto-grow with CSS only

```css
.composer textarea {
  field-sizing: content;   /* grows with content where supported */
  min-height: 2.5rem;
  max-height: 12rem;       /* then it scrolls */
  resize: none;
  overflow-y: auto;
}
```

### A baseline without JavaScript

```html
<form action="/chat" method="post" class="composer">
  <textarea name="prompt" rows="1" required placeholder="Message the assistant…"></textarea>
  <button type="submit">Send</button>
</form>
```

## Advantages

- Multi-line prompts work naturally, without scrolling invisible text.
- Enter-to-send with Shift+Enter for a new line matches the convention known from other chat applications.
- Respecting IME composition prevents accidental sending of messages by users writing in Japanese, Chinese, Korean and other languages that require an IME.
- Swapping Send for Stop during generation clearly communicates the current state of the system.
- Auto-grow keeps the whole draft visible; wrapping it in a `<form>` gives a working baseline even before JavaScript loads (Progressive Enhancement).

## Disadvantages / tradeoffs

- Keyboard handling has many edge cases (IME, autocomplete confirmation, mobile keyboards) — it requires tests on real devices, not only in a desktop browser.
- Enter-to-send can surprise some users who expect Enter = a new line — the convention is common in chats, but it needs a discoverable UI (e.g. a "Shift+Enter for new line" hint).
- A JavaScript auto-grow forces a reflow on every keystroke; CSS `field-sizing` is cleaner, but not supported everywhere.
- On small screens a growing textarea competes with the on-screen keyboard for space — a sensible height limit is needed.
- Toggling the busy/idle state on the button adds state that must be synchronized with the actual course of response generation.

## Related patterns

- [Message Thread](message-thread.md) — ai-chat-ui.
- [Stop Generation](stop-generation.md) — ai-chat-ui.
- [Streaming Response](streaming-response.md) — ai-chat-ui.
- `<textarea>` — MDN.
- `KeyboardEvent.isComposing` — MDN.
- `field-sizing` — MDN.

## When to use / when NOT to use

Use this pattern whenever you build an input field for a chat/AI interface — the edge cases (IME, multiline, busy state) are real and regularly reported by users, not theoretical.

For an ordinary, single-line form field (e.g. a search box, e-mail) it is excessive — a plain `<input type="text">` without auto-grow/IME handling is enough; do not copy this complexity where there is no multi-line content to type.
