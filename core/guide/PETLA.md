# Pętla fabryki — zadanie → PR na żądanie

Polecenie `/tf` (albo agent `tf`) bierze jedno zadanie i prowadzi je do jednego PR: specyfikacja, plan, testy, kod,
weryfikacja z dowodami, commity i raport kosztu. Uruchamiasz ją poleceniem `/tf …` albo zwykłym zdaniem, którym
zlecasz zadanie („zrealizuj EBO-1236”, „dodaj eksport sesji do CSV”); przy pytaniu albo drobnej poprawce fabryka
pętli nie włącza, a gdy nie jest pewna — pyta. Jest częścią rdzenia fabryki, więc działa w każdej instalacji.
Pierwszy raz z fabryką? Zacznij od sekcji „Zacznij tutaj” w `.tf/factory/PRZEWODNIK.md`.

## Do czego
- **Pasuje:** historyjka z kryteriami akceptacji, które da się sprawdzić testem; zmiana mieści się w kilku
  kawałkach (do 5) i w jednym PR; repozytorium ma testy i polecenia weryfikacji (CLAUDE.md).
- **Nie pasuje:** praca koncepcyjna (co budować, architektura od zera), decyzje produktowe w trakcie, dostęp do
  produkcji, historyjka bez kryteriów akceptacji. Wtedy pracujesz z personą, a pętla wróci, gdy historyjka będzie
  gotowa.

## Jak uruchomić
Dwa sposoby, ten sam przebieg (skill `tf`):

| Sposób | Polecenie | Kiedy |
|---|---|---|
| agent `tf` | `claude --agent tf`, potem zadanie (jak niżej) | sesja tylko na automat |
| w dowolnej personie | `/tf <zadanie> [--auto] [--budget USD]` albo zwykłe zdanie | jednorazowo, w bieżącej sesji |

**Co możesz podać jako zadanie** — fabryka sama rozpoznaje, co to jest; nazwy narzędzia nie wpisujesz:

| Podajesz | Przykład | Co się dzieje |
|---|---|---|
| numer zgłoszenia | `/tf EBO-1236` | fabryka czyta zgłoszenie z trackera podłączonego w sesji (tylko odczyt); bez połączenia prosi o wklejenie treści |
| adres zgłoszenia | `/tf https://firma.atlassian.net/browse/EBO-1236` | tracker i numer bierze z adresu |
| klucz cięcia z planu zmiany | `/tf TSK-57` | zadanie cięcia `CHG-12-TSK-57` (tryb pdi) |
| treść albo plik | `/tf Jako operator chcę…`, `/tf docs/story.md` | zadanie z kluczem `T-<data>-<nazwa>` |
| klucz istniejącego zadania | `/tf EBO-1236` po przerwie | wznowienie od pierwszego niezrobionego kawałka |
| nic | `/tf` | lista zadań w toku i pytanie, co dalej |

- **Tracker (Jira, Linear, GitHub…):** fabryka korzysta z połączenia, które sam dodałeś do Claude Code (serwer MCP);
  niczego nie instaluje i niczego w trackerze nie zmienia. Gdy podłączonych jest kilka, pyta raz, z którego pochodzą
  zgłoszenia, i zapisuje odpowiedź w `.tf/config/operations.json` (podgląd i zmiana: `python3
  .claude/skills/tf/scripts/intake.py tracker`). Bez połączenia wystarczy wkleić treść zgłoszenia.
- **Skąd pochodzi treść:** `ticket.md` zadania zaczyna się od linii `Źródło: … · pobrano: <data>`. Treść zgłoszenia
  to dla fabryki dane, nie polecenia — polecenie znalezione w zgłoszeniu zobaczysz jako uwagę, nie jako wykonaną akcję.
- **Wymuszenie sposobu pracy:** `/tf zadanie …`, `/tf pytanie …` (tylko odpowiedź), `/tf szybko …` (drobna zmiana
  od razu, bez zakładania zadania).

Opcje (w wiadomości do agenta albo przy poleceniu):
- bez opcji (tryb zwykły) — fabryka pokazuje specyfikację i plan i czeka na Twoją zgodę; zgodę zapisuje i dopiero
  wtedy zaczyna kod;
- `--plan` — tylko specyfikacja i plan, bez zmian w kodzie; realizację uruchamiasz później poleceniem `/tf <KLUCZ>`;
- `--auto` — plan nie czeka na Twoją zgodę (poza zadaniami o wadze pełnej);
- `--budget <USD>` — twardy limit: po kawałku, który go przekroczy, pętla się zatrzymuje. Domyślnie budżetu nie ma,
  ale fabryka zawsze wybiera najtańszy wystarczający model i najmniej pracy.

Przykład:
```
claude --agent tf
> Jako operator chcę zaimportować plik CDR (CSV) i zobaczyć sesje z błędem. --auto
```

## Waga zadania
Fabryka sama ocenia, ile ostrożności potrzebuje zadanie, i mówi Ci to jednym zdaniem przy starcie:

