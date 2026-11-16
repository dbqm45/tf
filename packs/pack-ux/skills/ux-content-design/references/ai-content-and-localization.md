# Treści funkcji z AI i lokalizacja

Spis treści: 1. Teksty funkcji z AI · 2. Proces lokalizacji · 3. Zarządzanie ciągami

## 1. Teksty funkcji z AI
| Element | Zasada | Przykład |
|---|---|---|
| Oznaczenie | od pierwszego kontaktu widać, że to AI; nazwa i opis nie udają człowieka | „Asystent AI banku” + „Odpowiada system AI, nie pracownik” |
| Możliwości i granice | 1–2 zdania: w czym pomoże, czego nie robi | „Pomogę znaleźć opłaty. Nie zmieniam limitów.” |
| Niepewność | słowami i źródłem, bez fałszywej precyzji | „Na podstawie regulaminu z 12.03.2026. Sprawdź w dokumencie.” |
| Błędy i odmowy | co się stało + co zrobić zamiast | „Nie umiem tego sprawdzić. Połącz się z konsultantem.” |
| Dane | co trafia do modelu, czy służy do uczenia | jedno zdanie + link do polityki |
| Informacja zwrotna | łatwe zgłoszenie złej odpowiedzi | „Ta odpowiedź jest zła” |
| Wyjście | zawsze droga do człowieka przy sprawach istotnych | przycisk „Porozmawiaj z konsultantem” |
Wymóg prawny: AI Act, art. 50 ust. 1 (informowanie osób, że wchodzą w interakcję z systemem AI, chyba że to oczywiste
z kontekstu); stosowany od 2 sierpnia 2026. Znakowanie treści generowanych (art. 50 ust. 2) – termin dla systemów
już na rynku wg źródeł wtórnych 2 grudnia 2026 [niezweryfikowane]. Decyzję o zakresie obowiązku zostaw prawnikowi.
Nie obiecuj „zawsze poprawnych” odpowiedzi; nie wstawiaj procentu pewności, jeśli system go nie liczy rzetelnie.

## 2. Proces lokalizacji
1. Internacjonalizacja najpierw: klucze zamiast zdań w kodzie, ICU dla liczby mnogiej i rodzaju (fe-web-platform).
2. Ciąg ma **opis dla tłumacza**: gdzie widać, limit znaków, znaczenie zmiennych, rejestr (ty/Pan).
3. Glosariusz z przewodnika stylu (terminy niezmienne, nazwy własne, zakazane kalki).
4. Pseudolokalizacja i test długości (+30–40%) przed wysłaniem do tłumaczy.
5. Tłumaczenie (człowiek lub MT + redakcja) → przegląd **w kontekście ekranu** → korekta (txt-polish-correctness dla polskiego).
6. Zmiana w źródle oznacza ciąg do ponownego tłumaczenia; nie wolno zmieniać znaczenia pod tym samym kluczem.
7. Daty, liczby, waluty, sortowanie — przez `Intl`, nie ręcznie.

## 3. Zarządzanie ciągami
- Jedno źródło prawdy (plik lub system zarządzania tłumaczeniami), klucze z przestrzeniami nazw (`billing.invoice.empty`).
- Ten sam tekst w kilku miejscach – jeden klucz, chyba że kontekst wymaga innego sformułowania.
- Statusy: nowy, do tłumaczenia, przetłumaczony, zatwierdzony; brak zatwierdzenia nie blokuje wydania, jeśli jest wersja zapasowa.
- Zmiany tekstów w PR z recenzją treści; test sprawdzający brakujące klucze w CI.
