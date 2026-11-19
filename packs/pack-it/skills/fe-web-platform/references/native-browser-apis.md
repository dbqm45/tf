# Native browser APIs — before you add a library

> **Contents:** Rules · Support map (MDN browser-compat-data 8.1.4, 2026-10-01) · Patterns

The browser has many features built in (sharing, clipboard, tab synchronization, code scanner). Before you add
a dependency (and a new dependency is approved by a human anyway), check whether the platform API is enough. First, though,
check **where** it works: some popular API lists omit that half of them work only in Chromium.

## Rules
1. **Feature detection, not browser detection**: `if ('share' in navigator)`, `if ('BarcodeDetector' in globalThis)`.
   No support → the ordinary path (a "Copy link" button instead of the share sheet), not a "change your browser" message.
2. **HTTPS (secure context)** — most of the APIs below work only there; `localhost` counts as secure.
3. **User activation** — you call `share()`, permission requests, `showOpenFilePicker()`, `EyeDropper.open()`
   in a click handler. A call on page load will be rejected or will irritate the user.
4. **Permissions in context**: you ask for location or notifications only when the user does something that
   requires them, and you first explain why. A refusal is a normal result — the application keeps working.
5. **Permissions-Policy**: disable in the header the features the application does not use, also for embedded frames
   (`Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), idle-detection=()`); grant them to frames
   explicitly (`<iframe allow="screen-wake-lock">`).
6. **SSR**: on the server there is no `navigator`, `window` or `document`. In Angular: access only in the browser
   (`isPlatformBrowser(inject(PLATFORM_ID))`, `afterNextRender`), cleanup through `DestroyRef` (fw-angular).
7. **Behind an adapter**: every such API in one small service with feature detection and a fallback path. Components
   and tests know only its interface; in tests you swap the adapter (eng-module-depth: an external dependency).
8. **Data from these APIs is untrusted**: clipboard text, the `rawValue` of a QR code and a file name are user input
   (validation, no `innerHTML`, a URL from a QR code only `http(s):`). Contacts and location are personal data — minimization,
   no sending without need.

## Support map (MDN browser-compat-data 8.1.4, 2026-10-01)
Ch = Chrome/Edge, FF = Firefox, Sf = Safari, A = Android, iOS = Safari iOS. Before rollout check the current state
on MDN or in `caniuse` — support changes.

**Usable everywhere (with feature detection)**
| API | What for | Notes |
|---|---|---|
| Page Visibility (`visibilitychange`, `document.hidden`) | pausing polling, animations, video in a hidden tab | to save state on exit use `visibilitychange`, not `unload` |
| BroadcastChannel | logout, a cart or theme change in all tabs of the same origin | Sf since 15.4; do not send tokens — only a "refresh state" signal |
| ResizeObserver | a component reacting to its own size (a chart, a table) | for layout alone, container queries first (fe-css) |
| Clipboard `writeText` / `readText` | a "Copy" button | read: FF since 125, Sf and FF show a system paste confirmation; write in a click handler |
| Screen Wake Lock | a recipe, a presentation, a scanner — the screen does not turn off | Baseline 2025 (iOS since 18.4); released when the tab is hidden → request it again after `visibilitychange` |
| Geolocation (`getCurrentPosition`, `watchPosition`) | a map, "nearby" | `clearWatch` when leaving the view; `enableHighAccuracy` costs battery |
| Speech Synthesis | reading a message aloud | voices depend on the system; it does not replace a screen reader |
| Origin Private File System (`navigator.storage.getDirectory()`) | the application's private files (a cache of large data, an offline editor) | these are not the user's files on disk |

