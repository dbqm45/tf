---
name: ux-accessibility
description: Użyj przy audycie dostępności WCAG 2.2 AA, raporcie ustaleń, planie napraw, deklaracji dostępności i wymogach prawnych (EAA, EN 301 549).
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy trzeba ocenić lub zorganizować dostępność produktu cyfrowego — proces audytu WCAG 2.2 poziom AA (zakres i próba, automaty, kontrola ręczna, klawiatura, technologie asystujące NVDA, JAWS, VoiceOver, TalkBack), raport ustaleń z kryterium sukcesu, wagą i naprawą, plan napraw i priorytety, adnotacje dostępności w projekcie (nagłówki, landmarki, kolejność tabulacji, nazwy), obowiązki prawne (EN 301 549, Europejski akt o dostępności – dyrektywa (UE) 2019/882 i polska ustawa wdrażająca, deklaracja dostępności podmiotów publicznych), projekt włączający i szkolenie zespołu. Nie do kodu dostępności komponentów (fe-web-platform), ręcznych testów w QA (qa-exploratory-manual) ani ogólnego UX (ux-feature-design)."
  slowa: "audyt dostępności, dostępność cyfrowa, WCAG, WCAG 2.2, czytnik ekranu, NVDA, JAWS, VoiceOver, TalkBack, deklaracja dostępności, ustawa o dostępności, europejski akt o dostępności, EAA, EN 301 549, raport z audytu, niezgodność z WCAG, kontrast, dostępność strony, osoby niewidome, projekt włączający, adnotacje dostępności, plan napraw, zgodność z WCAG, BIP"
---

# Dostępność cyfrowa — audyt, raport, prawo, zespół

Cel: wiedzieć, **kto nie może użyć produktu i dlaczego**, naprawić w kolejności wpływu i móc to udowodnić
(raport, deklaracja). Kod komponentów (ARIA, fokus, klawiatura) — **fe-web-platform** (`.claude/skills/fe-web-platform/references/accessibility/`);
ręczne testy w sesjach QA — **qa-exploratory-manual**; ogólny UX — **ux-feature-design**.

## Procedura audytu (WCAG 2.2 AA)
1. **Cel i miara.** Poziom A+AA wg WCAG 2.2 (rekomendacja W3C z 5 października 2023). Ustal, czy audyt jest wymagany
   prawnie (sekcja Prawo) i jaką normę wskazuje umowa lub przepis — w UE norma EN 301 549.
2. **Zakres i próba** wg metodyki W3C **WCAG-EM**: określ zakres (domena, aplikacja, wersje językowe), poznaj serwis,
   dobierz **reprezentatywną próbę** (strona główna, kluczowe ścieżki: logowanie, zakup, formularz kontaktowy,
   wyszukiwarka, strona z tabelą, dokument PDF, komponenty złożone: modal, menu, kalendarz) plus losowe strony do
   sprawdzenia, czy wybór nie jest zbyt optymistyczny. Zapisz wersję, adres, przeglądarki, daty. Próba nie daje
   gwarancji zgodności całości — raport tak mówi.
3. **Automaty** (axe, WAVE, Lighthouse, Pa11y) na całej próbie: szybki wynik, ale łapią tylko część problemów
   (rząd 30–40% [niezweryfikowane]); brak błędów nie znaczy zgodności.
4. **Kontrola ręczna** każdej strony z próby: sama klawiatura (kolejność, widoczny fokus, brak pułapek, skróty),
   powiększenie 200% i reflow 320 px, kontrast tekstu 4,5:1 i elementów 3:1, odstępy tekstu, treści po najechaniu,
   alternatywy tekstowe, nagłówki i landmarki, formularze (etykiety, błędy, autouzupełnianie), multimedia (napisy,
   transkrypcja), ruch i animacje, cele dotykowe ≥ 24×24 px, nowe w 2.2: 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8.
5. **Technologie asystujące** na ścieżkach krytycznych — minimum dwie pary: NVDA lub JAWS z przeglądarką na
   Windows oraz VoiceOver (Safari) na macOS/iOS; przy aplikacji mobilnej TalkBack na Androidzie. Sprawdź nazwy, role,
   stany, komunikaty dynamiczne, kolejność czytania. Najlepiej z udziałem osób, które na co dzień z nich korzystają.
