# Szablony dokumentów A–C

Każdy dokument zaczyna się nagłówkiem: `title`, `created`, `type` (`domain-distillation` / `refactor-plan`), commit,
na którym analizowano kod. Na końcu podsumowanie 5–8 zdań: co zawiera artefakt i najważniejszy wniosek.

## A. `docs/project/02-domain/distillation.md`
```markdown
# Destylacja domeny — <produkt>, <data>, commit <sha>
**Ograniczenia:** <np. brak PRD — źródłem README i kod>

## Słownik
| Pojęcie | Definicja | Źródło (dokument) | W kodzie | Inne nazwy |
|---|---|---|---|---|
| Sesja generacji | partia propozycji z jednego tekstu, z momentem finalizacji | `docs/prd.md:88` | BRAK w kodzie (tylko `generation_id` w `flashcards`) | „batch” (UI), „generation” (baza) |

## Subdomeny
| Obszar | Typ | Uzasadnienie (cele produktu) |

## Kandydaci na agregaty
| Kandydat | Niezmiennik (cytat) | Status: egzekwowany / deklarowany / ignorowany | Dowód |

## Rozjazdy model ↔ kod
| Dokument mówi | Kod robi | Dowód |

## Ranking
| # | Kandydat | Wartość | Ryzyko | Uzasadnienie |
```

## B. `docs/project/02-domain/invariant-<nazwa>.md`
```markdown
# Niezmiennik: <reguła> — plan agregatu-strażnika
## Lista niezmienników i osie
| Reguła | Źródło | Rdzeniowość | Rozsmarowanie (pliki/warstwy) | Egzekwowanie |
## Diagnoza wybranego (wszystkie warstwy)
| Warstwa | Miejsce | Co robi z regułą | Problem (brak / niespójnie / tylko UI / połyka błąd) |
## Projekt
- Korzeń: `<Agregat>`; metody z warunkami wstępnymi (sygnatury + pseudokod)
- Błędy domenowe: `<NazwaBłędu>` → mapowanie na odpowiedź (np. 409)
- Repozytorium: `load(id)` / `save(agregat)`; transakcja: <zakres>
- Trasa API: parsuj → metoda → mapuj błąd
## Before / after (każde dzisiejsze miejsce reguły)
## Fazy (test-first) i przypadki testowe
| Operacja | Stan wejściowy | Oczekiwanie (sukces / nazwany błąd) |
```

## C. `docs/project/02-domain/acl-<pakiet>.md`
```markdown
# ACL dla <pakiet> — plan
## Zależności i sygnały przecieku
| Pakiet | Pliki, które go znają | Warstwy | Typy w sygnaturach/DTO | Klient/serwer |
## Wybór (osie: zasięg · koszt wymiany · deklarowana wymienialność)
## Projekt
- Obiekt wartości `<Nazwa>`: mapowanie z/do persystencji, konwersja z/do typu biblioteki
- Port `<Nazwa>` (język domeny), adapter w `<katalog>/`
## Dowód izolacji
| Plik | Zna pakiet dziś | Zna po refaktorze |
## Kryterium ukończenia
`rg -l "<pakiet>" src | rg -v '^<katalog-adaptera>/'` → pusto; reguła CI: <dependency-cruiser / ESLint / ArchUnit>
## Fazy
```
