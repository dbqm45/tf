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
