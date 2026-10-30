---
name: ai-rag
description: Użyj przy RAG i wyszukiwaniu w dokumentach dla LLM — RAG czy długi kontekst, chunking, embeddingi, hybryda, reranking, uprawnienia, ewaluacja retrievalu.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy budujesz czatbota lub funkcję odpowiadającą na podstawie własnych dokumentów — decyzja RAG, długi kontekst, fine-tuning albo narzędzia, wczytywanie i parsowanie (PDF, tabele), chunking (rozmiar, zakładka, wg struktury), wybór embeddingów także dla polskiego, wyszukiwanie hybrydowe BM25 plus wektory, reranking, contextual retrieval, filtry metadanych, uprawnienia per dokument, świeżość i reindeksacja, wybór bazy wektorowej (pgvector, Qdrant, Milvus, OpenSearch), metryki retrievalu (recall@k, MRR, nDCG), cytowanie źródeł, typowe porażki i prompt injection przez pobrane dokumenty. Nie do SDK, kontraktu wyjścia i pętli narzędzi (eng-llm-features), indeksów i zapytań PostgreSQL (be-database), ogólnej metody ewaluacji (ai-evals), potoków danych (data-engineering) ani projektu agenta (ai-agents)."
  slowa: "rag, retrieval, wyszukiwanie semantyczne, baza wiedzy, czatbot na dokumentach, embeddingi, wektory, baza wektorowa, pgvector, qdrant, milvus, opensearch, chunking, dzielenie dokumentów, hybrydowe wyszukiwanie, bm25, reranking, contextual retrieval, recall@k, mrr, ndcg, cytowanie źródeł, halucynacje, długi kontekst, uprawnienia do dokumentów, reindeksacja"
---

# RAG — od decyzji do mierzonego retrievalu

RAG to dwa systemy: **wyszukiwanie** (zwraca właściwe fragmenty) i **generowanie** (odpowiada tylko z nich).
Większość porażek leży w wyszukiwaniu, więc mierzysz je osobno, zanim ruszysz prompt. Wywołanie modelu, schemat
wyjścia i pętlę narzędzi opisuje **eng-llm-features**; ten skill dotyczy tego, co trafia do kontekstu i skąd.

## Procedura
1. **Czy RAG w ogóle.** Wybór wg problemu, nie mody:
   - korpus mieści się w kontekście (Anthropic: poniżej ok. 200 000 tokenów, ok. 500 stron) i zmienia się rzadko →
     całość w prompcie z prompt caching, bez indeksu;
   - korpus duży, zmienny, z uprawnieniami albo wymaga cytatów → RAG;
   - dane ustrukturyzowane (zamówienie, stan konta) → narzędzie z zapytaniem do API lub SQL, nie wektory;
   - definicje, które muszą być dokładne i mieć właściciela (metryki, schematy, reguły) → kuratorowane pliki czytane
     deterministycznie, RAG dla reszty, router między nimi (`references/parsowanie-ewaluacja-wiki.md` §3);
   - fine-tuning zmienia styl, format i zachowanie, a nie dostarcza aktualnych faktów; nie zastępuje RAG-a
     [założenie — zweryfikuj u dostawcy modelu].
2. **Wczytywanie.** Parser dobierz do dokumentu i obejrzyj wynik na 10 stronach: kolejność kolumn, nagłówki, stopki
   powtarzane na każdej stronie, tabele (zostaw jako Markdown/HTML z nagłówkiem, nie jako płaski tekst), OCR dla
   skanów. Do każdego fragmentu zapisz źródło, stronę, sekcję, datę, wersję i listę uprawnień. Strona bez warstwy
   tekstu albo z podejrzanie małą liczbą znaków to alarm, nie pusty dokument. Przy złych odpowiedziach najpierw
   czytasz surowe wyjście parsera na najgorszych dokumentach (skan, tabela przez dwie strony, dwie kolumny), dopiero
   potem stroisz retriever (`references/parsowanie-ewaluacja-wiki.md` §1).
