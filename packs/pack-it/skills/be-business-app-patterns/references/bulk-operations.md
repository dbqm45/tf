# Operacje masowe

## Przed uruchomieniem
- Zakres jako filtr („wszystkie pasujące: status = new, 50 213 rekordów”), nie lista ID przesyłana z przeglądarki.
- Podgląd: liczba rekordów i próbka; potwierdzenie z liczbą; limit (powyżej progu dodatkowe potwierdzenie lub
  rola).
- Uprawnienie sprawdzane per rekord (te same reguły co dla pojedynczej zmiany) — rekordy bez uprawnienia pomijane
  i raportowane.

## Wykonanie
- Zadanie w tle (kolejka), w partiach (np. 500), każda partia w osobnej transakcji; postęp widoczny w UI.
- Idempotencja: identyfikator operacji, zapis przetworzonych rekordów; wznowienie po awarii nie zmienia ich drugi
  raz.
- Częściowe błędy nie przerywają całości: raport „zmienione / pominięte / błędy z powodem” do pobrania.
- Blokady i obciążenie: partie poza godzinami szczytu albo z limitem tempa, żeby nie zablokować bazy.

## Po wykonaniu
- Jeden wpis audytu operacji (kto, filtr, liczby) plus wpisy per rekord, jeśli audyt jest per obiekt.
- Cofnięcie: zapis poprzednich wartości pozwala odwrócić operację w oknie czasu; dla nieodwracalnych (wysyłka
  e-maili, płatności) wyraźne ostrzeżenie przed startem.
- Powiadomienie o zakończeniu (UI, e-mail) — użytkownik nie czeka na otwartej stronie.
