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

## Projekty w domenach naukowych (biologia, chemia, medycyna, materiały)
Gdy założenia projektu zależą od wiedzy naukowej spoza informatyki (np. degradacja ogniw, interakcje leków, dane
kliniczne), przegląd literatury i analiza danych z baz naukowych to osobny krok przed modelem:
1. **Narzędzie:** Claude Science (aplikacja desktopowa Anthropic, publiczna beta; literatura i ponad 60 baz
   naukowych, odtwarzalne notatniki, recenzent cytowań i liczb w tle — strona produktu claude.com/product/claude-science,
   dostęp 2026-11-08) prowadzi człowiek; agent fabryki nie ma do niego dostępu programowego. Bez niego: wyszukiwanie
   wg **core-source-research** i bazy dziedzinowe przez ich API.
2. **Do repozytorium wraca zapis dowodu, nie streszczenie rozmowy:** dla każdego ustalenia teza, źródło (DOI albo
   adres, wersja preprintu lub artykułu, data dostępu), warunki (próba, metoda, zakres) i ścieżka do notatnika lub
   skryptu, który odtwarza liczbę. Notatnik i dane pośrednie trafiają obok (np. katalog badań w dzienniku projektu, docs/project/02-domain/badania/),
   duże dane — tylko opis, skąd je pobrać.
3. **Sprawdzenie przed użyciem w projekcie:** liczby i daty w zapisie przez
   `python3 .claude/skills/core-grounding/scripts/claims_check.py`, odwołania przez `grounding_check.py`; ustalenie
   bez odtwarzalnego źródła ma status [niezweryfikowane] i nie wchodzi do wymagań ani do cech modelu.
4. Decyzje medyczne, prawne i bezpieczeństwa z takich ustaleń zatwierdza ekspert dziedzinowy, nie agent.

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
