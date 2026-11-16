# Pętla deweloperska (Developer Experience)

Pętla deweloperska to droga od sklonowania repozytorium do uruchomionej aplikacji i zielonych testów, a potem od
zmiany do odpowiedzi testów. Dla agenta to warunek pracy sprawdzalnej. Agent, który nie umie postawić bazy, zgaduje
albo pomija testy. Agent, który po każdej zmianie czeka 6 minut na cały zestaw, ma mniej prób na zadanie i większy
koszt.

## 1. Jedno polecenie startowe
- `make setup` / `just setup` / `task setup` (albo `npm run setup`) robi wszystko, czego potrzebuje świeży klon:
  instaluje zależności z lockfile'a (`npm ci`, `uv sync`, `poetry install --sync`), stawia usługi
  (`docker compose up -d --wait`), stosuje migracje i ładuje dane startowe.
- Obok jest `make dev` (aplikacja z przeładowaniem) i `make test` (cały zestaw). Te same nazwy w każdym
  repozytorium zespołu.
- Polecenia wpisz w README (sekcja „Szybki start”) i w CLAUDE.md lub AGENTS.md (sekcja komend). Agent czyta je
  zamiast zgadywać.
- Polecenie jest idempotentne: drugie uruchomienie niczego nie psuje.

## 2. Usługi lokalnie
- Zależności usług (PostgreSQL, Redis, kolejka, wyszukiwarka) w `compose.yaml` z wersjami jak na produkcji.
- **Healthcheck** przy każdej usłudze i `depends_on: { db: { condition: service_healthy } }`. W poleceniu
  startowym `docker compose up -d --wait`. Bez tego testy startują przed bazą i padają losowo.
- Testy integracyjne mogą zamiast tego stawiać usługi same: Testcontainers (Java, .NET, Go, Node, Python). Wtedy
  testy nie zależą od tego, czy ktoś uruchomił compose.
- Devcontainer (`.devcontainer/devcontainer.json`) opłaca się, gdy narzędzia są trudne do zainstalowania (kilka
  języków, natywne biblioteki, konkretne wersje CLI) albo zespół pracuje w Codespaces. Przy prostym stosie wystarczy
  compose i menedżer wersji (`.nvmrc`, `.python-version`, `mise.toml`).

## 3. Dane startowe i sekrety deweloperskie
- Skrypt danych startowych (seed) jest idempotentny i tworzy dane **syntetyczne**: kilku użytkowników z rolami,
  przykładowe rekordy dla głównych przepływów. Nigdy kopia produkcji (arch-privacy-compliance).
- `.env.example` ma wszystkie zmienne z pustymi wartościami albo oczywistymi atrapami
  (`DATABASE_URL=postgres://dev:dev@localhost:5432/app`). Prawdziwy klucz w tym pliku trzeba unieważnić, bo jest
  w historii gita (ops-secrets-identities).
- Usługi zewnętrzne w pracy lokalnej zastępują atrapy lub sandboxy dostawcy (Stripe w trybie testowym, lokalny
  serwer SMTP jak Mailpit). Agent nie potrzebuje prawdziwych kluczy do uruchomienia testów.

## 4. Szybka odpowiedź testów
- Testy powiązane ze zmianą: `npx vitest related <pliki> --run`, `npx jest --findRelatedTests <pliki>`,
  `npx nx affected -t test`, `pytest --lf` albo `pytest-testmon`, `go test ./<pakiet>/...`. Cały zestaw przed
  commitem lub w CI.
- Podział na szybkie (jednostkowe, sekundy) i wolne (integracyjne, e2e) z osobnymi poleceniami
  (`make test-unit`, `make test-int`). W CLAUDE.md wpisz, który zestaw agent uruchamia po zmianie, a który przed
  oddaniem pracy.
- Bramki lokalne (hook po edycji, pre-commit) opisuje eng-local-quality-gates.

## 5. Miara: od klonu do zielonych testów
Mierz to, zamiast oceniać na oko. Wynik i datę zapisz w raporcie gotowości.
1. Świeży klon do pustego katalogu tymczasowego, bez cache'ów projektu:
   `git clone <repo> /tmp/clone-check && cd /tmp/clone-check`.
2. Postępuj tylko według README i CLAUDE.md, bez wiedzy z głowy, i mierz czas: `time make setup && time make test`.
3. Zapisz w raporcie:
   - czas całkowity;
   - każde miejsce, w którym trzeba było zgadywać albo zapytać człowieka;
   - kroki ręczne.
   - Każdy krok ręczny to poprawka na liście.
4. Orientacyjny cel: setup poniżej 15 minut na zwykłej maszynie, zero kroków ręcznych poza wpisaniem własnych
   kluczy do `.env`. To cel zespołu, a nie norma branżowa [założenie — dostosuj do projektu].

Pomiar uruchamia instalację i usługi, więc robisz go za zgodą człowieka, w katalogu tymczasowym, bez prawdziwych
sekretów.

## 6. Fakty ze skryptu
`scripts/readiness_check.py` zwraca sekcję `dx`:
- `setup` — wykryte polecenia startowe (`make`/`just`/Taskfile, skrypty `dev`/`setup`, sekcja w README);
- `services_needed` — usługi wynikające z zależności (sterownik `pg` → postgres, `ioredis` → redis…);
- `services`, `services_without_healthcheck` — usługi z compose;
- `devcontainer`;
- `related_tests` — polecenie testów powiązanych ze zmianą dla wykrytego runnera.

Ustalenia obszaru `dx` mają wagi:

| Ustalenie | Waga |
|---|---|
| wartość wyglądająca na prawdziwy sekret w `.env.example` (w wyniku tylko nazwa zmiennej) | wysoka |
| brak polecenia startowego | średnia |
| usługi bez środowiska lokalnego | średnia |
| usługa zależna bez healthchecka | niska |
| baza bez danych startowych | niska |

Skrypt nie mierzy czasu i niczego nie uruchamia — pomiar z punktu 5 należy do agenta, za zgodą człowieka.
