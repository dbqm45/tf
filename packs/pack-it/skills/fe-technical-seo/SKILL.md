---
name: fe-technical-seo
description: Użyj przy technicznym SEO stron publicznych — indeksowanie (robots.txt, noindex), canonical, hreflang, sitemap, dane strukturalne, renderowanie, kody statusu.
metadata:
  przeglad: 2027-04-24
  widocznosc: nazwa
  katalog: "Użyj, gdy publiczne strony mają być poprawnie skanowane i indeksowane przez wyszukiwarki — robots.txt a noindex (X-Robots-Tag, meta robots), kody statusu i soft 404, przekierowania, canonical i duplikaty, wersje językowe (hreflang, x-default, powiązania wzajemne), mapa witryny (limity, lastmod, indeks map), nawigacja fasetowa i parametry w URL, renderowanie (SSR, statyczne, hydratacja; JavaScript SEO, dynamic rendering jako przestarzałe obejście), tytuł i opis, dane strukturalne JSON-LD (schema.org, Rich Results Test), sprawdzenie po wdrożeniu (curl, Search Console). Nie do wydajności i Core Web Vitals (fe-web-platform), tłumaczeń i formatów (eng-i18n), treści i tonu (ux-content-design) ani konfiguracji frameworka poza metadanymi (fw-nextjs, fw-angular)."
  slowa: "SEO, techniczne SEO, indeksowanie, Google nie indeksuje, strona w Google mimo robots.txt, robots.txt, noindex, X-Robots-Tag, meta robots, canonical, rel=canonical, duplikaty treści, hreflang, x-default, wersje językowe w Google, sitemap, sitemap.xml, mapa witryny, lastmod, crawl budget, nawigacja fasetowa, filtry w URL, soft 404, Search Console, dane strukturalne, JSON-LD, schema.org, rich results, rozszerzone wyniki, generateMetadata, JavaScript SEO, SSR dla SEO"
---

# Techniczne SEO

Cel: wyszukiwarka może **zeskanować** stronę, **zrozumieć**, która wersja jest właściwa, i **zindeksować** ją
z poprawnym tytułem, opisem i danymi. Fakty o Google wg Google Search Central (wyszukiwanie 2026-10-24).

## Procedura
1. **Skanowanie a indeksowanie — dwa różne mechanizmy.**
   - robots.txt steruje skanowaniem, nie indeksowaniem. Adres zablokowany w nim może trafić do indeksu (bez opisu),
     gdy prowadzą do niego linki.
   - Żeby strony nie było w wynikach: `noindex` w `<meta name="robots">` albo nagłówku `X-Robots-Tag` — i **nie
     blokuj** jej w robots.txt, bo crawler nie zobaczy `noindex`. `noindex` w robots.txt Google nie obsługuje
     (od 2019). Treść prywatna: hasło lub uwierzytelnienie, nie SEO.
   - Środowiska testowe i podglądowe: uwierzytelnienie albo `X-Robots-Tag: noindex` na całym hoście.
2. **Kody statusu mówią prawdę**: brak strony → 404 lub 410, nie „Nie znaleziono” z 200 (soft 404); trwała zmiana
   adresu → 301/308. W SPA bez kodów statusu: przekierowanie JavaScriptem na adres zwracający 404 albo `noindex`
   dodany skryptem; lepiej renderować po stronie serwera.
3. **Jeden adres na treść**: przekierowanie z wariantów (http/https, `www`, ukośnik końcowy) i
   `rel="canonical"` na stronie właściwej wskazujący ją samą. Canonical to silny sygnał, nie polecenie;
   kilka różnych canonicali na stronie → Google może zignorować wszystkie. Canonical wersji językowej wskazuje
   tę samą wersję językową, nie inną.
4. **Wersje językowe (`hreflang`)**: każda wersja wymienia wszystkie wersje, łącznie z sobą; powiązanie musi być
   wzajemne (brak linku zwrotnego → adnotacje mogą zostać zignorowane); `x-default` dla strony wyboru języka lub
   domyślnej. W `<head>`, nagłówku HTTP albo w sitemap — z jednego źródła danych.