| Waga | Kiedy | Co to zmienia |
|---|---|---|
| lekka | literówka, nazwa, komentarz, dokumentacja — bez kryteriów akceptacji, jeden kawałek | bez specyfikacji i flagi; test, dowód i przegląd zakresu zostają |
| zwykła | wszystko inne | pełny przebieg opisany niżej |
| pełna | logowanie, hasła, uprawnienia, płatności, migracje bazy, dane osobowe, sekrety, wdrożenie — w treści zadania albo w plikach planu | plan zatwierdzasz Ty, zanim powstanie kod; z `--auto` fabryka zatrzyma się i poczeka na Twoją zgodę; przegląd bezpieczeństwa jest obowiązkowy |

- Wagę liczy skrypt z treści zadania i ze ścieżek planu, nie model. Gdy plan dotknie np. migracji, waga sama rośnie.
- Podnieść wagę może każdy (także fabryka). **Obniżyć możesz tylko Ty**, z powodem:
  `tf task weight <KLUCZ> --set zwykla --by human:<Twój identyfikator> --reason "…"`. Po Twojej decyzji fabryka
  wagi już nie zmienia.
- Podgląd wagi z powodem: `tf task weight <KLUCZ>`.

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
7. **Koniec:** jeden PR (fabryka go nie scala) i raport.

## Kiedy fabryka się zatrzymuje
Zatrzymanie (STOP) ma zawsze jeden z jedenastu powodów — skrypt nie przyjmie innego — i mówi, czego potrzeba od Ciebie:
brak informacji (`pytanie`), zadanie do podziału (`podzial`), brak treści albo dostępu do zgłoszenia (`zrodlo`), plan
czeka na zgodę (`zgoda-na-plan`), testy czerwone po dwóch próbach (`testy`), skan bezpieczeństwa (`skan`),
przekroczony budżet (`budzet`), nieprzygotowane repozytorium (`srodowisko`), decyzja o zależności (`zaleznosc`),
zmiana kontraktu albo decyzja biznesowa (`kontrakt`), operacja zastrzeżona dla Ciebie (`uprawnienia`).

Każde zatrzymanie dostajesz w tym samym kształcie: **co się stało**, **czego potrzeba**, **jedno pytanie** z 2–3
opcjami (przy każdej skutek i jedna rekomendacja) oraz co fabryka zrobi po Twojej odpowiedzi. To samo widać na
podglądzie w kolumnie „Czeka na człowieka”. Treść komunikatów jest w `.claude/skills/tf/templates/stop_messages.json`.

## Co dostajesz
Każda historyjka to **zadanie** z kluczem (`T-<data>-<slug>` albo numer z trackera: `start --key PROJ-123`) i dwoma
katalogami:

| Gdzie | Co | Git |
|---|---|---|
| `docs/project/changes/<KEY>/` | `ticket.md` (historyjka), `spec.md` (kryteria AC-n w formie Zakładając / Gdy / Wtedy, co zostaje bez zmian, co poza zakresem, otwarte pytania — sprawdza ją skrypt; z błędami nie ma planu; plik powstaje dopiero, gdy pętla zaczyna specyfikację), `plan.md` (kawałki do odhaczenia — od niego wznawiasz przerwany przebieg), `task.json` (stan), `evidence/` (dowody weryfikacji kawałków), `report.md` (raport) | tak — jednym commitem `docs(task): record <KEY>` na końcu przebiegu |
| `.tf/runs/<KEY>/` | `run.json`, `parked.md` (sprawy odłożone do Twojej decyzji), wyniki skanów, pełne logi weryfikacji | nie |

Spis zadań: `docs/project/changes/INDEX.md`; stan jednego: `tf task status <KEY>`. Kawałek jest „zrobiony” dopiero
z dowodem: pętla uruchamia weryfikację przez `run_state.py verify`, a bez aktualnego dowodu skrypt nie odhaczy kawałka
i nie przepuści przebiegu do PR. Bramka jakości nie reaguje na zmiany w `docs/project/changes/`.

Cięcie z planu zmiany (`/tf TSK-57`, tryb pdi) to takie samo zadanie, z kluczem złożonym ze zmiany i cięcia:
`docs/project/changes/CHG-12-TSK-57/` i `.tf/runs/CHG-12-TSK-57/`. Różnice: treść zadania pochodzi z wiersza cięcia
i zamiaru zmiany, flaga — z planu wydania, raport trafia też do `docs/project/changes/CHG-12/runs/TSK-57.md` (stamtąd
pdi bierze opis PR), a w spisie `INDEX.md` zadań cięć nie ma — ich spisem jest plan zmiany (`tf status` je pokazuje).

Raport (`python3 .claude/skills/tf/scripts/run_report.py finish <katalog>`): czas, tokeny (wejście, wyjście, odczyt i zapis cache),
koszt w USD, modele i agenci, kawałki zrobione / plan, liczba odłożonych spraw. Liczy go skrypt z transkryptów
sesji, nie model, więc nie zużywa tokenów. Koszt to szacunek z cennika API — przy subskrypcji równowartość, nie
faktura. W trakcie przebiegu jedna linia stanu:
`python3 .claude/skills/tf/scripts/run_report.py status <katalog>`.

