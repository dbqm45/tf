# Przewodnik stylu treści i wzorce mikrotekstu

Spis treści: 1. Szablon przewodnika · 2. Głos i ton · 3. Wzorce mikrotekstu · 4. Antywzorce

## 1. Szablon przewodnika stylu (`docs/content-guide.md`)
Krótki dokument, nie podręcznik. Sekcje:
1. **Cel i odbiorcy** — dla kogo piszemy, w jakich sytuacjach (2–3 persony lub sytuacje).
2. **Głos** — 3–4 cechy, każda w formie „jesteśmy X, nie Y” z przykładem zdania „tak” i „nie”.
3. **Ton wg sytuacji** — tabela: sytuacja (sukces, błąd, ostrzeżenie, płatność, pierwsze użycie) → ton → przykład.
4. **Forma zwracania się** — jedna decyzja (ty / Pan, Pani / bezosobowo) i wyjątki.
5. **Słownik** — pojęcie preferowane, zakazane synonimy, definicja jednym zdaniem (zgodny ze słownikiem domeny
   z ddd-facilitation; ta sama lista zasila glosariusz tłumaczeń).
6. **Zasady pisania** — długość zdań, strona czynna, liczby i daty (format), wielkie litery, skróty, emoji.
7. **Wzorce** — gotowe szkielety z p. 3; każdy z przykładem dobrym i złym.
8. **Proces** — kto zatwierdza, jak zmieniać (PR), jak zgłaszać wyjątki.
Przegląd tekstów w PR jak kodu; polszczyzna — txt-polish-correctness i txt-polish-style.

## 2. Głos i ton
- Głos stały: np. „rzeczowy, nie zimny”; „życzliwy, nie poufały”; „konkretny, nie żargonowy”.
- Ton zmienny: im większy stres użytkownika (utrata pieniędzy, danych), tym mniej żartów, więcej konkretu i wyjścia.
- Humor tylko w sytuacjach bez ryzyka i bez kosztu dla osoby, która czyta po raz dziesiąty.
- Test: czy zdanie można powiedzieć głośno osobie przy okienku? Jeśli nie, przepisz.

## 3. Wzorce mikrotekstu
| Element | Szkielet | Przykład |
|---|---|---|
| Błąd pola | co poprawić + wymóg | „Wpisz NIP — 10 cyfr, bez kresek” |
| Błąd systemu | co się stało + czy dane bezpieczne + co dalej | „Nie udało się zapisać faktury. Twoje zmiany zostały w formularzu. Spróbuj za chwilę lub napisz do nas.” |
| Pusty stan | dlaczego pusto + pierwszy krok + przycisk | „Nie masz jeszcze klientów. Dodaj pierwszego albo zaimportuj plik CSV.” |
| Pusty wynik wyszukiwania | co znaleziono (nic) + wskazówka | „Brak wyników dla „fakt”. Sprawdź pisownię lub szukaj po numerze.” |
| Potwierdzenie | skutek + czasownik | „Usunąć projekt „Dom”? Usuniesz też 12 zadań.” → [Usuń projekt] [Anuluj] |
| Przycisk | czasownik + dopełnienie | „Wyślij fakturę”, nie „OK” |
| Sukces | co się stało + co dalej (opcjonalnie) | „Faktura 03/2026 wysłana do Jan Kowalski.” |
| Onboarding | jedna rzecz na ekran, korzyść przed funkcją | „Wystaw pierwszą fakturę w 2 minuty” |
| Powiadomienie | kto/co + czego dotyczy + akcja | „Klient zapłacił fakturę 03/2026. Zobacz płatność” |
| Zgoda | co, po co, jak wycofać; opcje równorzędne | „Wysyłać przypomnienia o terminach? Możesz to wyłączyć w Ustawieniach.” |

## 4. Antywzorce
- „Wystąpił nieoczekiwany błąd” bez dalszego kroku; „Nieprawidłowe dane”; kod zamiast zdania.
- Obwinianie: „Podałeś zły numer” → „Numer ma 9 cyfr, potrzeba 10”.
- „Przepraszamy za niedogodności” zamiast pomocy; wykrzykniki i „Ups!” przy utracie danych.
- Przyciski „Tak” / „Nie” na pytaniu z negacją; „Anuluj” niejasne (anulować akcję czy zamknąć okno?).
- Ta sama rzecz pod trzema nazwami (zamówienie, order, transakcja).
- Tekst jako obrazek lub tekst sklejany z fragmentów w kodzie (psuje tłumaczenie i czytniki ekranu).
