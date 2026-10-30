---
name: ai-product-management
description: Użyj przy decyzji o funkcji AI w produkcie — czy AI, kryteria akceptacji jako ewaluacje, koszt zadania, ryzyka, UX niepewności, wdrożenie etapowe.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy jako product manager lub właściciel produktu planujesz funkcję opartą na AI (LLM, ML) — czy AI jest właściwym narzędziem (reguła, klasyczny ML czy LLM; koszt błędów i kto go ponosi), ramowanie przez wynik i kryteria akceptacji zapisane jako ewaluacje (poprzeczka jakości, tolerancja na typ błędu, przykłady dobrych i złych wyników), cele jakości, opóźnienia i kosztu na zadanie z ekonomią jednostkową, kup, zbuduj czy użyj API, potrzeby danych, rejestr ryzyk (halucynacje, uprzedzenia, bezpieczeństwo, prywatność, prompt injection), UX niepewności i człowiek w pętli, wdrożenie etapowe (offline, dogfooding, beta, A/B), metryki produktowe a modelowe, monitoring po starcie, komunikacja z interesariuszami, sekcja PRD dla funkcji AI. Nie do odkrywania wyniku i priorytetyzacji (proc-product-discovery), PRD i MVP (proc-requirements-shaping), metody ewaluacji (ai-evals), tekstów w interfejsie (ux-content-design), klasyfikacji prawnej AI Act (ai-governance-compliance) ani wyboru architektury technicznej (arch-ai-solutions)."
  slowa: "funkcja AI, czy użyć AI, product manager AI, AI PM, wymagania dla AI, kryteria akceptacji AI, koszt na zapytanie, unit economics, koszt tokenów, kup czy zbuduj model, halucynacje ryzyko, człowiek w pętli, niepewność modelu, pokazać pewność, wdrożenie funkcji AI, beta AI, dogfooding, model się myli, asystent AI w produkcie, copilot, PRD funkcji AI, czy reguły wystarczą, komunikacja z zarządem o AI, czy warto użyć AI, AI czy zwykłe reguły, funkcja AI sama zatwierdza, kiedy AI ma sens, bezpiecznie wypuścić funkcję AI, wypuścić AI do klientów, model może się mylić, pokazać użytkownikom błędy modelu, prototyp AI, wdrożyć asystenta"
---

# Zarządzanie produktem z AI

Funkcja AI różni się od zwykłej tym, że **odpowiedź bywa błędna z natury**, a jakość jest rozkładem, nie wartością.
Zadanie PM-a: ustalić, czy AI jest tu uzasadnione, zapisać „dość dobrze” w sposób mierzalny, policzyć koszt i
zaprojektować życie z błędami. Czego **nie** robi ten skill: wynik i priorytety to **proc-product-discovery**, szkielet
PRD i budżet MVP to **proc-requirements-shaping**, metodę ewaluacji (zbiory, graderzy, CI) daje **ai-evals**.

## Procedura
1. **Czy AI?** Zacznij od najprostszego narzędzia, które zamyka problem (`references/decyzje-i-ekonomia.md`):
   reguła deterministyczna, gdy logikę da się zapisać; klasyczny ML, gdy są etykiety i stały kształt danych; LLM,
   gdy wejście jest otwartym tekstem, a wyjście wymaga rozumienia lub generowania. Test: „co się stanie, gdy
   model się pomyli, i **kto to poniesie**?” — klient, pracownik czy firma. Wysoki koszt błędu bez możliwości
   weryfikacji = nie AI albo AI tylko jako propozycja dla człowieka.
2. **Wynik, nie model.** Zapisz wynik biznesowy z miarą (proc-product-discovery) i zadanie użytkownika; model jest
   środkiem. Wskaż, co użytkownik robi dziś i ile to kosztuje — to punkt odniesienia dla modelu.
