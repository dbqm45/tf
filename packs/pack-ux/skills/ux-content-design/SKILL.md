---
name: ux-content-design
description: Użyj przy treściach w produkcie jako projekcie — głos i ton, przewodnik stylu, prosty język, mikrotekst, modele treści, lokalizacja, testy treści.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj, gdy treść produktu trzeba zaprojektować, a nie tylko napisać — głos i ton, przewodnik stylu treści, prosty język (w tym polski „prosty język”), wzorce mikrotekstu (błędy, puste stany, potwierdzenia, przyciski, onboarding, powiadomienia), modele i wzorce treści, projektowanie od treści (prawdziwa treść przed układem), proces lokalizacji i zarządzanie ciągami tekstu, testy treści (cloze, highlighter, zadania na zrozumienie), treści dostępne, teksty funkcji z AI (oznaczenie AI, niepewność, ograniczenia). Nie do podstawowych tekstów UI w specyfikacji ekranu (ux-feature-design), korekty i redakcji polszczyzny (txt-polish-correctness, txt-polish-style), dokumentacji technicznej (docs-tech-writing) ani samej mechaniki i18n w kodzie (eng-i18n, fe-web-platform)."
  slowa: "UX writing, content design, mikrotekst, microcopy, komunikat błędu, pusty stan, tekst przycisku, głos marki, ton komunikacji, przewodnik stylu, content style guide, prosty język, zrozumiały tekst, czy użytkownicy rozumieją, test cloze, lokalizacja, tłumaczenie aplikacji, klucze tłumaczeń, treść przed makietą, lorem ipsum, model treści, asystent AI teksty, oznaczenie AI, czy klienci rozumieją tekst, zrozumiałość treści, test zrozumienia tekstu, regulamin prostym językiem, nowa treść"
---

# Projektowanie treści produktu

Treść to część interfejsu, nie dekoracja. Zaczynasz od zadania użytkownika i prawdziwych słów, które pomagają je wykonać,
nie od pustej makiety. Podstawowe reguły tekstów UI (czasownik na przycisku, błąd: co się stało i co zrobić, pusty
stan) są w **ux-feature-design** (`.claude/skills/ux-feature-design/references/tresci-i-etyka.md`) — tu je rozwijasz do systemu i sprawdzasz na ludziach.

## Procedura
1. **Zadanie i odbiorca.** Kto, w jakiej sytuacji (pośpiech, stres, telefon w ruchu), co chce zrobić, co już wie.
   Brak badań → zapytaj albo oznacz [założenie]. Metody badań — ux-research-methods.
2. **Treść przed układem.** Napisz prawdziwe teksty dla najdłuższego, najkrótszego i typowego przypadku, dopiero
   potem układaj ekran. Zamiast „lorem ipsum” — dane z produkcji (zanonimizowane). Dla stron z wieloma typami
   stron zbuduj **model treści**: typy (np. artykuł pomocy), pola (tytuł ≤ 60 znaków, lead, kroki, ostrzeżenie),
   reguły (obowiązkowe/opcjonalne), relacje. Jeden typ = jeden wzorzec, więc autorzy nie wymyślają układu za każdym razem.
3. **Głos i ton.** Głos jest stały (3–4 cechy, każda z parą „jest / nie jest”: „rzeczowy, nie sztywny”), ton zmienia się
   z sytuacją użytkownika (błąd płatności ≠ sukces). Wybierz jedną formę zwracania się (ty / Pan, Pani / bezosobowo)
   i trzymaj ją w całym produkcie. Pełna procedura i szablon: `references/przewodnik-stylu-i-mikrotekst.md`.
4. **Prosty język.** Zdania średnio do ok. 15–20 słów, strona czynna, jedno pojęcie = jedna nazwa, ważne na początku,
   liczby i terminy konkretne, bez rzeczowników odczasownikowych („dokonać weryfikacji” → „sprawdzić”). Dla treści
   urzędowych i prawnych dodaj obok oryginału wersję w prostym języku. To nie upraszczanie treści, tylko usuwanie
   przeszkód. Redakcja polszczyzny — txt-polish-style, poprawność — txt-polish-correctness.
5. **Mikrotekst wg wzorca.** Dla każdego stanu z tabeli stanów (ux-feature-design): błąd (co się stało → dlaczego → co zrobić,
   przy polu), pusty stan (dlaczego pusto → pierwszy krok), potwierdzenie (skutek → czasownik na przycisku), onboarding
   (jedna rzecz na ekran, wartość przed funkcją), powiadomienie (po co teraz → czego oczekujemy → jak wyłączyć).
   Wzorce z przykładami i antywzorcami: `references/przewodnik-stylu-i-mikrotekst.md`.
6. **Treść dostępna.** Tekst linku sensowny bez kontekstu („Pobierz fakturę 03/2026”, nie „Kliknij tutaj”), nagłówki
   opisują sekcję, komunikat nie opiera się wyłącznie na kolorze lub ikonie, alternatywy tekstowe mówią funkcję, skróty
   rozwinięte przy pierwszym użyciu, język strony i fragmentów obcych oznaczony. Audyt dostępności — ux-accessibility.
