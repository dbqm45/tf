# Next.js App Router — metadata, sitemap, robots, structured data

> **Contents:** Shared · Product page · Sitemap and robots · Post-deployment check (any stack)

Checked on 2026-10-24 on Next.js 16.4.3 and React 19.3.1: `next build`, `next start`, responses fetched with `curl`.
A shop with `/pl` and `/en` versions, one product `kubek-termiczny` (a travel mug).

## Shared
```js
// lib.js
export const SITE = "https://sklep.example.com";
export const LANGS = ["pl", "en"];
export const PRODUCTS = {
  "kubek-termiczny": { name: { pl: "Kubek termiczny", en: "Travel mug" }, price: "89.00", updated: "2026-10-01" },
};
export function alternates(path) {
  const languages = Object.fromEntries(LANGS.map((l) => [l, `${SITE}/${l}${path}`]));
  return { languages: { ...languages, "x-default": `${SITE}/pl${path}` } };
}
```
One function builds the set of language versions for `<head>` and for the sitemap — the two lists cannot drift apart,
and every version points to all of them, including itself (reciprocal links).

## Product page
```js
// app/[lang]/produkty/[slug]/page.js
import { notFound } from "next/navigation";
import { PRODUCTS, SITE, alternates } from "../../../../lib.js";

export function generateStaticParams() {
  return ["pl", "en"].flatMap((lang) => Object.keys(PRODUCTS).map((slug) => ({ lang, slug })));
}

export async function generateMetadata({ params }) {
  const { lang, slug } = await params;
  const p = PRODUCTS[slug];
  if (!p) return {};
  const path = `/produkty/${slug}`;
  return {
    title: `${p.name[lang]} — Sklep`,
    description: `${p.name[lang]}: cena ${p.price} zł, wysyłka w 24 h.`,
    alternates: { canonical: `${SITE}/${lang}${path}`, ...alternates(path) },
  };
}

export default async function Page({ params }) {
  const { lang, slug } = await params;
  const p = PRODUCTS[slug];
  if (!p) notFound();
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name[lang],
    offers: { "@type": "Offer", price: p.price, priceCurrency: "PLN", availability: "https://schema.org/InStock" },
  };
  return (
    <main>
      <h1>{p.name[lang]}</h1>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
    </main>
  );
}
```
`.replace(/</g, "\\u003c")` — product data from the database will not close the `<script>` tag (XSS through `</script>` in the name).

The output of `curl -s /pl/produkty/kubek-termiczny` (selected lines of `<head>` and `<main>`):
```html
<title>Kubek termiczny — Sklep</title>
<meta name="description" content="Kubek termiczny: cena 89.00 zł, wysyłka w 24 h."/>
<link rel="canonical" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="pl" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="en" href="https://sklep.example.com/en/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="x-default" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Kubek termiczny","offers":{"@type":"Offer","price":"89.00","priceCurrency":"PLN","availability":"https://schema.org/InStock"}}</script>
```
An unknown product (`/pl/produkty/nie-ma`): `notFound()` gives **status 404** and `<meta name="robots" content="noindex"/>`
— no soft 404.

## Sitemap and robots
```js
// app/sitemap.js
import { LANGS, PRODUCTS, SITE, alternates } from "../lib.js";

export default function sitemap() {
  return Object.entries(PRODUCTS).flatMap(([slug, p]) =>
    LANGS.map((l) => ({
      url: `${SITE}/${l}/produkty/${slug}`,
      lastModified: p.updated,
      alternates: alternates(`/produkty/${slug}`),
    })),
  );
}
```
```js
// app/robots.js
export default function robots() {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/koszyk", "/*?sort="] }],
    sitemap: "https://sklep.example.com/sitemap.xml",
  };
}
```
`/sitemap.xml` contains, for every URL, `<loc>`, three `<xhtml:link rel="alternate" hreflang=…>` and
`<lastmod>2026-10-01</lastmod>`; `/robots.txt`:
```
User-Agent: *
Allow: /
Disallow: /koszyk
Disallow: /*?sort=

Sitemap: https://sklep.example.com/sitemap.xml
```
`lastModified` from the date of the product's last significant change, not from the build time (every build would change the date
of all URLs).

## Post-deployment check (any stack)
```bash
U=https://sklep.example.com/pl/produkty/kubek-termiczny
curl -sI "$U" | grep -iE '^(HTTP|x-robots-tag|location)'                 # status code, robots header, redirect
curl -s "$U" | grep -oE '<title>[^<]*</title>|<link rel="(canonical|alternate)"[^>]*>|<meta name="robots"[^>]*>'
curl -s -o /dev/null -w '%{http_code}\n' https://sklep.example.com/pl/produkty/nie-ma   # expected 404
curl -s https://sklep.example.com/robots.txt
```
What `curl` shows is in the HTML before JavaScript runs. Content and metadata that are not there
the crawler will see only after rendering (if at all) — in Search Console you check the rendered version
(the URL Inspection tool).
