# `context: fork` dla skilla, który dużo czyta — 2026-11-16

Pytanie: czy skill uruchamiany w osobnym podagencie (`context: fork`) zmniejsza kontekst głównej sesji i koszt bez
utraty jakości. Reguła w `core-skill-authoring` zalecała fork dla takich skilli, ale żaden skill go nie używał.

Zadanie: mapa kodu `core/factory` (36 plików Pythona, historia gita repozytorium fabryki) skillem
`eng-codebase-mapping`, zapis do `docs/mapa-core-factory.md`, potem w tej samej sesji krótkie pytanie („który plik
zmienić, żeby dodać polecenie `tf foo`”). Sonnet, `claude -p` z `--resume` dla drugiej tury, `acceptEdits`, świeży
klon i instalacja `pack-it` na każdy przebieg, jeden przebieg na wariant. Skrypt pomiaru był w katalogu roboczym sesji
i nie trafił do repozytorium. Koszt: 4,05 USD.

## Wyniki

| Wariant | Największy kontekst głównej sesji (tura 1 → 2) | Koszt obu tur | Mapa | Odpowiedź na pytanie |
|---|---|---|---|---|
| skill w rozmowie (dziś) | 104,7 tys. → 107,2 tys. tokenów | 1,09 USD | 139 linii | poprawna (`tf.py`) |
| fork, sam `context: fork` | 108,0 tys. → 109,6 tys. | 1,52 USD | 163 linie | poprawna |
| fork z zadaniem w `$ARGUMENTS` i `background: false` | 66,0 tys. → 72,1 tys. | 1,45 USD | 133 linie | poprawna |

Mapy we wszystkich wariantach wskazują punkt wejścia `tf.py`, centralny `build.py` i opisują cykle importów.

## Co się stało w wariancie z samym `context: fork`
Model wywołał skill bez argumentów (`{"skill": "eng-codebase-mapping"}`). Podagent nie widzi rozmowy, więc dostał
samą procedurę bez zadania i zwrócił tylko „completed”. Główna sesja zrobiła mapę sama: forka zapłacono na darmo,
a kontekst był taki jak bez niego. Dokumentacja Claude Code (code.claude.com, „Skills”, odczyt 2026-11-16): forked
skill dostaje treść SKILL.md jako polecenie, nie widzi historii rozmowy i domyślnie działa w tle (`background: true`).

W trzecim wariancie na górze treści było `**Zadanie:** $ARGUMENTS` i reguła „puste zadanie → odpowiedz BRAK ZADANIA”.
Model znów wywołał skill bez argumentów, dostał „BRAK ZADANIA” i od razu ponowił wywołanie z zakresem, pytaniem
i plikiem wyniku.

## Wnioski
- **Fork zmniejsza kontekst głównej sesji o ok. 37%** (66 wobec 105 tys. tokenów), przy tej samej jakości mapy
  i odpowiedzi na pytanie, które wymaga wiedzy z mapy.
- **Fork nie oszczędza pieniędzy:** +33% (1,45 wobec 1,09 USD). Podagent wczytuje skill i pliki od zera, a nieudane
  pierwsze wywołanie dokłada turę. Mniejszy kontekst w kolejnych turach jest czytany z cache, więc zwraca się
  powoli: odczyt cache Sonneta ok. 0,30 USD za mln tokenów [założenie] (cennika nie sprawdzałem w tej sesji),
  więc 35 tys. tokenów mniej to ok. 0,01 USD na turę [założenie], czyli kilkadziesiąt tur do zwrotu różnicy.
- **Decyzja:** `eng-codebase-mapping` zostaje bez forka. Fork ma sens, gdy po skillu sesja trwa długo albo jest blisko
  limitu kontekstu — dla miejsca w kontekście i mniejszego ryzyka kompaktowania, nie dla kosztu. Reguła
  w `core-skill-authoring` opisuje teraz warunki (`background: false`, `$ARGUMENTS` z regułą pustego zadania,
  `argument-hint`, krótki wynik, brak pytań do człowieka w trakcie).
- **Ograniczenia:** jeden przebieg na wariant, jedno zadanie, jeden model. Nie sprawdzono, czy forked skill działa,
  gdy wywoła go podagent (wykonawca persony) — dokumentacja tego nie opisuje, a fabryka ustawia limit zagnieżdżenia 2.