**With reservation — missing in some browsers**
| API | Where it does not work | Fallback path |
|---|---|---|
| Web Share (`navigator.share`, `canShare`) | FF desktop (flag only); Ch desktop since 128 | a "Copy link" button |
| Notification | iOS: only an app added to the home screen (with a manifest); Ch A and iOS: only through a service worker (`showNotification`) | in-app notifications; push — service-workers.md |
| Payment Request | missing in FF; the `basic-card` method removed (Chrome 100) | the providers' methods (Google Pay, Apple Pay) per their documentation, the provider's ordinary payment form |
| SpeechRecognition | FF missing; Sf only with the `webkit` prefix; in Chrome recognition usually happens on the provider's servers (the audio leaves the device — RODO, the Polish name for GDPR) | a text field; the keyboard's system dictation |
| Screen Orientation `lock()` | Ch desktop always throws `NotSupportedError`, missing in Sf/iOS; usually requires full screen | a responsive layout for both orientations |
| Vibration | missing in Sf/iOS; FF A disabled, FF desktop removed (129) | only an extra, never the only feedback |

**Chromium only, experimental — exclusively as an enhancement**
| API | Support | Notes |
|---|---|---|
| File System Access (`showOpenFilePicker`, `createWritable`) | pickers: Ch desktop, Ch A since 132 | writing to an existing file: FF 111+, Sf 26+; everywhere else `<input type="file">` + a file download |
| EyeDropper | Ch desktop | an `<input type="color">` field |
| Idle Detection | Ch; a permission request, a threshold of min. 60 s, top-level frame only | it tracks human activity — only with a clear purpose and consent |
| Contact Picker | Ch A only | manual entry, an invitation by link |
| WebOTP | Ch, Ch A; the SMS ends with the line `@your-domain #code` | `autocomplete="one-time-code"` on the field (also works in Sf) — always set it |
| BarcodeDetector | Ch A; Ch desktop only macOS and ChromeOS; you check formats with `getSupportedFormats()` | a decoding library in a Web Worker (a new dependency → approval) |
| Credential Management (`PasswordCredential`) | Chromium only | `autocomplete="username"` / `"current-password"` / `"new-password"`; passwordless login — passkeys (WebAuthn, be-auth-security) |
| Network Information (`navigator.connection`) | Chromium only | a "data saver mode" setting in the application; adaptive streaming on the player side |

**Do not use**
- **Battery Status** (`getBattery`) — Chromium only, removed from Firefox (52) because of fingerprinting; missing in Sf.
  To save energy use Page Visibility and `prefers-reduced-motion`.

## Patterns
```ts
// A wake lock that comes back after returning to the tab
let lock: WakeLockSentinel | null = null;
async function keepAwake() {
  if (!('wakeLock' in navigator)) return;
  try { lock = await navigator.wakeLock.request('screen'); } catch { /* e.g. power saving mode */ }
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && lock?.released) keepAwake();
});

// Logout in all tabs — the signal alone, without session data
const auth = new BroadcastChannel('auth');
auth.onmessage = (e) => { if (e.data === 'logout') location.assign('/login'); };
function logoutEverywhere() { auth.postMessage('logout'); location.assign('/login'); }

// Share or copy
async function shareOrCopy(data: ShareData) {
  if (navigator.canShare?.(data)) {
    try { await navigator.share(data); return 'shared'; }
    catch (e) { if ((e as DOMException).name === 'AbortError') return 'cancelled'; }
  }
  await navigator.clipboard.writeText(data.url ?? '');
  return 'copied'; // announce the result in an aria-live region
}
```
Tests: Playwright lets you grant permissions (`context.grantPermissions(['geolocation'])`) and set the location;
APIs without emulation you test through the adapter (tool-playwright).

## Sources
- D. Turnbull, [21 Native Browser APIs You Might Not Have Used Before](https://dev.to/lingodotdev/21-native-browser-apis-you-might-not-have-used-before-1nbp)
  (Lingo.dev, 2025) — the list of APIs and examples; the article does not give browser support or caveats.
- [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API) and the `@mdn/browser-compat-data` 8.1.4 package —
  support, secure context, activation and Permissions-Policy requirements. Described in our own words.
