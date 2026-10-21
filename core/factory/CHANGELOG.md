# Changes in the team factory core

Format: newest version on top. `python3 factory/update.py --check` shows entries newer than the installed version.
Versions up to 2.45.0 are the history of claude-team-factory, from which this core was extracted.

## [5.2.0] — 2026-10-21
### Added
- **modes:** mode-team for experimental agent teams (opt-in) (#10)

## [5.1.0] — 2026-10-21
### Added
- **pack-it:** code-audit workflow for the eng-code-audit skill (#9)

## [5.0.1] — 2026-10-21
### Fixed
- **install:** keep project test paths in skills; plugin analysis (#7)

## [5.0.0] — 2026-10-21
### Breaking
- **factory:** modes directory, Talos as the default mode-talos (#6)

## [4.0.0] — 2026-10-21
### Breaking
- **factory:** Talos story-to-PR mode, guard hooks fail closed (#4)
### Added
- **skills:** grounding modes, output form, evals and latency guidance (#3)
- **factory:** executor consultations, prompt contracts, guard hooks (#2)
### Fixed
- **packs:** accept core 4.x for the 4.0.0 release; Talos guide (#5)

## [3.0.0] — 2026-10-20
### Breaking
- **factory:** the factory is split into a core and packs — `pack-it`, `pack-ux`, `pack-docs`, `pack-editorial-pl` and `pack-ev`; domain skills, roles, personas and traits moved from the core to the packs
- **factory:** source layout `core/` + `packs/<id>/`; in a project, packs live in `factory/packs/<id>/` and agents are built at install time
- **skills:** `core-tech-docs` renamed to `docs-tech-writing` (pack-docs), `fe-ux-design` to `ux-feature-design` (pack-ux)
- **factory:** launcher `tf` and variable `TEAM_FACTORY` replace `ctf`/`CLAUDE_TEAM_FACTORY`; instruction markers `team-factory:begin`

### Added
- **factory:** packs (`pack.yaml`) with facets, shared agents, consultants, routing rows and contributions to other packs (`contributes`, `contributes_when`, `optional_packs`)
- **factory:** consultants — read-only agents a persona can ask about another pack's domain (docs/insights.md)
- **factory:** working language and commit language settings (`tf language`, `tf commit-language`); `pl` installs `pack-editorial-pl`
- **factory:** installer asks for languages and packs; `--packs`, `--add`, `--remove`; migration of claude-team-factory and ev-team-factory installs
- **factory:** `tf` launcher commands `add`, `remove`, `list`, `language`, `commit-language`, `doctor [--fix]`; `factory/migrations.py` rewrites renamed skills in project-owned files after every update
- **factory:** `tools/workspace.py` (assemble, check, matrix, refs, sync-gate) for developing the factory; CI checks core only, each pack and all packs

### Changed
- **skills:** core-* skills describe roles and facets instead of pack personas and skills; pack examples are marked with their pack
- **hooks:** `detect_stack` reads technology registries of installed packs; `skill_hint` scores small installs on the same scale as large ones
- **factory:** freshness intervals, skill visibility, clean-room profiles and permissions come from packs; installer and update messages are in English

## [2.45.0] — 2026-10-19
### Added
- **skills:** add fw-nestjs skill (#52)

## [2.44.0] — 2026-10-18
### Added
- **skills:** add fw-spring-boot skill for Spring Boot 3.5–4.1 (#49)

## [2.43.0] — 2026-10-18
### Added
- **skills:** browser support policy in fe-web-platform (#48)

## [2.42.0] — 2026-10-18
### Added
- **skills:** add multi-tenancy, billing and i18n skills for SaaS (#47)

## [2.41.0] — 2026-10-18
### Added
- **skills:** add EU product law map and compliance role (#46)

## [2.40.0] — 2026-10-18
### Added
- **skills:** add eng-code-audit for multi-dimension code audits (#45)

## [2.39.0] — 2026-10-18
### Added
- **source-research:** add fetch_page.py and text-first source order (#41)

## [2.38.0] — 2026-10-18
### Added
- **security:** sandbox_check script and resolved sandbox questions (#40)

## [2.37.0] — 2026-10-18
### Added
- **security:** shell write detection, guard_paths rules, opt-in sandbox (#38)

## [2.36.0] — 2026-10-18
### Added
- gate shell writes, parallel-work guidance and model–harness notes (#37)

## [2.35.0] — 2026-10-18
### Added
- **update:** auto-install factory patch/minor releases (#36)

## [2.34.0] — 2026-10-18
### Added
- **factory:** log delegations and report cost per task class (#35)

## [2.33.0] — 2026-10-18
### Added
- **tests:** select eval scenarios by id and record the new-scenario run (#34)

## [2.32.0] — 2026-10-18
### Added
- **factory:** warn when hooks are inactive; add second agent retro (#33)

## [2.31.0] — 2026-10-18
### Added
- **skills:** list registry entry points and split oversized groups (#32)

## [2.30.0] — 2026-10-18
### Added
- **skills:** reuse code_graph in neighbor skills and add --focus (#31)

## [2.29.0] — 2026-10-18
### Added
- **skills:** add code_graph.py import graph for codebase mapping (#30)

## [2.28.0] — 2026-10-17
### Added
- **factory:** suggest skill keywords and search verified facts (#29)

## [2.27.0] — 2026-10-17
### Added
- **factory:** add one-command checks and task finishing tools (#28)

## [2.26.0] — 2026-10-17
### Added
- **factory:** add cost statistics per period in PLN (#27)

## [2.25.0] — 2026-10-17
### Added
- **skills:** flag log gaps in agent retros and act on the first retro (#26)

## [2.24.0] — 2026-10-17
### Added
- **skills:** send retro signals about the factory back upstream (#25)

## [2.23.0] — 2026-10-17
### Added
- **skills:** give core-agent-retro memory across retrospectives (#24)

## [2.22.0] — 2026-10-17
### Added
- **skills:** add core-agent-retro for evidence-based agent retros (#23)

## [2.21.0] — 2026-10-17
### Added
- **skills:** add six business archetypes to ddd-archetypes (#22)

## [2.20.0] — 2026-10-17
### Added
- **factory:** add skill review dates and update notice on session start (#21)

## [2.19.0] — 2026-10-17
### Added
- **skills:** add Henryk, cloud and infrastructure architect with ops-* skills (#20)

## [2.18.0] — 2026-10-17
### Added
- **skills:** add Barbara, CISO with leadership and EU regulation skills (#19)

## [2.17.0] — 2026-10-17
### Added
- **skills:** add Wiktor, security engineer and architect with sec-* skills (#18)

## [2.16.0] — 2026-10-17
### Added
- **skills:** add Lena for AI product and governance, arch-ai-solutions (#17)

## [2.15.0] — 2026-10-17
### Added
- **skills:** add Iga, AI scientist with research, NLP and CV skills (#16)

## [2.14.0] — 2026-10-17
### Added
- **skills:** add Adam, AI/ML engineer with seven ai-* skills (#15)

## [2.13.0] — 2026-10-17
### Added
- **skills:** add UX team for Natalia and specialist facets (#14)

## [2.12.0] — 2026-10-17
### Added
- **skills:** add legacy dossier and per-project skill visibility (#12)

## [2.11.0] — 2026-10-17
### Added
- **agents:** let orchestrators work in their own context by default (#11)

## [2.10.0] — 2026-10-17
### Added
- **install:** add ctf command to install or update from the repo (#10)

## [2.9.0] — 2026-10-17
### Added
- **build:** add standalone_skills for skills used without a persona (#9)

## [2.8.0] — 2026-10-17
### Nowe
- **update:** fetch the latest release tag by default (#7)

## [2.7.1] — 2026-10-17
### Poprawione
- **hooks:** tdd_guard rozpoznaje testy uruchamiane jako skrypty

## [2.7.0] — 2026-10-17
### Nowe
- **Wydania automatyczne z Conventional Commits** (jak w ci_for_sdlc, opis w `docs/RELEASING.md`):
  po merge do `main` workflow `release` liczy wersję z commitów od ostatniego tagu (`feat` → MINOR, `fix`/`perf` →
  PATCH, `!` lub `BREAKING CHANGE:` → MAJOR; liczy `semver.py`), zapisuje `factory/VERSION` i wpis CHANGELOG,
  commituje `chore(release): X.Y.Z`, tworzy tag `vX.Y.Z` i GitHub Release z wpisem jako notatkami.
- Skrypty repozytorium fabryki (nie trafiają do projektów): `scripts/release.py` (`--dry-run`, `--ci`,
  `major|minor|patch|X.Y.Z`), `scripts/release_notes.py`, `scripts/check_commit_message.py`.
- Lint tytułu PR (workflow `pr-title`) i opcjonalny hook `commit-msg` (`git config core.hooksPath .githooks`).

## [2.6.0] — 2026-10-10
### Nowe
- **Wiedza z kursu 10xDevs (ed. 3, 2026)** przeniesiona własnymi słowami tam, gdzie uzupełnia fabrykę; skille kursu
  przeszły audyt (`skill_audit.py`: 0 wysokiej wagi), ale żaden nie został skopiowany. 9 nowych skilli (nazwy wg funkcji):
  - `proc-requirements-shaping` — od pomysłu do wymagań (PRD): MVP w budżecie czasu z briefu, pusty CRUD, wyzwanie dla
    wymagań, otwarte pytania zamiast domysłów; skrypt `requirements_lint.py` (wyciek technologii do wymagań, gotowość);
  - `qa-change-review` — przegląd planu przed kodem i kodu względem planu: dryf, waga × wpływ, triaż, werdykt;
  - `core-agent-instructions` — CLAUDE.md / AGENTS.md: test włączenia, karta pięciu kontroli, aktualizacja z historii
    gita, kalibracja A/B, skalowanie na moduły; skrypt `instructions_lint.py`;
  - `eng-repo-readiness` — repo gotowe dla agentów: szkielet z oficjalnego generatora z polityką konfliktów albo audyt
    (lockfile, audyt zależności, runner testów, CI, cztery bramki stacku); skrypt `readiness_check.py`;
  - `eng-local-quality-gates` — hook po edycji, pre-commit, pre-push, testy powiązane; szablon opcjonalnego hooka
    `post_edit_checks.py` (nie jest włączany automatycznie);
  - `eng-refactor-planning` — ranking opcji refaktoryzacji, intencja z historii, Strangler Fig, Branch by Abstraction,
    Mikado, weryfikacja liczb ast-grepem i `rg`;
  - `ddd-legacy-modernization` — słownik i rozjazdy model↔kod, niezmiennik w agregat, ACL ze sprawdzalnym kryterium;
  - `eng-llm-features` — funkcje i agenci LLM we własnym kodzie: kategoria SDK, structured output, pętla narzędzi
    z limitami, koszt, prywatność, ewaluacje (promptfoo);
  - `core-async-delegation` — praca agenta bez nadzoru: tryb kontroli, kontrakt przed startem, bramki faz, STOP, przegląd.
- `eng-codebase-mapping`: skrypt `git_territory.py` (terytorium z historii, pary i huby współzmian, hotspoty,
  kontrybutorzy bez botów), szeroki skan, analiza jednego przepływu, `research.md` pod zmianę.
- Uzupełnione skille (ok. 35): m.in. plan cięć z fundamentami i „Odblokowuje” (core-delivery-lifecycle), plan kroku
  z sekcją „Postęp” (szablony core-project-record), commit fazy i praca w worktree, przegląd AI w CI z werdyktem jako
  statusem commita, polityka uprawnień i dostęp agenta do produkcji, sygnały zużytego kontekstu, ocena nowego modelu
  (pass^k, koszt rozwiązanego zadania), koszt serwerów MCP, strategia testów projektu z mapą ryzyk, ocena przeżytych
  mutantów i celowe psucie, przeramowanie problemu i dowody z wielu źródeł w debugowaniu, E2E generowane przez agenta,
  cztery bramki „przyjazności dla agenta” w doborze stacku, platforma wdrożeniowa, test odporności decyzji (adwokat
  diabła, pre-mortem), tabela audytu zależności dla ekosystemów, pierwsze wdrożenie (sprint zero).
- Routing problemów (`core-problem-routing`): 10 nowych sygnałów. Nowe skille przypisane do ról.
- `CLAUDE.md`: odnośnik do `docs/project/lessons.md` i test włączenia reguły; zmiana kontraktu planu = stop i aktualizacja.
### Poprawione
- **Windows: „Stop hook error … No stderr output”.** Hook `project_record.py --hook-stop` mógł przekroczyć limit
  Claude Code (10 s), gdy `git status` wisiał (demon fsmonitor trzymał potok, duże repo, antywirus) — Claude Code
  zabijał proces bez komunikatu. Teraz: git bez fsmonitora i opcjonalnych blokad, wyjście w UTF-8, krótszy limit,
  a tryby hooków kończą się same z kodem 0 przed limitem (`CLAUDE_HOOK_DEADLINE`, domyślnie 7 s; też `detect_stack --hook`).
- **Windows: kodowanie.** Wszystkie hooki wymuszają UTF-8 na stdin/stdout/stderr — przy stronie kodowej cp1250 polskie
  podpowiedzi `skill_hint` docierały do modelu jako krzaczki, a część komunikatów znikała.
- `detect_stack.py --latest` na Windows: `npm` szukany przez `shutil.which` (`npm.cmd`).
- **`guard_bash`: opcje globalne gita omijały blokady** — `git -C dir push -f`, `git -c a=b reset --hard`,
  `git --git-dir=… clean -fd` przechodziły bez decyzji. Polecenie jest normalizowane przed dopasowaniem (8 testów).
- `tdd_guard`: „czerwony” bez wykonanej asercji (brak plików testów, błąd składni testu, zła konfiguracja runnera)
  daje ostrzeżenie dla agenta; decyzja bramki bez zmian.
- `install.py`: znacznik początku bloku bez znacznika końca kończy instalację czytelnym komunikatem zamiast wyjątku.
- Lista skilli dla modelu ≤ 14 tys. znaków mimo 9 nowych skilli (skrócone opisy 23 skilli).
### Testy
- Nowe: `test_hook_portability` (cp1250, zawieszony git), `test_requirements_lint`, `test_instructions_lint`,
  `test_readiness_check`, `test_post_edit_checks`, `test_git_territory`; rozszerzone `test_hooks` (97) i `test_tdd` (25).
- Bramka: 108/108 skilli bez ewaluacji na modelu — płatna ewaluacja nowych i zmienionych skilli czeka na zgodę.

## [2.5.1] — 2026-10-05
### Zmienione
- Dokumentacja dopasowana do wydań 2.2–2.5:
  - README: skrót ostatnich wydań na początku; tabela kroków bramki z krokiem 7 „audyt” (płatna ewaluacja to krok 8)
    i regułą wyboru w opisie; struktura z `skill_audit.py`, `control_band.py` i `team-factory.yml`; 15 plików testów
    z aktualnymi liczbami;
  - PRZEWODNIK: polecenie pasm kontrolnych w ściądze.
- `CLAUDE.md` (zasady instalowane w projektach): obcy skill dopiero po `skill_audit.py`, przeczytaniu i zgodzie
  człowieka; `tdd_guard` ostrzega przy osłabieniu testu; krok realizacji zaczyna się od planu zapisanego przed kodem.

## [2.5.0] — 2026-10-04
### Nowe
- **`factory/skill_audit.py`** — audyt skilli bez modelu i sieci (Anthropic: „Review all files bundled in the Skill”):
  - wysoka waga: wstrzyknięte polecenia („zignoruj poprzednie instrukcje”, ukrywanie działań przed użytkownikiem),
    pobieranie i uruchamianie skryptu z sieci, dostęp do plików z poświadczeniami, sieć bez deklaracji „Sieć: …”,
    ukryte znaki Unicode;
  - średnia: `eval`/`exec`/`shell=True`, szerokie `allowed-tools`, `hooks` w nagłówku, polecenia wykonywane przy
    wczytaniu skilla, pliki binarne, długie ciągi base64, odwołania do nieistniejących plików, błędy nagłówka;
  - niska (zalecenia Anthropic): opis bez reguły „kiedy”, brak przykładów, SKILL.md > 500 linii, referencje bez spisu
    treści, odwołania zagnieżdżone lub do plików innego skilla bez pełnej ścieżki, ścieżki z `\`, ogólnikowa nazwa;
  - pominięcie linii komentarzem `audit-ok` zawsze widoczne w raporcie. 17 testów (`tests/test_skill_audit.py`).
- **Bramka jakości, krok 7 „audyt”** — ustalenia wysokiej i średniej wagi blokują; płatna ewaluacja to teraz krok 8.
- **`update.py`**: audyt skilli nowej wersji narzędziem z wersji zainstalowanej przed zastosowaniem; flaga
  `--accept-audit`.
- **Przykłady w 26 skillach**, które ich nie miały: sekcja `## Przykład` w SKILL.md i `references/przyklady.md`
  (2–3 przykłady wejście → wynik). YAML, JSON, powłoka, Python i TypeScript w przykładach sprawdzone parserami
  i kompilatorami; liczby (Monte Carlo, WSJF, macierze ocen, symulacja ryzyka) policzone skryptami.
- `core-agent-security` sekcja 4a „Skille i wtyczki z obcych źródeł”; `core-skill-authoring` i szablon nowego skilla
  z zaleceniami Anthropic (reguła wyboru, jedno zadanie, przykłady, skrypty, jeden poziom referencji, deklaracja sieci).
- Workflow `team-factory`: testy i przebieg audytu skilli. Uprawnienie `Bash(python3 factory/skill_audit.py *)`.
### Zmienione
- **Opisy wszystkich 99 skilli jako reguły wyboru** („Użyj, gdy/przy … — …”). Claude Code pokazuje modelowi tylko
  `description` (pole `metadata` pomija), więc „kiedy użyć” musi być w opisie. Lista skilli krótsza: ≈13,2 tys. znaków
  (było ≈14 tys.). `build.py check` ostrzega o opisie bez reguły wyboru.
- `update.py --yes` zatrzymuje się, gdy audyt nowej wersji znajdzie ustalenia wysokiej wagi.
### Poprawione
- 29 odwołań do plików referencji innych skilli bez nazwy skilla (model szukałby ich we własnym katalogu) → pełne
  ścieżki `.claude/skills/<skill>/…`; spisy treści w 3 długich referencjach z kodem.
- Słowa użytkowników dla `arch-architect-practice`; słabych podpowiedzi w skanie 321 scenariuszy: 7 (bez zmian).
- Nowe scenariusze ewaluacji: `core-agent-security` (obcy skill z GitHuba), `core-skill-authoring` (słaby skill).

## [2.4.0] — 2026-10-04
### Nowe
- **Pętla AI-native w `core-delivery-lifecycle`** (`references/ai-native-sdlc.md`) na podstawie „The AI-Native SDLC
  Playbook” (Anthropic, 21.08.2026), kursu Anthropic Academy i „AI-Driven Development Life Cycle” (AWS, 31.07.2025):
  łańcuch artefaktów odwzorowany na `docs/project/`, sześć etapów z rolą agenta i człowieka oraz miarami
  wyprzedzającymi i opóźnionymi, ewaluacje konfiguracji agenta, agent do bramki produkcyjnej i nic dalej, pasma
  kontrolne, źródło prawdy, ustawienia zarządzane, kolejność wdrażania 12 „zagrań” ze stanem w fabryce, słownik AI-DLC,
  antywzorce. Skrót zasad w SKILL.md.
- **`core-delivery-lifecycle/scripts/control_band.py`** — pasma kontrolne metryk (reguły Western Electric 1–4, poziomy
  log / diagnose / act, `--side upper|lower`), tylko biblioteka standardowa; 8 testów (`tests/test_control_band.py`).
- **`tdd_guard`, reguła C — osłabienie testu:** edycja testu, która zmniejsza liczbę asercji lub testów albo dopisuje
  pominięcie (skip, xfail, @Disabled, xit…). Nowa zmienna `CLAUDE_TDD_WEAKEN=warn|ask|deny|off`; domyślnie `warn`
  (ostrzeżenie dla człowieka i `additionalContext` dla modelu, bez blokady). 5 nowych testów.
- **Przegląd PR przez AI** w `core-git-workflow`: `REVIEW.md` (szablon `references/review-md.md`), usługa Code Review
  i `anthropics/claude-code-action@v1`, rozdział obowiązków, ochrona gałęzi, strojenie; małe PR-y.
- `core-project-record`: źródło prawdy przy Jirze/ServiceNow (repozytorium, narzędzie, powiązanie); błąd agenta
  powtórzony drugi raz → propozycja reguły w `CLAUDE.md`; w szablonie raportu kroku sekcja „Plan kroku (zatwierdzony
  przed kodem)”.
- `ops-sre-incidents`: incydent zostawia test regresyjny i stały scenariusz ewaluacji agenta; metryki pod pasma kontrolne.
- `proc-project-planning`: dobór modelu cyklu życia (kaskadowy, V, spiralny, Agile, prototypowanie, DevOps, pętla
  AI-native) z zasadą łączenia modeli i uwagą o normach (IEC 62304).
- PRZEWODNIK: tabela ról SDLC i person fabryki.
- Workflow `team-factory`: testy TDD, pasm kontrolnych i `skill_gate.py --status --strict`.
### Poprawione
- Słowa użytkowników dla `proc-team-topologies` (podpowiedź hooka 0/2 → 2/2) i `proc-issue-triage`; słabych podpowiedzi
  w skanie 99 plików scenariuszy jest 7 (było 9).
- Nowe scenariusze ewaluacji (przed treścią): `core-delivery-lifecycle` ×2, `proc-project-planning`,
  `core-project-record`, `core-git-workflow`, `ops-sre-incidents`.

## [2.3.0] — 2026-10-03
### Nowe
- **Skille domykające fazy SDLC** (scenariusze ewaluacji napisane przed treścią; bramka offline z regresją
  podpowiedzi wszystkich skilli przeszła):
  - `proc-project-planning` — plan projektu: cel i miara sukcesu, zakres z „poza zakresem”, koszt i termin jako
    przedziały P50/P80 (stożek niepewności McConnella, klasa referencyjna Flyvbjerga, szacunek trzypunktowy
    z przykładem policzonym skryptem), rezerwy, rejestr ryzyk (ISO 31000, reakcje PMI), RACI, finansowanie etapami,
    prawo Brooksa. Źródła: PMBOK 8 (listopad 2025), GAO-20-195G, GOV.UK Service Manual.
  - `eng-debugging` — od objawu do przyczyny: odtworzenie czerwonym testem, hipotezy z eksperymentem, zawężanie
    o połowę, `git bisect run` z kodem 125 (sprawdzone na repozytorium testowym; pierwsza próba pokazała fałszywy
    wynik przez nieaktualny `__pycache__` — opisane jako pułapka), debugger, tabela typowych przyczyn.
  - `ops-dependency-upgrades` — planowe aktualizacje na prośbę człowieka: inwentarz i koniec wsparcia, jeden major
    naraz, codemody (ng update, @next/codemod, React, OpenRewrite, ruff UP), osobne commity, wycofanie; konfiguracje
    Renovate (sprawdzona `renovate-config-validator --strict` z Renovate 44.132.4) i Dependabot (klucze zgodne
    z oficjalnym opisem opcji, w tym `cooldown` i domyślne 3 dni karencji).
  - `arch-privacy-compliance` — RODO w projekcie: inwentarz danych, podstawy, prywatność w fazie projektowania,
    retencja, prawa osób (z kopiami zapasowymi i procesorami), transfery (DPF, T-553/23), DPIA (wykaz UODO), naruszenia
    (72 godziny), cookies, dane w promptach AI, stan prac nad Digital Omnibus (projekt, nie prawo). Przykład
    pseudonimizacji HMAC i zadania retencji sprawdzony pytest 9.1.1, `mypy --strict` i ruff. Nie jest poradą prawną.
- **Faza 9 „Utrzymanie”** w `core-delivery-lifecycle`: cykliczny przegląd utrzymania, poprawki z testem regresyjnym,
  łatki, aktualizacje, wygaszanie funkcji (SemVer), koniec życia systemu; nowa bramka **B6**.
- **Dziennik projektu:** faza `operations` w katalogu `08-operations/` (`project_record.py`, test); szablony
  `project-plan.md`, `privacy.md`, `operations-review.md`.
- Podpięcie: Maja i Tomasz — `proc-project-planning`; role frontend i backend — `eng-debugging`; devops —
  `ops-dependency-upgrades`; solution-architect i data-engineer — `arch-privacy-compliance`.
### Poprawione
- **Regresja podpowiedzi z 2.2.0:** pytanie o podatność w Next.js/RSC przestało podpowiadać `fe-architecture`
  (wygrywały nowe `fw-nextjs` i `fw-react`). `fe-architecture` dostało `metadata.slowa`; bramka znów 2/2.
- Słowa użytkowników dla `qa-exploratory-manual` („zgłoszenie defektu”), `arch-tech-selection` („który framework
  wybrać”) i `ddd-archetypes` (program lojalnościowy, saldo) — po skanie podpowiedzi wszystkich 99 plików
  scenariuszy. Słabych podpowiedzi jest 9 (w 2.2.0 było 11); żadna nie jest nowa.
- Ogólne słowa w polach podpowiedzi nowych skilli zawężone (np. „rezerwą” myliło się z rezerwacją, „przejść na”
  ściągało aktualizacje do pytania o CDC).
### Zmienione
- Krótsze opisy 12 skilli, żeby lista widoczna dla modelu zmieściła się w limicie 14 000 znaków (13 980). Treść
  i granice bez zmian (pełny opis w `metadata.katalog`).

## [2.2.0] — 2026-10-03
### Nowe
- **Skille dla stacku React + Next.js + Python:** `fw-react` (18–19.3), `fw-nextjs` (14–16.3, App Router),
  `lang-python` (3.11–3.15) i `tool-pytest` (8–9.1). Treść z oficjalnej dokumentacji (react.dev, nextjs.org/docs,
  docs.python.org, packaging.python.org, docs.pytest.org) i rejestrów npm/PyPI, dostęp 2026-10-03. Przykłady
  w `references/` sprawdzone: `tsc --noEmit` (React 19.3, Next.js 16.3.8), uruchomienie na CPython 3.14.8, 3.15.0rc3
  i 3.11 z `mypy --strict`, pytest 9.1.1 z pytest-asyncio i Hypothesis. Scenariusze ewaluacji napisane przed treścią
  (po 3 trigger i 1 no-trigger); bramka offline z regresją podpowiedzi wszystkich skilli przeszła.
- **Persona Nina** — fullstack React/Next.js z usługami w Pythonie (`frontend`, `backend`).
- `skill_requires`: `fw-react` → `fe-web-platform`, `fw-nextjs` → `fw-react`, `tool-pytest` → `lang-python`.
- **`detect_stack.py`:** wersja Pythona z `requires-python` (dolna granica) lub `.python-version`; pakiety PyPI
  z `uv.lock`, `poetry.lock`, `pylock.toml`, `requirements*.txt` i `pyproject.toml`; nowa technologia pytest w rejestrze.
  Python nie jest już „bez wersji”, więc projekt na Pythonie starszym niż 3.11 dostaje `PROJECT_OLDER`.
  Ograniczenia: Next.js 15 → React ≥19, Next.js 16 → React ≥19.2, pytest 9 → Python ≥3.10. 8 nowych testów.
### Zmienione
- Zofia: `stack: [lang-python, tool-pytest]`; Kasia: + `tool-pytest`.
- Lista skilli widoczna dla modelu: ≈13,5 tys. znaków (limit 14 tys.).
### Otwarte
- Ewaluacja czterech skilli na modelu (Haiku + Sonnet, 16 scenariuszy × 2 modele) czeka na zgodę człowieka.

## [2.1.0] — 2026-10-03
### Nowe
- **Mocniejsza podpowiedź hooka `skill_hint` przy wyraźnym liderze.** Przy wyniku ≥16 i przewadze 30% nad drugim
  skillem hook pisze „Wczytaj go narzędziem Skill, zanim odpowiesz” zamiast „prawdopodobnie pasujące”. Ewaluacje
  pokazały, że przy łagodnej podpowiedzi model pewny swojej wiedzy pomijał skill. Kalibracja: 176 trafnych i 2 błędne
  mocne podpowiedzi na 283 scenariuszach.
### Poprawione
- **Wdrożone poprawki ze wszystkich dotychczasowych ewaluacji** (stan w `docs/evals/2026-10-02-wyniki-i-poprawki.md`).
  14 scenariuszy niezaliczonych na Sonnecie przejrzano na podstawie odpowiedzi; po poprawkach 14/14 przechodzi na
  Haiku i Sonnecie (koszt $3,93):
  - 7 z poprawną treścią ujętą innymi słowami: równoważne sformułowania i rubryki w sprawdzeniach;
  - 5 z poprawnym sąsiednim skillem: pole `accept`;
  - fałszywe wczytanie przy `ng update` i 4 przypadki bez skilla: słowa użytkowników w `metadata.slowa`
    (fw-angular, core-agent-security, arch-system-design, txt-polish-style, arch-tech-selection,
    ddd-algorithm-recognition) i mocniejsza podpowiedź.
  - Z `core-stack-sync` usunięto ogólne „aktualizacja wersji”, które ściągało pytania o podnoszenie frameworka.
- R7: równoważne sformułowania w 6 sprawdzeniach, które oceniający już wcześniej uznawał.
- Treść skilli bez zmian merytorycznych (tylko `metadata.slowa`). Wszystkie zmienione skille przeszły bramkę,
  w tym regresję podpowiedzi wszystkich skilli.
- Otwarte: R8 (`--baseline`), R9 (Opus); pełny przebieg Sonneta potwierdziłby brak regresji na modelu.

## [2.0.1] — 2026-10-03
### Poprawione
- **Bramka skilli:** każda runda ewaluacji ma własny raport (`…-bramka-<skill>-2.md`). Wcześniej runner dopisywał
  wyniki do raportu z tego samego dnia, więc bramka liczyła razem wyniki kilku rund. Wyciągnięta funkcja
  `report_path` z testem.
- **Ewaluacja `eng-testing`** (zmieniony w 2.0.0), Haiku 4/4 i Sonnet 4/4, koszt $0,91. Raport:
  `docs/evals/2026-10-03-bramka-eng-testing-2.md`. Scenariusz TDD przeszedł na obu modelach: najpierw czerwony
  test, potem minimalny kod, przypadki brzegowe 200,00 i 200,01.

  Pierwsza runda dała Haiku 4/4 i Sonnet 2/4 (raport `…-bramka-eng-testing.md`). Obie porażki nie dotyczyły TDD,
  dlatego poprawiono scenariusze:
  - `jakosc-testow` — Sonnet konsekwentnie, także 2026-10-02, wybierał qa-spec-first-testing. Pytanie o „skąd brać
    oczekiwane wartości” należy do obu skilli, więc dodano `accept`;
  - `mock-vs-fake` — odpowiedź mówiła „asercje na wyniku, nie na interakcji”, co znaczy to samo co „zachowanie przez
    publiczne API”, ale wyrażenie tego nie łapało. Dodano równoważne sformułowania i rubrykę dla oceniającego.
- Dokumentacja:
  - README, „Bezpieczeństwo — warstwy”: opis `tdd_guard`;
  - README, „Struktura”: `tdd_guard`, 13 plików testów;
  - README, tabela skilli: TDD obowiązkowe w `eng-testing`.

## [2.0.0] — 2026-10-03
### Niezgodne
- **TDD jest wymuszane domyślnie.** Nowy hook `tdd_guard` blokuje edycję kodu produkcyjnego (`.ts`, `.js`, `.py`,
  `.java`, `.kt`, `.go` i inne), dopóki w danym kontekście (sesja albo subagent) nie zostanie zmieniony plik testu,
  a po tej zmianie testy nie zostaną uruchomione z wynikiem czerwonym. Wcześniej taka edycja przechodziła bez warunków,
  dlatego to wydanie MAJOR.
  - Przywrócenie poprzedniego zachowania: zmienna `CLAUDE_TDD=off` (całkiem) albo `CLAUDE_TDD=ask` (każdą blokadę
    rozstrzyga człowiek).
  - Pliki wyłączone spod bramki: testy, konfiguracja (`*.config.*`), style, szablony, dokumentacja, `.d.ts`,
    `.claude/`, `factory/`, katalogi wygenerowane. Dodatkowe wzorce ustawisz w `CLAUDE_TDD_EXEMPT`, np.
    `src/migrations/*`.
### Nowe
- Reguły `tdd_guard`:
  - test od razu zielony nie otwiera kodu, chyba że jest oznaczony jako `[charakteryzujący]` (refaktoryzacja kodu bez
    testów);
  - po `CLAUDE_TDD_MAX_EDITS` (domyślnie 12) zmianach kodu bez nowego testu wymagany jest następny test;
  - wynik testów rozpoznaje dla npm, pnpm, yarn, vitest, jest, pytest, Maven, Gradle, go test, cargo, dotnet i nx
    (kod wyjścia, PostToolUseFailure, komunikaty porażki).
- TDD w promptach:
  - cecha `test-driven` przepisana na ścisłe TDD i dodana personom marek, zofia i piotr;
  - routing: brief z przykładami wejście → wynik, a kluczową logikę najpierw testuje qa-analyst w clean-room;
  - kontrakt raportu: dowód czerwonego i zielonego testu;
  - CLAUDE.md: reguła TDD.
- Skill eng-testing: sekcja „TDD w fabryce — obowiązkowe” (kolejność, test od razu zielony, następny test, zakaz
  osłabiania testów, testy kluczowej logiki od innego autora, raport). Nowy scenariusz ewaluacji `tdd-nowa-regula`.
- `update.py` ostrzega przy aktualizacji do nowej wersji MAJOR i odsyła do sekcji „Niezgodne”.
- `factory/PUBLIC_API.md`: reguły blokujące hooków należą do publicznego API. Nowa blokada włączona domyślnie
  oznacza MAJOR, a wyłączona domyślnie MINOR.
- Testy `tests/test_tdd.py` (12).

## [1.35.1] — 2026-10-03
### Poprawione
- Dokumentacja nadąża za wersjami 1.31–1.35:
  - README, tabela „Zasady i proces”: wiersze core-semver, core-grounding, core-cost-control i core-skill-authoring;
  - README, „Dodawanie”: kolejność pracy nad skillem (scenariusze → treść → bramka → wersja MINOR), prefiksy
    w `config.yaml → facets`, pełna lista kontroli `build.py check`;
  - README, „Struktura”: aktualne hooki, skrypty, testy, dokumenty i workflow CI;
  - PRZEWODNIK: sekcja „Wersje i wydania (SemVer)” dla człowieka (publiczne API, 0.1.0 i 1.0.0, numer ze skryptu,
    zgoda na tag i publikację).

## [1.35.0] — 2026-10-03
### Nowe
- **Skill `core-semver`** (zawsze dołączany do person) obejmuje Semantic Versioning 2.0.0:
  - publiczne API;
  - tabela podbić z przypadkami granicznymi (`references/publiczne-api.md`);
  - faza 0.y.z i wydanie 1.0.0;
  - wersje przedpremierowe i metadane;
  - wydanie bez zmiany opublikowanej wersji i wycofywanie.
- **`scripts/semver.py`** — numer wersji liczy skrypt, a nie model:
  - `valid`, `compare`, `sort`, `bump` (major, minor, patch, pre, release);
  - `next` liczy podbicie z Conventional Commits od ostatniego tagu `vX.Y.Z`, w fazie 0.y.z łagodniej;
  - `check-changelog` sprawdza format, kolejność i zgodność z plikiem wersji.

  Używa oficjalnego wyrażenia regularnego z semver.org.
- **Fabryka wersjonowana wg SemVer.** `factory/PUBLIC_API.md` opisuje:
  - co jest publicznym API: skille, persony, polecenia i flagi, zmienne, klucze konfiguracji, układ instalacji,
    formaty danych;
  - które zmiany wymagają major, minor i patch;
  - wycofywanie przez alias;
  - procedurę wydania.
- `build.py check` (a więc także CI) sprawdza:
  - poprawność `factory/VERSION`;
  - kolejność i niepowtarzalność wpisów CHANGELOG;
  - zgodność VERSION z najnowszym wpisem;
  - od 1.35.0 (`semver_strict_from`) zgodność rodzaju podbicia z sekcjami wpisu (Niezgodne/Usunięte → major,
    Nowe/Wycofywane → co najmniej minor).
- Testy `tests/test_semver.py` (29): przykład kolejności z reguły 11, wersje poprawne i niepoprawne, podbicia,
  historia git, CHANGELOG, update.py, wersja samej fabryki.
### Zmienione
- `update.py` porównuje wersje według precedencji SemVer, także z wersjami przedpremierowymi
  (`1.36.0-rc.1 < 1.36.0`).
- CLAUDE.md: wersje tego, co agenci wydają, nadawane są według SemVer i liczone skryptem; tag, push i publikacja
  wymagają zgody człowieka.
- Odesłania do core-semver w skillach be-api-design, ops-release-engineering, core-conventional-commits
  i core-delivery-lifecycle (faza 8). core-conventional-commits ma słowa użytkownika (`metadata.slowa`).
- Bramka nie pokazuje własnego stanu („zmieniony po bramce”) jako uwagi w kroku struktury.
- Uprawnienie `Bash(python3 .claude/skills/core-semver/scripts/semver.py *)`: skrypt tylko liczy i czyta historię
  git. Ewaluacja pokazała, że bez tego uprawnienia Haiku liczył numer ręcznie, bo czekał na zatwierdzenie.
### Ewaluacja na modelu
- `core-semver` przez bramkę (`--model haiku,sonnet`): Haiku 4/4, Sonnet 4/4, koszt $0,90. Wyniki:
  - 2.4.1 z usuniętą funkcją → 3.0.0;
  - kolejność wersji przedpremierowych zgodna z regułą 11, a metadane budowania pominięte;
  - start od 0.1.0 i kryteria wydania 1.0.0;
  - przy pytaniu o commit message oba modele wybrały core-conventional-commits.
  Raport: `docs/evals/2026-10-03-bramka-core-semver.md`.
### Uwaga o historii
- Wydania 1.28.1, 1.29.2 i 1.29.3 (PATCH) miały sekcję „Nowe” z wynikami ewaluacji, a nie nowym API. Wydanych
  wersji nie zmieniamy (reguła 3); kontrola rodzaju podbicia obowiązuje od 1.35.0.

## [1.34.0] — 2026-10-03
### Zmienione (zgodność z oficjalną dokumentacją TypeSafe)
- Klient Jev zgodny z docs.typesafe.ai:
  - zmienne `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL` (`JEV_API_KEY` działa dalej jako alias);
  - adres `https://api.typesafe.ai/v1/systemone`;
  - ponawianie po 429/529 z wykładniczym odczekaniem, limit czasu 10 s;
  - pewność noul |2p − 1| i pas niepewności 0,30–0,70 (wcześniej 0,85);
  - instrukcje pytań po angielsku (najlepsza dokładność), stan po polsku.

  Wersja 1.33 opierała się na źródłach pośrednich i używała innych nazw zmiennych.
### Nowe
- **Podpowiedź skilli według cookbooka „Skill suggestion”** (`CLAUDE_SKILL_HINT_JEV=1`):
  - etap 1 to wybór spośród wszystkich skilli oraz 3 pytania bramki;
  - etap 2 to 3 kandydatów z pełnym opisem i początkiem SKILL.md oraz pytania „czy pasuje”;
  - progi 0,30;
  - przy braku Jev zostaje dopasowanie słów; log zapisuje, która metoda zadecydowała.
- **`grounding_check.py --jev`** (cookbook „Double-checking citations”): czy linie z `plik:linia` potwierdzają
  zdanie, przeczą mu, czy nic o nim nie mówią; pewność <0,8 oznacza przejrzenie przez człowieka.
- **Hook `jev_guard`**:
  - `CLAUDE_JEV_GUARD=1` (cookbook „Guardrails”) — ostrzeżenia przy treści z sieci, która próbuje zmienić
    instrukcje, każe coś uruchomić albo prosi o sekrety;
  - `CLAUDE_JEV_REPORT_CHECK=1` (kaskada „verify → escalate”) — jedna prośba o poprawę raportu wykonawcy, który
    ogłasza „działa” bez dowodu albo „gotowe” z otwartymi punktami.
- **`jev_client.py --tier "<zadanie>"`** — rubryka core-cost-control jako 5 pytań noul; decyzję składa kod.
- `factory/jev_calibration.py --routing` mierzy na wszystkich scenariuszach, ile podpowiedzi jest trafnych, błędnych,
  zbędnych i przeoczonych: same słowa kontra Jev.
- `docs/jev.md`: zastosowania, konfiguracja, procedura pomiaru, ograniczenia (jev-1.13), prywatność, oficjalny skill
  `typesafe-ai/skills`.
- Testy `tests/test_jev.py` (11, atrapa API: adres, nagłówek, sekrety, 429, kaskady, strażniki, tier, brak klucza).
- Skille core-grounding, core-agent-security i core-cost-control opisują opcjonalne narzędzia Jev; bramka przeszła.
- `docs/jev.md` trafia do projektu jako `.claude/JEV.md`.
- Ewaluacja `core-skill-authoring` na modelu (bramka z `--model haiku,sonnet`): Haiku 3/3, Sonnet 3/3, koszt $0,71;
  skill uruchomiony narzędziem Skill, przy pytaniu sąsiada oba modele wybrały core-skill-composition.
  Raport: `docs/evals/2026-10-03-bramka-core-skill-authoring.md`. Zamyka punkt „Do zrobienia” z 1.33.0.
- Testy fabryki przechodzą także w zainstalowanym projekcie (`.claude/tests/`). Poprawione ścieżki:
  - szkielet scenariuszy z `new-skill`;
  - rejestr bramki;
  - ustawienia w test_cost.

## [1.33.0] — 2026-10-03
### Nowe
- **Bramka jakości skilli** `factory/skill_gate.py`. Bezpłatne kroki:
  - struktura i scenariusze;
  - podpowiedź hooka dla pytań skilla i jego sąsiada;
  - regresja podpowiedzi wszystkich skilli;
  - polszczyzna i odwołania.

  Opcjonalnie płatna ewaluacja na modelach z limitem kosztu. Przerwanie limitem wydatków nie jest liczone jako
  porażka skilla.
- **Rejestr bramki.** `tests/skill_gate.json` przechowuje odcisk treści skilla, czyli SKILL.md, references, scripts
  i scenariusze. `build.py check` ostrzega o skillach zmienionych po bramce; `--status --strict` służy do CI.
- **Hook `skill_change_guard`** (PostToolUse i Stop) — przypomnienie o bramce po edycji skilla i lista skilli bez
  bramki na koniec sesji.
- **Skill `core-skill-authoring`** (persona Maja) — kolejność od ewaluacji do wydania i diagnoza nieuruchamiającego
  się skilla.
- `build.py new-skill` tworzy szkielet scenariuszy z TODO, którego bramka nie przepuści, i wypisuje kolejne kroki.
- Workflow `.github/workflows/factory-checks.yml`: wszystkie bezpłatne sprawdzenia w repozytorium fabryki.
- **Jev (TypeSafe), opcjonalnie.** Dochodzą:
  - klient `.claude/hooks/jev_client.py` (wycina sekrety i przy błędzie wraca do zwykłego modelu);
  - ocena `--judge jev` w kaskadzie z haiku;
  - drugi etap podpowiedzi skilli `CLAUDE_SKILL_HINT_JEV=1`;
  - pomiar `factory/jev_calibration.py`.

  Bez `JEV_API_KEY` nic się nie zmienia.
### Poprawione
- Bramka znalazła 3 pary sąsiadów z błędną podpowiedzią. Poprawki:
  - słowa użytkownika w fw-angular, proc-agile i tool-jest;
  - hook rozpoznaje „Jest” (narzędzie), a nie tylko polski czasownik.

  Wynik bramki: 90/90 skilli.
- core-grounding: słowa dla pytań z fałszywym założeniem („kolega twierdzi”, „czy taka opcja istnieje”).
- Testy `tests/test_skill_gate.py` (9, w tym atrapa API Jev); uprawnienie `ask` dla płatnej bramki (`--model`).
### Do zrobienia
- Ewaluacja `core-skill-authoring` na modelu nie przeszła z powodu limitu wydatków organizacji. Powtórz:
  `python3 factory/skill_gate.py core-skill-authoring --model haiku,sonnet --budget 2`.

## [1.32.0] — 2026-10-03
### Nowe
- **Skill `core-cost-control`** (zawsze dołączany do person):
  - rubryka oceny zadania przed delegowaniem;
  - kaskada modeli z parametrem `model` narzędzia Agent;
  - effort, doradca (advisor) i `opusplan`;
  - co kasuje cache, a co nie;
  - kompaktowanie i pomiar.
- **Profile kosztów** `oszczedny` / `zrownowazony` / `jakosc` (`factory/config.yaml → profiles`) i polecenie
  `factory/profile.py`:
  - przestawia model i effort tierów całego zespołu;
  - ustawia sesję w `.claude/settings.local.json` (effortLevel, autoCompactWindow, advisorModel);
  - wybór trzyma w `.claude/factory-profile.json`, więc aktualizacje fabryki go nie ruszają;
  - aktualizacja przebudowuje agentów, gdy profil jest ustawiony.
- **Samoocena wykonawców:** linia `Tier: za niski/za wysoki` w kontrakcie raportu. `log_usage` zapisuje ją jako
  `tier_feedback`, a `cost_report.py` wykrywa eskalacje (ten sam agent na mocniejszym modelu w jednej sesji)
  i podpowiada zmianę domyślnego tieru roli.
- **Pasek stanu** `.claude/hooks/statusline.py`: model, effort, kontekst, cache (także „zimny”), koszt, limity.
- `autoCompactWindow: 200000` w ustawieniach; `build.py check` ostrzega o SKILL.md powyżej 15 tys. znaków.
### Zmienione
- Routing w promptach person: rubryka i kaskada z parametrem `model`, powrót na tańszy model po decyzji.
- CLAUDE.md: zasada kosztu i cache.
- Instalator scala klucze najwyższego poziomu (Twoje wartości mają pierwszeństwo). Paska stanu nie dodaje, gdy masz
  własny w `~/.claude/settings.json`; polecenie Pythona w pasku dostosowuje do Windows.
- Testy `tests/test_cost.py` (10); ewaluacje `tests/skill_evals/core-cost-control.json`.
### Ewaluacja na modelu (Claude Code CLI 2.1.288, 2026-10-03)
- `core-cost-control`: Haiku 3/3, Sonnet 3/3 (6/6, koszt $0,96). Skill uruchomiony narzędziem Skill w obu
  scenariuszach na model, bez fałszywego uruchomienia przy pytaniu o wydajność SQL (oba modele wybrały be-database).
  Wyniki: `docs/evals/2026-10-03-core-cost-control.md`.

## [1.31.0] — 2026-10-03
### Nowe
- **Skill `core-grounding`** (zawsze dołączany do person): klasy twierdzeń i dowód dla każdej, „nie wiem” jako
  poprawna odpowiedź, miejsca, w których modele zmyślają najczęściej, cytaty przed wnioskami, higiena kontekstu,
  samosprawdzenie. Referencja `references/sprawdzanie.md` z poleceniami sprawdzającymi.
- **`scripts/grounding_check.py`** — bez modelu sprawdza, czy ścieżki, odwołania `plik:linia` i lokalne linki
  w dokumentach istnieją (`--warn` tylko ostrzega).
- **Hook `context_guard`** (UserPromptSubmit) — ostrzega przy długim kontekście (domyślnie 100 i 150 tys. tokenów,
  `CLAUDE_CONTEXT_WARN_K`, 0 wyłącza); każdy próg raz na sesję.
- **Cecha `grounded`** („Nie zmyśla”) we wszystkich personach; sekcja „Rzetelność” w promptach wspólnych agentów
  (`grounding_note` w `factory/config.yaml`); zdanie „Czego nie sprawdziłeś, napisz wprost.” w kontrakcie raportu.
- Sekcja „Rzetelność” w CLAUDE.md; ewaluacje `tests/skill_evals/core-grounding.json`; testy `tests/test_grounding.py`.
### Zmienione
- `.claude/settings.json` (na prośbę użytkownika): hook `context_guard` i uprawnienie do `grounding_check.py`.

## [1.30.0] — 2026-10-03
### Nowe
- **Zestaw do przebiegu próbnego** `docs/pilot/`:
  - opis pomysłu (rezerwacja sal) i decyzje właściciela produktu, żeby odpowiadać spójnie i móc powtórzyć przebieg;
  - polecenia krok po kroku dla Linuksa, macOS i Windowsa;
  - arkusz pomiarów jako artefakt `review`.
- **Pomiar podpowiedzi skilli w prawdziwej pracy**:
  - `skill_hint` zapisuje decyzje do `.claude/logs/skill-hints.jsonl` (bez treści polecenia, chyba że
    `CLAUDE_SKILL_HINT_LOG_PROMPT=1`);
  - `log_usage` zapisuje skille użyte w sesji;
  - `factory/hint_report.py` liczy podpowiedzi trafione, zignorowane i przeoczone, ze wskazówkami do
    `metadata.slowa`.
- **Ceny modeli** w `factory/config.yaml` (Haiku 4.5, Sonnet 5/5.5, Opus 5.5; cennik z 2026-10-03), więc
  `cost_report.py` pokazuje szacunek w USD.
### Zmienione
- Testy ewaluacji: 12, w tym log hooka bez treści polecenia oraz raport trafione/przeoczone.
- Uprawnienie `Bash(python3 factory/hint_report.py *)` w ustawieniach.

## [1.29.3] — 2026-10-03
### Nowe
- Dokończony przebieg na Sonnecie (wszystkie 269 scenariuszy): 254 zaliczone (94%), właściwy skill 169/176 (96%),
  fałszywe uruchomienia 1/93, koszt 34,98 USD. Skille bez zmian.

## [1.29.2] — 2026-10-03
### Nowe
- Wyniki ewaluacji na Sonnecie (234 z 269 scenariuszy; przerwane limitem organizacji): 223 zaliczone (95%), właściwy
  skill w 146 ze 152 pytań (96%), 1 fałszywe uruchomienie. Na tych samych scenariuszach Haiku przed poprawkami:
  204 (87%). Szczegóły: `docs/evals/2026-10-02-wyniki-i-poprawki.md`. Skille bez zmian.

## [1.29.1] — 2026-10-02
### Zmienione
- Odesłania między sąsiednimi skillami tam, gdzie model wybierał sąsiada (wyniki ewaluacji, grupa A):
  - `core-git-workflow` → `core-conventional-commits` (poprawianie typu commita);
  - `eng-module-depth` → `ddd-discovery-intake` (czy w ogóle modularyzować);
  - `arch-tech-selection` → `fe-engineering-levels` (tarcie zespołów, DevEx);
  - `ops-security-operations` → `fe-architecture` (podatności frameworków frontendu, np. RSC).

  Treść skilli bez usunięć.
- Ewaluacje: pole `accept` dla scenariuszy, w których obszary skilli celowo się pokrywają.

## [1.29.0] — 2026-10-02
Pełny przebieg ewaluacji na Haiku i poprawki według wyników (`docs/evals/2026-10-02-wyniki-i-poprawki.md`).
Wynik: 236/269 (88%), po poprawkach szacunkowo ~258/269 (96%).
### Poprawione
- **Usunięte `paths` z 8 skilli technologicznych** (`lang-*`, `fw-angular`, `tool-*`; sprostowanie do 1.27.0).
  Pomiar: skill z `paths` jest dla modelu nieznany („Unknown skill”), dopóki w sesji nie ma pasującego pliku, także
  przy jawnym wywołaniu i w personach. `build.py check` ostrzega przed tym polem, a szablon skilla je odradza.
- **Skille „tylko ręcznie”** (`core-factory-update`, `core-teaching-workspace`, `ddd-es-simulation`): model omijał
  `disable-model-invocation`, czytając plik narzędziem Read. Na początku każdego dodano notę, że przy odczycie
  z innego powodu nie wolno wykonywać kroków.
- **Hook `skill_hint`**:
  - normalizuje wynik treści względem długości skilla, więc długie skille nie wygrywają słowami ogólnymi;
  - indeksuje nowe pole `metadata.slowa` (słownictwo użytkowników, 18 skilli);
  - pomija cytowany materiał (tekst do redakcji, kod).

  Trafność offline wzrosła z 89% do 95%, a w 25 trudnych przypadkach z 11 do 23.
- Opisy `arch-system-design` (dostępność złożona) i `core-stack-sync` (nie podnosi zależności); w `ddd-deep-modeling`
  odesłanie „pole status → 5 why”. Treść skilli bez usunięć.
### Nowe
- Ewaluacje: scenariusz bez plików dla każdego skilla technologicznego. W runnerze:
  - `--only-failed <jsonl>` powtarza niezaliczone scenariusze;
  - odczyt skilla „tylko ręcznie” nie liczy się jako uruchomienie.

## [1.28.1] — 2026-10-02
### Nowe
- Pierwszy przebieg ewaluacji na Haiku: 94 z 261 scenariuszy (32 skille), przerwany limitem wydatków organizacji.
  Wynik: 81/94 zaliczone, uruchomienie skilla 49/57, fałszywe 3/37, koszt 9,54 USD. Wyniki
  i rekomendacje poprawek: `docs/evals/2026-10-02-rekomendacje.md` (wejście do kolejnej części). Najważniejsza:
  `paths` dodane w 1.27.0 najpewniej ukrywa skille technologiczne bez pasujących plików (R1 do potwierdzenia).
### Zmienione
- Runner ewaluacji:
  - wykrywa limit użycia lub częstości i nie startuje kolejnych przebiegów;
  - `--resume <jsonl>` dokańcza przerwany zestaw i przelicza raport z całości;
  - zapisuje, czy skill wczytano narzędziem Skill czy odczytem pliku (`via`), oraz błędy narzędzi;
  - raport oddziela przebiegi przerwane limitem.

## [1.28.0] — 2026-10-02
### Nowe
- **Ewaluacje skilli** (zalecenie Anthropic: co najmniej trzy na skill, test na Haiku, Sonnecie i Opusie).
  `tests/skill_evals/<skill>.json` dla wszystkich 87 skilli: 2 pytania, przy których skill ma się uruchomić,
  z kontrolą wiedzy specyficznej, i 1 pytanie sąsiedniego skilla. Runner `tests/run_skill_evals.py`:
  - uruchamia `claude -p` w trybie `plan`, w katalogu tymczasowym z pełnym środowiskiem fabryki;
  - wykrywa uruchomienie skilla (narzędzie Skill albo odczyt SKILL.md);
  - sprawdza treść wyrażeniami regularnymi, a gdy nie trafią, tanim modelem oceniającym (`--judge`);
  - pozwala porównać z przebiegiem bez skilli (`--baseline`);
  - pilnuje limitu kosztu (`--budget-usd`, domyślnie 5) i pyta o potwierdzenie;
  - zapisuje raport md i surowe wyniki jsonl.
- **Hook `skill_hint.py`** (UserPromptSubmit): przy każdym poleceniu podpowiada 1–3 skille fabryki pasujące do
  treści. Dopasowuje bez modelu rdzenie słów z wagą rzadkości: opis, katalog i treść SKILL.md, z progiem i wymogiem
  wyraźnego lidera. Pomiar na 10 pytaniach z 5 skilli: uruchomienia skilli wzrosły z 0/10 (Haiku) i 3/10 (Sonnet)
  do 10/10 na obu modelach, bez fałszywych uruchomień przy pytaniach sąsiadów. Bez podpowiedzi Haiku nie widział
  opisów skilli fabryki (lista w ~1% okna kontekstu mieściła same nazwy). `--explain` pokazuje ranking, a
  `CLAUDE_SKILL_HINT=0` wyłącza hook.
- `tests/test_skill_evals.py` (bez modelu): runner z atrapą `claude`, poprawność plików scenariuszy, trafność hooka
  ≥ 80% na scenariuszach i brak podpowiedzi przy poleceniach ogólnych.
### Zmienione
- `build.py check` ostrzega o skillu bez scenariuszy ewaluacji, a szablon skilla o nich przypomina.
- Zmiana obejmuje `.claude/settings.json` i hooki (na prośbę użytkownika). Aktualizacja dopisuje hook do ustawień.

## [1.27.0] — 2026-10-02
Dostosowanie do aktualnych zaleceń Anthropic (dokumentacja Claude Code i Agent Skills).
### Zmienione
- **Krótkie opisy skilli.** Claude Code trzyma listę opisów w ~1% okna kontekstu i przy przepełnieniu usuwa opisy
  najrzadziej używanych skilli. Opisy wszystkich 87 skilli skrócono do 141 znaków maksymalnie (średnio 126),
  co zmniejsza listę z ~29 tys. do ~12 tys. znaków. Pełny opis z granicami („Nie do …”) przeniesiono do
  `metadata.katalog`. Katalog Mai pokazuje krótki opis z granicami.
- `paths` dla skilli technologicznych (`lang-*`, `fw-angular`, `tool-*`). `disable-model-invocation: true` dla
  `ddd-es-simulation` (uruchamiany tylko na wyraźne żądanie).
- `build.py check`: opis skilla ≤ 170 znaków, ostrzeżenie, gdy suma listy przekracza 14 000 znaków, ostrzeżenie
  o braku `metadata.katalog`. Szablon nowego skilla i `new-skill` tworzą oba pola.
- **Spisy treści**: 95 plików referencyjnych dłuższych niż 100 linii ma jednoliniowy spis treści pod tytułem.
  Generuje go `build.py`, a `check` zgłasza brak lub nieaktualność.
- **Pamięć agentów** (`memory: project`) dla `architect` i `security-reviewer`. Instalacja prywatna wyklucza
  `.claude/agent-memory/` z gita.
- security-reviewer nie zgłasza preferencji stylu ani zabezpieczeń na niemożliwe przypadki (zalecenie Anthropic
  przeciw przeinżynierowaniu po przeglądzie).
- CLAUDE.md: co zachować przy kompaktowaniu kontekstu. `core-delivery-lifecycle`: mierzalny koniec kroku z `/goal`
  i przegląd w świeżym kontekście.
- README: sekcja „Zgodność z praktykami Anthropic” z poleceniami (`/context`, `/doctor`, `/skill-doctor`,
  `/doctor prompt-audit`, `/code-review`, `/verify`) i świadomymi odstępstwami.

## [1.26.0] — 2026-10-02
### Nowe
- **Punkt kontrolny pracy w toku** (`docs/project/wip/<zadanie>.md`). Pozwala przerwać sesję w dowolnym momencie
  i wrócić do pracy. Polecenia `project_record.py wip start "<cel>" | list | show | pause | block | resume | done |
  snapshot`. Szablon zawiera cel i kryterium „gotowe”, kroki z dowodem, następną czynność, ustalenia z rozmowy,
  pułapki i otwarte pytania. `done` przenosi plik do `archive/wip/`.
- Hooki:
  - `PreCompact` i `SessionEnd` zapisują w punkcie kontrolnym „Stan automatyczny” (gałąź, ostatni commit,
    niezacommitowane pliki) bez zmiany czasu modyfikacji pliku;
  - `Stop` prosi agenta o aktualizację punktu kontrolnego, gdy jest on o ponad 10 minut starszy niż zmiany w plikach
    (najwyżej raz z rzędu dzięki `stop_hook_active`);
  - `SessionStart` pokazuje aktywne zadania, następną czynność i niezrobione kroki.
- Indeks `docs/project/README.md` ma sekcję „Praca w toku”.
### Zmienione
- `core-project-record`: sekcja „Praca w toku — przerwanie sesji i powrót” (kiedy zakładać, co aktualizować po każdym
  kroku, jak wznawiać). CLAUDE.md i prompty orkiestratorów mówią o punkcie kontrolnym.
- Testy dziennika projektu: 32.
- Instalator scala hooki pojedynczo, a nie całymi wpisami. Wcześniej nowy hook dodany do istniejącego wpisu (np.
  drugi hook `SessionEnd`) nie trafiał do ustawień przy aktualizacji.
- Zmiana obejmuje `.claude/settings.json` i hooki (na prośbę użytkownika). Instalator dopisuje nowe hooki do
  istniejących ustawień przy aktualizacji.

## [1.25.1] — 2026-10-02
### Poprawione
- **Windows: polecenie Pythona.** Hooki uruchamiały Pythona poleceniem `python3`, które na Windowsie często nie
  istnieje albo prowadzi do aliasu Sklepu Microsoft. Taki hook kończy się błędem nieblokującym, więc strażnicy
  bezpieczeństwa po cichu nie działali. Instalator wykrywa teraz polecenie, które naprawdę uruchamia Pythona 3.9+
  (Windows: `py`, `python`, `python3`; Linux i macOS: `python3`, `python`). Gdy żadne nie działa, używa pełnej ścieżki
  interpretera instalatora. Wybór trafia do hooków, reguł uprawnień (`Bash(py …)`), manifestu (aktualizacje go
  zachowują) i sekcji CLAUDE.md („Python w tym projekcie: `py`”), żeby agenci uruchamiali skrypty tym samym
  poleceniem. Nowa opcja `--python <polecenie>` wymusza wybór, a instalator wypisuje wybrane polecenie i ostrzega,
  gdy nie działa.
- `guard_bash`: blokada „pobierz i wykonaj” obejmuje też `| py`. Testy hooków: 89.
- README: instalacja na Windowsie (PowerShell, `py`) i uwaga o trybie zespołowym przy zespołach z różnymi systemami.

## [1.25.0] — 2026-10-01
### Nowe
- Skill `core-delivery-lifecycle`: cykl od pomysłu do oprogramowania gotowego do wdrożenia. Opisuje fazy 0–8
  z katalogami `docs/project/`, personami, skillami i kryteriami wyjścia oraz bramki człowieka B1–B5 (zakres,
  wymagania, architektura, gotowość, wydanie). Zawiera też ścieżkę skróconą dla małych projektów (B4 i B5 zostają
  zawsze), zasady przebiegu (szkielet end-to-end i ryzyko najpierw, testy od wymagań, bez cichych zmian zakresu) oraz
  listę tego, czego fabryka nie zrobi sama.
- `references/gotowosc-produkcyjna.md`: przegląd gotowości w 8 obszarach (funkcje, bezpieczeństwo, wydajność,
  obserwowalność, wydanie i wycofanie, dane, dokumentacja, koszt i zgodność). Każdy punkt wymaga dowodu, punkty
  *minimum* obowiązują w ścieżce skróconej, a przegląd kończy się werdyktem dla bramki B4.
- `references/przebieg-probny.md`: jak na małym projekcie zmierzyć, czy fabryka dowozi (czas, koszt, interwencje
  człowieka, odesłania, defekty), z kryteriami oceny i zasadą zgłaszania poprawek do fabryki.
### Zmienione
- Maja (dyspozytorka) prowadzi cały projekt według nowego skilla. Skill dostały też role solution-architect i sre.
- `core-problem-routing`: wiersz o projekcie od pomysłu do produkcji i o gotowości produkcyjnej.

## [1.24.1] — 2026-10-01
### Zmienione
Na podstawie artykułu Developer Awam „7 Core Infrastructure Concepts You Need to Master to Become a DevOps Engineer”
(CodeX / Medium). Większość tematów (skalowanie, load balancer, CDN, brama API) była już opisana. Dodane zostało:
- `arch-system-design`: sekcja „Opóźnienie, przepustowość i skalowalność”: definicje i różnica, prawo Little'a do
  wymiarowania pul i instancji, skalowalność jako cecha całego systemu (wąskie gardło się przesuwa), skalowanie
  pionowe a poziome, przyklejone sesje, sprawdzanie zdrowia w load balancerze.
- `be-api-design/references/style-i-komunikacja.md`: brama API jako element wymagający wysokiej dostępności
  i własnych SLO; autoryzacja nadal w usługach.

## [1.24.0] — 2026-10-01
### Nowe
Na podstawie repozytorium [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)
(CC BY 4.0, © Donne Martin). README w większości pokrywało się z 1.22.0, więc dodane są głównie przykładowe
rozwiązania i drobne luki:
- `arch-system-design/references/przyklady-projektow.md`: przeliczniki (2,5 mln s w miesiącu, potęgi dwójki,
  długość identyfikatora base62), drabina skalowania od jednego serwera do milionów użytkowników, osiem ćwiczeń
  (pastebin, oś czasu i wyszukiwanie, robot sieciowy, Mint, graf społecznościowy, cache zapytań, ranking sprzedaży,
  skalowanie w AWS) z kluczowymi decyzjami, wzorce przekrojowe (rozsyłanie przy zapisie i przy odczycie, wyliczanie
  wsadowe, tylko aktywne dane w pamięci, haszowanie spójne).
### Zmienione
- `arch-system-design`: przeliczniki w szacunkach, skalowanie iteracyjne zamiast skoku do projektu docelowego.
- `eng-algorithms-data-structures`: cache LRU (mapa + lista dwukierunkowa, `Map` w JS, `LinkedHashMap`, biblioteki,
  LFU i TinyLFU); dwukierunkowy BFS i BFS na grafie podzielonym między maszyny.
- `be-database/references/wydajnosc-bazy.md`: sekcja „Schemat i typy a wydajność” z poprawkami do porad z MySQL 5.x
  (`text`/`varchar`/`char` w PostgreSQL, brak query cache w MySQL 8.0, `bigint`, `numeric` dla pieniędzy, duże
  importy).
- `core-problem-routing`: wiersz o przykładach projektów.

## [1.23.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Data Structures and Algorithms](https://roadmap.sh/datastructures-and-algorithms)
(107 tematów z repozytorium developer-roadmap):
- Skill `eng-algorithms-data-structures`: analiza złożoności (klasy, liczenie, ukryte pętle, pamięć, amortyzacja),
  dobór struktury danych z odpowiednikami w TS/JS i Javie, sortowanie i wyszukiwanie w praktyce (pułapka `sort()`
  bez komparatora), poprawność (niezmienniki, testy właściwości, głębokość rekurencji).
- `references/wzorce-i-techniki.md`: 11 wzorców (dwa wskaźniki, okno, szybki i wolny wskaźnik, przedziały, sortowanie
  cykliczne, top-k, dwa kopce, siatki, binarnie po odpowiedzi, sumy prefiksowe, stos monotoniczny), techniki
  (siłowo, rekurencja, nawroty, dziel i zwyciężaj, programowanie dynamiczne, zachłanne, losowe i probabilistyczne),
  podejście do nowego problemu.
- `references/drzewa-i-grafy.md`: przechodzenie drzew, BST i drzewa zrównoważone, B/B+-drzewa, kopiec, trie, drzewa
  przedziałowe i Fenwicka, sufiksy, skip list; reprezentacja grafów, BFS/DFS, Dijkstra, Bellman-Ford, A*, Kruskal,
  Prim, sortowanie topologiczne, union-find.
### Zmienione
- Role `backend`, `frontend`, `solution-architect` + `eng-algorithms-data-structures`; `ddd-algorithm-recognition`
  i `core-problem-routing`: odnośniki.

## [1.22.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — System Design](https://roadmap.sh/system-design) (147 tematów z repozytorium
developer-roadmap; wzorce chmurowe, cache, równoważenie, CAP i kolejki już były) — tylko to, czego brakowało:
- Skill `arch-system-design`: procedura od przypadków użycia i ograniczeń przez szacunki na serwetce, API i model
  danych, projekt ogólny i pogłębienia po wąskie gardła przy 10× i operacje; rzędy wielkości opóźnień; dostępność
  w liczbach (szeregowo, równolegle); failover aktywny–pasywny i aktywny–aktywny, replikacja, federacja, odkrywanie
  usług; TCP/UDP, CDN push i pull.
- `arch-system-design/references/antywzorce-wydajnosci.md`: 10 antywzorców z katalogu Azure (zajęta baza, zajęty
  front, gadatliwe I/O, zbędne pobieranie, niewłaściwe tworzenie instancji, monolityczne utrwalanie, brak cache,
  hałaśliwy sąsiad, burza ponowień, synchroniczne I/O) z objawem, wykryciem i naprawą.
### Zmienione
- `checklista-wydajnosci-backendu.md`: refresh-ahead; rola `solution-architect` + `arch-system-design`;
  `core-problem-routing`: wiersz.

## [1.21.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — AI and Data Scientist](https://roadmap.sh/ai-data-scientist) (10 tematów
z listą zagadnień i źródeł) — rozszerzenie `data-analysis`:
- `references/eksperymenty-zaawansowane.md`: centralne twierdzenie graniczne, losowanie i efekty sieciowe, MDE i moc,
  redukcja wariancji (CUPED z warunkami, CUPAC, stratyfikacja, ciężkie ogony), metryki ilorazowe (metoda delta,
  bootstrap po użytkownikach).
- `references/szeregi-czasowe-i-ekonometria.md`: dekompozycja, stacjonarność, modele od naiwnego przez ETS i ARIMA
  po regresję z cechami, backtesting, MASE, przedziały prognozy; regresja z odpornymi błędami, endogeniczność,
  różnica w różnicach, efekty stałe, zmienne instrumentalne, nieciągłość regresji; dopasowanie rozkładów.
### Zmienione
- `references/uczenie-maszynowe.md`: fundamenty matematyczne, zespoły modeli, mapa głębokiego uczenia i uczenie
  transferowe, inżynieria AI (prompt, RAG, agenci, dostrajanie, evals), MLOps (serwowanie, rejestr modeli, magazyn
  cech, CI/CD, wdrożenie w cieniu, monitorowanie przesunięcia).
- Persona Zofia: opis obejmuje eksperymenty, prognozy i MLOps.

## [1.20.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Data Engineer](https://roadmap.sh/data-engineer) (190 tematów z repozytorium
developer-roadmap) — tylko to, czego brakowało:
- Skill `data-engineering`: cykl życia danych i jego „nurty”, sposoby pozyskiwania (pełne, przyrostowe, CDC, zdarzenia,
  partnerzy), kolejki vs logi, zasady potoku (idempotencja, partycje czasu, backfill, spóźnione dane, ewolucja schematu
  i kontrakty danych, atomowa publikacja, koszt), orkiestracja (Airflow 3, Dagster, Prefect), warstwy i dbt, formaty
  (Parquet, Avro, Iceberg, Delta, Hudi), serwowanie i reverse ETL, testy potoków.
- `data-engineering/references/jakosc-zarzadzanie-i-zgodnosc.md`: wymiary jakości z testami, obserwowalność danych,
  katalog, pochodzenie (OpenLineage), lake / mart / lakehouse / hub / fabric / mesh, klasyfikacja, maskowanie,
  pseudonimizacja, tokenizacja, retencja, RODO, AI Act (art. 50 od 2.08.2026, wysokie ryzyko przesunięte przez
  Digital Omnibus).
- Rola `data-engineer`; persona Zofia ma teraz role `data-analyst` i `data-engineer`.
### Zmienione
- `core-problem-routing`: wiersz dla inżynierii danych; `data-analysis`: rozgraniczenie z `data-engineering`.

## [1.19.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Data Analyst](https://roadmap.sh/data-analyst) (102 tematy z repozytorium
developer-roadmap) — dziedzina, której fabryka nie miała:
- Wymiar `data-` (analiza danych) w `factory/config.yaml`.
- Skill `data-analysis`: rodzaje analizy, procedura (pytanie i decyzja, dane i RODO, rodzaje zmiennych, czyszczenie
  w skrypcie, EDA, analiza z kontrolą zakłóceń i paradoksem Simpsona, wizualizacja, raport z ograniczeniami),
  narzędzia (SQL, pandas, R, arkusze, BI). Referencje: `statystyka.md`, `wizualizacja.md`, `uczenie-maszynowe.md`.
- Rola `data-analyst` i persona **Zofia — Data Analyst** (`claude --agent zofia`); Maja może ją dołączać.
### Zmienione
- `core-problem-routing`: wiersz dla analizy danych.

## [1.18.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Cyber Security](https://roadmap.sh/cyber-security) (302 tematy, głównie ścieżka
kariery analityka i certyfikaty) — wybrane tematy przydatne zespołowi wytwarzającemu oprogramowanie:
- `ops-security-operations/references/ataki-i-analiza.md`: katalog ataków (phishing i odmiany, zgadywanie haseł,
  przejęcie sesji, MITM, replay, błędy webowe, podniesienie uprawnień, LOLBAS/GTFOBins, ruch boczny w AD, DoS,
  łańcuch dostaw, drive-by, zero-day, socjotechnika) z sygnałem i kontrolą; Cyber Kill Chain, MITRE ATT&CK, model
  diamentu; klasyfikacja alertów TP/FP/TN/FN; polowanie na zagrożenia; wywiad i OSINT z ostrzeżeniem o publicznych
  piaskownicach; honeypoty, honeytokeny, sinkhole.
- `ops-security-operations/references/forensyka-i-testy-penetracyjne.md`: kolejność ulotności (RFC 3227), obrazy
  i skróty, łańcuch dowodowy, oś czasu; zasady zaangażowania testów penetracyjnych, zespoły czerwony, niebieski
  i purpurowy; zasada dla agentów.
### Zmienione
- `siec-i-chmura.md`: tożsamość i sieć w firmie (AD/LDAPS, Kerberos, NTLM, 802.1X/RADIUS, NAC, VPN, WPA3, VLAN,
  DNSSEC, DLP, stacje programistów).
- `core-agent-security` 5b: zakaz testów ofensywnych bez pisemnego zakresu i przesyłania danych do publicznych
  serwisów analizy.

## [1.17.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Software Architect](https://roadmap.sh/software-architect) (112 tematów z repozytorium
developer-roadmap) — tylko to, czego brakowało:
- Skill `arch-architect-practice`: poziomy architektury (aplikacja, rozwiązanie, przedsiębiorstwo), oczekiwania wobec
  architekta, procedura decyzji i komunikacja do trzech odbiorców, upraszczanie i równowaga, szacowanie w przedziałach,
  lekki przegląd w stylu ATAM (punkty wrażliwości, kompromisy, ryzyka), dokumentacja (ADR, C4, arc42), doradztwo.
  Referencja `ramy-korporacyjne.md`: TOGAF (ADM), ArchiMate, Zachman, IAF, BABOK, ITIL 4, PRINCE2, PMBOK, RUP i ramy
  zwinne — z mapowaniem na artefakty fabryki.
- `arch-quality-attributes/references/architektura-danych.md`: ACID i izolacja, CAP i PACELC, BASE i spójność
  ostateczna, rodzaje baz z wyborem, OLTP vs OLAP, hurtownia i lakehouse, schemat gwiazdy i SCD2, ETL vs ELT, CDC,
  przetwarzanie wsadowe i strumieniowe.
### Zmienione
- `katalog-stylow.md`: orkiestracja procesów (choreografia, saga, Camunda, Temporal, BPEL).
- Rola `solution-architect` + `arch-architect-practice`; `arch-quality-attributes`, `core-problem-routing`: odnośniki.

## [1.16.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Technical Writer](https://roadmap.sh/technical-writer) (84 tematy z repozytorium
developer-roadmap) i źródeł (Diátaxis, Vale) — tylko to, czego brakowało w `core-tech-docs`:
- `references/rodzaje-dokumentacji.md`: Diátaxis (tutorial, instrukcja, referencja, wyjaśnienie — nie mieszać),
  ścieżka programisty (szybki start, uwierzytelnianie, referencja generowana, lista błędów, przykłady testowane w CI,
  macierz platform), rozwiązywanie problemów według objawu, FAQ, notatki o wydaniu vs CHANGELOG, inne formy.
- `references/utrzymanie-i-pomiar.md`: właściciel i data przeglądu, sprawdzanie linków i przykładów w CI, luki ze
  zgłoszeń, wyszukiwania i społeczności, przewodnik stylu i Vale (z zastrzeżeniem dla polskiego), metryki zadaniowe.
- `references/tresci-techniczne-i-seo.md`: odbiorca (ICP, persony), lejek treści, uczciwe porównania, SEO (intencja,
  frazy, tytuły, klastry, canonical, Open Graph, linki), dystrybucja i UTM, oryginalność.
### Zmienione
- `core-tech-docs`: tabela „Który dokument” i indeks referencji.

## [1.15.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — DevOps](https://roadmap.sh/devops) (140 tematów, w większości narzędzia)
— tylko to, czego brakowało:
- Skill `ops-linux-networking`: diagnoza od objawu do przyczyny tylko do odczytu (USE, procesy i systemd, `lsof`,
  `strace`, przetwarzanie logów), sieć warstwami (`mtr`, `ss`, `dig`, `openssl s_client`, `curl -w`, `tcpdump`),
  DNS i TTL, HTTP/1.1–3, zapora, SSH bez haseł i przez bastion, zarządzanie konfiguracją (Ansible, Pulumi, CDK).
  Referencje: `serwery-www-i-proxy.md` (reverse proxy, L4/L7, proxy wychodzące, cache, nagłówki `X-Forwarded-*`,
  limity czasu w łańcuchu, SSE i WebSocket, siatka usług, repozytoria artefaktów) i `poczta-email.md` (SPF, DKIM,
  DMARC z wyrównaniem, wymagania Gmaila dla nadawców masowych i egzekwowanie od 11.2025, RFC 8058, porty).
- `arch-quality-attributes/references/wzorce-chmurowe.md`: 44 wzorce chmurowe z katalogu Azure z mapą na skille
  fabryki, Strangler Fig, Deployment Stamps, Sidecar; wybór platformy (PaaS, funkcje, kontenery, Kubernetes, VM).
### Zmienione
- Role `devops` i `sre` + `ops-linux-networking`; `arch-quality-attributes`, `core-problem-routing`: odnośniki.

## [1.14.0] — 2026-10-01
### Nowe
Na podstawie listy [roadmap.sh — Backend Performance Best Practices](https://roadmap.sh/backend-performance-best-practices)
(ok. 45 punktów w 10 grupach) — tylko to, czego brakowało:
- `be-api-design/references/checklista-wydajnosci-backendu.md`: wzorce cache (cache-aside, read-through,
  write-through, write-behind), unieważnianie i ochrona przed lawiną zapytań, połączenia wielokrotnego użytku,
  budżet czasu i limity na wywołaniach, ponowienia z budżetem, batch, asynchroniczność, skalowanie i równoważenie,
  profilowanie (JFR, async-profiler, `--cpu-prof`), logowanie asynchroniczne, kiedy zmiana języka lub podział usług.
- `be-database/references/wydajnosc-bazy.md`: rozmiar puli połączeń (wzór z wiki HikariCP, suma instancji ≤
  `max_connections`, PgBouncer, limity czasu), log wolnych zapytań, `pg_stat_statements`, `auto_explain`,
  `EXPLAIN (ANALYZE, BUFFERS)`, indeksy częściowe i pokrywające, VACUUM, retencja, repliki i read-your-writes,
  widoki zmaterializowane, partycjonowanie, sharding jako ostateczność.
### Zmienione
- `be-database`, `be-api-design`: odnośniki do nowych referencji.

## [1.13.0] — 2026-10-01
### Nowe
- `fe-web-platform/references/checklista-wydajnosci.md`: checklista z [roadmap.sh — Frontend Performance Best
  Practices](https://roadmap.sh/frontend-performance-best-practices) i jej źródła (Front-End-Performance-Checklist,
  MIT), z poprawkami: Core Web Vitals zamiast „ładowania < 3 s”, TTFB ≤ 0,8 s zamiast 1,3 s, liczba żądań i łączenie
  CSS przy HTTP/2, krytyczny CSS w linii jako wyjątek, aktualizacja zależności tylko na prośbę człowieka. Dodane:
  bfcache, skrypty zewnętrzne, SSR i hydracja, ciasteczka, budżety w CI (Angular `budgets`, Lighthouse CI, RUM).
### Zmienione
- `fe-web-platform` i `core-web-vitals.md`: odnośniki do checklisty.

## [1.12.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — QA](https://roadmap.sh/qa) (146 tematów z repozytorium developer-roadmap)
i dokumentacji narzędzi (k6, Mailpit) — tylko tematy, których brakowało:
- Skill `qa-performance-testing`: rodzaje testów (dymny, obciążenia, przeciążenia, wytrzymałości, skoku, punktu
  granicznego), procedura od progów z SLO przez model obciążenia (otwarty vs zamknięty), środowisko i dane, skrypt
  k6 z progami, obserwację i analizę (USE) po raport; testy wydajności w CI.
- `qa-test-design/references/strategia-i-plan-testow.md`: weryfikacja i walidacja, podejścia (czarna/biała/szara
  skrzynka), dymne, sanity, regresja, UAT, myślenie testera, model V i praca zwinna, przesunięcie w lewo i w prawo,
  plan testów z kryteriami wejścia i wyjścia, raport, metryki, analiza ucieczek defektów.
- `qa-regression/references/dane-srodowiska-i-specjalne.md`: dane syntetyczne i anonimizacja, testowanie e-maili
  (Mailpit), kompatybilność, aplikacje mobilne, narzędzia testów API, bezpieczeństwo w pracy QA (ZAP), monitoring
  syntetyczny i śledzenie błędów po wydaniu.
### Zmienione
- Rola `qa-automation` + `qa-performance-testing`; `qa-test-design`, `qa-regression`, `core-problem-routing`: odnośniki.

## [1.11.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — UX Design](https://roadmap.sh/ux-design) (94 tematy z repozytorium
developer-roadmap) — projektowanie zachowań, model biznesowy i modelowanie procesów, których fabryka nie miała:
- `fe-ux-design/references/projektowanie-zachowan.md`: bramka etyczna (macierz manipulacji), aktor–działanie–wynik,
  siatka zachowań i model Fogga (B = MAP), lejek CREATE (Wendel), dwa systemy myślenia, trzy strategie (zrób za
  użytkownika → nawyk → świadome działanie), techniki z granicami nadużyć (wartości domyślne, dowód społeczny,
  niechęć do straty, grywalizacja, model haczyka), spektrum interwencji, pomiar.
- `proc-product-discovery/references/model-biznesowy-i-rynek.md`: kanwa modelu biznesowego, Lean Canvas, analiza
  konkurencji, SWOT z działaniami, pięć sił Portera, mapa doświadczenia klienta.
### Zmienione
- `ddd-event-storming`: sekcja 6a — formalny zapis procesu w BPMN 2.0 i EPC z mapowaniem z warsztatu.
- `proc-product-discovery/references/eksperymenty-i-wydanie.md`: testy przyrostowe, wielowariantowe i inkrementalności.
- `fe-ux-design`, `proc-product-discovery`: odnośniki do nowych referencji.

## [1.10.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Product Design](https://roadmap.sh/product-design) (118 tematów z repozytorium
developer-roadmap) i źródeł (NN/g, Product Talk, Google HEART, Material Design) — fabryka nie miała tej dziedziny:
- Skill `proc-product-discovery`: wynik zamiast funkcji, drzewo szans i rozwiązań, stwierdzenie problemu, JTBD,
  „jak moglibyśmy”, ≥ 3 rozwiązania, mapa założeń w czterech ryzykach, testy założeń od najtańszego. Referencje:
  `priorytety-i-metryki.md` (RICE, MoSCoW, Kano, HEART z GSM, OKR, metryka wiodąca i ochronne, PMF, plan zdarzeń,
  RODO) i `eksperymenty-i-wydanie.md` (projekt testu A/B, pułapki, gotowość do wydania).
- Skill `fe-ux-design`: analiza zadań, przepływy z tabelą stanów, architektura informacji, makiety i prototypy,
  specyfikacja dla programistów, przegląd projektu. Referencje: `heurystyki-i-testy.md` (10 heurystyk Nielsena,
  skala wagi, przegląd ekspercki, testy użyteczności, SUS, benchmark), `ui-wizualny-i-ruch.md` (hierarchia,
  typografia, kolor, siatka, stany, mikrointerakcje, ruch) i `tresci-i-etyka.md` (teksty interfejsu, głos i ton,
  projekt włączający, wzorce zwodnicze i DSA art. 25).
- Rola `product-designer` i persona **Natalia — Product Designer** (`claude --agent natalia`); Maja może ją dołączać
  do doraźnego zespołu.
### Zmienione
- `core-problem-routing`: wiersze dla odkrywania produktu i projektu UX.

## [1.9.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — DevSecOps](https://roadmap.sh/devsecops) (94 tematy z repozytorium developer-roadmap)
i źródeł (OWASP, NIST, AWS) — tylko tematy, których brakowało:
- Skill `arch-threat-modeling`: cztery pytania, DFD z granicami zaufania, mapa powierzchni ataku, STRIDE per element,
  PASTA, ocena ryzyka jakościowa i ilościowa (FAIR), decyzje o ryzyku (akceptacja tylko przez człowieka), testy nadużyć,
  OWASP Top 10:2025, szablon `threat-model.md`.
- Skill `ops-security-operations`: telemetria bezpieczeństwa i SIEM, rodzaje alertów i reguły jako kod (Sigma,
  MITRE ATT&CK), EDR/IDS/IPS/WAF, SOAR z bramką człowieka, podatności i łatki (inwentarz, KEV/EPSS, pierścienie),
  reagowanie według NIST SP 800-61r3 (dowody, ograniczanie skutków, usunięcie, odtworzenie, wnioski), zgłoszenia RODO
  i NIS2. Referencje: `siec-i-chmura.md` (CIA, obrona w głąb, segmentacja, zero trust, DDoS, CSPM, IAM, IGA, wiele
  regionów) i `zgodnosc.md` (NIST CSF 2.0, ISO 27001:2022, SOC 2, PCI DSS, mapowanie kontroli i dowody).
- `ops-secrets-identities/references/kryptografia-i-pki.md`: wybór algorytmów, KMS i szyfrowanie kopertowe, cykl
  życia certyfikatów (koniec OCSP w Let's Encrypt), własna PKI z odpornością na awarię, kryptografia postkwantowa.
### Zmienione
- Role: `solution-architect` + `arch-threat-modeling`; `devops` i `sre` + `ops-security-operations`.
- Agent `security-reviewer` wczytuje nowe skille, gdy diff dotyka granic zaufania, kryptografii lub wykrywania.
- `core-problem-routing`, `ops-secrets-identities`, `ops-sre-incidents`: odnośniki.

## [1.8.0] — 2026-10-01
### Nowe
- `be-auth-security/references/checklista-bezpieczenstwa-api.md`: checklista przed wydaniem API na podstawie
  [roadmap.sh — API Security Best Practices](https://roadmap.sh/api-security-best-practices) i jej źródła
  shieldfy/API-Security-Checklist (MIT, 64 punkty), z poprawkami uproszczeń (JWT to nie protokół logowania, twarda
  blokada konta jako wektor DoS, UUID nie zastępuje autoryzacji, „non-executable stack” to sprawa środowiska):
  JWT z algorytmem ustalonym na serwerze i JWKS, TLS i HSTS, zero trust i mTLS, `/me`, XXE i „billion laughs”,
  upload przez podpisany URL, RFC 9421, introspekcja GraphQL, nagłówki odpowiedzi API, CI/CD i monitorowanie.
### Zmienione
- `be-auth-security` i `be-api-design`: odnośniki do checklisty.

## [1.7.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — API Design](https://roadmap.sh/api-design) (99 tematów z repozytorium
developer-roadmap) i podlinkowanych źródeł — tylko tematy, których brakowało:
- `be-api-design/references/style-i-komunikacja.md`: wybór stylu (REST, GraphQL, gRPC, SOAP, webhooki, SSE, WebSocket,
  strumieniowanie, polling), operacje asynchroniczne `202`, projekt webhooków (HMAC, ponowienia, duplikaty, kolejność,
  SSRF), brama API i BFF (także jako strażnik tokenów).
- `be-api-design/references/http-w-praktyce.md`: cache HTTP, negocjacja treści, limity żądań (algorytmy, 429, projekt
  IETF RateLimit), paginacja kursorowa i filtry, batch vs bulk (207), ponowienia, HATEOAS w praktyce.
- `be-api-design/references/cykl-zycia-i-bezpieczenstwo.md`: design-first, wersjonowanie, `Deprecation` (RFC 9745)
  i `Sunset` (RFC 8594), OWASP API Security Top 10 2023 z kontrolami, klucze API, testy kontraktowe, mocki,
  wydajnościowe i bezpieczeństwa, dane osobowe.
- `be-auth-security/references/modele-autoryzacji.md`: RBAC, ABAC, ReBAC, PBAC, DAC, MAC — wybór i macierz testów.
### Zmienione
- `be-api-design`: indeks referencji, opis, punkty checklisty; `be-auth-security`: odnośnik do modeli autoryzacji.

## [1.6.0] — 2026-10-01
### Nowe
Na podstawie roadmapy [roadmap.sh — Software Design and Architecture](https://roadmap.sh/software-design-architecture)
(94 tematy z treścią paneli z repozytorium developer-roadmap) i podlinkowanych artykułów — tylko tematy, których brakowało:
- `eng-design-principles/references/komponenty-i-granice.md`: paradygmaty jako ograniczenia, polityka i szczegół,
  framework na dystans, struktura krzycząca domeną i podział według aktora, granice, zasady komponentów
  REP/CCP/CRP i ADP/SDP/SAP z metrykami I, A, D (strefa bólu, strefa bezużyteczności), praktyka w Nx i Javie.
- `be-database/references/wzorce-dostepu-do-danych.md`: skrypt transakcji / moduł tabeli / model domeny, Active Record
  vs Data Mapper, repozytorium, Unit of Work, Identity Map, lazy loading; co dają JPA, MikroORM, TypeORM i Prisma;
  ORM do zapisu i SQL do odczytu; DTO i mappery.
- `arch-quality-attributes/references/katalog-stylow.md`: warstwy, klient–serwer, SOA, peer-to-peer, mikrojądro,
  tablica, publish–subscribe, potoki i filtry, MVC/MVVM — kiedy, koszt, sygnał złego wyboru, jak wybierać.
### Zmienione
- `eng-design-principles`: tell-don't-ask (z zastrzeżeniem Fowlera), zasada Hollywood, hermetyzacja tego, co się zmienia.
- `eng-clean-code`: złożoność cyklomatyczna (próg, sposoby redukcji, reguły lintera), nieprzekazywanie `null`.

## [1.5.1] — 2026-10-01
### Zmienione
Na podstawie pełnego tekstu „10 Minor DevOps Mistakes That Can Cause Major Production Issues” (P. Natekar, 2026):
- `ops-observability`: „Zasoby, które rosną powoli” — alert z prognozy zapełnienia dysku, i-węzły, rotacja logów
  (Docker, kubelet, logrotate), `ephemeral-storage`, niezależny pomiar wygasania certyfikatów (blackbox_exporter,
  cert-manager), skracanie ważności certyfikatów publicznych (CA/B Forum SC-081v3); wdrożenia jako adnotacje
  „przed / po”; punkty checklisty.
- `ops-release-engineering`: „Wycofanie przećwiczone, nie założone” (retencja obrazów, warunki, zmiany nieodwracalne)
  i „Zmiana awaryjna na produkcji” (zapis, wstrzymanie samonaprawy GitOps, PR w ciągu dnia roboczego).
- `ops-sre-incidents`: kopie zapasowe z RPO/RTO i testem odtworzenia, przegląd pojedynczych punktów awarii,
  przegląd pojemności.
- `ops-kubernetes`: dlaczego `latest` zmienia zachowanie bez wdrożenia.
Nazwy metryk sprawdzone w kodzie źródłowym cert-manager, blackbox_exporter, node_exporter i kubelet.

## [1.5.0] — 2026-10-01
### Nowe
- `fe-web-platform/references/natywne-api-przegladarki.md`: 21 natywnych API przeglądarki z artykułu Lingo.dev, z mapą
  obsługi według MDN browser-compat-data (wszędzie / z rezerwą / tylko Chromium / nie używać), zasadami (wykrywanie
  funkcji, HTTPS, aktywacja użytkownika, uprawnienia w kontekście, Permissions-Policy, osłona SSR w Angularze, adapter),
  ścieżkami zastępczymi i wzorcami (wake lock, wylogowanie we wszystkich kartach, udostępnij albo skopiuj).
### Zmienione
- `fe-web-platform`: sekcja „API urządzeń i systemu”, indeks i punkt checklisty.

## [1.4.1] — 2026-10-01
### Zmienione
Uzupełnienia ze skilli Matta Pococka (opisy na aihero.dev: tdd, grilling, domain-modeling, codebase-design, teach,
handoff, wizard, triage, improve-codebase-architecture) — znane problemy i obejścia, których brakowało:
- `eng-module-depth`: „Jak wymusić głębokość w kodzie” (Nx `enforce-module-boundaries`, `exports`, dependency-cruiser,
  Java package-private / JPMS / ArchUnit); uwagi do przeglądu (pytanie startowe z kierunkiem, „brak kandydatów” jako
  poprawny wynik, zaniedbany kod, kod bez testów, raport bez CDN); krok 7 — od decyzji do zadań.
- `eng-testing` (TDD z agentem): pętla w przepływie, review sprawdza spoiny, specyfikacja dołączona do zadania.
- `core-plan-interview`: „Gdy przesłuchanie się psuje” (samodzielne odpowiedzi, słabszy model, pytania zależne, duży zakres).
- `ddd-facilitation`: słownik od agenta to propozycja do akceptacji, bez plików na zapas, słownik dla istniejącego repo.
- `core-teaching-workspace`: diagnoza przed lekcją 1, quiz jako bramka, powtórki z datami, kiedy skończyć kurs.
- `core-project-record` (przekazanie): cel następnej sesji, fakty sprawdzone vs założenia, powrót z rozgałęzienia,
  przekazanie czy `CLAUDE.md`.
- `ops-setup-wizard`: etapy, które mogły już zostać zrobione w usłudze zewnętrznej.
- `proc-issue-triage`: stany dla zewnętrznych PR, etykieta „zrobione, niezweryfikowane”.

## [1.4.0] — 2026-10-01
### Nowe
- `eng-module-depth`: głębokie moduły — słownik (moduł, interfejs, głębokość, spoina, adapter, dźwignia, lokalność),
  test usunięcia, kategorie zależności i testy po pogłębieniu, „zaprojektuj dwa razy” z 3 podagentami, przegląd
  kandydatów do pogłębienia z raportem w `docs/project/07-review/`.
- `core-plan-interview`: przesłuchanie planu — drzewo decyzji, rundy pytań niezależnych z rekomendacją, fakty sprawdzane
  samodzielnie, koniec po potwierdzeniu wspólnego zrozumienia.
- `proc-issue-triage`: triaż zgłoszeń i zewnętrznych PR — kategorie i stany, weryfikacja, `.out-of-scope/`, trwały brief.
- `ops-setup-wizard`: kreator konfiguracji jako skrypt bash dla człowieka (szablon `scripts/kreator.template.sh`;
  sekrety bez echa, `.env` z prawami 600, `gh secret` przez stdin).
- `core-teaching-workspace` (tylko na polecenie): nauka tematu przez wiele sesji — misja, źródła, lekcje, zapisy postępów.
### Zmienione
- `eng-testing`: `references/tdd-z-agentem.md` — uzgodnione spoiny, pionowe plasterki, trzy anty-wzorce, mocki na granicy.
- `ddd-facilitation`: słownik w trakcie projektowania (format wpisu z `_Unikaj_`, zapis od razu, konfrontacja z kodem).
- `core-tech-docs`: próg ADR (trudne do odwrócenia + zaskakujące + prawdziwy wybór).
- `core-project-record`: przekazanie pracy poza projekt lub sesję.
- Role: `solution-architect` i `backend` + `eng-module-depth`, `devops` + `ops-setup-wizard`, `qa-analyst` +
  `proc-issue-triage`, `ddd-analyst` i Maja + `core-plan-interview`; nowe wiersze w `core-problem-routing`.
- Źródło: [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) i opisy na aihero.dev — własnymi słowami.

## [1.3.0] — 2026-10-01
### Nowe
- Skill `eng-tech-debt-audit`: audyt długu technicznego (rozmiar × zmienność, 9 wymiarów, priorytet, raport, znaczniki `debt:`).
- Skill `eng-codebase-mapping`: mapa kodu z grafu zależności, trasa czytania, wpływ diffu → `docs/project/04-architecture/codebase-map.md`.
- Referencje: `core-tech-docs/references/diagramy-i-prezentacje.md`, `fe-css/references/przeglad-ui.md`,
  `fe-web-platform/references/seo-publiczne-strony.md`, `txt-polish-style/references/slady-pisania-ai.md`,
  `ddd-discovery-intake/references/badania-uzytkownikow.md`.
### Zmienione
- `eng-design-principles` (drabina minimalizmu), `core-project-record` (`docs/project/lessons.md`),
  `core-source-research` (tryb głębokiego badania), `core-agent-security` (pętle autonomiczne).
- Role: `solution-architect` dostaje `eng-codebase-mapping` i `eng-tech-debt-audit`; `frontend` i `backend` — `eng-codebase-mapping`.
- `core-problem-routing`: wiersze dla mapy kodu / długu oraz diagramów, przeglądu UI i SEO.
- Źródła: repozytoria z artykułu „20 AI agent skills…” (opisane własnymi słowami, bez ich skryptów).

## [1.2.0] — 2026-10-01
### Nowe
- Skill `core-source-research`: procedura badania aktualnych faktów i opinii — okno czasu z datą odniesienia,
  routing źródeł z rezerwą, ranga źródeł, scalanie tej samej historii z wielu źródeł, cytowanie z datą, nazwane luki.
  Wzorce z otwartoźródłowych skilli Agent-Reach i last30days-skill (opisane własnymi słowami, bez instalowania).
### Zmienione
- Agent `researcher` stosuje tę procedurę; skill dostali Tomasz (rola solution-architect) i Maja.
- Szablon skilla (`build.py new-skill`): sekcja „Procedura” i zasady pisania skilli jako procedur.

## [1.1.0] — 2026-10-01
### Nowe
- Aktualizacje jak w oprogramowaniu: `python3 factory/update.py` (źródło: katalog, plik .zip albo repozytorium git)
  i polecenie `/core-factory-update` w Claude Code. Manifest `.claude/factory-manifest.json` z wersją i skrótami plików:
  aktualizacja nie nadpisuje plików fabryki, które zmieniłeś (nowa wersja obok jako `*.factory-new`), i przenosi
  do `.claude/factory-backup/` pliki usunięte z fabryki.
- Persona **Piotr — DevOps / SRE** (role `devops` i nowa `sre`).
- Skille: `ops-kubernetes`, `ops-release-engineering`, `ops-sre-incidents` (z SLI → SLO → SLA), `ops-finops`,
  `ops-secrets-identities`, `ops-ai-inference`, `ops-supply-chain-security`, `core-agent-security`,
  `core-factory-update`.
- Hooki: blokada wzorców z analiz ataków (`base64 -d | sh`, `irm | iex`, `mshta`, metadane chmury, kasowanie historii,
  `chattr +i`, odczyt `~/.ssh`, `~/.kube/config`, `.git-credentials`); zgoda człowieka przy nowych zależnościach
  i wpisach trwałości (cron, systemd, LaunchAgents).
- Instalator działa w bieżącym katalogu (projekt nie musi być podany), ścieżki względne liczone od bieżącego katalogu;
  położenie fabryki raz w zmiennej `CLAUDE_TEAM_FACTORY` (używa jej też `update.py`). Ponowne uruchomienie
  instalatora w zainstalowanym projekcie = aktualizacja.
### Zmienione
- `be-auth-security`: kradzież i odtwarzanie sesji, rotacja i unieważnianie tokenów, OAuth (PKCE, zgody, device code),
  deserializacja, panele administracyjne.
- `ops-ci-cd`, `ops-docker`, `ops-iac-terraform` (bramki w PR, dryf, blokada stanu w S3), `ops-observability`
  (koszt telemetrii, sygnały bezpieczeństwa), `fe-architecture`, `lang-typescript`, `proc-team-topologies`,
  `arch-quality-attributes`.
- Skille spoza fabryki (projektu, osobiste, z wtyczek) mogą być łączone ze skillami fabryki — zasady pierwszeństwa
  w `core-skill-composition`; `build.py check` nie zgłasza dla nich błędów.
- Instalacja prywatna domyślnie wpisuje ścieżki do `.git/info/exclude`.

## [1.0.0] — 2026-09-28
- Pierwsza wersja instalowalna: `factory/install.py` (tryb prywatny i zespołowy), persony Ola, Marek, Kuba, Ewa, Ada,
  Jan, Tomasz, Filip, Kasia, Stefan i Maja, skille DDD, frontend, backend, QA, polszczyzna, warsztat Event Storming,
  dziennik projektu, hooki bezpieczeństwa i clean-room.
