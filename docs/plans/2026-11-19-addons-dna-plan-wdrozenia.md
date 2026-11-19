# Plan wdrożenia: dodatek `dna` — wiedza projektu, z której fabryka pisze kod jak zespół

Data: 2026-11-19. Status: propozycja; każdy kawałek to osobny PR, kod metodą TDD (testy czerwone przed kodem).
Podstawa: rozmowa z człowiekiem z 2026-11-18/19 (decyzje w sekcji 2) i przegląd przypadków innych firm (sekcja 9).

## 1. Cel

Zadanie z numerem Jiry albo z opisem kończy się kodem, którego nie da się odróżnić od kodu dewelopera z zespołu:
te same klocki (komponenty design systemu, tokeny, serwisy, narzędzia), te same ustalenia (standardy firmy,
zespołu i projektu) i ten sam styl co otaczający kod. Agent korzysta z dokumentacji oficjalnej **w wersji użytej
w projekcie**, a nie z pamięci modelu.

Wiedzę buduje jedno polecenie — `tf learn` (albo `python3 .tf/addons/dna/dna.py learn`) — bez pracy ręcznej.
Człowiek merguje PR zadań; nic poza tym.

Wiedza żyje w **dodatku `dna`**: cały kod, dane i wynik w jednym katalogu, który da się odpiąć, wymienić i rozwijać
niezależnie od fabryki. Fabryka korzysta z gotowych wytycznych przez stały kontrakt.

## 2. Decyzje już podjęte

| # | Decyzja | Uzasadnienie |
|---|---|---|
| D1 | Dodatek w katalogu `addons/dna/` w repo fabryki, nie w osobnym repo | jedno CI i jedna zmiana kontraktu w jednym PR; wydzielenie później `git filter-repo`, gdy pojawi się powód (inne uprawnienia, użycie bez fabryki) |
| D2 | `addons/`, nie `tools/` | `tools/` to narzędzia repo fabryki, które do projektów nie trafiają (decyzja 2026-11-07); `dna` działa w projektach |
| D3 | W projekcie jeden katalog `.tf/addons/dna/`; odpięcie = `tf addon remove dna` albo usunięcie katalogu | wymóg odpinalności |
| D4 | Rdzeń zna tylko ogólny mechanizm dodatków (kontrakt), nie nazwę `dna` | inne dodatki w przyszłości tą samą drogą |
| D5 | Bez pracy ręcznej: przyjęcie ustaleń regułą z dowodem, konflikty rozstrzyga hierarchia, korekty z pętli zwrotnej | wymóg człowieka |
| D6 | Wynik w `out/` w stałym, wersjonowanym formacie; jedno źródło prawdy `knowledge.json`, Markdown generowany z niego | spójność, sprawdzalność skryptem |
| D7 | Dokumentacja oficjalna dla dokładnej wersji z lockfile'a, wyszukiwanie lokalne (BM25), skrócony indeks w stałym kontekście | wynik Vercela: indeks w kontekście 100% wobec 79% dla skilla |
| D8 | Skille ze standardami (fe, be, mutual) z odnośnikami do Confluence i innych stron to źródło `dna`; `dna` idzie za odnośnikami | standardy firmy już spisane w skillach |
| D9 | Ustalenia mają moc (twarde, miękkie) i `since`; reguła równowagi kod ↔ standard (sekcja 4.4) | kod może być starszy niż standard |

## 3. Architektura

### 3.1 Repo fabryki

