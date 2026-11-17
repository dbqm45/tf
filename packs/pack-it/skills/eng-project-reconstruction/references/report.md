# Szablon raportu rekonstrukcji (`docs/project/00-reconstruction/report.md`)

Sekcje w tej kolejności (sprawdza je `recon_check.py --final`). Każde wypunktowanie: dowód `plik:linia` albo
oznaczenie [założenie] / [niezweryfikowane] / [pytanie]. W „Questions” i „Not checked” dowód nie jest wymagany.

`--final` sprawdza też:
- **Stack** jako tabelę z wierszami Language, Framework, Data, Build, Tests, CI, Configuration. Wiersz bez dowodu ma
  oznaczenie, np. „CI: [niezweryfikowane] brak plików pipeline'u w repo”. Rozjazd wersji (CI kontra plik budowania,
  obraz kontra SDK) wpisujesz w wierszu i powtarzasz w Risks.
- **CI**: gdy w repo są pliki pipeline'u (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` i podobne), wiersz CI
  wskazuje któryś z nich jako dowód. Sam „brak CI [niezweryfikowane]” wtedy nie przejdzie.
- **Modules**: każdy moduł z kart `modules/*.json` ma wpis i aktualny `modules/<moduł>.md` z `recon_cards.py`. Sekcję
  wstawia `recon_cards.py modules/ --into report.md`: cel, dowód, kluczowe elementy (wejścia, pojęcia, tabele)
  i odnośnik. Duży moduł dzielą partie (karta na pakiet albo projekt), więc poziom niżej widać bez dopisywania.

```markdown
# <Nazwa projektu> — rekonstrukcja z kodu
Commit: <sha> · data: RRRR-MM-DD · zakres: <całość | katalogi> · koszt przebiegu: <USD, modele>

## TL;DR
5–7 zdań: co to za system, dla kogo, najważniejsze moduły, największe ryzyko, ile pytań do ludzi.

## Stack
| Obszar | Ustalenie (z wersją) | Dowód |
|---|---|---|
| Language | <język i wersja; rozjazdy, np. CI ≠ plik budowania> | `<plik budowania>:<linia>` |
| Framework | <framework i wersja, główne biblioteki> | `<plik>:<linia>` |
| Data | <baza, ORM, migracje, wersje> | `<plik>:<linia>` |
| Build | <narzędzie i wersja, wrapper> | `<plik>:<linia>` |
| Tests | <framework, kontenery testowe, pokrycie (np. JaCoCo)> | `<plik>:<linia>` |
| CI | <system, wersje środowiska, kroki> | `<plik>:<linia>` |
| Configuration | <profile, ustawienia ze skutkiem (np. ddl-auto), zmienne środowiska> | `<plik>:<linia>` |
| Wdrożenie | <obraz, manifesty; opcjonalnie> | `<plik>:<linia>` |

## Modules
- <moduł>: <odpowiedzialność jednym zdaniem> — `<plik>:<linia>` · key: <wejścia, pojęcia, tabele> (szczegóły: modules/<moduł>.md)
  - <pakiet lub projekt poziom niżej>: <odpowiedzialność> — `<plik>:<linia>`

## Domains
- <subdomena> (core | supporting | generic): <po co> — `<plik>:<linia>`; słownik: domain.md

## Requirements
- <wymaganie językiem biznesu> — `<test lub kod>:<linia>` (confidence: test | kod | do potwierdzenia)

## Rules
- <reguła biznesowa> — `<plik>:<linia>` "<cytat z linii>" (pewność)

## Standards
- <obszar>: <reguła> — <udział>% (`standards/<obszar>.md`), wyjątki: <ile>

## Risks
- <ryzyko> — `<plik>:<linia>` (hotspot, cykl, brak testów, sekret w konfiguracji…)

## Questions
- [pytanie] <do kogo> — <pytanie>

## Not checked
- <obszar> — dlaczego (DI, refleksja, kolejki, HTTP między usługami, konfiguracja zewnętrzna, poza zakresem)
```
