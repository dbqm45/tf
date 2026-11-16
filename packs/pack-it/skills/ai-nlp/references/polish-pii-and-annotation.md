# Polski, PII i adnotacja — szczegóły

Spis: polszczyzna w NLP · narzędzia i modele · benchmarki · PII i anonimizacja · adnotacja

## Polszczyzna w NLP
- **Fleksja.** Jedno słowo ma wiele form („umowa, umowy, umowie, umową”). Modele na zliczeniach słów (TF-IDF, BM25,
  słowniki) potrzebują lematyzacji albo n-gramów znakowych; modele subwordowe radzą sobie lepiej, ale rzadkie formy
  rozpadają się na wiele tokenów, co skraca efektywny kontekst.
- **Lematyzacja nazw własnych zawodzi.** Nazwisko „Kowalskiego” analizator może sprowadzić do „Kowalski”, ale
  nieznane nazwiska i nazwy firm („Żabki”) bywają lematyzowane błędnie. Zliczanie po osobie opieraj na identyfikatorze
  lub kluczu z rozstrzygnięcia tożsamości, nie na samej formie z tekstu.
- **Diakrytyki.** Użytkownicy piszą bez polskich znaków („zazolc gesla jazn”). Znormalizowanie do ASCII gubi
  rozróżnienia (np. „łąka” i „laka”), więc nie zamieniaj tekstu na ASCII w treningu. Zamiast tego dodaj do zbioru
  testowego odsetek wpisów bez diakrytyków, jeśli ruch taki jest, i zmierz spadek. Normalizację Unicode (NFC) stosuj
  zawsze, bo ten sam znak może mieć dwie reprezentacje.
- **Szyk swobodny i brak podmiotu.** Reguły oparte na pozycji słowa psują się częściej niż w angielskim.
- **Wielkość liter.** Wielka litera w środku zdania wskazuje nazwę własną; nie sprowadzaj do małych liter przed NER.

## Narzędzia i modele (stan na 2026-10-17)
- **Morfeusz 2** — słownikowy analizator i generator morfologiczny polskiego, słowniki SGJP i Polimorf; licencja
  BSD 2-clause (Woliński, LREC 2014; repozytorium CLARIN-PL). Dla Pythona jest nakładka; licencja nakładki bywa inna,
  sprawdź przed redystrybucją. Aktualna wersja i opieka nad projektem: [niezweryfikowane].
- **spaCy, potoki `pl_core_news_*`** — tokenizacja, morfologia, lematyzator, parser, NER. Karta modelu
  `pl_core_news_lg` (Hugging Face, dostęp 2026-10-17): wersja 3.7.0 dla spaCy ≥ 3.7.0 i < 3.8.0, dokładność lematów
  ok. 94,2%, F-score NER ok. 84,1%, dane: UD Polish PDB, NKJP. Licencja modelu na karcie: GPL-3.0 — sprawdź
  zgodność z własnym produktem. Wyniki dotyczą tekstu ogólnego; na tekstach specjalistycznych (np. medycznych)
  mogą być znacznie gorsze, więc zmierz na własnych danych.
- **HerBERT** — model typu BERT dla polskiego, trenowany na polskich korpusach, wprowadzony razem z KLEJ (Allegro
  ML Research, ACL 2020). Dostępność aktualnych wariantów i licencji: [niezweryfikowane], sprawdź na Hugging Face.
- **Polskie modele generatywne (np. Bielik, PLLuM)** — status, licencje i wyniki [niezweryfikowane]; wybór
  przez własny test, nie przez ranking.
- Embeddingi i wyszukiwanie dla polskiego: benchmark PIRB i kryteria w **ai-rag**; tu stosuj te same zasady
  (własne pytania, zapisana nazwa modelu).