```
addons/dna/
  addon.yaml                 kontrakt: nazwa, wersja (SemVer), contract: 1, co dostarcza
  CHANGELOG.md  README.md
  dna.py                     wejście: learn | refresh | verify | docs | check | replay | status
  lib/
    detect.py                stack i wersje, monorepo, polecenia
    docs.py                  dokumentacja oficjalna dla wersji: pobranie, fragmenty, indeks, zapytania
    sources.py               ustalenia ze źródeł: skille standardów, dokumenty, Confluence, reguły innych narzędzi,
                             lint i CI, @deprecated, migracje z gita, komentarze z PR
    code.py                  katalog klocków, konwencje, wzorce
    decide.py                moc, since, przyjęcie automatyczne, hierarchia, porzucanie
    emit.py                  zapis out/ z knowledge.json
    check.py                 sprawdzenie diffu wobec wytycznych
    replay.py                odtwarzanie historycznych PR
    verify.py                schemat, dowody, cytaty, limity rozmiaru
  registry/
    docs-sources.yaml        technologia → oficjalne źródła i wzorce adresów dla wersji
    detectors/*.yaml         rozpoznawanie technologii i sygnałów stylu
  schema/knowledge.schema.json
  tests/  fixtures/
```

Zasady niezależności (sprawdzane testami w CI, osobny job `addon-dna`):
- `addons/dna/` nie importuje niczego z `core/`, `packs/`, `modes/`, `tools/`; potrzebną logikę kopiuje
  (np. z `tools/context.py`, `standards_scan.py`, `org/standards_from_docs.py`);
- w `core/` nie ma słowa `dna`;
- fabryka bez dodatku przechodzi wszystkie swoje testy i zachowuje się jak dziś;
- tylko biblioteka standardowa i PyYAML (jak silnik fabryki).

### 3.2 Projekt

```
.tf/addons/dna/
  addon.yaml  dna.py  lib/  registry/  schema/      kod (podmieniany przy aktualizacji)
  dna.yaml                                          konfiguracja projektu (opcjonalna)
  out/                                              wynik (zostaje przy aktualizacji)
  cache/                                            pełne teksty pobranych źródeł i dokumentacji (poza gitem)
```

### 3.3 Kontrakt `addon.yaml` (contract 1)

```yaml
name: dna
version: 0.1.0
contract: 1
provides:
  context: out/INDEX.md            # dołączany do stałego kontekstu (import w bloku fabryki w CLAUDE.md)
  context_extra: [out/docs-index.md]
  rules: out/rules/                # reguły z `paths`, kopiowane do .claude/rules/ przy budowie
  plan: out/knowledge.json         # wzorce, klocki, ustalenia dla zwiadu i planu
  check: "dna.py check --base {base} --json"
  docs: "dna.py docs query {tech} {query}"
  learn: "dna.py learn"
  refresh: "dna.py refresh --quiet"   # przy starcie sesji, z limitem czasu
  skill_overrides: out/skill-overrides.json   # skille skonsolidowane → name-only
```

### 3.4 Wynik `out/`

| Plik | Czyta | Kiedy | Zawartość |
|---|---|---|---|
| `INDEX.md` | model | zawsze | ≤ 15 linii: stack z wersjami, twarde ustalenia całego repo, odnośniki |
| `docs-index.md` | model | zawsze | skrócony indeks dokumentacji: technologia@wersja → tematy; ≤ 8 KB |
| `rules/<obszar>.md` | model | przy plikach z `paths` | ustalenia obszaru, najczęstsze klocki |
| `catalog/<obszar>.md` | model | na żądanie | klocki: import, warianty, przykład, status |
| `decisions/<id>.md` | model, człowiek | na żądanie | pełne ustalenie z cytatami i źródłami |
| `exemplars.json` | fabryka | zwiad | rodzaj zmiany → plik wzorcowy, powód |
| `knowledge.json` | fabryka | plan, sprawdzenie diffu | kanoniczny zapis wszystkiego |
| `skill-overrides.json` | fabryka | budowa | skille skonsolidowane przez `dna` |
| `coverage.md` | człowiek, fabryka | po `learn` | przeczytane i nieprzeczytane źródła z powodem, luki `unknown` |
| `report.md` | człowiek | na żądanie | rozstrzygnięcia z powodami, zmiany od ostatniego przebiegu, wynik `replay` |

