---
name: eng-i18n
description: Use for many languages and markets — ICU and plurals, Intl, IANA time zones, amounts, translations, RTL.
metadata:
  review: "2027-10-20"
  catalog: "Use when a product must work in many languages, countries or time zones — on the front end and the backend: messages in ICU MessageFormat (plurals, gender, the Polish categories one/few/many/other), MessageFormat 2, formatting through Intl (dates, numbers, amounts, lists, sorting), the user's and the tenant's locale, time in UTC and IANA time zones (meetings in the future, daylight saving time changes, Temporal), monetary amounts (decimal places per ISO 4217, rounding), texts from the backend (e-mails, PDF, notifications, API errors), the translation flow and keys, pseudolocalization, RTL and CSS logical properties, i18n tests. Not for writing the texts themselves and the tone (ux-content-design), details of the browser API (fe-web-platform) or styles (fe-css)."
  keywords: "i18n, internacjonalizacja, l10n, lokalizacja aplikacji, wiele języków w aplikacji, ICU, MessageFormat, liczba mnoga, 1 plik 2 pliki 5 plików, plural, PluralRules, Intl, DateTimeFormat, NumberFormat, format daty, format kwoty, ISO 4217, locale, strefa czasowa, UTC, IANA, zmiana czasu, spotkanie przesuwa się o godzinę, Temporal, RTL, arabski, hebrajski, prawej do lewej, logical properties, pseudolokalizacja, klucze tłumaczeń, e-mail w języku użytkownika, Accept-Language, internationalization, application localization, many languages in an application, plural forms, 1 file 2 files 5 files, date format, amount format, time zone, daylight saving time change, the meeting shifts by an hour, Arabic, Hebrew, right to left, pseudolocalization, translation keys, e-mail in the user's language"
---

# Internationalization (i18n) across the whole system

**The agent's role:** it designs the system so that a new language, country or time zone requires translations and configuration,
not changes in the code — on the front end, in the backend, in e-mails and in the data. Details of the browser API (`Intl`, RTL
in CSS, SSR): fe-web-platform, `i18n.md`. Facts and sources: `references/facts-and-sources.md`.

## 1. Locale — where from and where to
- The user's locale (language + region, e.g. `pl-PL`, `en-US`) from the profile, then from `Accept-Language` / `navigator.languages`;
  stored in the profile and in the URL of public pages. The tenant's default locale for accounts without a choice (arch-multi-tenancy).
- The locale goes through every path that creates text: a request, a background job, an e-mail, a PDF, a push. A background
  job takes the locale **of the recipient**, not of the one who triggered the event.
- Separately: the language of the texts, the format of numbers and dates (region), the time zone, the currency. These are four settings, not one.

## 2. Messages — ICU MessageFormat
- Texts outside the code, with keys that describe the place (`invoice.list.empty`), parameters and context for the translator.
- Plurals and gender in the message (`{count, plural, one {# plik} few {# pliki} many {# plików} other {# pliku}}` — Polish forms of "file"),
  never gluing fragments together. Polish has the categories `one`, `few`, `many`, `other` — do not assume "1 vs the rest".
- MessageFormat 2 is stable as a specification (CLDR 47), but implementations are sometimes in a preview phase — in a new
  project check the library before you choose it; ICU MessageFormat 1 remains a safe choice.
- Backend: the same message files and the same ICU library (or a compatible one) for e-mails, PDFs and API errors.
  An API error returns a code and parameters (be-api-design); the text for a human is created in the recipient's locale.

## 3. Formatting — always through a locale library
- Dates, numbers, currencies, lists, relative time, sorting: `Intl.*` in JS, ICU / CLDR in other languages
  (`java.text`/ICU4J, Babel in Python). No hand-made "dd.MM.yyyy" formats in the code.
- Formatting at the very end (the view, the e-mail template). The API and the database keep raw values: ISO 8601, numbers,
  currency and country codes (ISO 4217, ISO 3166).

## 4. Time and time zones
- A moment that has happened (creation, payment, a log): UTC in the database (`timestamptz`), the time zone only for display.
- An event in the future in local time (a meeting, a reminder at 9:00, the end of a billing period):
  store **the local time + the IANA time zone identifier** (`Europe/Warsaw`, `America/New_York`), and compute UTC at the time of use,
  because time zone rules change. An offset (`+02:00`) is not a time zone.
- Update the time zone database (tzdata in the system, the JDK, the library) — an outdated one gives wrong hours after a change of regulations.
- Tests on a controlled clock: the time change in spring and autumn, a day of 23 and 25 hours, the turn of the year, time zones
  with a half-hour offset. In JS for new code `Temporal` where it is available (lang-javascript).

## 5. Money and currencies
- Amount = a value + a currency code; an integer in the smallest unit or a decimal type, never a float.
  The number of decimal places depends on the currency (JPY 0, PLN 2, KWD 3 — ISO 4217); take it from the data, not a constant 2.
- Display through `NumberFormat` with `currency`; currency conversion with the rate and the rate date; rounding in one
  place (be-billing-subscriptions).

## 6. Translation flow
- One source language; new keys go to the translation system (a TMS or files in the repo with review) automatically
  from CI; a missing translation = the fallback language + a warning in the logs, not an empty text or a key on the screen.
- Context for the translator: a description, a screenshot, a length limit. The process and content style: ux-content-design.
- CI: validation of the ICU syntax in all languages, unused and missing keys, parameter consistency.

## 7. Layout, RTL, length
- `<html lang dir>`, CSS logical properties (`margin-inline-start` instead of `margin-left`), mirroring of directional
  icons, `dir="auto"` for user content — fe-web-platform, fe-css.
- Texts are sometimes 30–40% longer; a design without rigid widths.
- **Pseudolocalization** in the test build (accents, lengthening, brackets; an RTL variant) — it catches texts
  hard-coded in the code, truncated labels and gluing before translation.

## Rules
- A new language = new translations and configuration, without changes in the code.
- Raw values in the API and the database, formatting at the end in the recipient's locale.
- The past in UTC; the future in local time with an IANA time zone.
- Texts with plurals and gender only through ICU; tests on `pl` (four categories) and on RTL.

## Example
**Situation:** "Meetings at 9:00 in New York show up at 8:00 or 10:00 after the time change; we are also entering the Arabic
market."
**Result (summary):**
- Cause: the meeting stored as UTC computed on the day of creation. Fix: `local_start = 09:00`, `tz =
  America/New_York`, UTC computed at display and at the reminder; migration of existing entries with the creator's time zone.
- Tests: a recurring meeting across the time change in the USA and in the EU (different dates), a participant in another time zone.
- Arabic: `dir="rtl"`, logical properties, mirrored arrow icons, RTL pseudolocalization in CI, numbers and dates through
  `Intl` with `ar`; ICU messages with the Arabic categories (zero, one, two, few, many, other; CLDR, `references/facts-and-sources.md`).

## Checklist
- [ ] locale, region, time zone and currency as separate settings; they pass to background jobs and e-mails (the recipient's locale)
- [ ] messages in ICU, without gluing; the Polish plural categories tested
- [ ] formatting through Intl/ICU at the end; the API and the database with raw values
- [ ] the past in UTC, the future as local time + an IANA time zone; time change tests; tzdata updated
- [ ] amounts without float, decimal places from ISO 4217
- [ ] a translation flow with validation in CI; a fallback language; pseudolocalization and RTL in tests

## Sources
Described in our own words; facts with the access date in `references/facts-and-sources.md`.