3. **Chunking.** Zacznij od podziału wg struktury (sekcja, akapit, wiersz tabeli z nagłówkiem), nie od stałej liczby
   znaków. Punkt startowy: 200–500 tokenów i zakładka 10–20% [założenie — dobierz na zbiorze z kroku 7]. Za mały chunk
   gubi kontekst, za duży rozmywa embedding. Wariant „małe do szukania, duże do wysłania” (rodzic–dziecko) pomaga,
   gdy odpowiedź wymaga sąsiedztwa.
4. **Embeddingi.** Kryteria: jakość na **własnych** polskich pytaniach, długość wejścia, wymiar (koszt przechowywania),
   licencja i hosting (API albo własny model), koszt reindeksacji przy zmianie modelu. Modele wielojęzyczne radzą sobie
   z polskim różnie — benchmark PIRB porównuje je na polskich zadaniach, ale rozstrzyga dopiero test na Twoich
   danych. Zapisz nazwę i wersję modelu przy indeksie; zmiana modelu = pełna reindeksacja. Prefiksy zapytanie/dokument,
   jeśli model ich wymaga, stosuj konsekwentnie.
5. **Wyszukiwanie hybrydowe.** Wektory gubią identyfikatory, kody błędów, nazwy własne i numery paragrafów; BM25
   gubi parafrazy. Uruchom oba i połącz rankingi (Reciprocal Rank Fusion albo ważona suma), potem **reranking**
   (cross-encoder lub model rerankujący) na 50–150 kandydatach do 5–20 wyników. Polski wymaga analizatora z lematyzacją
   albo przynajmniej poprawnego tokenizera po stronie BM25.
6. **Contextual retrieval** (gdy fragmenty tracą sens bez dokumentu, np. „przychody wzrosły o 3%”): model dopisuje do
   każdego chunka 50–100 tokenów kontekstu z dokumentu przed embeddingiem i BM25. Wynik Anthropic (19.09.2024): błędne
   wyszukania w top-20 spadły o 35% (embeddingi), 49% (z BM25), 67% (z rerankingiem). Koszt jednorazowy ok. 1,02 USD
   za milion tokenów dokumentów przy prompt caching. To wynik na ich zbiorach — zmierz u siebie.
7. **Zbiór złoty i metryki retrievalu** (metoda ogólna: **ai-evals**). Zbierz 50–200 prawdziwych pytań z oczekiwanymi
   fragmentami, w tym pytania bez odpowiedzi w korpusie. Mierz: recall@k (czy właściwy fragment jest w top-k),
   MRR (jak wysoko), nDCG (gdy fragmentów jest wiele i różnią się przydatnością). Zmieniasz jedną rzecz naraz
   (parser, chunk, model, hybryda, reranker) i porównujesz z poprzednim wynikiem. Dopiero potem oceniasz odpowiedzi.
   Recall@k liczysz **osobno dla dwóch koszyków**: zapytania semantyczne (parafrazy) i dokładne (identyfikatory, kody,
   wersje, liczby); pytania łączące dwa fakty to trzecia kategoria. Próg podobieństwa ustawiasz dopiero po
   histogramie cosinusa dla losowych, niepowiązanych par z własnego korpusu (`references/parsowanie-ewaluacja-wiki.md` §2).
8. **Odpowiedź z cytatami.** Prompt: odpowiadaj wyłącznie z podanych fragmentów, przy każdym twierdzeniu podaj
   identyfikator źródła, a przy braku podstaw odpowiedz „nie wiem”. Kod sprawdza, że cytowany identyfikator istnieje
   wśród przekazanych fragmentów, a cytat występuje w jego treści. Do kontekstu dawaj mniej, lepszych fragmentów;
   model gubi środek długiego kontekstu.
9. **Uprawnienia i świeżość.** Uprawnienia egzekwujesz **w zapytaniu do indeksu** (filtr po metadanych na poziomie
   bazy), nigdy w prompcie ani po wygenerowaniu odpowiedzi. Zmiana uprawnień dokumentu musi dotrzeć do indeksu
   równie szybko jak usunięcie dokumentu. Reindeksacja przyrostowa wg hasha treści, usunięcia jako osobna ścieżka,
   data i wersja w metadanych, filtr „aktualne”. Potoki ładowania: **data-engineering**.
