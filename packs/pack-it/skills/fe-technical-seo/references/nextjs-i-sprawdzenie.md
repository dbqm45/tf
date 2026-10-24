# Next.js App Router — metadane, sitemap, robots, dane strukturalne

Sprawdzone 2026-10-24 na Next.js 16.4.3 i React 19.3.1: `next build`, `next start`, odpowiedzi pobrane `curl`.
Sklep z wersjami `/pl` i `/en`, jeden produkt `kubek-termiczny`.

## Wspólne
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
Jedna funkcja buduje zestaw wersji językowych dla `<head>` i dla sitemap — obie listy nie mogą się rozjechać,
a każda wersja wskazuje wszystkie, w tym siebie (powiązania wzajemne).

## Strona produktu
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
`.replace(/</g, "\\u003c")` — dane produktu z bazy nie zamkną tagu `<script>` (XSS przez `</script>` w nazwie).

Wynik `curl -s /pl/produkty/kubek-termiczny` (wybrane linie `<head>` i `<main>`):
```html
<title>Kubek termiczny — Sklep</title>
<meta name="description" content="Kubek termiczny: cena 89.00 zł, wysyłka w 24 h."/>
<link rel="canonical" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="pl" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="en" href="https://sklep.example.com/en/produkty/kubek-termiczny"/>
<link rel="alternate" hrefLang="x-default" href="https://sklep.example.com/pl/produkty/kubek-termiczny"/>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Kubek termiczny","offers":{"@type":"Offer","price":"89.00","priceCurrency":"PLN","availability":"https://schema.org/InStock"}}</script>
```
Nieznany produkt (`/pl/produkty/nie-ma`): `notFound()` daje **kod 404** i `<meta name="robots" content="noindex"/>`
— bez soft 404.

## Sitemap i robots
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
`/sitemap.xml` zawiera dla każdego adresu `<loc>`, trzy `<xhtml:link rel="alternate" hreflang=…>` i
`<lastmod>2026-10-01</lastmod>`; `/robots.txt`:
```
User-Agent: *
Allow: /
Disallow: /koszyk
Disallow: /*?sort=

Sitemap: https://sklep.example.com/sitemap.xml
```
`lastModified` z daty ostatniej istotnej zmiany produktu, nie z czasu budowania (każdy build zmieniałby datę
wszystkich adresów).

## Sprawdzenie po wdrożeniu (dowolny stack)
```bash
U=https://sklep.example.com/pl/produkty/kubek-termiczny
curl -sI "$U" | grep -iE '^(HTTP|x-robots-tag|location)'                 # kod, nagłówek robots, przekierowanie
curl -s "$U" | grep -oE '<title>[^<]*</title>|<link rel="(canonical|alternate)"[^>]*>|<meta name="robots"[^>]*>'
curl -s -o /dev/null -w '%{http_code}\n' https://sklep.example.com/pl/produkty/nie-ma   # oczekiwane 404
curl -s https://sklep.example.com/robots.txt
```
To, co pokazuje `curl`, jest w HTML przed uruchomieniem JavaScriptu. Treść i metadane, których tam nie ma,
crawler zobaczy dopiero po renderowaniu (o ile w ogóle) — w Search Console sprawdzisz wersję po renderowaniu
(narzędzie URL Inspection).
