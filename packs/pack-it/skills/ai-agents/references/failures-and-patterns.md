# Porażki agentów i środki zaradcze

## Porażki
| Objaw | Przyczyna | Środek |
|---|---|---|
| zapętlenie, te same wywołania | brak limitu, niejasny cel, narzędzie nie zwraca postępu | limit kroków, wykrycie powtórzeń, jawny stan końcowy |
| zły wybór narzędzia | za dużo, nakładające się opisy | konsolidacja, przestrzenie nazw, granice w opisie |
| błędne argumenty | niejednoznaczne parametry | enum, jednoznaczne nazwy, poka-yoke, błąd z poprawką |
| podwójna akcja po timeoucie | zapis bez idempotencji | klucz idempotencji, sprawdzenie stanu przed zapisem |
| zgubiony cel po długiej pracy | przepełniony kontekst | kompaktowanie, plik postępu, subagent z czystym kontekstem |
| błąd w kroku 3 psuje krok 9 | kumulacja błędów stanu | bramki kodu między krokami, punkty kontrolne, wznawianie |
| koszt rośnie bez poprawy wyniku | multi-agent lub agent tam, gdzie wystarczy workflow | wróć na niższy szczebel, mierz koszt na przypadek |
| polecenie z treści wykonane | dane traktowane jak instrukcje | dane ≠ polecenia, brak kanału wyjścia przy danych poufnych |
| subagenci dublują pracę | niedookreślone zadanie | cel, format, granice i narzędzia w zleceniu |
| „działa na demo” | brak zestawu przypadków | 10–20 przypadków, potem rozszerzanie z produkcji |

## Wzorzec zatwierdzenia przez człowieka
Agent przygotowuje akcję (`zwrot_przygotuj` → szkic z kwotą, odbiorcą, skutkiem), człowiek zatwierdza w osobnym
kanale, dopiero kod wykonuje `zwrot_wykonaj` z kluczem idempotencji. Model nie ma narzędzia wykonującego bez tego kroku.

## Co logować w śladzie
Id przebiegu, numer kroku, wywołanie (nazwa, argumenty, wynik skrócony), tokeny wejścia i wyjścia, czas, decyzja
o zakończeniu, wersja promptu i modelu. Dane osobowe maskuj lub pomijaj w śladach.

## Agent obsługujący program
Zanim agent dostanie zrzuty ekranu, szukasz wyższego interfejsu, w tej kolejności: własny format pliku programu →
wiersz poleceń (tryb bez okna) → skrypty lub automatyzacja (np. COM) → oficjalne API → drzewo dostępności (nazwy
kontrolek jako tekst) → piksele na końcu. Każdy szczebel wyżej jest szybszy, tańszy i odporny na zmianę wyglądu.
- **Każda funkcja jako narzędzie z kontraktem:** schemat argumentów, implementacja, **weryfikator** (odczyt wyniku
  z powrotem, np. ponowne otwarcie zapisanego pliku innym czytnikiem) i **skutek** — `local` albo `outward`. Działanie
  wychodzące do innych ludzi (wysyłka, publikacja) czeka na zgodę człowieka.
- Wynik narzędzia to krótki JSON z listą wykonanych sprawdzeń. Odmowa narzędzia podaje powód i wykonalną alternatywę.
- Lista narzędzi zawężona do grup pasujących do prośby, nie wszystkie schematy w każdym wywołaniu. Łańcuch zależnych
  wywołań planujesz w jednym wywołaniu modelu, z odwołaniami do wyników wcześniejszych kroków.
- Udany przebieg można skompilować do nowego narzędzia z parametrami. Odtwarzasz go tylko wtedy, gdy okno zgadza się
  z wyuczonym, i wyłączasz po 2 porażkach.
- Klasyfikator ryzyka akcji UI działa w kodzie, nie w modelu, bo tekst na ekranie może nieść wstrzyknięcie poleceń.
- Sprawdzenia dowodzą liczb, nie sensu: zły plan może przejść wszystkie weryfikatory. Wynik wychodzący na zewnątrz
  ogląda człowiek.

Źródło: F. Khan, „Building Fast Computer Agents to Solve Complex Tasks” (2026-10-07); liczby autora z jednego
stanowiska [niezweryfikowane].
