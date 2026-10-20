---
name: core-async-delegation
description: Użyj, gdy agent ma pracować bez nadzoru (claude -p, /goal, sandbox, rutyna) — kontrakt, bramki, przegląd.
metadata:
  przeglad: 2027-10-09
  katalog: "Użyj, gdy oddajesz zadanie agentowi, który działa bez człowieka przy ekranie — zdalna kontrola lokalnej sesji z telefonu, sandbox w chmurze (zamknięty laptop), rutyna lub przebieg według harmonogramu, wykonanie zatwierdzonego planu przez claude -p albo /goal — kwalifikacja zadania, wybór trybu kontroli, kontrakt przed startem (cel, zakres, setup, sieć, MCP, sekrety, stop, budżet), polityka wykonania planu bez pytań (bramki w fazach, celowe zepsucie, najwyżej 2 próby naprawy, blok STOP, commit na zielono, raport), monitorowanie i przegląd po. Nie do pętli recenzji i uprawnień agenta (core-agent-security), faz projektu (core-delivery-lifecycle), punktu kontrolnego sesji (core-project-record) ani doboru modelu (core-cost-control)."
  slowa: "bez nadzoru, w tle, w nocy, zamknięty laptop, odejść od komputera, z telefonu, remote control, sandbox w chmurze, claude code on the web, codex cloud, rutyna, harmonogram, routine, claude -p, headless, /goal, delegacja, zlecić agentowi, agent sam wykona plan, praca asynchroniczna"
---

# Delegacja pracy agentowi bez nadzoru

Kontrola nie znika, tylko zmienia miejsce: **konfigurujesz przed startem, monitorujesz wybiórczo, oceniasz po
zakończeniu.** Zielony przebieg znaczy tylko „infrastruktura nie padła”, nie „zadanie zrobione”. Im mniej patrzysz
na przebieg na żywo, tym ciaśniej środowisko musi wymuszać zakres — izolacja plików i sieci jest warunkiem
autonomii, nie przeszkodą.

## 1. Czy to zadanie do oddania
Tak, gdy wszystkie są prawdziwe:
- warunek „gotowe” sprawdzi polecenie lub lista kontrolna (testy, plik, raport), nie gust;
- zakres plików da się nazwać (edytuj / tylko czytaj / nie dotykaj);
- nie wymaga decyzji produktowych na żywo ani dostępu do produkcji;
- sekrety da się ograniczyć do zera albo do krótkotrwałych, bez prawa zapisu;
- wynik jest odwracalny: gałąź lub szkic PR, nigdy merge ani wdrożenie.

Dobre: aktualizacja planu testów, porządki w dokumentacji, drobna poprawka setupu, wycinek backlogu z planem,
przegląd zaległych zgłoszeń. Złe: „napraw produkcję”, „zdecyduj, jak ma działać rabat”.

## 2. Tryb kontroli — pytanie „kiedy człowiek odzyskuje kontrolę?”
| Tryb | Gdzie działa agent | Co kontrolujesz | Pasuje do | Główne ryzyko |
|---|---|---|---|---|
| **zdalna kontrola lokalnej sesji** (Remote Control w Claude Code, SSH + `tmux`, relay typu Happy) | Twoja maszyna lub VPS | samą sesję, z innego urządzenia | krótka poprawka, diagnoza, dokończenie pracy | bezpieczeństwo maszyny po Twojej stronie; relay = dodatkowa strona zaufania |
| **sandbox w chmurze** (Claude Code on the web, Codex Cloud) | zarządzany kontener | setup, sieć, MCP, sekrety, zakres | ograniczone zadanie do PR przy zamkniętym laptopie | źle przygotowane środowisko, za szerokie uprawnienia |
| **rutyna / przebieg cykliczny** (harmonogram, zdarzenie, API) | chmura lub serwer | wyzwalacz, warunek stopu, budżet, kryteria sukcesu | raport, przegląd zaległości, kontrola po wydaniu | zielony bez wartości, koszt, duplikaty, zapętlenie |

Problem tylko z interfejsem (telefon, inna sieć) → lokalny agent + zdalna kontrola. Chcesz odciąć agenta od
swojego katalogu domowego, kluczy i sieci → sandbox albo osobny VPS. Funkcje tych produktów (plany kont, wersje,
limity, cache) zmieniają się szybko — przed wdrożeniem w zespole sprawdź dokumentację dostawcy.