6. **Raport** wg `references/audyt-i-raport.md`: dla każdego ustalenia numer, kryterium sukcesu (np. 1.4.3), poziom,
   miejsce (adres, element, zrzut), opis i wpływ na użytkownika, **waga** (krytyczna / poważna / umiarkowana / niska),
   zalecenie naprawy, sposób weryfikacji. Najpierw podsumowanie: zakres, metoda, liczba ustaleń wg wagi, wnioski.
7. **Plan napraw.** Priorytet = waga × zasięg (ścieżka krytyczna, liczba stron) ÷ koszt; najpierw bariery blokujące
   zadanie (brak dostępu z klawiatury, brak etykiet w formularzu płatności), potem rozwiązania w komponentach
   (jedna poprawka w systemie projektowym zamyka wiele ustaleń), na końcu pojedyncze strony. Do każdej naprawy test
   regresji i kryterium „gotowe” (DoD komponentu).
8. **Powtórka** po naprawach na tych samych stronach i ścieżkach; aktualizacja raportu i, jeśli dotyczy, deklaracji.

## Adnotacje dostępności w projekcie (przed kodem)
Do specyfikacji ekranu (ux-feature-design, handoff) dopisz: strukturę nagłówków (jedno `h1`, brak skoków), landmarki
(`header`, `nav`, `main`, `footer`, `aside` z nazwą, gdy jest kilka), **kolejność fokusu** (numerowana na makiecie),
nazwy dostępne przycisków i pól (zgodne z widocznym tekstem), komunikaty (rola `status` lub `alert`), gdzie wraca
fokus po zamknięciu okna, alternatywy tekstowe, kontrasty z tokenów, zachowanie przy powiększeniu. Zadania na etapie
projektu są tańsze niż naprawy po wdrożeniu. Treści dostępne — ux-content-design.

## Prawo (stan sprawdzony 2026-10-17, szczegóły: `references/prawo-i-deklaracja.md`)
- **Europejski akt o dostępności** — dyrektywa (UE) 2019/882, stosowana od **28 czerwca 2025**; w Polsce ustawa z dnia
  26 kwietnia 2024 r. o zapewnianiu spełniania wymagań dostępności niektórych produktów i usług przez podmioty
  gospodarcze (Dz.U. 2024 poz. 731). Dotyczy m.in. handlu elektronicznego, bankowości detalicznej, usług
  telekomunikacyjnych, e-booków, transportu pasażerskiego; usługi mikroprzedsiębiorców są wyłączone (nie produkty).
- **Podmioty publiczne** — ustawa z dnia 4 kwietnia 2019 r. o dostępności cyfrowej stron internetowych i aplikacji
  mobilnych podmiotów publicznych (Dz.U. 2019 poz. 848; tekst jednolity Dz.U. 2023 poz. 82 — sprawdź aktualny):
  wymagania WCAG 2.1 AA, **deklaracja dostępności** na stronie, coroczny przegląd.
- **EN 301 549** — norma europejska dla ICT; wersja V3.2.1 wskazuje WCAG 2.1 AA, V4.1.1 (WCAG 2.2) opublikowana
  2 września 2026, a do uzyskania domniemania zgodności musi być przywołana w Dz.Urz. UE [niezweryfikowane — źródła wtórne].
  Wymóg prawny to więc obecnie WCAG 2.1 AA; stosuj 2.2 AA jako cel wyprzedzający.

## Projekt włączający i zespół
- Projektuj dla spektrum: trwała, czasowa i sytuacyjna niepełnosprawność (ux-feature-design, projekt włączający). Badania
  z osobami z niepełnosprawnościami, zapłata za udział, dostępne narzędzia badawcze.
- Dostępność jako **definicja ukończenia** komponentu i zadania, nie faza na końcu. Role: projektant (kontrast,
  adnotacje), autor treści (linki, nagłówki, alternatywy), programista (semantyka, klawiatura), QA (ścieżki z czytnikiem).
