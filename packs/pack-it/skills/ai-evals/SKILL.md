---
name: ai-evals
description: Użyj przy ewaluacji funkcji LLM i agentów — zbiory danych, graderzy, sędzia LLM, pass@k i pass^k, bramka w CI, ewaluacje online.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy trzeba zmierzyć jakość funkcji z LLM lub agenta, a nie tylko napisać pierwszą macierz testów — rozwój sterowany ewaluacjami, projekt zbiorów (złoty, regresyjny, przypadki brzegowe, adwersaryjne, próbki z ruchu, kontaminacja), rodzaje graderów (kod, sędzia LLM z rubryką i kalibracją do ocen ludzi, przegląd ludzki), ocena wyniku i trajektorii agenta, pass@k kontra pass^k, ewaluacje offline i online (A/B, shadow), bramka w CI z progami i alertem regresji, koszt i wariancja ewaluacji, format raportu. Nie do podstawowej macierzy promptfoo, schematu wyjścia i limitów pętli (eng-llm-features), ewaluacji skilli Claude (core-skill-authoring) ani wyroczni testów kodu (qa-spec-first-testing)."
  slowa: "ewaluacje, evals, eval, zbiór testowy, golden set, sędzia llm, llm-as-a-judge, rubryka, kalibracja sędziego, zgodność z ludźmi, pass@k, pass^k, niespójny agent, trajektoria agenta, regresja jakości, bramka w ci, próg jakości, a/b test, shadow, ewaluacja online, kontaminacja, wariancja ewaluacji, raport z ewaluacji, jak mierzyć jakość agenta"
---

# Ewaluacje funkcji LLM i agentów

Ewaluacja zamienia „wydaje się lepsze” w liczbę, na której opiera się decyzja: wypuścić, cofnąć, zmienić model.
Podstawową macierz (przypadki × kandydaci, asercje, podłożone błędy) daje **eng-llm-features** §8; ten skill zaczyna się
tam, gdzie pierwsza macierz przestaje wystarczać: zbiory rosną, ocena jest subiektywna, agent bywa niespójny, a wynik ma
blokować merge.

## Procedura
1. **Zacznij od porażek, nie od teorii.** Zapisz 20–50 prostych zadań z prawdziwych błędów (zgłoszenia, kolejka
   supportu, ręczne próby). To dobry start; zbiór rośnie z każdą nową porażką. Każde zadanie: wejście, kryterium
   sukcesu, rozwiązanie wzorcowe. Dwóch ekspertów powinno dojść do tego samego werdyktu — inaczej zadanie jest niejasne.
2. **Warstwy zbioru** (`references/zbiory-i-graderzy.md`): *złoty* (wzorcowe, małe, ręcznie sprawdzone), *regresyjny*
   (naprawione błędy; oczekiwane ok. 100%), *brzegowy* (puste, za długie, niejednoznaczne, w obcym języku),
   *adwersaryjny* (wstrzyknięcia, próby obejścia), *próbki z ruchu* (zanonimizowane, odświeżane). Dla każdego
   zachowania dodaj przypadki, w których ma wystąpić, **i** takie, w których nie ma (inaczej optymalizujesz jednostronnie).
3. **Kontaminacja i wyciek.** Zbioru ewaluacyjnego nie wklejasz do promptu, przykładów few-shot ani danych
   strojenia; przykłady do promptu bierzesz z osobnej puli. Publiczne benchmarki mogą być w danych modelu — dla
   decyzji produktowych liczy się własny zbiór.
4. **Dobierz gradera** (od najtańszego): kod (dokładne dopasowanie, schemat, test jednostkowy, stan w bazie) →
   sędzia LLM (nuans, ton, zgodność z faktami) → człowiek (kalibracja i próbki). Reguła: *deterministyczny, gdzie się
   da; LLM, gdzie trzeba; człowiek do walidacji*.
5. **Sędzia LLM — zbuduj i skalibruj.** Rubryka z opisem każdego poziomu, **jeden wymiar na sędziego**, opcja
   „nieznane / za mało danych”, inny model niż generujący, wynik w ustalonym formacie. Kalibracja: 30–50 przykładów
   ocenionych przez ludzi, zgodność liczysz (odsetek zgodnych albo kappa Cohena [próg ustal z zespołem]), rozbieżności
   czytasz i poprawiasz rubrykę. Bez tego sędzia jest nieznanym instrumentem. Szczegóły: `references/zbiory-i-graderzy.md`.
6. **Agent: wynik czy trajektoria.** Podstawą jest **wynik** (stan środowiska po przebiegu: rezerwacja istnieje w
   bazie, testy przechodzą), bo sztywne sprawdzanie ścieżki karze poprawne, inne rozwiązania. Trajektorię (wywołania
   narzędzi, liczba kroków, koszt) sprawdzasz osobno: limity, zakazane narzędzia, diagnoza porażek. Dla zadań
   wieloetapowych przyznawaj punkty częściowe. Każdą próbę uruchamiaj w czystym środowisku.
