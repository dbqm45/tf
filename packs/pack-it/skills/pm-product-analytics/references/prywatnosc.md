# Prywatność i zgody

## Kiedy potrzebna zgoda
- Zapis lub odczyt informacji na urządzeniu użytkownika (ciasteczka, localStorage, identyfikator w skrypcie)
  wymaga zgody, chyba że jest niezbędny do usługi, o którą użytkownik prosi (art. 5 ust. 3 ePrivacy; w Polsce
  art. 399 Prawa komunikacji elektronicznej). Analityka i nagrywanie sesji zwykle nie są niezbędne.
- Zgoda musi być aktywna (nie zaznaczone z góry pole, nie „dalsze korzystanie oznacza zgodę”), równie łatwa do
  odmowy jak do udzielenia i do wycofania.
- Dane osobowe w zdarzeniach (także pseudonimowe ID powiązane z osobą) to przetwarzanie wg RODO: cel, podstawa,
  retencja, umowa powierzenia z dostawcą narzędzia, transfer poza EOG. Szczegóły: arch-privacy-compliance.

## Wariant, gdy zgody nie ma
- Zdarzenia biznesowe z serwera (konto utworzone, płatność) — bez skryptu na urządzeniu; nadal dane osobowe,
  więc podstawa prawna i minimalizacja.
- Analityka bez identyfikatora na urządzeniu, tylko zagregowana (liczby wejść, bez śledzenia osoby między
  wizytami) — ocenę, czy w danym kraju nie wymaga zgody, zostawiasz prawnikowi; nie obiecujesz zgodności.

## Nagrywanie sesji i autocapture
- Tylko po zgodzie; domyślnie maskowane wszystkie pola tekstowe, wyłączone strony z danymi wrażliwymi
  (płatności, dane zdrowotne, panel administracyjny z danymi klientów).
- Krótka retencja nagrań (np. 30 dni) i dostęp tylko dla wskazanych osób.
- Autocapture wyłączone albo ograniczone do listy elementów; zbiera teksty z ekranu, w tym dane osobowe.

## Minimalizacja
- Przedziały zamiast dokładnych wartości, kraj zamiast adresu IP, wewnętrzne ID zamiast e-maila.
- Okres przechowywania surowych zdarzeń ustawiony w narzędziu, nie „bez końca”.
- Żądanie usunięcia danych (RODO art. 17) obejmuje też narzędzie analityczne — procedura usuwania po `user_id`.
