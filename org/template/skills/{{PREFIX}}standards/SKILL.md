---
name: {{PREFIX}}standards
description: Użyj przy ustaleniach firmy {{TITLE}} — kto zatwierdza, progi, zakazy i wyjątki obowiązujące w {{TITLE}}.
metadata:
  review: "{{REVIEW}}"
  catalog: "Użyj, gdy odpowiedź zależy od ustaleń {{TITLE}}, a nie od ogólnej praktyki — kto w {{TITLE}} zatwierdza zmianę, progi i zakazy, wyjątki, okna wdrożeń, gdzie {{TITLE}} trzyma decyzje. Nie do ogólnych praktyk (skille fabryki)."
  keywords: "TODO: słowa, którymi ludzie w firmie opisują te sprawy, np. nazwy systemów, zespołów, procesów"
---

# Standardy {{TITLE}}

Ten plik to spis. Ustalenia każdego obszaru są w osobnym pliku: **wczytaj tylko plik obszaru, którego dotyczy
zadanie** (zmiana w samym wyglądzie strony → tylko `ui.md`; nowy endpoint → `api.md`, a gdy zmienia schemat — też
`data.md`). Ustalenia sprawdzalne wzorcem (zakazany import, wymagany nagłówek) są w `rules.yaml` modułu
`{{COMPANY}}-standards` i sprawdza je `tf analyze` — w tych plikach ich nie powtarzasz.

## Wspólne dla każdej zmiany
- TODO: najwyżej kilka ustaleń, które obowiązują zawsze (np. numer zgłoszenia w opisie PR, kto zatwierdza).

## Obszary
| Obszar | Kiedy czytać | Plik |
|---|---|---|
| UI | wygląd, układ, komponenty, teksty i dostępność ekranów | `references/ui.md` |
| API | endpointy, kontrakty, błędy, wersje, autoryzacja wywołań | `references/api.md` |
| Dane | schemat bazy, migracje, dane osobowe, retencja | `references/data.md` |
| Wydania | wdrożenia, okna, zatwierdzenie wydania, wycofanie | `references/releases.md` |

TODO: obszar, którego firma nie ma, usuń razem z plikiem; nowy obszar to nowy wiersz i plik w `references/`.
Osobny skill zamiast pliku tylko dla dużego obszaru, o który ludzie pytają innymi słowami — kilka podobnych skilli
konkuruje o to samo pytanie.

## Gdzie szukać
- TODO: gdzie są decyzje i dokumentacja (np. przestrzeń w Confluence) — ścieżka albo nazwa, bez haseł i tokenów.
  Confluence nie jest czytany automatycznie; treść, która ma działać, przenieś do plików obszarów.

## Przykład
TODO: jedna prawdziwa sytuacja z firmy i poprawny wynik, np. „PR dodaje kolumnę w tabeli zamówień → `data.md`:
migracja wsteczna zgodna, zatwierdzenie zespołu danych”.

## Źródła
- TODO: dokument firmowy, z którego pochodzą ustalenia, i data sprawdzenia (RRRR-MM-DD).