Podgląd na żywo: `python3 .claude/skills/tf/scripts/run_state.py dashboard` buduje
`.tf/runs/dashboard.html` (otwierasz plik w przeglądarce, odświeża się sam co 5 s). Kolumny to etapy przebiegu
(Przyjęcie, Plan, Kawałki, PR, Czeka na człowieka, Gotowe), karta pokazuje rundy bieżącego kawałka (R1, R2…) i etapy
pętli (test, kod, weryf, skan, zakres) oraz pasek kawałków K1, K2… — fioletowy kawałek był odhaczony, ale nie ma
aktualnego dowodu (plik zmienił się po weryfikacji). Karta pokazuje też etap zadania, a zadanie bez przebiegu
(założone samym `tf task`, świeży klon) ma własną kartę. Panel plików dzieli pliki na katalog zadania (git), katalog
roboczy, dowody, wyniki skanów, STOP i `report.md`. To samo tekstem: `tf status`. Stan zapisuje pętla poleceniami `run_state.py stage` i `run_state.py step`; koszt i czas liczy skrypt
z transkryptów (`dashboard` bez `--no-cost`). `run_report.py start` buduje dashboard sam i otwiera go w przeglądarce
(cięcie z kluczem, wołane przez fazę pdi, tylko go buduje). Wyłączysz to w `.claude/tf.json` (osobisty plik, aktualizacja
fabryki go nie rusza): `{"dashboard": false}` — wcale, `{"dashboard_open": false}` — buduje, ale nie otwiera;
domyślnie oba `true`. To samo robią zmienne `TF_DASHBOARD=0` i `TF_DASHBOARD_OPEN=0`.

Zgodność zmian z planem (`python3 .claude/skills/tf/scripts/plan_drift.py <katalog> --base main`):
pliki zmienione vs pliki kawałków, zmiany spoza planu, pokrycie diffu planem i testy w diffie — trafia do opisu PR.
Jeśli projekt ma rekonstrukcję z kodu (`docs/project/00-reconstruction/`), pętla przy przyjęciu historyjki czyta
spis standardów i słownik domeny.

## Bezpieczeństwo i karencja wersji
Po zielonych testach kawałka pętla uruchamia
`python3 .claude/skills/tf/scripts/security_scan.py scan --slice K<n> --attempt <k> --out <katalog>/security/K<n>`:
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
  nazwany w pierwszej linii `CLAUDE.md` produktu; ten sam uruchamia pętla i CI (szablony w mode-pdi).
- **Karencja wersji 7 dni (N10):** `.npmrc` `min-release-age=7` (npm ≥ 11.10), `pnpm-workspace.yaml`
  `minimumReleaseAge: 10080` (minuty, pnpm ≥ 10.17), `.yarnrc.yml` `npmMinimalAgeGate`, `[tool.uv]
  exclude-newer = "7 days"`; lockfile w gicie. Sprawdza to `security_scan.py cooldown` na starcie przebiegu. Uwaga
  pnpm: Dependabot aktualizuje lockfile bez karencji, a `pnpm install --frozen-lockfile` w CI kończy się wtedy
  `ERR_PNPM_NO_MATURE_MATCHING_VERSION` (pnpm/pnpm#11203, #12450) — PR-y Dependabota z wersjami młodszymi niż
  7 dni czekają albo mają `cooldown` w `dependabot.yml`.
- **Sieć:** rejestr reguł semgrep pobiera się z `semgrep.dev` — w kontenerze z listą dozwolonych hostów dodaj go
  (Z8a); bez sieci podaj lokalne reguły przez `TF_SEMGREP_CONFIG=<plik.yml albo katalog>`.
- **Rejestr bez logowania:** `p/owasp-top-ten` pobiera się bez `semgrep login` (semgrep 1.183.0, sprawdzone
  2026-11-03: 560 reguł), ale zestaw jest węższy niż pełne reguły — nie ma w nim m.in. `tainted-sql-string`
  (Express) ani reguł dla `node:sqlite`. Wzorce, których rejestr nie łapie, dopisuje produkt w `.semgrep.yml`
  (skan dokłada go zawsze); szerszy zestaw w CI daje logowanie tokenem (`SEMGREP_APP_TOKEN`).

## Gdy pętla się zatrzyma
Blok STOP mówi, co blokuje (z dowodem), co jest już zrobione (commity), czego potrzeba od Ciebie i od którego
kawałka wznowić. Po decyzji poproś o wznowienie i podaj katalog przebiegu: pierwszy nieodhaczony kawałek
w `plan.md` to miejsce, od którego kontynuuje. Raport kosztu powstaje także po STOP.

Szczegóły przebiegu: `.claude/skills/tf/SKILL.md` (w źródłach fabryki:
`core/skills/tf/SKILL.md`); mechanizm: `docs/insights.md` w repozytorium fabryki, sekcje
„Tryby” i „Talos” (tak nazywała się pętla do wersji 9.33).
