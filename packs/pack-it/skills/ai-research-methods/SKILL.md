---
name: ai-research-methods
description: Użyj przy badaniu i walidacji modelu ML — baseline, wyciek danych (podział losowy, czasowy, grupowy), wynik offline vs po wdrożeniu, seedy, metryki, raport.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy trzeba przejść od pytania badawczego lub hipotezy AI/ML do wyniku, który da się obronić — ujęcie problemu i mocny prosty baseline, projekt eksperymentu (kontrolowane zmienne, ablacje, seedy, średnia ± rozrzut, ostrożność przy wielokrotnych porównaniach), podziały danych i wyciek (czasowe, grupowe, higiena zbioru testowego, kontaminacja benchmarków), metryka zgodna z decyzją, budżet obliczeń i skalowanie od pilotażu, reprodukowalność (konfiguracja, kod, wersje danych, środowisko), przegląd literatury i krytyczne czytanie artykułów, od artykułu do prototypu produktowego, walidacja offline→online, raport badawczy z wynikami negatywnymi i ograniczeniami, przegląd etyczny danych; artefakt docs/project/02-domain/experiment-NAZWA.md. Nie do ewaluacji funkcji LLM i agentów (ai-evals), ogólnej statystyki i eksperymentów produktowych (data-analysis), dostrajania modelu (ai-fine-tuning), narzędzi śledzenia eksperymentów i rejestru (ai-mlops) ani szukania faktów w sieci (core-source-research)."
  slowa: "badania ML, research scientist, applied scientist, hipoteza, eksperyment ML, baseline, ablacja, seedy, wariancja między uruchomieniami, średnia i odchylenie, czy nowy model jest lepszy, wyciek danych, data leakage, podział czasowy, podział grupowy, zbiór testowy, kontaminacja benchmarku, dobór metryki, pilotaż, skalowanie eksperymentu, reprodukowalność, powtarzalność wyników, przegląd literatury, czytanie artykułów, replikacja, z artykułu do produktu, offline online, raport z badania, wyniki negatywne, metoda nie zadziałała, nie poprawiła wyniku, jak zapisać badanie, metoda z artykułu, ograniczenia badania, etyka danych"
---

# Badania AI/ML — od hipotezy do wyniku, który się obroni

Wynik „model B jest lepszy” ma wartość tylko wtedy, gdy ktoś inny może go powtórzyć i wskazać, co go podważa.
Skill prowadzi przez cały cykl badawczy. Zostawia sąsiadom ich zadania: ewaluację funkcji LLM i agentów (**ai-evals**),
statystykę i testy A/B produktu (**data-analysis**, `.claude/skills/data-analysis/references/statystyka.md`,
`.claude/skills/data-analysis/references/eksperymenty-zaawansowane.md`), dostrajanie (**ai-fine-tuning**), narzędzia
śledzenia eksperymentów (**ai-mlops**) i badanie faktów w sieci (**core-source-research**).

## Procedura
1. **Pytanie i decyzja.** Zapisz hipotezę falsyfikowalnie („dodanie cechy X podnosi PR-AUC o ≥ 1 pkt na danych z
   kwartału Q”), decyzję, którą wynik zmieni, i kryterium porażki. Bez kryterium porażki każdy wynik „coś pokazuje”.
2. **Literatura przed kodem** (`references/literatura-i-prototyp.md`). Sprawdź, czy ktoś już to zrobił i czy
   zreplikowano wynik. Ustalenie artykułu = twierdzenie + dowód + warunki. Fakty z sieci zbieraj wg **core-source-research**.
3. **Mocny prosty baseline najpierw.** Reguła, regresja logistyczna, drzewo, ostatnia wartość, najczęstsza klasa
   albo istniejący system. Strojony baseline (tyle prób, co kandydat) jest uczciwym punktem odniesienia; kandydat
   bijący słaby baseline niczego nie dowodzi. Jeśli prosty model wystarcza do decyzji, badanie kończy się tutaj.
