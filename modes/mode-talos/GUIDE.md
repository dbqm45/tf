# Talos — historyjka → PR na żądanie

Talos (`mode-talos`) to tryb fabryki, który bierze jedną historyjkę użytkownika i prowadzi ją do jednego PR: plan, testy, kod,
weryfikacja, commity i raport kosztu. Działa tylko wtedy, gdy go uruchomisz — model nigdy nie włącza go sam.
Instaluje się domyślnie; bez niego: `tf remove mode-talos`, z powrotem: `tf add mode-talos`.
Pierwszy raz z fabryką? Zacznij od sekcji „Zacznij tutaj” w `.tf/factory/PRZEWODNIK.md`.

## Do czego
- **Pasuje:** historyjka z kryteriami akceptacji, które da się sprawdzić testem; zmiana mieści się w kilku
  kawałkach (do 5) i w jednym PR; repozytorium ma testy i polecenia weryfikacji (CLAUDE.md).
- **Nie pasuje:** praca koncepcyjna (co budować, architektura od zera), decyzje produktowe w trakcie, dostęp do
  produkcji, historyjka bez kryteriów akceptacji. Wtedy pracujesz z personą, a Talos wróci, gdy historyjka będzie
  gotowa.

## Jak uruchomić
Dwa sposoby, ten sam przebieg (skill `talos-story-run`):

| Sposób | Polecenie | Kiedy |
|---|---|---|
| agent Talos | `claude --agent talos`, potem treść historyjki albo ścieżka do pliku | sesja tylko na automat |
| w dowolnej personie | `/talos-story-run <plik story albo treść> [--auto] [--budget USD]` | jednorazowo, w bieżącej sesji |

Opcje (w wiadomości do Talosa albo przy poleceniu):
- `--auto` — plan nie czeka na Twoją akceptację; bez tej opcji Talos pokazuje plan i czeka;
- `--budget <USD>` — twardy limit: po kawałku, który go przekroczy, Talos się zatrzymuje. Domyślnie budżetu nie ma,
  ale Talos zawsze wybiera najtańszy wystarczający model i najmniej pracy.

Przykład:
```
claude --agent talos
> Jako operator chcę zaimportować plik CDR (CSV) i zobaczyć sesje z błędem. --auto
```

## Co robi
1. **Start:** wymaga czystego drzewa roboczego, zakłada katalog przebiegu i gałąź `story/<slug>`.
2. **Przyjęcie historyjki:** sprawdza, kto, co i po co oraz kryteria akceptacji. Gdy ich brakuje, zadaje do 3 pytań
   (z `--auto` — zatrzymuje się z tymi pytaniami).
3. **Plan:** do 5 kawałków pionowych — każdy niesie wartość, sam przechodzi testy i jest osobnym commitem.
   Historyjka na więcej kawałków → propozycja podziału i STOP.
4. **Kawałek po kawałku:** test, który nie przechodzi → najmniejszy kod → weryfikacja (testy, lint, typy) → skan
   bezpieczeństwa (semgrep OWASP Top 10 na plikach kawałka, audyt zależności przy zmianie manifestu) → przegląd
   zakresu przez `scope-reviewer` w świeżym kontekście → commit. Najwyżej 2 próby naprawy, potem STOP z opisem
   blokady.
5. **KISS:** przypadki brzegowe, pomysły i ryzyka spoza kryteriów nie trafiają do kodu, tylko do `parked.md`
   i do sekcji „Odłożone do decyzji” w opisie PR.
6. **Fazy warunkowe:** dokumentacja tylko przy zmianie publicznego API, przegląd bezpieczeństwa tylko przy auth,
   sekretach, IaC lub CI, architekt tylko przy decyzji trudnej do odwrócenia.
7. **Koniec:** jeden PR (Talos go nie scala) i raport.

## Co dostajesz
Każda historyjka to **zadanie** z kluczem (`T-<data>-<slug>` albo numer z trackera: `start --key PROJ-123`) i dwoma
katalogami:

