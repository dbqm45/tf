# Inwentarz, audyt, metadane i taksonomia

## Inwentarz treści
Arkusz lub eksport z CMS, jedna linia na stronę lub zasób:
`ID | adres | tytuł | typ | poziom w hierarchii | właściciel | autor | data publikacji i aktualizacji | język | ruch (12 mies.) | źródła wejść | metadane`.
Zbieraj automatycznie (mapa XML, crawler, API CMS, analityka). Ręcznie tylko dopisujesz właściciela i decyzję.
Bez właściciela strona jest kandydatem do usunięcia lub przejęcia.

## Audyt treści
Oceń próbkę lub całość według kryteriów:
| Kryterium | Pytanie |
|---|---|
| aktualność | czy treść jest zgodna ze stanem faktycznym i datą |
| dokładność | czy jest poprawna, nie sprzeczna z inną stroną |
| przydatność | czy ktoś jej potrzebuje (ruch, zadania z kroku 1) |
| zrozumiałość | prosty język, jedno zadanie na stronę |
| duplikaty | czy ta sama informacja jest gdzie indziej (połącz) |
Decyzja: **zostaw / popraw / połącz / usuń / dopisz**. Przy usuwaniu: przekierowania 301 i zmiana linków wewnętrznych.
Wynik audytu zasila zarówno karty do sortowania (reprezentatywna próbka stron), jak i plan migracji.

## Karty do sortowania z inwentarza
Wybierz 30–60 stron/pojęć reprezentujących wszystkie obszary, w tym te często szukane (z zapytań do wyszukiwarki).
Nazwy w języku użytkowników; krótki opis na rewersie.

## Metadane
- Minimum: tytuł, opis, typ treści, temat, odbiorca (jeśli różny), data aktualizacji, właściciel.
- Zakres wartości: **kontrolowane słownictwo** (lista, nie wolny tekst), synonimy i formy przestarzałe mapowane na nazwę preferowaną.
- Zastosowanie: filtry i facety w wyszukiwarce i listach, treści powiązane, raporty o stanie treści.
- Zasada: każdy atrybut ma użytkownika (filtr lub raport). Nie zbieraj metadanych „na wszelki wypadek”.

## Taksonomia i słownik etykiet
Wpis: `nazwa preferowana | definicja | synonimy i zwroty użytkowników | nazwa niezalecana | poziom | właściciel`.
Hierarchia i zasady: jedna zasada grupowania na poziom; nazwy rozłączne; relacje szersze/węższe/powiązane.
Fasety (np. kategoria, marka, cena, zastosowanie) zamiast jednego drzewa, gdy obiekty mają kilka niezależnych cech (sklep).
Słownik żyje: właściciel i data przeglądu (co kwartał lub przy zmianie oferty).