4. **Podział danych i wyciek — przed pierwszym treningiem** (`references/wyciek-i-podzialy.md`). Podział wynika z
   tego, jak model będzie użyty: przyszłość nie wpływa na przeszłość (podział czasowy), ta sama jednostka (klient,
   pacjent, dokument) nie trafia po obu stronach (podział grupowy). Przetwarzanie wstępne (skalowanie, imputacja,
   selekcja cech, kodowanie) uczysz tylko na treningu. **Zbiór testowy ogląda się raz**, na końcu; strojenie idzie
   na walidacji. Zbiór testowy użyty do wyboru jest już zbiorem walidacyjnym.
5. **Metryka zgodna z decyzją.** Metryka wynika z kosztu błędów i sposobu użycia (precision@k przy ograniczonej
   liczbie interwencji, kalibracja przy progach, koszt fałszywego alarmu), a nie z tego, co raportuje benchmark.
   Jedna metryka główna ustalona **przed** eksperymentem, reszta pomocnicza; wyniki w podgrupach, nie tylko średnia.
6. **Projekt eksperymentu.** Zmieniasz jedną rzecz naraz; dane, podziały, budżet strojenia i metryka są identyczne
   dla wszystkich wariantów. **Ablacje**: usuń po jednym elemencie nowej metody i pokaż, który wnosi zysk.
   Sprawdź też kontrolę negatywną (np. etykiety pomieszane — wynik ma spaść do losowego; jeśli nie, jest wyciek).
7. **Seedy i wariancja.** Pojedynczy przebieg to jedna próbka z rozkładu. Powtórz każdy wariant na ≥ 5 seedach
   [założenie — liczba zależy od rozrzutu; zacznij od 5 i zwiększ, gdy przedziały się nakładają] i raportuj
   **średnia ± odchylenie (albo przedział ufności)**, zapisując, co się zmieniało: inicjalizacja, kolejność danych,
   podział, hiperparametry. Źródła zmienności obejmują też wybór podziału danych, nie tylko seed
   (Bouthillier i in. 2021). Różnicę mniejszą od rozrzutu uznaj za nierozstrzygniętą.
8. **Istotność i wielokrotne porównania.** Porównuj **sparowanie** (ten sam podział i te same przykłady): test
   parowany, bootstrap różnicy, McNemar dla klasyfikacji. Podaj wielkość efektu i przedział, nie tylko p. Przy
   wielu wariantach, metrykach lub zbiorach popraw liczbę porównań (Bonferroni, Holm) albo nazwij je eksploracyjnymi;
   liczba prób strojenia i „podglądania” wyników trafia do raportu. Wybór testu: Dror i in. 2018;
   rachunek: **data-analysis**.
9. **Budżet obliczeń i skalowanie.** Przed dużym przebiegiem policz koszt (GPU-godziny × warianty × seedy).
   Pilotaż na małym modelu lub podzbiorze: czy pipeline działa, czy metryka reaguje, jaki jest rozrzut. Wniosków z
   małej skali nie przenoś na dużą bez sprawdzenia trendu na 2–3 rozmiarach [założenie — ranking metod bywa niestabilny].
10. **Reprodukowalność.** Dla każdego przebiegu zapisz: commit kodu, konfigurację (hiperparametry, seedy), wersję
    i skrót danych oraz podziału, środowisko (biblioteki, sprzęt), komendę uruchomienia. Śledzenie i rejestr
    (MLflow, DVC) to **ai-mlops**. Lista kontrolna: `references/raport-i-szablon.md`.
11. **Od artykułu i wyniku do produktu** (`references/literatura-i-prototyp.md`). Prototyp na własnych danych, nie na
    benchmarku; walidacja offline (dane historyczne, podział czasowy), potem online (shadow, A/B — **data-analysis**
    i **ai-evals**, krok 8). Różnica offline↔online jest wynikiem: zapisz ją i jej przyczynę.
12. **Etyka danych.** Przed użyciem sprawdź pochodzenie i licencję danych, zgody, dane osobowe i szczególne
    (**arch-privacy-compliance**), reprezentatywność i ryzyko szkód dla grup; kontaminację benchmarków i nadużycia.
13. **Raport** `docs/project/02-domain/experiment-<nazwa>.md` wg `references/raport-i-szablon.md`: hipoteza, metoda,
    wyniki z rozrzutem, **wyniki negatywne**, ograniczenia, decyzja. Wynik negatywny jest wartościowy:
    oszczędza następnym ślepe zaułki, ale tylko gdy opisano warunki, w których go uzyskano.

