# Techniki i migracja — stan na 2026-10-17

Spis treści: 1. Myślenie · 2. Prefill i format · 3. Cache · 4. Migracja · 5. Szablony i rejestr · 6. Błędy · 7. Inne dostawcy

Nazwy modeli, parametry i ceny zmieniają się często; przed zmianą sprawdź bieżącą stronę dokumentacji (core-grounding).

## 1. Myślenie
- Modele Claude 4.6 i nowsze używają adaptacyjnego myślenia (`thinking: {type: "adaptive"}`): model sam wybiera, czy
  i ile myśleć, zależnie od parametru `effort` i trudności. W części najnowszych modeli myślenie jest zawsze włączone.
- Starsze modele: rozszerzone myślenie z `budget_tokens`. Na modelach 4.7 i nowszych ustawienie `budget_tokens`
  zwraca błąd 400; budżet kontrolujesz przez `effort`. Przy migracji zamień konfigurację i sprawdź ewaluacją.
- Zbyt częste myślenie przy dużych promptach systemowych możesz ograniczyć instrukcją („myśl tylko, gdy zadanie
  wymaga rozumowania wieloetapowego”).
- Przykłady few-shot wpływają też na to, jak model rozumuje; podawaj je jako problem, metodę i wynik.
- Gdy myślenie wyłączone: ręczny łańcuch myślenia — „rozumuj przed odpowiedzią, wynik w `<answer>`”. Kod czyta tylko `<answer>`.
- Nie używaj myślenia do prostej ekstrakcji, klasyfikacji i przekształcania formatu; mierz zysk jakości i koszt.

## 2. Prefill i format wyjścia
- Prefill ostatniej wiadomości asystenta nie jest obsługiwany od modeli Claude 4.6 (żądanie zwraca błąd).
- Zamienniki: wymuszony format (JSON, YAML, klasyfikacja) → structured outputs ze schematem;
  pominięcie wstępu → instrukcja „odpowiadaj bezpośrednio, bez wstępu”, tag wyjściowy lub wywołanie narzędzia;
  kontynuacja przerwanej odpowiedzi → wiadomość użytkownika z końcówką poprzedniej odpowiedzi;
  odświeżanie kontekstu w długiej rozmowie → przypomnienie w turze użytkownika albo narzędzie dostarczające kontekst.
- Kontrakt wyjścia, walidacja po odbiorze i obsługa porażki: eng-llm-features §2.

## 3. Układ pod cache (Anthropic)
- Prefiks buforowany w kolejności: `tools` → `system` → `messages`; `cache_control` na ostatnim bloku
  identycznym w żądaniach (maks. 4 punkty jawne; jest też tryb automatyczny).
- TTL: 5 minut (domyślnie, odświeżany przy odczycie) albo 1 godzina (`"ttl": "1h"`); zapis kosztuje 1,25× (5 min) lub
  2× (1 godz.) ceny wejścia, odczyt zwykle 0,1× (na części modeli mniej).
- Minimalna długość prefiksu zależy od modelu (od 512 do 4096 tokenów); krótszy nie jest buforowany i bez błędu.
- Unieważniają: zmiana tekstu przed punktem (znacznik czasu, id użytkownika), zmiana definicji narzędzi, `tool_choice`,
  dodanie lub usunięcie obrazów, przełączniki wyszukiwania i cytowań, zmiana konfiguracji myślenia lub `effort` (zależnie od modelu).
- Sprawdzenie: pola `cache_creation_input_tokens` i `cache_read_input_tokens` w odpowiedzi; oba 0 = brak cache.
- Równoległe żądania trafiają w cache dopiero po rozpoczęciu pierwszej odpowiedzi.
- Reguły kosztowe sesji agenta: core-cost-control.

## 4. Migracja promptu na nowszy model
1. Przeczytaj przewodnik migracji dostawcy dla modelu docelowego.
2. Uruchom zestaw ewaluacji na starym i nowym modelu **z tym samym promptem**; zapisz różnice.
3. Usuń: prefill, ręczny `budget_tokens`, wielkie litery i „MUSISZ/ZAWSZE” (zamiast „CRITICAL: MUSISZ użyć narzędzia” →
   „Użyj narzędzia, gdy …”), zachęty typu „bądź dokładny, użyj wszystkich narzędzi” — nowsze modele są bardziej
   proaktywne i nadużywają narzędzi po takich zachętach.
4. Dodaj wprost, co wcześniej było domyślne, jeśli to potrzebne (np. wyraźna prośba o rozbudowany wynik).
5. Tuning pojedynczymi zmianami; wersja promptu podniesiona (MINOR przy zmianie zachowania, MAJOR przy zmianie kontraktu
   wyjścia [konwencja własna]); model przypięty w konfiguracji.

## 5. Szablony i rejestr
- Szablon: nazwa, wersja, zmienne z opisem, model docelowy, schemat wyjścia, zestaw ewaluacji, autor i data zmiany.
- Zmienne wstawiane w jednym miejscu (koniec promptu), dane w tagach; escapowanie treści użytkownika.
- Rejestr może być plikiem w repo (recenzja w PR) albo usługą; ważne: nieedytowalne wersje i powiązanie wersji z wynikami ewaluacji.
- Wdrożenie przez flagę lub konfigurację, żeby cofnięcie nie wymagało wydania kodu (ops-release-engineering).

## 6. Typowe błędy
- Niejednoznaczność: „krótko”, „profesjonalnie” bez miary → podaj długość, odbiorcę, przykład.
- Sprzeczne instrukcje po latach łatania → przegląd całości, priorytety wprost.
- Przeciążenie ograniczeniami: kilkanaście zakazów; model zaczyna odmawiać lub tłumi użyteczną treść → zostaw te, które
  zmierzone ewaluacją coś zmieniają.
- Prompt „na okazję”: instrukcja dopisana pod jeden przypadek bez dopisania przypadku do zbioru.
- Dane w instrukcjach: treść użytkownika wklejona bez tagów.

## 7. Inni dostawcy [niezweryfikowane]
Ogólne zasady (stała część na początku, przykłady w osobnym bloku, wersjonowanie, ewaluacje przy każdym wydaniu) są
wspólne; szczegóły parametrów OpenAI sprawdź w bieżącym przewodniku promptowania — strona nie była dostępna 2026-10-17.