Każda pozycja `knowledge.json`: `id`, `kind` (`fact`, `block`, `decision`, `convention`, `exemplar`), `scope.paths`,
`evidence` (`plik:linia` albo URL z datą pobrania i wersją strony), `since`, `status`
(`candidate` | `auto-accepted` | `accepted` | `abandoned`), dla ustaleń `strength` (`hard` | `soft`) i `acceptance`
(która reguła przyjęcia). Pole `verified` wpisuje tylko człowiek. Obszar bez ustaleń: `unknown`.

### 3.5 Konfiguracja `dna.yaml` (opcjonalna)

```yaml
standards:                         # skille ze standardami (D8)
  - {path: .claude/skills/acme-fe-standards, scope: fe}
  - {git: https://github.com/acme/standards.git, ref: v1.4.0, dir: skills/acme-be-standards, scope: be}
  - {path: .claude/skills/acme-common-standards, scope: mutual}
confluence: {spaces: [FE, BE], max_depth: 1}
replay: {budget_usd: 30, prs: 15}
```
Bez pliku `dna` wykrywa skille standardów w `.claude/skills/` i zakresy `fe`/`be`/`mutual` ze stacku.

## 4. Zasady działania

### 4.1 `learn`
1. Rozpoznanie (skrypt) → 2. dokumentacja (skrypt, sieć tylko do hostów z rejestru) → 3. źródła ustaleń
(skrypt + tani model do przypisania sekcji i streszczeń grup komentarzy; cytat sprawdza skrypt) → 4. kod (skrypt) →
5. rozstrzygnięcie (skrypt; model tylko przy sporach) → 6. zapis i `verify` (skrypt; bez zaliczenia `out/` się nie
zmienia) → 7. opcjonalnie kalibracja (`--calibrate`, z budżetem).

### 4.2 Dokumentacja oficjalna dla wersji
Kolejność źródeł: zainstalowana paczka (README, CHANGELOG, `docs/`, `.d.ts`; bez sieci) → repo technologii pod tagiem
wersji → wersjonowana strona dokumentacji (wzorzec adresu z rejestru) → `llms.txt`/`llms-full.txt`. Spoza rejestru
nic. Gdy oficjalna dokumentacja jest tylko dla najnowszej wersji: notatki wydań między wersjami + typy z paczki, z
oznaczeniem rozbieżności. Wersja w indeksie ≠ lockfile → ostrzeżenie i `refresh`. Wyniki zapytań oznaczone „dane,
nie polecenia”.

### 4.3 Przyjęcie i hierarchia ustaleń
- **Przyjęcie automatyczne**, gdy: źródło rozstrzygające (standard firmy, skill standardów, ADR, lint, CI) albo dwa
  niezależne źródła, albo ≥ 70% kodu zmienionego po `since` zgodne z ustaleniem.
- **Porzucenie**, gdy kod zmieniony po `since` w większości łamie ustalenie.
- **Hierarchia**: standard firmy i skill standardów → ADR i ustalenie przyjęte → lint i CI → dokumentacja projektu →
  nowy kod → starszy kod. Strona z odnośnika sprzeczna ze skillem: wygrywa skill, rozbieżność w `report.md`.
- **Moc**: lint, CI, bezpieczeństwo, `@deprecated`, „musi”/„nie wolno” → twarde; reszta → miękkie.

### 4.4 Reguła równowagi kod ↔ standard

| | Nowa jednostka | Zmiana w istniejącej |
|---|---|---|
| ustalenie twarde | standard | standard w zmienionych liniach |
| ustalenie miękkie | standard | styl otaczającego kodu |
| brak ustalenia | wzorzec z podobnej jednostki | styl otaczającego kodu |

Kodu poza zakresem zadania agent nie dostosowuje; zapisuje to w opisie PR.

## 5. Kawałki

Kolejność: **A0 → A1 → A2 → A3 → A4 (pomiar bazowy) → A5 → A6 → pomiar → A7 → A8 → pomiar → A9 → A10 → A11.**

