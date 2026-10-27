# Ramki Figmy w projekcie zmiany (Figma MCP)

Projekt zmiany to umowa: każde wymaganie z interfejsem ma ramkę dla każdego stanu, który jego przepływ zawiera.
Ten plik opisuje, jak to zapisać i sprawdzić przez serwer MCP Figmy. Treści ekranów: ux-content-design; dostępność
ramek: ux-accessibility; tokeny i komponenty: ux-design-systems.

## Dwa tryby pracy
- **A — dopasowanie (domyślny).** Ramki robi projektant. Agent czyta plik, dopasowuje ramki do wymagań i stanów,
  wypełnia tabelę i nazywa braki. Nie zmienia ramek projektanta.
- **B — szkic przez agenta (tylko na prośbę człowieka).** Agent zakłada ramki per ścieżka i stan z komponentów
  i tokenów systemu projektowego, w osobnej stronie oznaczonej jako szkic. Projektant poprawia; do przeglądu idą
  dopiero ramki zaakceptowane przez projektanta. Szkic agenta łatwo wziąć za gotowy projekt — dlatego nie domyślnie.

## Procedura (tryb A)
1. **Plik i sesja.** Z linku `figma.com/design/<fileKey>/…` weź `fileKey`; załóż sesję serwera Figmy dla pliku
   (wymóg serwera: sesja przed innymi narzędziami pliku).
2. **Spis ramek.** `get_metadata` (strony i ramki najwyższego poziomu: nazwy, `node-id`); `get_screenshot` dla ramki,
   której nazwa nie mówi, co pokazuje. Nie pobieraj całego pliku z detalami — wystarczy poziom ramek.
3. **Stany wymagane.** Z wymagań i kryteriów akceptacji wypisz przepływy (ścieżki) i stany: zawsze `idle`,
   `success` i co najmniej jeden stan błędu; dalej to, co wynika z treści — `empty` (lista), `loading`/`processing`
   (operacja trwa), `validation_error` (formularz), `network_failure`, `permission_denied`, `session_expired`,
   `confirmation`, `timeout`, `retry`. Lista stanów jest stała (kontrakt pdi, `conventions.design.states`).
4. **Dopasowanie.** Ramka do wiersza tylko wtedy, gdy pokazuje ten stan tej ścieżki (nazwa, tekst, zrzut). Link
   z `node-id` konkretnej ramki, nie do całego pliku. Ramka pokazująca kilka stanów może wystąpić w kilku wierszach.
5. **Braki.** Stan bez ramki: `brak` i w uwagach pytanie do projektanta („czy błąd częściowy ma osobny ekran?”).
   Stan, którego przepływ nie ma: `nie dotyczy` i powód. Nie dorysowujesz ramek w trybie A.
6. **Zapis w `design.md`** zmiany: tabela niżej, nad nią link do pliku i tryb pracy; pytania do projektanta także
   w sekcji pytań do bramki.
7. **Sprawdzenie przed przeglądem:** w trybie mode-pdi `design_check.py check CHG-n` (skrypt skilla pdi-decisions,
   tryb mode-pdi) — format, linki, stany minimalne per historyjka; braki trafiają jako pytania do bramki
   `design-review`.

## Tabela (format z kontraktu pdi, `conventions.design`)

| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |
|---|---|---|---|---|
| US-3 | wybór ładowarek | idle | https://www.figma.com/design/AbC123xyz/Taryfy?node-id=12-34 | |
| US-3/AC-3 | zastosowanie taryfy | server_error | brak | błąd częściowy (3 z 200 offline) — pytanie do projektanta |
| US-3/AC-3 | zastosowanie taryfy | session_expired | nie dotyczy | operacja trwa w tle |

- Wymaganie: `US-3` albo `US-3/AC-2` (klucz z Jiry też). Stany minimalne liczone są per historyjka.
- Nagłówek po angielsku (`Requirement | Journey | State | Frame | Notes`) też jest poprawny.

## Bez Figmy
Tabela zostaje: zamiast linku `brak` i opis stanu w uwagach (albo makieta tekstowa pod tabelą). Faza działa,
a przegląd widzi braki jako pytania.

## Przykład
**Wejście:** plik z 6 ramkami, wymaganie US-3 (AC-1 wybór, AC-2 zastosowanie z postępem, AC-3 błędy częściowe).
**Wynik:** 6 wierszy: `idle`, `empty`, `processing`, `success` z linkami; `server_error` — `brak` z pytaniem
o ekran błędu częściowego; `session_expired` — `nie dotyczy` (operacja w tle). Przegląd dostaje jedno pytanie.
