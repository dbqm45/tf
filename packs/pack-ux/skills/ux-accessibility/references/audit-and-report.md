# Audyt dostępności — raport, waga, kontrole

Spis treści: 1. Szablon raportu · 2. Skala wagi · 3. Kontrole ręczne · 4. Pary czytnik–przeglądarka · 5. Plan napraw

## 1. Szablon raportu
1. **Podsumowanie** (pół strony): zakres, norma i poziom (WCAG 2.2 A+AA), data, wersja produktu, liczba ustaleń wg wagi,
   3 najważniejsze bariery, ocena ogólna słowami („częściowo zgodny: 5 barier blokujących zakup”).
2. **Zakres i metoda**: adresy z próby i powód wyboru (WCAG-EM), narzędzia z wersjami, przeglądarki, technologie asystujące,
   ograniczenia (czego nie sprawdzono: treści za logowaniem, PDF-y, aplikacja mobilna).
3. **Ustalenia** — tabela lub karty: `ID | Kryterium sukcesu (numer, poziom) | Waga | Miejsce (URL, element, zrzut) | Opis i wpływ na użytkownika | Zalecenie | Jak sprawdzić po naprawie`.
4. **Zgodność z kryteriami**: tabela kryteriów A+AA ze statusem: spełnione / niespełnione / nie dotyczy / nie sprawdzono.
5. **Mocne strony** (co zachować) i **plan napraw** (sekcja 5).
Jedno ustalenie = jeden problem w jednym wzorcu; to samo w 30 miejscach to jedno ustalenie z listą miejsc.
Opis wpływu pisz o człowieku: „osoba niewidoma nie dowie się, które pole jest błędne”, nie „brak aria-describedby”.

## 2. Skala wagi (własna; dopasuj do umowy)
| Waga | Kryterium | Przykład |
|---|---|---|
| Krytyczna | uniemożliwia wykonanie zadania w ścieżce kluczowej | formularz płatności niedostępny z klawiatury |
| Poważna | bardzo utrudnia lub wymaga obejścia | brak etykiet pól, kontrast przycisku 2:1 |
| Umiarkowana | utrudnia, jest obejście | niejasna kolejność nagłówków |
| Niska | drobna niedogodność, ryzyko przy zmianie | nadmiarowy tekst alternatywny |
Waga bierze pod uwagę zasięg (ścieżka kluczowa czy zakątek serwisu) i dotknięte grupy. Wagi nie mylić z poziomem A/AA
kryterium.

## 3. Kontrole ręczne (zestaw na stronę z próby)
- Klawiatura: Tab/Shift+Tab przechodzi wszystko, kolejność zgodna z układem, fokus zawsze widoczny i nie zasłonięty (2.4.7, 2.4.11),
  brak pułapki, Escape zamyka nakładki, skróty jednoznakowe da się wyłączyć (2.1.4).
- Powiększenie 200% oraz reflow przy szerokości 320 px bez przewijania w dwóch kierunkach (1.4.4, 1.4.10); odstępy tekstu (1.4.12).
- Kontrast: tekst 4,5:1 (duży 3:1), elementy interfejsu i fokus 3:1 (1.4.3, 1.4.11).
- Treść: nagłówki, landmarki, tytuł strony, język (`lang`), alternatywy tekstowe, linki zrozumiałe poza kontekstem (2.4.4).
- Formularze: etykiety, wymagane pola, błędy tekstem z sugestią, autouzupełnianie (1.3.5), brak ponownego wpisywania (3.3.7),
  uwierzytelnianie bez testu poznawczego (3.3.8).
- Multimedia: napisy, transkrypcja, audiodeskrypcja tam, gdzie obraz niesie treść; brak autoodtwarzania z dźwiękiem.
- Ruch: możliwość wstrzymania, brak błysków (> 3 na sekundę), alternatywa dla przeciągania (2.5.7), cele ≥ 24×24 px (2.5.8).
- Dynamika: komunikaty statusu ogłaszane bez zabierania fokusu (4.1.3).

## 4. Pary czytnik–przeglądarka (typowy zestaw testowy)
NVDA + Firefox lub Chrome (Windows), JAWS + Chrome (Windows), VoiceOver + Safari (macOS, iOS), TalkBack + Chrome (Android).
Dobór pary według tego, z czego korzystają odbiorcy (ankieta WebAIM o czytnikach – sprawdź aktualną edycję [niezweryfikowane]).
Zapisuj wersję czytnika i przeglądarki w raporcie; niezgodności między parami często wynikają z błędów czytnika.

## 5. Plan napraw
Tabela: `ID ustaleń | Naprawa | Właściciel | Wysiłek | Termin | Weryfikacja`. Kolejność: (1) bariery blokujące zadanie,
(2) poprawki w komponentach i szablonach, (3) pozostałe na ścieżkach kluczowych, (4) reszta. Ustalenia, których nie da
się naprawić przed terminem prawnym, trafiają do deklaracji jako niezgodności z planem i datą.