| # | Kawałek | Zależy od |
|---|---|---|
| A0 | Mechanizm dodatków w rdzeniu (contract 1) | — |
| A1 | Szkielet `dna`: CLI, schemat, `verify`, `emit`, job CI | A0 |
| A2 | `detect`: stack, wersje, monorepo, polecenia | A1 |
| A3 | `docs`: dokumentacja oficjalna dla wersji | A2 |
| A4 | `replay`: pomiar na historycznych PR, wynik bazowy | A1 |
| A5 | `code`: katalog UI, konwencje, wzorce | A2 |
| A6 | `check`: sprawdzenie diffu, reguła równowagi, ponawianie | A5 |
| A7 | `sources`: skille standardów, Confluence, dokumenty, reguły innych narzędzi, lint, CI, git | A1 |
| A8 | `decide`: moc, przyjęcie, hierarchia, porzucanie, `name-only` | A7 |
| A9 | `refresh` i samodzielność | A3, A5, A8 |
| A10 | Pętla zwrotna z PR | A8, dostęp do platformy |
| A11 | Katalog backendu i kolejne stacki | A5 |

### A0 — mechanizm dodatków w rdzeniu
- **Co:** `tf addon add <id|ścieżka|git> | remove | list`; zapis w `.tf/config/config.yaml` (`addons:`).
  `build.py`: dla każdego dodatku z `provides.context` jedna linia importu w bloku fabryki w `CLAUDE.md`; pliki
  z `provides.rules` kopiowane do `.claude/rules/addon-<nazwa>-*.md` (kopie, nie dowiązania — Windows);
  `skill_overrides` scalane do `.claude/settings.local.json` i usuwane przy odpięciu. Skill `tf`
  i `core-delivery-lifecycle`: zwiad i plan czytają `provides.plan` (pola `wzorzec:`, `klocki:`, `ustalenia:`),
  pętla przed oddaniem uruchamia `provides.check`. Hook startu sesji: `provides.refresh` z limitem czasu (np. 20 s,
  potem w tle) i `build` reguł po zmianie. `tf doctor`: stan dodatków, zgodność kontraktu, ostatni błąd.
- **Testy:** brak dodatków = zachowanie i pliki jak dziś; dodatek z `contract: 2` ignorowany z ostrzeżeniem; błąd
  `check`/`refresh` nie blokuje sesji, trafia do `.tf/logs/hook-errors.jsonl`; `remove` usuwa import, reguły
  i nadpisania; w `core/` brak nazwy konkretnego dodatku; Windows (ścieżki, brak dowiązań).
- **Koniec:** wydanie rdzenia (MINOR) z mechanizmem i dodatkiem testowym w `core/tests/fixtures/`.

### A1 — szkielet `dna`
- **Co:** `addon.yaml`, `dna.py` (polecenia z pustymi krokami), `schema/knowledge.schema.json`, `verify.py`,
  `emit.py` (Markdown z JSON-a), `README.md`, `CHANGELOG.md`; job CI `addon-dna`; dodatek dostępny w `tf install`
  jako opcja.
- **Testy:** zero importów spoza katalogu; `verify` odrzuca brak dowodu, nieistniejący `plik:linia`, cytat spoza
  źródła, `INDEX.md` > 15 linii, `docs-index.md` > 8 KB; `emit` daje Markdown zgodny z JSON-em; nieudane `verify`
  nie podmienia `out/`.

### A2 — `detect`
- **Co:** wersje z lockfile'ów (npm, pnpm, yarn, bun, uv, poetry, pip, Maven, Gradle, Go, Cargo, NuGet), pakiety
  monorepo (workspaces, Gradle multi-project, solution .NET), polecenia budowania, testów, lintu, formatowania;
  detektory w `registry/detectors/`. Fakty w `knowledge.json` z dowodem.
