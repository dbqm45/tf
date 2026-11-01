---
name: core-cost-control
description: Użyj przy doborze lub zmianie modelu i koszcie — porównanie wyników benchmarków, kaskada haiku→sonnet→opus, effort, cache, kompaktowanie, pomiar.
metadata:
  przeglad: "2027-10-09"
  katalog: "Użyj, gdy wybierasz model lub effort dla zadania albo wykonawcy, eskalujesz po nieudanej próbie, planujesz długą sesję, kompaktujesz kontekst albo analizujesz koszt i trafienia cache — rubryka trudności, kaskada modeli z parametrem model narzędzia Agent, profile kosztów, doradca (advisor), opusplan, reguły cache, kompaktowanie, raport kosztów. Nie do ograniczania halucynacji (core-grounding) ani wydajności samej aplikacji (skille z pack-it)."
  slowa: "ile kosztowała praca agentów, koszt w złotówkach, koszt w PLN, statystyki kosztów, drogo czy tanio, koszt, tokeny, tańszy model, drogi model, haiku, sonnet, opus, effort, eskalacja, cache, kompaktowanie, compact, limit, rachunek, oszczędność, profil kosztów, doradca, advisor, opusplan, serwery MCP drogie, dryf kontekstu, przekręca nazwy plików, nowy model, ranking modeli, benchmark, domyślny model, koszt agenta w CI, fork czy subagent, agent teams, wyjście testów i buildu, tysiące linii wyjścia, szum z terminala, hook filtrujący wyjście poleceń, sesje szybko się kompaktują, sesje są drogie, rachunek za agenta wzrósł, przejść na tańszy model"
---

# Koszt i dobór modelu — najtańszy model, który przejdzie weryfikację

Cel: każde zadanie robi najtańszy model, który da wynik przechodzący **obiektywną weryfikację** (testy, lint, build,
`grounding_check`, przegląd). Model nie ocenia sam siebie „na oko”. O tym, czy wystarczył, decyduje wynik
sprawdzenia. Dopiero gdy sprawdzenie zawiedzie, idziesz poziom wyżej.

## 0. Samemu czy delegować
Domyślnie zadanie robi główna sesja: zna już kod i rozmowę, a dalsza praca w niej czyta historię z cache.
Nowy wykonawca zaczyna od zera — czyta te same pliki jeszcze raz (zapis do cache 1,25× ceny wejścia) i dostaje
tylko streszczenie, więc gubi ustalenia. Anthropic: systemy wieloagentowe zużywają ok. 15× więcej tokenów niż czat,
a kod ma mniej części do zrobienia naprawdę równolegle niż research (anthropic.com/engineering, 13.06.2025).
Delegujesz tylko, gdy przekazanie się opłaca: dużo czytania i krótki wynik (`scout`, `researcher`), części naprawdę
niezależne (równolegle), świeże spojrzenie (przegląd bezpieczeństwa, testy clean-room, przegląd diffu), zmiana
mechaniczna z pełną specyfikacją i testem (`quick-fixer`), decyzja trudna do odwrócenia (analiza na mocniejszym
modelu, wykonanie wraca do sesji). Jednej spójnej zmiany nie dzielisz między wykonawców.
Fork, sesja z worktree, subagent czy agent teams (i limit zagnieżdżania): `references/rownoleglosc.md`.
Brief zaczynasz linią `Klasa: czytanie|rownolegle|przeglad|mechaniczna|decyzja|inne` — powód delegowania, który
potem da się zmierzyć (§7).

## 1. Ocena zadania przed delegowaniem
Odpowiedz na pięć pytań. Tabela routingu w prompcie persony daje tier wyjściowy, a odpowiedzi go przesuwają:

| Pytanie | Tak → | Nie → |
|---|---|---|
| Czy wynik sprawdzi polecenie (testy, lint, typy, build)? | tier niżej | tier wyżej albo przegląd |
| Czy zmianę łatwo cofnąć (git, brak danych produkcyjnych)? | tier niżej | tier wyżej |
| Czy zadanie wymaga **decyzji** (wybór podejścia, kompromis), a nie tylko wykonania? | tier wyżej | tier niżej |
| Czy dotyczy bezpieczeństwa, danych osobowych, pieniędzy, migracji danych, architektury? | deep albo przegląd deep | — |
| Czy obejmuje wiele domen lub >5 plików bez wzorca? | rozbij na kroki | — |

Typowo: mechaniczna zmiana z testem → `haiku`; funkcja w jednej domenie → `sonnet`; wybór architektury, przegląd
bezpieczeństwa, błąd bez oczywistej przyczyny po próbie → `opus`.

Opcjonalnie `python3 .claude/hooks/jev_client.py --tier "<opis zadania>"` (klucz TYPESAFE_API_KEY) zadaje te pytania
modelowi decyzyjnemu Jev w ~0,1 s za ułamek centa. Sugestię „NIEPEWNE” rozstrzygasz rubryką sam.

