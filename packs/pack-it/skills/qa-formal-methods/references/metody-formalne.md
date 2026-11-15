# Metody formalne jako wyrocznia

Spis treści: 1. Kiedy warto · 2. Drabina kosztu · 3. Przebieg · 4. Granice wyniku · 5. Przykład (Z3) · Źródła

## 1. Kiedy warto
Model sprawdzany narzędziem opłaca się tam, gdzie przykładów i losowania jest za mało, a błąd jest drogi:
- **współbieżność i ponowienia** — dwie rezerwacje ostatniego miejsca, podwójne obciążenie po timeoucie, wyścig
  przy blokadzie optymistycznej (testy integracyjne trafiają tylko w przeploty, które akurat wystąpiły);
- **protokoły i maszyny stanów** — synchronizacja, sesja ładowania, cykl życia faktury, migracja z dwoma zapisami;
- **reguły kombinatoryczne z limitem** — rabaty, limity kredytowe, uprawnienia łączone z kilku źródeł.

Nie opłaca się przy mapowaniu danych, UI, integracji z zewnętrznym API ani przy regułach, które da się przejrzeć
tabelą. „Zweryfikujmy formalnie cały moduł” → wybierz 1–3 właściwości o najwyższym koszcie błędu, resztę testami.

## 2. Drabina kosztu (od najtańszego)
1. Asercje i kontrakty w kodzie (warunki wejścia i wyjścia, niezmienniki agregatu).
2. Testy właściwości (Hypothesis, fast-check) — losowanie; nie trafia w próg ani w rzadki przeplot.
3. Solver SMT (Z3) — dowód albo kontrprzykład dla reguł nad liczbami i warunkami logicznymi.
4. Model checking (TLA+/PlusCal z TLC lub Apalache, Alloy) — wszystkie przeploty małego modelu protokołu.
5. Weryfikacja programu (Dafny) i asystenci dowodu — gwarancja na samym kodzie, najdroższe w utrzymaniu.

Wchodzisz o szczebel wyżej tylko wtedy, gdy niższy nie umie wyrazić właściwości albo jej nie znajduje.

## 3. Przebieg
1. **Właściwość słowami, z kryterium.** „Nigdy dwie potwierdzone rezerwacje tego samego miejsca” — z identyfikatorem
   kryterium `AC-n` ze specyfikacji zadania (`tf spec`), z którego wynika.
2. **Model, nie kod.** Tylko stan i kroki, które dotyczą właściwości; zdarzenia środowiska jako wybór niedeterministyczny
   (utrata odpowiedzi, opóźnienie, restart, ponowienie).
3. **Negacja wymagania do narzędzia.** Solver lub checker szuka stanu, który łamie właściwość.
4. **Kontrprzykład → test.** Każdy znaleziony ślad zamieniasz w test akceptacyjny z identyfikatorem `AC-n` w nazwie
   (wtedy `tf trace` łączy go z kryterium); test ma być czerwony na obecnym kodzie, zanim go naprawisz.
5. **Poprawka najpierw w modelu.** Checker bez kontrprzykładu na poprawionym modelu, dopiero potem zmiana kodu.
6. **Model obok kodu.** Plik modelu w repozytorium, w katalogu modułu, z linią,
   który commit kodu opisuje; zmiana protokołu w kodzie bez zmiany modelu to ustalenie w przeglądzie
   (qa-change-review).

## 4. Granice wyniku
- **„Brak kontrprzykładu” dotyczy tylko modelu.** W raporcie zawsze: liczba procesów, wiadomości, zakres liczb, głębokość
  przeszukania („TLC: 2 serwisy, 1 miejsce, do 2 ponowień — brak naruszenia”). Bez tych granic wynik brzmi jak dowód
  dla produkcji, a nim nie jest.
- **Model upraszcza arytmetykę.** Liczby rzeczywiste w solverze to nie grosze i nie `float` — kwoty modeluj liczbami
  całkowitymi w groszach albo dopisz krok zaokrąglenia tak, jak robi to kod; kolejność stosowania reguł jak w kodzie.
- **Model rozjeżdża się z kodem.** Bez kroku 6 przebiegu za pół roku sprawdza nieistniejący protokół.
- **Za mały model daje fałszywe „OK”.** Błąd, który wymaga trzech uczestników, nie pojawi się w modelu z dwoma.
  Rozszerz zakres, gdy czas sprawdzania na to pozwala.

## 5. Przykład (Z3, uruchomiony)
Trzy reguły rabatowe łączone warunkami, wymaganie: łączny rabat ≤ 30% i cena nie ujemna. Losowe koszyki w typowym
zakresie (50–500 zł) nic nie znalazły.

```python
from z3 import Real, Bool, If, Solver, Or, sat

koszyk = Real("koszyk")
kod, lojalny = Bool("kod"), Bool("lojalny")

def rabat(z_limitem):
    r = If(koszyk >= 200, 0.10 * koszyk, 0)      # R1: próg koszyka
    r = r + If(kod, 0.15 * koszyk, 0)             # R2: kod promocyjny
    r = r + If(lojalny, 20, 0)                    # R3: lojalność, kwota stała
    return If(r > 0.30 * koszyk, 0.30 * koszyk, r) if z_limitem else r

for z_limitem in (False, True):
    s = Solver()
    s.add(koszyk > 0)
    r = rabat(z_limitem)
    s.add(Or(r > 0.30 * koszyk, koszyk - r < 0))  # negacja wymagania
    print(z_limitem, s.check(), s.model() if s.check() == sat else "")
```

Wynik (z3-solver 4.15.4):
```
limit w kodzie=False: sat -> koszyk=1/2, kod=False, lojalny=True
limit w kodzie=True: unsat
```
Kontrprzykład: koszyk 0,50 zł i rabat lojalnościowy 20 zł → ujemna cena. Staje się testem
`AC-2: koszyk 0,50 zł z lojalnością → cena 0,35 zł` (czerwony przed poprawką). Po dodaniu limitu w kodzie `unsat`
oznacza: w tym modelu (liczby rzeczywiste, trzy reguły) żadna kombinacja nie łamie wymagania — granice wyniku
z §4 wpisujesz do raportu.

## Źródła
- Z3 (`z3-solver` 4.15.4 z PyPI) — przykład z §5 uruchomiony 2026-11-15.
- TLA+, TLC, Apalache, Alloy, Dafny — nazwy i role narzędzi z wiedzy ogólnej; składni ani wersji nie sprawdzano
  w tej sesji [niezweryfikowane: nie uruchamiano].
Opisane własnymi słowami.