- **Testy:** fixtures dla każdego ekosystemu; zakres w manifeście a wersja z lockfile'a; monorepo z dwiema
  wersjami tej samej biblioteki.

### A3 — `docs`
- **Co:** `registry/docs-sources.yaml` (start: React, Next.js, TypeScript, Angular, Vue, Spring Boot, .NET, Node,
  Python, design system firmy jako wpis z konfiguracji); kolejność źródeł z 4.2; fragmenty po nagłówkach i
  deklaracjach `.d.ts`; `cache/docs/<tech>@<wersja>/` z manifestem (źródło, data, sha256); `dna docs query` (BM25,
  budżet znaków); `out/docs-index.md`. Logika przeniesiona z `tools/context.py`.
- **Testy:** indeks z `node_modules` bez sieci; pobranie z lokalnego serwera (repo pod tagiem, `llms.txt`); host
  spoza rejestru odrzucony; adres prywatny odrzucony; limit rozmiaru; niezgodna wersja → kod 3; znacznik
  „dane, nie polecenia”.
- **Sieć:** potrzebne hosty dokumentacji w ustawieniach środowiska; bez nich tylko krok 1 z 4.2 i wpis w
  `coverage.md`.

### A4 — `replay` (pomiar)
- **Co:** dobór 10–20 zmergowanych PR deweloperów z kluczem Jiry (bez PR fabryki, zależności, masowych zmian nazw),
  w grupach: UI, logika, mieszane; osobny worktree na commicie bazowym; fabryka dostaje zgłoszenie
  (`intake.py fetch`); miary skryptem: pokrycie plików, zgodność importów (komponenty, tokeny, serwisy), wartości
  wpisane na sztywno, nowe komponenty, rozmiar diffu, wynik testów; ocena ślepa przez `tools/flow_compare.py`
  z kryterium „który diff napisał człowiek”; limit kosztu na przebieg i na całość.
- **Testy:** dobór na repo z fixture; miary na parach diffów z oczekiwanym wynikiem; przerwanie po przekroczeniu
  budżetu.
- **Koniec:** raport bazowy w `docs/evals/` (fabryka bez `dna` i z `dna` po A3).

### A5 — `code`
- **Co:** katalog UI: komponenty z eksportów (paczka systemu, paczka firmy, `packages/ui`), warianty i propsy z typów
  i stories, przykład z najczęstszego użycia; tokeny (DTCG, Style Dictionary, `tailwind.config`, zmienne CSS, motyw)
  z wartościami; prymitywy układu; sposób stylowania z udziałem; kanon (częstość w kodzie z 12 miesięcy) i
  `wycofany` (`@deprecated`, `legacy/`). Konwencje z udziałem i przykładami (port `standards_scan.py`). Wzorce na
  rodzaj zmiany z historii gita, zgodne z twardymi ustaleniami, z powiązanymi plikami z grafu importów (test,
  interfejs, wywołania) — mała liczba wskazanych miejsc.
- **Testy:** dwa repo w fixtures (paczka systemu; system w monorepo) z oczekiwanym katalogiem; wzorzec nie jest
  plikiem sprzed `since` ani z naruszeniem; wycofany komponent nie trafia do kanonu.

### A6 — `check`
- **Co:** sprawdzenia diffu: wartość na sztywno przy istniejącym tokenie, duplikat komponentu z katalogu, surowy
  element zamiast komponentu, bezpośrednie wywołanie zamiast klienta projektu, inny sposób stylowania; decyzja wg
  tabeli 4.4; wynik JSON z opisem dla agenta. Po stronie fabryki (A0): najwyżej 2 rundy poprawek z tym opisem
  (wzorem Airbnb i Stripe), potem oddanie z listą w opisie PR. Formatowanie wyłącznie formatterem projektu.
- **Testy:** każda reguła na przykładzie naruszenia i kodu zgodnego; twarde blokuje w zmienianym pliku tylko w
  zmienionych liniach; miękkie w zmienianym pliku ostrzega.
