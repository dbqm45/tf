# Bramka w CI i ewaluacje na ruchu

Spis treści: 1. Bramka w CI · 2. Progi z rozrzutu · 3. Koszt · 4. Offline kontra online · 5. Format raportu · 6. Agent

## 1. Bramka w CI
| Zestaw | Kiedy | Wielkość | Cel |
|---|---|---|---|
| smoke | każdy PR | 10–20 zadań, tani model sędziego | wyłapać oczywiste regresje |
| regresyjny | każdy PR zmieniający prompt, narzędzia, schemat | cały zbiór regresyjny | żaden naprawiony błąd nie wraca |
| pełny | nocą, przed wydaniem, przy zmianie modelu | wszystkie warstwy, k prób | decyzja o wydaniu |

Zmiana modelu, wersji harnessu, promptu, opisu narzędzia lub schematu uruchamia pełny zestaw. Ten sam model w innym
harnessie daje inne wyniki, więc po podmianie mierzysz od nowa.

## 2. Progi z rozrzutu
1. Uruchom bazę (obecną wersję) n = 3–5 razy [praktyka]; zapisz minimum, maksimum, średnią.
2. Próg bezwzględny = dolna granica rozrzutu minus margines uzgodniony z zespołem (nie okrągła liczba „na oko”).
3. Regresja = spadek względem bazy poza rozrzutem; przy małych zbiorach policz przedział ufności lub użyj testu na
   parach zadań (data-analysis).
4. Zadania regresyjne: próg bliski 100%, każde wywrócone zadanie czerwone.
5. Luzowanie progu to decyzja z zapisem (kto, dlaczego, do kiedy), nie edycja liczby w configu.
6. Alert: spadek metryki w CI lub online powyżej progu → zgłoszenie do właściciela; trend tygodniowy w raporcie.

## 3. Koszt
Koszt = zadania × próby × kandydaci × (generowanie + sędzia). Policz przed uruchomieniem. Oszczędności: tani model
dla sędziego po kalibracji, cache stałego prefiksu (core-cost-control), smoke zamiast pełnego zestawu, równoległość
bez zwiększania liczby prób. Wariancję zmniejszają powtórzenia, nie dłuższe prompty sędziego.

## 4. Offline kontra online
- **Offline:** powtarzalne, tanie, przed wdrożeniem. Nie zobaczy rozkładu prawdziwych użytkowników.
- **Shadow:** nowa wersja przetwarza ten sam ruch w tle, wyniki porównujesz z obecną; użytkownik ich nie widzi.
  Dobre dla zmian wysokiego ryzyka.
- **A/B:** część ruchu dostaje nową wersję; metryka biznesowa (rozwiązane sprawy, konwersja, eskalacje) i metryki
  ochronne (koszt, czas, skargi). Czas trwania i wielkość próby z data-analysis.
- **Próbki z ruchu:** losowe i z sygnałów negatywnych (kciuk w dół, ponowienie, eskalacja) do ręcznej oceny; nowe
  porażki wracają do zbioru regresyjnego.
- Telemetria i alerty produkcyjne: ops-observability.

## 5. Format raportu (wersja pełna)
```
Ewaluacja: <funkcja> | data | commit/wersja promptu | model + harness
Zbiór: <warstwy, N, wersja> | k prób: <k> | sędzia: <wersja, zgodność z ludźmi>
Wynik: sukces <x% [min–max]> vs baza <y% [min–max]> | pass^k <..> | pass@k <..>
Koszt: <USD/przebieg>, czas p50/p95 | Limity trajektorii: kroki <..>, narzędzia zakazane <0>
Regresje: lista zadań z linkiem do transkryptu | Nowe porażki do zbioru: lista
Werdykt: wypuść / wstrzymaj / zbadaj — uzasadnienie w 1–2 zdaniach
```

## 6. Agent
- Środowisko czyste na każdą próbę (brak wspólnego stanu, brak wycieków między próbami).
- Wynik: stan końcowy; trajektoria: limity kroków i kosztu, zakazane narzędzia, pętle.
- Transkrypty porażek czyta człowiek co najmniej dla próbki — sprawdza też uczciwość gradera.