5. **Mapa witryny**: tylko adresy kanoniczne ze statusem 200 i bez `noindex`; do 50 000 adresów i 50 MB
   (bez kompresji) na plik, większe → indeks map; `lastmod` = ostatnia istotna zmiana treści (Google używa go tylko,
   gdy jest konsekwentnie prawdziwy); adres mapy w robots.txt. Ping mapy w Google nie działa (wyłączony 2023).
6. **Filtry i parametry**: adresy filtrów, które nie mają być w indeksie → `Disallow` w robots.txt albo filtry
   we fragmencie `#`; canonical zmniejsza skanowanie filtrów tylko stopniowo. Parametry rozdzielane `&`,
   w stałej kolejności.
7. **Renderowanie**: treść, linki (`<a href>`) i metadane w HTML z serwera — SSR, generowanie statyczne albo
   hydratacja. Routing przez History API, nie fragmenty `#`. Dynamic rendering (osobny HTML dla botów) Google
   nazywa przestarzałym obejściem.
8. **Tytuł i opis**: unikalny, opisowy `<title>` i `meta description` na stronę, z treści strony (szablon
   z nazwą produktu, nie jeden tytuł dla całego serwisu).
9. **Dane strukturalne**: JSON-LD ze słownikiem schema.org (np. `Product` + `Offer` z `price`, `priceCurrency`,
   `availability`; `BreadcrumbList`) zgodne z tym, co widzi użytkownik. Rich Results Test sprawdza poprawność,
   ale nie gwarantuje wyniku rozszerzonego. Dane z bazy w `<script type="application/ld+json">` z zabezpieczonym `<`.
10. **Sprawdzenie po wdrożeniu**: `curl` (kod, `X-Robots-Tag`, `<head>` przed JavaScriptem) i Search Console
    (URL Inspection, raporty indeksowania i wyników rozszerzonych). Wydajność stron: fe-web-platform.

## Przykład
Sklep w Next.js 16.4.3 z `/pl` i `/en`: `generateMetadata` zwraca canonical tej samej wersji językowej
i `alternates.languages` z `pl`, `en`, `x-default` z jednej funkcji używanej też przez `app/sitemap.js`;
nieznany produkt → `notFound()` → kod 404 i `noindex`; `app/robots.js` blokuje `/koszyk` i `/*?sort=`
i podaje adres mapy; JSON-LD `Product` z `Offer` w PLN. Wynik `curl` każdej odpowiedzi:
`references/nextjs-i-sprawdzenie.md`.

## Checklista
- [ ] nic, co ma być poza indeksem, nie polega tylko na robots.txt; strony z `noindex` nie są w nim zablokowane
- [ ] brakująca strona zwraca 404/410; przekierowania stałe 301/308
- [ ] jeden canonical na stronę, wskazujący adres kanoniczny tej samej wersji językowej
- [ ] `hreflang` wzajemny, z `x-default`, z jednego źródła z sitemap
- [ ] sitemap: tylko kanoniczne 200, prawdziwy `lastmod`, adres w robots.txt
- [ ] treść i metadane w HTML z serwera; JSON-LD zgodny z widoczną treścią

## Źródła
- Google Search Central (developers.google.com/search/docs): „Robots.txt Introduction”, „Block Search Indexing with
  noindex”, „Consolidate duplicate URLs”, „Localized Versions of your Pages”, „Build and Submit a Sitemap”,
  „Managing crawling of faceted navigation URLs”, „Redirects and Google Search”, „Influencing Title Links”, „Understand JavaScript SEO Basics”, „Dynamic Rendering as
  a workaround”, „General Structured Data Guidelines”; blog: „Sitemaps ping endpoint is going away” (2023) —
  treść ustalona wyszukiwaniem 2026-10-24 (strony niedostępne bezpośrednio z sesji).
- schema.org: typy i właściwości z `data/schema.ttl` (schemaorg/schemaorg, commit e5133e0, odczyt 2026-10-24).
- Next.js 16.4.3: przykład zbudowany i sprawdzony `curl` 2026-10-24.
- Inspiracja tematu: Addy Osmani, skill `seo` — treści nie przejęto.
Opisane własnymi słowami.