3. **Kryteria akceptacji jako ewaluacje.** Zamiast „model odpowiada poprawnie” zapisz:
   - **zbiór ewaluacyjny** (N przypadków z prawdziwych zgłoszeń, w tym brzegowe i adwersaryjne) i właściciela zbioru;
   - **poprzeczkę jakości** na metrykę, np. „≥ 90% odpowiedzi zgodnych ze źródłem”;
   - **tolerancję na typ błędu**: błędy nierówne (fałszywe zatwierdzenie zwrotu ≠ fałszywe odrzucenie); każdy typ ma
     własny limit, także „0 w kategorii X”;
   - **po 3–5 przykładów dobrego i złego wyniku** oraz wyniku granicznego, uzgodnione z ekspertem dziedziny.
   Jak zbudować zbiór, graderów i bramkę — **ai-evals**. Bez zbioru funkcja nie wchodzi do zakresu.
4. **Cele jakości, opóźnienia i kosztu.** Ustal razem: jakość (krok 3), opóźnienie (p50/p95 do pierwszego i ostatniego
   tokenu, budżet czasu użytkownika) i **koszt na udane zadanie** (nie na zapytanie: uwzględnij ponowienia, kontekst,
   sędziego, człowieka sprawdzającego). Zestaw z przychodem lub kosztem dzisiejszego procesu (unit economics:
   `references/decyzje-i-ekonomia.md`). Cele się wykluczają — zapisz, który ustępuje.
5. **Kup, zbuduj czy API.** Kolejność prób: gotowy produkt → API modelu z własnym promptem i kontekstem → dostrojenie
   → własny model. Każdy kolejny szczebel ma sens dopiero po zmierzonej luce na poprzednim. Decyzję techniczną
   i architekturę podaje **arch-ai-solutions**; PM dostarcza kryteria: dane, koszt, opóźnienie, zależność od dostawcy.
6. **Dane.** Jakie dane są potrzebne (przykłady, etykiety, treści do wyszukiwania), czy je mamy, kto jest ich
   właścicielem, czy wolno ich użyć do tego celu, jak świeże. Brak danych na zbiór ewaluacyjny to blokada, nie ryzyko.
7. **Rejestr ryzyk** (`references/ryzyka-i-ux.md`): halucynacje, uprzedzenia, bezpieczeństwo treści, prywatność,
   prompt injection, uzależnienie od dostawcy, drift. Każde: scenariusz, skutek, prawdopodobieństwo, środek, właściciel.
   Klasę regulacyjną (AI Act) i obowiązki ustala **ai-governance-compliance**; PM wpisuje wynik do rejestru.
8. **UX niepewności i człowiek w pętli** (`references/ryzyka-i-ux.md`): ustaw oczekiwania („to propozycja”), pokaż
   źródła lub pewność tylko tam, gdzie jest skalibrowana, zaprojektuj wyjście awaryjne (fallback bez AI), łatwą
   korektę i zbieranie sygnałów z poprawek do zbioru ewaluacyjnego. Teksty: **ux-content-design**.
9. **Wdrożenie etapowe.** Ewaluacja offline (bramka) → dogfooding wewnętrzny → beta z wąską grupą i wyłącznikiem →
   A/B lub shadow na części ruchu → pełne wdrożenie. Samo stopniowe zwiększanie ruchu nie zastępuje A/B ani shadow:
   potrzebne jest porównanie z grupą kontrolną na metryce produktowej. Przejście wymaga kryterium zapisanego z góry. Kill switch i
   plan wycofania gotowe przed betą (ops-release-engineering).
10. **Metryki.** Dwie warstwy: **produktowe** (ukończenie zadania, retencja, czas oszczędzony, eskalacje do człowieka —
    to one decydują) i **modelowe** (zgodność, odsetek odrzuceń, halucynacje wg ewaluacji — diagnostyka). Dobra metryka
    modelu bez ruchu metryki produktowej to nie sukces. Dodaj metryki ochronne: koszt, skargi, bezpieczeństwo.