## 3. Kontrakt przed startem
Każda linia to decyzja, którą i tak podejmiesz — lepiej przed startem niż po pierwszej porażce. Część trafia do
konfiguracji środowiska (setup, sieć, sekrety), reszta do polecenia:
1. **cel i warunek „gotowe”** — sprawdzalny;
2. **zakres** — pliki do edycji, pliki tylko do odczytu, czego nie robić (kod produkcyjny, merge, push na `main`);
3. **setup** — zależności instalowane skryptem startowym, nie „w trakcie”; narzędzia z obrazu bazowego wypisane jawnie;
4. **sieć** — allowlista hostów; często wyłączona po setupie, więc „doinstaluj pakiet w trakcie” się nie uda;
5. **MCP i konfiguracja** — tylko to, co środowisko widzi przy starcie (np. `.mcp.json` w repo); profil lokalny
   użytkownika jest w chmurze niewidoczny;
6. **sekrety** — żadnych produkcyjnych ani z prawem zapisu; minimalny zakres i czas życia;
7. **stop i budżet** — limit tur i kosztu (`claude -p … --max-budget-usd <kwota>`), czas;
8. **kryteria przeglądu** — z góry: diff tylko w zakresie, raport z założeniami i niepewnościami, brak prośby
   o szersze uprawnienia.

Szablon do wypełnienia, przykład i wariant „dry run”: `references/kontrakt-delegacji.md`.

## 4. Wykonanie planu bez człowieka
Gdy delegujesz zatwierdzony plan kroku (core-delivery-lifecycle, core-project-record), agent dostaje politykę
zamiast pytań:
- **Zakaz pytań do użytkownika.** Niejednoznaczność → wariant zachowawczy (mniej plików, mniejsza zmiana zachowania,
  najbliżej litery planu), zapisany w raporcie.
- **Przed startem** sprawdza, że każde polecenie weryfikacji z planu da się uruchomić; brak = STOP w tej fazie.
- **Rozjazd z planem:** drobny (przeniesiony plik, nowa nazwa) → dostosuj i zapisz `ADAPT: …`; strukturalny (brak
  zależności, inna architektura, brak wyniku poprzedniej fazy) → STOP. W wątpliwości — strukturalny.
- **Bramki fazy, od najtańszej:** polecenia z planu → pliki fazy dodane do indeksu po nazwie → **celowe zepsucie**
  dla nowych testów (pack-it: qa-spec-first-testing) → pełne testy, lint, typy → commit. Po każdej bramce linia
  `BRAMKA <nazwa>: PASS` albo `FAIL (<skrót>, próba k/2)` — oceniający `/goal` widzi tylko transkrypt.
- **Najwyżej 2 próby naprawy na bramkę;** trzecia porażka = STOP. Testu, asercji ani reguły lint nie osłabia.
- **Commit tylko na zielono** (core-conventional-commits), pliki po nazwie; brudne pliki spoza fazy wypisuje,
  nie dodaje; bez `--no-verify` i `--amend`; padający hook przed commitem = porażka bramki.
- Weryfikacji ręcznej nie odhacza — lista dla człowieka na końcu. Stan postępu tylko w planie (pierwszy
  nieodhaczony punkt = miejsce wznowienia).
- Na końcu **raport**: fazy z SHA, adaptacje, niepewności, lista weryfikacji ręcznej, propozycja przeglądu
  w świeżym kontekście.

Format bloku STOP, raportu i polecenie `/goal` do skopiowania: `references/polityka-wykonania.md`.

## 5. Rutyny i przebiegi cykliczne
- Kontrakt mocniejszy niż przy jednym przebiegu: **cel, warunek stopu, zakres** (repo, etykiety, katalogi),
  **limit kosztu** (iteracje, czas, budżet), **kryteria sukcesu** i **kryteria porażki** (kiedy zielony status
  techniczny nadal jest porażką — np. raport bez nowych pozycji, ten sam wniosek co wczoraj).
