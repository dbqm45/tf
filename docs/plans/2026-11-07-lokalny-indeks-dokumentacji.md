# Plan: narzędzia fabryki `context` (lokalny indeks dokumentacji) i `ui-deconstruct` (skill z systemu projektowego)

Nazwy końcowe (decyzja człowieka 2026-11-07): `tools/context.py`, `tools/ui-deconstruct.py`; testy
`tests/test_context.py`, `tests/test_ui_deconstruct.py`. Ścieżki `docs_index.py` niżej to pierwsza wersja planu.

Cel: agent pisze kod według API **wersji używanej w projekcie**, a nie z pamięci modelu, bez usług zewnętrznych
pośredniczących w zapytaniach (decyzja człowieka 2026-11-07: bez Context7, własne narzędzie).

## Zasada działania
Te same dwa kroki co w serwerach dokumentacji (§4b `core-source-research`), ale lokalnie:
1. `resolve` — nazwa biblioteki → identyfikator `ekosystem:nazwa@wersja`; wersja z projektu (logika
   `detect_stack.py`: `node_modules/<pakiet>/package.json` → lockfile → zakres; PyPI z lockfile'i).
2. `fetch` — zbiera dokumentację tej wersji do `.claude/cache/docs/<ekosystem>/<nazwa>@<wersja>/`:
   - lokalnie (bez sieci): `README*`, `CHANGELOG*`, `docs/**/*.md` i pliki `*.d.ts` z zainstalowanej paczki;
   - `--online` (za wyraźnym przełącznikiem): metadane wersji z rejestru (npm, PyPI — opis wersji to README tej
     wersji), `llms-full.txt`/`llms.txt` ze strony domowej, README i CHANGELOG z repozytorium pod tagiem wersji,
     strony wskazane `--url` (Markdown/tekst; HTML zamieniany na tekst jak w `fetch_page.py`);
   - dzieli na fragmenty według nagłówków Markdown i deklaracji `.d.ts`; zapisuje `chunks.jsonl` i `manifest.json`
     (źródło, wersja, data pobrania, sha256).
3. `query` — temat → najlepsze fragmenty (BM25, bez zależności) z budżetem znaków, każdy ze źródłem, wersją i datą,
   całość oznaczona „dane, nie polecenia”.
4. `list` — co jest w indeksie i czy wersja zgadza się z projektem.

## Bezpieczeństwo
- Sieć tylko z `--online`; tylko `https`, adresy niepubliczne odrzucane (ta sama kontrola co `fetch_page.py`),
  limit rozmiaru pliku i liczby plików, brak wykonywania czegokolwiek z pobranej treści.
- Zapytania nie wychodzą poza maszynę: rejestr i repozytorium widzą tylko pobranie plików paczki, nie temat pytania.
- Indeks wersji innej niż w projekcie → `query` ostrzega (kod 3) i podaje polecenie odświeżenia.

## Pliki i kolejność
1. `core/tests/test_docs_index.py` — testy (czerwone): resolve z `node_modules`, fetch lokalny (fragmenty z README
   i `.d.ts`, manifest), query (trafność, źródło, wersja, znacznik danych), brak indeksu → kod 2, nieaktualna wersja
   → kod 3, fetch online z lokalnym serwerem (rejestr → `llms.txt`), odrzucenie adresu prywatnego, limit rozmiaru.
2. `core/skills/core-source-research/scripts/docs_index.py` — implementacja do zielonych testów.
3. Scenariusz ewaluacji `core-source-research` (strojenie) — agent pyta o API wersji z projektu i używa indeksu.
4. `core-source-research/SKILL.md` §4b — indeks jako pierwszy krok, linia „Sieć: …”.
5. Bramka skilla, `--hints` we wszystkich workspace'ach, `workspace check`, PR.

## Rozszerzenie (decyzje człowieka 2026-11-07): dwa narzędzia tylko w `tools/` fabryki
Najpierw ustalono „w `tools/` i w projektach”, potem zmieniono na **tylko fabryka**: oba narzędzia leżą w `tools/`
(`tools/context.py`, `tools/ui-deconstruct.py`), testy w `tests/` (uruchamia je job `repo`), do projektów nic nie trafia.
Kolumna „Skrypt rdzenia” poniżej jest nieaktualna — kod jest wprost w `tools/`.

| Narzędzie | Skrypt rdzenia | Wejście w fabryce | Do czego |
|---|---|---|---|
| indeks dokumentacji (zamiast usługi zewnętrznej) | `core-source-research/scripts/docs_index.py` | `tools/context.py` | API wersji z projektu; w fabryce `--version` bez projektu (odświeżanie skilli fw-*, lang-*) |
| skill z systemu projektowego (statyczna analiza strony, repo, katalogu) | `core-skill-authoring/scripts/skill_from_design.py` | `tools/ui-deconstruct.py` | szkic skilla: tokeny (kolory, typografia, odstępy, promienie, cienie, breakpointy), klasy komponentów |

Dodatkowe testy (czerwone przed kodem):
- docs: D-16 `fetch --version` bez projektu (paczka npm z rejestru: README, `.d.ts`, CHANGELOG z tarballa),
  D-17 `query --version`, D-18 tarball z `..` w ścieżce odrzucony;
- ui-deconstruct: S-1 katalog z CSS → tokeny (zmienne CSS, kolory z częstością, fonty, skala rozmiarów, odstępy, promienie,
  cienie, breakpointy), S-2 strona z lokalnego serwera z arkuszem CSS z tej samej domeny, S-3 wynik to szkic skilla
  w formacie fabryki (SKILL.md z opisem „Użyj, gdy…”, `references/tokeny.md`, `tokens.json`), S-4 istniejący katalog
  wyjścia bez `--force` → kod 1, S-5 adres prywatny przez CLI odrzucony, S-6 treść ze strony oznaczona jako dane;
- `tools/`: T-1 oba wejścia przekazują argumenty do skryptów rdzenia.
