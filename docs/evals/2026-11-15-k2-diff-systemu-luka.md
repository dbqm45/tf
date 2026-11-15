# K2 „diff systemu”: pomiar luki przed budową — 2026-11-15

Pytanie: czy modele bez dodatkowej procedury przeoczają, co zmiana zmienia w systemie (dane, API, konfiguracja,
zależności, kryteria, operacje, bezpieczeństwo)? Jeśli tak — sekcja w `qa-change-review` i skrypt `system_diff.py`.
Workspace `--packs pack-it`, obecna wersja `qa-change-review` (bez K2) i przebieg bez skilli fabryki; haiku i sonnet.
Scenariusze tylko w workspace (nie w repo), bo luka się nie potwierdziła.

| Scenariusz | Treść | Wynik |
|---|---|---|
| `sd-co-zmienia-pr` — mały diff (7 plików): `DROP COLUMN`, usunięte `AC-2`, `REMINDER_CRON`, `node-cron`, zmiana pola w odpowiedzi API, cron łamiący „jedno przypomnienie”, endpoint bez autoryzacji wysyłający mail na adres z żądania | 8 grup sprawdzeń | 8/8 we wszystkich 4 przebiegach (z obecnym skillem i bez skilli) |
| `edge-sd-bez-diffu` — „zrób diff systemu” bez wskazania zmiany | dopytanie o zakres | 4/4 |
| `sd-duzy-pr-szum` — 609 linii, 45 plików refaktoru nazw i trzy ukryte zmiany (`DROP COLUMN tax_id_verified`, `EXPORT_BUCKET`, `/export` bez `auth`), autor twierdzi „czysty refaktor” | 4 grupy | 4/4 we wszystkich 8 przebiegach (2 powtórzenia) |

Koszt: 0,83 + 1,13 = 1,96 USD. „✗” w surowym raporcie runnera dotyczą tylko niewczytania `qa-change-review`
(pytanie nie mówi o planie), nie treści.

## Wniosek
Luka niepotwierdzona: na diffach do ~600 linii modele same wypisują zmiany systemowe, także ukryte w szumie.
K2 nie jest budowane. Wracamy, gdy pojawi się prawdziwy przypadek, w którym przegląd przeoczył zmianę systemową
(wtedy ten diff jako scenariusz), albo PR większy niż to, co model czyta w całości — tam skrypt wybierający pliki
o znaczeniu systemowym miałby sens.

Surowe wyniki: `2026-11-15-k2-diff-systemu-luka.jsonl`.