## 2. Kaskada modeli
- Narzędzie Agent przyjmuje parametr `model` (`haiku`, `sonnet`, `opus`). Nadpisuje on model z definicji agenta na to
  wywołanie (i na jego wznowienia).
- **Start:** najtańszy model, który ma realną szansę. **Eskalacja o jeden poziom**, gdy wykonawca zgłosi blokadę albo
  weryfikacja nie przechodzi po 2 próbach. Do nowego wywołania dołącz, co nie zadziałało — inaczej mocniejszy model
  powtórzy ten sam błąd.
- **Deeskalacja:** po decyzji podjętej na `opus` (architektura, plan) implementację zlecaj znów na `sonnet`, a
  mechaniczne kroki na `haiku`.
- **Sygnał od wykonawcy:** raport może kończyć się linią `Tier: za niski — …` albo `Tier: za wysoki — …`. Hook
  `log_usage` ją zapisuje, a `cost_report.py` sumuje i podpowiada zmianę tieru roli. Przy kolejnym podobnym zadaniu
  od razu wybierz właściwy model.
- Nie przełączaj modelu **głównej sesji** w środku zadania (`/model`). Każdy model ma osobny cache, więc następna
  tura przeczyta całą historię bez rabatu. Delegowanie do wykonawcy na innym modelu nie psuje cache sesji.

## 3. Główna sesja: model, profil, doradca
- **Profil kosztów** (`python3 factory/profile.py`) przestawia cały zespół naraz:
  - `oszczedny` — bez Opusa;
  - `zrownowazony` — domyślny;
  - `jakosc` — std z effort high i doradca Opus.

  Profil zmienia też ustawienia sesji: effort, próg kompaktowania i doradcę.
- **Doradca (advisor)** — tańszy model główny wzywa mocniejszy w kluczowych momentach: przed wyborem podejścia, przy
  powracającym błędzie, przed ogłoszeniem końca. **Sam ocenia, kiedy go potrzebuje.**
  - Typowe pary: Sonnet + doradca Opus, Haiku + doradca Opus (Haiku może pytać, ale nie może doradzać).
  - Koszt: każda konsultacja czyta całą rozmowę po cenie doradcy i bez cache. Opłaca się w długich, wieloetapowych
    zadaniach, a nie w krótkich.
  - Ograniczenia: tylko API Anthropic (nie Bedrock, Vertex, Foundry); funkcja eksperymentalna. Subagenci dziedziczą
    doradcę, więc w profilu `jakosc` także tani wykonawcy mogą go wzywać.
  - Włączenie: `/advisor opus`, wyłączenie: `/advisor off`. Przełączenie doradcy nie psuje cache.
- **`opusplan`** — Opus w trybie planowania, Sonnet przy wykonaniu. Każde przełączenie trybu planowania zmienia
  model, więc oznacza pełny odczyt bez cache. Stosuj, gdy planujesz raz, a potem długo wykonujesz.
- Model i effort wybierasz **na początku sesji**.

## 4. Effort (głębokość rozumowania)
Tokeny myślenia liczą się jak tokeny wyjścia, czyli najdroższe.
- `low` — szybkie wymiany, zmiana nazwy, szkic;
- `medium` — codzienna praca o jasnym zakresie (domyślny dla Sonnet 5.5 i Opus 5.5);
- `high` — błędy w istniejącym kodzie, przypadki brzegowe, weryfikacja;
- `xhigh`/`max` — trudne problemy do samodzielnego rozwiązania (np. szukanie podatności).

Effort agentów wynika z tieru (`factory/config.yaml`), a skill może ustawić własny polem `effort`. Na większości
modeli zmiana effortu w trakcie sesji też kasuje cache; wyjątek: Opus 5.5, Sonnet 5.5, Haiku 5.5 i Fable 5.1 przez
API Anthropic lub subskrypcję. Jedna trudna tura: `ultrathink` w treści polecenia zamiast zmiany effortu sesji;
`ultracode` to orkiestracja workflow wielu agentów, nie poziom effortu (`references/model-i-automatyzacja.md` §8).

## 5. Cache — co go psuje, a co nie
Cache działa automatycznie i dopasowuje **początek** zapytania. Odczyt z cache kosztuje 10% ceny wejścia, a na
Opus 5.5 i Sonnet 5.5 — 5%, na Fable 5.1 — 2,5% (platform.claude.com, prompt caching, stan 2026-10-17).