- **Pomiar po A6:** `replay` z `dna` (A3+A5+A6) wobec wyniku bazowego.

### A7 — `sources`
- **Co:** skille standardów (konfiguracja albo wykrycie; `SKILL.md`, `references/`, reguły dosłowne z
  identyfikatorem); odnośniki: Confluence przez API (tokeny ze środowiska, wersja strony, głębokość z konfiguracji),
  strony publiczne z dozwolonych hostów, źródła z logowaniem przez konektor albo wpis w `coverage.md`; dokumenty
  projektu (`README`, `CONTRIBUTING`, `docs/`, ADR); pliki reguł innych narzędzi (`CLAUDE.md`, `AGENTS.md`,
  `.cursor/rules`, `.github/copilot-instructions.md`, `.github/instructions/`, `.windsurf`); lint i CI (zakazane
  importy, wymagane wzorce, wyjątki); `@deprecated`, codemody, commity migracji z datą. Podział na sekcje i
  przypisanie z kontrolą cytatów (port `org/standards_from_docs.py`). Pełne teksty w `cache/`, do `out/` tylko
  ustalenia z cytatem.
- **Testy:** skill z odnośnikiem do lokalnego serwera udającego Confluence; głębokość; cytat spoza sekcji odrzucony;
  reguła z lintu wyciągnięta z konfiguracji; host spoza listy → `coverage.md`.

### A8 — `decide`
- **Co:** moc, `since`, reguły przyjęcia i porzucenia, hierarchia, scalanie duplikatów, dziennik rozstrzygnięć w
  `report.md`; `skill-overrides.json` dla skilli skonsolidowanych (`name-only`).
- **Testy:** każda reguła przyjęcia; porzucenie przy ≥ 70% naruszeń po `since`; konflikt skill ↔ strona →
  wygrywa skill i wpis w raporcie; duplikat z trzech źródeł → jedna pozycja z trzema dowodami.
- **Okres ostrzeżeń:** ustalenie przyjęte automatycznie przez pierwsze 14 dni tylko ostrzega w `check`.
- **Pomiar po A8:** `replay` z pełnym `dna`; warstwy bez zysku wyłączane w `knowledge.json` (`layers`).

### A9 — `refresh` i samodzielność
- **Co:** manifest hashy źródeł i HEAD; odświeżanie tylko zmienionych części (pliki, tagi repo standardów, wersje
  stron Confluence bez pobierania treści); budowa obszaru przy pierwszym zadaniu, które go dotyka; brak `out/` przy
  pierwszym zadaniu → `learn` w tle, zadanie korzysta z tego, co gotowe.
- **Testy:** zmiana jednego pliku → przebudowa jednego obszaru; brak zmian → brak pracy; przekroczenie czasu → praca
  w tle, sesja nie czeka.

### A10 — pętla zwrotna z PR
- **Co:** po merge PR fabryki: różnica między ostatnim commitem fabryki a wersją zmergowaną i komentarze z
  przeglądu → kandydaci; tylko komentarze, po których kod się zmienił; waga autora z `CODEOWNERS`/historii;
  potwierdzenie w drugim PR → reguła przyjęcia; PR deweloperów odświeżają wzorce i potwierdzają ustalenia.
- **Wymaga:** tokenu do GitHuba lub GitLaba w środowisku.
- **Testy:** komentarz bez zmiany kodu ignorowany; ten sam wzorzec poprawki w dwóch PR → ustalenie.

### A11 — katalog backendu i kolejne stacki
Serwisy, klienci HTTP i kolejek, repozytoria, rejestracja DI, obsługa błędów, logowanie, konfiguracja; detektory
i źródła dokumentacji dla kolejnych technologii. Każdy stack z własnymi fixtures i pomiarem `replay`.

