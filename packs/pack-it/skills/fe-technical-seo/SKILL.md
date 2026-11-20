---
name: fe-technical-seo
description: Use for technical SEO of public pages — indexing (robots.txt, noindex), canonical, hreflang, sitemap, structured data, rendering, status codes.
disable-model-invocation: true
metadata:
  status: "inactive"  # measured 2026-11-16: docs/inactive-skills.md
  review: "2027-04-24"
  visibility: name
  catalog: "Use when public pages must be crawled and indexed correctly by search engines — robots.txt versus noindex (X-Robots-Tag, meta robots), status codes and soft 404, redirects, canonical and duplicates, language versions (hreflang, x-default, reciprocal links), the sitemap (limits, lastmod, sitemap index), faceted navigation and URL parameters, rendering (SSR, static, hydration; JavaScript SEO, dynamic rendering as a deprecated workaround), title and description, JSON-LD structured data (schema.org, Rich Results Test), the post-deployment check (curl, Search Console). Not for performance and Core Web Vitals (fe-web-platform), translations and formats (eng-i18n), content and tone (ux-content-design) or framework configuration beyond metadata (fw-nextjs, fw-angular)."
  keywords: "SEO, techniczne SEO, indeksowanie, Google nie indeksuje, strona w Google mimo robots.txt, robots.txt, noindex, X-Robots-Tag, meta robots, canonical, rel=canonical, duplikaty treści, hreflang, x-default, wersje językowe w Google, sitemap, sitemap.xml, mapa witryny, lastmod, crawl budget, nawigacja fasetowa, filtry w URL, soft 404, Search Console, dane strukturalne, JSON-LD, schema.org, rich results, rozszerzone wyniki, generateMetadata, JavaScript SEO, SSR dla SEO, technical SEO, indexing, Google does not index, page in Google despite robots.txt, duplicate content, language versions in Google, site map, faceted navigation, filters in URL, structured data, enhanced results, SSR for SEO"
---

# Technical SEO

Goal: a search engine can **crawl** the page, **understand** which version is the right one, and **index** it
with the correct title, description and data. Facts about Google according to Google Search Central (search 2026-10-24).

## Procedure
1. **Crawling versus indexing — two different mechanisms.**
   - robots.txt controls crawling, not indexing. A URL blocked in it can end up in the index (without a description)
     when links lead to it.
   - To keep a page out of the results: `noindex` in `<meta name="robots">` or the `X-Robots-Tag` header — and **do not
     block** it in robots.txt, because the crawler will not see the `noindex`. Google does not support `noindex` in robots.txt
     (since 2019). Private content: a password or authentication, not SEO.
   - Test and preview environments: authentication or `X-Robots-Tag: noindex` on the whole host.
2. **Status codes tell the truth**: a missing page → 404 or 410, not "Not found" with 200 (soft 404); a permanent change
   of address → 301/308. In an SPA without status codes: a JavaScript redirect to a URL returning 404 or a `noindex`
   added by a script; it is better to render on the server.
3. **One URL per piece of content**: a redirect from the variants (http/https, `www`, trailing slash) and
   `rel="canonical"` on the right page pointing to itself. Canonical is a strong signal, not a directive;
   several different canonicals on a page → Google may ignore all of them. The canonical of a language version points to
   the same language version, not another one.
4. **Language versions (`hreflang`)**: every version lists all versions, including itself; the link must be
   reciprocal (no return link → the annotations may be ignored); `x-default` for the language selection page or the
   default page. In `<head>`, an HTTP header or the sitemap — from a single data source.
5. **Sitemap**: only canonical URLs with status 200 and without `noindex`; up to 50,000 URLs and 50 MB
   (uncompressed) per file, larger → a sitemap index; `lastmod` = the last significant content change (Google uses it only
   when it is consistently true); the sitemap URL in robots.txt. Pinging a sitemap in Google does not work (turned off in 2023).
6. **Filters and parameters**: filter URLs that are not to be in the index → `Disallow` in robots.txt or filters
   in the `#` fragment; canonical reduces the crawling of filters only gradually. Parameters separated by `&`,
   in a fixed order.
7. **Rendering**: content, links (`<a href>`) and metadata in the HTML from the server — SSR, static generation or
   hydration. Routing through the History API, not `#` fragments. Google calls dynamic rendering (separate HTML for bots)
   a deprecated workaround.
8. **Title and description**: a unique, descriptive `<title>` and `meta description` per page, from the page content (a template
   with the product name, not one title for the whole site).
9. **Structured data**: JSON-LD with the schema.org vocabulary (e.g. `Product` + `Offer` with `price`, `priceCurrency`,
   `availability`; `BreadcrumbList`) matching what the user sees. The Rich Results Test checks validity,
   but does not guarantee a rich result. Data from the database in `<script type="application/ld+json">` with `<` escaped.
10. **Post-deployment check**: `curl` (status code, `X-Robots-Tag`, `<head>` before JavaScript) and Search Console
    (URL Inspection, the indexing and rich results reports). Page performance: fe-web-platform.

## Example
A shop in Next.js 16.4.3 with `/pl` and `/en`: `generateMetadata` returns the canonical of the same language version
and `alternates.languages` with `pl`, `en`, `x-default` from one function also used by `app/sitemap.js`;
an unknown product → `notFound()` → status 404 and `noindex`; `app/robots.js` blocks `/koszyk` and `/*?sort=`
and gives the sitemap URL; JSON-LD `Product` with `Offer` in PLN. The `curl` output of every response:
`references/nextjs-and-verification.md`.

## Checklist
- [ ] nothing that is to stay out of the index relies only on robots.txt; pages with `noindex` are not blocked in it
- [ ] a missing page returns 404/410; permanent redirects 301/308
- [ ] one canonical per page, pointing to the canonical URL of the same language version
- [ ] `hreflang` reciprocal, with `x-default`, from one source shared with the sitemap
- [ ] sitemap: only canonical 200s, a true `lastmod`, the URL in robots.txt
- [ ] content and metadata in the HTML from the server; JSON-LD matches the visible content

## Sources
- Google Search Central (developers.google.com/search/docs): "Robots.txt Introduction", "Block Search Indexing with
  noindex", "Consolidate duplicate URLs", "Localized Versions of your Pages", "Build and Submit a Sitemap",
  "Managing crawling of faceted navigation URLs", "Redirects and Google Search", "Influencing Title Links", "Understand JavaScript SEO Basics", "Dynamic Rendering as
  a workaround", "General Structured Data Guidelines"; blog: "Sitemaps ping endpoint is going away" (2023) —
  content established by search on 2026-10-24 (the pages were not directly reachable from the session).
- schema.org: types and properties from `data/schema.ttl` (schemaorg/schemaorg, commit e5133e0, read 2026-10-24).
- Next.js 16.4.3: the example was built and checked with `curl` on 2026-10-24.
- Topic inspiration: Addy Osmani, the `seo` skill — no content was taken over.
Described in our own words.
