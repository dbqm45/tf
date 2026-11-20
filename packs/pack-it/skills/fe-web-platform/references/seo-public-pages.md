# SEO of a public application (e.g. Angular with SSR)

It concerns pages that are meant to be found by search engines and AI assistants. You skip the panel behind the login.

## Rendering
- Public content rendered on the server or statically (Angular SSR / prerendering with hydration). Pure client-side
  rendering only behind the login.
- Check what the bot gets: the HTML **before** JS runs must contain the title, description, headings and main content.

## Core Web Vitals (75th percentile of real users)
| Metric | Good | Poor |
|---|---|---|
| LCP | ≤ 2.5 s | > 4 s |
| INP | ≤ 200 ms | > 500 ms |
| CLS | ≤ 0.1 | > 0.25 |
LCP breaks down into TTFB, the resource load delay and duration, and rendering — you start from the largest component.
Details of measurement and improvement: `core-web-vitals.md`.

## Indexing
- `robots.txt` and the sitemap up to date; important pages at most ~3 clicks from the home page.
- A canonical URL on every page (usually pointing to itself), not contradicting `noindex`.
- Pagination through ordinary `<a href>` links; redirects without chains (one hop).
- Short, readable URLs; one version (with a trailing slash or without, one host).

## Metadata
- `<title>` unique, approx. 30–60 characters; the description approx. 120–160 characters, not repeating the title.
- Open Graph and social cards for shared pages.
- In Angular: the title through the route's `title` property (and a custom `TitleStrategy`), the description and Open Graph through the `Meta` service
  (a resolver or an effect on the route) — rendered in SSR.

## Structured data
- JSON-LD (`<script type="application/ld+json">`) consistent with the page content (Organization, Product, Article,
  BreadcrumbList…). Do not mark up content the user does not see.

## AI bots
Distinguish bots collecting data for training models from search bots and citation bots in assistants — the decision
which ones to allow is made by the business and recorded in `robots.txt` (a conscious change, with an ADR).

## The verification rule
Every recommendation has a way of checking whether it worked (e.g. an indexing report, a CWV measurement from RUM after rollout).

## Source of inspiration
[claude-seo](https://github.com/AgriciDaniel/claude-seo) — CWV thresholds, the rules of indexing, metadata, rendering
and structured data, the distinction of AI bots, "how will we know it did not work" (described in our own words; without
its crawler, paid APIs and audit agents).
