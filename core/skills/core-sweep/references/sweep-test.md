# Jak przetestować sweep w projekcie

Instrukcja dla człowieka, który chce sprawdzić skill `core-sweep` w swoim projekcie (`PROJECT`) przed szerszym użyciem.
Na Windows zamiast `python3` użyj `py`.

## 0. Gałąź testowa i aktualna fabryka
```
git switch -c test/sweep
tf update
```
Gałąź testowa pozwala cofnąć wszystko jednym poleceniem. Jeśli `tf` nie zna polecenia, użyj
`python3 .tf/factory/tf.py <polecenie>` (launcher bywa starszy niż fabryka w projekcie).

## 1. Sam skan — darmowy, bez modelu, niczego nie zmienia
```
python3 .claude/skills/core-sweep/scripts/sweep_scan.py scan
```
Wypisuje kandydatów:
- TODO z numerem zgłoszenia i TODO starsze niż 12 miesięcy;
- ścieżki, polecenia i nazwy z `CLAUDE.md` i `docs/project/`, których już nie ma;
- zamknięte zadania oraz wpisy w `parked.md` i `lessons.md`, załatwione później.

Pierwszy test: czy skan nie zgłasza w tym repozytorium rzeczy bez sensu.

## 2. Kontrolne pułapki
Dodaj na gałęzi testowej znane przypadki i zrób commit (skan korzysta z historii gita):

| Pułapka | Gdzie | Oczekiwana grupa w raporcie |
|---|---|---|
| `// TODO TICKET-123: tymczasowe obejście` (TICKET-123 to zamknięte zgłoszenie) | dowolny plik kodu | nieaktualne |
| „Strona X jest w `apps/web/old-page`” (ścieżka, której nie ma) | `CLAUDE.md` | nieaktualne albo sprzeczność |
| `npm run test:legacy` (skryptu nie ma w `package.json`) | `CLAUDE.md` | nieaktualne |
| `// Nie usuwaj tego warunku — bez niego wraca błąd Y` | dowolny plik kodu | **bez zmian** (niepewne albo pominięte) |

Ostatni wiersz jest najważniejszy: sweep nie może zaproponować usunięcia notatki, która wciąż jest potrzebna.

## 3. Pełny przebieg w Claude Code
Napisz „posprzątaj projekt ze starych notatek” albo `/core-sweep`. Sprawdź, czy:
- powstał raport `.tf/reports/sweep-<data>.md` z grupami: nieaktualne, sprzeczności, niepewne — i przy każdej pozycji
  jest dowód (plik:linia, commit);
- przy statusach zgłoszeń agent czyta tracker przez podłączone narzędzie (MCP) albo prosi o wklejenie statusów,
  a nie zgaduje;
- dostajesz pytanie z gotowymi odpowiedziami i nic się nie zmienia bez Twojej zgody.

## 4. Archiwizacja i blokada archiwum
1. Zatwierdź jedną pozycję, np. stary plan. Plik powinien trafić do `docs/project/archive/sweep/<data>/` jednym
   commitem `chore(sweep): archive stale notes`.
2. Poproś agenta: „przeczytaj ten zarchiwizowany plan”. Hook powinien odmówić.
3. Z `TF_ARCHIVE_READ=1` w środowisku hook powinien przepuścić odczyt.

## 5. Sprzątanie po teście
```
git switch main
git branch -D test/sweep
```

## Koszt
Krok 1 jest darmowy. Kroki 3–4 to tani model (Haiku) — rząd centów na przebieg [szacunek]; dokładny koszt pokaże
raport `/tf-task` lub status sesji.

## Gdy coś jest nie tak
Skan zgłasza coś bez sensu albo pomija pułapkę z kroku 2 → zapisz wynik `scan --json` i zgłoś to w repozytorium
fabryki (nie poprawiaj skryptu w projekcie — aktualizacja fabryki go nadpisze).
