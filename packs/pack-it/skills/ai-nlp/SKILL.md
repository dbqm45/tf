---
name: ai-nlp
description: Użyj przy zadaniach NLP na tekście, w tym polskim — dobór podejścia, klasyfikacja, NER, ewaluacja spanowa, adnotacja, PII i anonimizacja.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy trzeba rozwiązać zadanie na tekście i wybrać metodę — reguły i regex, klasyczny ML, mały model enkoderowy, LLM zero/few-shot albo model dotrenowany (koszt, opóźnienie, dane, dokładność), klasyfikacja tekstu, NER i ekstrakcja informacji, ewaluacja na poziomie spanów (precision, recall, F1 micro i macro), normalizacja i tokenizacja, embeddingi i podobieństwo semantyczne, wykrywanie tematu i intencji, ograniczenia oceny streszczeń, projekt adnotacji (wytyczne, zgodność annotatorów, active learning), niezbalansowane klasy, polszczyzna (fleksja, lematyzacja, Morfeusz, spaCy, HerBERT, KLEJ, diakrytyki) oraz wykrywanie danych osobowych i anonimizacja w tekście (PESEL, imiona, adresy). Nie do RAG i chunkingu (ai-rag), pisania promptów (ai-prompt-engineering), dotrenowania modelu (ai-fine-tuning), ogólnej metody ewaluacji LLM (ai-evals), pisowni polskiego tekstu dla ludzi (txt-polish-correctness), statystyki i raportu z danych (data-analysis) ani podstaw prawnych RODO (arch-privacy-compliance)."
  slowa: "nlp, przetwarzanie języka naturalnego, klasyfikacja tekstu, klasyfikacja maili, ner, rozpoznawanie encji, ekstrakcja informacji, f1, precision, recall, micro, macro, tokenizacja, lematyzacja, fleksja, polski model językowy, herbert, klej, morfeusz, spacy, diakrytyki, embeddingi, podobieństwo zdań, intencja, temat, streszczenia, adnotacja, wytyczne adnotacji, kappa, active learning, niezbalansowane klasy, anonimizacja, pii, pesel, dane osobowe w tekście, presidio, regex czy llm"
---

# NLP — dobór metody i ewaluacja na tekście

NLP rzadko zaczyna się od modelu. Zaczyna się od zadania, danych i miary sukcesu. Prompt do LLM piszesz wg
**ai-prompt-engineering**, retrieval dla LLM projektujesz wg **ai-rag**, dotrenowanie prowadzisz wg **ai-fine-tuning**,
a metodę ewaluacji funkcji LLM opisuje **ai-evals**. Ten skill wybiera podejście i mierzy je na tekście.

## Procedura
1. **Zadanie i miara.** Nazwij typ: klasyfikacja (jedna etykieta, wiele etykiet), NER/ekstrakcja (spany), podobieństwo
   lub wyszukiwanie, generowanie (streszczenie). Zapisz: wolumen dziennie, dopuszczalne opóźnienie, koszt błędu
   (co boli bardziej: pominięcie czy fałszywy alarm), język i domenę, ilość etykiet. Bez tego nie wybierzesz metody.
2. **Najtańsze podejście, które przejdzie próg** (drabina; schodź wyżej po porażce, nie z góry):
   - reguły, słowniki, regex — gdy wzorzec jest zamknięty (kody, numery, daty, formaty); zero danych, pełna
     przewidywalność;
   - klasyczny ML (TF-IDF + regresja logistyczna lub SVM) — **zawsze jako punkt odniesienia**; często wystarcza przy
     setkach etykiet;
   - mały model enkoderowy (BERT-podobny, dla polskiego np. HerBERT) dotrenowany — gdy liczy się opóźnienie, koszt
     przy dużym wolumenie i jest ≥ ok. 1 000 etykiet [założenie — sprawdź krzywą uczenia];
   - LLM zero/few-shot — gdy etykiet mało, kategorie się zmieniają, zadanie wymaga rozumienia; płacisz za każde
     wywołanie i opóźnienie, zmierz na tym samym zbiorze co reszta;
   - model dotrenowany (ai-fine-tuning) — gdy LLM jest za drogi lub za wolny, a dane są.
   Często działa kaskada: reguły → mały model → LLM tylko dla niepewnych przypadków.
3. **Dane i podział.** Zbiór testowy zamrożony przed pracą, z rozkładu produkcyjnego, nie z ręcznie wybranych
   przykładów. Dla tekstów z tego samego źródła (klient, wątek, dokument) dziel **po źródle**, nie losowo, bo
   inaczej wyciekają duplikaty i wynik jest zawyżony.
4. **Tekst przed modelem.** Ustal normalizację raz i stosuj tak samo w treningu i na produkcji: Unicode NFC,
   białe znaki, wielkość liter tylko jeśli model jej nie niesie, zamiana URL/liczb na tokeny — tylko gdy nie niesie
   sygnału. Nie usuwaj stop-słów dla modeli kontekstowych. Tokenizator musi pasować do modelu; nie licz „słów”
   po spacjach przy fleksji. Specyfika polskiego: `references/polski-pii-i-adnotacja.md`.
5. **Miary.**
   - Klasyfikacja: precision, recall, F1 **per klasa** oraz macro-F1 (klasy równo) i micro-F1 (przykłady równo);
     przy niezbalansowaniu macro i recall rzadkiej klasy, nie sama accuracy. Macierz pomyłek czytaj ręcznie.
   - NER/ekstrakcja: **ocena na poziomie spanów** (encja trafiona, gdy zgadza się typ i granice), np. `seqeval`;
     accuracy na tokenach jest bezużyteczna, bo dominuje etykieta `O`. Podaj tryb ścisły i luźny (nakładanie).
     Micro-F1 po wszystkich encjach i macro po typach; raport per typ.
   - Podobieństwo i wyszukiwanie: recall@k, MRR, nDCG (jak w **ai-rag**); próg podobieństwa dobierz na zbiorze,
     nie z przykładu w dokumentacji.
   - Streszczenia i generowanie: ROUGE i podobne miary mierzą nakładanie słów, nie wierność ani spójność; używaj
     oceny ludzi lub sędziego LLM skalibrowanego do ludzi (ai-evals) i osobno sprawdzaj fakty (halucynacje).
