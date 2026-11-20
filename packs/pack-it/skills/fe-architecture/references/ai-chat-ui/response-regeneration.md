# Response Regeneration

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/response-regeneration.

## Metadata

- **Category:** AI chat UI (at the source: Resilience)
- **Level:** Intermediate
- **Examples:** React, Vue, Svelte, Native web
- **Last updated:** 2 July 2026
- **Author:** Den Odell

## TLDR

"Because a model gives a different answer each time, regenerating is a core action, not an error
path. Re-run the prompt, keep the earlier attempts as switchable variants, and let users compare
instead of losing the previous reply."

**A context note:** this pattern is specific to AI/chat interfaces (language model responses
are non-deterministic) — it has no equivalent in ordinary, deterministic CRUD applications,
where the same request always gives the same response.

## Notes (state in 2026, corrections to the source)

- **Address tokens by `variantId`, not by `activeVariant`** — if the user switches the variant during
  streaming, the tokens would go to the wrong version. Corrected in the reducer below.
- `temperature` is not supported by all models (some reasoning models ignore or reject it) —
  ensure variety through the given API's parameters or simply through resampling; check the provider's
  documentation.
- The Web Components example corrected from `innerHTML` (model content = untrusted data) to the DOM API.
- The Svelte examples use Svelte 4 syntax (`export let`, `$:`, `on:click`). In Svelte 5: `$props()`, `$state`,
  `$derived`, `onclick` attributes.

## Problem

The user receives an "almost good" answer and wants to try once more. Bad implementations: no
regeneration option at all (the user has to retype the question), or a regenerate button **overwrites**
the previous answer — if the new version is worse, the previous, acceptable version is already
lost for good.

## Solution

Regeneration re-runs the same question and stores the result **next to** the previous one, not in its
place. The assistant's message has a list of variants + a pointer to the active variant; a "‹ 2 / 3 ›" control
lets you switch between attempts — the previous answer is never lost, it just becomes
one of several options. Regeneration enters the same cycle as the original generation: it can
stream, it can be stopped (see `stop-generation.md`), it can fail and be retried (see
`retry.md`) — it differs only in **where** the result lands.

## Code examples

### Modeling Variants (reducer)

```javascript
// Assistant turn with switchable attempts
// { id, role: 'assistant', variants: [{ id, content, status }], activeVariant: 0 }

function messageReducer(message, action) {
  switch (action.type) {
    case 'regenerate': // append a fresh, streaming variant and switch to it
      return {
        ...message,
        variants: [...message.variants, { id: action.variantId, content: '', status: 'streaming' }],
        activeVariant: message.variants.length,
      };

    case 'token': // target the variant that is streaming, not whichever one is on screen
      return {
        ...message,
        variants: message.variants.map(v =>
          v.id === action.variantId ? { ...v, content: v.content + action.chunk } : v
        ),
      };

    case 'finish': // 'complete' | 'stopped' | 'error'
      return {
        ...message,
        variants: message.variants.map(v =>
          v.id === action.variantId ? { ...v, status: action.status } : v
        ),
      };

    case 'switch': // page between attempts without losing any
      return { ...message, activeVariant: action.index };

    default:
      return message;
  }
}
```

### Regenerate and Switch Between Attempts — React

```javascript
function AssistantTurn({ message, onRegenerate, onSwitch }) {
  const { variants, activeVariant } = message;
  const active = variants[activeVariant];
  const many = variants.length > 1;

  return (
    <article className="assistant-turn">
      <div className="content">{active.content}</div>
      <footer className="actions">
        {many && (
          <div className="variant-pager" role="group" aria-label="Response versions">
            <button onClick={() => onSwitch(activeVariant - 1)} disabled={activeVariant === 0} aria-label="Previous version">‹</button>
            <span>{activeVariant + 1} / {variants.length}</span>
            <button onClick={() => onSwitch(activeVariant + 1)} disabled={activeVariant === variants.length - 1} aria-label="Next version">›</button>
          </div>
        )}
        <button onClick={onRegenerate} disabled={active.status === 'streaming'}>
          Regenerate
        </button>
      </footer>
    </article>
  );
}
```

### Regenerate and Switch Between Attempts — Vue