7. **Powtórz próby i wybierz metrykę.** Agent jest niedeterministyczny, więc `k` prób na zadanie.
   **pass@k** = szansa na co najmniej jeden sukces w k próbach (rośnie z k; gdy wystarczy jedno dobre
   rozwiązanie). **pass^k** = szansa, że wszystkie k prób się uda (maleje z k; gdy liczy się spójność, np. obsługa klienta).
   Skuteczność 75% na próbę daje pass^3 ≈ 42%.
8. **Offline, potem online.** Offline: zbiór przed wdrożeniem, bramka. Online (po wdrożeniu): shadow (nowa wersja
   liczy równolegle, użytkownik jej nie widzi), A/B na części ruchu z metryką biznesową, próbki do ręcznego
   przeglądu i nowe porażki z ruchu wracają do zbioru. Wzorzec i progi: `references/ci-i-ruch.md`.
9. **Bramka w CI.** Szybki podzbiór (smoke) na każdy PR, pełny zestaw nocą lub przy zmianie modelu, promptu, narzędzi.
   Próg ustaw względem **linii bazowej z rozrzutem** (powtórz bazę 3–5 razy), nie „na oko”; regresja = spadek poza
   przedział szumu. Zmiana progu tylko świadomie, z zapisem. Szczegóły: `references/ci-i-ruch.md`.
10. **Koszt i wariancja.** Policz koszt przebiegu (przypadki × próby × kandydaci × sędzia) przed uruchomieniem;
    tani model do triażu, pełny zestaw tylko przy zmianie. 0% sukcesów w wielu próbach to zwykle zepsute zadanie lub
    grader, nie niezdolny agent. Czytaj transkrypty porażek — to najszybsza diagnoza.
11. **Raport** w stałym formacie (niżej). Saturacja (zbiór zdaje ~100% i nie odróżnia wersji) → dodaj trudniejsze zadania.

## Format raportu
```
Ewaluacja: <funkcja> | zbiór: <nazwa, N zadań, data> | kandydat vs baza: <model/prompt>
Metryki: sukces <x%> (baza <y%>), pass^3 <..>, koszt/przebieg <..>, czas <..>
Rozrzut bazy: <min–max z n powtórzeń> | Werdykt: wypuść / wstrzymaj / zbadaj
Regresje: <zadanie → przyczyna>; Nowe porażki do zbioru: <lista>
```

## Przykład
**Wejście:** agent wsparcia zwrotów, 40 zadań z kolejki supportu, 4 powtórzenia, wynik 75% na próbę.
**Wynik:**
- grader wyniku: kod sprawdza stan zamówienia w bazie testowej (zwrot utworzony, kwota ≤ zamówienie);
  sędzia LLM tylko dla tonu odpowiedzi, skalibrowany na 40 ocenach ludzi (zgodność 85%, rubryka poprawiona raz);
- pass^4 = 0,75⁴ ≈ 32% → dla klienta zbyt niska spójność, mimo 75% średniej; pass@4 ≈ 99,6%;
- baza powtórzona 4 razy: 72–78% → próg regresji w CI to 68%, nie 75%;
- raport: werdykt „wstrzymaj”, 3 nowe porażki z transkryptów dodane do zbioru regresyjnego.

## Checklista
- [ ] zbiór startowy z prawdziwych porażek, warstwy opisane, przypadki „ma” i „nie ma wystąpić”
- [ ] zbiór oddzielony od promptu i przykładów (kontaminacja)
- [ ] grader najtańszy z możliwych; sędzia LLM z rubryką, opcją „nieznane” i kalibracją do ocen ludzi
- [ ] agent: ocena wyniku, trajektoria osobno, czyste środowisko, k prób, wybrane pass@k lub pass^k
- [ ] linia bazowa z rozrzutem; próg w CI wyprowadzony z niej; smoke na PR, pełny zestaw okresowo
- [ ] koszt policzony przed uruchomieniem; transkrypty porażek przeczytane
- [ ] ruch online (shadow, A/B) zasila zbiór; raport w stałym formacie

## Źródła
- Anthropic Engineering, „Demystifying evals for AI agents” (2026-01-09, odczyt 2026-10-17): zadanie, próba, transkrypt,
  wynik; graderzy kodowi, modelowi i ludzcy; pass@k i pass^k (przykład 75% → ok. 42% dla 3 prób); 20–50 zadań z
  prawdziwych porażek; ocena wyniku zamiast ścieżki; opcja „Unknown” i osobny sędzia na wymiar; saturacja.
- Anthropic, „Create strong empirical evaluations / Define success criteria and build evaluations”
  (platform.claude.com/docs/en/test-and-evaluate/develop-tests, odczyt 2026-10-17, strona bez daty): zadaniowość,
  automatyzacja, objętość ponad jakość pojedynczego przypadku, przypadki brzegowe, inny model jako sędzia.
- OpenAI, przewodnik po ewaluacjach (platform.openai.com/docs/guides/evals) — [niezweryfikowane]: strona nieosiągalna
  z tego środowiska 2026-10-17; z niej pochodzi tylko ogólna zasada „ewaluacje przy każdym wydaniu”, bez szczegółów API.
- Progi kappa, rozmiar próbki kalibracji (30–50) i reguła „3–5 powtórzeń bazy” to praktyka autorów skilla [założenie].

Opisane własnymi słowami.
