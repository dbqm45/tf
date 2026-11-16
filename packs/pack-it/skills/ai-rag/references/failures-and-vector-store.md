# Porażki RAG i wybór bazy wektorowej

## Spis treści
- Objaw → przyczyna → poprawka
- Baza wektorowa: kryteria i kandydaci
- Kolejność diagnozy

## Objaw → przyczyna → poprawka
| Objaw | Najczęstsza przyczyna | Poprawka |
|---|---|---|
| właściwy fragment nie jest w top-k | chunk bez kontekstu; słaby model; brak BM25 | contextual retrieval, hybryda, test modeli na zbiorze złotym |
| fragment jest w top-50, ale nie w top-5 | brak rerankingu | reranker na 50–150 kandydatach |
| odpowiedź ignoruje dobry fragment | za dużo szumu w kontekście; fragment w środku | mniej fragmentów, lepsza kolejność, cytaty wymuszone |
| odpowiedź nieprawdziwa, brak źródła | prompt dopuszcza wiedzę ogólną | „tylko z fragmentów”, „nie wiem”, weryfikacja cytatu |
| stare dane w odpowiedzi | brak reindeksacji, brak wersji | hash treści, data w metadanych, filtr aktualności |
| tabela rozbita, liczby bez nagłówków | parser spłaszcza tabele | parser strukturalny, wiersz z nagłówkiem w chunku |
| ten sam fragment 5 razy | duplikaty wersji, zakładka | deduplikacja po hashu, jedna wersja w indeksie |
| kody i numery nie znajdowane | tylko wektory | BM25 w hybrydzie |
| selektywny filtr zwraca mało wyników (pgvector) | filtr po skanie indeksu | iterative scan, partycje, albo baza z filtrem w indeksie |
| użytkownik widzi cudzy fragment | filtr uprawnień po wyszukaniu lub w prompcie | filtr w zapytaniu do indeksu, test z kontem bez uprawnień |
| odpowiedź wykonuje polecenie z dokumentu | fragment traktowany jak instrukcja | dane, nie polecenia; brak narzędzi sterowanych treścią |

## Baza wektorowa: kryteria i kandydaci
Kryteria w kolejności ważności: (1) skala i opóźnienie p95 przy filtrach, (2) filtrowanie metadanych w tym samym
zapytaniu, (3) hybryda (BM25 plus wektory) bez sklejania dwóch systemów, (4) operacje i utrzymanie, (5) koszt,
(6) integracja z posiadanym stosem. Wynik porównania zapisz jako macierz kryteriów (arch-tech-selection).

| Kandydat | Kiedy | Uwaga |
|---|---|---|
| pgvector | PostgreSQL już jest, korpus do kilku milionów wektorów, transakcje z danymi | indeks HNSW lub IVFFlat; filtr po skanie przybliżonym; indeksy i plan: be-database |
| Qdrant | filtrowanie po metadanych, średnia i duża skala | osobna usługa do utrzymania [niezweryfikowane — sprawdź bieżące funkcje hybrydy] |
| Milvus | bardzo duża skala, wiele typów indeksów | najwięcej elementów do utrzymania [niezweryfikowane] |
| OpenSearch | BM25 i wektory w jednym silniku, już używany do logów lub wyszukiwania | dobra hybryda leksykalna, polskie analizatory [niezweryfikowane] |

Nie wybieraj po rankingach z internetu: wczytaj własne 100 tys. fragmentów, uruchom zbiór złoty i zmierz
recall@k, opóźnienie i koszt.

## Kolejność diagnozy
1. Czy właściwy fragment w ogóle istnieje w indeksie (parser, ingestia)?
2. Czy jest w top-50 (embedding, BM25, chunk)? 3. Czy jest w top-5 (reranking)? 4. Czy odpowiedź go używa (prompt,
kontekst)? Naprawiasz pierwszy etap, który zawodzi.