7. **Funkcje z AI.** Powiedz wprost, że odpowiada AI (od 2 sierpnia 2026 wymóg art. 50 ust. 1 AI Act, gdy użytkownik
   mógłby wziąć system za człowieka), co potrafi i czego nie, skąd bierze odpowiedzi, że może się mylić i co sprawdzić
   (pewność wyrażona słowami i źródłem, nie fałszywą precyzją „97%”). Dawaj wyjście: poprawienie, kontakt z człowiekiem,
   zgłoszenie błędnej odpowiedzi. Szczegóły: `references/tresci-ai-i-lokalizacja.md`.
8. **Lokalizacja.** Teksty trzymaj w kluczach z opisem dla tłumacza (gdzie widać, limit znaków, zmienne), bez sklejania
   zdań z fragmentów; liczba mnoga i rodzaj przez ICU MessageFormat (mechanika — fe-web-platform, `i18n.md`). Zapas na
   długość (niemiecki, polski dłuższe niż angielski), glosariusz, przegląd w kontekście ekranu. Proces:
   `references/tresci-ai-i-lokalizacja.md`.
9. **Test treści** przed wydaniem, dopasowany do pytania:
   - **cloze** — wytnij co 5.–6. słowo, badany uzupełnia luki; wynik ok. 60% i więcej oznacza zrozumiały tekst dla tej grupy;
   - **highlighter** — badani zaznaczają zielonym to, co jasne i budzi zaufanie, a czerwonym to, co niejasne lub
     niepokojące; liczysz, które fragmenty dostały czerwień u wielu osób;
   - **zadanie na zrozumienie** — „Co się stanie po kliknięciu?”, „Ile zapłacisz?”, odpowiedź własnymi słowami.
   5–8 osób na grupę wystarcza do znalezienia głównych problemów. Wskaźniki czytelności (np. Flesch) to najwyżej sygnał.
   Szczegóły: `references/testy-tresci.md`.
10. **Wynik.** Przewodnik stylu (lub aktualizacja), teksty z kluczami i opisami, lista decyzji o słowach, wyniki testu
    z poprawkami. Kolejne iteracje: zmiana tekstu to zmiana w kodzie, przechodzi przegląd jak PR.

## Przykład
Wejście: „Aplikacja do faktur: komunikat »Błąd 422. Nieprawidłowe dane.« po zapisie faktury z pustym NIP-em.”

Wynik:
- Pole NIP: „Wpisz NIP nabywcy — 10 cyfr, bez kresek.” (co zrobić, przy polu, bez kodu)
- Podsumowanie nad formularzem: „Faktura nie została zapisana. Popraw 2 pola: NIP, Data sprzedaży.” — linki do pól.
- Kod 422 tylko w szczegółach dla wsparcia („Kod: INV-422”).
- Test: highlighter na 6 osobach; 4 zaznaczyły „nabywcy” na czerwono → zamiana na „klienta”, zgodnie ze słownikiem
  produktu. Nazwa „klient” zapisana w przewodniku stylu i w glosariuszu tłumaczeń.

## Checklista
- [ ] zadanie i odbiorca nazwane; teksty napisane na prawdziwych danych, także skrajnych
- [ ] głos (3–4 cechy), ton wg sytuacji, jedna forma zwracania się, słownik pojęć
- [ ] mikrotekst wg wzorców dla każdego stanu; kody błędów tylko jako identyfikator dla wsparcia
- [ ] prosty język; treści prawne i urzędowe z wersją w prostym języku
- [ ] treść dostępna (linki, nagłówki, alternatywy, nie tylko kolor)
- [ ] funkcje z AI: oznaczenie, ograniczenia, niepewność, wyjście do człowieka
- [ ] klucze i opisy dla tłumaczy, ICU, zapas długości; przegląd w kontekście
- [ ] test treści (cloze, highlighter lub zadanie) albo jawne „nie testowano”

## Materiały dodatkowe
- `references/przewodnik-stylu-i-mikrotekst.md` — szablon przewodnika stylu, głos i ton, wzorce mikrotekstu; czytaj przy pisaniu tekstów.
- `references/testy-tresci.md` — przebieg cloze, highlightera i zadań na zrozumienie, interpretacja; czytaj przed testem.
- `references/tresci-ai-i-lokalizacja.md` — teksty funkcji z AI, proces lokalizacji i zarządzanie ciągami; czytaj przy tych tematach.

## Źródła
- GOV.UK, Content design guidance — „Writing for GOV.UK” i „Content design: planning, writing and managing content”
  (design/content guidance; zasady: potrzeby użytkownika, prosty angielski). Tylko źródła wtórne, strony pierwotne
  niedostępne w sesji 2026-10-17 [niezweryfikowane].
- NN/g — testy treści (cloze, highlighter) opisane w źródłach wtórnych jako metody z książki Nielsen, Budiu,
  *Mobile Usability*; próg ok. 60% dla cloze [niezweryfikowane] (dostęp 2026-10-17).
- KPRM, *Komunikacja pisemna. Rekomendacje* (2. wyd. 2017, gov.pl) i materiały „Prosto i kropka” — polski prosty język
  (dostęp 2026-10-17, przez wyszukiwanie).
- Rozporządzenie (UE) 2024/1689 (AI Act), art. 50 — obowiązki przejrzystości; stosowanie od 2 sierpnia 2026, przy czym
  obowiązek znakowania treści z art. 50 ust. 2 dla systemów już na rynku przesunięty do 2 grudnia 2026 przez pakiet
  Digital Omnibus (rozporządzenie 2026/1744) — źródła prawnicze wtórne (dostęp 2026-10-17) [niezweryfikowane w Dz.Urz. UE].
Opisane własnymi słowami.
