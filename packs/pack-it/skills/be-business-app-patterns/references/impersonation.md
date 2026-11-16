# Impersonacja (support działa jako użytkownik)

## Najpierw: czy wystarczy mniej
- Widok tylko do odczytu konta klienta albo udostępnienie ekranu przez klienta często rozwiązuje problem bez
  działania w jego imieniu.

## Jeśli impersonacja
- Osobne uprawnienie (nie każda rola supportu), powód lub numer zgłoszenia wymagany przy starcie; dla kont
  wrażliwych zgoda klienta.
- Sesja z dwoma identyfikatorami: `user_id` (w czyim imieniu) i `actor_id` (kto działa) — oba w każdym wpisie
  audytu i w logach.
- Baner w interfejsie przez cały czas trwania i przycisk zakończenia; krótki limit czasu (np. 30 min).
- Zakazane w trybie impersonacji: zmiana hasła, e-maila, MFA, metod płatności, eksport danych, usuwanie konta,
  operacje finansowe — sprawdzane na serwerze po `actor_id`.
- Nigdy przez hasło klienta ani jego token; sesja wydawana przez serwer na podstawie uprawnienia supportu.
- Powiadomienie klienta (e-mail lub wpis w historii konta), że support miał dostęp.

## Testy
- Operacja zakazana zwraca odmowę w trybie impersonacji; wpis audytu ma oba identyfikatory; sesja wygasa po
  limicie; użytkownik bez uprawnienia nie rozpocznie impersonacji.