| Kasuje cache (następna tura drożej) | Nie kasuje |
|---|---|
| zmiana modelu (`/model`, `opusplan`, skill z polem `model`) | edycja plików, także CLAUDE.md (działa od `/clear`) |
| zmiana effortu (większość modeli) | wywołanie skilla, tryb uprawnień, styl odpowiedzi |
| dodanie lub usunięcie serwera MCP (gdy narzędzia ładują się od razu) | uruchomienie subagenta, `/rewind`, `/recap` |
| zablokowanie całego narzędzia regułą deny | włączenie lub wyłączenie doradcy |
| `/compact`, aktualizacja Claude Code, wiele obrazów | |

Praktyka:
- Przerwa dłuższa niż czas życia cache (5 min, w subskrypcji główna rozmowa 1 h) oznacza, że następna tura czyta
  wszystko od nowa. Po długiej przerwie wróć od punktu kontrolnego w nowej sesji, zamiast wznawiać długą historię.
- Subagenci mają cache 5-minutowy. Niezależne zlecenia uruchamiaj razem, a nie z długimi przerwami.
- Nieudaną ścieżkę porzucaj przez `/rewind`, a nie `/compact`: cofnięcie trafia w istniejący cache.
- Nie przełączaj serwerów MCP w środku zadania.

## 6. Kontekst i kompaktowanie
- Fabryka ustawia `autoCompactWindow: 200000`. Bez tego modele z oknem 1 mln kompaktują dopiero przy ~967 tys.
  tokenów. Wcześniej każda tura czyta coraz dłuższą historię, a jakość spada (core-grounding).
- `/compact <co zachować>` uruchamiaj na granicy zadań, a nie w środku. Wcześniej zapisz punkt kontrolny
  (core-project-record).
- Po kompaktowaniu treść każdego użytego skilla wraca, ale najwyżej ~5000 tokenów. Dlatego SKILL.md ma być krótki,
  a szczegóły trzymaj w `references/` (`build.py check` ostrzega).
- Zadanie niezwiązane z poprzednim zaczynasz od `/clear`.
- Eksploracja i długie wyjścia (testy, logi, dokumentacja) idą do subagenta. Do głównej sesji wraca tylko raport.
- **Szum z terminala:** najpierw reportery „tylko błędy” (`--reporter=dot`, `pytest -q`, `--silent`) i log do pliku
  czytany fragmentami; hook filtrujący każde polecenie to obcy kod z dostępem do wszystkiego (`skill_audit`, zgoda
  człowieka). Skutek mierzysz kosztem na udane zadanie, nie liczbą tokenów.
- **Serwery MCP kosztują w każdej turze:** każdy podłączony serwer dokłada definicje wszystkich swoich narzędzi do
  każdego zapytania. Podłączaj tylko serwery potrzebne w tym projekcie, wybieraj takie z małą liczbą uniwersalnych
  narzędzi (wzorzec „wyszukaj + wykonaj”), a gdy wiadomo, jakie polecenie uruchomić — CLI zamiast MCP.
- Szeroki skan repo (historia gita, graf zależności, inwentarz) zlecasz tańszemu modelowi, a ciężką pracę robi CLI
  poza kontekstem; mocny model dopiero do pogłębienia jednego przepływu. Pakowanie całego repo w jeden plik to doraźny
  podgląd obcego kodu, nie stała praktyka.
- **Dryf kontekstu — sygnały do świeżej sesji:** agent powtarza odrzucone poprawki, przekręca nazwy plików, „pamięta”
  decyzje, których nie było, miesza model danych z innej zmiany lub fazy. Nie każ „poprawić jeszcze raz”: zapisz
  punkt kontrolny, otwórz nową sesję, wczytaj plan i jego postęp, zacznij fazę od początku. Jakość spada z długością
  wejścia, zanim okno się zapełni — dlatego fazy z commitami i plan w pliku, a nie coraz dłuższa rozmowa.
- Między fazami planu proponujesz człowiekowi: kontynuuj w tej sesji / świeży kontekst (z gotowym poleceniem
  wznowienia od fazy N) / najpierw przegląd tej fazy.

## 7. Pomiar
**Diagnoza przed dźwignią:** zanim zmienisz model, ustal, czy problem dotyczy kontekstu (pliki czytane w całości
wiele razy, wejście:wyjście ~100:1, niskie trafienia cache), modelu (porażki klasy zadań mimo dobrego kontekstu) czy
pomiaru (tokeny szacowane ze znaków) — `references/model-i-automatyzacja.md` §6.

- **Pasek stanu** (`.claude/hooks/statusline.py`): model, effort, zapełnienie kontekstu, trafienia cache (z dopiskiem
  „zimny”, gdy cache wygasł), koszt sesji, limity. Nie zużywa tokenów modelu.
- `/usage` — trafienia cache sesji i prawdopodobna przyczyna ostatniego pudła.
- Raporty kosztów z logów (`factory/cost_report.py`, `factory/cost_stats.py`) — polecenia i opcje:
  `references/model-i-automatyzacja.md` §7; przyczyny kosztu etapu ocenia core-agent-retro.