```vue
<template>
  <article class="assistant-turn">
    <div class="content">{{ active.content }}</div>
    <footer class="actions">
      <div v-if="variants.length > 1" class="variant-pager" role="group" aria-label="Response versions">
        <button @click="onSwitch(message.activeVariant - 1)" :disabled="message.activeVariant === 0">‹</button>
        <span>{{ message.activeVariant + 1 }} / {{ variants.length }}</span>
        <button @click="onSwitch(message.activeVariant + 1)" :disabled="message.activeVariant === variants.length - 1">›</button>
      </div>
      <button @click="onRegenerate" :disabled="active.status === 'streaming'">Regenerate</button>
    </footer>
  </article>
</template>

<script setup>
import { computed } from 'vue';
const props = defineProps({ message: Object });
defineEmits(['regenerate', 'switch']);
const variants = computed(() => props.message.variants);
const active = computed(() => variants.value[props.message.activeVariant]);
</script>
```

### Regenerate and Switch Between Attempts — Svelte

```svelte
<script>
  export let message;
  export let onRegenerate;
  export let onSwitch;
  $: variants = message.variants;
  $: active = variants[message.activeVariant];
</script>

<article class="assistant-turn">
  <div class="content">{active.content}</div>
  <footer class="actions">
    {#if variants.length > 1}
      <div class="variant-pager" role="group" aria-label="Response versions">
        <button on:click={() => onSwitch(message.activeVariant - 1)} disabled={message.activeVariant === 0}>‹</button>
        <span>{message.activeVariant + 1} / {variants.length}</span>
        <button on:click={() => onSwitch(message.activeVariant + 1)} disabled={message.activeVariant === variants.length - 1}>›</button>
      </div>
    {/if}
    <button on:click={onRegenerate} disabled={active.status === 'streaming'}>Regenerate</button>
  </footer>
</article>
```

### Regenerate — Web Components

```javascript
class AssistantTurn extends HTMLElement {
  set message(m) {
    const active = m.variants[m.activeVariant];
    const many = m.variants.length > 1;
    const content = document.createElement('div');
    content.className = 'content';
    content.textContent = active.content; // model output is untrusted — never innerHTML
    const footer = document.createElement('footer');
    footer.className = 'actions';
    if (many) {
      const pager = document.createElement('span');
      pager.textContent = `${m.activeVariant + 1} / ${m.variants.length}`;
      footer.append(pager);
    }
    const regen = document.createElement('button');
    regen.textContent = 'Regenerate';
    regen.onclick = () => this.dispatchEvent(new CustomEvent('regenerate'));
    footer.append(regen);
    this.replaceChildren(content, footer);
  }
}
customElements.define('assistant-turn', AssistantTurn);
```

### Nudging the Model to Differ

```javascript
function regenerate(messages, previousAttempts) {
  return model.chat({
    messages,
    // Push variety up as attempts accumulate so users don't get the same answer twice
    temperature: Math.min(0.7 + previousAttempts * 0.15, 1.2),
  });
}
```

### Edit-and-Resubmit Truncates the Thread

```javascript
function editAndResubmit(messages, editedId, newText) {
  const index = messages.findIndex(m => m.id === editedId);
  // Everything after the edited prompt is now stale
  const kept = messages.slice(0, index);
  return [...kept, { ...messages[index], content: newText }];
  // …then start a new generation from this truncated history
}
```

## Advantages

- The user can try to get a better answer without retyping the question from scratch.
- Storing attempts as variants makes regeneration **non-destructive** — the previous answer is
  one click away, not lost.
- The variant paginator lets you compare versions and choose the preferred one.
- Reuse of the existing streaming/stop/retry infrastructure — regeneration is not
  a separate system.
- Edit-and-resubmit gives a clean way to correct the **input**, instead of negotiating with the model over
  the output itself.

## Disadvantages / tradeoffs

- Every kept variant is a full response in memory/storage — the cost grows in long
  conversations with many regenerations.
- The variant paginator adds UI and state that must stay consistent while a **new**
  attempt is streaming.
- Without increasing temperature/sampling, regeneration can give a practically identical answer —
  the feature then looks broken.
- Edit-and-resubmit must truncate the subsequent turns of the conversation — that is destructive unless you build full
  conversation branching.
- The definition of "the answer" (for saving, exporting, further use) becomes ambiguous when one
  message has many variants.

## Related patterns

- [Stop Generation](stop-generation.md) — ai-chat-ui
- [Message Thread](message-thread.md)
- [Streaming Response](streaming-response.md) — ai-chat-ui
- [Retry](../resilience/retry.md) — Resilience
- [Prompt Input](prompt-input.md)
- Temperature and sampling — OpenAI
- Regenerate response — ChatGPT patterns
- Structuring Reducers — Redux

## When to use / when NOT to use

Reach for this pattern **only** in generative AI/chat interfaces, where the same prompt
really can give a different answer. **Do not transfer** this mechanism to ordinary, deterministic
operations (e.g. "regenerate the report") — there repeating the same operation gives the same result, and
a collection of "variants" makes no sense and only complicates the data model without any benefit.