| Gdzie | Co | Git |
|---|---|---|
| `docs/project/changes/<KEY>/` | `ticket.md` (historyjka), `plan.md` (kawałki do odhaczenia — od niego wznawiasz przerwany przebieg), `task.json` (stan), `evidence/` (dowody weryfikacji kawałków), `report.md` (raport) | tak — jednym commitem `docs(task): record <KEY>` na końcu przebiegu |
| `.tf/runs/<KEY>/` | `run.json`, `parked.md` (sprawy odłożone do Twojej decyzji), wyniki skanów, pełne logi weryfikacji | nie |

Spis zadań: `docs/project/changes/INDEX.md`; stan jednego: `tf task status <KEY>`. Kawałek jest „zrobiony” dopiero
z dowodem: Talos uruchamia weryfikację przez `run_state.py verify`, a bez aktualnego dowodu skrypt nie odhaczy kawałka
i nie przepuści przebiegu do PR. Bramka jakości nie reaguje na zmiany w `docs/project/changes/`.

Przebiegi sprzed tej zmiany (`.tf/runs/talos/<data>-<slug>/`, wszystkie pliki w jednym katalogu) są dalej czytane
przez `status`, `finish` i dashboard — przez jedno wydanie MINOR; nowe tam nie powstają. Wyjątek: przebieg cięcia
z planu zmiany (`start --task TSK-n`, tryb pdi) na razie zostaje w starym układzie.

Raport (`python3 .claude/skills/talos-story-run/scripts/run_report.py finish <katalog>`): czas, tokeny (wejście, wyjście, odczyt i zapis cache),
koszt w USD, modele i agenci, kawałki zrobione / plan, liczba odłożonych spraw. Liczy go skrypt z transkryptów
sesji, nie model, więc nie zużywa tokenów. Koszt to szacunek z cennika API — przy subskrypcji równowartość, nie
faktura. W trakcie przebiegu jedna linia stanu:
`python3 .claude/skills/talos-story-run/scripts/run_report.py status <katalog>`.

Podgląd na żywo: `python3 .claude/skills/talos-story-run/scripts/run_state.py dashboard` buduje
`.tf/runs/talos/dashboard.html` (otwierasz plik w przeglądarce, odświeża się sam co 5 s). Kolumny to etapy przebiegu
(Przyjęcie, Plan, Kawałki, PR, Czeka na człowieka, Gotowe), karta pokazuje rundy bieżącego kawałka (R1, R2…) i etapy
pętli (test, kod, weryf, skan, zakres), a panel plików — `ticket.md`, `plan.md`, `parked.md`, wyniki skanów, STOP
i `report.md`. Stan zapisuje Talos poleceniami `run_state.py stage` i `run_state.py step`; koszt i czas liczy skrypt
z transkryptów (`dashboard` bez `--no-cost`). `run_report.py start` buduje dashboard sam i otwiera go w przeglądarce
(cięcie z kluczem, wołane przez fazę pdi, tylko go buduje). Wyłączysz to w `.claude/talos.json` (osobisty plik, aktualizacja
fabryki go nie rusza): `{"dashboard": false}` — wcale, `{"dashboard_open": false}` — buduje, ale nie otwiera;
domyślnie oba `true`. To samo robią zmienne `TALOS_DASHBOARD=0` i `TALOS_DASHBOARD_OPEN=0`.

Zgodność zmian z planem (`python3 .claude/skills/talos-story-run/scripts/plan_drift.py <katalog> --base main`):
pliki zmienione vs pliki kawałków, zmiany spoza planu, pokrycie diffu planem i testy w diffie — trafia do opisu PR.
Jeśli projekt ma rekonstrukcję z kodu (`docs/project/00-reconstruction/`), Talos przy przyjęciu historyjki czyta
spis standardów i słownik domeny.

