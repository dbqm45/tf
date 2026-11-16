# Parsowanie, ewaluacja w koszykach i wiedza kanoniczna

Spis treści: 1. Kontrola parsowania przed indeksacją · 2. Ewaluacja w dwóch koszykach i próg podobieństwa ·
3. Wiki kanoniczne czy RAG · 4. Świeżość generowanych artefaktów wiedzy

## 1. Kontrola parsowania przed indeksacją
Błędny tekst z parsera psuje każdy dalszy krok, a stroić retriever na złym tekście to strata czasu. Kolejność:
1. **Alarmy na stronę:** strona bez warstwy tekstu albo z podejrzanie małą liczbą znaków w stosunku do sąsiednich
   to alarm (skan bez OCR, tekst jako obraz), nie pusty dokument. Liczysz to automatycznie dla całego korpusu.
2. **Przegląd surowego wyjścia na najgorszych dokumentach:** skan, tabela przez dwie strony, układ w dwóch kolumnach,
   przypisy, nagłówki powtarzane na stronach. Czytasz wynik parsera, zanim ktokolwiek zmieni model embeddingów.
3. **Miary w zestawie ewaluacyjnym:** struktura tabel (np. TEDS — podobieństwo drzewa tabeli do wzorca) i kolejność
   czytania (czy akapity z dwóch kolumn nie są przeplecione) na kilkunastu ręcznie opisanych stronach.
4. **Parser świadomy układu** (open source albo usługa) wybierasz po kryteriach: tabele i scalone komórki, kolejność
   czytania, OCR i języki (polskie znaki), wzory i przypisy, koszt na stronę, przetwarzanie lokalne czy u dostawcy
   (dane wrażliwe), stabilność wyniku między wersjami. Rozstrzyga test na Twoich najgorszych dokumentach, nie ranking.

## 2. Ewaluacja w dwóch koszykach i próg podobieństwa
- Każde pytanie w zbiorze ma **typ zapytania**: *semantyczne* (parafrazy, intencje) albo *dokładne*
  (identyfikatory, kody, numery umów, wersje, liczby, negacje). Recall@k liczysz osobno dla każdego koszyka.
  Średnia 0,82 potrafi ukryć 0,95 dla parafraz i 0,4 dla numerów. Koszyk dokładny ratuje BM25 i hybryda (SKILL.md krok 5).
- **Pytania łączące dwa fakty** (z dwóch dokumentów albo fragmentów) to trzecia kategoria: pojedynczy wektor
  zapytania ma teoretyczną granicę tego, ile różnych kombinacji dokumentów umie wskazać (Weller i in., „On the
  Theoretical Limitations of Embedding-Based Retrieval”, 2025 [niezweryfikowane]). Pomaga dekompozycja pytania albo
  kilka zapytań.
- **Próg podobieństwa ustawiasz z rozkładu, nie „na oko”.** Najpierw histogram cosinusa dla kilkuset losowych,
  niepowiązanych par z własnego korpusu: przestrzeń embeddingów bywa anizotropowa i losowe pary leżą przy 0,8–0,9.
  Próg poniżej tego rozkładu niczego nie odcina. Lepiej odcinać po reranku albo stałym top-k i mierzyć „nie wiem”.

## 3. Wiki kanoniczne czy RAG
| Treść | Gdzie | Dlaczego |
|---|---|---|
| definicje, które muszą być dokładne i mają właściciela (metryki, schematy tabel, reguły biznesowe) | kuratorowane pliki (Markdown z frontmatterem: `type`, właściciel, data weryfikacji, linki do powiązanych) czytane deterministycznie od indeksu | jedna definicja, wersjonowana, z przeglądem; RAG zwróci trzy sprzeczne wersje z różnych stron |
| archiwa, treści masowe, dokumenty bez właściciela | RAG | za dużo, by kuratorować |
| dane z systemów (stan zamówienia, liczby) | narzędzie z zapytaniem | wektory nie liczą |

Router wybiera ścieżkę przed wyszukiwaniem: pytanie o definicję → plik kanoniczny, reszta → RAG. Przykładowy format
otwarty: Open Knowledge Format (github.com/GoogleCloudPlatform/knowledge-catalog, plik SPEC w katalogu okf, wersja 0.2,
odczyt 2026-10-29): wymagane tylko pole `type`; plik indeksu jako spis do stopniowego odsłaniania; zwykłe linki Markdown.

Jeśli wiki utrzymuje agent, trzy strefy z różnymi prawami zapisu:
- źródła — tylko do odczytu;
- strony utrzymywane przez agenta, z polem `sources` i aktualizacją zamiast przepisywania;
- notatki i decyzje zespołu — zmieniane tylko za zgodą człowieka.

Wczytanie nowych źródeł najpierw pokazuje plan (nowe i zmienione strony), a dopiero potem zapisuje. Pole
„zweryfikowane” wpisuje człowiek, agent tylko „wygenerowane”.

## 4. Świeżość generowanych artefaktów wiedzy
Generowany indeks, graf kodu albo mapa dryfuje po cichu: hook zgłasza sukces, a mapa jest sprzed tygodni. Każdy taki
artefakt ma znacznik czasu i commit źródła; kontrola w CI porównuje go z `git log -1` i alarmuje po progu (np. 24 h).
Pola `stale_after` i `verified` (OKF) albo własne odpowiedniki niosą tę informację do agenta, który czyta artefakt.

Źródła: P. Perrone, „Why Your RAG Pipeline Dies on Real Documents” (2026-10-01, artykuł sponsorowany — bez
rekomendacji dostawcy); J. Wąsowski, „The Limits of Vector Search in RAG” (2026-09-14, liczby [niezweryfikowane]);
Dev Evolution, „Beyond RAG: … Open Knowledge Format” (2026-09-09); R. Brasil Monteiro, „Building a Complete Personal
Harness: LLM Wiki…” (2026-05-03); U. Estari, „Production-Grade OKF + Graphify Setup” (2026-08-13).
