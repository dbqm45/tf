---
artifact: test-plan
phase: plan
status: draft
version: 1
author: kasia
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md]
---
# Plan testów: wycena pozycji zamówienia — rabat ilościowy (H1)

## TL;DR
14 przypadków testowych (clean-room, bez wglądu w src/pricing.ts) pokrywających H1-AC1..AC5: klasy równoważności i
wartości brzegowe ilości (0, 1, 9, 10, 11, 49, 50, 51, wartości niecałkowite, ujemne), zaokrąglanie .5 grosza w górę
przy 5% i 10% rabatu (wyliczone ręcznie), oraz przykład sprzedaży (10 szt. × 1999 gr → 18991 gr). Najwyższe ryzyko:
błąd „o jeden” na progach 10/50 i błędne zaokrąglanie połówek grosza — obie klasy pokryte kilkoma przypadkami.
3 otwarte pytania dot. mechanizmu błędu (AC4) i dopuszczalnych wartości ceny jednostkowej — oznaczone propozycjami,
nie blokują automatyzacji. Poziom testu: jednostkowy (czysta logika obliczeniowa); dobre kandydaty na property-based
(fast-check) dla właściwości „rabat nigdy nie zwiększa ceny”, „wynik zawsze ≥ 0” i testy mutacyjne (Stryker) na
granicach progów.

## Zakres i ryzyka
| Obszar / wymaganie | Wpływ | Prawdopodobieństwo | Ryzyko | Techniki | Poziom |
|---|---|---|---|---|---|
| Progi 10 i 50 szt. (AC2, AC3) | Wysoki (błędna kwota na fakturze) | Średnie (klasyczny błąd o jeden) | Wysokie | wartości brzegowe | jednostkowy |
| Zaokrąglanie .5 gr (AC5) | Wysoki (rozjazd groszowy przy skali) | Średnie (zależy od implementacji round) | Wysokie | wyliczenie ręczne + brzegowe | jednostkowy |
| Walidacja ilości (AC4) | Średni (błędne dane wejściowe) | Wysokie (wiele źródeł wejścia) | Wysokie | klasy równoważności | jednostkowy |
| Brak sumowania rabatów (AC3) | Średni | Niskie | Średnie | tablica decyzyjna (2 progi) | jednostkowy |

## Przypadki testowe
Oczekiwany wynik pochodzi ze źródła — nigdy z kodu (qa-spec-first-testing).

