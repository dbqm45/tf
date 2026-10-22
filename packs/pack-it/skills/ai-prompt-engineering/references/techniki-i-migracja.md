# Techniki i migracja — stan na 2026-10-17

Spis treści: 1. Myślenie · 1a. Modele Claude 5.5 · 2. Prefill i format · 3. Cache · 4. Migracja · 5. Szablony i rejestr · 6. Błędy · 7. Inne dostawcy

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

## 1a. Modele Claude 5.5 (przewodniki „Prompting Claude Opus/Sonnet/Haiku 5.5”, odczyt 2026-10-20)
- `effort` to główna kontrola myślenia (na Opus 5.5 myślenie jest zawsze włączone); domyślnie `medium` na Opus,
  Sonnet i Haiku 5.5 — ustaw jawnie i porównaj kilka poziomów na własnych ewaluacjach. `xhigh` i `max` tylko tam,
  gdzie zmierzono zysk; mniej myślenia → najpierw niższy `effort`, nie instrukcja w prompcie.
- Myślenie liczy się do `max_tokens`, także gdy treść myślenia nie wraca: limit ustawiony pod starszy model ucina
  odpowiedzi. W długich turach agentowych na Opus 5.5 dobrze działało 128 000 (maksimum modelu).
- Zmiana `effort` między żądaniami unieważnia cache; zmiana w trakcie rozmowy bez utraty cache — per-message effort
  (beta).
- Agent bez nadzoru: tura zakończona samym tekstem (podsumowanie z zapowiedzią kroku) to raport, nie koniec zadania —
  lista otwartych pozycji i krótka wiadomość „kontynuuj” (core-async-delegation).
- Sonnet 5.5 na `low`/`medium` bywa, że pyta przed końcem pracy, a na każdym poziomie dodaje niezamówione testy
  i dokumentację; Haiku 5.5 przy długim prompcie agenta na `low` kończy za wcześnie. Pomaga instrukcja: „pracuj, aż
  wszystko jest zrobione; zatrzymaj się tylko bez decyzji człowieka albo przed ryzykownym krokiem; po sprawdzeniu
  zgłoś wynik, a pomysły na dodatki wymień na końcu” (fabryka: `work_contract` w `factory/config.yaml`).

## 2. Prefill i format wyjścia
- Prefill ostatniej wiadomości asystenta nie jest obsługiwany od modeli Claude 4.6 (żądanie zwraca błąd).
- Zamienniki: wymuszony format (JSON, YAML, klasyfikacja) → structured outputs ze schematem;
  pominięcie wstępu → instrukcja „odpowiadaj bezpośrednio, bez wstępu”, tag wyjściowy lub wywołanie narzędzia;
  kontynuacja przerwanej odpowiedzi → wiadomość użytkownika z końcówką poprzedniej odpowiedzi;
  odświeżanie kontekstu w długiej rozmowie → przypomnienie w turze użytkownika albo narzędzie dostarczające kontekst.
- Kontrakt wyjścia, walidacja po odbiorze i obsługa porażki: eng-llm-features §2.

## 3. Układ pod cache (Anthropic)
Mechanikę cache API (kolejność `tools` → `system` → `messages`, `cache_control`, TTL, ceny zapisu i odczytu, minimalna
długość prefiksu, co unieważnia) opisuje aktualnie wbudowany skill `claude-api`; reguły kosztowe sesji agenta:
core-cost-control. Dla promptu liczy się jedno: część stała na początku, zmienna na końcu, a trafienia sprawdzasz
w polach `cache_creation_input_tokens` i `cache_read_input_tokens` (oba 0 = brak cache).

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
