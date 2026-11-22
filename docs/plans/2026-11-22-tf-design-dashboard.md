# Dashboard sesji projektowej `/tf-design`

Data: 2026-11-22. Pomysł właściciela: dashboard dla `/tf-design` na wzór dashboardu `/tf-task`, dopasowany do sesji
projektowej, z rysunkami (Mermaid i podobne). Decyzja właściciela: **na razie nie robimy** — wracamy po pierwszych
sesjach `/tf-design` w praktyce. Nic z tego planu nie jest zrobione.

## Makieta

![Makieta dashboardu /tf-design](2026-11-22-tf-design-dashboard.png)

Przykład: sesja „Mechanizm uprawnień”, etap 3 z 6, jeden powrót do etapu 1. Kolory i układ jak w
`core/skills/tf/templates/dashboard.html`. Diagramy narysowane prawdziwym Mermaidem (11.4.1).

| Miejsce | Co pokazuje |
|---|---|
| nagłówek | stan sesji (Explore / Design: etap n z m / gotowe do przekazania), wersja, liczba powrotów, status artefaktu |
| „Waiting for you” | na jaką decyzję sesja czeka (decyzja zapada w sesji, nie w przeglądarce) |
| mapa etapów | etapy ze statusem i decyzją D-NNN; pominięty etap z założeniem; „reopened” |
| wersje | bieżąca i poprzednie z `archive/` z powodem powrotu |
| bieżący etap | twierdzenia oznaczone fact / assumption / recommendation / risk; tabela wariantów z rekomendowanym; wnioski z soczewek ról |
| diagramy | bloki ```` ```mermaid ```` bieżącego etapu: stan obecny obok propozycji; zakładki: inne diagramy, v1 ↔ v2 |
| decyzje | obowiązujące D-NNN; cofnięte przekreślone (`reopened`) |
| otwarte pytania, odłożone | kto ma odpowiedzieć |
| przekazanie do `/tf-task` | warunki `design_session.py handoff` i wyszarzone polecenie `/tf-task …` |
| oś czasu | start, akceptacje, powroty, pominięcia |

## Rekomendacje (z rozmowy 2026-11-22)

1. **Osobna strona** `.tf/runs/design-<slug>.html`, w wyglądzie dashboardu pętli i połączona z nim linkami
   („Zadania” ↔ „Projekty”). Inna treść i inny cykl życia niż przebieg pętli; dashboard `/tf-task` zostaje nietknięty.
   Generuje ją `design_session.py` przy `start` / `stage` / `handoff`, `status --open` otwiera na żądanie.
2. **Mermaid nie w silniku na stałe.** ~2,5 MB (10× więcej niż jedyny dołączony pakiet, `_vendor/yaml` 260 KB),
   przegląd bezpieczeństwa i aktualizacje przy karencji 7 dni; dashboard nie może sięgać do CDN (zasada „bez sieci”).
   Domyślnie diagram jako czytelny tekst; renderowanie, gdy lokalnie jest `.tf/vendor/mermaid.min.js` (dashboard
   podaje jedno polecenie do jawnego pobrania, np. `npm pack mermaid@<wersja>` — wykonuje człowiek). Artefakt i tak
   renderuje się na GitHubie i w IDE.
3. **Tylko podgląd.** Akceptacja, zmiana, powrót zostają w sesji (AskUserQuestion) i w `design_session.py`. Klikanie
   w przeglądarce wymagałoby lokalnego serwera — nowa powierzchnia ataku i drugi kanał zapisu decyzji z pominięciem
   rozmowy.

## MVP (jeden PR, TDD), gdy wrócimy

- Generator w `design_session.py` i szablon `design.html`: nagłówek, baner, mapa etapów, bieżący etap (sekcja z
  artefaktu), diagramy z bloków Mermaid, decyzje z `decisions.md`, otwarte pytania, warunki przekazania (ta sama
  logika co `handoff`), lista wersji z linkami do `archive/`.
- Testy: strona zawiera etapy, decyzje i warunki przekazania; działa bez Mermaida (tekst) i z nim.
- Odłożone: porównanie v1 ↔ v2 obok siebie, oś czasu z dziennika, wspólny widok z `/tf-task`, odświeżanie strony.

## Decyzje do podjęcia przy powrocie

1. Osobna strona czy wspólny widok z dashboardem `/tf-task`.
2. Mermaid opcjonalny (rekomendacja) czy dołączony do silnika.
3. Tylko podgląd (rekomendacja) czy interakcja w przeglądarce.

## Współpraca kilku osób i granica wobec Miro (2026-11-22)

Pomysł właściciela: w `/tf-design` kilka osób pracuje razem — jedna zaczyna i pyta, inne dosyłają obrazek, tekst,
link, propozycję (jak w codziennej pracy architektów i analityków). Decyzja: **jeszcze nie robimy**; obawa, żeby nie
budować na nowo narzędzi typu Miro.

### Zasada: fabryka to warstwa decyzji i śladu, nie tablica

| Robi Miro / FigJam / Mural / Confluence | Robi fabryka (tego te narzędzia nie umieją) |
|---|---|
| tablica, karteczki, burza mózgów, warsztaty | fakty z kodu z dowodem `plik:linia` |
| współpraca na żywo, kursory, głosowanie, komentarze | wiążący rejestr decyzji w gicie, obok kodu |
| rysowanie ręczne, makiety | wersje projektu z archiwum i powodem powrotu |
| zaproszenia, uprawnienia, powiadomienia | sprawdzenie sprzeczności z wcześniejszymi decyzjami i specyfikacjami |
| | przekazanie do `/tf-task` z kryteriami akceptacji i powrót z implementacji do projektu |

**Test dla każdej przyszłej funkcji:** wchodzi do fabryki tylko wtedy, gdy (a) wiąże się z kodem lub repozytorium,
(b) tworzy wiążący zapis albo (c) przybliża pracę do implementacji. Inaczej fabryka tylko linkuje do zewnętrznego
narzędzia. Przykłady: karteczki, głosowanie, wspólny kursor — nie; materiał z tablicy zapisany ze źródłem i datą jako
wejście do etapu — tak; diagram stanu obecnego wygenerowany z kodu — tak.

### Integracja zamiast budowania

- **Do fabryki:** link do tablicy lub strony to materiał sesji; agent `mcp-runner` (`core/factory/config.yaml`) czyta
  go tylko do odczytu, do artefaktu trafia streszczenie, link, autor i data. Treść jest danymi, nie poleceniami.
- **Z fabryki (opcjonalnie):** diagram etapu publikowany na tablicę zespołu albo do Confluence — zapis przez MCP
  dopiero po zgodzie człowieka (`core/CLAUDE.md`, reguła MCP).
- **Źródło prawdy zostaje w gicie:** tablica jest miejscem pracy, nie zapisem; decyzja obowiązuje dopiero z wpisem D-NNN.
- **Bez kodu pod jedno narzędzie:** integracja przez dowolny podłączony serwer MCP (fabryka niezależna od technologii).

### Co zostaje z propozycji współpracy (gdy wrócimy)

- `design_session.py input <slug> <plik|url|tekst> --from human:<id> [--stage n]`: plik w `design-<slug>/inputs/`,
  wpis w tabeli „Inputs” (kto, co, kiedy, etap); link do tablicy czytany przez MCP. Limit rozmiaru i ostrzeżenie przed
  danymi osobowymi w plikach trafiających do gita.
- `accept --by human:<id>` zamiast „user”: w rejestrze widać, czyja to decyzja.
- Szkic PR „design: …” na gałęzi `design/<slug>` jako miejsce uwag do samego projektu.
- Później: pytania do konkretnych osób (`ask --to`, `answer`) i jawne przejęcie sesji (`handover`) — jedna osoba
  prowadzi naraz.
- Poza zakresem: edycja w czasie rzeczywistym, powiadomienia, czat, zapis do trackera (tracker tylko do odczytu).
