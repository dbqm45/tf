---
name: eng-project-reconstruction
description: Użyj, gdy z samego kodu trzeba odtworzyć, czym jest projekt — stack, moduły, domeny, wymagania, reguły, standardy — raport z dowodami.
metadata:
  przeglad: 2027-04-23
  katalog: "Użyj, gdy trzeba z samego repozytorium (duże, stare, wiele języków, bez dokumentacji) odtworzyć opis projektu: stack, moduły, domeny i słownik, wymagania z testów i walidacji, reguły biznesowe, standardy faktycznie stosowane w kodzie, ryzyka, pytania do ludzi — raport w docs/project/00-reconstruction/ z dowodem plik:linia przy każdym twierdzeniu, szkice CLAUDE.md i REVIEW.md ze standardów, odświeżanie przyrostowe po zmianach (manifest z hashami), wersja HTML do czytania. Najpierw skrypty bez modelu (spis i partie w budżecie, graf, historia gita, standardy, schemat bazy), potem karty modułów tańszym modelem, synteza mocniejszym, kontrola dowodów skryptem. Nie do opisu architektury przed refaktorem z oceną i roadmapą (eng-legacy-dossier), samej mapy i wpływu zmiany (eng-codebase-mapping), długu (eng-tech-debt-audit) ani pełnego audytu z bezpieczeństwem (eng-code-audit)."
  slowa: "rekonstrukcja projektu, odtworzyć z kodu, z samego kodu, czym jest ten projekt, przejąłem repozytorium, przejęte repo, duże repozytorium, bez dokumentacji, raport o projekcie, opis projektu, stack projektu, domeny z kodu, wymagania z kodu, wymagania z testów, reguły biznesowe z kodu, standardy z kodu, konwencje zespołu, których zespół przestrzega, agent ma pisać tak samo, CLAUDE.md z kodu, REVIEW.md, słownik domeny z kodu, odświeżyć raport, zaktualizować raport, zmieniło się kilkadziesiąt plików, maister, automat ma znać projekt, kontekst dla agenta, raport w przeglądarce, raport HTML, pokazać raport zarządowi"
---

# Rekonstrukcja projektu z kodu

Cel: z samego repozytorium powstaje raport, który człowiek czyta w kwadrans, a agent (np. automat historyjek) czyta
przy każdej zmianie. Kod jest źródłem prawdy, każde twierdzenie ma dowód `plik:linia` albo oznaczenie
[założenie] / [niezweryfikowane] / [pytanie] (core-grounding). Nic w kodzie nie zmieniasz.

**Taniej niż „przeczytaj repo”:** model nigdy nie czyta całego repozytorium. Najpierw liczą skrypty (zero tokenów),
model dostaje streszczenia i partie w budżecie; najtańszy wystarczający model na krok (core-cost-control).
Skrypty leżą w `.claude/skills/eng-codebase-mapping/scripts/`; niżej podaję same nazwy.

## Procedura
0. **Zakres i budżet.** Commit HEAD, zakres (całość albo katalogi), budżet USD od człowieka. `repo_inventory.py
   <repo>` podaje tokeny i partie — szacunek kosztu (partie × cennik modelu kart) pokaż przed startem. Plan przebiegu
   z polami do odhaczenia w `docs/project/00-reconstruction/plan.md` — po przerwie wznawiasz od niego.
1. **Spis bez modelu, jednym poleceniem:** `recon_scan.py <repo> --out docs/project/00-reconstruction/raw` —
   inwentarz i partie, graf, historia, standardy z idiomami, schemat bazy do `raw/*.json`, na ekran streszczenie.
   Czytasz streszczenie; po szczegóły sięgasz do konkretnego pliku JSON, nie uruchamiasz skanów osobno.
2. **Karty modułów** — zawsze wykonawcy na najtańszym modelu (Haiku), także w małym repozytorium: partia
   z `raw/inventory.json` = jedno zadanie, równolegle (drobne partie łącz po kilka w jedno zadanie). Główny model
   nie czyta plików źródłowych partii; wykonawca zapisuje kartę do pliku i odpowiada jedną linią. Wszystkich
   wykonawców uruchamiasz w jednej wiadomości, na pierwszym planie (bez pracy w tle), i czekasz na ich odpowiedzi —
   nie odpytujesz katalogu `modules/` w pętli (każde sprawdzenie to tura z pełnym kontekstem). Prompt ze stałym
   początkiem (`references/prompt-karty.md`) i zmienną końcówką (lista plików partii) — wspólny prefiks trafia
   w cache. Wynik: JSON wg `references/karta-modulu.json` w `modules/<moduł>.json`.
   Wykonawca sam przepuszcza swoją kartę przez `recon_cards.py` (karta → `modules/<moduł>.md`, dowody względne wobec
   partii poprawione) i `recon_check.py` i poprawia złe dowody. Po wszystkich kartach `recon_check.py modules/ --repo
   <repo>`; kartę ze złym dowodem zwracasz wykonawcy raz (nie poprawiasz jej sam), potem eskalacja na mocniejszy model.
3. **Domeny i słownik** (mocniejszy model, wejście: karty + graf): subdomeny, konteksty, słownik termin → `plik:linia`,
   rozjazdy nazw kod ↔ biznes (ddd-legacy-modernization, ddd-strategic-analysis).
4. **Wymagania i reguły:** `recon_cards.py modules/ --repo <repo> --rules` składa `rules.md` z reguł kart bez
   modelu; reguły przekrojowe i ograniczenia ze `schema.json` dopisujesz pod nagłówkiem `## Reguły przekrojowe`
   (ponowne składanie go zachowuje). Wymagania z testów (nazwy, asercje),
   walidacji i endpointów z kart; każde
   z pewnością: `test` (jest test) / `kod` (tylko kod) / `do potwierdzenia`. Mapowanie (błąd → kod HTTP, lista błędów
   domenowych, wartości enuma) wypisujesz w całości, łącznie z przypadkiem domyślnym i kodem sukcesu.
