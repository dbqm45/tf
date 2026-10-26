---
name: core-git-workflow
description: Użyj przy pracy z gitem — gałęzie, commity, pull requesty i ich przegląd (także AI), konflikty.
metadata:
  przeglad: 2027-10-10
  katalog: "Użyj przy pracy z gitem — gałęzie, przygotowanie commitów, pull requesty, przegląd PR (także przez AI: REVIEW.md, claude-code-action, rozdział obowiązków, ochrona gałęzi), konflikty, operacje niebezpieczne. Nie do formatu commit message (core-conventional-commits) ani pipeline'ów CI (skill CI/CD, pack-it)."
  slowa: "worktree, równolegle dwóch agentów, zmiana kontraktu między sesjami, powiadom drugą sesję, commit fazy, przegląd AI w CI, werdykt przeglądu, skip ci, pull request, PR, code review, przegląd kodu, review przez AI, Claude przegląda PR, REVIEW.md, claude-code-action, ai-review.yml, ai_review.py, workflow przeglądu AI, ochrona gałęzi, branch protection, konflikt, rebase, merge, stos PR, stacked PR, rebase --onto, squash merge, strategia scalania, gh pr merge, zmiana bazy PR"
---

# Git workflow

## Gałęzie
- Nazwa: `<typ>/<krótki-opis>` np. `feat/user-avatar`, `fix/login-redirect`, `chore/deps-bump`.
- Praca nad cięciem albo zmianą z kluczem (`TSK-57`, `CHG-12`): klucz w nazwie gałęzi małymi literami
  (`story/tsk-57-ponowienie-platnosci`), a każdy commit ze stopką `Change: TSK-57` (core-conventional-commits).
  Hook `commit-msg` z tego skilla odrzuca commit bez stopki na takiej gałęzi. Klucz pochodzi z planu zmiany albo
  od człowieka.
- Gałęzie krótko żyjące (godziny–dni) i częsta integracja z główną (trunk-based, zob. skill dostarczania, pack-it: eng-continuous-delivery).
- Nigdy nie pracujesz bezpośrednio na `main`/`master`. Jeśli jesteś na nim — utwórz gałąź przed pierwszą zmianą.

## Commity
- Format commit message i tytułu PR: skill **core-conventional-commits** (tam też: jak poprawić zły typ commita —
  `--amend` tylko dla ostatniego, niewypchniętego commita i na wyraźną prośbę).
- Jeden commit = jedna logiczna zmiana; małe, częste commity (łatwy review i revert).

## Przed commitem
1. `git status` i `git diff --staged` — sprawdź, że commitujesz tylko zamierzone pliki.
2. Żadnych sekretów, plików `.env`, dumpów, artefaktów buildu.
3. Testy i lint przechodzą.
4. Dodawaj pliki po nazwie (`git add ścieżka`), nie `git add -A`, chyba że diff jest w pełni przejrzany.

## Commit fazy (praca według planu kroku)
- Do indeksu dodajesz **pliki dotknięte w tej fazie** (każdy Edit/Write) i raport kroku — nie listę z `git status`.
- Inne zmienione pliki pokaż i zapytaj: tylko pliki fazy (zalecane) / wszystko / przerwij. Nie dołączasz ich po cichu.
- Przed pierwszym commitem nowej zmiany sprawdź, czy w indeksie nie czekają wcześniej dodane cudze pliki.
- `git diff --cached --quiet` kończy się kodem 0 → nie ma czego commitować; pustego commita nie tworzysz.
- Temat: `<typ>(<identyfikator-zmiany>): <tytuł fazy> (f<N>)`; w treści dotknięte pliki. `Refs:` tylko z odnośników
  widocznych w rozmowie albo podanych przez człowieka, nigdy wywnioskowanych z nazwy gałęzi.
- Hook pre-commit odrzucił commit → usuń przyczynę i zrób **nowy** commit. Bez `--no-verify` i bez `--amend`
  (commit się nie odbył, więc `--amend` zmieniłby poprzednią fazę).
- Po commicie dopisz SHA w sekcji „Postęp” raportu kroku (core-project-record); przy ostatniej fazie SHA i status
  raportu idą w osobnym commicie zamykającym.

## Praca równoległa (kilka zmian naraz)
- Zacznij od **dwóch** zmian, nie pięciu: równoległość ogranicza przepustowość przeglądu człowieka, nie liczba agentów.
- Przed startem sprawdź niezależność (agent może to zrobić z planów): wspólne pliki, kontrakty (API, typy, schemat),
  migracje, usługi zewnętrzne. Konflikt → po kolei.
- Jedna zmiana = jeden worktree + jedna gałąź + jedna świeża sesja agenta:
  `git worktree add ../<repo>-<zmiana> -b feat/<zmiana>`; główny katalog służy do koordynacji.
  Fork, nowa sesja czy subagent (koszt, izolacja): `.claude/skills/core-cost-control/references/rownoleglosc.md`.
- **Zmiana kontraktu w trakcie** (API, typy, schemat) → od razu wiadomość do drugiej sesji:
  `Zmiana kontraktu: <co> · <plik/commit> · co musisz zrobić · odpowiedz „przyjęte”`. Bez „przyjęte” druga sesja
  nie scala. Kanał: od v2.1.224 `SendMessage` (lista sesji: `/peers`), od v2.1.232 `@nazwa-sesji`; tylko tekst,
  odbiór reguluje `crossSessionInbound`. Starsza wersja → tę samą wiadomość przekazuje człowiek.
- Która sesja czeka na decyzję: `claude agents` (widok agentów, research preview) pokazuje grupę „Needs input”
  (sprawdzone 2026-10-18).
