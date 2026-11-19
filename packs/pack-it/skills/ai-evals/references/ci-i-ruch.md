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

### Gotowa bramka: `scripts/eval_gate.py`
Skrypt nie uruchamia modelu. Twój runner ewaluacji zapisuje wyniki w JSON Lines, jedna linia na próbę:
`{"id": "zwrot-17", "passed": true, "layer": "regression", "cost_usd": 0.012, "trial": 2}` (`id` i `passed` wymagane;
`layer: regression` oznacza zadanie ze zbioru regresyjnego; kilka linii z tym samym `id` to powtórzone próby).

```bash
# raz, i po każdej zmianie zbioru: baza z 3–5 przebiegów obecnej wersji → evals/baseline.json (commit do repo)
python3 .claude/skills/ai-evals/scripts/eval_gate.py baseline baza1.jsonl baza2.jsonl baza3.jsonl --margin 0.02
# w CI, po przebiegu kandydata
python3 .claude/skills/ai-evals/scripts/eval_gate.py check wyniki.jsonl --budget-usd 5 --report eval-gate.md
```

| Werdykt | Kiedy | Kod |
|---|---|---|
| wstrzymaj | sukces poniżej progu (dolna granica rozrzutu − margines), porażka zadania z warstwy regresyjnej, koszt ponad budżet | 1 |
| zbadaj | sukces poniżej dolnej granicy rozrzutu, ale w marginesie; padło zadanie stabilne w bazie; zestaw zadań inny niż w bazie; budżet podany, a wyniki bez kosztu | 0 (`--strict`: 1) |
| wypuść | pozostałe | 0 |

Pusty albo uszkodzony plik wyników to kod 2, nie „0 porażek”. `--json` daje wynik maszynowy (werdykt, sukces, próg,
rozrzut bazy, pass^k, pass@k, koszt, regresje, powody), np. jako dowód przy bramce wydania. Margines i każdą jego zmianę
zapisujesz jak decyzję (kto, dlaczego, do kiedy). Szkic kroku w GitHub Actions (akcje przypięte do SHA — ops-ci-cd):

```yaml
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - run: ./scripts/run-evals.sh --suite smoke --out wyniki.jsonl      # Twój runner; klucz modelu z sekretów
      - run: python3 .claude/skills/ai-evals/scripts/eval_gate.py check wyniki.jsonl --budget-usd 5 --report eval-gate.md
      - if: always()
        run: cat eval-gate.md >> "$GITHUB_STEP_SUMMARY"
```

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