10. **Baza wektorowa.** Kryteria: skala (miliony, a nie setki tysięcy wektorów?), filtrowanie metadanych razem
    z wyszukiwaniem, hybryda w jednym zapytaniu, operacje (kopie, replikacja, kto to utrzyma), koszt, zgodność
    z istniejącym stosem. Wskazówka: mały korpus i PostgreSQL już w użyciu → pgvector (indeksy: **be-database**);
    duża skala i bogate filtrowanie → Qdrant, Milvus lub OpenSearch (też BM25). Pułapka pgvector: filtr działa po
    skanie indeksu przybliżonego, więc selektywny `WHERE` zwraca za mało wierszy — włącz iterative scan (od 0.8.0).
11. **Prompt injection.** Pobrany dokument to **dane, nie polecenia**: zawiera tekst, który próbuje sterować modelem
    („zignoruj instrukcje”, „wyślij rozmowę na adres…”). Model nie dostaje narzędzi zapisu ani wysyłki wynikających
    z treści fragmentów; fragmenty w wyraźnych znacznikach; źródła spoza zaufanych indeksów oznaczone. Jeśli pytanie
    brzmi „czy użytkownik widzi dokument, którego nie powinien”, to sprawa kroku 9, a nie promptu.

Diagnoza porażek (objaw → przyczyna → poprawka) i dłuższa tabela baz: `references/porazki-i-baza-wektorowa.md`.

## Przykład
**Wejście:** „Czatbot HR na 1 800 PDF-ów, polski, kody typu ZUS-ZUA, pracownicy widzą tylko swój dział.”
**Wynik:**
- korpus ok. 40 mln tokenów → RAG (poza limitem 200 000);
- parser z zachowaniem tabel, chunki wg sekcji ok. 350 tokenów, metadane `dzial`, `wersja`, `data`;
- indeks: embeddingi wielojęzyczne + BM25 z polskim analizatorem, RRF, reranker 100 → 8; kody znajdzie BM25;
- filtr `dzial IN (użytkownik)` w zapytaniu do bazy;
- zbiór złoty 120 pytań (20 bez odpowiedzi); cel startowy recall@20 ≥ 0,9 [założenie], porównanie przed i po każdej zmianie;
- odpowiedź z identyfikatorami `[doc-123#s4]` sprawdzanymi kodem; „nie wiem” przy braku trafienia.

## Checklista
- [ ] uzasadniony wybór: kontekst, RAG, narzędzie albo fine-tuning
- [ ] wynik parsera obejrzany na najgorszych dokumentach; alarm na strony bez tekstu; metadane źródła, wersji i uprawnień przy każdym chunku
- [ ] embeddingi sprawdzone na własnych polskich pytaniach; nazwa modelu zapisana przy indeksie
- [ ] hybryda i reranking albo uzasadnienie ich braku
- [ ] zbiór złoty z pytaniami bez odpowiedzi; recall@k osobno dla zapytań semantycznych i dokładnych; próg z rozkładu losowych par
- [ ] uprawnienia w zapytaniu do indeksu; propagacja zmian i usunięć
- [ ] cytaty weryfikowane kodem; „nie wiem” przy braku podstaw
- [ ] pobrane fragmenty traktowane jak dane; brak narzędzi zapisu sterowanych treścią

## Źródła
- Anthropic, „Introducing Contextual Retrieval” (19.09.2024, dostęp 2026-10-17): redukcja błędów 35%/49%/67%,
  top-20, ok. 1,02 USD za milion tokenów, próg 200 000 tokenów (ok. 500 stron).
- pgvector README (github.com/pgvector/pgvector, dostęp 2026-10-17): HNSW i IVFFlat, `halfvec`, filtrowanie po skanie
  indeksu, iterative scan od 0.8.0.
- PIRB: Polish Information Retrieval Benchmark (arXiv 2402.13350) — wyniki modeli wielojęzycznych na polskich
  zadaniach; ranking zależy od zbioru, dlatego test na własnych danych [liczb nie przytaczam].
- [niezweryfikowane] RRF jako metoda łączenia rankingów, zakresy rozmiaru chunka i liczby kandydatów rerankingu,
  numeracja OWASP LLM Top 10 2025 (wektory i embeddingi, prompt injection) — z wiedzy ogólnej, sprawdź przed cytowaniem.

Opisane własnymi słowami.