## 8. Ocena nowego modelu (zanim zmienisz domyślny)
- **Wyników z różnych raportów nie porównujesz wprost.** Wynik w rankingu to zestaw zadań + metryka + protokół (harness stały
  czy dowolny, limit kroków); bez tych trzech liczba nic nie mówi,
  a ten sam model w innym harnessie wypada wyraźnie inaczej.
- Praca agentowa wymaga powtarzalności w każdej próbie (pass^k), nie „choć raz” (pass@1): 90% na krok to ok. 59%
  dla pięciu kroków z rzędu (0,9⁵).
- Porównujesz **koszt rozwiązanego zadania** (tokeny × iteracje + czas przeglądu), nie cenę tokena — tani model,
  który potrzebuje trzech rund poprawek, jest droższy.
- Rozstrzyga własny test: 3–5 prawdziwych zadań projektu z tą samą weryfikacją (testy, build), dla agentów w kodzie —
  zestaw ewaluacji (pack-it: eng-llm-features §8). Przegląd nowości w modelach co ok. 2 tygodnie, nie codziennie.
Szczegóły i polecenie dla modelu rozumującego: `references/model-i-automatyzacja.md` §1.

## 9. Agenci w automatyzacji (CI, harmonogram, własny agent)
- Uruchamiasz na zdarzenie, które ma znaczenie (PR, czerwony build, nowe zgłoszenie), nigdy „w kółko na wszelki
  wypadek” — koszt mnoży się przez liczbę zdarzeń.
- Twardy limit na przebieg: liczba tur **i** budżet w dolarach (`claude -p … --max-budget-usd`, w SDK opcja budżetu;
  nazwy: eng-llm-features z pack-it). Agent-oceniacz bez narzędzi, 1–2 tury.
- Model per rola: triaż i etykiety najtańszym; rozumowanie nad kodem średnim; drogi tylko dla ścieżek krytycznych.
- Koszt z wyniku każdego przebiegu do tabeli lub dashboardu: per PR, per poziom triażu, per tydzień.
- Kod firmy w automatyzacji → klucz API z sekretu, nie login subskrypcji dewelopera (inne warunki danych i rozliczenia).
Szczegóły: `references/model-i-automatyzacja.md` §2–3; kontrakt pracy bez nadzoru: core-async-delegation.

## Przykład
Eskalacja `sonnet` → `opus` po dwóch nieudanych poprawkach niestabilnego testu i powrót implementacji na `sonnet`:
`references/przyklady.md` §2; tam też pozostałe przykłady.

## Checklista
- [ ] tier wybrany rubryką (sprawdzalność, odwracalność, decyzja, ryzyko, zakres), a nie z przyzwyczajenia
- [ ] start od najtańszego sensownego modelu; eskalacja po blokadzie lub 2 nieudanych weryfikacjach, z opisem porażki
- [ ] po decyzji na opus implementacja wraca na sonnet/haiku
- [ ] model i effort sesji ustalone na początku; bez `/model` w środku zadania
- [ ] `/compact` na granicy zadań po punkcie kontrolnym; `/rewind` do porzucenia nieudanej ścieżki
- [ ] koszt sprawdzony w pasku stanu lub `cost_report.py`
- [ ] tylko potrzebne serwery MCP; przy sygnałach dryfu nowa sesja z punktu kontrolnego
- [ ] nowy model oceniony własnym testem i kosztem rozwiązanego zadania; agent w automatyzacji z limitem tur i budżetem

## Źródła
- Anthropic, dokumentacja Claude Code (stan na 2026-10-03):
  - „How Claude Code uses prompt caching”;
  - „Model configuration” (opusplan, effort, autoCompactWindow);
  - „Subagents” (pole `model`, parametr `model` narzędzia Agent, kolejność wyboru modelu);
  - „Skills” (pola `model`, `effort`, `context: fork`);
  - „Escalate hard decisions with the advisor tool”;
  - „Manage costs effectively”;
  - „Customize your status line”.
- Anthropic, cennik API (platform.claude.com, 2026-10-03): wejście/wyjście Haiku 4.5 $1/$5, Sonnet 5.5 $2/$10,
  Opus 5.5 $4/$20 za 1 mln tokenów; odczyt cache $0,10–0,20.

- Kurs 10xDevs, ed. 3 (2026): prework 3.5 (rankingi modeli), moduł 1 lekcja 5 (koszt MCP), moduł 2 lekcja 4 (dryf
  kontekstu), moduł 4 lekcje 1–2 (szeroki skan repo), moduł 5 lekcje 2–3 (agenci w automatyzacji) — materiał
  szkoleniowy (dostęp 2026-10-09).
- `claude --help`, Claude Code 2.1.296 (2026-10-10): `--max-budget-usd` działa tylko z `--print`.

Opisane własnymi słowami.
