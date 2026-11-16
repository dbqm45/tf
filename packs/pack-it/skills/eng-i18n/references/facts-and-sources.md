# Fakty i źródła do eng-i18n

Fakty sprawdzone przez agenta `researcher` 2026-10-18. Strony źródłowe nie zostały otwarte z sesji w chmurze
(WebFetch ENOTFOUND, proxy 403), więc werdykty opierają się na streszczeniach wyszukiwarki z oficjalnych domen —
oznaczenie [wtórne].

| Fakt | Źródło | Status |
|---|---|---|
| Polski ma kategorie liczby mnogiej (cardinal): `one`, `few`, `many`, `other`. | unicode.org/cldr/charts/45/verify/numbers/pl.html; unicode.org/reports/tr35/47/tr35-numbers.html | [wtórne] |
| ICU MessageFormat: `plural` wybiera podkomunikat wg reguł języka (wymagane `other`, `=N` ma pierwszeństwo, `#` to liczba); `select` wybiera wg słowa kluczowego. | unicode-org.github.io/icu/userguide/format_parse/messages/ | [wtórne] |
| MessageFormat 2 stabilny od CLDR 47 (13.03.2025); stabilne tylko funkcje `:string`, `:number`, `:integer`, reszta w wersji roboczej; implementacje ICU (Java, C++) w fazie technology preview. | blog.unicode.org/2025/03/unicode-cldr-47-release-messageformat-2.html; cldr.unicode.org/downloads/cldr-47 | [wtórne] |
| `Intl.NumberFormat` dostępny we wszystkich przeglądarkach od 2017, `Intl.RelativeTimeFormat` od 2020 (Baseline MDN). | developer.mozilla.org/…/Global_Objects/Intl | [wtórne] |
| Temporal: TC39 Stage 4 (ES2026); domyślnie w Firefox 139 i Chrome/Edge 144; Safari — źródła sprzeczne. | github.com/tc39/proposal-temporal (README, issues) | [wtórne; nie z MDN] |
| IANA tzdb to baza reguł stref; czasy przyszłe są przewidywaniem, bo rządy zmieniają reguły — dla zdarzeń przyszłych zapisuje się czas lokalny i strefę. | iana.org/time-zones/theory; data.iana.org/time-zones/tz-link.html | [wtórne] |
| „UTC dla momentów z przeszłości” — praktyka, IANA tego wprost nie podaje. | — | [założenie] |
| Miejsca po przecinku: JPY 0, KWD 3, BHD 3 (CLDR `supplementalData.xml`, `<fractions>`; listy SIX nie sprawdzono). Kwota w najmniejszej jednostce to praktyka, nie zapis normy. | github.com/unicode-org/cldr, `common/supplemental/supplementalData.xml` (main, dostęp 2026-10-20) | potwierdzone w CLDR |
| Android: pseudolokalizacje `en-XA` (akcenty, wydłużenie, nawiasy) i `ar-XB` (kierunek RTL), włączane `pseudoLocalesEnabled` w buildType. | developer.android.com/guide/topics/resources/pseudolocales | [wtórne] |
| `margin-inline-start` odpowiada `margin-left` w LTR i `margin-right` w RTL (zapis poziomy); MDN zaleca atrybut HTML `dir` zamiast CSS `direction`. | developer.mozilla.org/…/margin-inline-start; …/direction | [wtórne] |

Kategorie liczby mnogiej (CLDR `common/supplemental/plurals.xml`, main, dostęp 2026-10-20): arabski — zero (0), one (1),
two (2), few (n % 100 = 3..10), many (n % 100 = 11..99), other; polski — one, few, many, other (ułamki), bez zero i two.