- Idempotencja: przebieg sprawdza, co już zrobił poprzedni (raport z dziś istnieje → aktualizuje, nie dubluje).
- Wyzwalacz to zdarzenie, które ma znaczenie, albo rozsądny rytm — nie „co 5 minut na wszelki wypadek”.
- Pętla, która sama iteruje do akceptacji recenzenta, nie trafia do harmonogramu (core-agent-security §5a).
- Typowe porażki są nudne: godziny prób pobrania z zablokowanego hosta, drugi podobny raport, łatanie objawu
  zamiast przyczyny, gałąź, której nikt nie umie scalić.

## 6. Monitorowanie
Telefon to panel kontrolny, nie miejsce na przegląd diffu. Sprawdzasz: czy przeszedł setup, czy blokada sieci,
MCP lub sekretu nie zatrzymała pracy, czy agent nie rozszerza zakresu. Decyzja: kontynuuj / doprecyzuj /
zatrzymaj / zostaw do przeglądu.

## 7. Przegląd po
Przy komputerze: diff, logi, testy i raport wobec kryteriów z kontraktu — nie wobec zielonego statusu. Zmiany
w zakresie i bramki z dowodem → przegląd w świeżym kontekście i decyzja człowieka o scaleniu. Na końcu jedno zdanie
do dziennika projektu: co musi się zmienić, żeby ten tryb był bezpieczny dla zespołu (core-project-record).

## Przykład
**Sytuacja:** „Po zmianie limitów subskrypcji chcę, żeby agent w sandboxie uzupełnił plan testów modułu płatności,
a ja zamknę laptopa.”

**Wynik (polecenie + konfiguracja):**
```text
/goal Gotowe, gdy docs/test-plans/payments.md ma scenariusze nowych limitów subskrypcji
(min. przekroczenie, równy limit, zmiana planu w trakcie okresu) i krótki raport luk.
Zakres: edytuj tylko docs/test-plans/payments.md; src/modules/payments/** tylko czytaj. Bez merge i push na main.
Setup: npm ci w skrypcie startowym. Sieć: wyłączona po setupie. MCP: tylko .mcp.json z repo.
Sekrety: brak. Stop: po raporcie albo po 20 turach; budżet ustalony w konfiguracji.
Przegląd: diff dotyczy tylko planu testów; raport wymienia założenia i niepewności; brak prośby o sekrety.
```
Tryb: sandbox (laptop zamknięty, zadanie bez sekretów). Rano: diff tylko w jednym pliku, raport z 2 niepewnościami
→ przegląd i PR. Wniosek do dziennika: „do sandboxa potrzebny jest dostęp tylko do odczytu do specyfikacji limitów”.

Więcej: `references/kontrakt-delegacji.md` (szablon, dry run), `references/polityka-wykonania.md` (STOP, raport).

## Checklista
- [ ] zadanie przechodzi kwalifikację z §1 (sprawdzalne, nazwany zakres, bez produkcji i sekretów, odwracalne)
- [ ] tryb wybrany pytaniem „kiedy odzyskuję kontrolę”
- [ ] kontrakt: cel, zakres, setup, sieć, MCP, sekrety, stop, budżet, kryteria przeglądu
- [ ] przy planie: zakaz pytań, wariant zachowawczy, bramki z liniami werdyktu, ≤2 próby, STOP, commit na zielono
- [ ] rutyna: kryteria porażki mimo zielonego statusu, idempotencja, limit kosztu
- [ ] przegląd po wobec kontraktu; wniosek zapisany w dzienniku

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 5, lekcja 5 (praca asynchroniczna i zdalna) oraz skill kursu do autonomicznego
  wykonania planu z lekcji 5 — materiał szkoleniowy (dostęp 2026-10-09).
- `claude --help`, Claude Code 2.1.296 (sprawdzone 2026-10-10): `--max-budget-usd` (tylko z `--print`),
  `--allowedTools`, `--permission-mode` (`acceptEdits`, `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`),
  `--remote-control`, `--json-schema`. Opcja `--max-turns` nie jest wypisana w pomocy [niezweryfikowane].
- Anthropic: „Claude Code on the web”, „Remote Control”, „Routines”; OpenAI: „Codex Cloud environments” — wg kursu,
  nieotwierane bezpośrednio [niezweryfikowane szczegóły: plany kont, wersje minimalne, limity, cache].

Opisane własnymi słowami.
