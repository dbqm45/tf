# Evidence from many sources

A symptom usually leaves traces in more than one place. Pick the first source by the symptom, read code last and only with a
hypothesis in hand, and verify the fix on every channel that showed the problem.

## Where to start, by symptom
| Symptom | First source | Then |
|---|---|---|
| an exception, HTTP 5xx | error monitoring (Sentry or similar): stack, frequency, release, affected users | logs around the event id |
| success reported, no effect (200, `ok: true`, nothing stored or sent) | logs at warn/error level that never reached the caller; monitoring for handled errors | the durable state (DB row, file, outgoing message) |
| visible only in the UI | browser console, network tab, accessibility tree (e.g. via Playwright) — separates front end from back end | the API response for the same action |
| a failing test | its full output and the test code | the commit that changed either |
| random, or only in production | monitoring: frequency, versions, regions; logs filtered by request id | a reproduction with the same data |

## Channels and their limits
- **Error monitoring.** Shows what was captured. Console warnings and handled errors appear only if capture is enabled for them, and that
  uses the event quota — check the configuration before concluding "no errors".
- **Application logs.** Decide the scale first: one incident (filter by request or entity id) or the whole population (counts per hour,
  per version). Missing correlation ids are themselves a finding.
- **The browser.** Drive the scenario with Playwright and capture console messages and network requests; this tells whether the request
  left the browser and what came back.
- **Pixels.** A screenshot given to a model yields hypotheses only — models misjudge positions and sizes. For a test, use a deterministic
  visual-regression comparison.
- **The code.** Read it to confirm or refute a specific hypothesis, not to browse.

## Swallowed errors
Typical shape: an exception is caught, logged at warn level (or not at all), and the handler still returns success.
- **The reproducing test asserts the durable effect** — the stored row, the written file, the sent message — never only the status code.
- **The fix has two parts:**
  1. stop hiding: return or propagate the error so the caller and monitoring see it;
  2. fix the operation that failed.
  Part 1 alone turns a silent 200 into a visible 500 — progress, but not a fix. Ship both, or ship part 1 knowingly with the human's
  agreement.
- Search for the same pattern elsewhere (`rg -n "except Exception:\s*$" -A2`, `catch (e) {}`), and ask why the gates missed it —
  an escape analysis in the test strategy (qa-test-design).

## Verification mirrors the investigation
Every channel that showed the problem must now show its absence: the test is green, the log has no warning for the request, monitoring
shows no new events after the release, the browser shows the expected request and response.

## A failing test in the hook loop
When a hook (e.g. `tdd_guard`) keeps reporting the same failing test after one or two fix attempts, stop patching and run the procedure
from the symptom description.

## Example — booking saved "successfully", but not stored
Report: "Customers say their booking disappears." `POST /bookings` returns 200 with `{"ok": true}`; the `bookings` table has no row;
the log shows `WARN booking insert failed: slot_id violates foreign key`.
1. Monitoring: no event — handled exceptions are not captured. Logs: 37 such warnings since Tuesday's release, all for slots created
   by the new admin import.
2. Hypotheses: (a) the import writes slots to another schema; (b) the slot id is formatted differently; (c) a transaction rollback after
   insert. Cheapest decisive check: compare a failing `slot_id` with the `slots` table → (b): the import stores ids with a prefix.
3. Red test: book an imported slot, assert a row exists in `bookings` (not the 200).
4. Fix part 1: the handler returns 409 with the error instead of `ok: true`. Part 2: the import strips the prefix; a migration fixes
   existing slots.
5. Verification: test green, no `booking insert failed` in logs for a day, monitoring now captures the error class. Trap recorded in
   `docs/project/lessons.md`: "a handler must not return ok after a failed write".