## Bezpieczeństwo i karencja wersji
Po zielonych testach kawałka Talos uruchamia
`python3 .claude/skills/talos-story-run/scripts/security_scan.py scan --slice K<n> --attempt <k> --out <katalog>/security/K<n>`:
semgrep z regułami `p/owasp-top-ten` (i `.semgrep.yml` produktu, jeśli jest) tylko na zmienionych plikach, `npm audit`
albo `pip-audit` tylko przy zmianie manifestu lub lockfile'a (`package.json` bez zależności i bez lockfile'a —
audyt pominięty z adnotacją w raporcie; z zależnościami bez lockfile'a — błąd skanu); wynik każdej próby (SARIF,
`verdict.json`, `summary.md`) to osobny katalog `<katalog>/security/K<n>/proba-<k>/`, a
`<katalog>/security/K<n>/feedback.md` to ustalenia ostatniej próby. Raport przebiegu wymienia każdą próbę kawałka
(np. FAIL z ustaleniami, potem PASS). Ustalenie
blokujące (error albo warning z CWE z OWASP Top 10 — ta sama reguła co SEC-001 w ci_for_sdlc) to czerwona bramka:
druga próba dostaje ustalenia (reguła, plik:linia), po dwóch próbach STOP i brak commitu. Ustalenia poniżej progu
trafiają do sekcji „Bezpieczeństwo” raportu. Brak semgrep albo pip-audit to FAIL z poleceniem instalacji
(`pipx install semgrep`, `pipx install pip-audit`), nigdy cichy PASS.

Wymagania wobec produktu:
- **Jedno polecenie weryfikacji (N3):** skrypt w stylu `templates/verify.sh` (format, lint, typy, testy, skan),
  nazwany w pierwszej linii `CLAUDE.md` produktu; ten sam uruchamia Talos i CI (szablony w mode-pdi).
- **Karencja wersji 7 dni (N10):** `.npmrc` `min-release-age=7` (npm ≥ 11.10), `pnpm-workspace.yaml`
  `minimumReleaseAge: 10080` (minuty, pnpm ≥ 10.17), `.yarnrc.yml` `npmMinimalAgeGate`, `[tool.uv]
  exclude-newer = "7 days"`; lockfile w gicie. Sprawdza to `security_scan.py cooldown` na starcie przebiegu. Uwaga
  pnpm: Dependabot aktualizuje lockfile bez karencji, a `pnpm install --frozen-lockfile` w CI kończy się wtedy
  `ERR_PNPM_NO_MATURE_MATCHING_VERSION` (pnpm/pnpm#11203, #12450) — PR-y Dependabota z wersjami młodszymi niż
  7 dni czekają albo mają `cooldown` w `dependabot.yml`.
- **Sieć:** rejestr reguł semgrep pobiera się z `semgrep.dev` — w kontenerze z listą dozwolonych hostów dodaj go
  (Z8a); bez sieci podaj lokalne reguły przez `TALOS_SEMGREP_CONFIG=<plik.yml albo katalog>`.
- **Rejestr bez logowania:** `p/owasp-top-ten` pobiera się bez `semgrep login` (semgrep 1.183.0, sprawdzone
  2026-11-03: 560 reguł), ale zestaw jest węższy niż pełne reguły — nie ma w nim m.in. `tainted-sql-string`
  (Express) ani reguł dla `node:sqlite`. Wzorce, których rejestr nie łapie, dopisuje produkt w `.semgrep.yml`
  (skan dokłada go zawsze); szerszy zestaw w CI daje logowanie tokenem (`SEMGREP_APP_TOKEN`).

## Gdy Talos się zatrzyma
Blok STOP mówi, co blokuje (z dowodem), co jest już zrobione (commity), czego potrzeba od Ciebie i od którego
kawałka wznowić. Po decyzji poproś Talosa o wznowienie i podaj katalog przebiegu: pierwszy nieodhaczony kawałek
w `plan.md` to miejsce, od którego kontynuuje. Raport kosztu powstaje także po STOP.

Szczegóły przebiegu: `.claude/skills/talos-story-run/SKILL.md` (w źródłach fabryki:
`modes/mode-talos/skills/talos-story-run/SKILL.md`); mechanizm: `docs/insights.md` w repozytorium fabryki, sekcje
„Tryby” i „Talos”.
