---
name: eng-repo-readiness
description: Użyj, gdy repo ma być gotowe dla agentów — szkielet z generatora albo audyt lockfile, testów, CI.
metadata:
  przeglad: "2027-10-10"
  katalog: "Użyj, gdy repozytorium ma być gotowe do bezpiecznej, weryfikowalnej pracy agentów — nowy projekt: szkielet z oficjalnego generatora z decyzji o stacku, świeżość startera, katalog tymczasowy i polityka konfliktów plików, raport z kodem wyjścia; istniejący projekt: audyt tylko do odczytu (lockfile, komenda audytu zależności, runner testów na sucho, etapy CI, konfiguracja, cztery bramki stacku z kompensacją w CLAUDE.md), werdykt i lista poprawek. Skrypt scripts/readiness_check.py. Nie do wyboru stacku (arch-tech-selection), audytu długu w kodzie (eng-tech-debt-audit), dopasowania skilli do wersji (core-stack-sync) ani podnoszenia zależności (ops-dependency-upgrades)."
  slowa: "gotowość repo, repo gotowe dla agentów, czy agent może tu pracować, przejmujemy repo, postaw szkielet, szkielet projektu, scaffold, bootstrap, generator projektu, starter, create-app, nowy projekt od zera, audyt repo, health check repo, brak lockfile, brak testów, runner testów, porzucony starter, generator zwrócił błąd"
---

# Gotowość repozytorium do pracy agentów

Pytanie skilla: **czy agent może w tym repo od jutra pracować bezpiecznie i sprawdzalnie?** Bezpiecznie, czyli nie
nadpisze plików człowieka i nie zainstaluje czegoś po cichu. Sprawdzalnie, czyli ma lockfile, testy uruchamiane jednym
poleceniem, CI i jasne konwencje. Nowy projekt dostaje szkielet (ścieżka A), istniejący — audyt (ścieżka B).

## Zasada nadrzędna: deleguj do autorytatywnego CLI
- Jeśli istnieje narzędzie, które robi zadanie (generator projektu, `docker init`, `ng generate`, `prisma migrate dev`),
  agent je wywołuje, zamiast odtwarzać pliki z pamięci. Pamięć modelu to często składnia sprzed dwóch wydań.
- Gdy autorytatywne CLI zwróci błąd, agent też się zatrzymuje: **nie dopisuje brakujących plików ręcznie**, nie
  „dokańcza” szkieletu. Raportuje polecenie, kod wyjścia i ostatnie linie wyjścia.

## Ścieżka A — nowy projekt (szkielet)
**Warunek wstępny:** zaakceptowana decyzja o stacku (`docs/project/04-architecture/stack-decision.md`, status
`accepted`) z poleceniem generatora i jego wersją. Brak pliku → odmowa i odesłanie do arch-tech-selection. Ustalenia
z rozmowy nie zastępują pliku.
1. **Świeżość generatora** (ostrzeżenie, nie blokada):
   - `npm view <pakiet-generatora> version time.modified` albo `gh api repos/<właściciel>/<repo> --jq .pushed_at`;
   - < 3 mies. świeży · 3–6 mies. starzejący się · > 6 mies. nieaktualny → pokaż człowiekowi i zaproponuj oficjalną
     alternatywę z tej samej rodziny.
2. **Szkielet do katalogu tymczasowego** `.bootstrap-scaffold/` (nigdy wprost do korzenia repo). Generator z kodem
   ≠ 0 → STOP: katalog zostaje do inspekcji, raport ze statusem `failed`.
3. **Przeniesienie z polityką konfliktów** (tabela niżej). Klonowany starter: usuń jego `.git/` przed przeniesieniem.
   Plików człowieka nie kasujesz ani nie nadpisujesz.
4. **Po przeniesieniu:** audyt zależności (komendy:
   `.claude/skills/ops-supply-chain-security/references/audyt-zaleznosci.md`), testy i build szkieletu. Audyt nie naprawia sam — `npm audit fix` itp. tylko za zgodą.
5. **Raport** `docs/project/06-delivery/bootstrap-verification.md`: polecenie i wersja generatora, kod wyjścia,
   przeniesione pliki, konflikty `.scaffold`, wynik audytu (bezpośrednie / przechodnie), wynik testów i builda,
   następne kroki. `git init` i pierwszy commit to decyzja człowieka.

| Plik w szkielecie | Gdy w repo już istnieje |
|---|---|
| `CLAUDE.md`, `AGENTS.md`, `README.md`, `.claude/`, `docs/project/` | istniejący wygrywa; wersja generatora obok jako `<plik>.scaffold` |
| `package.json`, `pyproject.toml` i inne manifesty | istniejący wygrywa, `<plik>.scaffold` + lista różnic w raporcie do decyzji |
| `.gitignore` | scalenie dopisujące: linie generatora, których brak, bez duplikatów |
| pozostałe pliki | przeniesienie; konflikt nazwy → `.scaffold` |

