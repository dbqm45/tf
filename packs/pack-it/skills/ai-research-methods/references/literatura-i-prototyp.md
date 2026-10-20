# Literatura i droga od artykułu do prototypu

## Szukanie i czytanie artykułu krytycznie
1. **Zakres:** sformułuj pytanie i hasła; przejrzyj przeglądy (survey), potem prace często cytowane i najnowsze.
   Zapisz zapytania, daty i kryteria włączenia, żeby przegląd dało się powtórzyć. Szukanie faktów w sieci:
   **core-source-research**.
2. **Preprint a praca recenzowana:** preprint nie przeszedł recenzji; sprawdź, czy wersja opublikowana się zmieniła.
3. **Twierdzenie → dowód.** Wypisz główne twierdzenia i dla każdego: na jakich danych, jaka metryka, ile przebiegów,
   jaki baseline. Pytania kontrolne:
   - czy baseline był strojony tak samo starannie;
   - czy raportowano rozrzut i istotność, czy jeden przebieg;
   - czy zbiór testowy służył do wyboru; czy możliwa jest kontaminacja;
   - czy poprawa wynika z metody, czy z większej mocy obliczeniowej lub danych;
   - czy ablacje wskazują element odpowiedzialny za zysk;
   - czy kod i dane są dostępne.
4. **Przenaszalność:** czy nasze dane, skala i ograniczenia (opóźnienie, koszt) przypominają warunki z artykułu.
5. **Replikacja:** przed wdrożeniem odtwórz kluczowy wynik na danych z artykułu (lub choć na jego małej wersji).
   Nie udało się — to też wynik; zapisz różnice w konfiguracji.
6. **Notatka:** jedna strona na artykuł: twierdzenie, dowód, wiarygodność (wysoka/średnia/niska) z powodem, pomysł na
   użycie.

## Z artykułu do prototypu produktowego
1. Zacznij od decyzji produktowej i metryki zgodnej z nią, nie od metody.
2. Porównaj metodę z baseline na **własnych** danych z podziałem odpowiadającym użyciu (czasowy/grupowy).
3. Pilotaż małej skali, potem budżet na pełny przebieg (SKILL.md, krok 9).
4. Sprawdź wymagania wdrożeniowe: opóźnienie, koszt na predykcję, pamięć (**ai-model-optimization**), zależność
   od danych, które w produkcji nie istnieją lub są spóźnione.
5. **Offline → online:** walidacja offline na danych historycznych; potem shadow (wynik liczony, nieużywany) i
   A/B z metryką biznesową (**data-analysis**). Różnica offline↔online wynika z dryfu, pętli sprzężenia zwrotnego albo
   metryki niezgodnej z celem — ustal, która, i zapisz.
6. Przekazanie do produkcji: rejestr modeli, monitoring, progi wycofania (**ai-mlops**).
7. Dostrajanie dużych modeli i wybór prompt/RAG/fine-tuning: **ai-fine-tuning**; ewaluacja funkcji LLM: **ai-evals**.

## Przegląd etyczny danych
- pochodzenie i licencja (czy wolno trenować, czy wolno komercyjnie), zgody i cel pierwotny;
- dane osobowe i szczególne kategorie → **arch-privacy-compliance** (DPIA);
- reprezentatywność: kogo brakuje w danych, wyniki per podgrupa, ryzyko szkody dla grup;
- etykiety: kto je nadał, w jakich warunkach, zgodność oceniających;
- zastosowanie wtórne i nadużycie: do czego wynik może posłużyć poza zamierzeniem.