## 6. Kryteria sukcesu
Progi do potwierdzenia po wyniku bazowym A4:
- ocena ślepa: trafność zgadywania autora spada w stronę 50%;
- zgodność importów z diffem dewelopera rośnie; wartości na sztywno i duplikaty komponentów spadają;
- testy przechodzą nie rzadziej niż w wyniku bazowym;
- `learn`: skrypty < 1 min na obszar, model ≤ 1 USD na repo [założenie];
- narzut `dna` na zadanie (zwiad, `check`, poprawki) ≤ 10% kosztu zadania [założenie];
- `refresh` bez zmian: < 2 s.

## 7. Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| błędnie przyjęte ustalenie działa w każdym zadaniu | reguły przyjęcia z dowodem, 14 dni ostrzeżeń, pętla zwrotna, porzucanie, pomiar po A8 |
| za dużo kontekstu (badanie ETH) | limity `INDEX.md` i `docs-index.md`, reguły z `paths`, `name-only`, wyłączanie warstw po pomiarze |
| historia przeglądów uczy złych nawyków (zastrzeżenie Qodo) | hierarchia: standard i lint ponad komentarzami; tylko przyjęte komentarze |
| dokumentacja wersji niedostępna albo tylko najnowsza | paczka zainstalowana jako pierwsze źródło, notatki wydań, oznaczenie rozbieżności |
| koszt `replay` | budżet na przebieg i całość, pełny zestaw tylko po kawałkach zmieniających zachowanie |
| poufność dokumentów | pełne teksty w `cache/` poza gitem, do `out/` tylko cytaty z odnośnikiem |
| różnorodność stacków | pierwsza wersja: TypeScript i React; reszta w A11 po pomiarze |

## 8. Do decyzji przed startem
1. Repo pilotażowe: front-end z design systemem i historią PR z kluczami Jiry.
2. Budżet `replay` [założenie: kilkadziesiąt USD na wynik bazowy i dwa pomiary; do potwierdzenia na pierwszym
   przebiegu].
3. Dostęp do platformy repozytorium (A4, A10); Jira i Confluence są już w środowisku.
4. Nowy status `auto-accepted` obok `verified` (które dalej wpisuje tylko człowiek).
5. Okres ostrzeżeń 14 dni dla ustaleń przyjętych automatycznie.
6. Hosty dokumentacji oficjalnej do dodania w ustawieniach środowiska (lista z `registry/docs-sources.yaml`).

## 9. Na czym opiera się plan
Przypadki przejrzane 2026-11-18/19 (szczegóły i odnośniki w rozmowie):
- **Stripe (Minions):** reguły przypięte do katalogów, wspólne dla kilku narzędzi; kontekst zadania zbierany
  deterministycznie przed startem; lint jako krok bez modelu; najwyżej dwie rundy CI.
- **Spotify (Honk):** statyczny, wersjonowany prompt; narzędzie „verify”; mało narzędzi.
- **Google (migracje):** powiązane pliki z grafu odwołań; mało wskazanych miejsc; walidacja buildem i testami;
  wybór wariantu najbliższego przykładom.
- **Airbnb (migracja testów):** sąsiednie pliki i przykłady w kontekście; ponawianie z informacją zwrotną.
- **Vercel:** indeks dokumentacji wersji w stałym kontekście zamiast skilla.
- **Qodo, Greptile, CodeRabbit:** reguły z historii przeglądów, tylko przyjęte komentarze, zakres na ścieżki.
- **Devin:** wciąganie plików reguł innych narzędzi; wiki generowana z repo.
- **Badania:** ETH (pliki kontekstu nie pomagają ogólnie, +20% kosztu), „Agent READMEs” (2303 pliki: rosną,
  rzadko maleją — dług kontekstu), FSE 2025 (różnice stylu modelu i człowieka głównie w wyrażeniach i
  formatowaniu; prompt pomaga nieznacznie).
- **Dokumentacja Claude Code:** `CLAUDE.md` < 200 linii, reguły z `paths`, hooki do egzekwowania, `skillOverrides`.