| ID | Wymaganie | Technika | Warunki wstępne | Kroki / wejście | Oczekiwany wynik | Źródło wyniku | Poziom | Auto/ręczny | Priorytet |
|---|---|---|---|---|---|---|---|---|---|
| TC-001 | H1-AC1 | wartość brzegowa (min ważna) | — | qty=1, cena=1999 gr | 1999 gr | AC1: poniżej 10 szt. brak rabatu; wartość = 1×1999 | jednostkowy | auto | H |
| TC-002 | H1-AC1 | wartość brzegowa (tuż pod progiem 10) | — | qty=9, cena=1999 gr | 17991 gr | AC1 + wyliczenie: 9×1999=17991, brak rabatu | jednostkowy | auto | H |
| TC-003 | H1-AC2, H1-AC5 | wartość brzegowa (próg 10) + przykład sprzedaży | — | qty=10, cena=1999 gr | 18991 gr | Przykład od działu sprzedaży w requirements.md: 10×19,99 zł − 5% = 189,905 zł → 189,91 zł = 18991 gr | jednostkowy | auto | H |
| TC-004 | H1-AC2 | wartość brzegowa (tuż nad progiem 10) | — | qty=11, cena=1999 gr | 20890 gr | Wyliczenie: 11×1999=21989; 21989×0,95=20889,55 → zaokr. do 20890 gr | jednostkowy | auto | H |
| TC-005 | H1-AC2 | wartość brzegowa (tuż pod progiem 50) | — | qty=49, cena=1999 gr | 93053 gr | Wyliczenie: 49×1999=97951; 97951×0,95=93053,45 → zaokr. do 93053 gr (rabat wciąż 5%, nie 10%) | jednostkowy | auto | H |
| TC-006 | H1-AC3 | wartość brzegowa (próg 50) | — | qty=50, cena=1999 gr | 89955 gr | Wyliczenie: 50×1999=99950; 99950×0,90=89955 (dokładne, bez zaokrąglenia) | jednostkowy | auto | H |
| TC-007 | H1-AC3 | wartość brzegowa (tuż nad progiem 50) | — | qty=51, cena=1999 gr | 91754 gr | Wyliczenie: 51×1999=101949; 101949×0,90=91754,1 → zaokr. do 91754 gr | jednostkowy | auto | H |
| TC-008 | H1-AC5 | wyliczenie połówki grosza (rabat 5%) | — | qty=10, cena=11 gr | 105 gr | Wyliczenie: wartość=110 gr; 110×0,95=104,5 gr → zaokrąglenie w górę (AC5: „połówka w górę”) = 105 gr | jednostkowy | auto | H |
| TC-009 | H1-AC5 | wyliczenie połówki grosza (rabat 10%) | — | qty=51, cena=15 gr | 689 gr | Wyliczenie: wartość=765 gr; 765×0,90=688,5 gr → zaokrąglenie w górę = 689 gr | jednostkowy | auto | H |
| TC-010 | H1-AC4 | klasa równoważności (niepoprawna: zero) | — | qty=0, cena=1999 gr | Wycena odrzucona (błąd walidacji) | AC4: „ilość musi być liczbą całkowitą ≥ 1; inaczej wycena jest odrzucana” | jednostkowy | auto | H |
| TC-011 | H1-AC4 | klasa równoważności (niepoprawna: ujemna) | — | qty=-1, cena=1999 gr | Wycena odrzucona (błąd walidacji) | AC4 jw. — wartość ujemna nie jest ≥ 1 | jednostkowy | auto | H |
| TC-012 | H1-AC4 | klasa równoważności (niepoprawna: niecałkowita) | — | qty=2.5, cena=1999 gr | Wycena odrzucona (błąd walidacji) | AC4: „liczbą całkowitą” — 2,5 nie jest całkowita | jednostkowy | auto | H |
| TC-013 | H1-AC4 | zgadywanie błędów (duża niecałkowita blisko progu) | — | qty=9.999999, cena=1999 gr | Wycena odrzucona (błąd walidacji), nie traktowane jako qty=10 | AC4 — walidacja całkowitości ma priorytet nad progiem ilościowym | jednostkowy | auto | M |
| TC-014 | H1-AC3 | tablica decyzyjna (brak sumowania progów) | — | qty=100, cena=1999 gr | 179910 gr | Wyliczenie: 100×1999=199900; rabaty się nie sumują (potwierdzone przez sprzedaż 2026-09-21) → tylko 10%: 199900×0,90=179910 | jednostkowy | auto | M |

## Sesje eksploracyjne i UAT
Nie dotyczy — czysta logika obliczeniowa bez UI; brak sesji ręcznych. Jeśli po automatyzacji ujawni się rozbieżność
w mechanizmie błędu (patrz Otwarte pytania), zalecana krótka sesja z właścicielem produktu, nie sesja eksploracyjna.

## Kryteria wejścia i wyjścia
- Wejście: `docs/project/03-requirements/requirements.md` w wersji zawierającej H1-AC1..AC5 i odpowiedź na pytanie o sumowanie rabatów (już odhaczone).
- Wyjście: wszystkie przypadki TC-001..TC-014 zaimplementowane w Vitest i zielone (lub czerwone ze zgłoszonym defektem wg protokołu rozbieżności z qa-spec-first-testing — nigdy z podmienioną wartością oczekiwaną); rekomendowane uzupełnienie o testy property-based (fast-check) dla niezmienników „wynik ≥ 0” i „wynik ≤ wartość bazowa”; mutation score (Stryker) dla modułu wyceny ≥ 80% jako cel jakości (do potwierdzenia z zespołem).

## Otwarte pytania
- [ ] TC-010/011/012 zakładają **[propozycja]**: nieprawidłowa ilość powoduje odrzucenie wyceny (błąd/wyjątek albo wynik z flagą błędu — mechanizm techniczny do ustalenia przez automatyka wg kontraktu funkcji, nie wpływa na oczekiwanie biznesowe „brak poprawnej kwoty”). Czy zero i wartość ujemna mają zwracać ten sam rodzaj błędu, czy różne komunikaty? → analityk domeny / właściciel produktu.
- [ ] Czy cena jednostkowa może być 0 gr (produkt promocyjny/gratis) lub ujemna (korekta)? Wymagania tego nie precyzują — **[propozycja]**: cena jednostkowa to liczba całkowita ≥ 0 gr; wartości ujemne odrzucane analogicznie do AC4. → dział sprzedaży.
- [ ] Czy cena jednostkowa musi być liczbą całkowitą groszy, czy dopuszczalne są ułamki grosza na wejściu (np. z przeliczeń walutowych) zaokrąglane przed wyceną? → analityk domeny.

## Przekazanie
- **Dla:** kasia (do automatyzacji)
- **Zadanie:** automatyzacja testów wg planu w Vitest
- **Przeczytaj:** cała tabela przypadków
