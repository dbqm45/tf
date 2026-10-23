# Szablon raportu rekonstrukcji (`docs/project/00-reconstruction/report.md`)

Sekcje w tej kolejności (sprawdza je `recon_check.py --final`). Każde wypunktowanie: dowód `plik:linia` albo
oznaczenie [założenie] / [niezweryfikowane] / [pytanie]. W „Pytaniach” i „Czego nie sprawdzono” dowód nie jest wymagany.

```markdown
# <Nazwa projektu> — rekonstrukcja z kodu
Commit: <sha> · data: RRRR-MM-DD · zakres: <całość | katalogi> · koszt przebiegu: <USD, modele>

## TL;DR
5–7 zdań: co to za system, dla kogo, najważniejsze moduły, największe ryzyko, ile pytań do ludzi.

## Stack
- <język/framework wersja> — `<plik budowania>:<linia>`

## Moduły
- <moduł>: <odpowiedzialność jednym zdaniem> — `<plik>:<linia>` (karta: modules/<moduł>.json)

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