6. **Niezbalansowane klasy.** Najpierw wagi klas lub dobór progu decyzyjnego po krzywej precision–recall,
   potem zbieranie etykiet rzadkiej klasy (active learning), na końcu oversampling. Test zostaw w rozkładzie
   produkcyjnym; po zmianie progu przelicz miary.
7. **Adnotacja, gdy brakuje etykiet.** Wytyczne z definicją każdej klasy, przykładami granicznymi i regułami
   rozstrzygania; pilot 100–200 przykładów na ≥ 2 annotatorów; zgodność: Cohen's kappa (2 osoby) albo Krippendorff's
   alpha (więcej), dla spanów także F1 między annotatorami. Niska zgodność = niejasne wytyczne, nie zła wina modelu;
   zgodność annotatorów to też górna granica sensownego wyniku. Active learning (uncertainty sampling) kieruje
   etykietowanie na przykłady, których model jest niepewny; testu nim nie zasilaj.
8. **Dane osobowe w tekście.** Reguły z walidacją (np. suma kontrolna PESEL) + model NER na imiona, nazwiska,
   adresy; mierz **recall** na własnym oznaczonym zbiorze, bo pominięcie to wyciek. Anonimizacja (nieodwracalna)
   kontra pseudonimizacja (stały token na osobę); odmiana polskich nazwisk utrudnia zliczanie — szczegóły w pliku
   referencyjnym. Podstawy prawne i minimalizacja: **arch-privacy-compliance**.
9. **Wynik: projekt rozwiązania NLP** w stałym układzie: zadanie i miara sukcesu; wybrane podejście z uzasadnieniem
   z drabiny; dane (źródło, liczba etykiet, podział); plan ewaluacji (zbiór, miary, próg akceptacji); ryzyka
   (niezbalansowanie, dryf, PII); następny krok, jeśli próg nie przejdzie.

Polszczyzna, narzędzia, benchmarki, PII i adnotacja w szczegółach: `references/polski-pii-i-adnotacja.md`.

## Przykład
**Wejście:** „40 000 maili dziennie po polsku, 6 działów, 800 oznaczonych, rzadki dział „Windykacja” to 3% maili.”
**Wynik:**
- miara: macro-F1 oraz recall „Windykacji” ≥ 0,85 [założenie — próg uzgodnij z biznesem], bo pominięcie kosztuje najwięcej;
- punkt odniesienia: TF-IDF + regresja logistyczna z wagami klas (godzina pracy, zero kosztu wywołań);
- jeśli macro-F1 poniżej progu: dotrenowany HerBERT; zmierz krzywą uczenia (400/800 etykiet), by wiedzieć, czy
  dosypanie etykiet pomoże; LLM few-shot na tym samym teście jako porównanie kosztu (40 000 × cena wywołania);
- podział po nadawcy, nie losowy; test 300 maili w rozkładzie produkcyjnym;
- active learning: 200 maili o najniższej pewności modelu do etykietowania, kappa na pilocie 100 maili ≥ 0,7 [założenie];
- kaskada: reguły (nagłówki, słowa kluczowe) → model → LLM dla maili o pewności poniżej progu.

## Checklista
- [ ] zadanie, wolumen, opóźnienie i koszt błędu zapisane; miara sukcesu wybrana przed modelem
- [ ] punkt odniesienia klasyczny (reguły lub TF-IDF); wyższy szczebel drabiny uzasadniony wynikiem
- [ ] zbiór testowy zamrożony, z rozkładu produkcyjnego, podział po źródle
- [ ] klasyfikacja: miary per klasa oraz macro i micro; NER: miary spanowe, nie accuracy na tokenach
- [ ] niezbalansowanie obsłużone (wagi, próg), test nietknięty
- [ ] adnotacja: wytyczne, zgodność annotatorów, pilot przed pełnym etykietowaniem
- [ ] polskie: normalizacja NFC, lematyzacja lub tokenizacja dopasowana do fleksji, model sprawdzony na własnych danych
- [ ] PII: recall zmierzony na własnym zbiorze; anonimizacja czy pseudonimizacja rozstrzygnięta
- [ ] fakty o modelach i narzędziach (wersje, licencje) sprawdzone w źródle z datą

## Źródła
- Rybak i in., „KLEJ: Comprehensive Benchmark for Polish Language Understanding” (ACL 2020, arXiv 2005.00630,
  dostęp 2026-10-17): benchmark KLEJ z rankingiem; HerBERT wprowadzony w tej pracy.
- Augustyniak i in., „This is the way: designing and compiling LEPISZCZE” (NeurIPS 2022 Datasets and Benchmarks,
  dostęp 2026-10-17): 13 par zadanie–zbiór dla polskiego, w tym pięć z KLEJ.
- seqeval (pypi.org/project/seqeval, dostęp 2026-10-17): ocena spanowa NER wzorowana na `conlleval`; scikit-learn
  `f1_score`, parametr `average` (micro, macro, weighted), dostęp 2026-10-17.
- [niezweryfikowane] progi liczbowe (≥ 1 000 etykiet, kappa ≥ 0,7, recall ≥ 0,85) — reguły praktyczne, nie wyniki
  z literatury; dobierz do własnego kosztu błędu.

Opisane własnymi słowami.
