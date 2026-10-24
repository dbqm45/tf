# Szablon raportu rekonstrukcji (`docs/project/00-reconstruction/report.md`)

Sekcje w tej kolejności (sprawdza je `recon_check.py --final`). Każde wypunktowanie: dowód `plik:linia` albo
oznaczenie [założenie] / [niezweryfikowane] / [pytanie]. W „Pytaniach” i „Czego nie sprawdzono” dowód nie jest wymagany.

`--final` sprawdza też:
- **Stack** jako tabelę z wierszami Język, Framework, Dane, Build, Testy, CI, Konfiguracja. Wiersz bez dowodu ma
  oznaczenie, np. „CI: [niezweryfikowane] brak plików pipeline'u w repo”. Rozjazd wersji (CI kontra plik budowania,
  obraz kontra SDK) wpisujesz w wierszu i powtarzasz w Ryzykach.
- **CI**: gdy w repo są pliki pipeline'u (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` i podobne), wiersz CI
  wskazuje któryś z nich jako dowód. Sam „brak CI [niezweryfikowane]” wtedy nie przejdzie.
- **Moduły**: każdy moduł z kart `modules/*.json` ma wpis i aktualny `modules/<moduł>.md` z `recon_cards.py`. Sekcję
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
| Język | <język i wersja; rozjazdy, np. CI ≠ plik budowania> | `<plik budowania>:<linia>` |
| Framework | <framework i wersja, główne biblioteki> | `<plik>:<linia>` |
| Dane | <baza, ORM, migracje, wersje> | `<plik>:<linia>` |
| Build | <narzędzie i wersja, wrapper> | `<plik>:<linia>` |
| Testy | <framework, kontenery testowe, pokrycie (np. JaCoCo)> | `<plik>:<linia>` |
| CI | <system, wersje środowiska, kroki> | `<plik>:<linia>` |
| Konfiguracja | <profile, ustawienia ze skutkiem (np. ddl-auto), zmienne środowiska> | `<plik>:<linia>` |
| Wdrożenie | <obraz, manifesty; opcjonalnie> | `<plik>:<linia>` |

## Moduły
- <moduł>: <odpowiedzialność jednym zdaniem> — `<plik>:<linia>` · kluczowe: <wejścia, pojęcia, tabele> (szczegóły: modules/<moduł>.md)
  - <pakiet lub projekt poziom niżej>: <odpowiedzialność> — `<plik>:<linia>`

## Domeny
- <subdomena> (core | supporting | generic): <po co> — `<plik>:<linia>`; słownik: domain.md

## Wymagania
- <wymaganie językiem biznesu> — `<test lub kod>:<linia>` (pewność: test | kod | do potwierdzenia)

## Reguły
- <reguła biznesowa> — `<plik>:<linia>` "<cytat z linii>" (pewność)

## Standardy
- <obszar>: <reguła> — <udział>% (`standards/<obszar>.md`), wyjątki: <ile>

## Ryzyka
- <ryzyko> — `<plik>:<linia>` (hotspot, cykl, brak testów, sekret w konfiguracji…)

## Pytania
- [pytanie] <do kogo> — <pytanie>

## Czego nie sprawdzono
- <obszar> — dlaczego (DI, refleksja, kolejki, HTTP między usługami, konfiguracja zewnętrzna, poza zakresem)
```
