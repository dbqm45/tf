# Metody formalne jako wyrocznia

> **Spis treści:** 1. Kiedy warto · 2. Drabina kosztu (od najtańszego) · 3. Przebieg · 4. Granice wyniku · 5. Przykład: reguły rabatowe (Z3, uruchomiony) · 6. Przykład: ponowienie po zgubionej odpowiedzi (TLA+, TLC,… · 7. Przykład: uprawnienia przez zagnieżdżone grupy (Alloy,…

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

## 5. Przykład: reguły rabatowe (Z3, uruchomiony)
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
    wynik = s.check()
    print(f"limit w kodzie={z_limitem}: {wynik}", end="")
    if wynik == sat:
        m = s.model()
        print(f" -> koszyk={m[koszyk]}, kod={m[kod]}, lojalny={m[lojalny]}", end="")
    print()
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

## 6. Przykład: ponowienie po zgubionej odpowiedzi (TLA+, TLC, uruchomiony)
Klient rezerwuje miejsce, odpowiedź może zginąć w sieci, po timeoucie klient ponawia żądanie. Właściwość z kryterium:
jedno żądanie klienta daje najwyżej jedną rezerwację. Testy integracyjne przechodzą, bo zgubiona odpowiedź w nich
nie występuje.

```tla
---- MODULE Rezerwacja ----
\* Klient rezerwuje miejsce; odpowiedź może zginąć, po timeoucie klient ponawia żądanie.
EXTENDS Naturals, FiniteSets
CONSTANTS Klienci, Miejsca, MaxPonowien, Idempotencja
VARIABLES wolne, rezerwacje, stan, ponowienia, siec
vars == <<wolne, rezerwacje, stan, ponowienia, siec>>

Init == /\ wolne = Miejsca
        /\ rezerwacje = {}
        /\ stan = [k \in Klienci |-> "start"]
        /\ ponowienia = [k \in Klienci |-> 0]
        /\ siec = {}

Wyslij(k) == /\ stan[k] = "start"
             /\ siec' = siec \cup {[typ |-> "zad", k |-> k]}
             /\ stan' = [stan EXCEPT ![k] = "czeka"]
             /\ UNCHANGED <<wolne, rezerwacje, ponowienia>>

Obsluz(m) == /\ m.typ = "zad"
             /\ IF Idempotencja /\ \E r \in rezerwacje : r.k = m.k
                  THEN UNCHANGED <<wolne, rezerwacje>>          \* to samo żądanie: zwróć istniejącą
                  ELSE \E s \in wolne :
                         /\ rezerwacje' = rezerwacje \cup {[k |-> m.k, miejsce |-> s]}
                         /\ wolne' = wolne \ {s}
             /\ siec' = (siec \ {m}) \cup {[typ |-> "odp", k |-> m.k]}
             /\ UNCHANGED <<stan, ponowienia>>

Odbierz(m) == /\ m.typ = "odp"
              /\ siec' = siec \ {m}
              /\ stan' = [stan EXCEPT ![m.k] = "ok"]
              /\ UNCHANGED <<wolne, rezerwacje, ponowienia>>

Zgub(m) == /\ m.typ = "odp"                                  \* utrata odpowiedzi w sieci
           /\ siec' = siec \ {m}
           /\ UNCHANGED <<wolne, rezerwacje, stan, ponowienia>>

Ponow(k) == /\ stan[k] = "czeka"
            /\ ~\E m \in siec : m.k = k                       \* timeout: nic w drodze
            /\ ponowienia[k] < MaxPonowien
            /\ ponowienia' = [ponowienia EXCEPT ![k] = @ + 1]
            /\ siec' = siec \cup {[typ |-> "zad", k |-> k]}
            /\ UNCHANGED <<wolne, rezerwacje, stan>>

Next == \/ \E k \in Klienci : Wyslij(k) \/ Ponow(k)
        \/ \E m \in siec : Obsluz(m) \/ Odbierz(m) \/ Zgub(m)

Spec == Init /\ [][Next]_vars

\* AC-1: jedno żądanie klienta daje najwyżej jedną rezerwację.
JednaRezerwacjaNaKlienta == \A k \in Klienci : Cardinality({r \in rezerwacje : r.k = k}) <= 1
====
```

Konfiguracja `Rezerwacja.cfg` (dwa warianty, różnią się tylko `Idempotencja`):
```
CONSTANTS Klienci = {a, b}  Miejsca = {m1, m2, m3}  MaxPonowien = 1  Idempotencja = FALSE
SPECIFICATION Spec
INVARIANT JednaRezerwacjaNaKlienta
```
Uruchomienie: `java -cp tla2tools.jar tlc2.TLC -config Rezerwacja.cfg -deadlock -workers 1 Rezerwacja.tla`
(`-deadlock` wyłącza zgłaszanie stanów końcowych jako zakleszczeń — klient po `ok` nic już nie robi).

Wynik bez idempotencji (skrót śladu TLC, 6 stanów, 83 różne stany przejrzane; nazwy akcji przy stanach 3, 4 i 6
odczytane ze zmiany stanu — TLC podaje tam `<Next …>`, bo akcje są wywoływane wewnątrz `\E m \in siec`):
```
Error: Invariant JednaRezerwacjaNaKlienta is violated.
State 2: <Wyslij(a)>    siec = {[k |-> a, typ |-> "zad"]}
State 3: <Obsluz>       rezerwacje = {[k |-> a, miejsce |-> m1]}, siec = {[k |-> a, typ |-> "odp"]}
State 4: <Zgub>         siec = {}
State 5: <Ponow(a)>     siec = {[k |-> a, typ |-> "zad"]}
State 6: <Obsluz>       rezerwacje = {[k |-> a, miejsce |-> m1], [k |-> a, miejsce |-> m2]}
```
Z `Idempotencja = TRUE`: `Model checking completed. No error has been found.` — 719 stanów wygenerowanych,
382 różne, głębokość 13. Ślad staje się testem `AC-1: odpowiedź na rezerwację ginie, klient ponawia → jedna
rezerwacja` (wstrzyknięta utrata odpowiedzi; czerwony przed dodaniem klucza idempotencji). Raport z granicami:
„TLC: 2 klientów, 3 miejsca, 1 ponowienie, zbiór wiadomości bez duplikatów i bez kolejności — brak naruszenia”.
Model nie obejmuje duplikatów w sieci (zbiór zamiast wielozbioru) ani wygasania klucza — to osobne rozszerzenia.

## 7. Przykład: uprawnienia przez zagnieżdżone grupy (Alloy, uruchomiony)
Faktura udostępniona grupie; grupa może zawierać podgrupy. Reguły zapisu z kodu pilnują najemcy członków i faktur,
ale nie podgrup.

```alloy
-- Dostęp do faktur przez grupy, które mogą zawierać inne grupy.
sig Najemca {}
sig Uzytkownik { najemca: one Najemca }
sig Grupa { najemcaG: one Najemca, czlonkowie: set Uzytkownik, podgrupy: set Grupa }
sig Faktura { wlasciciel: one Najemca, udostepniona: set Grupa }

-- użytkownik widzi fakturę, gdy należy do grupy udostępnienia albo do jej podgrupy (na dowolnej głębokości)
fun widzi[u: Uzytkownik]: set Faktura {
  { f: Faktura | some g: f.udostepniona | u in g.*podgrupy.czlonkowie }
}

-- reguła z kodu: członkowie grupy i faktura udostępniana grupie należą do tego samego najemcy
fact RegulyZapisu {
  all g: Grupa | g.czlonkowie.najemca in g.najemcaG
  all f: Faktura | f.udostepniona.najemcaG in f.wlasciciel
}

-- AC-3: nikt nie widzi faktury innego najemcy
pred Izolacja { all u: Uzytkownik | widzi[u].wlasciciel in u.najemca }
-- poprawka: podgrupa należy do tego samego najemcy co grupa nadrzędna
pred PodgrupyTegoSamegoNajemcy { all g: Grupa | g.podgrupy.najemcaG in g.najemcaG }

check BezPoprawki { Izolacja } for 4
check ZPoprawka { PodgrupyTegoSamegoNajemcy implies Izolacja } for 4
```

Uruchomienie: `java -jar alloy.jar exec -f Uprawnienia.als` (kontrprzykłady w katalogu `Uprawnienia/`,
`receipt.json`). Wynik:
```
00. check BezPoprawki              0    1/1     SAT
01. check ZPoprawka                0       UNSAT
```
`SAT` przy `check` to kontrprzykład. Najmniejszy (zakres 2): faktura najemcy A udostępniona grupie G1 najemcy A;
G1 ma podgrupę G0 najemcy B; członek G0 (najemca B) widzi fakturę A. Test: `AC-3: podgrupa innego najemcy w grupie
udostępnienia → brak dostępu do faktury`. `UNSAT` po poprawce dotyczy zakresu `for 4` (do 4 obiektów każdego typu).

## Źródła
- Z3 (`z3-solver` 4.15.4 z PyPI) — przykład z §5 uruchomiony 2026-11-15.
- TLA+: `tla2tools.jar` z wydania `v1.8.0` repozytorium tlaplus/tlaplus (TLC zgłasza się jako „TLC2 Version
  2026.11.15.002146, rev bc1b506”), OpenJDK 21 — przykład z §6 uruchomiony 2026-11-15.
- Alloy 6.2.0 (`org.alloytools.alloy.dist.jar` z wydania AlloyTools/org.alloytools.alloy), polecenie `exec` —
  przykład z §7 uruchomiony 2026-11-15.
- Apalache i Dafny — nazwy i role narzędzi z wiedzy ogólnej [niezweryfikowane: nie uruchamiano].
Opisane własnymi słowami.