5. **Standardy:** sygnał z `standards_scan` (udział, przykłady, wyjątki) → reguła po obejrzeniu przykładów. Plik na
   obszar w `standards/` + `standards/INDEX.md`. Udział < 70% to nie standard, tylko „mieszane” z wyjątkami.
   Sygnały `idiomy testów` i `idiomy kodu` oceniasz w obrębie miejsca, którego dotyczą (testy danej warstwy,
   kontrolery, agregaty), nie wobec wszystkich plików. Standard testów podaje z przykładem `plik:linia`: rodzaj testu
   na warstwę (np. test web, test repozytorium, integracyjny), bibliotekę dublerów, strukturę przypadków (podtesty,
   tabela, parametry), dane testowe (buildery, fixtures). Standard kodu: idiomy sygnatur, hermetyzacji i kontrolerów.
6. **Raport** `report.md` wg `references/raport.md`; sekcję Moduły wstawia `recon_cards.py modules/ --repo <repo>
   --into report.md` (nie przepisujesz jej; szczegóły modułów są w `modules/*.md`) + szkice `CLAUDE.draft.md` i `REVIEW.draft.md`
   (`references/szkice.md`) — do zatwierdzenia przez człowieka, nie wpisujesz ich sam do `CLAUDE.md`.
7. **Kontrola:** `recon_check.py docs/project/00-reconstruction --repo <repo> --final` — zero złych dowodów,
   wszystkie sekcje, twierdzenia bez dowodu oznaczone, tabela stacku z wymaganymi wierszami (z wersjami, CI, testami
   i konfiguracją; wiersz CI wskazuje plik pipeline'u, jeśli taki jest w repo), każdy moduł z kart wymieniony
   w sekcji Moduły i z aktualnym `modules/<moduł>.md`. Raport kosztu przebiegu (core-cost-control), potem
   `recon_manifest.py write <repo> --out docs/project/00-reconstruction/manifest.json --budget-tokens N --cost-usd X`.
8. **Wersja do czytania (opcjonalnie):** jedna strona HTML z `report.md` (spis treści, tabele, dowody jako tekst).
   Gdy sesja ma narzędzie Artifact — prywatna strona, udostępnia ją człowiek; bez niego plik
   `report.html` obok. Źródłem prawdy zostaje Markdown; strona to widok, po odświeżeniu generujesz ją od nowa.

## Wynik
`docs/project/00-reconstruction/`: `plan.md`, `raw/`, `modules/*.json`, `domain.md`, `requirements.md`, `rules.md`,
`standards/` z `INDEX.md`, `report.md`, `CLAUDE.draft.md`, `REVIEW.draft.md`, `manifest.json`
(commit bazowy, partie i pliki z hashem sha256, budżet partii, data, koszt), opcjonalnie `report.html`.

## Odświeżanie przyrostowe
`recon_manifest.py diff <repo> --manifest docs/project/00-reconstruction/manifest.json` (ten sam budżet partii
co w manifeście) → partie do odświeżenia (zmieniony hash albo nowe), usunięte (skasuj ich karty), zmienione testy.
Tylko te karty od nowa, potem synteza dotkniętych sekcji (domeny, reguły, standardy z nowymi kartami; wymagania
także ze zmienionych testów), `recon_check --final` i `recon_manifest.py write` z nowym commitem. Partie bez zmian
zostają; w raporcie data i commit odświeżenia. Ponad połowa plików zmieniona → pełny przebieg (skrypt to podpowie).

## Zasady
- **Kontekst głównego modelu jest drogi:** każda tura czyta go od nowa. Pełne wyniki zostają w plikach, model czyta
  streszczenia i karty; pliki piszesz jednym zapisem, skrypty uruchamiasz jednym poleceniem. Kod źródłowy otwierasz
  tylko, żeby sprawdzić konkretny dowód (fragment pliku, nie cały plik).
- **Dowód albo oznaczenie** — bez wyjątków; cytat przy dowodzie musi się zgadzać z kodem (sprawdza `recon_check`).
- **Czego nie widać, to nie istnieje w raporcie:** DI, refleksja, kolejki, wywołania HTTP między usługami, konfiguracja
  zewnętrzna → „Czego nie sprawdzono” i pytania do ludzi.
- **Bez sieci i bez uruchamiania kodu** repozytorium; sekretów z plików nie cytujesz (core-agent-security).
- **Budżet to STOP:** po partii, która go przekracza, zatrzymujesz się z raportem częściowym i planem dalszych partii.

## Przykład
Repo 400 tys. linii (Java + Go, 2012). `repo_inventory --budget-tokens 60000` → 38 partii, ~2,2 mln tokenów; szacunek
podany człowiekowi, zgoda na 6 USD. Skrypty kroku 1 w kilka minut; 38 kart na Haiku równolegle; 3 karty wróciły po
`recon_check` (zły cytat), jedna eskalowana. Standard „błędy przez wyjątki domenowe” — 81% klas serwisów, wyjątki
w `legacy/` → wpis z wyjątkami. Raport: 14 reguł z testem, 9 „do potwierdzenia”, 6 pytań; szkic `REVIEW.md` z 5 regułami.

## Źródła
- Claude Code — subagenci, prompt caching, koszt: dokumentacja code.claude.com i platform.claude.com.
- Zasada dowodu i oznaczeń: core-grounding; koszt i dobór modelu: core-cost-control.