## Benchmarki
- **KLEJ** (2020): dziewięć zadań rozumienia języka, w tym NER-podobne, wnioskowanie, sentyment (Allegro Reviews).
- **LEPISZCZE** (NeurIPS 2022): 13 par zadanie–zbiór, pięć z KLEJ, osiem nowych; zaprojektowany jako rozszerzalny.
- Ranking publiczny mówi, który model jest dobry **średnio**; o wyborze rozstrzyga zbiór testowy z Twojej domeny.
  Konkretnych wyników tu nie przytaczam [niezweryfikowane].

## PII i anonimizacja w tekście
1. **Inwentarz typów:** imię i nazwisko, PESEL, NIP, REGON, numer dowodu, telefon, e-mail, adres, IBAN, tablica
   rejestracyjna, dane w tekście swobodnym („mój sąsiad z Lipowej 5”).
2. **Warstwy:** regex z walidacją tam, gdzie jest struktura; NER na imiona, nazwiska, adresy; słowniki dla
   kontekstu. Suma kontrolna PESEL: wagi 1-3-7-9-1-3-7-9-1-3 dla dziesięciu cyfr, cyfra kontrolna = (10 − suma mod 10)
   mod 10; walidacja odrzuca losowe 11-cyfrowe liczby i podnosi precyzję. NIP ma własną sumę kontrolną [założenie —
   sprawdź w przepisach].
3. **Presidio** (Microsoft, open source): domyślnie konfiguracja angielska; polski wymaga podmiany silnika NLP
   (spaCy lub Stanza) i recognizerów oraz listy słów kontekstowych per język; własne rozpoznawacze to klasa
   `PatternsRecognizer` albo podklasa bazowa (dokumentacja Presidio, dostęp 2026-10-17). Czy jest gotowy rozpoznawacz
   PESEL w bieżącej wersji: [niezweryfikowane] — sprawdź w kodzie.
4. **Miara:** zbiór złoty z oznaczonymi PII (≥ 200 dokumentów w domenie); raportuj **recall per typ** (pominięcie
   to wyciek) i precision (nadmiar psuje użyteczność tekstu). Błędy w ciągu znaków granicznych też liczą się jako
   wyciek częściowy.
5. **Anonimizacja a pseudonimizacja:** zamiana na `[OSOBA]` jest nieodwracalna; stały token (`OSOBA_17`) zachowuje
   spójność w dokumencie i pozwala zliczać, ale wymaga rozstrzygnięcia koreferencji i odmiany („Kowalskiemu” =
   „Kowalski”); mapowanie token ↔ osoba trzymaj osobno i chroń. Pseudonimizacja nadal jest przetwarzaniem danych
   osobowych — ocena prawna: **arch-privacy-compliance**.
6. **Przed wysłaniem do zewnętrznego LLM** wykonaj anonimizację lokalnie i sprawdź na próbce, że nic nie wycieka.

## Adnotacja
- **Wytyczne:** definicja klasy, 3–5 przykładów typowych i granicznych, reguły rozstrzygania („gdy dwie klasy
  pasują, wybierz…”), granice spanu (czy „Pan” wchodzi w nazwisko?). Wersjonuj wytyczne; zmiana = nota o wpływie
  na już oznaczone dane.
- **Pilot:** 100–200 przykładów, ≥ 2 annotatorów niezależnie. Miary: Cohen's kappa (2 osoby), Krippendorff's alpha
  (więcej osób, braki), dla spanów F1 jednego annotatora względem drugiego. Rozbieżności omawiaj i dopisuj do wytycznych.
- **Złoty zbiór:** część oznacza dwóch annotatorów z rozstrzygnięciem; resztę jedna osoba z kontrolą próbki.
- **Active learning:** uncertainty sampling (najniższa pewność) lub różnorodność; po każdej rundzie przelicz miary na
  stałym zbiorze testowym, który nie bierze udziału w wyborze przykładów.
- **LLM jako pomoc annotatora:** podpowiedź etykiety przyspiesza pracę, ale ryzykuje kotwiczenie; kontroluj próbkę
  oznaczoną bez podpowiedzi.
