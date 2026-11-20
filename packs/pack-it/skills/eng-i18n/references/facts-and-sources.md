# Facts and sources for eng-i18n

Facts checked by the `researcher` agent on 2026-10-18. The source pages were not opened from the cloud session
(WebFetch ENOTFOUND, proxy 403), so the verdicts are based on search engine summaries from official domains —
marked [secondary].

| Fact | Source | Status |
|---|---|---|
| Polish has the plural categories (cardinal): `one`, `few`, `many`, `other`. | unicode.org/cldr/charts/45/verify/numbers/pl.html; unicode.org/reports/tr35/47/tr35-numbers.html | [secondary] |
| ICU MessageFormat: `plural` chooses a submessage by the language's rules (`other` required, `=N` takes precedence, `#` is the number); `select` chooses by a keyword. | unicode-org.github.io/icu/userguide/format_parse/messages/ | [secondary] |
| MessageFormat 2 stable since CLDR 47 (13.03.2025); only the functions `:string`, `:number`, `:integer` are stable, the rest is a draft; the ICU implementations (Java, C++) are in the technology preview phase. | blog.unicode.org/2025/03/unicode-cldr-47-release-messageformat-2.html; cldr.unicode.org/downloads/cldr-47 | [secondary] |
| `Intl.NumberFormat` available in all browsers since 2017, `Intl.RelativeTimeFormat` since 2020 (MDN Baseline). | developer.mozilla.org/…/Global_Objects/Intl | [secondary] |
| Temporal: TC39 Stage 4 (ES2026); on by default in Firefox 139 and Chrome/Edge 144; Safari — sources contradict each other. | github.com/tc39/proposal-temporal (README, issues) | [secondary; not from MDN] |
| IANA tzdb is the database of time zone rules; future times are a prediction, because governments change the rules — for future events the local time and the time zone are stored. | iana.org/time-zones/theory; data.iana.org/time-zones/tz-link.html | [secondary] |
| "UTC for moments in the past" — a practice, IANA does not state it directly. | — | [assumption] |
| Decimal places: JPY 0, KWD 3, BHD 3 (CLDR `supplementalData.xml`, `<fractions>`; the SIX list was not checked). An amount in the smallest unit is a practice, not a provision of the standard. | github.com/unicode-org/cldr, `common/supplemental/supplementalData.xml` (main, accessed 2026-10-20) | confirmed in CLDR |
| Android: the pseudolocales `en-XA` (accents, lengthening, brackets) and `ar-XB` (RTL direction), enabled with `pseudoLocalesEnabled` in the buildType. | developer.android.com/guide/topics/resources/pseudolocales | [secondary] |
| `margin-inline-start` corresponds to `margin-left` in LTR and `margin-right` in RTL (horizontal writing); MDN recommends the HTML `dir` attribute instead of CSS `direction`. | developer.mozilla.org/…/margin-inline-start; …/direction | [secondary] |

Plural categories (CLDR `common/supplemental/plurals.xml`, main, accessed 2026-10-20): Arabic — zero (0), one (1),
two (2), few (n % 100 = 3..10), many (n % 100 = 11..99), other; Polish — one, few, many, other (fractions), without zero and two.