11. **Po starcie.** Monitoruj ruch próbkami i alertami (ai-evals, ops-observability), przeglądaj porażki co tydzień,
    nowe porażki dodawaj do zbioru, a zmianę modelu lub promptu traktuj jak wydanie przez tę samą bramkę.
12. **Komunikacja.** Interesariuszom powiedz wprost: co model robi dobrze, czego nie robi, jak często się myli
    (liczba z ewaluacji z datą), co dzieje się przy błędzie, co kosztuje. Bez obietnic „100%” i bez „AI wszystko
    załatwi”. Jedna strona z trzema blokami: potrafi / nie potrafi / nie wiemy jeszcze.
13. **Zapis.** Sekcja funkcji AI w `docs/project/03-requirements/requirements.md` albo `ai-feature-brief.md`
    (szablon: `references/szablon-sekcji-prd.md`; core-project-record). Decyzję o wdrożeniu podejmuje człowiek.

## Przykład
**Wejście:** sklep chce, żeby AI zatwierdzała zwroty bez udziału obsługi (3 000 zgłoszeń/mies., 4 min pracy każde).
**Wynik (sekcja briefu):**
- Czy AI: reguły pokrywają 60% (zwrot w 14 dni, brak śladów użycia); reszta to opisy tekstowe → LLM tylko dla tej części;
- koszt błędu: fałszywe zatwierdzenie = strata towaru (firma), fałszywe odrzucenie = skarga (klient); limity:
  fałszywe zatwierdzenia ≤ 1%, odrzucenia ≤ 5% [przykład];
- tryb: model proponuje, człowiek zatwierdza zwroty > 200 zł, poniżej — automat po okresie próbnym;
- zbiór: 300 zgłoszeń z archiwum + 30 adwersaryjnych, po 4 przykłady dobre/złe/graniczne;
- cele: p95 < 6 s, koszt ≤ 0,15 zł na zgłoszenie wobec 4 min pracy [przykład];
- etapy: offline → dogfooding (obsługa, 2 tyg.) → beta 10% ruchu z kill switchem → A/B; metryka produktowa: czas
  rozpatrzenia, odsetek ponownych kontaktów; ochronna: wartość błędnie zatwierdzonych zwrotów.

## Checklista
- [ ] uzasadnione, dlaczego nie reguła; koszt błędu i jego nosiciel nazwani
- [ ] kryteria akceptacji jako ewaluacje: zbiór, poprzeczka, tolerancja na typ błędu, przykłady dobre i złe
- [ ] jakość, opóźnienie i koszt na udane zadanie razem; wskazane, co ustępuje
- [ ] dane: dostępność, prawo użycia, właściciel; rejestr ryzyk z właścicielami; klasa regulacyjna od ai-governance-compliance
- [ ] UX: oczekiwania, fallback bez AI, korekta użytkownika wraca do zbioru
- [ ] etapy z kryteriami przejścia, kill switch; metryki produktowe ponad modelowymi
- [ ] komunikat dla interesariuszy: potrafi / nie potrafi / nie wiemy; zapis w docs/project/

## Źródła
- Microsoft, „Guidelines for Human-AI Interaction” (HAX Toolkit, microsoft.com/en-us/haxtoolkit/ai-guidelines, odczyt 2026-10-17):
  18 wytycznych w czterech fazach (początek interakcji, w trakcie, gdy AI się myli, z czasem). Pełnej listy tytułów nie
  odczytano [niezweryfikowane].
- Google PAIR, „People + AI Guidebook” (pair.withgoogle.com/guidebook, strona główna nieosiągalna z tego środowiska
  2026-10-17; rozdziały Mental Models, Explainability + Trust, Feedback + Control, Errors + Graceful Failure potwierdzone
  wyszukiwaniem tego dnia; treść rozdziałów Explainability i Feedback [niezweryfikowane]).
- Etapy wdrożenia, struktura rejestru ryzyk i szablon sekcji PRD to praktyka autorów skilla [założenie].
Opisane własnymi słowami.