- Szkolenie: warsztat z klawiaturą i czytnikiem ekranu (30 minut własnego doświadczenia przekonuje bardziej niż slajdy),
  checklista roli, wyznaczona osoba (champion), mierzone ustalenia na sprint. Plan: `references/zespol-i-szkolenie.md`.

## Przykład
Wejście: „Sklep z butami (45 osób, Polska), formularz zamówienia: pola bez etykiet, błąd tylko na czerwono.”

Wynik (fragment raportu):

| ID | SC | Waga | Ustalenie | Naprawa |
|---|---|---|---|---|
| A-007 | 3.3.2 / 1.3.1 (A) | krytyczna | Pole „Kod pocztowy” ma tylko placeholder; NVDA czyta „edycja”. Dotyczy 4 z 4 kroków zamówienia | `label` powiązany z polem, placeholder jako podpowiedź |
| A-008 | 1.4.1 (A), 3.3.1 (A) | poważna | Błąd oznaczony kolorem; brak tekstu błędu | Tekst „Wpisz kod w formacie 00-000” + `aria-describedby` |

Plan: A-007 i A-008 jako jedna poprawka w komponencie pola (system projektowy) — zamyka 11 z 23 ustaleń; wdrożenie przed
kolejnym wydaniem. Obowiązek: sklep (50 osób) podlega ustawie z 26.04.2024 od 28.06.2025.

## Checklista
- [ ] cel i norma ustalone (WCAG 2.2 AA; w UE EN 301 549), zakres i próba wg WCAG-EM zapisane
- [ ] automaty + kontrola ręczna + klawiatura + co najmniej dwie technologie asystujące
- [ ] każde ustalenie: kryterium sukcesu, waga, miejsce, wpływ, naprawa, weryfikacja
- [ ] plan napraw wg wagi i zasięgu; poprawki w komponentach przed pojedynczymi stronami
- [ ] adnotacje dostępności w specyfikacji projektu
- [ ] obowiązek prawny rozpoznany; deklaracja dostępności (podmioty publiczne) aktualna
- [ ] DoD z dostępnością, szkolenie, powtórka po naprawach

## Materiały dodatkowe
- `references/audyt-i-raport.md` — szablon raportu, skala wagi, zestaw ręcznych kontroli i par czytnik–przeglądarka; czytaj przy audycie.
- `references/prawo-i-deklaracja.md` — EAA, polskie ustawy, EN 301 549, treść deklaracji dostępności; czytaj przy pytaniu o obowiązki.
- `references/zespol-i-szkolenie.md` — DoD, role, plan szkolenia, metryki; czytaj przy wdrażaniu dostępności w zespole.

## Źródła
- W3C, WCAG 2.2 (rekomendacja z 5 października 2023; 4.1.1 Parsing usunięte) i WCAG-EM (metodyka oceny) — potwierdzone
  wyszukiwaniem wtórnym, strony W3C niedostępne w sesji 2026-10-17 [niezweryfikowane u źródła].
- Dyrektywa (UE) 2019/882 (EAA), stosowanie od 28 czerwca 2025 — EUR-Lex niedostępny w sesji; potwierdzone przez
  źródła wtórne (dostęp 2026-10-17) [niezweryfikowane u źródła].
- Ustawa z 26 kwietnia 2024 r. (Dz.U. 2024 poz. 731, wejście w życie art. 88 – 28 czerwca 2025; nadzór: prezes PFRON
  i organy sektorowe) — eli.gov.pl i wyniki wyszukiwania, dostęp 2026-10-17.
- Ustawa z 4 kwietnia 2019 r. (Dz.U. 2019 poz. 848, t.j. Dz.U. 2023 poz. 82), gov.pl/web/dostepnosc-cyfrowa — wyniki
  wyszukiwania, dostęp 2026-10-17; termin corocznego przeglądu „do 31 marca” tylko ze źródeł wtórnych [niezweryfikowane].
- ETSI EN 301 549 V3.2.1 (2021) i V4.1.1 (publikacja 2 września 2026) — źródła wtórne (Deque, NDA), dostęp 2026-10-17.
Opisane własnymi słowami.
