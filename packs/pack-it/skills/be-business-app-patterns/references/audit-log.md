# Audit log

## Co zapisać w jednym wpisie
| Pole | Przykład | Uwagi |
|---|---|---|
| kiedy | `2026-11-09T18:20:00Z` | czas serwera, UTC |
| kto | `user_id`, rola | przy impersonacji także `actor_id` (kto naprawdę działał) |
| skąd | IP, klient (web, API, zadanie w tle), `request_id` | do korelacji z logami aplikacji |
| co | `order.status_changed`, `order_id` | typ zdarzenia ze słownika, nie wolny tekst |
| zmiana | `{"status": ["new", "paid"]}` | stara i nowa wartość tylko zmienionych pól |
| powód | „zwrot na prośbę klienta”, numer zgłoszenia | wymagany dla operacji wrażliwych |

## Zapis
- W tej samej transakcji co zmiana danych (tabela audytu w tej samej bazie) albo przez outbox
  (be-messaging-outbox), gdy audyt trafia do osobnego systemu — nigdy „po”, bo awaria między zapisami gubi wpis.
- Tylko dopisywanie: aplikacja nie ma uprawnień `UPDATE`/`DELETE` na tabeli audytu; dla wysokich wymagań łańcuch
  skrótów albo magazyn WORM.
- Zapis w warstwie usług (jedno miejsce), nie w kontrolerach; zmiany z zadań w tle i migracji danych też.

## Dane osobowe i retencja
- Nie zapisuj wartości wrażliwych w całości (hasła, tokeny, numery kart nigdy; dane osobowe tylko, gdy cel tego
  wymaga) — zamiast wartości informacja „pole zmienione”.
- Okres przechowywania ustalony z celem (spory, rozliczenia, wymagania prawne); żądanie usunięcia danych obejmuje
  też audyt — pseudonimizacja wpisów zamiast kasowania historii, jeśli audyt musi zostać.

## Odczyt
- Widok historii obiektu dla użytkownika (kto zmienił moje zamówienie) i wyszukiwanie dla audytora; dostęp do
  pełnego audytu tylko dla wskazanych ról, a sam odczyt audytu też jest audytowany.