## Przykład
[przykład — liczby ilustracyjne, nie z pomiaru]
**Wejście:** model odejść klientów (churn), baseline: regresja logistyczna, PR-AUC 0,41; nowy gradient boosting
z 14 cechami czasowymi daje 0,46 w jednym przebiegu z losowym podziałem 80/20 (kilka wierszy na klienta).
**Wynik:**
- podział zmieniony na czasowy + grupowy (trening: miesiące 1–9, test: 10–12, klient tylko po jednej stronie);
  baseline spada do 0,34, nowy model do 0,37 — wcześniejszy wynik zawyżał wyciek;
- 5 seedów × 2 podziały: baseline 0,34 ± 0,01, nowy 0,37 ± 0,02; różnica 0,03, przedział bootstrapu różnicy
  sparowanej [0,01; 0,05] — poprawa jest, ale mniejsza niż deklarowane 5 pkt;
- ablacja: 11 z 14 cech nic nie wnosi; trzy cechy „liczba kontaktów z supportem” dają cały zysk;
- 12 wariantów porównano → próg Bonferroniego 0,05/12 ≈ 0,004; efekt nadal wyraźny dla wariantu z trzema cechami;
- raport `experiment-churn-gb.md`: werdykt „pilotaż shadow”, ograniczenie „dane z jednego kraju”, wynik negatywny
  „pozostałe 11 cech bez efektu”.

## Checklista
- [ ] hipoteza falsyfikowalna, kryterium porażki i decyzja zapisane przed eksperymentem
- [ ] literatura sprawdzona, twierdzenia artykułów odróżnione od dowodów
- [ ] mocny prosty baseline z takim samym budżetem strojenia
- [ ] podział czasowy/grupowy, przetwarzanie uczone tylko na treningu, zbiór testowy użyty raz
- [ ] metryka główna zgodna z decyzją wybrana przed wynikami; wyniki w podgrupach
- [ ] ablacje i kontrola negatywna; zmieniana jedna rzecz naraz
- [ ] ≥ 5 seedów, średnia ± rozrzut, porównanie sparowane, korekta wielokrotnych porównań
- [ ] budżet obliczeń policzony, pilotaż przed dużym przebiegiem
- [ ] commit, konfiguracja, wersja danych i środowisko zapisane
- [ ] etyka i licencje danych sprawdzone; raport z wynikami negatywnymi i ograniczeniami

## Źródła
- Bouthillier i in., „Accounting for Variance in Machine Learning Benchmarks”, MLSys 2021 (arXiv 2103.03098,
  odczyt 2026-10-17): zmienność od próbkowania danych, inicjalizacji i wyboru hiperparametrów jest niedoszacowana;
  rekomendacje porównywania.
- Pineau i in., „Improving Reproducibility in Machine Learning Research”, JMLR 22(164), 2021 (arXiv 2003.12206,
  odczyt 2026-10-17): program reprodukowalności NeurIPS 2019 z listą kontrolną, polityką kodu i wyzwaniem replikacji.
  Treść pozycji listy: [niezweryfikowane] w tym środowisku.
- Kapoor, Narayanan, „Leakage and the reproducibility crisis in machine-learning-based science”, Patterns 4(9),
  2023 (odczyt 2026-10-17): wyciek w 17 dziedzinach i 294 pracach, osiem typów wycieku.
- Henderson i in., „Deep Reinforcement Learning That Matters”, AAAI 2018 (odczyt 2026-10-17): wynik zależy od
  seedów i liczby prób, wniosek o testach istotności i rzetelnym raportowaniu.
- Dror i in., „The Hitchhiker’s Guide to Testing Statistical Significance in NLP”, ACL 2018 (odczyt 2026-10-17):
  protokół doboru testu istotności; przegląd ACL/TACL 2017 wykazał pomijanie lub błędne użycie testów.
- Liczba 5 seedów, progi pilotażu i przenoszenie wniosków ze skali to praktyka autorów skilla [założenie].

Opisane własnymi słowami.