- Worktree izoluje pliki i gałąź, **nie środowisko**: osobny port serwera deweloperskiego, osobna lokalna baza
  (albo schemat), osobny sandbox usług płatności i kolejek.
- Zmiana z decyzjami w trakcie → interaktywnie, faza po fazie; zmiana z zamkniętym zakresem i mierzalnym końcem →
  `/goal` z limitem tur (core-delivery-lifecycle). Każda zmiana → przegląd → osobny PR.
- Drobne usprawnienia odkryte w trakcie dopisz do planu jako osobną pozycję zamiast rozszerzać bieżącą zmianę.
- Po scaleniu: `git worktree remove ../<repo>-<zmiana>`.

## Zakazane bez wyraźnej zgody człowieka
- `git push --force` (dopuszczalne `--force-with-lease` na własnej gałęzi po zgodzie),
- `git reset --hard`, `git clean -fd`, przepisywanie historii opublikowanych gałęzi,
- push do `main`.

## Pull request
Tytuł jak commit. Opis: **Co** (1–3 punkty), **Dlaczego**, **Jak przetestowano**, **Ryzyka/rollback**.
Mały PR (jedna zmiana, kilkaset linii) przegląda się szybciej i dokładniej niż duży; duży dziel na kolejne PR-y.
Odwołaj się do planu kroku i wymagań (`docs/project/`), żeby przeglądający sprawdził zgodność z zamiarem.

## Przegląd PR — także przez AI
- **Pierwszy przegląd może robić agent**, drugi i decydujący — człowiek. Człowiek skupia się na zachowaniu
  („czy rozwiązuje zamiar?”) i ryzyku, a nie na stylu, który sprawdza lint i CI.
- **`REVIEW.md` w katalogu głównym repozytorium** opisuje zasady przeglądu (czyta go usługa Code Review w Claude Code;
  różni się od `CLAUDE.md`, który dotyczy całej pracy agenta). Szablon: `references/review-md.md`.
- **Narzędzia:** usługa Code Review albo `anthropics/claude-code-action@v1` w GitHub Actions — reaguje na wzmiankę
  `@claude` w komentarzu albo działa automatycznie z poleceniem w `prompt`; konfiguracja przez `/install-github-app`
  (tylko github.com), klucz w sekrecie repozytorium (`ANTHROPIC_API_KEY`). Instalację i sekrety wykonuje człowiek.
- **Rozdział obowiązków:** agent nie zatwierdza własnego kodu. Ochrona gałęzi głównej wymaga zatwierdzenia człowieka
  i zielonego CI; poprawki po uwagach agent może wypchnąć na gałąź PR, ale scala człowiek.
- **Strojenie raz w miesiącu:** oceń trafność ustaleń, ogranicz liczbę drobiazgów, wyklucz kod generowany i to, co
  sprawdza CI. Nienastrojony przegląd zasypuje zespół uwagami i przestaje być czytany.
- Przegląd bezpieczeństwa zmian w uwierzytelnianiu, IaC i CI: agent `security-reviewer` przed scaleniem.
- **Przegląd AI jako krok CI** (triaż ryzyka, kontrakt wyjścia, werdykt jako status commita, `[skip ci]` przy
  commitach bota, komentarze tylko na liniach diffu, deduplikacja): `references/przeglad-ai-w-ci.md`. Bramka
  blokująca żyje w workflow (krok po agencie czyta werdykt), nie w odpowiedzi modelu.
- **Gotowy workflow:** `python3 .claude/skills/core-git-workflow/scripts/ai_review.py install [--all-prs]` →
  `.github/workflows/ai-review.yml`: przegląd PR z etykietą `ai-review` (albo każdego) według `REVIEW.md`, agent tylko
  czyta i zwraca JSON, krok workflow ustawia status `ai-review/verdict` i jeden komentarz zbiorczy, etykieta
  `ai-review-override` (człowiek) to świadome obejście. Akcje przypięte do SHA, `permissions: {}`, blokada forka.
  Sekret i ochronę gałęzi ustawia człowiek. `REVIEW.md` z zatwierdzonego szkicu rekonstrukcji z kodu:
  `ai_review.py review-md`.
- Przegląd zgodności z planem kroku i triaż ustaleń z człowiekiem: skill przeglądu zmiany (pack-it: qa-change-review).

## Scalanie i stos PR-ów
- Jedna strategia scalania w repozytorium (squash, rebase albo merge commit); przy squash tytuł commita podajesz
  wprost (tytuł PR z numerem). Wybór strategii i polecenia: `references/scalanie-i-stos-pr.md`.
- **Stos PR-ów** (każdy celuje w gałąź poprzedniego): po squash pierwszego następny przenosisz
  `git rebase --onto origin/main <stara-baza> <gałąź>`, wypychasz `--force-with-lease` (za zgodą), zmieniasz gałąź
  docelową PR na `main` i scalasz po zielonym CI. Konflikty w trakcie pokazujesz człowiekowi.

## Konflikty
Rozwiązuj, rozumiejąc obie strony — nigdy „weź wszystko moje”. Po rozwiązaniu uruchom testy.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 2, lekcje 3 i 5 (commit fazy, praca równoległa) i moduł 5, lekcja 3 (przegląd AI
  w CI) — materiał szkoleniowy (dostęp 2026-10-09); `git help worktree`;
  dokumentacja Claude Code (code.claude.com/docs: sesje równoległe, komunikacja między sesjami, `claude agents`),
  dostęp 2026-10-18. Opisane własnymi słowami.
- Scalanie i stos PR-ów: callstackincubator/agent-skills, skill `github` (wersja sprzed usunięcia 2026-08-07), MIT;
  szczegóły w `references/scalanie-i-stos-pr.md`.