## Ścieżka B — istniejący projekt (audyt tylko do odczytu)
Najpierw fakty, potem ocena:
`python3 .claude/hooks/detect_stack.py` oraz **uruchom** `python3 .claude/skills/eng-repo-readiness/scripts/readiness_check.py [katalog] [--json]`
(rodziny, lockfile, komenda audytu, runner i komenda na sucho, etapy CI, konfiguracja, pliki instrukcji; kod 1 =
ustalenia wysokiej wagi). Skrypt niczego nie uruchamia — audyt i listę testów puszczasz sam, za zgodą człowieka.
1. **Fundament:** lockfile właściwy dla ekosystemu (`requirements.txt` to słaby zamiennik), wynik audytu
   zależności (bezpośrednie osobno od przechodnich), zależności zaległe o ≥ 1–2 wersje główne (tylko główne luki).
   Rodzina bez wbudowanego audytu (Java, Dart) → „pominięto”, **nigdy „0 znalezisk”**.
2. **Środowisko wykonania:** runner testów i próba na sucho (`npx vitest list`, `npx jest --listTests`,
   `pytest --collect-only -q`, `cargo test --no-run`, `go test -list . ./...`, `dotnet test --list-tests`); etapy CI
   lint / test / build / typy / bezpieczeństwo (✓/✗); konfiguracja: `.gitignore` (wysoka), TypeScript bez `strict`
   (wysoka), brak lintera lub formatera (średnia), `.editorconfig` i `.env.example` (niska).
3. **Cztery bramki stacku per komponent** — z dowodem (plik, konfiguracja) przy każdej ocenie:
   **typy** (jawne kontrakty danych w kodzie) · **konwencje** (ustalone miejsca na routing, testy, konfigurację) ·
   **popularność w obrębie rodziny języka** (Django wśród frameworków Pythona, nie wobec Reacta) · **aktualna,
   wersjonowana dokumentacja**. Dla oblanej bramki: **gotowe do wklejenia reguły do CLAUDE.md**, np. „trasy
   w `src/routes/`, każda eksportuje `router`; middleware w kolejności rejestracji w `src/app.js`”. Nie „dodaj
   dokumentację”.
4. **Werdykt** (informuje, nie blokuje; nigdy nie rekomenduje zmiany stacku):
   - stack: `gotowe` / `gotowe-z-kompensacją` / `duże-tarcie`;
   - projekt: `zdrowe` / `wymaga-uwagi` / `krytyczne` (krytyczne podatności, brak runnera testów, ≥ 3 luki wysokie).
5. **Lista poprawek** w kolejności wpływu na pracę agenta (brak testów > niski alert audytu): co · dlaczego dla
   agenta · konkretne polecenie · wysiłek (szybko < 5 min / średnio 15–30 min / duże > 1 h). Nic nie naprawiasz sam.

Raport: `docs/project/07-review/<data>-gotowosc-repo.md` (core-project-record). Szablon obu raportów:
`references/raporty.md`.

## Przykład
**Sytuacja:** „Przejmujemy API w Express (JavaScript, bez TS). Czy agenci mogą tu pracować?”
**Wynik:** `readiness_check.py` — `package-lock.json` jest, `npm audit --json` do uruchomienia, runner testów:
BRAK (wysoka), CI tylko `npm run build`, `.gitignore` jest, linter jest, formatera brak (średnia). Audyt (za zgodą):
2 wysokie w zależnościach przechodnich, 0 w bezpośrednich. Bramki: typy ✗, konwencje ✗, popularność ✓,
dokumentacja ✓ → `gotowe-z-kompensacją`; reguły do CLAUDE.md: układ katalogów tras, kolejność middleware, wzorzec
obsługi błędów (`next(err)` + jeden handler), JSDoc na funkcjach publicznych. Projekt: `krytyczne` (brak runnera).
Poprawka nr 1: runner testów z jednym testem dymnym (średnio); nr 2: etap testów w CI; nr 3: przechodnie
podatności — czekamy na opiekuna albo `overrides` po przeglądzie.

## Checklista
- [ ] (A) generator z zaakceptowanej decyzji, nie z pamięci; świeżość sprawdzona; katalog tymczasowy
- [ ] (A) pliki człowieka i fabryki nietknięte, konflikty jako `.scaffold`; błąd generatora = stop i raport
- [ ] (B) fakty ze skryptu i poleceń przed oceną; każda ocena z dowodem `plik` lub polecenie
- [ ] (B) pominięty audyt opisany jako „pominięto”, nie „0”; bezpośrednie osobno od przechodnich
- [ ] kompensacje jako konkretne reguły do CLAUDE.md; runner testów działa albo jest poprawką nr 1
- [ ] raport w `docs/project/`; nic nie zainstalowano ani nie naprawiono bez zgody

## Źródła
- Kurs 10xDevs, ed. 3 (2026), lekcja 4.1 (dobór stacku) i moduł 1, lekcje 2 i 5 (start projektu z agentem,
  wdrożenie) — materiał szkoleniowy (dostęp 2026-10-09); opisane własnymi słowami.
- Dokumentacja CLI sprawdzona 2026-10-10 w izolowanym katalogu: `vitest list` (Vitest 3.2.4), `mocha --dry-run`
  (Mocha 11.7.1), `pip-audit --format json` (pip-audit 2.10.1), `npm view <pakiet> time.modified` (npm 10).
- Composer: `composer audit` od wersji 2.4 — [php.watch](https://php.watch/articles/composer-audit) (dostęp 2026-10-10);
  govulncheck: raportuje podatności osiągalne z kodu — [pkg.go.dev](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
  (dostęp 2026-10-10).
