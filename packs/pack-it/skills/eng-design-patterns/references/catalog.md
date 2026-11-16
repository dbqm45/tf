# Katalog 22 wzorców — skrót „kiedy tak / kiedy nie”

Pełny opis w pliku wzorca (problem, rozwiązanie, koszty, powiązania, forma idiomatyczna w TS, przykład sprawdzony
kompilatorem, pułapki).

## Kreacyjne
| Wzorzec | Jednym zdaniem | Kiedy NIE (skrót) | Plik |
|---|---|---|---|
| Metoda wytwórcza | podklasa wymienia tworzony produkt, logika bazowa zostaje | jeden wariant; wystarczy funkcja fabrykująca | `creational/factory-method.md` |
| Fabryka abstrakcyjna | spójne rodziny obiektów bez znajomości klas | jedna rodzina „na zapas”; częściej przybywa typów niż rodzin | `creational/abstract-factory.md` |
| Budowniczy | złożony obiekt krokami, walidacja przy `build()` | kilka opcji — obiekt opcji wystarczy | `creational/builder.md` |
| Prototyp | obiekt sam się klonuje, także z prywatnym stanem | płaskie DTO — `structuredClone`/spread | `creational/prototype.md` |
| Singleton | jedna instancja + globalny dostęp | prawie zawsze: moduł ES lub zakres DI zamiast klasy | `creational/singleton.md` |

## Strukturalne
| Wzorzec | Jednym zdaniem | Kiedy NIE (skrót) | Plik |
|---|---|---|---|
| Adapter | tłumaczy cudze API na nasz port | obie strony są nasze — ujednolić u źródła | `structural/adapter.md` |
| Most | dwa niezależne wymiary zmienności jako dwie hierarchie | rośnie tylko jeden wymiar | `structural/bridge.md` |
| Kompozyt | element i grupa pod jednym interfejsem, rekurencyjnie | dane nie są drzewem | `structural/composite.md` |
| Dekorator | warstwy zachowania składane w runtime, ten sam interfejs | 1–2 stałe dodatki; nie mylić z `@dekoratorem` TS | `structural/decorator.md` |
| Fasada | prosty interfejs do złożonego podsystemu | podsystem już jest prosty; fasada-bóg | `structural/facade.md` |
| Pyłek | współdzielenie niezmiennego stanu tysięcy obiektów | brak zmierzonego problemu z pamięcią | `structural/flyweight.md` |
| Pełnomocnik | kontrola dostępu (leniwość, uprawnienia, cache) za tym samym interfejsem | motywacją jest nowe zachowanie (Dekorator) albo wystarczy `if`/`??=` | `structural/proxy.md` |

Dekorator i Pełnomocnik wyglądają w kodzie tak samo — rozstrzyga motywacja.

## Behawioralne
| Wzorzec | Jednym zdaniem | Kiedy NIE (skrót) | Plik |
|---|---|---|---|
| Łańcuch zobowiązań | obsłuż albo przekaż dalej; można przerwać | stała, krótka sekwencja; framework ma middleware | `behavioral/chain-of-responsibility.md` |
| Polecenie | akcja jako obiekt: kolejka, log, cofanie | bez cofania/serializacji — closure wystarczy | `behavioral/command.md` |
| Iterator | przechodzenie bez ujawniania struktury | protokół iteracji i generatory są w języku | `behavioral/iterator.md` |
| Mediator | komponenty rozmawiają przez pośrednika | 2–3 obiekty z jedną relacją; store frameworka | `behavioral/mediator.md` |
| Pamiątka | migawka stanu bez łamania hermetyzacji | stan niezmienny — historia to tablica stanów | `behavioral/memento.md` |
| Obserwator | subskrybenci dowiadują się o zmianie | jeden znany odbiorca — callback | `behavioral/observer.md` |
| Stan | zachowanie zależne od stanu w obiektach-stanach | stany różnią się danymi — unia + `switch` | `behavioral/state.md` |
| Strategia | wymienny wariant algorytmu/polityki | to zwykle po prostu funkcja; jeden wariant | `behavioral/strategy.md` |
| Metoda szablonowa | stały szkielet, nadpisywane kroki | różnice rozproszone lub zmienne w runtime — Strategia | `behavioral/template-method.md` |
| Odwiedzający | nowe operacje na stabilnej hierarchii typów | typy często przybywają; mało typów i operacji | `behavioral/visitor.md` |

Polecenie, Iterator i Strategia najczęściej mają w TS lżejszą formę niż klasowa — `critique-and-pitfalls.md`, pkt 1.
