---
name: pm-product-strategy
description: Użyj przy strategii produktu na rynku — pozycjonowanie, wielkość rynku TAM/SAM/SOM, ściągawka konkurencyjna dla sprzedaży, PESTEL, kierunek wzrostu (Ansoff).
metadata:
  przeglad: 2027-10-23
  katalog: "Użyj, gdy trzeba ustalić, dla kogo jest produkt i dlaczego wygra z alternatywami — pozycjonowanie (konkurencyjne alternatywy, unikalne cechy, wartość, najlepiej dopasowani klienci, kategoria rynku) i komunikat, wielkość rynku TAM/SAM/SOM od dołu z założeniami, ściągawka konkurencyjna dla handlowców (kiedy wygrywamy i przegrywamy, obiekcje, pytania, dowody z datą), otoczenie (PESTEL) i kierunek wzrostu (macierz Ansoffa: penetracja, nowy rynek, nowy produkt, dywersyfikacja). Nie do wyboru funkcji, drzewa szans, kanwy modelu biznesowego, pięciu sił Portera i SWOT (proc-product-discovery), metryk SaaS (pm-saas-metrics), wycofania produktu (pm-product-lifecycle) ani planu projektu (proc-project-planning)."
  slowa: "pozycjonowanie, komunikat marketingowy, kolejny program, czym się wyróżniamy, wielkość rynku, TAM, SAM, SOM, inwestor pyta o rynek, ściągawka dla handlowców, battle card, przegrywamy z konkurentem, karta konkurencji, PESTEL, nowy kraj czy nowy produkt, macierz Ansoffa, ekspansja zagraniczna, wejść do innego kraju, wejście na nowy rynek, drugi produkt dla obecnych klientów, nowy produkt czy nowy rynek, strategia wzrostu, kategoria rynku"
---

# Strategia produktu na rynku

Cel: wiedzieć, dla kogo produkt jest najlepszym wyborem, z czym naprawdę konkuruje i gdzie rosnąć — z dowodem albo
z oznaczonym założeniem przy każdym zdaniu (core-grounding). Decyzję strategiczną podejmuje człowiek; ty dajesz
opcje, liczby z założeniami i rekomendację.

## Procedura
1. **Pytanie i decyzja.** Zapisz, jaką decyzję ma wesprzeć praca (komunikat na stronę, prezentacja dla inwestora,
   wejście na rynek, ściągawka dla sprzedaży) i kto decyduje. Od tego zależy, które kroki niżej robisz.
2. **Pozycjonowanie** — w tej kolejności, bo każdy krok wynika z poprzedniego:
   1. **konkurencyjne alternatywy** — co klient zrobiłby bez nas (arkusz, biuro rachunkowe, „nic”, konkurent);
   2. **unikalne cechy** — co mamy, czego alternatywy nie mają (funkcja, model dostawy, wiedza, cena);
   3. **wartość** — co te cechy dają klientowi, z dowodem (liczba, cytat klienta, przypadek);
   4. **najlepiej dopasowani klienci** — cechy klientów, dla których ta wartość jest największa (nie „wszyscy”);
   5. **kategoria rynku** — rama, w której klient od razu rozumie wartość; zła kategoria = „kolejny program X”.
   Wynik: zdanie pozycjonujące i 3 komunikaty z dowodami — szablon w `references/pozycjonowanie.md`.
3. **Wielkość rynku** od dołu: liczba klientów docelowych × roczny przychód na klienta, z rozdzieleniem TAM / SAM /
   SOM i źródłem z datą przy każdej liczbie; szacunek od góry („1% dużego rynku”) tylko jako kontrola —
   `references/rynek-i-otoczenie.md`.
4. **Konkurencja dla sprzedaży** — ściągawka na jednego konkurenta z danych o wygranych i przegranych:
   `references/sciagawka-konkurencyjna.md`. Porównanie zadań klienta, SWOT i pięć sił Portera:
   proc-product-discovery (`.claude/skills/proc-product-discovery/references/model-biznesowy-i-rynek.md`).
5. **Otoczenie i kierunek wzrostu** — PESTEL dla rynku, na który wchodzisz, i macierz Ansoffa dla opcji wzrostu
   (`references/rynek-i-otoczenie.md`). Każda opcja kończy się najtańszym testem kluczowego założenia
   (proc-product-discovery, krok 8).
6. **Zapis**: decyzja, odrzucone opcje z powodem, założenia do sprawdzenia i termin przeglądu →
   `docs/project/01-discovery/` (core-project-record).

## Zasady
- Liczba bez źródła i daty to [założenie] — tak ją oznaczasz, także w materiale dla inwestora.
- Pozycjonowanie opisuje stan dzisiejszy produktu; obietnice z roadmapy oznaczasz jako plan.
- Konkurenta opisujesz faktami, które da się sprawdzić; reklama porównawcza w UE musi porównywać obiektywnie
  i sprawdzalnie (dyrektywa 2006/114/WE, art. 4) — przy materiałach zewnętrznych: arch-eu-product-law.

## Przykład
Narzędzie do rozliczeń dla biur rachunkowych, klienci: „kolejny program księgowy”. Alternatywy: Excel i program
księgowy, którego biuro już używa. Unikalna cecha: automatyczne uzgadnianie wyciągów z 12 banków. Wartość: 6 h
mniej pracy na 100 klientów biura miesięcznie (pomiar u 4 pilotażowych biur). Najlepiej dopasowani: biura 3–15
osób z ponad 150 klientami JDG. Kategoria: nie „program księgowy”, tylko „automat do uzgadniania płatności dla
biur rachunkowych” — działa obok obecnego programu, więc nie konkuruje z nim. Rynek od dołu: biura 3–15 osób
[liczba z GUS, rok — do sprawdzenia] × 2 400 zł rocznie = SAM; SOM na 3 lata z pojemności 2 handlowców.

## Źródła
- A. Dunford, *Obviously Awesome* (2019) — składniki pozycjonowania i ich kolejność.
- G. Moore, *Crossing the Chasm* (1991) — zdanie pozycjonujące, klient docelowy.
- H. I. Ansoff, „Strategies for Diversification”, *Harvard Business Review* (1957) — macierz produkt × rynek.
- F. Aguilar, *Scanning the Business Environment* (1967) — skanowanie otoczenia (rodowód PEST/PESTEL).
- Dyrektywa 2006/114/WE dotycząca reklamy wprowadzającej w błąd i reklamy porównawczej, art. 4.
Opisane własnymi słowami.
